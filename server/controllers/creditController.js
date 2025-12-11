/**
 * Credit Controller
 * Handles credit purchases, deductions, history, and balance
 */

const Razorpay = require('razorpay');
const crypto = require('crypto');
const UserCredits = require('../models/UserCredits');
const CreditTransaction = require('../models/CreditTransaction');
const PageVisit = require('../models/PageVisit');
const User = require('../models/User');

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

/**
 * Create Razorpay order for credit purchase
 */
async function createCreditOrder(req, res) {
  try {
    if (!razorpay) {
      return res.status(503).json({
        success: false,
        error: 'Payment service unavailable',
        message: 'Razorpay is not configured. Please contact support.'
      });
    }

    const { plan, credits, amount, currency = 'USD' } = req.body;
    const userId = req.userId;

    if (!plan || !credits || !amount) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        message: 'Plan, credits, and amount are required'
      });
    }

    // Convert USD to INR (1 USD = 95 INR as per user requirement)
    const USD_TO_INR = 95;
    const amountInINR = currency === 'USD' ? amount * USD_TO_INR : amount;
    
    // Convert amount to paise (Razorpay expects amount in smallest currency unit)
    const amountInPaise = Math.round(amountInINR * 100);

    const orderOptions = {
      amount: amountInPaise,
      currency: 'INR', // Razorpay primarily uses INR
      receipt: `credit_${plan}_${Date.now()}`,
      payment_capture: 1,
      notes: {
        userId: userId.toString(),
        plan,
        credits: credits.toString(),
        type: 'credit_purchase'
      }
    };

    const order = await razorpay.orders.create(orderOptions);

    // Save order details to transaction (pending)
    await CreditTransaction.create({
      user_id: userId,
      type: 'purchase',
      credits_change: credits,
      balance_after: 0, // Will be updated after payment
      metadata: {
        orderId: order.id,
        plan,
        amount,
        currency
      }
    });

    res.json({
      success: true,
      order,
      key_id: process.env.RAZORPAY_KEY_ID,
      credits,
      plan
    });
  } catch (error) {
    console.error('Error creating credit order:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to create order',
      message: error.message
    });
  }
}

/**
 * Verify payment and add credits
 */
async function verifyPaymentAndAddCredits(req, res) {
  try {
    const {
      razorpay_payment_id,
      razorpay_order_id,
      razorpay_signature,
      orderId,
      plan,
      credits,
      amount
    } = req.body;

    const userId = req.userId;

    if (!razorpay_payment_id || !razorpay_order_id || !razorpay_signature) {
      return res.status(400).json({
        success: false,
        error: 'Missing payment details'
      });
    }

    // Verify signature
    if (!process.env.RAZORPAY_KEY_SECRET) {
      console.error('RAZORPAY_KEY_SECRET not configured');
      return res.status(500).json({
        success: false,
        error: 'Payment verification service not configured'
      });
    }

    const text = `${razorpay_order_id}|${razorpay_payment_id}`;
    const generatedSignature = crypto
      .createHmac('sha256', process.env.RAZORPAY_KEY_SECRET)
      .update(text)
      .digest('hex');

    if (generatedSignature !== razorpay_signature) {
      return res.status(400).json({
        success: false,
        error: 'Invalid payment signature'
      });
    }

    // Get or create user credits
    const userCredits = await UserCredits.getOrCreate(userId);
    
    // Add credits (90 days expiry)
    await userCredits.addCredits(parseInt(credits), 90);

    // Update transaction
    const transaction = await CreditTransaction.findOne({
      user_id: userId,
      'metadata.orderId': orderId,
      type: 'purchase'
    });

    if (transaction) {
      transaction.credits_change = parseInt(credits);
      transaction.balance_after = userCredits.credits;
      transaction.metadata.paymentId = razorpay_payment_id;
      await transaction.save();
    } else {
      // Create new transaction if not found
      await CreditTransaction.create({
        user_id: userId,
        type: 'purchase',
        credits_change: parseInt(credits),
        balance_after: userCredits.credits,
        metadata: {
          orderId,
          paymentId: razorpay_payment_id,
          plan,
          amount: parseFloat(amount),
          currency: 'USD'
        }
      });
    }

    // Send email receipt (if email service is configured)
    // TODO: Integrate with email service

    res.json({
      success: true,
      message: 'Credits added successfully',
      credits: userCredits.credits,
      expiresAt: userCredits.expiresAt
    });
  } catch (error) {
    console.error('Error verifying payment:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to verify payment',
      message: error.message
    });
  }
}

/**
 * Get user credit balance
 */
async function getCreditBalance(req, res) {
  try {
    const userId = req.userId;

    // Check if MongoDB is connected
    const mongoose = require('mongoose');
    if (mongoose.connection.readyState !== 1) {
      // MongoDB not connected - return default values
      return res.json({
        success: true,
        credits: 0,
        expiresAt: null,
        lastUsedAt: null,
        isExpired: false
      });
    }

    const userCredits = await UserCredits.getOrCreate(userId);
    
    // Check expiry
    userCredits.checkExpiry();

    res.json({
      success: true,
      credits: userCredits.credits,
      expiresAt: userCredits.expiresAt,
      lastUsedAt: userCredits.lastUsedAt,
      isExpired: userCredits.isExpired
    });
  } catch (error) {
    console.error('Error getting credit balance:', error);
    // Return default values instead of error to not break frontend
    res.json({
      success: true,
      credits: 0,
      expiresAt: null,
      lastUsedAt: null,
      isExpired: false
    });
  }
}

/**
 * Deduct credits
 */
async function deductCredits(req, res) {
  try {
    const { amount, tool_used, page, file_name, page_count, processor } = req.body;
    const userId = req.userId;

    if (!amount || amount <= 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid amount'
      });
    }

    const userCredits = await UserCredits.getOrCreate(userId);
    
    // Check expiry
    userCredits.checkExpiry();

    if (userCredits.credits < amount) {
      return res.status(400).json({
        success: false,
        error: 'Insufficient credits',
        credits: userCredits.credits,
        required: amount
      });
    }

    // Deduct credits
    await userCredits.deductCredits(amount);

    // Record transaction
    await CreditTransaction.create({
      user_id: userId,
      type: 'deduct',
      credits_change: -amount,
      balance_after: userCredits.credits,
      metadata: {
        tool_used,
        page,
        file_name,
        page_count,
        processor
      }
    });

    // Record page visit
    if (page) {
      await PageVisit.recordVisit(userId, page, tool_used, amount);
    }

    res.json({
      success: true,
      credits: userCredits.credits,
      message: 'Credits deducted successfully'
    });
  } catch (error) {
    console.error('Error deducting credits:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to deduct credits',
      message: error.message
    });
  }
}

/**
 * Get credit transaction history
 */
async function getCreditHistory(req, res) {
  try {
    const userId = req.userId;
    const limit = parseInt(req.query.limit) || 50;
    const offset = parseInt(req.query.offset) || 0;

    // Check if MongoDB is connected
    const mongoose = require('mongoose');
    if (mongoose.connection.readyState !== 1) {
      return res.json({
        success: true,
        transactions: [],
        count: 0
      });
    }

    const transactions = await CreditTransaction.find({ user_id: userId })
      .sort({ createdAt: -1 })
      .limit(limit)
      .skip(offset)
      .lean();

    res.json({
      success: true,
      transactions,
      count: transactions.length
    });
  } catch (error) {
    console.error('Error getting credit history:', error);
    // Return empty array instead of error
    res.json({
      success: true,
      transactions: [],
      count: 0
    });
  }
}

/**
 * Track page visit
 */
async function trackPageVisit(req, res) {
  try {
    const { page, tool_used, credits_spent } = req.body;
    const userId = req.userId;

    if (!page) {
      return res.status(400).json({
        success: false,
        error: 'Page is required'
      });
    }

    await PageVisit.recordVisit(userId, page, tool_used || null, credits_spent || 0);

    res.json({
      success: true,
      message: 'Visit recorded'
    });
  } catch (error) {
    console.error('Error tracking page visit:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to track visit',
      message: error.message
    });
  }
}

/**
 * Get page visit history
 */
async function getPageVisitHistory(req, res) {
  try {
    const userId = req.userId;
    const limit = parseInt(req.query.limit) || 50;

    const visits = await PageVisit.find({ user_id: userId })
      .sort({ last_visited: -1 })
      .limit(limit)
      .lean();

    res.json({
      success: true,
      visits,
      count: visits.length
    });
  } catch (error) {
    console.error('Error getting page visit history:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get visit history',
      message: error.message
    });
  }
}

module.exports = {
  createCreditOrder,
  verifyPaymentAndAddCredits,
  getCreditBalance,
  deductCredits,
  getCreditHistory,
  trackPageVisit,
  getPageVisitHistory
};

