/**
 * Verify Razorpay Payment and Activate Subscription
 */

const Razorpay = require('razorpay');
const crypto = require('crypto');
const admin = require('firebase-admin');

// Initialize Razorpay
const razorpayKeyId = process.env.RAZORPAY_KEY_ID;
const razorpayKeySecret = process.env.RAZORPAY_KEY_SECRET;

const razorpay = razorpayKeyId && razorpayKeySecret 
  ? new Razorpay({ key_id: razorpayKeyId, key_secret: razorpayKeySecret })
  : null;

// Plan configurations (prices in USD)
const PLANS = {
  premium50: { monthly: { price: 3, duration: 30 }, yearly: { price: 20, duration: 365 } },
  premium500: { monthly: { price: 5, duration: 30 }, yearly: { price: 50, duration: 365 } }
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
    return res.status(503).json({ error: 'Razorpay is not configured' });
  }

  try {
    const { 
      razorpay_order_id, 
      razorpay_payment_id, 
      razorpay_signature,
      plan,
      billing,
      userId,
      orderId,
      currency,
      amount
    } = req.body;

    if (!razorpay_order_id || !razorpay_payment_id || !razorpay_signature || !plan || !billing || !userId) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Verify payment signature
    const text = `${razorpay_order_id}|${razorpay_payment_id}`;
    const generatedSignature = crypto
      .createHmac('sha256', razorpayKeySecret)
      .update(text)
      .digest('hex');

    if (generatedSignature !== razorpay_signature) {
      return res.status(400).json({ 
        success: false,
        error: 'Invalid payment signature' 
      });
    }

    // Get plan details
    const planDetails = PLANS[plan]?.[billing];
    if (!planDetails) {
      return res.status(400).json({ error: 'Invalid plan or billing cycle' });
    }

    // Calculate expiration date
    const now = new Date();
    const expiresAt = new Date(now.getTime() + planDetails.duration * 24 * 60 * 60 * 1000);

    // Activate subscription in Firestore
    if (admin.apps.length && admin.firestore) {
      try {
        const db = admin.firestore();
        
        // Get actual currency and amount from request (or fallback to defaults)
        const actualCurrency = currency || 'USD';
        const actualAmount = amount || planDetails.price;
        
        // Update subscription
        await db.collection('subscriptions').doc(userId).set({
          plan: plan,
          status: 'active',
          startDate: admin.firestore.Timestamp.fromDate(now),
          expiresAt: admin.firestore.Timestamp.fromDate(expiresAt),
          billing: billing,
          paymentId: razorpay_payment_id,
          orderId: razorpay_order_id,
          currency: actualCurrency, // Store actual currency used
          autopay: false,
          createdAt: admin.firestore.FieldValue.serverTimestamp(),
          updatedAt: admin.firestore.FieldValue.serverTimestamp()
        }, { merge: true });

        // Record payment with actual currency and amount
        await db.collection('payments').doc(razorpay_payment_id).set({
          userId: userId,
          plan: plan,
          amount: actualAmount, // Actual amount paid in user's currency
          currency: actualCurrency, // Actual currency used (not hardcoded)
          originalPriceUSD: planDetails.price, // Original USD price for reference
          billing: billing,
          status: 'completed',
          paymentId: razorpay_payment_id,
          orderId: razorpay_order_id,
          paymentDate: admin.firestore.FieldValue.serverTimestamp()
        });

        // Update order status
        if (orderId) {
          await db.collection('subscription_orders').doc(orderId).update({
            status: 'completed',
            paymentId: razorpay_payment_id,
            completedAt: admin.firestore.FieldValue.serverTimestamp()
          });
        }

      } catch (error) {
        console.error('Error activating subscription:', error);
        return res.status(500).json({ 
          success: false,
          error: 'Failed to activate subscription',
          details: error.message 
        });
      }
    }

    res.status(200).json({
      success: true,
      message: 'Subscription activated successfully',
      subscription: {
        plan: plan,
        billing: billing,
        expiresAt: expiresAt.toISOString()
      }
    });

  } catch (error) {
    console.error('Error verifying payment:', error);
    res.status(500).json({ 
      success: false,
      error: 'Failed to verify payment',
      details: error.message 
    });
  }
};

