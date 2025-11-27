/**
 * PDF API Routes
 * Handles all PDF-related endpoints
 */

const express = require('express');
const router = express.Router();
const pdfController = require('../controllers/pdfController');
const { uploadPDF, handleUploadError } = require('../middleware/upload');

/**
 * POST /api/pdf/upload
 * Upload a PDF file
 */
router.post('/upload', uploadPDF, handleUploadError, pdfController.uploadPDF);

/**
 * POST /api/pdf/edit
 * Edit PDF (text, images, etc.)
 */
router.post('/edit', express.json({ limit: '100mb' }), pdfController.editPDF);

/**
 * POST /api/pdf/edit-text
 * Edit PDF text specifically
 */
router.post('/edit-text', express.json({ limit: '100mb' }), pdfController.editText);

/**
 * POST /api/pdf/ocr
 * Perform OCR on PDF page
 */
router.post('/ocr', express.json({ limit: '100mb' }), pdfController.performOCR);

/**
 * POST /api/pdf/ocr/batch
 * Perform OCR on multiple PDF pages
 */
router.post('/ocr/batch', express.json({ limit: '100mb' }), pdfController.performBatchOCR);

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
 * GET /api/pdf/status
 * Check server and API status
 */
router.get('/status', pdfController.getStatus);

/**
 * GET /api/pdf/ocr/status
 * Check OCR service status
 */
router.get('/ocr/status', pdfController.getOCRStatus);

module.exports = router;

