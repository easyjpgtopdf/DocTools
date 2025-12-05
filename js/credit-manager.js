/**
 * Complete Credit Management System
 * Handles credit purchase, deduction, balance checking, and transaction history
 */

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { getAuth, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';
import { getFirestore, doc, getDoc, setDoc, updateDoc, collection, query, where, getDocs, serverTimestamp, increment, arrayUnion } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js';

// Get API base URL
function getApiBaseUrl() {
  const hostname = window.location.hostname;
  const isDevelopment = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.');
  if (isDevelopment) {
    return 'http://localhost:3000';
  }
  const origin = window.location.origin;
  return origin.endsWith('/') ? origin.slice(0, -1) : origin;
}

const API_BASE_URL = getApiBaseUrl();

// Initialize Firebase
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
  console.warn('Firebase not initialized, credit features may be limited');
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
  
  return new Promise((resolve) => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      unsubscribe();
      resolve(user ? user.uid : null);
    });
    setTimeout(() => resolve(null), 2000);
  });
}

/**
 * Initialize user credits (called on signup/first login)
 */
export async function initializeUserCredits(userId) {
  if (!db || !userId) return;
  
  try {
    const userRef = doc(db, 'users', userId);
    const userDoc = await getDoc(userRef);
    
    if (!userDoc.exists()) {
      // Create user with initial credits
      await setDoc(userRef, {
        credits: 0,
        totalCreditsEarned: 0,
        totalCreditsUsed: 0,
        creditTransactions: [],
        createdAt: serverTimestamp(),
        lastCreditUpdate: serverTimestamp()
      }, { merge: true });
    } else {
      // Ensure credits field exists
      const data = userDoc.data();
      if (data.credits === undefined) {
        await updateDoc(userRef, {
          credits: 0,
          totalCreditsEarned: 0,
          totalCreditsUsed: 0,
          creditTransactions: [],
          lastCreditUpdate: serverTimestamp()
        });
      }
    }
  } catch (error) {
    console.error('Error initializing user credits:', error);
  }
}

/**
 * Get user credit balance
 */
export async function getUserCredits(userId) {
  if (!db || !userId) return { credits: 0, error: 'Database not available' };
  
  try {
    const userRef = doc(db, 'users', userId);
    const userDoc = await getDoc(userRef);
    
    if (!userDoc.exists()) {
      await initializeUserCredits(userId);
      return { credits: 0 };
    }
    
    const data = userDoc.data();
    return {
      credits: data.credits || 0,
      totalCreditsEarned: data.totalCreditsEarned || 0,
      totalCreditsUsed: data.totalCreditsUsed || 0
    };
  } catch (error) {
    console.error('Error getting user credits:', error);
    return { credits: 0, error: error.message };
  }
}

/**
 * Check if user has sufficient credits
 */
export async function hasSufficientCredits(userId, requiredCredits) {
  const creditInfo = await getUserCredits(userId);
  
  // Check subscription for unlimited credits
  try {
    const subscriptionRef = doc(db, 'subscriptions', userId);
    const subscriptionDoc = await getDoc(subscriptionRef);
    
    if (subscriptionDoc.exists()) {
      const subData = subscriptionDoc.data();
      if (subData.plan === 'premium' || subData.plan === 'business') {
        // Premium/Business users may have unlimited credits for some features
        const features = subData.features || {};
        if (features.unlimitedBackgroundRemoval) {
          return { hasCredits: true, unlimited: true };
        }
      }
    }
  } catch (e) {
    // Continue with credit check
  }
  
  return {
    hasCredits: (creditInfo.credits || 0) >= requiredCredits,
    creditsAvailable: creditInfo.credits || 0,
    requiredCredits: requiredCredits
  };
}

/**
 * Deduct credits from user account
 */
export async function deductCredits(userId, amount, reason = 'Background removal', metadata = {}) {
  if (!db || !userId) {
    return { success: false, error: 'Database not available' };
  }
  
  try {
    // Check if user has sufficient credits
    const creditCheck = await hasSufficientCredits(userId, amount);
    
    if (creditCheck.unlimited) {
      // User has unlimited credits, no deduction needed
      return {
        success: true,
        creditsDeducted: 0,
        creditsRemaining: 'unlimited',
        unlimited: true
      };
    }
    
    if (!creditCheck.hasCredits) {
      return {
        success: false,
        error: 'Insufficient credits',
        creditsAvailable: creditCheck.creditsAvailable,
        requiredCredits: amount
      };
    }
    
    const userRef = doc(db, 'users', userId);
    const userDoc = await getDoc(userRef);
    const currentCredits = userDoc.data()?.credits || 0;
    
    // Deduct credits
    await updateDoc(userRef, {
      credits: increment(-amount),
      totalCreditsUsed: increment(amount),
      lastCreditUpdate: serverTimestamp()
    });
    
    // Record transaction
    const transactionRef = doc(collection(db, 'users', userId, 'creditTransactions'));
    await setDoc(transactionRef, {
      type: 'deduction',
      amount: amount,
      reason: reason,
      creditsBefore: currentCredits,
      creditsAfter: currentCredits - amount,
      timestamp: serverTimestamp(),
      metadata: metadata
    });
    
    return {
      success: true,
      creditsDeducted: amount,
      creditsRemaining: currentCredits - amount,
      creditsBefore: currentCredits
    };
  } catch (error) {
    console.error('Error deducting credits:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Add credits to user account (for purchases, bonuses, etc.)
 */
export async function addCredits(userId, amount, reason = 'Credit purchase', metadata = {}) {
  if (!db || !userId) {
    return { success: false, error: 'Database not available' };
  }
  
  try {
    const userRef = doc(db, 'users', userId);
    const userDoc = await getDoc(userRef);
    
    if (!userDoc.exists()) {
      await initializeUserCredits(userId);
    }
    
    const currentCredits = userDoc.data()?.credits || 0;
    
    // Add credits
    await updateDoc(userRef, {
      credits: increment(amount),
      totalCreditsEarned: increment(amount),
      lastCreditUpdate: serverTimestamp()
    });
    
    // Record transaction
    const transactionRef = doc(collection(db, 'users', userId, 'creditTransactions'));
    await setDoc(transactionRef, {
      type: 'addition',
      amount: amount,
      reason: reason,
      creditsBefore: currentCredits,
      creditsAfter: currentCredits + amount,
      timestamp: serverTimestamp(),
      metadata: metadata
    });
    
    return {
      success: true,
      creditsAdded: amount,
      creditsRemaining: currentCredits + amount,
      creditsBefore: currentCredits
    };
  } catch (error) {
    console.error('Error adding credits:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Get credit transaction history
 */
export async function getCreditHistory(userId, limit = 50) {
  if (!db || !userId) return [];
  
  try {
    const transactionsRef = collection(db, 'users', userId, 'creditTransactions');
    const q = query(transactionsRef);
    const snapshot = await getDocs(q);
    
    return snapshot.docs
      .map(doc => ({
        id: doc.id,
        ...doc.data()
      }))
      .sort((a, b) => {
        const aTime = a.timestamp?.toDate?.() || new Date(a.timestamp);
        const bTime = b.timestamp?.toDate?.() || new Date(b.timestamp);
        return bTime - aTime;
      })
      .slice(0, limit);
  } catch (error) {
    console.error('Error getting credit history:', error);
    return [];
  }
}

/**
 * Purchase credits via Razorpay
 */
export async function purchaseCredits(creditPack, userId) {
  if (!userId) {
    // Store pending purchase and redirect to login
    sessionStorage.setItem('pendingCreditPurchase', JSON.stringify({
      creditPack: creditPack.id,
      timestamp: Date.now()
    }));
    window.location.href = `login.html?returnTo=${encodeURIComponent(window.location.href)}`;
    return;
  }
  
  // Credit pack configurations
  // Base prices in USD, converted to INR at $1 = ₹95, with 18% GST
  const USD_TO_INR = 95;
  const GST_RATE = 0.18; // 18% GST
  
  const creditPacks = {
    'pack-50': { 
      credits: 50, 
      priceUSD: 4, 
      priceINR: Math.round(4 * USD_TO_INR * (1 + GST_RATE)), // ₹448 (₹380 + 18% GST)
      name: '50 Credits Pack',
      description: 'Perfect for regular users'
    },
    'pack-200': { 
      credits: 200, 
      priceUSD: 15, 
      priceINR: Math.round(15 * USD_TO_INR * (1 + GST_RATE)), // ₹1,682 (₹1,425 + 18% GST)
      name: '200 Credits Pack',
      description: 'Best value for power users'
    }
  };
  
  // Get user currency (INR for India, USD for others)
  function getUserCurrency() {
    const locale = navigator.language || navigator.userLanguage || 'en-US';
    const storedCurrency = sessionStorage.getItem('userCurrency');
    if (storedCurrency) return storedCurrency;
    
    if (locale.includes('en-IN') || locale.includes('hi')) {
      return 'INR';
    }
    return 'USD';
  }
  
    const pack = creditPacks[creditPack.id] || creditPack;
    const userCurrency = getUserCurrency();
    const amount = userCurrency === 'INR' ? pack.priceINR : pack.priceUSD;
    
    try {
        // Create Razorpay order
        const response = await fetch(`${API_BASE_URL}/api/payment/purchase`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${await getAuthToken()}`
            },
            body: JSON.stringify({
                userId: userId,
                creditPack: creditPack.id,
                credits: pack.credits,
                amount: amount,
                amountUSD: pack.priceUSD,
                amountINR: pack.priceINR,
                currency: userCurrency,
                gstIncluded: userCurrency === 'INR' ? true : false,
                gstRate: userCurrency === 'INR' ? GST_RATE : 0
            })
        });
    
    if (!response.ok) {
      throw new Error('Failed to create order');
    }
    
    const orderData = await response.json();
    
    // Initialize Razorpay
    await loadRazorpayScript();
    
    const options = {
      key: orderData.key_id || orderData.key || '',
      amount: orderData.amount,
      currency: orderData.currency || 'INR',
      name: 'easyjpgtopdf',
      description: `${pack.name} - ${pack.credits} Credits`,
      order_id: orderData.orderId || orderData.id,
      handler: async function(paymentResponse) {
        await handleCreditPurchaseSuccess(
          paymentResponse,
          userId,
          pack,
          orderData.orderId || orderData.id
        );
      },
      theme: {
        color: '#4361ee'
      }
    };
    
    if (!options.key) {
      throw new Error('Razorpay key not found');
    }
    
    const razorpay = new Razorpay(options);
    razorpay.open();
    
  } catch (error) {
    console.error('Error purchasing credits:', error);
    alert('Failed to initiate credit purchase. Please try again.');
  }
}

/**
 * Handle successful credit purchase
 */
async function handleCreditPurchaseSuccess(paymentResponse, userId, pack, orderId) {
  try {
    // Verify payment
    const verifyResponse = await fetch(`${API_BASE_URL}/api/payment/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify({
        orderId: orderId,
        paymentId: paymentResponse.razorpay_payment_id,
        signature: paymentResponse.razorpay_signature,
        userId: userId,
        credits: pack.credits
      })
    });
    
    if (!verifyResponse.ok) {
      throw new Error('Payment verification failed');
    }
    
    const result = await verifyResponse.json();
    
    if (result.success) {
      // Add credits to user account
      await addCredits(userId, pack.credits, 'Credit purchase', {
        orderId: orderId,
        paymentId: paymentResponse.razorpay_payment_id,
        packId: pack.id
      });
      
      alert(`Success! ${pack.credits} credits added to your account.`);
      
      // Reload page or update UI
      if (window.location.pathname.includes('dashboard')) {
        window.location.reload();
      } else {
        window.location.href = 'dashboard.html#credits';
      }
    } else {
      throw new Error('Payment verification failed');
    }
  } catch (error) {
    console.error('Error handling credit purchase:', error);
    alert('Payment verification failed. Please contact support.');
  }
}

/**
 * Get auth token helper
 */
async function getAuthToken() {
  if (!auth) return null;
  const user = auth.currentUser;
  if (!user) return null;
  return await user.getIdToken();
}

/**
 * Load Razorpay script
 */
function loadRazorpayScript() {
  return new Promise((resolve, reject) => {
    if (typeof Razorpay !== 'undefined') {
      resolve();
      return;
    }
    
    const existingScript = document.querySelector('script[src*="checkout.razorpay.com"]');
    if (existingScript) {
      existingScript.onload = resolve;
      existingScript.onerror = reject;
      return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => {
      if (typeof Razorpay !== 'undefined') {
        resolve();
      } else {
        reject(new Error('Razorpay script loaded but Razorpay object not found'));
      }
    };
    script.onerror = () => reject(new Error('Failed to load Razorpay script'));
    document.head.appendChild(script);
    
    setTimeout(() => {
      if (typeof Razorpay === 'undefined') {
        reject(new Error('Razorpay script loading timeout'));
      }
    }, 10000);
  });
}

// Auto-initialize credits for new users
if (auth) {
  onAuthStateChanged(auth, async (user) => {
    if (user) {
      await initializeUserCredits(user.uid);
    }
  });
}

// Export for global use
window.creditManager = {
  getUserCredits,
  hasSufficientCredits,
  deductCredits,
  addCredits,
  getCreditHistory,
  purchaseCredits,
  initializeUserCredits
};

// Export all functions (purchaseCredits, getCreditHistory, addCredits, deductCredits, hasSufficientCredits, and initializeUserCredits already exported above as named exports)
export {
  getUserCredits
  // purchaseCredits already exported at line 301 as: export async function purchaseCredits
  // getCreditHistory already exported at line 273 as: export async function getCreditHistory
  // addCredits already exported at line 224 as: export async function addCredits
  // deductCredits already exported at line 158 as: export async function deductCredits
  // hasSufficientCredits already exported at line 126 as: export async function hasSufficientCredits
  // initializeUserCredits already exported as named export above
};

