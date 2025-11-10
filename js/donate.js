import { auth, setPendingAction } from "./auth.js";

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
    const response = await fetch("/api/payments/create-donation-session", {
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
    // In a real implementation, you would call your backend to create an order
    // For now, we'll simulate a successful order creation
    const orderId = 'order_' + Math.random().toString(36).substr(2, 9);
    
    // Create Razorpay options
    const options = {
      key: 'YOUR_RAZORPAY_KEY', // Replace with your Razorpay key
      amount: donation.amount * 100, // Razorpay expects amount in paise
      currency: donation.currency || 'INR', 
      name: 'easyjpgtopdf',
      description: 'Donation for easyjpgtopdf',
      order_id: orderId,
      handler: function(response) {
        // This function runs after successful payment
        const txnId = response.razorpay_payment_id || 'TXN' + Date.now();
        // Redirect to receipt page with transaction details
        window.location.href = `payment-receipt.html?txn_id=${txnId}&amount=${donation.amount}&method=razorpay`;
      },
      prefill: {
        name: donation.name || '',
        email: user.email || '',
        contact: '' // Add phone if available
      },
      theme: {
        color: '#4361ee'
      }
    };
    
    // Initialize Razorpay checkout
    const rzp = new Razorpay(options);
    rzp.open();
    
    // Close any existing payment windows
    rzp.on('payment.failed', function(response) {
      showMessage('Payment failed. Please try again.');
      console.error('Payment failed:', response.error);
    });

    const payload = await response.json();

    if (!payload?.orderId || !payload?.razorpayKeyId) {
      throw new Error("Incomplete Razorpay order payload.");
    }

    const options = {
      key: payload.razorpayKeyId,
      order_id: payload.orderId,
      amount: payload.amountInPaise,
      currency: payload.currency,
      name: "easyjpgtopdf",
      description: "Support easyjpgtopdf",
      prefill: payload.prefill || {},
      notes: payload.notes || {},
      handler: (razorpayResponse) => {
        console.log("Razorpay success", razorpayResponse);
        showMessage("Payment processing... Razorpay will confirm shortly.");
      },
      modal: {
        ondismiss: () => {
          showMessage("Donation checkout closed.", { hidden: false });
        },
      },
      theme: {
        color: "#4361ee",
      },
    };

    const rzp = new window.Razorpay(options);
    rzp.on("payment.failed", (response) => {
      console.warn("Razorpay failed", response);
      showMessage("Payment failed or was cancelled. Please try again.");
    });

    showMessage("Launching Razorpay checkout...", { hidden: true });
    rzp.open();
  } catch (error) {
    console.error("Razorpay donation failed:", error);
    showMessage("Unable to start Razorpay checkout right now. Please try again in a moment.");
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
    const response = await fetch('/api/payments/payu/order', {
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

  pendingDonation = null;
  initiateDonation(user, donation);
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
      setPendingAction({ type: "donate", payload: donation });
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
