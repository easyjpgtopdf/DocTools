/**
 * Organization Model
 * Multi-tenant architecture for teams
 */

const mongoose = require('mongoose');

const organizationSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true
  },
  domain: {
    type: String,
    trim: true,
    index: true
  },
  ownerId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  members: [{
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    role: {
      type: String,
      enum: ['admin', 'editor', 'viewer'],
      default: 'viewer'
    },
    invitedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    invitedAt: {
      type: Date,
      default: Date.now
    },
    joinedAt: Date,
    status: {
      type: String,
      enum: ['pending', 'active', 'suspended'],
      default: 'pending'
    }
  }],
  subscriptionPlan: {
    type: String,
    enum: ['free', 'basic', 'pro', 'enterprise'],
    default: 'free'
  },
  subscriptionStatus: {
    type: String,
    enum: ['active', 'cancelled', 'expired'],
    default: 'active'
  },
  billingEmail: String,
  usageLimits: {
    pdfsPerMonth: { type: Number, default: 100 },
    storageGB: { type: Number, default: 10 },
    apiCallsPerMonth: { type: Number, default: 10000 },
    teamMembers: { type: Number, default: 5 }
  },
  currentUsage: {
    pdfsThisMonth: { type: Number, default: 0 },
    storageUsedGB: { type: Number, default: 0 },
    apiCallsThisMonth: { type: Number, default: 0 },
    activeMembers: { type: Number, default: 0 }
  },
  settings: {
    allowPublicSharing: { type: Boolean, default: false },
    requireApprovalForSharing: { type: Boolean, default: true },
    dataRetentionDays: { type: Number, default: 90 }
  },
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

// Indexes
organizationSchema.index({ ownerId: 1 });
organizationSchema.index({ 'members.userId': 1 });
organizationSchema.index({ domain: 1 });

// Add member to organization
organizationSchema.methods.addMember = function(userId, role = 'viewer', invitedBy) {
  const existingMember = this.members.find(m => m.userId.toString() === userId.toString());
  
  if (existingMember) {
    existingMember.role = role;
    existingMember.status = 'pending';
    existingMember.invitedBy = invitedBy;
    existingMember.invitedAt = new Date();
  } else {
    this.members.push({
      userId,
      role,
      invitedBy,
      invitedAt: new Date(),
      status: 'pending'
    });
  }
  
  return this.save();
};

// Remove member
organizationSchema.methods.removeMember = function(userId) {
  this.members = this.members.filter(m => m.userId.toString() !== userId.toString());
  this.currentUsage.activeMembers = this.members.filter(m => m.status === 'active').length;
  return this.save();
};

// Check usage limits
organizationSchema.methods.checkUsageLimit = function(type) {
  const limits = this.usageLimits;
  const usage = this.currentUsage;
  
  switch(type) {
    case 'pdf':
      return usage.pdfsThisMonth < limits.pdfsPerMonth;
    case 'storage':
      return usage.storageUsedGB < limits.storageGB;
    case 'api':
      return usage.apiCallsThisMonth < limits.apiCallsPerMonth;
    case 'members':
      return usage.activeMembers < limits.teamMembers;
    default:
      return true;
  }
};

module.exports = mongoose.model('Organization', organizationSchema);

