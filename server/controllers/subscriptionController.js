/**
 * Subscription Controller
 * Manage user subscriptions and billing
 */

const User = require('../models/User');
const Organization = require('../models/Organization');
const AuditLog = require('../models/AuditLog');
const Razorpay = require('razorpay');
const { asyncHandler } = require('../middleware/errorHandler');

// Initialize Razorpay
const razorpay = new Razorpay({
  key_id: process.env.RAZORPAY_KEY_ID || '',
  key_secret: process.env.RAZORPAY_KEY_SECRET || ''
});

// Subscription plans
const SUBSCRIPTION_PLANS = {
  free: {
    name: 'Free',
    price: 0,
    pdfsPerMonth: 10,
    storageGB: 1,
    apiCallsPerMonth: 100,
    features: ['Basic PDF editing', 'OCR (limited)']
  },
  basic: {
    name: 'Basic',
    price: 3,
    priceId: process.env.RAZORPAY_PLAN_BASIC || 'plan_basic',
    pdfsPerMonth: 100,
    storageGB: 5,
    apiCallsPerMonth: 1000,
    features: ['All basic features', '100 PDFs/month', 'Email support']
  },
  pro: {
    name: 'Pro',
    price: 7,
    priceId: process.env.RAZORPAY_PLAN_PRO || 'plan_pro',
    pdfsPerMonth: 1000,
    storageGB: 20,
    apiCallsPerMonth: 10000,
    features: ['All Pro features', '1000 PDFs/month', 'API access', 'Priority support']
  },
  business: {
    name: 'Business',
    price: 299,
    priceId: process.env.RAZORPAY_PLAN_BUSINESS || 'plan_business',
    pdfsPerMonth: 10000,
    storageGB: 100,
    apiCallsPerMonth: 100000,
    features: ['All Business features', '10,000 PDFs/month', 'White label', 'Team management', 'Dedicated support']
  },
  enterprise: {
    name: 'Enterprise',
    price: 999,
    priceId: process.env.RAZORPAY_PLAN_ENTERPRISE || 'plan_enterprise',
    pdfsPerMonth: -1, // Unlimited
    storageGB: -1, // Unlimited
    apiCallsPerMonth: -1, // Unlimited
    features: ['Unlimited everything', 'Custom features', 'Dedicated support', 'SLA guarantee']
  }
};

/**
 * Get available subscription plans
 */
async function getPlans(req, res) {
  try {
    res.json({
      success: true,
      plans: SUBSCRIPTION_PLANS
    });
  } catch (error) {
    console.error('Get plans error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get plans',
      code: 'PLANS_ERROR'
    });
  }
}

/**
 * Create subscription order
 */
async function createOrder(req, res) {
  try {
    const { plan } = req.body;
    const user = await User.findById(req.userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    if (!SUBSCRIPTION_PLANS[plan]) {
      return res.status(400).json({
        success: false,
        error: 'Invalid subscription plan',
        code: 'INVALID_PLAN'
      });
    }
    
    const selectedPlan = SUBSCRIPTION_PLANS[plan];
    
    // Create Razorpay order
    const options = {
      amount: selectedPlan.price * 100, // Convert to paise
      currency: 'INR',
      receipt: `sub_${user._id}_${Date.now()}`,
      notes: {
        userId: user._id.toString(),
        plan: plan,
        email: user.email
      }
    };
    
    const order = await razorpay.orders.create(options);
    
    // Log order creation
    await AuditLog.create({
      userId: user._id,
      action: 'subscription_order_created',
      resourceType: 'payment',
      resourceId: order.id,
      details: { plan, amount: selectedPlan.price },
      ipAddress: req.ip || req.connection.remoteAddress,
      status: 'success'
    });
    
    res.json({
      success: true,
      order: {
        id: order.id,
        amount: order.amount,
        currency: order.currency,
        key: razorpay.key_id
      },
      plan: selectedPlan
    });
  } catch (error) {
    console.error('Create order error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to create order',
      code: 'ORDER_ERROR'
    });
  }
}

/**
 * Verify payment and activate subscription
 */
async function verifyPayment(req, res) {
  try {
    const { orderId, paymentId, signature, plan } = req.body;
    const user = await User.findById(req.userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    // Verify payment signature
    const crypto = require('crypto');
    const generatedSignature = crypto
      .createHmac('sha256', razorpay.key_secret)
      .update(`${orderId}|${paymentId}`)
      .digest('hex');
    
    if (generatedSignature !== signature) {
      return res.status(400).json({
        success: false,
        error: 'Invalid payment signature',
        code: 'INVALID_SIGNATURE'
      });
    }
    
    // Update user subscription
    const selectedPlan = SUBSCRIPTION_PLANS[plan];
    user.subscriptionPlan = plan;
    user.subscriptionStatus = 'active';
    user.subscriptionExpiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days
    
    // Update usage limits
    user.usageLimits = {
      pdfsPerMonth: selectedPlan.pdfsPerMonth,
      storageGB: selectedPlan.storageGB,
      apiCallsPerMonth: selectedPlan.apiCallsPerMonth
    };
    
    // Reset current usage
    user.currentUsage = {
      pdfsThisMonth: 0,
      storageUsedGB: 0,
      apiCallsThisMonth: 0
    };
    
    await user.save();
    
    // Log subscription activation
    await AuditLog.create({
      userId: user._id,
      action: 'subscription_activated',
      resourceType: 'payment',
      resourceId: paymentId,
      details: { plan, orderId, paymentId },
      ipAddress: req.ip || req.connection.remoteAddress,
      status: 'success'
    });
    
    res.json({
      success: true,
      message: 'Subscription activated successfully',
      subscription: {
        plan: user.subscriptionPlan,
        status: user.subscriptionStatus,
        expiresAt: user.subscriptionExpiresAt,
        usageLimits: user.usageLimits
      }
    });
  } catch (error) {
    console.error('Verify payment error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to verify payment',
      code: 'VERIFY_ERROR'
    });
  }
}

/**
 * Get current subscription
 */
async function getSubscription(req, res) {
  try {
    const user = await User.findById(req.userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    const plan = SUBSCRIPTION_PLANS[user.subscriptionPlan] || SUBSCRIPTION_PLANS.free;
    
    res.json({
      success: true,
      subscription: {
        plan: user.subscriptionPlan,
        planName: plan.name,
        status: user.subscriptionStatus,
        expiresAt: user.subscriptionExpiresAt,
        usageLimits: user.usageLimits,
        currentUsage: user.currentUsage,
        features: plan.features
      }
    });
  } catch (error) {
    console.error('Get subscription error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get subscription',
      code: 'SUBSCRIPTION_ERROR'
    });
  }
}

/**
 * Cancel subscription
 */
async function cancelSubscription(req, res) {
  try {
    const user = await User.findById(req.userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    user.subscriptionStatus = 'cancelled';
    await user.save();
    
    // Log cancellation
    await AuditLog.create({
      userId: user._id,
      action: 'subscription_cancelled',
      resourceType: 'payment',
      ipAddress: req.ip || req.connection.remoteAddress,
      status: 'success'
    });
    
    res.json({
      success: true,
      message: 'Subscription cancelled successfully'
    });
  } catch (error) {
    console.error('Cancel subscription error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to cancel subscription',
      code: 'CANCEL_ERROR'
    });
  }
}

module.exports = {
  getPlans: asyncHandler(getPlans),
  createOrder: asyncHandler(createOrder),
  verifyPayment: asyncHandler(verifyPayment),
  getSubscription: asyncHandler(getSubscription),
  cancelSubscription: asyncHandler(cancelSubscription)
};

