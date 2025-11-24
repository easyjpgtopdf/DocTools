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

// Plan configurations
const PLANS = {
  premium50: { monthly: 5, yearly: 60 },
  premium500: { monthly: 10, yearly: 100 }
};

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
    const { plan, billing, amount, currency = 'INR', userId } = req.body;

    if (!plan || !billing || !userId) {
      return res.status(400).json({ error: 'Missing required fields: plan, billing, userId' });
    }

    // Get plan price
    const planPrice = PLANS[plan]?.[billing];
    if (!planPrice) {
      return res.status(400).json({ error: 'Invalid plan or billing cycle' });
    }

    // Use plan price if amount not provided
    const orderAmount = amount || planPrice;

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
    const orderOptions = {
      amount: Math.round(orderAmount * 100), // Convert to paise
      currency: currency,
      receipt: `sub_${plan}_${billing}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      payment_capture: 1,
      notes: {
        plan: plan,
        billing: billing,
        userId: userId,
        type: 'subscription'
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
      userName: userName
    });

  } catch (error) {
    console.error('Error creating subscription order:', error);
    res.status(500).json({ 
      error: 'Failed to create order',
      details: error.message 
    });
  }
};

