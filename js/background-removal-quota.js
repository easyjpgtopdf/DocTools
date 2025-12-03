/**
 * Background Removal Quota Management
 * Free: 1MB upload, 150KB compressed download, 40 images/month, 10MB monthly quota
 * Premium: 50MB upload, original quality, 500MB monthly quota, login required
 * Device fingerprinting for free users (IP + device ID)
 */

// Quota limits - ALL REMOVED (unlimited for all users)
const FREE_LIMITS = {
  maxUploadSize: null, // No limit
  maxDownloadSize: null, // No limit
  monthlyImages: null, // No limit
  monthlyQuota: null // No limit
};

const PREMIUM_LIMITS = {
  maxUploadSize: null, // No limit
  maxDownloadSize: null, // No limit
  monthlyImages: null, // No limit
  monthlyQuota: null // No limit
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

// Check upload quota before processing - ALL LIMITS REMOVED
export async function checkUploadQuota(fileSize) {
  // No limits - always allowed
  return { allowed: true };
}

export async function compressImageForFree(imageDataURL) {
  return imageDataURL;
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
  }
  
  return {
    isPremium: false,
    remainingImages: 'Unlimited',
    totalImages: 'Unlimited',
    remainingQuota: 'Unlimited',
    totalQuota: 'Unlimited',
    usedImages: 0,
    usedQuota: 0
  };
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

