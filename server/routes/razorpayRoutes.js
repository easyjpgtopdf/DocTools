const express = require('express');
const router = express.Router();
const razorpayController = require('../controllers/razorpayController');

// Create a new Razorpay order
router.post('/create-order', razorpayController.createOrder);

// Verify payment signature
router.post('/verify-payment', razorpayController.verifyPayment);

// Get payment details
router.get('/payment/:paymentId', razorpayController.getPaymentDetails);

module.exports = router;
