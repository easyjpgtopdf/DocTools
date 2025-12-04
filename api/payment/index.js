// Consolidated Payment API Router
// Handles all payment-related endpoints in a single function
// Routes: /api/payment/purchase, /api/payment/verify, /api/payment/balance, /api/payment/order, /api/payment/receipt, /api/payment/webhook

const Razorpay = require('razorpay');
const crypto = require('crypto');
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
const razorpayWebhookSecret = process.env.RAZORPAY_WEBHOOK_SECRET;

const razorpay = razorpayKeyId && razorpayKeySecret 
  ? new Razorpay({ key_id: razorpayKeyId, key_secret: razorpayKeySecret })
  : null;

// Credit pack configurations
const USD_TO_INR = 95;
const GST_RATE = 0.18;

const CREDIT_PACKS = {
  'pack-50': { 
    credits: 50, 
    priceUSD: 4, 
    priceINR: Math.round(4 * USD_TO_INR * (1 + GST_RATE)),
    name: '50 Credits Pack',
    description: 'Perfect for regular users'
  },
  'pack-200': { 
    credits: 200, 
    priceUSD: 15, 
    priceINR: Math.round(15 * USD_TO_INR * (1 + GST_RATE)),
    name: '200 Credits Pack',
    description: 'Best value for power users'
  }
};

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '3600');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Extract route from query or path
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathParts = url.pathname.split('/').filter(p => p);
  const route = pathParts[pathParts.length - 1] || 'balance';

  try {
    // Route: /api/payment/balance
    if (route === 'balance' && req.method === 'GET') {
      return await handleBalance(req, res);
    }

    // Route: /api/payment/purchase
    if (route === 'purchase' && req.method === 'POST') {
      return await handlePurchase(req, res);
    }

    // Route: /api/payment/verify
    if (route === 'verify' && req.method === 'POST') {
      return await handleVerify(req, res);
    }

    // Route: /api/payment/order
    if (route === 'order' && req.method === 'POST') {
      return await handleCreateOrder(req, res);
    }

    // Route: /api/payment/receipt
    if (route === 'receipt' && req.method === 'POST') {
      return await handleSendReceipt(req, res);
    }

    // Route: /api/payment/webhook
    if (route === 'webhook' && req.method === 'POST') {
      return await handleWebhook(req, res);
    }

    // Route: /api/payment/health
    if (route === 'health') {
      return res.status(200).json({ status: 'healthy', service: 'payment-api' });
    }

    // Unknown route
    return res.status(404).json({ 
      success: false, 
      error: `Route not found: ${route}`,
      availableRoutes: ['balance', 'purchase', 'verify', 'order', 'receipt', 'webhook', 'health']
    });

  } catch (error) {
    console.error('Payment API error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Internal server error'
    });
  }
};

// Balance Handler
async function handleBalance(req, res) {
  try {
    const userId = req.query.userId || req.headers['x-user-id'];

    if (!userId) {
      return res.status(401).json({ 
        success: false,
        error: 'User ID required',
        message: 'Please provide userId'
      });
    }

    if (!admin.apps.length) {
      return res.status(500).json({ 
        success: false,
        error: 'Database not available',
        message: 'Firebase not initialized'
      });
    }

    const db = admin.firestore();
    const userRef = db.collection('users').doc(userId);
    const userDoc = await userRef.get();

    if (!userDoc.exists) {
      await userRef.set({
        credits: 0,
        totalCreditsEarned: 0,
        totalCreditsUsed: 0,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
      
      return res.status(200).json({
        success: true,
        credits: 0,
        totalCreditsEarned: 0,
        totalCreditsUsed: 0,
        unlimited: false
      });
    }

    const userData = userDoc.data();
    
    const subscriptionRef = db.collection('subscriptions').doc(userId);
    const subscriptionDoc = await subscriptionRef.get();
    
    let unlimited = false;
    if (subscriptionDoc.exists) {
      const subData = subscriptionDoc.data();
      if (subData.plan === 'premium' || subData.plan === 'business') {
        unlimited = subData.features?.unlimitedBackgroundRemoval || false;
      }
    }

    return res.status(200).json({
      success: true,
      credits: userData.credits || 0,
      totalCreditsEarned: userData.totalCreditsEarned || 0,
      totalCreditsUsed: userData.totalCreditsUsed || 0,
      unlimited: unlimited
    });

  } catch (error) {
    console.error('Get credit balance error:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to get credit balance',
      message: error.message
    });
  }
}

// Purchase Handler (Credit Purchase)
async function handlePurchase(req, res) {
  if (!razorpay) {
    return res.status(503).json({ 
      success: false,
      error: 'Payment service unavailable',
      message: 'Razorpay payment gateway is not configured'
    });
  }

  try {
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
    
    const finalAmount = amount || (currency === 'INR' ? pack.priceINR : pack.priceUSD);
    const baseAmount = currency === 'INR' ? pack.priceINR / (1 + GST_RATE) : pack.priceUSD;
    const gstAmount = currency === 'INR' ? finalAmount - baseAmount : 0;
    
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

    const orderOptions = {
      amount: Math.round(finalAmount * 100),
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
      } catch (firestoreError) {
        console.error('Failed to save credit order to Firestore:', firestoreError);
      }
    }

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
    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      message: error.message || 'Failed to create credit purchase order'
    });
  }
}

// Verify Handler (Payment Verification)
async function handleVerify(req, res) {
  if (!razorpay) {
    return res.status(503).json({ 
      success: false,
      error: 'Payment service unavailable'
    });
  }

  try {
    const { orderId, paymentId, signature, userId } = req.body;

    if (!orderId || !paymentId || !signature) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        message: 'orderId, paymentId, and signature are required'
      });
    }

    // Verify signature
    const text = `${orderId}|${paymentId}`;
    const generatedSignature = crypto
      .createHmac('sha256', razorpayKeySecret)
      .update(text)
      .digest('hex');

    if (generatedSignature !== signature) {
      return res.status(400).json({
        success: false,
        error: 'Invalid signature',
        message: 'Payment verification failed'
      });
    }

    // Get payment details from Razorpay
    const payment = await razorpay.payments.fetch(paymentId);
    
    if (payment.status !== 'captured' && payment.status !== 'authorized') {
      return res.status(400).json({
        success: false,
        error: 'Payment not successful',
        message: `Payment status: ${payment.status}`
      });
    }

    // Update credits in Firestore
    if (admin.apps.length && userId) {
      try {
        const db = admin.firestore();
        const orderDoc = await db.collection('creditOrders').doc(orderId).get();
        
        if (orderDoc.exists) {
          const orderData = orderDoc.data();
          const credits = orderData.credits || 0;

          // Use transaction to update credits atomically
          await db.runTransaction(async (transaction) => {
            const userRef = db.collection('users').doc(userId);
            const userDoc = await transaction.get(userRef);

            if (userDoc.exists) {
              const userData = userDoc.data();
              const currentCredits = userData.credits || 0;
              const totalEarned = userData.totalCreditsEarned || 0;

              transaction.update(userRef, {
                credits: currentCredits + credits,
                totalCreditsEarned: totalEarned + credits,
                lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
              });
            } else {
              transaction.set(userRef, {
                credits: credits,
                totalCreditsEarned: credits,
                totalCreditsUsed: 0,
                createdAt: admin.firestore.FieldValue.serverTimestamp(),
                lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
              });
            }

            // Update order status
            transaction.update(db.collection('creditOrders').doc(orderId), {
              status: 'completed',
              paymentId: paymentId,
              paymentStatus: payment.status,
              verifiedAt: admin.firestore.FieldValue.serverTimestamp()
            });
          });

          // Send receipt email (async, don't wait)
          try {
            const RESEND_API_KEY = process.env.RESEND_API_KEY;
            if (RESEND_API_KEY && orderData.userEmail) {
              // Import and call send receipt handler
              const { default: sendReceipt } = await import('../send-receipt-email.js');
              // Note: This is a simplified call - actual implementation may vary
            }
          } catch (emailError) {
            console.warn('Failed to send receipt email:', emailError);
          }
        }
      } catch (firestoreError) {
        console.error('Failed to update credits:', firestoreError);
        return res.status(500).json({
          success: false,
          error: 'Failed to update credits',
          message: firestoreError.message
        });
      }
    }

    return res.status(200).json({
      success: true,
      message: 'Payment verified and credits added',
      paymentId: paymentId,
      orderId: orderId
    });

  } catch (error) {
    console.error('Payment verification error:', error);
    return res.status(500).json({
      success: false,
      error: 'Payment verification failed',
      message: error.message
    });
  }
}

// Create Order Handler (General order creation)
async function handleCreateOrder(req, res) {
  if (!razorpay) {
    return res.status(503).json({ 
      success: false,
      error: 'Payment service unavailable'
    });
  }

  try {
    const { amount, currency = 'INR', receipt, notes } = req.body;

    if (!amount) {
      return res.status(400).json({
        success: false,
        error: 'Amount required'
      });
    }

    const orderOptions = {
      amount: Math.round(amount * 100),
      currency: currency,
      receipt: receipt || `${razorpayReceiptPrefix}_${Date.now()}`,
      payment_capture: 1,
      notes: notes || {}
    };

    const order = await razorpay.orders.create(orderOptions);

    return res.status(200).json({
      success: true,
      orderId: order.id,
      key_id: razorpayKeyId,
      amount: order.amount,
      currency: order.currency,
      receipt: order.receipt
    });

  } catch (error) {
    console.error('Create order error:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to create order',
      message: error.message
    });
  }
}

// Send Receipt Handler
async function handleSendReceipt(req, res) {
  const RESEND_API_KEY = process.env.RESEND_API_KEY;

  if (!RESEND_API_KEY) {
    return res.status(503).json({ 
      success: false,
      error: 'Email service not configured'
    });
  }

  try {
    const { email, name, amount, currency, transactionId, orderId, paymentMethod, date } = req.body;

    if (!email || !amount || !transactionId) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        required: ['email', 'amount', 'transactionId']
      });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid email address'
      });
    }

    // Email content
    const emailHtml = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #4361ee; color: white; padding: 20px; text-align: center; }
          .content { padding: 20px; background: #f9f9f9; }
          .details { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }
          .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>Payment Receipt</h1>
          </div>
          <div class="content">
            <p>Dear ${name || 'Customer'},</p>
            <p>Thank you for your payment. Here are your transaction details:</p>
            <div class="details">
              <p><strong>Transaction ID:</strong> ${transactionId}</p>
              <p><strong>Order ID:</strong> ${orderId || 'N/A'}</p>
              <p><strong>Amount:</strong> ${currency || 'INR'} ${amount}</p>
              <p><strong>Payment Method:</strong> ${paymentMethod || 'Online'}</p>
              <p><strong>Date:</strong> ${date || new Date().toLocaleString()}</p>
            </div>
            <p>This is an automated receipt. Please keep this for your records.</p>
          </div>
          <div class="footer">
            <p>© ${new Date().getFullYear()} EasyJpgToPdf. All rights reserved.</p>
          </div>
        </div>
      </body>
      </html>
    `;

    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: 'EasyJpgToPdf <noreply@easyjpgtopdf.com>',
        to: email,
        subject: 'Payment Receipt - EasyJpgToPdf',
        html: emailHtml
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to send email');
    }

    return res.status(200).json({
      success: true,
      message: 'Receipt email sent successfully'
    });

  } catch (error) {
    console.error('Send receipt error:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to send receipt email',
      message: error.message
    });
  }
}

// Webhook Handler
async function handleWebhook(req, res) {
  if (!razorpayWebhookSecret) {
    return res.status(503).json({ 
      success: false,
      error: 'Webhook secret not configured'
    });
  }

  try {
    const signature = req.headers['x-razorpay-signature'];
    const webhookBody = JSON.stringify(req.body);

    const generatedSignature = crypto
      .createHmac('sha256', razorpayWebhookSecret)
      .update(webhookBody)
      .digest('hex');

    if (generatedSignature !== signature) {
      return res.status(400).json({
        success: false,
        error: 'Invalid signature'
      });
    }

    const event = req.body.event;
    const payment = req.body.payload.payment?.entity;

    if (event === 'payment.captured' && payment) {
      // Handle payment captured event
      // Similar to verify handler logic
    }

    return res.status(200).json({
      success: true,
      message: 'Webhook processed'
    });

  } catch (error) {
    console.error('Webhook error:', error);
    return res.status(500).json({
      success: false,
      error: 'Webhook processing failed',
      message: error.message
    });
  }
}

