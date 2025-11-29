/**
 * Subscription Routes
 * Subscription management and billing
 */

const express = require('express');
const router = express.Router();
const subscriptionController = require('../controllers/subscriptionController');
const { authenticate } = require('../middleware/auth');
const { apiLimiter } = require('../middleware/rateLimiter');

// Public route
router.get('/plans', apiLimiter, subscriptionController.getPlans);

// Protected routes
router.post('/order', authenticate, apiLimiter, subscriptionController.createOrder);
router.post('/verify', authenticate, apiLimiter, subscriptionController.verifyPayment);
router.get('/current', authenticate, subscriptionController.getSubscription);
router.post('/cancel', authenticate, apiLimiter, subscriptionController.cancelSubscription);

/**
 * GET /api/subscription/usage
 * Get usage tracking data (day-wise, month-wise)
 */
router.get('/usage', authenticate, apiLimiter, subscriptionController.getUsageTracking);

/**
 * POST /api/subscription/check-limit
 * Check if user has reached usage limit
 */
router.post('/check-limit', authenticate, apiLimiter, subscriptionController.checkUsageLimit);

/**
 * POST /api/subscription/increment-usage
 * Increment usage counter (called by PDF operations)
 */
router.post('/increment-usage', authenticate, apiLimiter, subscriptionController.incrementUsage);

module.exports = router;

