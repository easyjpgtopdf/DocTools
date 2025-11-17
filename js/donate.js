// Payment donation handler - v2.2 (Added Firestore payment tracking)
import { auth, setPendingAction } from "./auth.js";
import { API_BASE_URL } from "./config.js";
import { db } from "./firebase-init.js";

const donateForm = document.getElementById("donate-form");
const amountInput = document.getElementById("donate-amount");
const currencySelect = document.getElementById("donate-currency");
const gatewayOptions = Array.from(document.querySelectorAll('input[name="donate-gateway"]'));
const typeOptions = Array.from(document.querySelectorAll('input[name="donate-type"]'));
const messageEl = document.getElementById("donate-message");

let pendingDonation = null;

function showMessage(text, { hidden = false } = {}) {
  if (!messageEl) return;
  if (hidden || !text) {
    messageEl.hidden = true;
    messageEl.textContent = "";
    return;
  }
  messageEl.hidden = false;
  messageEl.textContent = text;
}

function selectGateway() {
  const selected = gatewayOptions.find((option) => option.checked);
  return selected ? selected.value : "razorpay";
}

function highlightGatewaySelection() {
  document.querySelectorAll('.donate-gateway-option').forEach((label) => {
    const input = label.querySelector('input[type="radio"]');
    if (input && input.checked) {
      label.classList.add('selected');
    } else {
      label.classList.remove('selected');
    }
  });
}

async function initiateStripeDonation(user, donation) {
  if (!user || !donation) {
    return;
  }

  showMessage("Preparing secure checkout...");

  try {
    const apiUrl = `${API_BASE_URL}/api/payments/create-donation-session`;
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${await user.getIdToken()}`,
      },
      body: JSON.stringify(donation),
    });

    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const payload = await response.json();

    if (payload?.checkoutUrl) {
      window.location.href = payload.checkoutUrl;
      return;
    }

    throw new Error("Missing checkout URL in server response.");
  } catch (error) {
    console.error("Donation checkout failed:", error);
    showMessage(
      "Unable to start the donation checkout right now. Please try again in a moment."
    );
  }
}

async function initiateRazorpayDonation(user, donation) {
  if (!user || !donation) {
    return;
  }

  if (!window.Razorpay) {
    showMessage("Razorpay checkout is still loading. Please try again in a moment.");
    return;
  }

  showMessage("Creating secure Razorpay order...");

  try {
    // Call backend to create Razorpay order
    const apiUrl = `${API_BASE_URL}/api/create-order`;
    
    console.log('🔍 Donation API Debug:', {
      API_BASE_URL,
      endpoint: '/api/create-order',
      fullUrl: apiUrl,
      amount: donation.amount,
      currency: donation.currency || "INR"
    });
    
    showMessage("Creating secure Razorpay order...");

    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        amount: donation.amount,
        currency: donation.currency || "INR",
        name: user.displayName || "Donor",
        email: user.email || "",
        firebaseUid: user.uid || ""
      }),
    });

    console.log('📊 API Response:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ API Error Response:', errorText);
      throw new Error(`Server error: ${response.status} - ${response.statusText}`);
    }

    const payload = await response.json();

    console.log('✅ Order Created - Full Payload:', payload);
    console.log('📦 Payload Structure Check:', {
      hasData: !!payload.data,
      hasDirectId: !!payload.id,
      payloadKeys: Object.keys(payload)
    });

    // Extract data from response (backend sends data in 'data' object)
    const orderData = payload.data || payload;

    console.log('🔍 Order Data Extracted:', {
      id: orderData.id,
      key: orderData.key,
      amount: orderData.amount,
      currency: orderData.currency
    });

    if (!orderData?.id || !orderData?.key) {
      console.error('❌ Missing required fields:', { 
        orderData, 
        payload,
        hasId: !!orderData?.id,
        hasKey: !!orderData?.key,
        idValue: orderData?.id,
        keyValue: orderData?.key
      });
      throw new Error("Incomplete Razorpay order payload. Missing id or key.");
    }

    console.log('✅ Validation passed - Opening Razorpay checkout');

    // Create Razorpay options
    const options = {
      key: orderData.key,
      order_id: orderData.id,
      amount: orderData.amountInPaise || orderData.amount,
      currency: orderData.currency || "INR",
      name: "easyjpgtopdf",
      description: `Donation - ${donation.donationType}`,
      receipt: orderData.receipt,
      prefill: {
        name: user.displayName || "",
        email: user.email || "",
        contact: user.phoneNumber || "",  // Auto-fill phone if available from Google account
      },
      notes: {
        donationType: donation.donationType,
        motive: donation.motive
      },
      handler: async (razorpayResponse) => {
        console.log("🎉 Razorpay payment success!", razorpayResponse);
        console.log("📦 Payment Details:", {
          paymentId: razorpayResponse.razorpay_payment_id,
          orderId: razorpayResponse.razorpay_order_id,
          signature: razorpayResponse.razorpay_signature
        });
        
        showMessage("Payment successful! Saving to database...", { hidden: false });
        
        // Save payment to Firestore immediately
        let firestoreSaved = false;
        try {
          console.log("🔄 Attempting Firestore save...");
          console.log("📍 User UID:", user.uid);
          console.log("📍 Database instance:", db ? "✅ Available" : "❌ Not available");
          
          if (!db) {
            throw new Error("Firestore database not initialized");
          }
          
          const { doc, setDoc, serverTimestamp } = await import("https://www.gstatic.com/firebasejs/10.14.0/firebase-firestore.js");
          
          const paymentData = {
            orderId: razorpayResponse.razorpay_order_id || orderData.id,
            paymentId: razorpayResponse.razorpay_payment_id || "",
            signature: razorpayResponse.razorpay_signature || "",
            amount: donation.amount,
            currency: donation.currency || "INR",
            status: "succeeded",
            paymentStatus: "captured",
            method: "razorpay",
            name: user.displayName || "Donor",
            email: user.email || "",
            contact: "", // Will be updated by webhook if user entered mobile
            createdAt: serverTimestamp(),
            updatedAt: serverTimestamp()
          };

          const docId = razorpayResponse.razorpay_order_id || orderData.id;
          const paymentRef = doc(db, "payments", user.uid, "records", docId);
          
          console.log("💾 Saving to path:", `payments/${user.uid}/records/${docId}`);
          console.log("💾 Payment data:", paymentData);
          
          await setDoc(paymentRef, paymentData, { merge: true });
          
          firestoreSaved = true;
          console.log("✅ SUCCESS! Payment saved to Firestore:", docId);
          showMessage("✅ Payment recorded! Sending receipt email...", { hidden: false });
        } catch (firestoreError) {
          console.error("❌ FIRESTORE SAVE FAILED:", firestoreError);
          console.error("Error details:", {
            message: firestoreError.message,
            code: firestoreError.code,
            stack: firestoreError.stack
          });
          showMessage("⚠️ Payment successful but dashboard update delayed. Check email for receipt.", { hidden: false });
          // Continue anyway - webhook will handle it
        }
        
        // Send receipt email
        try {
          const emailResponse = await fetch(`${API_BASE_URL}/api/send-receipt-email`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: user.email || "",
              name: user.displayName || "Donor",
              amount: donation.amount,
              currency: donation.currency || "INR",
              transactionId: razorpayResponse.razorpay_payment_id || "",
              orderId: razorpayResponse.razorpay_order_id || orderData.id,
              paymentMethod: "Razorpay",
              date: new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
            }),
          });

          const emailResult = await emailResponse.json();
          if (emailResult.success) {
            console.log("✅ Receipt email sent:", emailResult.emailId);
            showMessage("Receipt sent to your email! Redirecting...", { hidden: false });
          } else {
            console.warn("⚠️ Email sending failed:", emailResult.error);
            showMessage("Payment successful! Redirecting to receipt...", { hidden: false });
          }
        } catch (emailError) {
          console.error("❌ Error sending receipt email:", emailError);
          // Continue anyway - receipt page will still work
        }

        // Redirect to receipt page with payment details
        setTimeout(() => {
          const params = new URLSearchParams({
            txn_id: razorpayResponse.razorpay_payment_id || "",
            order_id: razorpayResponse.razorpay_order_id || orderData.id,
            amount: donation.amount,
            currency: donation.currency || "INR",
            method: "razorpay",
            email: user.email || "",
            name: user.displayName || "Donor"
          });
          window.location.href = `payment-receipt.html?${params.toString()}`;
        }, 2000);
      },
      modal: {
        ondismiss: () => {
          showMessage("Donation checkout closed. Your order was not completed.", { hidden: false });
        },
      },
      theme: {
        color: "#4361ee",
      },
    };

    // Initialize and open Razorpay checkout
    const rzp = new window.Razorpay(options);
    rzp.on("payment.failed", (response) => {
      console.warn("Razorpay failed", response);
      showMessage("Payment failed. Error: " + (response.error?.description || "Unknown error"));
    });

    showMessage("Launching Razorpay checkout...", { hidden: true });
    rzp.open();
  } catch (error) {
    console.error("❌ Razorpay donation failed:", {
      errorMessage: error.message,
      errorStack: error.stack,
      API_BASE_URL,
      endpoint: '/api/create-order'
    });
    showMessage("Unable to start Razorpay checkout: " + error.message);
  }
}

function submitPayuForm(actionUrl, params) {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = actionUrl;
  form.style.display = 'none';

  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = key;
    input.value = String(value);
    form.appendChild(input);
  });

  document.body.appendChild(form);
  form.submit();
  setTimeout(() => {
    form.remove();
  }, 1000);
}

async function initiatePayuDonation(user, donation) {
  if (!user || !donation) {
    return;
  }

  showMessage('Creating PayU request...');

  try {
    const response = await fetch(`${API_BASE_URL}/api/payments/payu/order`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${await user.getIdToken()}`,
      },
      body: JSON.stringify(donation),
    });

    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const payload = await response.json();

    if (!payload?.actionUrl || !payload?.params) {
      throw new Error('Incomplete PayU payload received.');
    }

    showMessage('Redirecting to PayU...', { hidden: true });
    submitPayuForm(payload.actionUrl, payload.params);
  } catch (error) {
    console.error('PayU donation failed:', error);
    showMessage('Unable to start PayU checkout right now. Please try again in a moment.');
  }
}

async function initiateDonation(user, donation) {
  const gateway = selectGateway();

  if (gateway === "razorpay") {
    return initiateRazorpayDonation(user, donation);
  }

  if (gateway === "payu") {
    return initiatePayuDonation(user, donation);
  }

  return initiateStripeDonation(user, donation);
}

function selectDonationType() {
  const selected = typeOptions.find((option) => option.checked);
  return selected ? selected.value : "project";
}

function highlightTypeSelection() {
  document.querySelectorAll('.donate-type-option').forEach((label) => {
    const input = label.querySelector('input[type="radio"]');
    if (input && input.checked) {
      label.classList.add('selected');
    } else {
      label.classList.remove('selected');
    }
  });
}

function handleAuthResume(event) {
  if (!event?.detail?.action) {
    return;
  }

  const { action, user } = event.detail;
  if (action?.type !== "donate") {
    return;
  }

  const donation = action?.payload;
  if (!donation) {
    showMessage("Donation details missing. Please enter the amount again.");
    return;
  }

  console.log('🔄 Resuming donation after login:', donation);
  
  // Scroll to donation section if not visible
  const donateSection = document.getElementById('donation-section') || document.getElementById('donate');
  if (donateSection) {
    donateSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  
  // Show a brief message
  showMessage("Continuing with your donation...");
  
  // Small delay to ensure UI is ready, then initiate donation
  setTimeout(() => {
    pendingDonation = null;
    initiateDonation(user, donation);
  }, 500);
}

document.addEventListener("auth-action-resume", handleAuthResume);

// Add Razorpay script if not already loaded
if (!window.Razorpay) {
  const script = document.createElement('script');
  script.src = 'https://checkout.razorpay.com/v1/checkout.js';
  script.async = true;
  script.onload = function() {
    console.log('Razorpay SDK loaded successfully');
  };
  script.onerror = function() {
    console.error('Failed to load Razorpay SDK');    
  };
  document.head.appendChild(script);
}

if (donateForm) {
  gatewayOptions.forEach((option) => {
    option.addEventListener("change", highlightGatewaySelection);
  });
  highlightGatewaySelection();

  typeOptions.forEach((option) => {
    option.addEventListener("change", highlightTypeSelection);
  });
  highlightTypeSelection();

  donateForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const amountValue = parseFloat(amountInput?.value ?? "0");
    const currencyValue = currencySelect?.value || "INR";

    if (Number.isNaN(amountValue) || amountValue <= 0) {
      showMessage("Please enter a valid donation amount (greater than zero).");
      amountInput?.focus();
      return;
    }

    const donationType = selectDonationType();

    const donation = {
      amount: amountValue,
      currency: currencyValue,
      donationType,
      motive:
        donationType === "premium"
          ? "premium-access"
          : donationType === "humanity"
          ? "humanity-support"
          : "project-development",
    };

    const user = auth.currentUser;

    if (!user) {
      pendingDonation = donation;
      // Set pending action with redirect URL to come back to donation page
      const currentPage = window.location.pathname === '/dashboard.html' || window.location.pathname.endsWith('/dashboard.html')
        ? window.location.origin + '/index.html#donate'
        : window.location.href.split('#')[0] + '#donate';
      
      setPendingAction({ 
        type: "donate", 
        payload: donation,
        redirectTo: currentPage
      });
      showMessage("Please log in or sign up to continue with your donation.");
      if (typeof window.showModal === "function") {
        window.showModal("login-modal");
      }
      return;
    }

    pendingDonation = donation;
    await initiateDonation(user, donation);
  });
}

// Auto-trigger donation form when coming from dashboard
document.addEventListener('DOMContentLoaded', () => {
  // Check if URL has #donation-section or #donate hash
  const hash = window.location.hash;
  if (hash === '#donation-section' || hash === '#donate') {
    // Scroll to donation section
    const donateSection = document.getElementById('donation-section') || document.getElementById('donate');
    if (donateSection) {
      donateSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
      
      // Check if user is logged in and auto-trigger donation
      const checkUserAndProceed = () => {
        const user = auth.currentUser;
        if (user) {
          // User is logged in, auto-trigger Razorpay payment
          setTimeout(() => {
            const donateBtn = donateForm?.querySelector('button[type="submit"]');
            if (donateBtn && amountInput?.value) {
              // Highlight the form briefly
              if (donateForm) {
                donateForm.style.boxShadow = '0 0 20px rgba(67, 97, 238, 0.4)';
                donateForm.style.transition = 'box-shadow 0.5s ease';
              }
              // Show processing message
              showMessage("Opening Razorpay payment...");
              // Auto-click the donate button to open Razorpay
              setTimeout(() => {
                donateBtn.click();
              }, 500);
            }
          }, 800);
        } else {
          // User not logged in, show login prompt
          setTimeout(() => {
            showMessage("Please log in to make a donation.");
          }, 800);
        }
      };
      
      // Wait for auth to be ready
      if (auth.currentUser) {
        checkUserAndProceed();
      } else {
        // Listen for auth state change
        const unsubscribe = auth.onAuthStateChanged((user) => {
          if (user) {
            checkUserAndProceed();
          } else {
            // Show login message if still not logged in
            setTimeout(() => {
              showMessage("Please log in to make a donation.");
            }, 1000);
          }
          unsubscribe();
        });
      }
    }
  }
});
