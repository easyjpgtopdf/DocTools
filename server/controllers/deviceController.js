/**
 * Device Quota Controller
 * Handles IP/device fingerprint-based quota tracking
 */

const DeviceQuota = require('../models/DeviceQuota');
const { asyncHandler } = require('../middleware/errorHandler');
const mongoose = require('mongoose');

// Free plan limits
const FREE_LIMITS = {
  imageRemover: {
    count: 40, // 40 images per month
    uploadMB: 10, // 10 MB monthly upload
    downloadMB: 10, // 10 MB monthly download
    maxFileSizeMB: 1 // 1 MB per image
  },
  pdfEdit: {
    count: 10, // 10 PDFs per month
    uploadMB: 50, // 50 MB monthly upload
    maxFileSizeMB: 50 // 50 MB per file
  }
};

/**
 * Get client IP address
 */
function getClientIP(req) {
  return req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
         req.headers['x-real-ip'] ||
         req.connection?.remoteAddress ||
         req.socket?.remoteAddress ||
         req.ip ||
         'unknown';
}

/**
 * Check device quota
 */
async function checkDeviceQuota(req, res) {
  try {
    const { deviceId, fingerprint, ip, operationType } = req.body;
    const clientIP = ip || getClientIP(req);
    
    if (!deviceId || !fingerprint) {
      return res.status(400).json({
        success: false,
        error: 'Device ID and fingerprint required',
        code: 'MISSING_DEVICE_INFO'
      });
    }
    
    // Check if MongoDB is connected
    if (mongoose.connection.readyState !== 1) {
      console.warn('⚠️ MongoDB not connected, allowing operation (fail-open)');
      return res.json({
        success: true,
        allowed: true,
        remaining: 999,
        limit: 40,
        currentUsage: { count: 0, uploadMB: 0, downloadMB: 0 },
        message: 'Database unavailable, allowing operation'
      });
    }
    
    // Get or create device quota
    const device = await DeviceQuota.getOrCreate(
      deviceId,
      fingerprint,
      clientIP,
      req.headers['user-agent']
    );
    
    // Get limits based on operation type
    const limits = FREE_LIMITS[operationType] || FREE_LIMITS.imageRemover;
    
    // Check quota
    let allowed = true;
    let remaining = 0;
    let message = '';
    
    if (operationType === 'imageRemover') {
      const countRemaining = limits.count - device.imageRemoverCount;
      const uploadRemaining = limits.uploadMB - device.imageRemoverUploadMB;
      const downloadRemaining = limits.downloadMB - device.imageRemoverDownloadMB;
      
      remaining = Math.min(countRemaining, Math.floor(uploadRemaining), Math.floor(downloadRemaining));
      
      if (device.imageRemoverCount >= limits.count) {
        allowed = false;
        message = `Monthly quota exceeded: ${limits.count} images/month`;
      } else if (device.imageRemoverUploadMB >= limits.uploadMB) {
        allowed = false;
        message = `Monthly upload limit exceeded: ${limits.uploadMB} MB/month`;
      } else if (device.imageRemoverDownloadMB >= limits.downloadMB) {
        allowed = false;
        message = `Monthly download limit exceeded: ${limits.downloadMB} MB/month`;
      }
    } else if (operationType === 'pdfEdit') {
      const countRemaining = limits.count - device.pdfEditCount;
      const uploadRemaining = limits.uploadMB - device.pdfEditUploadMB;
      
      remaining = Math.min(countRemaining, Math.floor(uploadRemaining));
      
      if (device.pdfEditCount >= limits.count) {
        allowed = false;
        message = `Monthly quota exceeded: ${limits.count} PDFs/month`;
      } else if (device.pdfEditUploadMB >= limits.uploadMB) {
        allowed = false;
        message = `Monthly upload limit exceeded: ${limits.uploadMB} MB/month`;
      }
    }
    
    res.json({
      success: true,
      allowed: allowed,
      remaining: Math.max(0, remaining),
      limit: limits.count,
      currentUsage: {
        count: operationType === 'imageRemover' ? device.imageRemoverCount : device.pdfEditCount,
        uploadMB: operationType === 'imageRemover' ? device.imageRemoverUploadMB : device.pdfEditUploadMB,
        downloadMB: device.imageRemoverDownloadMB || 0
      },
      message: message
    });
  } catch (error) {
    console.error('Check device quota error:', error);
    // Fail-open: Allow operation if database/backend error
    // Better UX than blocking users when service is down
    res.json({
      success: true,
      allowed: true,
      remaining: 999,
      limit: 40, // Default free limit
      currentUsage: {
        count: 0,
        uploadMB: 0,
        downloadMB: 0
      },
      message: 'Quota check unavailable, allowing operation'
    });
  }
}

/**
 * Increment device quota
 */
async function incrementDeviceQuota(req, res) {
  try {
    const { deviceId, fingerprint, ip, operationType, amount = 1, fileSize = 0 } = req.body;
    const clientIP = ip || getClientIP(req);
    
    if (!deviceId || !fingerprint) {
      return res.status(400).json({
        success: false,
        error: 'Device ID and fingerprint required',
        code: 'MISSING_DEVICE_INFO'
      });
    }
    
    // Get or create device quota
    const device = await DeviceQuota.getOrCreate(
      deviceId,
      fingerprint,
      clientIP,
      req.headers['user-agent']
    );
    
    // Get limits
    const limits = FREE_LIMITS[operationType] || FREE_LIMITS.imageRemover;
    const fileSizeMB = fileSize / (1024 * 1024);
    
    // Check if quota allows
    let allowed = true;
    
    if (operationType === 'imageRemover') {
      if (device.imageRemoverCount + amount > limits.count) {
        allowed = false;
      } else if (device.imageRemoverUploadMB + fileSizeMB > limits.uploadMB) {
        allowed = false;
      } else if (fileSizeMB > limits.maxFileSizeMB) {
        allowed = false;
      }
      
      if (allowed) {
        device.imageRemoverCount += amount;
        device.imageRemoverUploadMB += fileSizeMB;
      }
    } else if (operationType === 'pdfEdit') {
      if (device.pdfEditCount + amount > limits.count) {
        allowed = false;
      } else if (device.pdfEditUploadMB + fileSizeMB > limits.uploadMB) {
        allowed = false;
      } else if (fileSizeMB > limits.maxFileSizeMB) {
        allowed = false;
      }
      
      if (allowed) {
        device.pdfEditCount += amount;
        device.pdfEditUploadMB += fileSizeMB;
      }
    }
    
    if (allowed) {
      device.lastActivity = new Date();
      await device.save();
    }
    
    res.json({
      success: allowed,
      remaining: allowed ? (limits.count - (operationType === 'imageRemover' ? device.imageRemoverCount : device.pdfEditCount)) : 0,
      limit: limits.count,
      currentUsage: {
        count: operationType === 'imageRemover' ? device.imageRemoverCount : device.pdfEditCount,
        uploadMB: operationType === 'imageRemover' ? device.imageRemoverUploadMB : device.pdfEditUploadMB,
        downloadMB: device.imageRemoverDownloadMB || 0
      },
      message: allowed ? 'Quota incremented' : 'Quota limit exceeded'
    });
  } catch (error) {
    console.error('Increment device quota error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to increment quota',
      code: 'QUOTA_INCREMENT_ERROR'
    });
  }
}

/**
 * Get device IP address
 */
async function getDeviceIP(req, res) {
  try {
    const ip = getClientIP(req);
    res.json({
      success: true,
      ip: ip
    });
  } catch (error) {
    console.error('Get device IP error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get IP address',
      code: 'IP_ERROR'
    });
  }
}

/**
 * Get device quota status
 */
async function getDeviceQuotaStatus(req, res) {
  try {
    const { deviceId, fingerprint, ip } = req.body;
    const clientIP = ip || getClientIP(req);
    
    if (!deviceId || !fingerprint) {
      return res.status(400).json({
        success: false,
        error: 'Device ID and fingerprint required'
      });
    }
    
    const device = await DeviceQuota.findOne({
      deviceId: deviceId,
      currentMonth: new Date().toISOString().substring(0, 7)
    });
    
    if (!device) {
      return res.json({
        success: true,
        quota: {
          imageRemover: {
            count: 0,
            limit: FREE_LIMITS.imageRemover.count,
            uploadMB: 0,
            uploadLimitMB: FREE_LIMITS.imageRemover.uploadMB,
            downloadMB: 0,
            downloadLimitMB: FREE_LIMITS.imageRemover.downloadMB
          },
          pdfEdit: {
            count: 0,
            limit: FREE_LIMITS.pdfEdit.count,
            uploadMB: 0,
            uploadLimitMB: FREE_LIMITS.pdfEdit.uploadMB
          }
        }
      });
    }
    
    res.json({
      success: true,
      quota: {
        imageRemover: {
          count: device.imageRemoverCount,
          limit: FREE_LIMITS.imageRemover.count,
          uploadMB: device.imageRemoverUploadMB,
          uploadLimitMB: FREE_LIMITS.imageRemover.uploadMB,
          downloadMB: device.imageRemoverDownloadMB,
          downloadLimitMB: FREE_LIMITS.imageRemover.downloadMB
        },
        pdfEdit: {
          count: device.pdfEditCount,
          limit: FREE_LIMITS.pdfEdit.count,
          uploadMB: device.pdfEditUploadMB,
          uploadLimitMB: FREE_LIMITS.pdfEdit.uploadMB
        }
      }
    });
  } catch (error) {
    console.error('Get device quota status error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get quota status',
      code: 'QUOTA_STATUS_ERROR'
    });
  }
}

module.exports = {
  checkDeviceQuota: asyncHandler(checkDeviceQuota),
  incrementDeviceQuota: asyncHandler(incrementDeviceQuota),
  getDeviceIP: asyncHandler(getDeviceIP),
  getDeviceQuotaStatus: asyncHandler(getDeviceQuotaStatus)
};

