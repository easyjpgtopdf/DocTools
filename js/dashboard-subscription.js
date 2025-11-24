/**
 * Dashboard Subscription Management
 * Loads and displays user subscription information
 */

import { getCurrentSubscription, getUserActivity, trackActivity } from './subscription.js';
import { getAuth, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';
import { getFirestore, collection, query, where, getDocs, orderBy, limit } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js';
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';

let db, auth;

// Initialize Firebase
try {
  const firebaseConfig = JSON.parse(sessionStorage.getItem('firebaseConfig') || '{}');
  if (firebaseConfig.apiKey) {
    const app = initializeApp(firebaseConfig);
    db = getFirestore(app);
    auth = getAuth(app);
  }
} catch (e) {
  console.warn('Firebase not initialized');
}

/**
 * Load and display subscription information
 */
export async function loadSubscriptionInfo() {
  if (!auth || !db) return;
  
  onAuthStateChanged(auth, async (user) => {
    if (!user) return;
    
    const userId = user.uid;
    
    try {
      // Get subscription
      const subscription = await getCurrentSubscription(userId);
      
      // Update plan display
      const planEl = document.querySelector('.user-plan');
      if (planEl) {
        planEl.textContent = subscription.plan === 'free' ? 'Free' : 
                           subscription.plan === 'premium50' ? 'Premium 50' : 
                           subscription.plan === 'premium500' ? 'Premium 500' : 'Free';
        
        // Add plan badge
        if (subscription.plan !== 'free') {
          planEl.style.color = '#4361ee';
          planEl.style.fontWeight = '600';
        }
      }
      
      // Display subscription details in orders panel
      await displaySubscriptionDetails(userId, subscription);
      
      // Load payment history
      await loadPaymentHistory(userId);
      
      // Load activity
      await loadUserActivity(userId);
      
    } catch (error) {
      console.error('Error loading subscription info:', error);
    }
  });
}

/**
 * Display subscription details
 */
async function displaySubscriptionDetails(userId, subscription) {
  const ordersCard = document.getElementById('orders-card');
  if (!ordersCard) return;
  
  let html = '<h3>Orders & Subscriptions</h3>';
  
  if (subscription.plan === 'free') {
    html += `
      <div class="subscription-info" style="background: #f8f9ff; padding: 20px; border-radius: 12px; margin: 20px 0;">
        <h4 style="margin: 0 0 10px 0; color: #0b1630;">Current Plan: Free</h4>
        <p style="color: #56607a; margin: 8px 0;">You're currently on the free plan. Upgrade to unlock premium features!</p>
        <a href="pricing.html" class="btn btn-primary" style="display: inline-block; margin-top: 12px; padding: 10px 24px; text-decoration: none; border-radius: 8px; background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; font-weight: 600;">Upgrade Now</a>
      </div>
    `;
  } else {
    const expiresAt = subscription.expiresAt;
    const now = new Date();
    const daysRemaining = expiresAt ? Math.ceil((expiresAt - now) / (1000 * 60 * 60 * 24)) : 0;
    const isExpiringSoon = daysRemaining <= 7 && daysRemaining > 0;
    const isExpired = daysRemaining <= 0;
    
    const planName = subscription.plan === 'premium50' ? 'Premium 50' : 'Premium 500';
    const statusColor = isExpired ? '#dc3545' : isExpiringSoon ? '#ffc107' : '#4bb543';
    const statusText = isExpired ? 'Expired' : isExpiringSoon ? 'Expiring Soon' : 'Active';
    
    html += `
      <div class="subscription-info" style="background: #f8f9ff; padding: 20px; border-radius: 12px; margin: 20px 0; border-left: 4px solid ${statusColor};">
        <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 16px;">
          <div>
            <h4 style="margin: 0 0 8px 0; color: #0b1630;">Current Plan: ${planName}</h4>
            <p style="margin: 4px 0; color: #56607a;">
              <strong>Status:</strong> <span style="color: ${statusColor}; font-weight: 600;">${statusText}</span>
            </p>
            ${expiresAt ? `
              <p style="margin: 4px 0; color: #56607a;">
                <strong>Expires:</strong> ${expiresAt.toLocaleDateString()} 
                ${!isExpired ? `(${daysRemaining} days remaining)` : ''}
              </p>
            ` : ''}
            ${subscription.startDate ? `
              <p style="margin: 4px 0; color: #56607a;">
                <strong>Started:</strong> ${subscription.startDate.toLocaleDateString()}
              </p>
            ` : ''}
            <p style="margin: 4px 0; color: #56607a;">
              <strong>Billing:</strong> ${subscription.billing === 'yearly' ? 'Yearly' : 'Monthly'}
            </p>
            ${subscription.autopay ? `
              <p style="margin: 4px 0; color: #4bb543;">
                <i class="fas fa-sync-alt"></i> Autopay Enabled
              </p>
            ` : ''}
          </div>
          <div style="text-align: right;">
            ${isExpired ? `
              <a href="pricing.html" class="btn btn-primary" style="display: inline-block; padding: 10px 24px; text-decoration: none; border-radius: 8px; background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; font-weight: 600;">Renew Subscription</a>
            ` : isExpiringSoon ? `
              <a href="pricing.html" class="btn btn-primary" style="display: inline-block; padding: 10px 24px; text-decoration: none; border-radius: 8px; background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; font-weight: 600;">Renew Now</a>
            ` : `
              <a href="pricing.html" class="btn btn-outline" style="display: inline-block; padding: 10px 24px; text-decoration: none; border-radius: 8px; border: 2px solid #4361ee; color: #4361ee; font-weight: 600;">Manage Plan</a>
            `}
          </div>
        </div>
      </div>
    `;
  }
  
  // Add existing order list items
  const existingOrders = ordersCard.querySelector('.order-list');
  if (existingOrders) {
    html += existingOrders.outerHTML;
  } else {
    html += `
      <ul class="order-list" style="list-style: none; padding: 0; margin: 20px 0;">
        <li class="order-item" style="padding: 12px; background: #f8f9ff; border-radius: 8px; margin: 8px 0;">
          <strong>Digital products activate instantly</strong><br>
          Upcoming purchases will appear here with invoice IDs once you complete a payment.
        </li>
      </ul>
    `;
  }
  
  ordersCard.innerHTML = html;
}

/**
 * Load payment history
 */
async function loadPaymentHistory(userId) {
  if (!db) return;
  
  try {
    const paymentsRef = collection(db, 'payments');
    const q = query(
      paymentsRef,
      where('userId', '==', userId),
      orderBy('paymentDate', 'desc'),
      limit(10)
    );
    
    const snapshot = await getDocs(q);
    const paymentList = document.querySelector('.payment-list');
    
    if (!paymentList) return;
    
    if (snapshot.empty) {
      paymentList.innerHTML = '<li>No payments found yet.</li>';
      return;
    }
    
    let html = '';
    snapshot.docs.forEach(doc => {
      const payment = doc.data();
      const date = payment.paymentDate?.toDate?.() || new Date();
      const planName = payment.plan === 'premium50' ? 'Premium 50' : 
                      payment.plan === 'premium500' ? 'Premium 500' : 'Free';
      
      html += `
        <li style="padding: 16px; background: #f8f9ff; border-radius: 8px; margin: 8px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <strong style="color: #0b1630;">${planName} Plan</strong>
            <p style="margin: 4px 0; color: #56607a; font-size: 0.9rem;">
              ${date.toLocaleDateString()} • ₹${payment.amount || 0} • ${payment.billing === 'yearly' ? 'Yearly' : 'Monthly'}
            </p>
            <p style="margin: 4px 0; color: #4bb543; font-size: 0.85rem;">
              <i class="fas fa-check-circle"></i> ${payment.status || 'Completed'}
            </p>
          </div>
          <div style="text-align: right;">
            <span style="color: #4361ee; font-weight: 600;">₹${payment.amount || 0}</span>
            ${payment.paymentId ? `
              <p style="margin: 4px 0; color: #9ca3af; font-size: 0.75rem;">ID: ${payment.paymentId.substring(0, 12)}...</p>
            ` : ''}
          </div>
        </li>
      `;
    });
    
    paymentList.innerHTML = html;
    
  } catch (error) {
    console.error('Error loading payment history:', error);
    const paymentList = document.querySelector('.payment-list');
    if (paymentList) {
      paymentList.innerHTML = '<li>Error loading payment history.</li>';
    }
  }
}

/**
 * Load user activity
 */
async function loadUserActivity(userId) {
  try {
    const activities = await getUserActivity(userId, 10);
    const usageList = document.querySelector('.usage-list');
    
    if (!usageList) return;
    
    if (activities.length === 0) {
      usageList.innerHTML = '<li>No activity recorded yet.</li>';
      return;
    }
    
    let html = '';
    activities.forEach(activity => {
      const timestamp = activity.timestamp?.toDate?.() || new Date();
      const type = activity.type || 'unknown';
      const details = activity.details || {};
      
      html += `
        <li style="padding: 12px; background: #f8f9ff; border-radius: 8px; margin: 8px 0; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong style="color: #0b1630;">${formatActivityType(type)}</strong>
            ${details.toolName ? `<p style="margin: 4px 0; color: #56607a; font-size: 0.9rem;">${details.toolName}</p>` : ''}
            <p style="margin: 4px 0; color: #9ca3af; font-size: 0.85rem;">${timestamp.toLocaleString()}</p>
          </div>
        </li>
      `;
    });
    
    usageList.innerHTML = html;
    
  } catch (error) {
    console.error('Error loading activity:', error);
  }
}

/**
 * Format activity type for display
 */
function formatActivityType(type) {
  const types = {
    'file_upload': 'File Uploaded',
    'file_converted': 'File Converted',
    'tool_used': 'Tool Used',
    'subscription_purchased': 'Subscription Purchased',
    'subscription_renewed': 'Subscription Renewed',
    'subscription_expired': 'Subscription Expired'
  };
  return types[type] || type;
}

// Auto-load on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadSubscriptionInfo);
} else {
  loadSubscriptionInfo();
}

// Export for manual calls
window.loadSubscriptionInfo = loadSubscriptionInfo;

