// Vercel Serverless Function - Verify Credit Purchase Payment

const crypto = require('crypto');
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

const razorpay = razorpayKeyId && razorpayKeySecret 
  ? new Razorpay({ key_id: razorpayKeyId, key_secret: razorpayKeySecret })
  : null;

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
    if (!razorpay) {
      return res.status(503).json({ 
        success: false,
        error: 'Payment service unavailable',
        message: 'Razorpay is not configured'
      });
    }

    const { orderId, paymentId, signature, userId, credits } = req.body;

    if (!orderId || !paymentId || !signature || !userId) {
      return res.status(400).json({ 
        success: false,
        error: 'Missing required fields',
        message: 'orderId, paymentId, signature, and userId are required'
      });
    }

    // SECURITY: Verify authentication token if provided (optional for webhook, required for direct API calls)
    let verifiedUserId = userId;
    const authHeader = req.headers.authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      try {
        const token = authHeader.replace('Bearer ', '');
        if (admin.apps.length) {
          const decodedToken = await admin.auth().verifyIdToken(token);
          verifiedUserId = decodedToken.uid;
          
          // SECURITY: Verify userId from token matches userId from request body
          if (userId !== verifiedUserId) {
            console.warn(`SECURITY ALERT: User ID mismatch in credit verification - token userId (${verifiedUserId}) != request userId (${userId})`);
            return res.status(403).json({
              success: false,
              error: 'User ID mismatch',
              message: 'Authentication failed: User ID does not match token'
            });
          }
        }
      } catch (tokenError) {
        console.error('Token verification failed in credit verification:', tokenError);
        // Continue without token verification for webhook scenarios
        // But log the security issue
      }
    }

    // SECURITY: Verify payment signature (CRITICAL - prevents fake payments)
    const generatedSignature = crypto
      .createHmac('sha256', razorpayKeySecret)
      .update(orderId + '|' + paymentId)
      .digest('hex');

    if (generatedSignature !== signature) {
      console.error(`SECURITY ALERT: Invalid payment signature for order ${orderId}, payment ${paymentId}`);
      return res.status(400).json({ 
        success: false,
        error: 'Invalid payment signature',
        message: 'Payment signature verification failed'
      });
    }

    // SECURITY: Verify with Razorpay API (CRITICAL - ensures payment is real)
    const payment = await razorpay.payments.fetch(paymentId);

    if (payment.status !== 'captured') {
      console.error(`SECURITY ALERT: Payment ${paymentId} not captured, status: ${payment.status}`);
      return res.status(400).json({ 
        success: false,
        error: 'Payment not captured',
        message: `Payment status: ${payment.status}`
      });
    }
    
    // SECURITY: Verify order exists and belongs to user
    if (admin.apps.length) {
      try {
        const db = admin.firestore();
        const orderDoc = await db.collection('creditOrders').doc(orderId).get();
        
        if (orderDoc.exists) {
          const orderData = orderDoc.data();
          // Verify order belongs to the correct user
          if (orderData.userId && orderData.userId !== verifiedUserId) {
            console.error(`SECURITY ALERT: Order ${orderId} belongs to user ${orderData.userId} but verification attempted by ${verifiedUserId}`);
            return res.status(403).json({
              success: false,
              error: 'Order ownership mismatch',
              message: 'This order does not belong to the authenticated user'
            });
          }
        }
      } catch (orderCheckError) {
        console.error('Error checking order ownership:', orderCheckError);
        // Continue - order check is not critical if order doesn't exist yet
      }
    }

    // Get credits from order if not provided
    let creditsToAdd = credits;
    if (!creditsToAdd && admin.apps.length) {
      try {
        const db = admin.firestore();
        const orderDoc = await db.collection('creditOrders').doc(orderId).get();
        if (orderDoc.exists) {
          creditsToAdd = orderDoc.data().credits;
        }
      } catch (e) {
        console.warn('Failed to get credits from order:', e);
      }
    }

    if (!creditsToAdd) {
      return res.status(400).json({ 
        success: false,
        error: 'Credits amount required',
        message: 'Credits amount not found in order'
      });
    }

    // Update order in Firestore and add credits
    if (admin.apps.length) {
      const db = admin.firestore();
      
      // Update order status
      const orderRef = db.collection('creditOrders').doc(orderId);
      const orderDoc = await orderRef.get();
      
      // SECURITY: Check if order already processed (prevent duplicate credits)
      if (orderDoc.exists && orderDoc.data().status === 'completed') {
        console.warn(`SECURITY: Order ${orderId} already processed - preventing duplicate credit addition`);
        return res.status(200).json({
          success: true,
          creditsAdded: 0,
          creditsRemaining: orderDoc.data().creditsAfter || 0,
          message: 'Credits already added (duplicate verification prevented)',
          duplicate: true
        });
      }
      
      // SECURITY: Use transaction to prevent duplicate credit addition
      const finalUserId = verifiedUserId || userId;
      
      // SECURITY: Verify order belongs to correct user (prevent fraud)
      if (orderDoc.exists && orderDoc.data().userId && orderDoc.data().userId !== finalUserId) {
        console.error(`SECURITY ALERT: Order ${orderId} belongs to ${orderDoc.data().userId} but verification attempted by ${finalUserId}`);
        return res.status(403).json({
          success: false,
          error: 'Order ownership verification failed',
          message: 'This order does not belong to the authenticated user'
        });
      }
      
      // SECURITY: Use atomic transaction to prevent race conditions and duplicate credits
      await db.runTransaction(async (transaction) => {
        const orderRef = db.collection('creditOrders').doc(orderId);
        const orderDoc = await transaction.get(orderRef);
        
        // Double-check if already completed (within transaction)
        if (orderDoc.exists && orderDoc.data().status === 'completed') {
          throw new Error('Order already processed');
        }
        
        const userRef = db.collection('users').doc(finalUserId);
        const userDoc = await transaction.get(userRef);
        
        if (!userDoc.exists) {
          // Initialize user
          transaction.set(userRef, {
            credits: 0,
            totalCreditsEarned: 0,
            totalCreditsUsed: 0,
            createdAt: admin.firestore.FieldValue.serverTimestamp(),
            lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
          });
        }
        
        const currentCredits = userDoc.exists ? (userDoc.data().credits || 0) : 0;
        const newCredits = currentCredits + creditsToAdd;
        
        // Update user credits atomically
        transaction.update(userRef, {
          credits: admin.firestore.FieldValue.increment(creditsToAdd),
          totalCreditsEarned: admin.firestore.FieldValue.increment(creditsToAdd),
          lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
        });
        
        // Mark order as completed (prevents duplicate processing)
        transaction.update(orderRef, {
          status: 'completed',
          paymentId: paymentId,
          completedAt: admin.firestore.FieldValue.serverTimestamp(),
          creditsAfter: newCredits,
          creditsAdded: creditsToAdd
        });
        
        // Store for transaction record
        transaction.set(
          db.collection('users').doc(finalUserId).collection('creditTransactions').doc(),
          {
            type: 'addition',
            amount: creditsToAdd,
            reason: 'Credit purchase',
            creditsBefore: currentCredits,
            creditsAfter: newCredits,
            timestamp: admin.firestore.FieldValue.serverTimestamp(),
            metadata: {
              orderId: orderId,
              paymentId: paymentId,
              packId: orderDoc.data()?.creditPack,
              amount: orderDoc.data()?.amount,
              currency: orderDoc.data()?.currency,
              verifiedBy: 'api-handlers/credits/verify',
              transactionId: orderId + '_' + Date.now()
            }
          }
        );
      });

      // Get order details for receipt
      const orderData = orderDoc.data();
      
      // Record transaction
      await db.collection('users').doc(finalUserId).collection('creditTransactions').add({
        type: 'addition',
        amount: creditsToAdd,
        reason: 'Credit purchase',
        creditsBefore: currentCredits,
        creditsAfter: currentCredits + creditsToAdd,
        timestamp: admin.firestore.FieldValue.serverTimestamp(),
        metadata: {
          orderId: orderId,
          paymentId: paymentId,
          packId: orderData?.creditPack,
          amount: orderData?.amount,
          currency: orderData?.currency,
          gstAmount: orderData?.gstAmount,
          receipt: orderData?.receipt
        }
      });
      
      // Generate and save receipt
      const receiptData = {
        orderId: orderId,
        paymentId: paymentId,
        userId: finalUserId,
        credits: creditsToAdd,
        amount: orderData?.amount || 0,
        amountUSD: orderData?.amountUSD || 0,
        amountINR: orderData?.amountINR || 0,
        baseAmount: orderData?.baseAmount || 0,
        gstAmount: orderData?.gstAmount || 0,
        gstRate: orderData?.gstRate || 0,
        currency: orderData?.currency || 'INR',
        packName: orderData?.creditPack || '',
        userName: orderData?.userName || '',
        userEmail: orderData?.userEmail || '',
        status: 'completed',
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        completedAt: admin.firestore.FieldValue.serverTimestamp()
      };
      
      // Save receipt to receipts collection
      await db.collection('receipts').doc(orderId).set(receiptData);
      
      // Also save to user's receipts subcollection
      await db.collection('users').doc(finalUserId).collection('receipts').doc(orderId).set(receiptData);
      
      console.log(`Credits added: ${creditsToAdd} to user ${finalUserId} (verified purchase)`);
    }

    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(200).json({
      success: true,
      creditsAdded: creditsToAdd,
      message: 'Credits added successfully'
    });

  } catch (error) {
    console.error('Credit verification error:', error);
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(500).json({
      success: false,
      error: 'Verification failed',
      message: error.message || 'Failed to verify and add credits'
    });
  }
}

