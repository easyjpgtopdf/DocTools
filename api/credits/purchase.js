// Vercel Serverless Function - Credit Purchase via Razorpay

const Razorpay = require('razorpay');
const admin = require('firebase-admin');

// Initialize Firebase if not already done
if (!admin.apps.length) {
  try {
    const serviceAccountRaw = process.env.FIREBASE_SERVICE_ACCOUNT;
    if (serviceAccountRaw) {
      try {
        const serviceAccount = JSON.parse(serviceAccountRaw);
        admin.initializeApp({
          credential: admin.credential.cert(serviceAccount)
        });
      } catch (parseError) {
        console.warn('Firebase service account JSON parse failed, using default');
        admin.initializeApp();
      }
    } else {
      admin.initializeApp();
    }
  } catch (error) {
    console.error('Firebase init error:', error);
  }
}

const razorpayKeyId = process.env.RAZORPAY_KEY_ID;
const razorpayKeySecret = process.env.RAZORPAY_KEY_SECRET;
const razorpayReceiptPrefix = process.env.RAZORPAY_RECEIPT_PREFIX || 'easyjpgtopdf';

const razorpay = razorpayKeyId && razorpayKeySecret 
  ? new Razorpay({ key_id: razorpayKeyId, key_secret: razorpayKeySecret })
  : null;

// Credit pack configurations
// Base prices in USD, converted to INR at $1 = ₹95, with 18% GST
const USD_TO_INR = 95;
const GST_RATE = 0.18; // 18% GST

const CREDIT_PACKS = {
  'pack-50': { 
    credits: 50, 
    priceUSD: 4, 
    priceINR: Math.round(4 * USD_TO_INR * (1 + GST_RATE)), // ₹448
    name: '50 Credits Pack',
    description: 'Perfect for regular users'
  },
  'pack-200': { 
    credits: 200, 
    priceUSD: 15, 
    priceINR: Math.round(15 * USD_TO_INR * (1 + GST_RATE)), // ₹1,682
    name: '200 Credits Pack',
    description: 'Best value for power users'
  }
};

module.exports = async function handler(req, res) {
  // Handle CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ 
      success: false,
      error: 'Method not allowed',
      message: 'Only POST requests are accepted'
    });
  }

  try {
    // Check if Razorpay is configured
    if (!razorpay) {
      console.error('Razorpay not configured');
      return res.status(503).json({ 
        success: false,
        error: 'Payment service unavailable',
        message: 'Razorpay payment gateway is not configured'
      });
    }

    const { userId, creditPack, credits, amount, amountUSD, amountINR, currency = 'INR', gstIncluded = false, gstRate = 0 } = req.body;

    if (!userId) {
      return res.status(401).json({ 
        success: false,
        error: 'User ID required',
        message: 'Please sign in to purchase credits'
      });
    }

    if (!creditPack) {
      return res.status(400).json({ 
        success: false,
        error: 'Credit pack required',
        message: 'Please select a credit pack (50 or 200 credits)'
      });
    }

    const pack = CREDIT_PACKS[creditPack];
    if (!pack) {
      return res.status(400).json({ 
        success: false,
        error: 'Invalid credit pack',
        message: 'Please select a valid credit pack'
      });
    }
    
    // Use provided amount or calculate from pack
    const finalAmount = amount || (currency === 'INR' ? pack.priceINR : pack.priceUSD);
    const baseAmount = currency === 'INR' ? pack.priceINR / (1 + GST_RATE) : pack.priceUSD;
    const gstAmount = currency === 'INR' ? finalAmount - baseAmount : 0;
    
    // Get user info for order
    let userEmail = '';
    let userName = '';
    if (admin.apps.length) {
      try {
        const db = admin.firestore();
        const userDoc = await db.collection('users').doc(userId).get();
        if (userDoc.exists) {
          const userData = userDoc.data();
          userEmail = userData.email || '';
          userName = userData.displayName || '';
        }
      } catch (e) {
        console.warn('Failed to get user info:', e);
      }
    }

    // Create Razorpay order
    const orderOptions = {
      amount: Math.round(finalAmount * 100), // Convert to paise (INR) or cents (USD)
      currency: currency,
      receipt: `${razorpayReceiptPrefix}_credit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      payment_capture: 1,
      notes: {
        userId: userId,
        creditPack: creditPack,
        credits: pack.credits,
        type: 'credit_purchase',
        name: userName,
        email: userEmail,
        amountUSD: pack.priceUSD,
        amountINR: pack.priceINR,
        baseAmount: baseAmount,
        gstAmount: gstAmount,
        gstRate: currency === 'INR' ? GST_RATE : 0,
        finalAmount: finalAmount
      }
    };

    let order;
    try {
      order = await razorpay.orders.create(orderOptions);
    } catch (razorpayError) {
      console.error('Razorpay API error:', razorpayError);
      return res.status(502).json({
        success: false,
        error: 'Payment gateway error',
        message: 'Failed to create payment order. Please try again.'
      });
    }

    // Save order to Firestore
    if (admin.apps.length) {
      try {
        const db = admin.firestore();
        await db.collection('creditOrders').doc(order.id).set({
          userId: userId,
          creditPack: creditPack,
          credits: pack.credits,
          amount: finalAmount,
          amountUSD: pack.priceUSD,
          amountINR: pack.priceINR,
          baseAmount: baseAmount,
          gstAmount: gstAmount,
          gstRate: currency === 'INR' ? GST_RATE : 0,
          currency: currency,
          status: 'created',
          orderId: order.id,
          receipt: order.receipt,
          userName: userName,
          userEmail: userEmail,
          createdAt: admin.firestore.FieldValue.serverTimestamp()
        });
        console.log(`Credit order ${order.id} saved to Firestore for user ${userId}`);
      } catch (firestoreError) {
        console.error('Failed to save credit order to Firestore:', firestoreError);
        // Continue anyway
      }
    }

    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(200).json({
      success: true,
      orderId: order.id,
      key_id: razorpayKeyId,
      amount: order.amount,
      currency: order.currency,
      credits: pack.credits,
      receipt: order.receipt
    });

  } catch (error) {
    console.error('Credit purchase error:', error);
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      message: error.message || 'Failed to create credit purchase order'
    });
  }
}

