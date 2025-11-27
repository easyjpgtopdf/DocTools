/**
 * PDF Controller
 * Handles PDF operations (upload, edit, OCR, download)
 */

const fs = require('fs');
const path = require('path');
const { getVisionClient } = require('../config/google-cloud');
const visionOCR = require('../api/pdf-ocr/vision-ocr');

/**
 * Upload PDF file
 * Returns file ID and metadata
 */
async function uploadPDF(req, res) {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No PDF file uploaded'
      });
    }

    // Validate file type
    const allowedMimes = ['application/pdf'];
    const allowedExtensions = ['.pdf'];
    const isValidMime = allowedMimes.includes(req.file.mimetype);
    const isValidExtension = allowedExtensions.some(ext => 
      req.file.originalname.toLowerCase().endsWith(ext)
    );
    
    if (!isValidMime && !isValidExtension) {
      return res.status(400).json({
        success: false,
        error: 'Invalid file type. Only PDF files are allowed.'
      });
    }

    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (req.file.size > maxSize) {
      return res.status(400).json({
        success: false,
        error: `File size exceeds 100MB limit. File size: ${(req.file.size / 1024 / 1024).toFixed(2)}MB`
      });
    }

    const fileStorage = require('../utils/fileStorage');
    const fileBuffer = fs.readFileSync(req.file.path);

    // Store file and get ID
    const fileId = fileStorage.storeFile(
      fileBuffer,
      req.file.originalname,
      req.file.mimetype
    );

    // Cleanup uploaded temp file
    try {
      fs.unlinkSync(req.file.path);
    } catch (e) {
      console.warn('Could not delete temp file:', e.message);
    }

    // Optionally extract text and fonts for preview
    let textItems = [];
    let fonts = [];
    
    try {
      const pdfContentParser = require('../api/pdf-edit/pdf-content-parser');
      textItems = await pdfContentParser.extractTextWithPositions(fileBuffer);
      fonts = await pdfContentParser.getFontsFromPDF(fileBuffer);
    } catch (e) {
      console.warn('Could not extract PDF content:', e.message);
    }

    // Get metadata
    const metadata = fileStorage.getFileMetadata(fileId);

    res.json({
      success: true,
      message: 'PDF uploaded successfully',
      fileId: fileId,
      filename: req.file.originalname,
      size: req.file.size,
      mimeType: req.file.mimetype,
      createdAt: metadata.createdAt,
      textItems: textItems,
      fonts: fonts
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({
      success: false,
      error: 'Upload failed: ' + error.message
    });
  }
}

/**
 * Edit PDF (text, images, etc.)
 */
async function editPDF(req, res) {
  try {
    const { pdfData, edits } = req.body;

    if (!pdfData) {
      return res.status(400).json({
        success: false,
        error: 'No PDF data provided'
      });
    }

    // Use native PDF editor
    const nativePdfEditor = require('../api/pdf-edit/native-pdf-editor');
    
    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf;base64,')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }

    // Apply edits
    const editedBuffer = await nativePdfEditor.applyNativeEdits(pdfBuffer, edits || {});
    const editedBase64 = editedBuffer.toString('base64');

    res.json({
      success: true,
      pdfData: `data:application/pdf;base64,${editedBase64}`,
      message: 'PDF edited successfully'
    });
  } catch (error) {
    console.error('PDF editing error:', error);
    res.status(500).json({
      success: false,
      error: 'PDF editing failed: ' + error.message
    });
  }
}

/**
 * Edit PDF text specifically
 * Takes file ID and text edits
 */
async function editText(req, res) {
  try {
    const { fileId, textEdits } = req.body;

    if (!fileId) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required'
      });
    }

    if (!textEdits || !Array.isArray(textEdits) || textEdits.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Text edits array is required'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    
    // Get file
    const { buffer: pdfBuffer, metadata } = fileStorage.getFile(fileId);

    // Use native PDF editor
    const nativePdfEditor = require('../api/pdf-edit/native-pdf-editor');

    // Prepare edits object
    const edits = {
      textEdits: textEdits.map(edit => ({
        pageIndex: edit.pageIndex || 0,
        x: edit.x || 0,
        y: edit.y || 0,
        text: edit.text || '',
        fontSize: edit.fontSize || 12,
        fontName: edit.fontName || 'Helvetica',
        fontColor: edit.fontColor || [0, 0, 0]
      }))
    };

    // Apply edits
    const editedBuffer = await nativePdfEditor.applyNativeEdits(pdfBuffer, edits);

    // Update stored file
    fileStorage.updateFile(fileId, editedBuffer);
    fileStorage.addEdit(fileId, {
      type: 'text',
      edits: textEdits
    });

    // Convert to base64 for response
    const editedBase64 = editedBuffer.toString('base64');

    res.json({
      success: true,
      fileId: fileId,
      pdfData: `data:application/pdf;base64,${editedBase64}`,
      message: 'Text edited successfully',
      editsCount: textEdits.length
    });
  } catch (error) {
    console.error('Text editing error:', error);
    res.status(500).json({
      success: false,
      error: 'Text editing failed: ' + error.message
    });
  }
}

/**
 * Perform OCR on PDF page
 * Takes file ID and page number
 */
async function performOCR(req, res) {
  try {
    const visionClient = getVisionClient();
    if (!visionClient) {
      return res.status(503).json({
        success: false,
        error: 'Google Cloud Vision API not initialized. Please check your service account credentials.'
      });
    }

    const { fileId, pageIndex = 0, scale = 2.0, languageHints = ['en'] } = req.body;

    if (!fileId) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    
    // Get file
    const { buffer: pdfBuffer } = fileStorage.getFile(fileId);

    // Get client ID for rate limiting
    const clientId = req.ip || req.headers['x-forwarded-for'] || 'default';

    // Perform OCR
    const ocrResult = await visionOCR.performOCR(pdfBuffer, pageIndex, {
      scale: scale,
      languageHints: languageHints,
      clientId: clientId
    });

    // Map coordinates back to PDF space
    const mappedWords = ocrResult.words.map(word => {
      // Convert image coordinates to PDF coordinates
      // This is a simplified mapping - adjust based on your PDF rendering scale
      return {
        ...word,
        pdfCoordinates: {
          x: word.boundingBox.x,
          y: word.boundingBox.y,
          width: word.boundingBox.width,
          height: word.boundingBox.height
        }
      };
    });

    res.json({
      success: true,
      fileId: fileId,
      pageIndex: pageIndex,
      text: ocrResult.text,
      words: mappedWords,
      paragraphs: ocrResult.paragraphs,
      blocks: ocrResult.blocks,
      confidence: ocrResult.confidence,
      method: ocrResult.method
    });
  } catch (error) {
    console.error('OCR error:', error);
    
    let statusCode = 500;
    if (error.message.includes('Rate limit')) {
      statusCode = 429;
    } else if (error.message.includes('not initialized') || error.message.includes('credentials')) {
      statusCode = 503;
    } else if (error.message.includes('Invalid') || error.message.includes('not found')) {
      statusCode = 400;
    }

    res.status(statusCode).json({
      success: false,
      error: error.message || 'OCR failed',
      code: error.code || 'OCR_ERROR'
    });
  }
}

/**
 * Perform batch OCR on multiple pages
 */
async function performBatchOCR(req, res) {
  try {
    const visionClient = getVisionClient();
    if (!visionClient) {
      return res.status(503).json({
        success: false,
        error: 'Google Cloud Vision API not initialized'
      });
    }

    const { pdfData, pageIndices = [0], scale = 2.0, languageHints = ['en'] } = req.body;

    if (!pdfData || !Array.isArray(pageIndices) || pageIndices.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request. Provide pdfData and pageIndices array.'
      });
    }

    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf;base64,')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }

    // Get client ID for rate limiting
    const clientId = req.ip || req.headers['x-forwarded-for'] || 'default';

    // Perform batch OCR
    const batchResult = await visionOCR.performBatchOCR(pdfBuffer, pageIndices, {
      scale: scale,
      languageHints: languageHints,
      clientId: clientId
    });

    res.json({
      success: batchResult.success,
      ...batchResult
    });
  } catch (error) {
    console.error('Batch OCR error:', error);
    
    let statusCode = 500;
    if (error.message.includes('Rate limit')) {
      statusCode = 429;
    }

    res.status(statusCode).json({
      success: false,
      error: error.message || 'Batch OCR failed',
      code: error.code || 'BATCH_OCR_ERROR'
    });
  }
}

/**
 * Download edited PDF (legacy endpoint)
 */
async function downloadPDF(req, res) {
  try {
    const { pdfData, filename = 'edited-document.pdf' } = req.body;

    if (!pdfData) {
      return res.status(400).json({
        success: false,
        error: 'No PDF data provided'
      });
    }

    // Convert base64 to buffer
    let pdfBuffer;
    if (typeof pdfData === 'string') {
      if (pdfData.startsWith('data:application/pdf;base64,')) {
        pdfData = pdfData.split(',')[1];
      }
      pdfBuffer = Buffer.from(pdfData, 'base64');
    } else {
      pdfBuffer = Buffer.from(pdfData);
    }

    // Set headers for download
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Content-Length', pdfBuffer.length);

    // Send PDF buffer
    res.send(pdfBuffer);
  } catch (error) {
    console.error('Download error:', error);
    res.status(500).json({
      success: false,
      error: 'Download failed: ' + error.message
    });
  }
}

/**
 * Download edited PDF by file ID
 * Handles large file downloads with progress
 */
async function downloadPDFById(req, res) {
  try {
    const { id } = req.params;

    if (!id) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    
    // Get file
    const { buffer: pdfBuffer, metadata } = fileStorage.getFile(id);

    // Get filename from metadata or use default
    const filename = metadata.originalName || 'edited-document.pdf';
    
    // Sanitize filename
    const safeFilename = filename.replace(/[^a-zA-Z0-9.-]/g, '_');

    // Set headers for download
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="${safeFilename}"`);
    res.setHeader('Content-Length', pdfBuffer.length);
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('X-File-Id', id);

    // For large files, stream the response
    if (pdfBuffer.length > 10 * 1024 * 1024) { // > 10MB
      // Stream in chunks
      const chunkSize = 1024 * 1024; // 1MB chunks
      let offset = 0;
      
      const streamChunk = () => {
        if (offset >= pdfBuffer.length) {
          // Cleanup file after download (optional)
          // fileStorage.deleteFile(id);
          return;
        }
        
        const chunk = pdfBuffer.slice(offset, Math.min(offset + chunkSize, pdfBuffer.length));
        offset += chunkSize;
        
        if (res.write(chunk)) {
          streamChunk();
        } else {
          res.once('drain', streamChunk);
        }
      };
      
      streamChunk();
      res.on('finish', () => {
        // Optional: cleanup after download
      });
    } else {
      // Send entire buffer for smaller files
      res.send(pdfBuffer);
    }
  } catch (error) {
    console.error('Download error:', error);
    
    if (error.message.includes('not found')) {
      return res.status(404).json({
        success: false,
        error: 'File not found'
      });
    }
    
    res.status(500).json({
      success: false,
      error: 'Download failed: ' + error.message
    });
  }
}

/**
 * Get server status
 */
function getStatus(req, res) {
  const { checkGoogleCloudStatus } = require('../config/google-cloud');
  const status = checkGoogleCloudStatus();
  
  res.json({
    success: true,
    server: 'running',
    visionApi: status.vision.initialized ? 'initialized' : 'not initialized',
    firebase: status.firebase.initialized ? 'initialized' : 'not initialized',
    timestamp: new Date().toISOString()
  });
}

/**
 * Get OCR service status
 */
function getOCRStatus(req, res) {
  const visionClient = getVisionClient();
  
  res.json({
    success: true,
    visionApi: visionClient ? 'active' : 'inactive',
    method: visionClient ? 'Google Cloud Vision API' : 'not available'
  });
}

/**
 * Load PDF by file ID
 */
async function loadPDF(req, res) {
  try {
    const { id } = req.params;

    if (!id) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    
    // Get file
    const { buffer: pdfBuffer, metadata } = fileStorage.getFile(id);

    // Set headers
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Length', pdfBuffer.length);
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('X-File-Id', id);

    // Send PDF buffer
    res.send(pdfBuffer);
  } catch (error) {
    console.error('Load PDF error:', error);
    
    if (error.message.includes('not found')) {
      return res.status(404).json({
        success: false,
        error: 'File not found'
      });
    }
    
    res.status(500).json({
      success: false,
      error: 'Failed to load PDF: ' + error.message
    });
  }
}

module.exports = {
  uploadPDF,
  editPDF,
  editText,
  performOCR,
  performBatchOCR,
  downloadPDF,
  downloadPDFById,
  loadPDF,
  getStatus,
  getOCRStatus
};

