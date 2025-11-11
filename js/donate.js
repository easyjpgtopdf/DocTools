import { auth, setPendingAction } from "./auth.js";
import { API_BASE_URL } from "./config.js";

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

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const payload = await response.json();

    if (!payload?.id || !payload?.key) {
      throw new Error("Incomplete Razorpay order payload.");
    }

    // Create Razorpay options
    const options = {
      key: payload.key,
      order_id: payload.id,
      amount: payload.amountInPaise || payload.amount,
      currency: payload.currency || "INR",
      name: "easyjpgtopdf",
      description: `Donation - ${donation.donationType}`,
      receipt: payload.receipt,
      prefill: {
        name: user.displayName || "",
        email: user.email || "",
      },
      notes: {
        donationType: donation.donationType,
        motive: donation.motive
      },
      handler: (razorpayResponse) => {
        console.log("Razorpay success", razorpayResponse);
        showMessage("Payment successful! Generating receipt...", { hidden: true });
        // Redirect to receipt page with payment details
        setTimeout(() => {
          const params = new URLSearchParams({
            txn_id: razorpayResponse.razorpay_payment_id || "",
            order_id: razorpayResponse.razorpay_order_id || payload.id,
            amount: donation.amount,
            currency: donation.currency || "INR",
            method: "razorpay",
            email: user.email || "",
            name: user.displayName || "Donor"
          });
          window.location.href = `payment-receipt.html?${params.toString()}`;
        }, 1500);
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
    console.error("Razorpay donation failed:", error);
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
