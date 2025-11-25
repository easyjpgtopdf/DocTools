/**
 * Complete Subscription Management System
 * Handles Razorpay payments, plan management, auto-expiry, and activity tracking
 */

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { getAuth, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';
import { getFirestore, doc, getDoc, setDoc, updateDoc, collection, query, where, getDocs, serverTimestamp, Timestamp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js';

// Initialize Firebase (use existing config)
let db;
let auth;

try {
  const firebaseConfig = JSON.parse(sessionStorage.getItem('firebaseConfig') || '{}');
  if (firebaseConfig.apiKey) {
    const app = initializeApp(firebaseConfig);
    db = getFirestore(app);
    auth = getAuth(app);
  }
} catch (e) {
  console.warn('Firebase not initialized, subscription features may be limited');
}

// Plan configurations
const PLANS = {
  free: {
    name: 'Free',
    price: 0,
    duration: Infinity, // Never expires
    features: {
      maxFileSize: 6 * 1024 * 1024, // 6 MB
      bgRemoverQuota: 1 * 1024 * 1024, // 1 MB
      totalTransferCap: 5 * 1024 * 1024 * 1024, // 5 GB
      priorityProcessing: false,
      emailInvoicing: false,
      premiumSupport: false
    }
  },
  premium50: {
    name: 'Premium 50',
    price: 3, // $3/month
    duration: 30, // 30 days
    features: {
      maxFileSize: 50 * 1024 * 1024, // 50 MB
      bgRemoverQuota: Infinity,
      totalTransferCap: Infinity,
      priorityProcessing: true,
      emailInvoicing: true,
      premiumSupport: true
    }
  },
  premium500: {
    name: 'Premium 500',
    price: 5, // $5/month
    duration: 30, // 30 days
    features: {
      maxFileSize: 500 * 1024 * 1024, // 500 MB
      bgRemoverQuota: Infinity,
      totalTransferCap: Infinity,
      priorityProcessing: true,
      emailInvoicing: true,
      premiumSupport: true
    }
  }
};

// Yearly plans (12 months)
const YEARLY_PLANS = {
  premium50: { ...PLANS.premium50, price: 20, duration: 365 }, // $20/year
  premium500: { ...PLANS.premium500, price: 50, duration: 365 } // $50/year
};

/**
 * Get current user subscription
 */
export async function getCurrentSubscription(userId) {
  if (!db || !userId) return { plan: 'free', status: 'active', expiresAt: null };
  
  try {
    const subDoc = await getDoc(doc(db, 'subscriptions', userId));
    if (!subDoc.exists()) {
      return { plan: 'free', status: 'active', expiresAt: null };
    }
    
    const data = subDoc.data();
    const expiresAt = data.expiresAt?.toDate();
    const now = new Date();
    
    // Check if subscription expired
    if (expiresAt && expiresAt < now && data.plan !== 'free') {
      // Auto-expire subscription
      await updateDoc(doc(db, 'subscriptions', userId), {
        plan: 'free',
        status: 'expired',
        expiredAt: serverTimestamp(),
        previousPlan: data.plan
      });
      return { plan: 'free', status: 'expired', expiresAt: null };
    }
    
    return {
      plan: data.plan || 'free',
      status: data.status || 'active',
      expiresAt: expiresAt,
      startDate: data.startDate?.toDate(),
      autopay: data.autopay || false,
      razorpaySubscriptionId: data.razorpaySubscriptionId || null
    };
  } catch (error) {
    console.error('Error getting subscription:', error);
    return { plan: 'free', status: 'active', expiresAt: null };
  }
}

/**
 * Get plan features for current user
 */
export async function getUserPlanFeatures(userId) {
  const subscription = await getCurrentSubscription(userId);
  const planKey = subscription.plan;
  return PLANS[planKey]?.features || PLANS.free.features;
}

/**
 * Check if user has access to a feature
 */
export async function hasFeatureAccess(userId, feature) {
  const features = await getUserPlanFeatures(userId);
  return features[feature] !== undefined && features[feature] !== false;
}

/**
 * Get user's currency based on browser locale
 */
function getUserCurrency() {
  // Try to detect from browser
  const locale = navigator.language || navigator.userLanguage || 'en-US';
  
  // Check if currency is stored in session
  const storedCurrency = sessionStorage.getItem('userCurrency');
  if (storedCurrency) {
    return storedCurrency;
  }
  
  // Detect from locale
  if (locale.includes('en-IN') || locale.includes('hi')) {
    return 'INR';
  }
  if (locale.includes('ja')) {
    return 'JPY';
  }
  if (locale.includes('ru')) {
    return 'RUB';
  }
  if (locale.includes('en-US') || locale.includes('en')) {
    return 'USD';
  }
  
  // Default to USD
  return 'USD';
}

/**
 * Initiate subscription purchase with Razorpay
 */
export async function initiateSubscriptionPurchase(planKey, billing = 'monthly', userId) {
  // If no userId provided, try to get it from auth
  if (!userId && auth) {
    const user = auth.currentUser;
    if (user) {
      userId = user.uid;
    } else {
      // Wait for auth state
      userId = await new Promise((resolve) => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
          unsubscribe();
          resolve(user ? user.uid : null);
        });
        setTimeout(() => {
          unsubscribe();
          resolve(null);
        }, 2000);
      });
    }
  }
  
  if (!userId) {
    // Store pending purchase and redirect to login
    const currentUrl = window.location.href;
    sessionStorage.setItem('pendingSubscription', JSON.stringify({ plan: planKey, billing }));
    window.location.href = `login.html?returnTo=${encodeURIComponent(currentUrl)}`;
    return;
  }
  
  const plan = billing === 'yearly' ? YEARLY_PLANS[planKey] : PLANS[planKey];
  if (!plan) {
    throw new Error('Invalid plan selected');
  }
  
  // Get user's currency (auto-detect)
  const userCurrency = getUserCurrency();
  
  // Create Razorpay order
  try {
    const response = await fetch('/api/subscriptions/create-order', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`,
        'Accept-Language': navigator.language || 'en-US'
      },
      body: JSON.stringify({
        plan: planKey,
        billing: billing,
        amount: plan.price, // Price in USD (will be converted on server)
        currency: userCurrency, // User's preferred currency
        userId: userId
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to create order');
    }
    
    const orderData = await response.json();
    
    // Initialize Razorpay checkout
    const options = {
      key: orderData.key_id || process.env.RAZORPAY_KEY_ID,
      amount: orderData.amount,
      currency: orderData.currency,
      name: 'easyjpgtopdf',
      description: `${plan.name} Plan - ${billing === 'yearly' ? 'Yearly' : 'Monthly'}`,
      order_id: orderData.orderId,
      prefill: {
        email: orderData.userEmail || '',
        name: orderData.userName || ''
      },
      theme: {
        color: '#4361ee'
      },
      handler: async function(response) {
        // Payment successful
        await handlePaymentSuccess(response, planKey, billing, userId, orderData.orderId, orderData.currency, orderData.convertedPrice);
      },
      modal: {
        ondismiss: function() {
          console.log('Payment cancelled');
        }
      }
    };
    
    const razorpay = new Razorpay(options);
    razorpay.open();
    
  } catch (error) {
    console.error('Error initiating subscription:', error);
    alert('Failed to initiate payment. Please try again.');
  }
}

/**
 * Handle successful payment
 */
async function handlePaymentSuccess(paymentResponse, planKey, billing, userId, orderId, currency, convertedAmount) {
  try {
    // Verify payment on server
    const verifyResponse = await fetch('/api/subscriptions/verify-payment', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify({
        razorpay_order_id: paymentResponse.razorpay_order_id,
        razorpay_payment_id: paymentResponse.razorpay_payment_id,
        razorpay_signature: paymentResponse.razorpay_signature,
        plan: planKey,
        billing: billing,
        userId: userId,
        orderId: orderId,
        currency: currency,
        amount: convertedAmount
      })
    });
    
    if (!verifyResponse.ok) {
      throw new Error('Payment verification failed');
    }
    
    const result = await verifyResponse.json();
    
    if (result.success) {
      // Update subscription in Firestore with actual currency and amount
      await activateSubscription(userId, planKey, billing, paymentResponse.razorpay_payment_id, currency, convertedAmount);
      
      // Redirect to dashboard
      window.location.href = 'dashboard.html#dashboard-overview';
    } else {
      throw new Error('Payment verification failed');
    }
  } catch (error) {
    console.error('Error handling payment:', error);
    alert('Payment verification failed. Please contact support.');
  }
}

/**
 * Activate subscription after payment
 */
async function activateSubscription(userId, planKey, billing, paymentId, currency = 'USD', amount = null) {
  if (!db) return;
  
  const plan = billing === 'yearly' ? YEARLY_PLANS[planKey] : PLANS[planKey];
  const now = new Date();
  const expiresAt = new Date(now.getTime() + plan.duration * 24 * 60 * 60 * 1000);
  
  // Use provided amount or fallback to plan price (in USD)
  const actualAmount = amount !== null ? amount : plan.price;
  
  await setDoc(doc(db, 'subscriptions', userId), {
    plan: planKey,
    status: 'active',
    startDate: Timestamp.fromDate(now),
    expiresAt: Timestamp.fromDate(expiresAt),
    billing: billing,
    paymentId: paymentId,
    currency: currency, // Store actual currency used
    autopay: false, // Can be enabled later
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp()
  }, { merge: true });
  
  // Record payment with actual currency and amount
  await setDoc(doc(db, 'payments', paymentId), {
    userId: userId,
    plan: planKey,
    amount: actualAmount, // Actual amount paid in user's currency
    currency: currency, // Actual currency used (not hardcoded)
    originalPriceUSD: plan.price, // Original USD price for reference
    billing: billing,
    status: 'completed',
    paymentDate: serverTimestamp(),
    orderId: paymentId
  });
}

/**
 * Enable/disable autopay
 */
export async function toggleAutopay(userId, enable) {
  if (!db) return;
  
  await updateDoc(doc(db, 'subscriptions', userId), {
    autopay: enable,
    updatedAt: serverTimestamp()
  });
}

/**
 * Track user activity
 */
export async function trackActivity(userId, activityType, details = {}) {
  if (!db) return;
  
  try {
    await setDoc(doc(collection(db, 'activities'), `${userId}_${Date.now()}`), {
      userId: userId,
      type: activityType,
      details: details,
      timestamp: serverTimestamp()
    });
  } catch (error) {
    console.error('Error tracking activity:', error);
  }
}

/**
 * Get user activity history
 */
export async function getUserActivity(userId, limit = 50) {
  if (!db) return [];
  
  try {
    const q = query(
      collection(db, 'activities'),
      where('userId', '==', userId)
    );
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    })).sort((a, b) => b.timestamp - a.timestamp).slice(0, limit);
  } catch (error) {
    console.error('Error getting activity:', error);
    return [];
  }
}

/**
 * Get auth token (helper function)
 */
async function getAuthToken() {
  if (!auth) return null;
  const user = auth.currentUser;
  if (!user) return null;
  return await user.getIdToken();
}

// Load Razorpay script
if (typeof Razorpay === 'undefined') {
  const script = document.createElement('script');
  script.src = 'https://checkout.razorpay.com/v1/checkout.js';
  script.async = true;
  document.head.appendChild(script);
}

// Export for use in other files
window.subscriptionService = {
  getCurrentSubscription,
  getUserPlanFeatures,
  hasFeatureAccess,
  initiateSubscriptionPurchase,
  toggleAutopay,
  trackActivity,
  getUserActivity,
  PLANS,
  YEARLY_PLANS
};

