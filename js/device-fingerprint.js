/**
 * Device Fingerprinting and IP-based Quota Tracking
 * Prevents abuse by tracking usage by device/IP instead of just user login
 * Similar to how Cursor detects fake users
 * Works for both Image Remover and PDF Editing
 */

// Generate device fingerprint
function generateDeviceFingerprint() {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.textBaseline = 'top';
  ctx.font = '14px Arial';
  ctx.fillText('Device fingerprint', 2, 2);
  
  const fingerprint = [
    navigator.userAgent,
    navigator.language,
    screen.width + 'x' + screen.height,
    new Date().getTimezoneOffset(),
    canvas.toDataURL(),
    navigator.hardwareConcurrency || 'unknown',
    navigator.deviceMemory || 'unknown',
    navigator.platform
  ].join('|');
  
  // Create hash from fingerprint
  let hash = 0;
  for (let i = 0; i < fingerprint.length; i++) {
    const char = fingerprint.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  
  return Math.abs(hash).toString(36);
}

// Generate device ID (persistent across sessions)
function getDeviceId() {
  let deviceId = localStorage.getItem('deviceId');
  if (!deviceId) {
    deviceId = 'device_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('deviceId', deviceId);
  }
  return deviceId;
}

// Get client IP (via backend)
async function getClientIP() {
  try {
    const apiBaseUrl = window.location.origin;
    const response = await fetch(`${apiBaseUrl}/api/device/ip`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.ip || 'unknown';
    }
  } catch (error) {
    console.warn('Failed to get client IP:', error);
  }
  return 'unknown';
}

// Get device info
async function getDeviceInfo() {
  const deviceId = getDeviceId();
  const fingerprint = generateDeviceFingerprint();
  const ip = await getClientIP();
  
  return {
    deviceId,
    fingerprint,
    ip,
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
  };
}

// Check device quota (for both imageRemover and pdfEdit)
async function checkDeviceQuota(operationType = 'imageRemover') {
  try {
    const deviceInfo = await getDeviceInfo();
    const apiBaseUrl = window.location.origin;
    
    const response = await fetch(`${apiBaseUrl}/api/device/check-quota`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        deviceId: deviceInfo.deviceId,
        fingerprint: deviceInfo.fingerprint,
        ip: deviceInfo.ip,
        operationType: operationType
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      return {
        allowed: data.allowed,
        remaining: data.remaining || 0,
        limit: data.limit || 0,
        currentUsage: data.currentUsage || {},
        message: data.message || ''
      };
    } else {
      const error = await response.json().catch(() => ({}));
      return {
        allowed: false,
        remaining: 0,
        limit: 0,
        currentUsage: {},
        message: error.error || 'Failed to check quota'
      };
    }
  } catch (error) {
    console.error('Device quota check error:', error);
    // Allow on error (fail open) - but log it
    return {
      allowed: true,
      remaining: 999,
      limit: 999,
      currentUsage: {},
      message: 'Quota check failed, allowing operation'
    };
  }
}

// Increment device quota (for both imageRemover and pdfEdit)
async function incrementDeviceQuota(operationType = 'imageRemover', amount = 1, fileSize = 0) {
  try {
    const deviceInfo = await getDeviceInfo();
    const apiBaseUrl = window.location.origin;
    
    const response = await fetch(`${apiBaseUrl}/api/device/increment-quota`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        deviceId: deviceInfo.deviceId,
        fingerprint: deviceInfo.fingerprint,
        ip: deviceInfo.ip,
        operationType: operationType,
        amount: amount,
        fileSize: fileSize
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      return {
        success: data.success,
        remaining: data.remaining || 0,
        limit: data.limit || 0,
        currentUsage: data.currentUsage || {},
        message: data.message || ''
      };
    } else {
      const error = await response.json().catch(() => ({}));
      return {
        success: false,
        remaining: 0,
        limit: 0,
        currentUsage: {},
        message: error.error || 'Failed to increment quota'
      };
    }
  } catch (error) {
    console.error('Device quota increment error:', error);
    return {
      success: false,
      remaining: 0,
      limit: 0,
      currentUsage: {},
      message: 'Quota increment failed'
    };
  }
}

// Get device quota status
async function getDeviceQuotaStatus() {
  try {
    const deviceInfo = await getDeviceInfo();
    const apiBaseUrl = window.location.origin;
    
    const response = await fetch(`${apiBaseUrl}/api/device/quota-status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        deviceId: deviceInfo.deviceId,
        fingerprint: deviceInfo.fingerprint,
        ip: deviceInfo.ip
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.quota || {};
    }
  } catch (error) {
    console.error('Get device quota status error:', error);
  }
  return {};
}

// Export functions
export {
  getDeviceId,
  generateDeviceFingerprint,
  getDeviceInfo,
  getClientIP,
  checkDeviceQuota,
  incrementDeviceQuota,
  getDeviceQuotaStatus
};
