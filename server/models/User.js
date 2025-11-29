/**
 * User Model
 * Enterprise-grade user authentication with MongoDB
 */

const mongoose = require('mongoose');
const bcrypt = require('bcrypt');
const crypto = require('crypto');

const userSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true,
    index: true
  },
  password: {
    type: String,
    required: true,
    select: false // Don't return password by default
  },
  firstName: {
    type: String,
    trim: true
  },
  lastName: {
    type: String,
    trim: true
  },
  subscriptionPlan: {
    type: String,
    enum: ['free', 'premium', 'business', 'basic', 'pro', 'enterprise'],
    default: 'free',
    index: true
  },
  subscriptionStatus: {
    type: String,
    enum: ['active', 'cancelled', 'expired', 'trial'],
    default: 'trial'
  },
  subscriptionExpiresAt: {
    type: Date
  },
  teamId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Organization',
    index: true
  },
  role: {
    type: String,
    enum: ['admin', 'editor', 'viewer'],
    default: 'viewer'
  },
  apiKeys: [{
    key: String,
    name: String,
    createdAt: Date,
    lastUsed: Date,
    permissions: [String]
  }],
  usageLimits: {
    pdfsPerMonth: { type: Number, default: 10 },
    storageGB: { type: Number, default: 1 },
    apiCallsPerMonth: { type: Number, default: 1000 },
    imageRemoverPerMonth: { type: Number, default: 100 }, // Temporarily increased, will reduce to 40 later
    imageRemoverMonthlyUploadMB: { type: Number, default: 100 }, // Temporarily increased, will reduce to 10 later
    imageRemoverMonthlyDownloadMB: { type: Number, default: 100 } // Temporarily increased, will reduce to 2 later
  },
  currentUsage: {
    pdfsThisMonth: { type: Number, default: 0 },
    storageUsedGB: { type: Number, default: 0 },
    apiCallsThisMonth: { type: Number, default: 0 },
    imageRemoverThisMonth: { type: Number, default: 0 },
    imageRemoverUploadMB: { type: Number, default: 0 },
    imageRemoverDownloadMB: { type: Number, default: 0 }
  },
  passwordResetToken: String,
  passwordResetExpires: Date,
  emailVerified: {
    type: Boolean,
    default: false
  },
  emailVerificationToken: String,
  lastLogin: Date,
  failedLoginAttempts: {
    type: Number,
    default: 0
  },
  lockedUntil: Date,
  acceptedTerms: {
    type: Boolean,
    default: false
  },
  acceptedTermsAt: Date,
  privacyPolicyAccepted: {
    type: Boolean,
    default: false
  },
  privacyPolicyAcceptedAt: Date,
  gdprDataDeletionRequested: {
    type: Boolean,
    default: false
  },
  gdprDataDeletionRequestedAt: Date,
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Indexes for performance
userSchema.index({ email: 1 });
userSchema.index({ teamId: 1, role: 1 });
userSchema.index({ subscriptionPlan: 1, subscriptionStatus: 1 });
userSchema.index({ createdAt: -1 });

// Hash password before saving
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  
  try {
    const salt = await bcrypt.genSalt(12);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error);
  }
});

// Compare password method
userSchema.methods.comparePassword = async function(candidatePassword) {
  if (!this.password) return false;
  return await bcrypt.compare(candidatePassword, this.password);
};

// Generate API key
userSchema.methods.generateApiKey = function(name = 'Default') {
  const key = crypto.randomBytes(32).toString('hex');
  this.apiKeys.push({
    key,
    name,
    createdAt: new Date(),
    permissions: ['read', 'write']
  });
  return key;
};

// Check if user is locked
userSchema.methods.isLocked = function() {
  return this.lockedUntil && this.lockedUntil > new Date();
};

// Increment failed login attempts
userSchema.methods.incrementFailedAttempts = async function() {
  this.failedLoginAttempts += 1;
  
  if (this.failedLoginAttempts >= 5) {
    this.lockedUntil = new Date(Date.now() + 30 * 60 * 1000); // Lock for 30 minutes
  }
  
  await this.save();
};

// Reset failed login attempts
userSchema.methods.resetFailedAttempts = async function() {
  this.failedLoginAttempts = 0;
  this.lockedUntil = undefined;
  await this.save();
};

// Check usage limits
userSchema.methods.checkUsageLimit = function(type) {
  const limits = this.usageLimits;
  const usage = this.currentUsage;
  
  switch(type) {
    case 'pdf':
      return limits.pdfsPerMonth === -1 || usage.pdfsThisMonth < limits.pdfsPerMonth;
    case 'storage':
      return limits.storageGB === -1 || usage.storageUsedGB < limits.storageGB;
    case 'api':
      return limits.apiCallsPerMonth === -1 || usage.apiCallsThisMonth < limits.apiCallsPerMonth;
    case 'imageRemover':
      return limits.imageRemoverPerMonth === -1 || limits.imageRemoverPerMonth === Infinity || usage.imageRemoverThisMonth < limits.imageRemoverPerMonth;
    default:
      return true;
  }
};

// Increment usage
userSchema.methods.incrementUsage = async function(type, amount = 1) {
  switch(type) {
    case 'pdf':
      this.currentUsage.pdfsThisMonth += amount;
      break;
    case 'storage':
      this.currentUsage.storageUsedGB += amount;
      break;
    case 'api':
      this.currentUsage.apiCallsThisMonth += amount;
      break;
    case 'imageRemover':
      this.currentUsage.imageRemoverThisMonth += amount;
      break;
  }
  await this.save();
};

module.exports = mongoose.model('User', userSchema);

