const express = require('express');
const router = express.Router();
const razorpayController = require('../controllers/razorpayController');

// Middleware for webhook (must be raw body)
const webhookMiddleware = express.raw({ type: 'application/json' });

// Create a new Razorpay order
router.post('/create-order', razorpayController.createOrder);

// Verify payment signature
router.post('/verify-payment', razorpayController.verifyPayment);

// Get payment details
router.get('/payment/:paymentId', razorpayController.getPaymentDetails);

// Razorpay webhook endpoint (for subscription events)
// Note: Webhook must use raw body parser, not JSON
router.post('/webhook', webhookMiddleware, razorpayController.handleWebhook);

module.exports = router;
