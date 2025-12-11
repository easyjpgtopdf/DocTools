/**
 * Credit Routes
 * API endpoints for credit management
 * SECURITY: All routes require authentication and have rate limiting
 */

const express = require('express');
const router = express.Router();
const creditController = require('../controllers/creditController');
const { authenticate } = require('../middleware/auth');
const { apiLimiter } = require('../middleware/rateLimiter');

// All routes require authentication
router.use(authenticate);

// Strict rate limiter for payment operations
const paymentLimiter = require('express-rate-limit')({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10, // Max 10 payment attempts per 15 minutes
  message: {
    success: false,
    error: 'Too Many Payment Requests',
    message: 'Too many payment attempts. Please try again later.',
    code: 'PAYMENT_RATE_LIMIT'
  }
});

// Create Razorpay order for credit purchase
router.post('/create-order', paymentLimiter, creditController.createCreditOrder);

// Verify payment and add credits (strict rate limit)
router.post('/verify-payment', paymentLimiter, creditController.verifyPaymentAndAddCredits);

// Get credit balance
router.get('/balance', creditController.getCreditBalance);

// Deduct credits (rate limited)
router.post('/deduct', apiLimiter, creditController.deductCredits);

// Get credit transaction history
router.get('/history', creditController.getCreditHistory);

// Track page visit
router.post('/track-visit', creditController.trackPageVisit);

// Get page visit history
router.get('/visit-history', creditController.getPageVisitHistory);

// Razorpay webhook (no auth required, signature verified)
// Note: Webhook uses raw body parser, not JSON
const webhookMiddleware = express.raw({ type: 'application/json' });
router.post('/webhook', webhookMiddleware, creditController.handleRazorpayWebhook);

module.exports = router;

