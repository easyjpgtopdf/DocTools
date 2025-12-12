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
const AuditLog = require('../models/AuditLog');
const { getPricingPlan } = require('../config/pricingConfig');

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
    // Handle OPTIONS requests for CORS preflight
    if (req.method === 'OPTIONS') {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'POST, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      return res.status(200).end();
    }
    
    if (!razorpay) {
      return res.status(503).json({
        success: false,
        error: 'Payment service unavailable',
        message: 'Razorpay is not configured. Please contact support.'
      });
    }

    const { plan, credits, amount, currency = 'USD' } = req.body;
    const userId = req.userId;
    
    if (!userId) {
      return res.status(401).json({
        success: false,
        error: 'User not authenticated',
        message: 'Please sign in to purchase credits.'
      });
    }

    // Try to get plan from config (if exists)
    const planConfig = getPricingPlan(plan);
    
    // Use config values if available, otherwise use request body
    const finalCredits = planConfig ? planConfig.credits : credits;
    const finalAmount = planConfig ? planConfig.price : amount;
    const finalCurrency = planConfig ? planConfig.currency : currency;

    if (!plan || (!finalCredits && !credits) || (!finalAmount && !amount)) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        message: 'Plan, credits, and amount are required'
      });
    }

    // Convert USD to INR (1 USD = 95 INR as per user requirement)
    const USD_TO_INR = 95;
    const amountInINR = finalCurrency === 'USD' ? finalAmount * USD_TO_INR : finalAmount;
    
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
        credits: finalCredits.toString(),
        type: 'credit_purchase'
      }
    };

    const order = await razorpay.orders.create(orderOptions);

    // Save order details to transaction (pending)
    await CreditTransaction.create({
      user_id: userId,
      type: 'purchase',
      credits_change: finalCredits,
      balance_after: 0, // Will be updated after payment
      metadata: {
        orderId: order.id,
        plan,
        amount: finalAmount,
        currency: finalCurrency
      }
    });

    res.json({
      success: true,
      order,
      key_id: process.env.RAZORPAY_KEY_ID,
      credits: finalCredits,
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
 * SECURITY: All payment data verified from Razorpay API, not from request body
 */
async function verifyPaymentAndAddCredits(req, res) {
  try {
    const {
      razorpay_payment_id,
      razorpay_order_id,
      razorpay_signature,
      orderId
    } = req.body;

    const userId = req.userId; // From JWT token - CANNOT BE FAKED

    if (!razorpay_payment_id || !razorpay_order_id || !razorpay_signature || !orderId) {
      return res.status(400).json({
        success: false,
        error: 'Missing payment details'
      });
    }

    // SECURITY CHECK 1: Verify signature (prevents fake payments)
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
      console.error(`Invalid payment signature for order ${orderId} by user ${userId}`);
      return res.status(400).json({
        success: false,
        error: 'Invalid payment signature'
      });
    }

    // SECURITY CHECK 2: Verify payment status with Razorpay API (prevents fake/unpaid orders)
    try {
      const payment = await razorpay.payments.fetch(razorpay_payment_id);
      
      if (payment.status !== 'captured' && payment.status !== 'authorized') {
        console.error(`Payment ${razorpay_payment_id} not captured. Status: ${payment.status}`);
        return res.status(400).json({
          success: false,
          error: 'Payment not successful',
          message: `Payment status: ${payment.status}`
        });
      }

      // Verify order ID matches
      if (payment.order_id !== razorpay_order_id) {
        console.error(`Order ID mismatch: ${payment.order_id} !== ${razorpay_order_id}`);
        return res.status(400).json({
          success: false,
          error: 'Order ID mismatch'
        });
      }

      // Verify amount matches (prevent amount manipulation)
      const order = await razorpay.orders.fetch(razorpay_order_id);
      if (!order) {
        return res.status(400).json({
          success: false,
          error: 'Order not found'
        });
      }
    } catch (razorpayError) {
      console.error('Razorpay API verification failed:', razorpayError);
      return res.status(400).json({
        success: false,
        error: 'Payment verification failed',
        message: 'Could not verify payment with Razorpay'
      });
    }

    // SECURITY CHECK 3: Get credits from stored transaction, NOT from request body (prevents credit manipulation)
    const existingTransaction = await CreditTransaction.findOne({
      user_id: userId,
      'metadata.orderId': orderId,
      type: 'purchase'
    });

    if (!existingTransaction) {
      console.error(`SECURITY ALERT: Transaction not found for order ${orderId} by user ${userId}`);
      // Log security event
      await AuditLog.create({
        userId: userId,
        action: 'unauthorized_credit_attempt',
        resourceType: 'security',
        details: { orderId, paymentId: razorpay_payment_id },
        ipAddress: req.ip || req.connection.remoteAddress,
        userAgent: req.headers['user-agent'],
        status: 'failure'
      });
      return res.status(400).json({
        success: false,
        error: 'Order not found',
        message: 'This order was not created by you'
      });
    }

    // SECURITY: Verify the order belongs to this user (prevent order hijacking)
    if (existingTransaction.user_id.toString() !== userId.toString()) {
      console.error(`SECURITY ALERT: User ${userId} attempted to use order ${orderId} belonging to another user`);
      await AuditLog.create({
        userId: userId,
        action: 'order_hijack_attempt',
        resourceType: 'security',
        details: { orderId, actualOwner: existingTransaction.user_id },
        ipAddress: req.ip || req.connection.remoteAddress,
        userAgent: req.headers['user-agent'],
        status: 'failure'
      });
      return res.status(403).json({
        success: false,
        error: 'Unauthorized',
        message: 'This order does not belong to you'
      });
    }

    // SECURITY CHECK 4: Prevent duplicate credit addition (check if payment already processed)
    if (existingTransaction.metadata.paymentId) {
      console.warn(`Payment ${razorpay_payment_id} already processed for order ${orderId}`);
      return res.status(400).json({
        success: false,
        error: 'Payment already processed',
        message: 'Credits for this payment have already been added'
      });
    }

    // SECURITY: Use credits from stored transaction, NOT from request body
    const creditsToAdd = existingTransaction.credits_change;
    if (!creditsToAdd || creditsToAdd <= 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid credits amount'
      });
    }

    // Get or create user credits
    const userCredits = await UserCredits.getOrCreate(userId);
    
    // Add credits (90 days expiry) - using verified amount from database
    await userCredits.addCredits(creditsToAdd, 90);

    // Get payment and order details for receipt
    const payment = await razorpay.payments.fetch(razorpay_payment_id);
    const order = await razorpay.orders.fetch(razorpay_order_id);
    
    // Update transaction with payment ID (mark as processed)
    existingTransaction.balance_after = userCredits.credits;
    existingTransaction.metadata.paymentId = razorpay_payment_id;
    existingTransaction.metadata.verifiedAt = new Date();
    existingTransaction.metadata.amount = order.amount / 100; // Convert paise to INR
    existingTransaction.metadata.currency = order.currency;
    existingTransaction.metadata.paymentDate = new Date();
    await existingTransaction.save();

    // Log successful credit addition
    console.log(`✓ Credits added: ${creditsToAdd} to user ${userId} for order ${orderId}`);

    // Get user details for receipt
    const user = await User.findById(userId);
    
    // Prepare receipt data
    const receiptData = {
      paymentId: razorpay_payment_id,
      orderId: razorpay_order_id,
      amount: order.amount / 100, // Convert paise to INR
      currency: order.currency,
      credits: creditsToAdd,
      plan: existingTransaction.metadata.plan || plan,
      paymentDate: new Date(),
      userEmail: user?.email || '',
      userName: user?.firstName && user?.lastName 
        ? `${user.firstName} ${user.lastName}` 
        : user?.email?.split('@')[0] || 'User',
      creditsBalance: userCredits.credits,
      expiresAt: userCredits.expiresAt
    };

    // Send email receipt (if email service is configured)
    try {
      await sendPaymentReceiptEmail(receiptData, user);
    } catch (emailError) {
      console.warn('Failed to send receipt email:', emailError.message);
      // Don't fail the payment if email fails
    }

    res.json({
      success: true,
      message: 'Credits added successfully',
      credits: userCredits.credits,
      expiresAt: userCredits.expiresAt,
      receipt: receiptData
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
 * SECURITY: Only allows deduction for authenticated users, prevents negative amounts
 */
async function deductCredits(req, res) {
  try {
    const { amount, tool_used, page, file_name, page_count, processor } = req.body;
    const userId = req.userId; // From JWT - CANNOT BE FAKED

    // SECURITY: Validate amount (prevent negative or zero amounts)
    if (!amount || amount <= 0 || !Number.isInteger(Number(amount))) {
      return res.status(400).json({
        success: false,
        error: 'Invalid amount',
        message: 'Amount must be a positive integer'
      });
    }

    // SECURITY: Prevent excessive credit deduction in single request
    const maxDeduction = 1000; // Max credits per single deduction
    if (amount > maxDeduction) {
      console.warn(`Excessive deduction attempt: ${amount} credits by user ${userId}`);
      return res.status(400).json({
        success: false,
        error: 'Amount too large',
        message: `Maximum ${maxDeduction} credits can be deducted per request`
      });
    }

    const userCredits = await UserCredits.getOrCreate(userId);
    
    // Check expiry
    userCredits.checkExpiry();

    if (userCredits.credits < amount) {
      return res.status(402).json({
        success: false,
        error: 'Insufficient credits',
        credits: userCredits.credits,
        required: amount,
        message: `You need ${amount} credits. You have ${userCredits.credits} credits.`
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

/**
 * Razorpay Webhook Handler
 * Additional security layer - Razorpay directly calls this on payment success
 * SECURITY: Uses raw body for signature verification
 */
async function handleRazorpayWebhook(req, res) {
  try {
    const webhookSignature = req.headers['x-razorpay-signature'];
    
    if (!webhookSignature) {
      return res.status(400).json({
        success: false,
        error: 'Missing webhook signature'
      });
    }

    // Parse raw body (it's a Buffer when using express.raw())
    const webhookBody = req.body.toString('utf8');
    
    // Verify webhook signature
    const expectedSignature = crypto
      .createHmac('sha256', process.env.RAZORPAY_KEY_SECRET)
      .update(webhookBody)
      .digest('hex');

    if (webhookSignature !== expectedSignature) {
      console.error('Invalid webhook signature');
      return res.status(400).json({
        success: false,
        error: 'Invalid webhook signature'
      });
    }

    // Parse JSON body
    const event = JSON.parse(webhookBody);
    
    // Handle payment.captured event
    if (event.event === 'payment.captured') {
      const payment = event.payload.payment.entity;
      const orderId = payment.order_id;

      // Find transaction by order ID
      const transaction = await CreditTransaction.findOne({
        'metadata.orderId': orderId,
        type: 'purchase'
      });

      if (transaction && !transaction.metadata.paymentId) {
        // Payment verified via webhook - add credits
        const userId = transaction.user_id;
        const creditsToAdd = transaction.credits_change;

        const userCredits = await UserCredits.getOrCreate(userId);
        await userCredits.addCredits(creditsToAdd, 90);

        transaction.metadata.paymentId = payment.id;
        transaction.metadata.verifiedAt = new Date();
        transaction.metadata.verifiedVia = 'webhook';
        transaction.balance_after = userCredits.credits;
        await transaction.save();

        console.log(`✓ Webhook: Credits added via webhook for order ${orderId}`);
      }
    }

    res.json({ success: true });
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({
      success: false,
      error: 'Webhook processing failed'
    });
  }
}

/**
 * Send payment receipt email
 */
async function sendPaymentReceiptEmail(receiptData, user) {
  try {
    // Check if email service is available (Resend or similar)
    const RESEND_API_KEY = process.env.RESEND_API_KEY;
    
    if (!RESEND_API_KEY || !user?.email) {
      console.log('Email service not configured or user email not available');
      return;
    }

    const Resend = require('resend');
    const resend = new Resend(RESEND_API_KEY);

    const receiptHTML = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #4361ee; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
          .receipt-details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .detail-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
          .detail-row:last-child { border-bottom: none; }
          .label { font-weight: bold; color: #666; }
          .value { color: #333; }
          .highlight { color: #4361ee; font-weight: bold; font-size: 1.2em; }
          .footer { text-align: center; margin-top: 20px; color: #999; font-size: 12px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>Payment Receipt</h1>
            <p>Thank you for your purchase!</p>
          </div>
          <div class="content">
            <p>Dear ${receiptData.userName},</p>
            <p>Your payment has been successfully processed. Here are your receipt details:</p>
            
            <div class="receipt-details">
              <div class="detail-row">
                <span class="label">Payment ID:</span>
                <span class="value">${receiptData.paymentId}</span>
              </div>
              <div class="detail-row">
                <span class="label">Order ID:</span>
                <span class="value">${receiptData.orderId}</span>
              </div>
              <div class="detail-row">
                <span class="label">Plan:</span>
                <span class="value">${receiptData.plan.toUpperCase()}</span>
              </div>
              <div class="detail-row">
                <span class="label">Amount Paid:</span>
                <span class="value highlight">${receiptData.currency} ${receiptData.amount.toFixed(2)}</span>
              </div>
              <div class="detail-row">
                <span class="label">Credits Added:</span>
                <span class="value highlight">${receiptData.credits.toLocaleString()} Credits</span>
              </div>
              <div class="detail-row">
                <span class="label">Current Balance:</span>
                <span class="value highlight">${receiptData.creditsBalance.toLocaleString()} Credits</span>
              </div>
              <div class="detail-row">
                <span class="label">Credits Expire:</span>
                <span class="value">${new Date(receiptData.expiresAt).toLocaleDateString()}</span>
              </div>
              <div class="detail-row">
                <span class="label">Payment Date:</span>
                <span class="value">${new Date(receiptData.paymentDate).toLocaleString()}</span>
              </div>
            </div>
            
            <p>Your credits have been added to your account and are ready to use!</p>
            <p>Visit your <a href="https://easyjpgtopdf.com/dashboard.html#dashboard-credits" style="color: #4361ee;">dashboard</a> to view your credit balance and transaction history.</p>
            
            <div class="footer">
              <p>This is an automated receipt. Please keep this email for your records.</p>
              <p>&copy; ${new Date().getFullYear()} easyjpgtopdf.com - All rights reserved</p>
            </div>
          </div>
        </div>
      </body>
      </html>
    `;

    await resend.emails.send({
      from: 'easyjpgtopdf <noreply@easyjpgtopdf.com>',
      to: user.email,
      subject: `Payment Receipt - ${receiptData.credits} Credits Added`,
      html: receiptHTML
    });

    console.log(`✓ Receipt email sent to ${user.email}`);
  } catch (error) {
    console.error('Error sending receipt email:', error);
    // Don't throw - email failure shouldn't break payment
  }
}

module.exports = {
  createCreditOrder,
  verifyPaymentAndAddCredits,
  getCreditBalance,
  deductCredits,
  getCreditHistory,
  trackPageVisit,
  getPageVisitHistory,
  handleRazorpayWebhook
};

