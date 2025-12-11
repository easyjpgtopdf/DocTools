/**
 * User Credits Model
 * Tracks credit balance and expiry for users
 */

const mongoose = require('mongoose');

const userCreditsSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    unique: true,
    index: true
  },
  credits: {
    type: Number,
    default: 0,
    min: 0
  },
  expiresAt: {
    type: Date,
    default: null
  },
  lastUsedAt: {
    type: Date,
    default: null
  },
  isExpired: {
    type: Boolean,
    default: false,
    index: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Index for efficient queries
userCreditsSchema.index({ userId: 1 });
userCreditsSchema.index({ expiresAt: 1 });
userCreditsSchema.index({ isExpired: 1 });

// Method to check if credits are expired
userCreditsSchema.methods.checkExpiry = function() {
  if (!this.expiresAt) return false;
  
  // Credits expire 90 days after last use, or 90 days after purchase if never used
  const expiryDate = this.lastUsedAt 
    ? new Date(this.lastUsedAt.getTime() + 90 * 24 * 60 * 60 * 1000)
    : this.expiresAt;
  
  const now = new Date();
  if (expiryDate < now && this.credits > 0) {
    this.isExpired = true;
    this.credits = 0;
    return true;
  }
  
  return false;
};

// Method to add credits
userCreditsSchema.methods.addCredits = async function(amount, expiryDays = 90) {
  this.credits += amount;
  
  // Set expiry date: 90 days from now if no expiry exists, or extend if credits already exist
  const now = new Date();
  if (!this.expiresAt || this.expiresAt < now) {
    this.expiresAt = new Date(now.getTime() + expiryDays * 24 * 60 * 60 * 1000);
  }
  
  this.isExpired = false;
  this.updatedAt = now;
  await this.save();
};

// Method to deduct credits
userCreditsSchema.methods.deductCredits = async function(amount) {
  if (this.credits < amount) {
    throw new Error('Insufficient credits');
  }
  
  this.credits -= amount;
  this.lastUsedAt = new Date();
  
  // Reset expiry: 90 days from last use
  this.expiresAt = new Date(this.lastUsedAt.getTime() + 90 * 24 * 60 * 60 * 1000);
  this.isExpired = false;
  this.updatedAt = new Date();
  
  await this.save();
};

// Static method to get or create user credits
userCreditsSchema.statics.getOrCreate = async function(userId) {
  let userCredits = await this.findOne({ userId });
  
  if (!userCredits) {
    userCredits = new this({
      userId,
      credits: 0,
      isExpired: false
    });
    await userCredits.save();
  }
  
  // Check and update expiry
  userCredits.checkExpiry();
  
  return userCredits;
};

module.exports = mongoose.model('UserCredits', userCreditsSchema);

