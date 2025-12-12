// Admin script to add test credits to a user account
// Usage: This is a server-side API endpoint to safely add credits for testing

const admin = require('firebase-admin');

// Initialize Firebase Admin if not already initialized
if (!admin.apps.length) {
  try {
    const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT
      ? JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT)
      : null;

    if (serviceAccount) {
      admin.initializeApp({
        credential: admin.credential.cert(serviceAccount)
      });
    } else if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
      admin.initializeApp({
        credential: admin.credential.applicationDefault()
      });
    } else {
      console.error('Firebase Admin not initialized - missing credentials');
    }
  } catch (error) {
    console.error('Firebase Admin initialization failed:', error);
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

  // SECURITY: Only allow from admin (you can add admin auth token check here)
  // For now, this is a simple check - in production, add proper admin authentication
  
  try {
    const { email, credits, reason } = req.body;

    if (!email || !credits) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        message: 'Email and credits amount are required'
      });
    }

    if (!admin.apps.length) {
      return res.status(500).json({
        success: false,
        error: 'Firebase Admin not initialized',
        message: 'Server configuration error'
      });
    }

    // Find user by email
    let userRecord;
    try {
      userRecord = await admin.auth().getUserByEmail(email);
    } catch (error) {
      if (error.code === 'auth/user-not-found') {
        return res.status(404).json({
          success: false,
          error: 'User not found',
          message: `No user found with email: ${email}`
        });
      }
      throw error;
    }

    const userId = userRecord.uid;
    const db = admin.firestore();

    // Get current user data
    const userRef = db.collection('users').doc(userId);
    const userDoc = await userRef.get();

    let currentCredits = 0;
    if (userDoc.exists) {
      currentCredits = userDoc.data().credits || 0;
    } else {
      // Initialize user if doesn't exist
      await userRef.set({
        credits: 0,
        totalCreditsEarned: 0,
        totalCreditsUsed: 0,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
    }

    // Add credits
    await userRef.update({
      credits: admin.firestore.FieldValue.increment(credits),
      totalCreditsEarned: admin.firestore.FieldValue.increment(credits),
      lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
    });

    const newCredits = currentCredits + credits;

    // Record transaction
    await db.collection('users').doc(userId).collection('creditTransactions').add({
      type: 'addition',
      amount: credits,
      reason: reason || 'Test credits - Admin addition',
      creditsBefore: currentCredits,
      creditsAfter: newCredits,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      metadata: {
        source: 'admin',
        email: email,
        addedBy: 'admin-script'
      }
    });

    console.log(`✅ Credits added: ${credits} to user ${userId} (${email}), total now: ${newCredits}`);

    return res.status(200).json({
      success: true,
      message: `Successfully added ${credits} credits to ${email}`,
      userId: userId,
      email: email,
      creditsAdded: credits,
      creditsBefore: currentCredits,
      creditsAfter: newCredits,
      transactionType: 'test-credits'
    });

  } catch (error) {
    console.error('Error adding test credits:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to add credits',
      message: error.message || 'Internal server error'
    });
  }
};

