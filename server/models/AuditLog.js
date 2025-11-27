/**
 * Audit Log Model
 * Track all user operations for compliance and security
 */

const mongoose = require('mongoose');

const auditLogSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    index: true
  },
  organizationId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Organization',
    index: true
  },
  action: {
    type: String,
    required: true,
    index: true
  },
  resourceType: {
    type: String,
    enum: ['pdf', 'user', 'organization', 'api', 'payment', 'security'],
    index: true
  },
  resourceId: String,
  details: mongoose.Schema.Types.Mixed,
  ipAddress: String,
  userAgent: String,
  status: {
    type: String,
    enum: ['success', 'failure', 'error'],
    default: 'success',
    index: true
  },
  errorMessage: String,
  timestamp: {
    type: Date,
    default: Date.now,
    index: true
  }
}, {
  timestamps: false
});

// Indexes for fast queries
auditLogSchema.index({ userId: 1, timestamp: -1 });
auditLogSchema.index({ organizationId: 1, timestamp: -1 });
auditLogSchema.index({ action: 1, timestamp: -1 });
auditLogSchema.index({ resourceType: 1, resourceId: 1 });
auditLogSchema.index({ timestamp: -1 }); // TTL index for auto-deletion

// TTL index - auto-delete logs older than 1 year
auditLogSchema.index({ timestamp: 1 }, { expireAfterSeconds: 31536000 });

module.exports = mongoose.model('AuditLog', auditLogSchema);

