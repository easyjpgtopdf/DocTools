const crypto = require('crypto');
const admin = require('firebase-admin');

const razorpayWebhookSecret = process.env.RAZORPAY_WEBHOOK_SECRET;

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

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  if (!razorpayWebhookSecret) {
    console.error('Webhook secret not configured');
    return res.status(503).json({ error: 'Webhook secret not configured' });
  }

  try {
    const signature = req.headers['x-razorpay-signature'];
    const body = JSON.stringify(req.body);

    if (!signature) {
      return res.status(400).json({ error: 'Missing signature' });
    }

    const generatedSignature = crypto
      .createHmac('sha256', razorpayWebhookSecret)
      .update(body)
      .digest('hex');

    if (generatedSignature !== signature) {
      console.error('Signature verification failed');
      return res.status(400).json({ error: 'Signature verification failed' });
    }

    const event = req.body;
    const eventType = event.event;
    const payload = event.payload || {};
    const payment = payload.payment?.entity;
    const order = payload.order?.entity;

    const orderId = payment?.order_id || order?.id;
    const paymentId = payment?.id || null;
    const status = payment?.status || order?.status;

    if (!orderId) {
      console.warn('Razorpay webhook missing order id', eventType);
      return res.status(200).json({ received: true });
    }

    if (!admin.apps.length || !admin.firestore) {
      console.warn('Firestore not initialised, skipping Razorpay webhook persistence');
      return res.status(200).json({ received: true });
    }

    const updates = {
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
      webhookEvent: eventType,
      paymentId,
      paymentStatus: status,
      razorpayPayload: event,
    };

    if (status === 'captured') {
      updates.status = 'succeeded';
    } else if (status === 'failed') {
      updates.status = 'failed';
    }

    const metadata = order?.notes || payment?.notes || {};
    const firebaseUid = metadata.firebaseUid;

    if (firebaseUid && firebaseUid !== 'anonymous') {
      const targetDoc = admin
        .firestore()
        .collection('payments')
        .doc(firebaseUid)
        .collection('records')
        .doc(orderId);

      await targetDoc.set(updates, { merge: true });
      console.log(`Webhook processed for user: ${firebaseUid}, order: ${orderId}`);
    }

    res.status(200).json({ received: true });
  } catch (error) {
    console.error('Razorpay webhook error:', error);
    res.status(500).json({ error: 'Webhook processing failed', details: error.message });
  }
}
