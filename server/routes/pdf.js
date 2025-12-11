/**
 * PDF API Routes
 * Handles all PDF-related endpoints
 */

const express = require('express');
const router = express.Router();
const pdfController = require('../controllers/pdfController');
const { uploadPDF, handleUploadError } = require('../middleware/upload');
const { errorHandler, asyncHandler } = require('../middleware/errorHandler');
const { apiLimiter, ocrLimiter, uploadLimiter } = require('../middleware/rateLimiter');
const { deductCredits } = require('../middleware/creditDeduct');
const { authenticate } = require('../middleware/auth');

/**
 * POST /api/pdf/upload
 * Upload a PDF file
 */
router.post('/upload', uploadLimiter, uploadPDF, handleUploadError, asyncHandler(pdfController.uploadPDF));

/**
 * POST /api/pdf/edit
 * Edit PDF (text, images, etc.)
 */
router.post('/edit', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.editPDF));

/**
 * POST /api/pdf/edit-text
 * Edit PDF text specifically
 */
router.post('/edit-text', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.editText));

/**
 * POST /api/pdf/ocr
 * Perform OCR on PDF page
 */
router.post('/ocr', ocrLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.performOCR));

/**
 * POST /api/pdf/ocr/batch
 * Perform OCR on multiple PDF pages
 */
router.post('/ocr/batch', ocrLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.performBatchOCR));

/**
 * GET /api/pdf/ocr/status/:jobId
 * Get OCR job status
 */
router.get('/ocr/status/:jobId', pdfController.getOCRJobStatus);

/**
 * POST /api/pdf/download
 * Download edited PDF (legacy endpoint)
 */
router.post('/download', express.json({ limit: '100mb' }), pdfController.downloadPDF);

/**
 * GET /api/pdf/download/:id
 * Download edited PDF by file ID
 */
router.get('/download/:id', pdfController.downloadPDFById);

/**
 * GET /api/pdf/load/:id
 * Load PDF by file ID
 */
router.get('/load/:id', pdfController.loadPDF);

/**
 * GET /api/pdf/status
 * Check server and API status
 */
router.get('/status', pdfController.getStatus);

/**
 * GET /api/pdf/ocr/status
 * Check OCR service status
 */
router.get('/ocr/status', pdfController.getOCRStatus);

/**
 * POST /api/pdf/search
 * Search text in PDF
 */
router.post('/search', apiLimiter, express.json({ limit: '10mb' }), asyncHandler(pdfController.searchText));

/**
 * POST /api/pdf/replace-all
 * Find and replace all occurrences of text
 */
router.post('/replace-all', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.replaceAllText));

/**
 * POST /api/pdf/compress
 * Compress PDF file
 */
router.post('/compress', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.compressPDF));

/**
 * POST /api/pdf/protect
 * Protect PDF with password
 */
router.post('/protect', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.protectPDF));

/**
 * POST /api/pdf/forms/detect
 * Detect form fields in PDF
 */
router.post('/forms/detect', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.detectFormFields));

/**
 * POST /api/pdf/forms/fill
 * Fill form fields in PDF
 */
router.post('/forms/fill', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.fillFormFields));

/**
 * POST /api/pdf/pages/rotate
 * Rotate pages in PDF
 */
router.post('/pages/rotate', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.rotatePages));

/**
 * POST /api/pdf/pages/delete
 * Delete pages from PDF
 */
router.post('/pages/delete', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.deletePages));

/**
 * POST /api/pdf/pages/reorder
 * Reorder pages in PDF
 */
router.post('/pages/reorder', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.reorderPages));

/**
 * POST /api/pdf/pages/extract
 * Extract pages from PDF
 */
router.post('/pages/extract', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.extractPages));

/**
 * POST /api/pdf/pages/add
 * Add new page to PDF
 */
router.post('/pages/add', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.addPage));

/**
 * POST /api/pdf/export/word
 * Export PDF to Word (DOCX)
 * Credit: 0.5 credits per page (text), 1 credit per page (OCR)
 * Note: Credit deduction is dynamic based on PDF type and pages
 */
router.post('/export/word', 
  apiLimiter, 
  authenticate,  // User must be logged in for credit deduction
  express.json({ limit: '100mb' }), 
  asyncHandler(pdfController.exportToWord)
);

/**
 * POST /api/pdf/export/excel
 * Export PDF to Excel (XLSX)
 */
router.post('/export/excel', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.exportToExcel));

/**
 * POST /api/pdf/export/powerpoint
 * Export PDF to PowerPoint (PPTX)
 */
router.post('/export/powerpoint', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.exportToPowerPoint));

/**
 * POST /api/pdf/export/images
 * Export PDF pages to images
 */
router.post('/export/images', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.exportToImages));

/**
 * POST /api/pdf/redact
 * Redact text/images from PDF
 */
router.post('/redact', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.redactPDF));

/**
 * POST /api/pdf/watermark
 * Add watermark to PDF
 */
router.post('/watermark', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.addWatermark));

/**
 * POST /api/pdf/signature
 * Add digital signature to PDF
 */
router.post('/signature', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.addSignature));

/**
 * POST /api/pdf/merge
 * Merge multiple PDFs
 */
router.post('/merge', apiLimiter, express.json({ limit: '200mb' }), asyncHandler(pdfController.mergePDFs));

/**
 * POST /api/pdf/split
 * Split PDF into multiple files
 */
router.post('/split', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.splitPDF));

/**
 * POST /api/pdf/save-cloud
 * Save PDF to cloud storage
 */
router.post('/save-cloud', apiLimiter, express.json({ limit: '100mb' }), asyncHandler(pdfController.saveToCloud));

module.exports = router;

