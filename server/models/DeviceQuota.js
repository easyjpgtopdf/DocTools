/**
 * Device Quota Model
 * Tracks usage by device fingerprint and IP address to prevent abuse
 */

const mongoose = require('mongoose');

const deviceQuotaSchema = new mongoose.Schema({
  deviceId: {
    type: String,
    required: true,
    index: true
  },
  fingerprint: {
    type: String,
    required: true,
    index: true
  },
  ipAddress: {
    type: String,
    required: true,
    index: true
  },
  // Monthly usage tracking
  currentMonth: {
    type: String,
    default: () => new Date().toISOString().substring(0, 7), // YYYY-MM
    index: true
  },
  // Image remover usage
  imageRemoverCount: {
    type: Number,
    default: 0
  },
  imageRemoverUploadMB: {
    type: Number,
    default: 0
  },
  imageRemoverDownloadMB: {
    type: Number,
    default: 0
  },
  // PDF editing usage
  pdfEditCount: {
    type: Number,
    default: 0
  },
  pdfEditUploadMB: {
    type: Number,
    default: 0
  },
  // Last activity
  lastActivity: {
    type: Date,
    default: Date.now,
    index: true
  },
  // User ID (if logged in)
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    index: true,
    default: null
  },
  // Device metadata
  userAgent: String,
  platform: String,
  language: String,
  timezone: String,
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

// Compound index for efficient queries
deviceQuotaSchema.index({ deviceId: 1, currentMonth: 1 });
deviceQuotaSchema.index({ ipAddress: 1, currentMonth: 1 });
deviceQuotaSchema.index({ fingerprint: 1, currentMonth: 1 });

// Reset monthly usage (called by cron job)
deviceQuotaSchema.statics.resetMonthlyUsage = async function() {
  const currentMonth = new Date().toISOString().substring(0, 7);
  
  await this.updateMany(
    { currentMonth: { $ne: currentMonth } },
    {
      $set: {
        currentMonth: currentMonth,
        imageRemoverCount: 0,
        imageRemoverUploadMB: 0,
        imageRemoverDownloadMB: 0,
        pdfEditCount: 0,
        pdfEditUploadMB: 0
      }
    }
  );
};

// Get or create device quota
deviceQuotaSchema.statics.getOrCreate = async function(deviceId, fingerprint, ipAddress, userAgent = null) {
  const currentMonth = new Date().toISOString().substring(0, 7);
  
  let device = await this.findOne({
    deviceId: deviceId,
    currentMonth: currentMonth
  });
  
  if (!device) {
    // Check if device exists in previous months
    const existingDevice = await this.findOne({ deviceId: deviceId }).sort({ createdAt: -1 });
    
    device = new this({
      deviceId: deviceId,
      fingerprint: fingerprint,
      ipAddress: ipAddress,
      currentMonth: currentMonth,
      userAgent: userAgent || 'unknown',
      platform: 'unknown',
      language: 'unknown',
      timezone: 'unknown'
    });
    
    await device.save();
  } else {
    // Update last activity
    device.lastActivity = new Date();
    await device.save();
  }
  
  return device;
};

module.exports = mongoose.model('DeviceQuota', deviceQuotaSchema);

