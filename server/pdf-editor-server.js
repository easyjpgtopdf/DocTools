/**
 * PDF Editor Server
 * Express server for PDF editing with:
 * - PDF text editing using pdf-lib
 * - Image insertion in PDF
 * - Google Cloud Vision OCR integration
 * - File upload handling
 * - Download edited PDF functionality
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { PDFDocument, rgb, StandardFonts } = require('pdf-lib');
const vision = require('@google-cloud/vision');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '100mb' }));
app.use(express.urlencoded({ extended: true, limit: '100mb' }));

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, 'uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage: storage,
  limits: { fileSize: 100 * 1024 * 1024 }, // 100MB limit
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf' || file.originalname.toLowerCase().endsWith('.pdf')) {
      cb(null, true);
    } else {
      cb(new Error('Only PDF files are allowed!'), false);
    }
  }
});

// Initialize Google Cloud Vision API client (will be initialized by vision-ocr module)
let visionClient = null;

// Initialize on startup
try {
  const visionOCR = require('./api/pdf-ocr/vision-ocr');
  visionClient = visionOCR.initializeVisionClient();
} catch (error) {
  console.warn('⚠ Google Cloud Vision API initialization deferred:', error.message);
  console.warn('⚠ OCR functionality will be initialized on first use');
}

/**
 * POST /api/pdf/upload
 * Upload a PDF file
 */
app.post('/api/pdf/upload', upload.single('pdfFile'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No PDF file uploaded'
      });
    }

    const filePath = req.file.path;
    const fileUrl = `/uploads/${req.file.filename}`;

    res.json({
      success: true,
      message: 'PDF uploaded successfully',
      filePath: filePath,
      pdfUrl: fileUrl,
      filename: req.file.originalname
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({
      success: false,
      error: 'Upload failed: ' + error.message
    });
  }
});

/**
 * POST /api/pdf/edit
 * Edit PDF text and insert images
 * Body: { pdfData: base64 string, edits: { textEdits: [], imageInserts: [] } }
 */
app.post('/api/pdf/edit', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const { pdfData, edits } = req.body;

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

    // Load PDF document
    const pdfDoc = await PDFDocument.load(pdfBuffer);

    // Apply text edits
    if (edits && edits.textEdits && Array.isArray(edits.textEdits)) {
      for (const textEdit of edits.textEdits) {
        const { pageIndex, x, y, text, fontSize = 12, fontName = 'Helvetica', fontColor = [0, 0, 0] } = textEdit;
        
        if (pageIndex >= 0 && pageIndex < pdfDoc.getPageCount()) {
          const page = pdfDoc.getPage(pageIndex);
          const pageHeight = page.getHeight();
          
          // Convert Y coordinate (PDF uses bottom-left origin)
          const pdfY = pageHeight - y - fontSize;
          
          // Get or embed font
          let font;
          try {
            const fontMap = {
              'Helvetica': StandardFonts.Helvetica,
              'Helvetica-Bold': StandardFonts.HelveticaBold,
              'Times-Roman': StandardFonts.TimesRoman,
              'Times-Bold': StandardFonts.TimesRomanBold,
              'Courier': StandardFonts.Courier,
              'Courier-Bold': StandardFonts.CourierBold
            };
            const standardFont = fontMap[fontName] || StandardFonts.Helvetica;
            font = await pdfDoc.embedFont(standardFont);
          } catch (e) {
            font = await pdfDoc.embedFont(StandardFonts.Helvetica);
          }
          
          // Draw text
          page.drawText(text, {
            x: x,
            y: pdfY,
            size: fontSize,
            font: font,
            color: rgb(fontColor[0], fontColor[1], fontColor[2])
          });
        }
      }
    }

    // Apply image inserts
    if (edits && edits.imageInserts && Array.isArray(edits.imageInserts)) {
      for (const imageInsert of edits.imageInserts) {
        const { pageIndex, imageData, x, y, width, height, opacity = 1.0 } = imageInsert;
        
        if (pageIndex >= 0 && pageIndex < pdfDoc.getPageCount()) {
          const page = pdfDoc.getPage(pageIndex);
          const pageHeight = page.getHeight();
          const pdfY = pageHeight - y - height;
          
          let image;
          try {
            if (imageData.startsWith('data:image/png')) {
              const base64Data = imageData.split(',')[1];
              const imageBytes = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));
              image = await pdfDoc.embedPng(imageBytes);
            } else if (imageData.startsWith('data:image/jpeg') || imageData.startsWith('data:image/jpg')) {
              const base64Data = imageData.split(',')[1];
              const imageBytes = Uint8Array.from(atob(base64Data), c => c.charCodeAt(0));
              image = await pdfDoc.embedJpg(imageBytes);
            } else {
              throw new Error('Unsupported image format');
            }
            
            page.drawImage(image, {
              x: x,
              y: pdfY,
              width: width,
              height: height,
              opacity: opacity
            });
          } catch (error) {
            console.warn('Error embedding image:', error.message);
          }
        }
      }
    }

    // Save PDF
    const pdfBytes = await pdfDoc.save();
    const editedBase64 = Buffer.from(pdfBytes).toString('base64');

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
});

/**
 * POST /api/pdf/ocr
 * Perform OCR on PDF pages using Google Cloud Vision API
 * Body: { pdfData: base64 string, pageIndex: number (optional), scale: number (optional), languageHints: array (optional) }
 */
app.post('/api/pdf/ocr', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const visionOCR = require('./api/pdf-ocr/vision-ocr');
    
    // Initialize Vision client if not already done
    if (!visionClient) {
      visionClient = visionOCR.initializeVisionClient();
      if (!visionClient) {
        return res.status(503).json({
          success: false,
          error: 'Google Cloud Vision API not initialized. Please check your service account credentials.'
        });
      }
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

    // Get client ID for rate limiting (from IP or default)
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
    
    // Handle specific error types
    let statusCode = 500;
    if (error.message.includes('Rate limit')) {
      statusCode = 429; // Too Many Requests
    } else if (error.message.includes('not initialized') || error.message.includes('credentials')) {
      statusCode = 503; // Service Unavailable
    } else if (error.message.includes('Invalid')) {
      statusCode = 400; // Bad Request
    }

    res.status(statusCode).json({
      success: false,
      error: error.message || 'OCR failed',
      code: error.code || 'OCR_ERROR'
    });
  }
});

/**
 * POST /api/pdf/ocr/batch
 * Perform OCR on multiple PDF pages
 * Body: { pdfData: base64 string, pageIndices: array, scale: number (optional), languageHints: array (optional) }
 */
app.post('/api/pdf/ocr/batch', express.json({ limit: '100mb' }), async (req, res) => {
  try {
    const visionOCR = require('./api/pdf-ocr/vision-ocr');
    
    // Initialize Vision client if not already done
    if (!visionClient) {
      visionClient = visionOCR.initializeVisionClient();
      if (!visionClient) {
        return res.status(503).json({
          success: false,
          error: 'Google Cloud Vision API not initialized'
        });
      }
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
});

/**
 * POST /api/pdf/download
 * Download edited PDF
 * Body: { pdfData: base64 string, filename: string (optional) }
 */
app.post('/api/pdf/download', express.json({ limit: '100mb' }), async (req, res) => {
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
});

/**
 * GET /api/pdf/status
 * Check server status and API availability
 */
app.get('/api/pdf/status', (req, res) => {
  res.json({
    success: true,
    server: 'running',
    visionApi: visionClient ? 'initialized' : 'not initialized',
    timestamp: new Date().toISOString()
  });
});

/**
 * GET /api/pdf/ocr/status
 * Check OCR service status
 */
app.get('/api/pdf/ocr/status', (req, res) => {
  res.json({
    success: true,
    visionApi: visionClient ? 'active' : 'inactive',
    method: visionClient ? 'Google Cloud Vision API' : 'not available'
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Server error:', error);
  res.status(error.status || 500).json({
    success: false,
    error: error.message || 'Internal server error'
  });
});

// Start server
app.listen(PORT, () => {
  console.log('\n' + '='.repeat(50));
  console.log('PDF Editor Server');
  console.log('='.repeat(50));
  console.log(`Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Status: http://localhost:${PORT}/api/pdf/status`);
  console.log(`OCR Status: http://localhost:${PORT}/api/pdf/ocr/status`);
  console.log('='.repeat(50) + '\n');
});

module.exports = app;

