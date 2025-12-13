// Vercel Serverless Function - Get User Credit Balance

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
  // Handle CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ 
      success: false,
      error: 'Method not allowed',
      message: 'Only GET requests are accepted'
    });
  }

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
      credits: credits,
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
}

