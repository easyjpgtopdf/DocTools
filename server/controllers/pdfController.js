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
 */
async function uploadPDF(req, res) {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No PDF file uploaded'
      });
    }

    const filePath = req.file.path;
    const fileUrl = `/uploads/pdfs/${req.file.filename}`;
    const fileBuffer = fs.readFileSync(filePath);

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

    res.json({
      success: true,
      message: 'PDF uploaded successfully',
      filePath: filePath,
      pdfUrl: fileUrl,
      filename: req.file.originalname,
      size: req.file.size,
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
 * Perform OCR on PDF page
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

    const { pdfData, pageIndex = 0, scale = 2.0, languageHints = ['en'] } = req.body;

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

    // Get client ID for rate limiting
    const clientId = req.ip || req.headers['x-forwarded-for'] || 'default';

    // Perform OCR
    const ocrResult = await visionOCR.performOCR(pdfBuffer, pageIndex, {
      scale: scale,
      languageHints: languageHints,
      clientId: clientId
    });

    res.json({
      success: true,
      ...ocrResult
    });
  } catch (error) {
    console.error('OCR error:', error);
    
    let statusCode = 500;
    if (error.message.includes('Rate limit')) {
      statusCode = 429;
    } else if (error.message.includes('not initialized') || error.message.includes('credentials')) {
      statusCode = 503;
    } else if (error.message.includes('Invalid')) {
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
 * Download edited PDF
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

module.exports = {
  uploadPDF,
  editPDF,
  performOCR,
  performBatchOCR,
  downloadPDF,
  getStatus,
  getOCRStatus
};

