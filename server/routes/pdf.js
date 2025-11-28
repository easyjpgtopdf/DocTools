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

module.exports = router;

