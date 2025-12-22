/**
 * Manual Credit Addition Script
 * Use this to add credits to a user account
 * 
 * Usage: node server/utils/add-credits-manually.js <userId> <credits>
 * Example: node server/utils/add-credits-manually.js 1234567890 790
 */

require('dotenv').config();
const mongoose = require('mongoose');
const UserCredits = require('../models/UserCredits');
const User = require('../models/User');

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/pdf-editor-enterprise';

async function addCreditsToUser(userId, creditsToAdd) {
  try {
    // Connect to MongoDB
    console.log('🔌 Connecting to MongoDB...');
    await mongoose.connect(MONGODB_URI, {
      serverSelectionTimeoutMS: 5000,
      connectTimeoutMS: 5000
    });
    console.log('✅ MongoDB connected');

    // Find user by Firebase UID or MongoDB _id
    let user = null;
    
    // Try to find by Firebase UID first
    user = await User.findOne({ firebaseUid: userId });
    
    // If not found, try MongoDB _id
    if (!user && mongoose.Types.ObjectId.isValid(userId)) {
      user = await User.findById(userId);
    }
    
    // If still not found, try email
    if (!user && userId.includes('@')) {
      user = await User.findOne({ email: userId });
    }

    if (!user) {
      console.error('❌ User not found. Please provide:');
      console.error('   - Firebase UID (from Firebase Auth)');
      console.error('   - MongoDB User _id');
      console.error('   - User email');
      process.exit(1);
    }

    console.log(`✅ Found user: ${user.email || user.name || user._id}`);
    console.log(`   Firebase UID: ${user.firebaseUid || 'N/A'}`);
    console.log(`   MongoDB ID: ${user._id}`);

    // Get or create user credits
    const userCredits = await UserCredits.getOrCreate(user._id);
    
    const creditsBefore = userCredits.credits;
    
    // Add credits
    await userCredits.addCredits(parseInt(creditsToAdd), 90);
    
    const creditsAfter = userCredits.credits;

    console.log('');
    console.log('✅ Credits added successfully!');
    console.log(`   Credits before: ${creditsBefore}`);
    console.log(`   Credits added: ${creditsToAdd}`);
    console.log(`   Credits after: ${creditsAfter}`);
    console.log(`   Expires at: ${userCredits.expiresAt ? userCredits.expiresAt.toLocaleString() : 'Never'}`);

    await mongoose.disconnect();
    console.log('✅ Disconnected from MongoDB');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

// Get command line arguments
const args = process.argv.slice(2);

if (args.length < 2) {
  console.log('Usage: node server/utils/add-credits-manually.js <userId> <credits>');
  console.log('');
  console.log('Examples:');
  console.log('  node server/utils/add-credits-manually.js firebase_uid_here 790');
  console.log('  node server/utils/add-credits-manually.js user@example.com 790');
  console.log('  node server/utils/add-credits-manually.js 507f1f77bcf86cd799439011 790');
  console.log('');
  console.log('Note: userId can be:');
  console.log('  - Firebase UID (recommended)');
  console.log('  - User email');
  console.log('  - MongoDB User _id');
  process.exit(1);
}

const userId = args[0];
const credits = args[1];

addCreditsToUser(userId, credits);

