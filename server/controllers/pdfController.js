/**
 * PDF Controller
 * Handles PDF operations (upload, edit, OCR, download)
 */

const fs = require('fs');
const path = require('path');
const { getVisionClient } = require('../config/google-cloud');
const visionOCR = require('../api/pdf-ocr/vision-ocr');
const { 
  validatePDF, 
  validateFileSize, 
  validateFileType,
  asyncHandler,
  withTimeout,
  PDFCorruptionError,
  FileSizeError,
  QuotaExceededError
} = require('../middleware/errorHandler');
const { cacheFile, getCachedFile, cacheResult, getCachedResult } = require('../utils/cache');
const { streamPDFResponse } = require('../utils/streaming');
const jobQueue = require('../utils/backgroundJobs');

/**
 * Upload PDF file
 * Returns file ID and metadata
 */
async function uploadPDF(req, res) {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No PDF file uploaded',
        code: 'NO_FILE'
      });
    }

    // Validate file type
    try {
      validateFileType(req.file.mimetype, req.file.originalname);
    } catch (error) {
      return res.status(error.statusCode || 400).json({
        success: false,
        error: error.message,
        code: error.name
      });
    }

    // Validate file size
    try {
      validateFileSize(req.file.size);
    } catch (error) {
      return res.status(error.statusCode || 413).json({
        success: false,
        error: error.message,
        code: error.name
      });
    }

    const fileStorage = require('../utils/fileStorage');
    let fileBuffer;

    try {
      fileBuffer = fs.readFileSync(req.file.path);
    } catch (error) {
      return res.status(500).json({
        success: false,
        error: 'Failed to read uploaded file',
        code: 'FILE_READ_ERROR'
      });
    }

    // Validate PDF structure
    try {
      await withTimeout(validatePDF(fileBuffer), 10000, 'PDF validation timed out');
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid or corrupted PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // Check cache first
    const fileHash = require('crypto').createHash('md5').update(fileBuffer).digest('hex');
    const cachedFile = getCachedFile(fileHash);
    
    let fileId;
    if (cachedFile) {
      // Use cached file ID if available
      const metadata = fileStorage.getFileMetadata(cachedFile.fileId);
      if (metadata) {
        fileId = cachedFile.fileId;
      }
    }

    if (!fileId) {
      // Store file and get ID
      fileId = fileStorage.storeFile(
        fileBuffer,
        req.file.originalname,
        req.file.mimetype
      );
      
      // Cache file
      cacheFile(fileHash, { fileId, buffer: fileBuffer });
    }

    // Cleanup uploaded temp file
    try {
      fs.unlinkSync(req.file.path);
    } catch (e) {
      console.warn('Could not delete temp file:', e.message);
    }

    // Optionally extract text and fonts for preview (with timeout)
    let textItems = [];
    let fonts = [];
    
    try {
      const pdfContentParser = require('../api/pdf-edit/pdf-content-parser');
      const parserResult = await withTimeout(
        Promise.all([
          pdfContentParser.extractTextWithPositions(fileBuffer),
          pdfContentParser.getFontsFromPDF(fileBuffer)
        ]),
        15000,
        'PDF parsing timed out'
      );
      textItems = parserResult[0] || [];
      fonts = parserResult[1] || [];
    } catch (e) {
      console.warn('Could not extract PDF content:', e.message);
      // Continue without extracted content
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
    throw error; // Let error handler middleware handle it
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
 * Supports background processing for large files
 */
async function performOCR(req, res) {
  try {
    const visionClient = getVisionClient();
    if (!visionClient) {
      return res.status(503).json({
        success: false,
        error: 'Google Cloud Vision API not initialized. Please check your service account credentials.',
        code: 'SERVICE_UNAVAILABLE'
      });
    }

    const { fileId, pageIndex = 0, scale = 2.0, languageHints = ['en'], background = false } = req.body;

    if (!fileId) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required',
        code: 'MISSING_FILE_ID'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    
    // Get file with error handling
    let pdfBuffer;
    try {
      const fileData = fileStorage.getFile(fileId);
      pdfBuffer = fileData.buffer;
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'File not found',
        code: 'FILE_NOT_FOUND'
      });
    }

    // Validate PDF
    try {
      await withTimeout(validatePDF(pdfBuffer), 10000);
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // Check cache for OCR results
    const cacheKey = `ocr-${fileId}-${pageIndex}-${scale}`;
    const cachedResult = getCachedResult(cacheKey);
    if (cachedResult) {
      return res.json({
        success: true,
        ...cachedResult,
        cached: true
      });
    }

    // Get client ID for rate limiting
    const clientId = req.ip || req.headers['x-forwarded-for'] || 'default';

    // Background processing for large files
    if (background || pdfBuffer.length > 50 * 1024 * 1024) {
      const jobId = jobQueue.enqueue({
        handler: async (data) => {
          return await visionOCR.performOCR(data.pdfBuffer, data.pageIndex, {
            scale: data.scale,
            languageHints: data.languageHints,
            clientId: data.clientId
          });
        },
        data: {
          pdfBuffer,
          pageIndex,
          scale,
          languageHints,
          clientId
        }
      });

      return res.json({
        success: true,
        message: 'OCR job queued for background processing',
        jobId: jobId,
        status: 'queued',
        statusUrl: `/api/pdf/ocr/status/${jobId}`
      });
    }

    // Perform OCR with timeout
    let ocrResult;
    try {
      ocrResult = await withTimeout(
        visionOCR.performOCR(pdfBuffer, pageIndex, {
          scale: scale,
          languageHints: languageHints,
          clientId: clientId
        }),
        60000, // 60 second timeout
        'OCR processing timed out'
      );
    } catch (error) {
      // Handle quota exceeded
      if (error.code === 8 || error.message.includes('RESOURCE_EXHAUSTED') || error.message.includes('quota')) {
        throw new QuotaExceededError('Google Cloud Vision API quota exceeded. Please try again later.');
      }
      throw error;
    }

    // Map coordinates back to PDF space
    const mappedWords = ocrResult.words.map(word => {
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

    const result = {
      success: true,
      fileId: fileId,
      pageIndex: pageIndex,
      text: ocrResult.text,
      words: mappedWords,
      paragraphs: ocrResult.paragraphs,
      blocks: ocrResult.blocks,
      confidence: ocrResult.confidence,
      method: ocrResult.method
    };

    // Cache result
    cacheResult(cacheKey, result, 1800); // 30 minutes

    res.json(result);
  } catch (error) {
    console.error('OCR error:', error);
    throw error; // Let error handler middleware handle it
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
 * Handles large file downloads with streaming
 */
async function downloadPDFById(req, res) {
  try {
    const { id } = req.params;

    if (!id) {
      return res.status(400).json({
        success: false,
        error: 'File ID is required',
        code: 'MISSING_FILE_ID'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    
    // Get file with error handling
    let pdfBuffer, metadata;
    try {
      const fileData = fileStorage.getFile(id);
      pdfBuffer = fileData.buffer;
      metadata = fileData.metadata;
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'File not found',
        code: 'FILE_NOT_FOUND'
      });
    }

    // Validate PDF
    try {
      await withTimeout(validatePDF(pdfBuffer), 10000);
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // Get filename from metadata or use default
    const filename = metadata.originalName || 'edited-document.pdf';
    
    // Sanitize filename
    const safeFilename = filename.replace(/[^a-zA-Z0-9.-]/g, '_');

    // Use streaming for large files
    await streamPDFResponse(res, pdfBuffer, safeFilename);
  } catch (error) {
    console.error('Download error:', error);
    throw error; // Let error handler middleware handle it
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
        error: 'File ID is required',
        code: 'MISSING_FILE_ID'
      });
    }

    const fileStorage = require('../utils/fileStorage');
    
    // Get file with error handling
    let pdfBuffer, metadata;
    try {
      const fileData = fileStorage.getFile(id);
      pdfBuffer = fileData.buffer;
      metadata = fileData.metadata;
    } catch (error) {
      return res.status(404).json({
        success: false,
        error: 'File not found',
        code: 'FILE_NOT_FOUND'
      });
    }

    // Validate PDF
    try {
      await withTimeout(validatePDF(pdfBuffer), 10000);
    } catch (error) {
      return res.status(error.statusCode || 422).json({
        success: false,
        error: error.message || 'Invalid PDF file',
        code: error.name || 'PDF_VALIDATION_ERROR'
      });
    }

    // Set headers
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Length', pdfBuffer.length);
    res.setHeader('Cache-Control', 'public, max-age=3600'); // Cache for 1 hour
    res.setHeader('X-File-Id', id);

    // Send PDF buffer
    res.send(pdfBuffer);
  } catch (error) {
    console.error('Load PDF error:', error);
    throw error; // Let error handler middleware handle it
  }
}

/**
 * Get OCR job status
 */
function getOCRJobStatus(req, res) {
  try {
    const { jobId } = req.params;
    
    if (!jobId) {
      return res.status(400).json({
        success: false,
        error: 'Job ID is required',
        code: 'MISSING_JOB_ID'
      });
    }

    const jobStatus = jobQueue.getJobStatus(jobId);
    
    if (!jobStatus) {
      return res.status(404).json({
        success: false,
        error: 'Job not found',
        code: 'JOB_NOT_FOUND'
      });
    }

    res.json({
      success: true,
      jobId: jobId,
      status: jobStatus.status,
      createdAt: jobStatus.createdAt,
      updatedAt: jobStatus.updatedAt,
      result: jobStatus.result,
      error: jobStatus.error
    });
  } catch (error) {
    console.error('Get OCR job status error:', error);
    throw error;
  }
}

module.exports = {
  uploadPDF: asyncHandler(uploadPDF),
  editPDF: asyncHandler(editPDF),
  editText: asyncHandler(editText),
  performOCR: asyncHandler(performOCR),
  performBatchOCR: asyncHandler(performBatchOCR),
  downloadPDF: asyncHandler(downloadPDF),
  downloadPDFById: asyncHandler(downloadPDFById),
  loadPDF: asyncHandler(loadPDF),
  getStatus,
  getOCRStatus,
  getOCRJobStatus
};

