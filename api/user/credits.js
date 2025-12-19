// Proxy endpoint for /api/user/credits -> /api/credits/balance
// This maintains backward compatibility with frontend code

// Import Firebase Admin initialization
// Try different possible paths
let initializeFirebase;
try {
  initializeFirebase = require('../config/google-cloud').initializeFirebase;
} catch (e) {
  try {
    initializeFirebase = require('../../config/google-cloud').initializeFirebase;
  } catch (e2) {
    // Fallback: use same pattern as credits/balance.js
    const admin = require('firebase-admin');
    initializeFirebase = async () => {
      if (!admin.apps.length) {
        try {
          const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_KEY || '{}');
          if (serviceAccount.project_id) {
            admin.initializeApp({ credential: admin.credential.cert(serviceAccount) });
          }
        } catch (err) {
          console.error('Firebase initialization error:', err);
        }
      }
      return admin;
    };
  }
}

module.exports = async function handler(req, res) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      message: 'Only GET requests are accepted'
    });
  }

  try {
    const admin = await initializeFirebase();
    
    if (!admin || !admin.apps.length) {
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(500).json({ 
        success: false,
        error: 'Database not available',
        message: 'Firebase not initialized'
      });
    }

    const userId = req.query.userId || req.headers['x-user-id'];

    if (!userId) {
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(401).json({ 
        success: false,
        error: 'User ID required',
        message: 'Please provide userId'
      });
    }

    const db = admin.firestore();
    const userRef = db.collection('users').doc(userId);
    const userDoc = await userRef.get();

    if (!userDoc.exists) {
      // Initialize user with 0 credits
      await userRef.set({
        credits: 0,
        totalCreditsEarned: 0,
        totalCreditsUsed: 0,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
      
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(200).json({
        success: true,
        credits: 0,
        totalCreditsEarned: 0,
        totalCreditsUsed: 0,
        unlimited: false
      });
    }

    const userData = userDoc.data();
    
    // CRITICAL: Ensure credits is a number, not a string
    // Firestore may store credits as strings, so we need to parse them
    const credits = typeof userData.credits === 'number' 
      ? userData.credits 
      : (typeof userData.credits === 'string' ? parseFloat(userData.credits) || 0 : 0);
    
    // Check subscription for unlimited credits
    const subscriptionRef = db.collection('subscriptions').doc(userId);
    const subscriptionDoc = await subscriptionRef.get();
    
    let unlimited = false;
    if (subscriptionDoc.exists) {
      const subData = subscriptionDoc.data();
      if (subData.plan === 'premium' || subData.plan === 'business') {
        unlimited = subData.features?.unlimitedBackgroundRemoval || false;
      }
    }

    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(200).json({
      success: true,
      credits: credits, // Ensure this is a number
      totalCreditsEarned: userData.totalCreditsEarned || 0,
      totalCreditsUsed: userData.totalCreditsUsed || 0,
      unlimited: unlimited
    });

  } catch (error) {
    console.error('Get credit balance error:', error);
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(500).json({
      success: false,
      error: 'Failed to get credit balance',
      message: error.message
    });
  }
};

