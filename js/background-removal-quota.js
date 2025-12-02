/**
 * Background Removal Quota Management
 * Free: 1MB upload, 150KB compressed download, 40 images/month, 10MB monthly quota
 * Premium: 50MB upload, original quality, 500MB monthly quota, login required
 * Device fingerprinting for free users (IP + device ID)
 */

import { getDeviceInfo, checkDeviceQuota, incrementDeviceQuota, getDeviceQuotaStatus } from './device-fingerprint.js';

// Quota limits
const FREE_LIMITS = {
  maxUploadSize: 1 * 1024 * 1024, // 1 MB per upload
  maxDownloadSize: 150 * 1024, // 150 KB compressed
  monthlyImages: 40, // 40 images per month
  monthlyQuota: 10 * 1024 * 1024 // 10 MB total upload + download
};

const PREMIUM_LIMITS = {
  maxUploadSize: 50 * 1024 * 1024, // 50 MB per upload
  maxDownloadSize: null, // No limit, original quality
  monthlyImages: null, // No limit
  monthlyQuota: 500 * 1024 * 1024 // 500 MB total upload + download
};

// Check if user is premium
async function isPremiumUser() {
  try {
    const { auth } = await import('./firebase-init.js');
    const user = auth?.currentUser;
    if (!user) return false;
    
    const token = await user.getIdToken();
    const apiBaseUrl = window.location.origin;
    
    const response = await fetch(`${apiBaseUrl}/api/subscription/status`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.isPremium === true || data.plan === 'premium';
    }
  } catch (error) {
    console.warn('Failed to check premium status:', error);
  }
  return false;
}

// Check upload quota before processing
export async function checkUploadQuota(fileSize) {
  const premium = await isPremiumUser();
  const limits = premium ? PREMIUM_LIMITS : FREE_LIMITS;
  
  // Check file size limit
  if (fileSize > limits.maxUploadSize) {
    const sizeMB = (fileSize / (1024 * 1024)).toFixed(2);
    const maxMB = (limits.maxUploadSize / (1024 * 1024)).toFixed(0);
    return {
      allowed: false,
      message: `File size (${sizeMB} MB) exceeds ${premium ? 'premium' : 'free'} limit of ${maxMB} MB per upload. ${premium ? '' : 'Upgrade to Premium for up to 50 MB per upload.'}`
    };
  }
  
  // Check monthly quota (for free users via device fingerprinting)
  if (!premium) {
    const quotaCheck = await checkDeviceQuota('backgroundRemoval');
    if (!quotaCheck.allowed) {
      return {
        allowed: false,
        message: quotaCheck.message || `Monthly limit reached. Free users can process ${FREE_LIMITS.monthlyImages} images per month (${(FREE_LIMITS.monthlyQuota / (1024 * 1024)).toFixed(0)} MB total). Upgrade to Premium for unlimited processing.`
      };
    }
    
    // Check monthly quota size
    const currentUsage = quotaCheck.currentUsage || {};
    const usedQuota = (currentUsage.uploadSize || 0) + (currentUsage.downloadSize || 0);
    const remainingQuota = FREE_LIMITS.monthlyQuota - usedQuota;
    
    if (fileSize > remainingQuota) {
      const remainingMB = (remainingQuota / (1024 * 1024)).toFixed(2);
      return {
        allowed: false,
        message: `Monthly quota exceeded. Remaining: ${remainingMB} MB. Free users have ${(FREE_LIMITS.monthlyQuota / (1024 * 1024)).toFixed(0)} MB monthly quota. Upgrade to Premium for 500 MB monthly quota.`
      };
    }
  }
  
  return { allowed: true };
}

// Compress image for free users (to 150KB)
export async function compressImageForFree(imageDataURL) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      // Calculate dimensions to fit 150KB
      let width = img.width;
      let height = img.height;
      let quality = 0.9;
      
      // Try to compress
      canvas.width = width;
      canvas.height = height;
      ctx.drawImage(img, 0, 0);
      
      let dataURL = canvas.toDataURL('image/png', quality);
      let size = (dataURL.length * 0.75) / 1024; // Approximate KB
      
      // If still too large, reduce dimensions
      if (size > 150) {
        const ratio = Math.sqrt(150 / size);
        width = Math.floor(width * ratio);
        height = Math.floor(height * ratio);
        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(img, 0, 0, width, height);
        dataURL = canvas.toDataURL('image/png', 0.85);
      }
      
      resolve(dataURL);
    };
    img.onerror = () => resolve(imageDataURL); // Fallback to original
    img.src = imageDataURL;
  });
}

// Track usage after successful processing
export async function trackUsage(uploadSize, downloadSize) {
  const premium = await isPremiumUser();
  
  if (premium) {
    // Track premium usage (if needed)
    try {
      const { auth } = await import('./firebase-init.js');
      const user = auth?.currentUser;
      if (user) {
        const token = await user.getIdToken();
        const apiBaseUrl = window.location.origin;
        
        await fetch(`${apiBaseUrl}/api/subscription/track-usage`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            type: 'backgroundRemoval',
            uploadSize,
            downloadSize
          })
        });
      }
    } catch (error) {
      console.warn('Failed to track premium usage:', error);
    }
  } else {
    // Track free usage via device fingerprinting
    await incrementDeviceQuota('backgroundRemoval', 1, uploadSize + downloadSize);
  }
}

// Get quota status for display
export async function getQuotaStatus() {
  const premium = await isPremiumUser();
  
  if (premium) {
    try {
      const { auth } = await import('./firebase-init.js');
      const user = auth?.currentUser;
      if (user) {
        const token = await user.getIdToken();
        const apiBaseUrl = window.location.origin;
        
        const response = await fetch(`${apiBaseUrl}/api/subscription/quota-status`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          return {
            isPremium: true,
            remainingImages: data.remainingImages || 'Unlimited',
            remainingQuota: data.remainingQuota || PREMIUM_LIMITS.monthlyQuota,
            totalQuota: PREMIUM_LIMITS.monthlyQuota,
            usedQuota: (data.remainingQuota || PREMIUM_LIMITS.monthlyQuota) - (data.remainingQuota || PREMIUM_LIMITS.monthlyQuota)
          };
        }
      }
    } catch (error) {
      console.warn('Failed to get premium quota status:', error);
    }
    
    return {
      isPremium: true,
      remainingImages: 'Unlimited',
      remainingQuota: PREMIUM_LIMITS.monthlyQuota,
      totalQuota: PREMIUM_LIMITS.monthlyQuota
    };
  } else {
    const quotaStatus = await getDeviceQuotaStatus();
    const currentUsage = quotaStatus.currentUsage || {};
    const usedImages = quotaStatus.usedImages || 0;
    const usedQuota = (currentUsage.uploadSize || 0) + (currentUsage.downloadSize || 0);
    
    return {
      isPremium: false,
      remainingImages: Math.max(0, FREE_LIMITS.monthlyImages - usedImages),
      totalImages: FREE_LIMITS.monthlyImages,
      remainingQuota: Math.max(0, FREE_LIMITS.monthlyQuota - usedQuota),
      totalQuota: FREE_LIMITS.monthlyQuota,
      usedImages,
      usedQuota
    };
  }
}

// Export for use in pages
window.backgroundRemovalQuota = {
  checkUploadQuota,
  compressImageForFree,
  trackUsage,
  getQuotaStatus,
  isPremiumUser,
  FREE_LIMITS,
  PREMIUM_LIMITS
};

