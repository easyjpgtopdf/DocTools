/**
 * File Size Limits and Subscription-based Access Control
 * Integrates with subscription service to enforce plan-based limits
 */

import { getUserPlanFeatures, hasFeatureAccess, trackActivity } from './subscription.js';
import { getAuth, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';

let auth;

// Initialize Firebase
try {
  const firebaseConfig = JSON.parse(sessionStorage.getItem('firebaseConfig') || '{}');
  if (firebaseConfig.apiKey) {
    const app = initializeApp(firebaseConfig);
    auth = getAuth(app);
  }
} catch (e) {
  console.warn('Firebase not initialized');
}

/**
 * Get current user ID
 */
async function getCurrentUserId() {
  if (!auth) {
    return sessionStorage.getItem('userId') || sessionStorage.getItem('user') || null;
  }
  
  const user = auth.currentUser;
  if (user) return user.uid;
  
  // Wait for auth state
  return new Promise((resolve) => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      unsubscribe();
      resolve(user ? user.uid : null);
    });
    setTimeout(() => resolve(null), 1000);
  });
}

/**
 * Check if file size is within plan limits
 */
export async function checkFileSizeLimit(fileSize) {
  const userId = await getCurrentUserId();
  if (!userId) {
    // Not logged in - use free plan limits
    return fileSize <= 6 * 1024 * 1024; // 6 MB
  }
  
  try {
    const features = await getUserPlanFeatures(userId);
    return fileSize <= features.maxFileSize;
  } catch (error) {
    console.error('Error checking file size limit:', error);
    return fileSize <= 6 * 1024 * 1024; // Default to free plan
  }
}

/**
 * Get max file size for current user
 */
export async function getMaxFileSize() {
  const userId = await getCurrentUserId();
  if (!userId) {
    return 6 * 1024 * 1024; // 6 MB for free
  }
  
  try {
    const features = await getUserPlanFeatures(userId);
    return features.maxFileSize;
  } catch (error) {
    return 6 * 1024 * 1024; // Default to free
  }
}

/**
 * Initiate purchase flow (redirects to pricing if not logged in)
 */
export async function initiatePurchase(plan, billing = 'monthly') {
  const userId = await getCurrentUserId();
  
  if (!userId) {
    // Store pending purchase and redirect to login
    sessionStorage.setItem('pendingPurchase', JSON.stringify({ plan, billing }));
    window.location.href = `login.html?returnTo=${encodeURIComponent('pricing.html')}`;
    return;
  }
  
  // Import and use subscription service
  try {
    const { initiateSubscriptionPurchase } = await import('./subscription.js');
    await initiateSubscriptionPurchase(plan, billing, userId);
  } catch (error) {
    console.error('Error initiating purchase:', error);
    // Fallback: redirect to pricing page
    window.location.href = 'pricing.html';
  }
}

/**
 * Track tool usage
 */
export async function trackToolUsage(toolName, fileSize = 0) {
  const userId = await getCurrentUserId();
  if (!userId) return;
  
  try {
    await trackActivity(userId, 'tool_used', {
      toolName: toolName,
      fileSize: fileSize,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error tracking tool usage:', error);
  }
}

// Export for global use
window.limitsService = {
  checkFileSizeLimit,
  getMaxFileSize,
  initiatePurchase,
  trackToolUsage
};

