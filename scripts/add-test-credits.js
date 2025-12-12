// Script to add 100 test credits to easyjpgtopdf@gmail.com
// Run: node scripts/add-test-credits.js

require('dotenv').config({ path: '.env.local' });
const admin = require('firebase-admin');

// Initialize Firebase Admin
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
      console.error('❌ Firebase Admin not initialized - missing credentials');
      console.error('Please set FIREBASE_SERVICE_ACCOUNT or GOOGLE_APPLICATION_CREDENTIALS');
      process.exit(1);
    }
  } catch (error) {
    console.error('❌ Firebase Admin initialization failed:', error);
    process.exit(1);
  }
}

async function addTestCredits() {
  const email = 'easyjpgtopdf@gmail.com';
  const creditsToAdd = 100;
  const reason = 'Test credits for premium download testing';

  try {
    console.log(`🔍 Looking up user with email: ${email}...`);
    
    // Find user by email
    let userRecord;
    try {
      userRecord = await admin.auth().getUserByEmail(email);
      console.log(`✅ User found: ${userRecord.uid}`);
    } catch (error) {
      if (error.code === 'auth/user-not-found') {
        console.error(`❌ User not found with email: ${email}`);
        console.error('Please make sure the user has signed in at least once.');
        process.exit(1);
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
      console.log(`📊 Current credits: ${currentCredits}`);
    } else {
      console.log('📝 Initializing user account...');
      // Initialize user if doesn't exist
      await userRef.set({
        credits: 0,
        totalCreditsEarned: 0,
        totalCreditsUsed: 0,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
    }

    console.log(`➕ Adding ${creditsToAdd} credits...`);

    // Add credits
    await userRef.update({
      credits: admin.firestore.FieldValue.increment(creditsToAdd),
      totalCreditsEarned: admin.firestore.FieldValue.increment(creditsToAdd),
      lastCreditUpdate: admin.firestore.FieldValue.serverTimestamp()
    });

    const newCredits = currentCredits + creditsToAdd;

    // Record transaction
    await db.collection('users').doc(userId).collection('creditTransactions').add({
      type: 'addition',
      amount: creditsToAdd,
      reason: reason,
      creditsBefore: currentCredits,
      creditsAfter: newCredits,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      metadata: {
        source: 'admin',
        email: email,
        addedBy: 'admin-script',
        scriptRun: new Date().toISOString()
      }
    });

    console.log(`✅ Successfully added ${creditsToAdd} credits to ${email}`);
    console.log(`📊 Credits before: ${currentCredits}`);
    console.log(`📊 Credits after: ${newCredits}`);
    console.log(`👤 User ID: ${userId}`);
    console.log('');
    console.log('🎉 Test credits added successfully!');

  } catch (error) {
    console.error('❌ Error adding test credits:', error);
    process.exit(1);
  }
}

// Run the script
addTestCredits()
  .then(() => {
    console.log('✅ Script completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('❌ Script failed:', error);
    process.exit(1);
  });

