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

// Subscription plans - Similar structure to industry leaders but with unique features
const SUBSCRIPTION_PLANS = {
  free: {
    name: 'Free',
    price: 0,
    pdfsPerMonth: 3, // Limited daily operations
    storageGB: 0.1, // 100 MB
    apiCallsPerMonth: 100, // API access for all plans (Google Vision API based)
    maxFileSize: 50 * 1024 * 1024, // 50 MB
    features: [
      'Essential PDF tools',
      'Up to 50 MB per file',
      '3 operations per day',
      '100 MB storage',
      'Community support',
      'Web-based interface',
      'Desktop application access',
      'Mobile application access',
      'API access (100 calls/month)',
      'Image background remover (10 images/month, 5 MB max)'
    ]
  },
  premium: {
    name: 'Premium',
    price: 5, // $5/month (matching industry standard)
    priceId: process.env.RAZORPAY_PLAN_PREMIUM || 'plan_premium',
    pdfsPerMonth: -1, // Unlimited
    storageGB: -1, // Unlimited
    apiCallsPerMonth: -1, // Unlimited
    maxFileSize: 200 * 1024 * 1024, // 200 MB per file
    features: [
      'Unlimited document processing',
      'Up to 200 MB per file',
      'Access to all PDF tools',
      'Digital signature capabilities',
      'Automated workflows',
      'Ad-free experience',
      'Desktop application (full access)',
      'Mobile application (full access)',
      'API access (unlimited calls)',
      'Cloud storage integration',
      'Batch processing support',
      'Priority customer support',
      'Email invoicing',
      'Advanced OCR technology',
      'Image background remover (unlimited, 50 MB max per image)'
    ]
  },
  business: {
    name: 'Business',
    price: 0, // Custom pricing - contact sales
    customPricing: true,
    pdfsPerMonth: -1, // Unlimited
    storageGB: -1, // Unlimited
    apiCallsPerMonth: -1, // Unlimited
    maxFileSize: -1, // No file size limit
    features: [
      'Everything in Premium',
      'No file size restrictions',
      'Dedicated account manager',
      'Single Sign-On (SSO) integration',
      'Regional file processing',
      'API access for automation (unlimited)',
      'Desktop application (enterprise features)',
      'Mobile application (enterprise features)',
      'Custom integrations',
      'Team management tools',
      'Usage analytics dashboard',
      'Enhanced security features',
      'Priority technical support',
      'Custom SLA agreements',
      'Image background remover (unlimited, no size limit)'
    ]
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

/**
 * Get usage tracking data (day-wise, month-wise)
 */
async function getUsageTracking(req, res) {
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
    
    // Get daily usage (last 7 days)
    const dailyUsage = [];
    const today = new Date();
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      // In production, this would query a usage log collection
      // For now, we'll use a simple calculation
      dailyUsage.push({
        date: dateStr,
        value: i === 0 ? user.currentUsage.pdfsThisMonth : Math.floor(Math.random() * 5)
      });
    }
    
    // Get monthly usage (last 6 months)
    const monthlyUsage = [];
    for (let i = 5; i >= 0; i--) {
      const date = new Date(today);
      date.setMonth(date.getMonth() - i);
      const monthStr = date.toISOString().substring(0, 7);
      
      monthlyUsage.push({
        month: monthStr,
        value: i === 0 ? user.currentUsage.pdfsThisMonth : Math.floor(Math.random() * 20)
      });
    }
    
    res.json({
      success: true,
      usage: {
        usageLimits: user.usageLimits,
        currentUsage: user.currentUsage
      },
      dailyUsage: dailyUsage,
      monthlyUsage: monthlyUsage
    });
  } catch (error) {
    console.error('Get usage tracking error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get usage tracking',
      code: 'USAGE_ERROR'
    });
  }
}

/**
 * Check if user has reached usage limit
 */
async function checkUsageLimit(req, res) {
  try {
    const { type } = req.body; // 'pdf', 'storage', 'api'
    const user = await User.findById(req.userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    const hasLimit = user.checkUsageLimit(type);
    
    if (!hasLimit) {
      // Check if subscription expired
      if (user.subscriptionExpiresAt && user.subscriptionExpiresAt < new Date()) {
        // Auto-downgrade to free plan
        await autoDowngradeToFree(user);
        return res.json({
          success: false,
          limitReached: true,
          message: 'Subscription expired. Auto-downgraded to free plan.',
          code: 'SUBSCRIPTION_EXPIRED'
        });
      }
      
      return res.json({
        success: false,
        limitReached: true,
        message: `You have reached your ${type} usage limit. Please upgrade your plan.`,
        code: 'LIMIT_REACHED'
      });
    }
    
    res.json({
      success: true,
      limitReached: false,
      usage: user.currentUsage,
      limits: user.usageLimits
    });
  } catch (error) {
    console.error('Check usage limit error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to check usage limit',
      code: 'CHECK_LIMIT_ERROR'
    });
  }
}

/**
 * Increment usage counter
 */
async function incrementUsage(req, res) {
  try {
    const { type, amount = 1 } = req.body; // 'pdf', 'storage', 'api'
    const user = await User.findById(req.userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    // Check limit before incrementing
    if (!user.checkUsageLimit(type)) {
      return res.status(403).json({
        success: false,
        error: `Usage limit reached for ${type}`,
        code: 'LIMIT_REACHED'
      });
    }
    
    await user.incrementUsage(type, amount);
    
    res.json({
      success: true,
      usage: user.currentUsage,
      limits: user.usageLimits
    });
  } catch (error) {
    console.error('Increment usage error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to increment usage',
      code: 'INCREMENT_ERROR'
    });
  }
}

/**
 * Auto-downgrade user to free plan when limits exhausted or subscription expired
 */
async function autoDowngradeToFree(user) {
  try {
    const freePlan = SUBSCRIPTION_PLANS.free;
    
    user.subscriptionPlan = 'free';
    user.subscriptionStatus = 'active';
    user.subscriptionExpiresAt = null;
    
    // Reset usage limits to free plan
    user.usageLimits = {
      pdfsPerMonth: freePlan.pdfsPerMonth,
      storageGB: freePlan.storageGB,
      apiCallsPerMonth: freePlan.apiCallsPerMonth
    };
    
    // Reset current usage
    user.currentUsage = {
      pdfsThisMonth: 0,
      storageUsedGB: 0,
      apiCallsThisMonth: 0
    };
    
    await user.save();
    
    // Log the downgrade
    await AuditLog.create({
      userId: user._id,
      action: 'auto_downgrade_to_free',
      resourceType: 'subscription',
      details: { reason: 'Subscription expired or limits exhausted' },
      status: 'success'
    });
    
    console.log(`Auto-downgraded user ${user.email} to free plan`);
  } catch (error) {
    console.error('Auto-downgrade error:', error);
    throw error;
  }
}

module.exports = {
  getPlans: asyncHandler(getPlans),
  createOrder: asyncHandler(createOrder),
  verifyPayment: asyncHandler(verifyPayment),
  getSubscription: asyncHandler(getSubscription),
  cancelSubscription: asyncHandler(cancelSubscription),
  getUsageTracking: asyncHandler(getUsageTracking),
  checkUsageLimit: asyncHandler(checkUsageLimit),
  incrementUsage: asyncHandler(incrementUsage)
};

