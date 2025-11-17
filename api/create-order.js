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

module.exports = async function handler(req, res) {
  // Enable CORS with better headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ 
      success: false,
      error: 'Method not allowed',
      message: 'Only POST requests are accepted',
      allowedMethods: ['POST', 'OPTIONS']
    });
  }

  try {
    // Check if Razorpay is configured
    if (!razorpay) {
      console.error('Razorpay not configured - missing environment variables');
      return res.status(503).json({ 
        success: false,
        error: 'Payment service unavailable',
        message: 'Razorpay payment gateway is not configured. Please contact support.',
        details: process.env.NODE_ENV === 'development' 
          ? 'Missing RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET' 
          : undefined
      });
    }

    const { amount, name, email, firebaseUid, currency = 'INR' } = req.body;
    
    // Validate required fields
    const missingFields = [];
    if (!amount) missingFields.push('amount');
    if (!name) missingFields.push('name');
    if (!email) missingFields.push('email');
    
    if (missingFields.length > 0) {
      return res.status(400).json({ 
        success: false,
        error: 'Validation error',
        message: 'Required fields are missing',
        missingFields: missingFields
      });
    }

    // Validate amount
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid amount',
        message: 'Amount must be a positive number'
      });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid email',
        message: 'Please provide a valid email address'
      });
    }

    const orderOptions = {
      amount: Math.round(numAmount * 100), // Convert to paise
      currency: currency,
      receipt: `${razorpayReceiptPrefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      payment_capture: 1,
      notes: {
        name: name,
        email: email,
        firebaseUid: firebaseUid || 'anonymous',
        purpose: 'Donation to easyjpgtopdf'
      }
    };

    // Create Razorpay order with better error handling
    let order;
    try {
      order = await razorpay.orders.create(orderOptions);
    } catch (razorpayError) {
      console.error('Razorpay API error:', razorpayError);
      return res.status(502).json({
        success: false,
        error: 'Payment gateway error',
        message: 'Failed to create payment order. Please try again.',
        details: process.env.NODE_ENV === 'development' 
          ? razorpayError.message 
          : undefined
      });
    }
    
    // Save initial order record to Firestore if user is logged in
    if (firebaseUid && firebaseUid !== 'anonymous' && admin.apps.length) {
      try {
        const db = admin.firestore();
        await db.collection('payments')
          .doc(firebaseUid)
          .collection('records')
          .doc(order.id)
          .set({
            orderId: order.id,
            amount: numAmount,
            currency: currency,
            status: 'pending',
            paymentStatus: 'created',
            method: 'razorpay',
            name: name,
            email: email,
            createdAt: admin.firestore.FieldValue.serverTimestamp(),
            updatedAt: admin.firestore.FieldValue.serverTimestamp()
          });
        console.log(`Order ${order.id} saved to Firestore for user ${firebaseUid}`);
      } catch (firestoreError) {
        console.error('Failed to save order to Firestore:', firestoreError);
        // Continue anyway - webhook will handle it
      }
    }
    
    // Success response
    return res.status(200).json({
      success: true,
      message: 'Payment order created successfully',
      data: {
        id: order.id,
        amount: order.amount,
        currency: order.currency,
        receipt: order.receipt,
        key: razorpayKeyId || '',
        amountInPaise: order.amount,
        amountInRupees: numAmount
      }
    });
    
  } catch (error) {
    console.error('Unexpected error creating Razorpay order:', error);
    return res.status(500).json({ 
      success: false,
      error: 'Internal server error',
      message: 'An unexpected error occurred while processing your request',
      details: process.env.NODE_ENV === 'development' 
        ? error.message 
        : 'Please try again or contact support if the problem persists'
    });
  }
}
