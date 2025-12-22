const Razorpay = require('razorpay');
const crypto = require('crypto');
const { convertPrice, isRazorpaySupported, getCurrencySymbol } = require('../config/pricingConfig');
const { detectUserCurrency } = require('../utils/currencyDetector');

// Initialize Razorpay (only if keys are available)
let razorpay = null;
if (process.env.RAZORPAY_KEY_ID && process.env.RAZORPAY_KEY_SECRET) {
  try {
    razorpay = new Razorpay({
      key_id: process.env.RAZORPAY_KEY_ID,
      key_secret: process.env.RAZORPAY_KEY_SECRET
    });
  } catch (error) {
    console.error('Failed to initialize Razorpay:', error);
  }
}

// Create a new order (for donations and general payments)
const createOrder = async (req, res) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    return res.status(200).end();
  }

  try {
    const { amount, currency, receipt, name, email, firebaseUid, donationType } = req.body;
    
    if (!amount) {
      return res.status(400).json({ 
        success: false, 
        message: 'Amount is required' 
      });
    }

    // Detect user currency if not provided
    let userCurrency = currency || detectUserCurrency(req);
    
    // Validate and convert amount if needed
    let finalCurrency = userCurrency;
    let finalAmount = parseFloat(amount);

    // If amount is in USD but currency is different, convert
    if (currency && currency !== userCurrency) {
      // Amount is already in requested currency
      finalCurrency = currency;
    } else if (!currency) {
      // No currency specified - assume amount is in user's currency
      finalCurrency = userCurrency;
    }

    // Check if currency is supported by Razorpay
    if (!isRazorpaySupported(finalCurrency)) {
      console.warn(`Currency ${finalCurrency} not supported by Razorpay, falling back to INR`);
      finalCurrency = 'INR';
      // Convert to INR if amount was in different currency
      if (userCurrency !== 'INR') {
        finalAmount = convertPrice(finalAmount, 'INR');
      }
    }

    // Convert amount to smallest currency unit
    const currencyMultipliers = {
      'INR': 100,  // 1 INR = 100 paise
      'USD': 100,  // 1 USD = 100 cents
      'EUR': 100,  // 1 EUR = 100 cents
      'GBP': 100,  // 1 GBP = 100 pence
      'JPY': 1,    // 1 JPY = 1 yen (no smaller unit)
      'AUD': 100,
      'CAD': 100,
      'SGD': 100,
      'AED': 100,
      'SAR': 100,
      'RUB': 100
    };

    const multiplier = currencyMultipliers[finalCurrency] || 100;
    const amountInSmallestUnit = Math.round(finalAmount * multiplier);

    // Generate receipt ID
    const receiptId = receipt || `donation_${Date.now()}`;

    const options = {
      amount: amountInSmallestUnit,
      currency: finalCurrency,
      receipt: receiptId,
      payment_capture: 1, // Auto capture payment
      notes: {
        type: donationType || 'donation',
        name: name || '',
        email: email || '',
        firebaseUid: firebaseUid || '',
        originalAmount: amount.toString(),
        originalCurrency: currency || userCurrency
      }
    };

    if (!razorpay) {
      return res.status(503).json({
        success: false,
        message: 'Payment service not configured'
      });
    }
    
    const order = await razorpay.orders.create(options);
    
    // Return response in format expected by donate.js
    res.status(200).json({
      success: true,
      data: {
        id: order.id,
        amount: order.amount,
        currency: order.currency,
        receipt: order.receipt,
        status: order.status,
        created_at: order.created_at,
        key: process.env.RAZORPAY_KEY_ID, // Required by donate.js
        key_id: process.env.RAZORPAY_KEY_ID
      },
      // Also include direct properties for compatibility
      id: order.id,
      amount: order.amount,
      currency: order.currency,
      key_id: process.env.RAZORPAY_KEY_ID,
      key: process.env.RAZORPAY_KEY_ID
    });

  } catch (error) {
    console.error('Error creating Razorpay order:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to create order',
      error: error.message
    });
  }
};

// Verify payment signature
const verifyPayment = (req, res) => {
  try {
    const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = req.body;
    
    const text = `${razorpay_order_id}|${razorpay_payment_id}`;
    const generatedSignature = crypto
      .createHmac('sha256', process.env.RAZORPAY_KEY_SECRET)
      .update(text)
      .digest('hex');

    const isSignatureValid = generatedSignature === razorpay_signature;

    if (isSignatureValid) {
      // Payment is successful
      // Here you can update your database, send confirmation email, etc.
      
      return res.status(200).json({
        success: true,
        message: 'Payment verified successfully',
        orderId: razorpay_order_id,
        paymentId: razorpay_payment_id
      });
    } else {
      return res.status(400).json({
        success: false,
        message: 'Invalid signature'
      });
    }
  } catch (error) {
    console.error('Error verifying payment:', error);
    res.status(500).json({
      success: false,
      message: 'Error verifying payment',
      error: error.message
    });
  }
};

// Get payment details
const getPaymentDetails = async (req, res) => {
  try {
    const { paymentId } = req.params;
    
    if (!razorpay) {
      return res.status(503).json({
        success: false,
        message: 'Payment service not configured'
      });
    }
    
    const payment = await razorpay.payments.fetch(paymentId);
    
    res.status(200).json({
      success: true,
      payment
    });
    
  } catch (error) {
    console.error('Error fetching payment details:', error);
    res.status(500).json({
      success: false,
      message: 'Error fetching payment details',
      error: error.message
    });
  }
};

// Handle Razorpay webhook events
const handleWebhook = async (req, res) => {
  try {
    const webhookSignature = req.headers['x-razorpay-signature'];
    const webhookSecret = process.env.RAZORPAY_WEBHOOK_SECRET || process.env.RAZORPAY_KEY_SECRET;
    
    // Parse raw body (it's a Buffer when using express.raw())
    const bodyString = req.body.toString('utf8');
    const body = JSON.parse(bodyString);
    
    // Verify webhook signature
    const crypto = require('crypto');
    const generatedSignature = crypto
      .createHmac('sha256', webhookSecret)
      .update(bodyString)
      .digest('hex');
    
    if (generatedSignature !== webhookSignature) {
      console.error('Invalid webhook signature');
      return res.status(400).json({ success: false, error: 'Invalid signature' });
    }
    
    const event = body.event;
    const payload = body.payload;
    
    console.log('Razorpay webhook event:', event);
    
    // Handle different webhook events
    switch (event) {
      case 'payment.captured':
        await handlePaymentCaptured(payload.payment.entity);
        break;
      case 'payment.failed':
        await handlePaymentFailed(payload.payment.entity);
        break;
      case 'subscription.activated':
        await handleSubscriptionActivated(payload.subscription.entity);
        break;
      case 'subscription.cancelled':
        await handleSubscriptionCancelled(payload.subscription.entity);
        break;
      case 'subscription.charged':
        await handleSubscriptionCharged(payload.subscription.entity);
        break;
      default:
        console.log('Unhandled webhook event:', event);
    }
    
    res.status(200).json({ success: true, received: true });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ success: false, error: error.message });
  }
};

// Handle payment captured
async function handlePaymentCaptured(payment) {
  try {
    const User = require('../models/User');
    const AuditLog = require('../models/AuditLog');
    
    // Find user by payment notes
    const userId = payment.notes?.userId;
    if (!userId) {
      console.warn('No userId in payment notes');
      return;
    }
    
    const user = await User.findById(userId);
    if (!user) {
      console.warn('User not found:', userId);
      return;
    }
    
    // Update subscription based on payment amount
    const plan = payment.notes?.plan || 'basic';
    user.subscriptionPlan = plan;
    user.subscriptionStatus = 'active';
    user.subscriptionExpiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days
    
    await user.save();
    
    // Log event
    await AuditLog.create({
      userId: user._id,
      action: 'payment_captured',
      resourceType: 'payment',
      resourceId: payment.id,
      details: { amount: payment.amount, currency: payment.currency, plan },
      status: 'success'
    });
    
    console.log('Payment captured and subscription activated for user:', userId);
  } catch (error) {
    console.error('Error handling payment captured:', error);
  }
}

// Handle payment failed
async function handlePaymentFailed(payment) {
  try {
    const AuditLog = require('../models/AuditLog');
    const userId = payment.notes?.userId;
    
    if (userId) {
      await AuditLog.create({
        userId: userId,
        action: 'payment_failed',
        resourceType: 'payment',
        resourceId: payment.id,
        details: { amount: payment.amount, error: payment.error_description },
        status: 'failed'
      });
    }
  } catch (error) {
    console.error('Error handling payment failed:', error);
  }
}

// Handle subscription activated
async function handleSubscriptionActivated(subscription) {
  try {
    const User = require('../models/User');
    const userId = subscription.customer_id;
    
    const user = await User.findOne({ email: subscription.customer_email });
    if (user) {
      user.subscriptionStatus = 'active';
      user.subscriptionExpiresAt = new Date(subscription.end_at * 1000);
      await user.save();
    }
  } catch (error) {
    console.error('Error handling subscription activated:', error);
  }
}

// Handle subscription cancelled
async function handleSubscriptionCancelled(subscription) {
  try {
    const User = require('../models/User');
    const user = await User.findOne({ email: subscription.customer_email });
    if (user) {
      user.subscriptionStatus = 'cancelled';
      await user.save();
    }
  } catch (error) {
    console.error('Error handling subscription cancelled:', error);
  }
}

// Handle subscription charged
async function handleSubscriptionCharged(subscription) {
  try {
    const User = require('../models/User');
    const user = await User.findOne({ email: subscription.customer_email });
    if (user) {
      user.subscriptionExpiresAt = new Date(subscription.end_at * 1000);
      await user.save();
    }
  } catch (error) {
    console.error('Error handling subscription charged:', error);
  }
}

module.exports = {
  createOrder,
  verifyPayment,
  getPaymentDetails,
  handleWebhook
};
