/**
 * Auto-expire Subscriptions Cron Job
 * Run this daily to check and expire subscriptions
 * Can be called via cron job or scheduled task
 */

const admin = require('firebase-admin');

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Optional: Add authentication for cron job
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && req.headers.authorization !== `Bearer ${cronSecret}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  if (!admin.apps.length || !admin.firestore) {
    return res.status(503).json({ error: 'Firebase not initialized' });
  }

  try {
    const db = admin.firestore();
    const now = admin.firestore.Timestamp.now();
    
    // Find all active subscriptions that have expired
    const subscriptionsRef = db.collection('subscriptions');
    const activeSubs = await subscriptionsRef
      .where('status', '==', 'active')
      .where('plan', '!=', 'free')
      .get();
    
    let expiredCount = 0;
    const batch = db.batch();
    
    activeSubs.docs.forEach(doc => {
      const data = doc.data();
      const expiresAt = data.expiresAt;
      
      if (expiresAt && expiresAt.toMillis() < now.toMillis()) {
        // Subscription expired
        batch.update(doc.ref, {
          plan: 'free',
          status: 'expired',
          previousPlan: data.plan,
          expiredAt: admin.firestore.FieldValue.serverTimestamp(),
          updatedAt: admin.firestore.FieldValue.serverTimestamp()
        });
        
        // Track expiration activity
        db.collection('activities').add({
          userId: doc.id,
          type: 'subscription_expired',
          details: {
            previousPlan: data.plan,
            expiredAt: expiresAt.toDate().toISOString()
          },
          timestamp: admin.firestore.FieldValue.serverTimestamp()
        });
        
        expiredCount++;
      }
    });
    
    if (expiredCount > 0) {
      await batch.commit();
    }
    
    res.status(200).json({
      success: true,
      message: `Processed ${expiredCount} expired subscriptions`,
      expiredCount: expiredCount,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error auto-expiring subscriptions:', error);
    res.status(500).json({
      error: 'Failed to process expired subscriptions',
      details: error.message
    });
  }
};

