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

module.exports = router;

