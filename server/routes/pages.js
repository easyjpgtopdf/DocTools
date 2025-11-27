/**
 * PDF Page Management Routes
 * Handles page operations (rotate, delete, reorder, extract, add)
 */

const express = require('express');
const router = express.Router();
const pagesController = require('../controllers/pagesController');

/**
 * POST /api/pdf/pages/rotate
 * Rotate pages in PDF
 */
router.post('/rotate', express.json({ limit: '100mb' }), pagesController.rotatePages);

/**
 * POST /api/pdf/pages/delete
 * Delete pages from PDF
 */
router.post('/delete', express.json({ limit: '100mb' }), pagesController.deletePages);

/**
 * POST /api/pdf/pages/reorder
 * Reorder pages in PDF
 */
router.post('/reorder', express.json({ limit: '100mb' }), pagesController.reorderPages);

/**
 * POST /api/pdf/pages/extract
 * Extract pages from PDF
 */
router.post('/extract', express.json({ limit: '100mb' }), pagesController.extractPages);

/**
 * POST /api/pdf/pages/add
 * Add new page to PDF
 */
router.post('/add', express.json({ limit: '100mb' }), pagesController.addPage);

module.exports = router;

