/**
 * PRICING CONFIGURATION
 * Centralized pricing configuration for easy updates
 * 
 * To add/update prices:
 * 1. Update the PRICING_PLANS object below
 * 2. Update pricing.html frontend (optional - can be dynamic)
 * 3. System will automatically work with new prices
 */

const PRICING_PLANS = {
  free: {
    name: 'Free',
    tagline: 'Free Forever',
    price: 0,
    credits: 0,
    currency: 'USD',
    tag: null,
    savings: null,
    expiryDays: null,
    features: [
      'Access to core PDF tools',
      'Standard processing speed',
      'Community support',
      'Web-based interface',
      'No credit usage',
      'No payment required'
    ]
  },
  pro: {
    name: 'PRO',
    tagline: '900 credit points',
    price: 40,
    credits: 900,
    currency: 'USD',
    tag: 'PRO',
    savings: 'Save 10%',
    expiryDays: 90,
    featured: true,
    features: [
      '900 Premium HD Background Removals',
      '1 credit = 1 HD image',
      'Credits expire after 90 days',
      'Access to all premium tools',
      'Priority processing'
    ]
  },
  proplus: {
    name: 'PRO+',
    tagline: '5000 credit points',
    price: 200,
    credits: 5000,
    currency: 'USD',
    tag: 'PRO+',
    savings: 'Best value',
    expiryDays: 90,
    features: [
      '5000 Premium HD Background Removals',
      '1 credit = 1 HD image',
      'Credits expire after 90 days',
      'Access to all premium tools',
      'Faster processing'
    ]
  },
  superpremium: {
    name: 'Super Premium',
    tagline: '11000 credit points',
    price: 400,
    credits: 11000,
    currency: 'USD',
    tag: 'Super Premium',
    savings: 'Maximum savings',
    expiryDays: 90,
    features: [
      '11000 Premium HD Background Removals',
      '1 credit = 1 HD image',
      'Credits expire after 90 days',
      'Unlimited access to all tools',
      'Dedicated support'
    ]
  }
};

/**
 * TOOL CREDIT COSTS
 * Define credit costs for each premium tool
 * 
 * To add/update tool prices:
 * 1. Add/update entry in TOOL_CREDIT_COSTS
 * 2. Use in route: deductCredits(TOOL_CREDIT_COSTS['tool-name'], 'tool-name')
 */
const TOOL_CREDIT_COSTS = {
  'background-remover-premium': 1,
  'background-remover-hd': 1,
  'pdf-ocr': 2,
  'pdf-ocr-batch': 1, // per file
  'pdf-advanced-edit': 5,
  'pdf-batch-process': 1, // per file
  'image-hd-process': 1,
  'image-ultra-hd': 3,
  'pdf-export-word': 2,
  'pdf-export-excel': 2,
  'pdf-export-powerpoint': 2,
  'pdf-export-images': 1, // per page
  'pdf-redact': 3,
  'pdf-watermark': 2,
  'pdf-signature': 2,
  'pdf-merge': 1, // per file
  'pdf-split': 1, // per file
  'pdf-compress': 1,
  'pdf-protect': 1,
  'pdf-forms-detect': 2,
  'pdf-forms-fill': 2
};

/**
 * Get pricing plan by ID
 */
function getPricingPlan(planId) {
  return PRICING_PLANS[planId] || null;
}

/**
 * Get all pricing plans
 */
function getAllPricingPlans() {
  return PRICING_PLANS;
}

/**
 * Get credit cost for a tool
 */
function getToolCreditCost(toolName) {
  return TOOL_CREDIT_COSTS[toolName] || 1; // Default: 1 credit
}

/**
 * Get all tool credit costs
 */
function getAllToolCreditCosts() {
  return TOOL_CREDIT_COSTS;
}

/**
 * Update tool credit cost (for admin use)
 */
function updateToolCreditCost(toolName, newCost) {
  if (typeof newCost !== 'number' || newCost < 0) {
    throw new Error('Credit cost must be a positive number');
  }
  TOOL_CREDIT_COSTS[toolName] = newCost;
  return true;
}

/**
 * Add new pricing plan (for admin use)
 */
function addPricingPlan(planId, planData) {
  if (PRICING_PLANS[planId]) {
    throw new Error(`Plan ${planId} already exists`);
  }
  PRICING_PLANS[planId] = planData;
  return true;
}

/**
 * Update existing pricing plan (for admin use)
 */
function updatePricingPlan(planId, updates) {
  if (!PRICING_PLANS[planId]) {
    throw new Error(`Plan ${planId} does not exist`);
  }
  PRICING_PLANS[planId] = { ...PRICING_PLANS[planId], ...updates };
  return true;
}

module.exports = {
  PRICING_PLANS,
  TOOL_CREDIT_COSTS,
  getPricingPlan,
  getAllPricingPlans,
  getToolCreditCost,
  getAllToolCreditCosts,
  updateToolCreditCost,
  addPricingPlan,
  updatePricingPlan
};

