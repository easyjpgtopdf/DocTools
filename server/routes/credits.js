/**
 * Credit Routes
 * API endpoints for credit management
 */

const express = require('express');
const router = express.Router();
const creditController = require('../controllers/creditController');
const { authenticate } = require('../middleware/auth');

// All routes require authentication
router.use(authenticate);

// Create Razorpay order for credit purchase
router.post('/create-order', creditController.createCreditOrder);

// Verify payment and add credits
router.post('/verify-payment', creditController.verifyPaymentAndAddCredits);

// Get credit balance
router.get('/balance', creditController.getCreditBalance);

// Deduct credits
router.post('/deduct', creditController.deductCredits);

// Get credit transaction history
router.get('/history', creditController.getCreditHistory);

// Track page visit
router.post('/track-visit', creditController.trackPageVisit);

// Get page visit history
router.get('/visit-history', creditController.getPageVisitHistory);

module.exports = router;

