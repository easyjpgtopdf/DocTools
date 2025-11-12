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
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Check if Razorpay is configured
    if (!razorpay) {
      return res.status(503).json({ 
        error: 'Razorpay is not configured on the server.',
        details: 'Missing RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET in environment variables'
      });
    }

    const { amount, name, email, firebaseUid, currency = 'INR' } = req.body;
    
    if (!amount || !name || !email) {
      return res.status(400).json({ error: 'Missing required fields: amount, name, email' });
    }

    const orderOptions = {
      amount: Math.round(amount * 100), // Convert to paise
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

    const order = await razorpay.orders.create(orderOptions);
    
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
            amount: amount,
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
    
    res.json({
      id: order.id,
      amount: order.amount,
      currency: order.currency,
      receipt: order.receipt,
      key: razorpayKeyId || '',
      amountInPaise: order.amount
    });
    
  } catch (error) {
    console.error('Error creating Razorpay order:', error);
    res.status(500).json({ 
      error: 'Failed to create order',
      details: error.message 
    });
  }
}
