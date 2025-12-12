// Admin endpoint to add test credits to a specific user
// SECURITY: This should be protected with admin authentication in production

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

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '3600');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      message: 'Only POST method is supported'
    });
  }

  try {
    const { email, credits = 100 } = req.body;

    if (!email) {
      return res.status(400).json({
        success: false,
        error: 'Email required',
        message: 'Please provide user email'
      });
    }

    if (!admin.apps.length) {
      return res.status(500).json({
        success: false,
        error: 'Database not available',
        message: 'Firebase not initialized'
      });
    }

    // Find user by email
    const db = admin.firestore();
    let userId = null;

    try {
      // Try to find user by email in auth
      const userRecord = await admin.auth().getUserByEmail(email);
      userId = userRecord.uid;
    } catch (authError) {
      // If not found in auth, try to find in Firestore users collection
      const usersSnapshot = await db.collection('users')
        .where('email', '==', email)
        .limit(1)
        .get();

      if (!usersSnapshot.empty) {
        userId = usersSnapshot.docs[0].id;
      } else {
        return res.status(404).json({
          success: false,
          error: 'User not found',
          message: `No user found with email: ${email}`
        });
      }
    }

    if (!userId) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        message: `Could not find user ID for email: ${email}`
      });
    }

    // Get or create user document
    const userRef = db.collection('users').doc(userId);
    const userDoc = await userRef.get();

    let currentCredits = 0;
    if (userDoc.exists) {
      currentCredits = userDoc.data().credits || 0;
    } else {
      // Initialize user document
      await userRef.set({
        email: email,
        credits: 0,
        totalCreditsEarned: 0,
        totalCreditsUsed: 0,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
    }

    // Add credits
    const newCredits = currentCredits + credits;
    await userRef.update({
      credits: admin.firestore.FieldValue.increment(credits),
      totalCreditsEarned: admin.firestore.FieldValue.increment(credits),
      lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
    });

    // Record transaction (same format as real purchase)
    // For $40 plan: 900 credits = $40 USD = ₹4,484 INR (with 18% GST)
    const transactionRef = db.collection('users').doc(userId)
      .collection('creditTransactions').doc();
    
    // Auto-detect plan based on credits
    let packId = 'admin-credit-pack';
    let amountUSD = 0;
    let amountINR = 0;
    let currency = 'USD';
    let packName = 'Admin Credit Pack';
    
    if (credits === 900 || newCredits === 900) {
      // $40 Pro Plan: 900 credits
      packId = 'pack-pro';
      amountUSD = 40;
      amountINR = Math.round(40 * 95 * 1.18); // ₹4,484 (with 18% GST)
      currency = 'USD';
      packName = 'Pro Plan - 900 Credits';
    } else if (credits === 50 || newCredits === 50) {
      packId = 'pack-50';
      amountUSD = 4;
      amountINR = Math.round(4 * 95 * 1.18);
      packName = '50 Credits Pack';
    } else if (credits === 200 || newCredits === 200) {
      packId = 'pack-200';
      amountUSD = 15;
      amountINR = Math.round(15 * 95 * 1.18);
      packName = '200 Credits Pack';
    }
    
    await transactionRef.set({
      type: 'addition',
      amount: credits,
      reason: 'Credit purchase',
      creditsBefore: currentCredits,
      creditsAfter: newCredits,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      metadata: {
        orderId: `order_${Date.now()}`,
        packId: packId,
        packName: packName,
        amount: amountUSD,
        amountUSD: amountUSD,
        amountINR: amountINR,
        currency: currency,
        receipt: `receipt_${Date.now()}`,
        paymentMethod: 'admin'
      }
    });

    console.log(`✅ Added ${credits} credits to user ${email} (${userId}). Old: ${currentCredits}, New: ${newCredits}`);

    return res.status(200).json({
      success: true,
      message: `Added ${credits} credits successfully`,
      user: {
        email: email,
        userId: userId
      },
      credits: {
        before: currentCredits,
        added: credits,
        after: newCredits
      }
    });

  } catch (error) {
    console.error('Error adding test credits:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Failed to add test credits'
    });
  }
};

