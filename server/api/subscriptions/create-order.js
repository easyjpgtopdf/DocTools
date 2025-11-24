/**
 * Create Razorpay Order for Subscription
 */

const Razorpay = require('razorpay');
const admin = require('firebase-admin');

// Initialize Razorpay
const razorpayKeyId = process.env.RAZORPAY_KEY_ID;
const razorpayKeySecret = process.env.RAZORPAY_KEY_SECRET;

const razorpay = razorpayKeyId && razorpayKeySecret 
  ? new Razorpay({ key_id: razorpayKeyId, key_secret: razorpayKeySecret })
  : null;

// Plan configurations (prices in USD)
const PLANS = {
  premium50: { monthly: 3, yearly: 20 },
  premium500: { monthly: 5, yearly: 50 }
};

// Currency conversion rates (update these regularly)
// Base currency is USD
const CURRENCY_RATES = {
  USD: 1,
  INR: 83.5, // 1 USD = 83.5 INR (update regularly)
  EUR: 0.92,
  GBP: 0.79,
  JPY: 150.5,
  RUB: 92.0,
  AUD: 1.52,
  CAD: 1.35,
  // Add more currencies as needed
};

/**
 * Get user's currency based on location or accept header
 */
function getUserCurrency(req) {
  // Check Accept-Language header for currency preference
  const acceptLanguage = req.headers['accept-language'] || '';
  
  // Check for currency in query params
  if (req.query.currency) {
    return req.query.currency.toUpperCase();
  }
  
  // Detect from Accept-Language header
  if (acceptLanguage.includes('en-IN') || acceptLanguage.includes('hi')) {
    return 'INR';
  }
  if (acceptLanguage.includes('en-US') || acceptLanguage.includes('en')) {
    return 'USD';
  }
  if (acceptLanguage.includes('ja')) {
    return 'JPY';
  }
  if (acceptLanguage.includes('ru')) {
    return 'RUB';
  }
  
  // Default to USD
  return 'USD';
}

/**
 * Convert price to user's currency
 */
function convertPrice(usdPrice, targetCurrency) {
  const rate = CURRENCY_RATES[targetCurrency] || 1;
  return Math.round(usdPrice * rate * 100) / 100; // Round to 2 decimal places
}

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!razorpay) {
    return res.status(503).json({ 
      error: 'Razorpay is not configured',
      details: 'Missing RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET'
    });
  }

  try {
    const { plan, billing, amount, currency, userId } = req.body;

    if (!plan || !billing || !userId) {
      return res.status(400).json({ error: 'Missing required fields: plan, billing, userId' });
    }

    // Get user's currency (auto-detect or use provided)
    const userCurrency = currency || getUserCurrency(req);
    
    // Get plan price in USD
    const planPriceUSD = PLANS[plan]?.[billing];
    if (!planPriceUSD) {
      return res.status(400).json({ error: 'Invalid plan or billing cycle' });
    }

    // Convert to user's currency
    const orderAmount = amount || convertPrice(planPriceUSD, userCurrency);
    
    // Razorpay supported currencies
    const razorpaySupportedCurrencies = ['INR', 'USD', 'EUR', 'GBP', 'JPY', 'RUB', 'AUD', 'CAD', 'SGD', 'AED', 'SAR'];
    const finalCurrency = razorpaySupportedCurrencies.includes(userCurrency) ? userCurrency : 'USD';

    // Get user info from Firebase
    let userEmail = '';
    let userName = '';
    
    if (admin.apps.length && admin.firestore) {
      try {
        const userDoc = await admin.firestore().collection('users').doc(userId).get();
        if (userDoc.exists()) {
          const userData = userDoc.data();
          userEmail = userData.email || '';
          userName = userData.name || userData.displayName || '';
        }
      } catch (error) {
        console.warn('Could not fetch user data:', error);
      }
    }

    // Create Razorpay order
    // Razorpay expects amount in smallest currency unit (paise for INR, cents for USD, etc.)
    const currencyMultiplier = finalCurrency === 'INR' ? 100 : (finalCurrency === 'JPY' ? 1 : 100);
    const orderOptions = {
      amount: Math.round(orderAmount * currencyMultiplier),
      currency: finalCurrency,
      receipt: `sub_${plan}_${billing}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      payment_capture: 1,
      notes: {
        plan: plan,
        billing: billing,
        userId: userId,
        type: 'subscription',
        originalPriceUSD: planPriceUSD,
        currency: finalCurrency,
        exchangeRate: CURRENCY_RATES[finalCurrency] || 1
      }
    };

    const order = await razorpay.orders.create(orderOptions);

    // Store order in Firestore
    if (admin.apps.length && admin.firestore) {
      try {
        await admin.firestore()
          .collection('subscription_orders')
          .doc(order.id)
          .set({
            userId: userId,
            plan: plan,
            billing: billing,
            amount: orderAmount,
            currency: currency,
            status: 'pending',
            orderId: order.id,
            receipt: order.receipt,
            createdAt: admin.firestore.FieldValue.serverTimestamp()
          });
      } catch (error) {
        console.warn('Failed to store order in Firestore:', error);
      }
    }

    res.status(200).json({
      success: true,
      orderId: order.id,
      amount: order.amount,
      currency: order.currency,
      receipt: order.receipt,
      key_id: razorpayKeyId,
      userEmail: userEmail,
      userName: userName,
      originalPriceUSD: planPriceUSD,
      convertedPrice: orderAmount,
      exchangeRate: CURRENCY_RATES[finalCurrency] || 1
    });

  } catch (error) {
    console.error('Error creating subscription order:', error);
    res.status(500).json({ 
      error: 'Failed to create order',
      details: error.message 
    });
  }
};

