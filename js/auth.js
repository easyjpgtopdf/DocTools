import { app } from "./firebase-init.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
  updateProfile,
  onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/10.14.0/firebase-auth.js";
import {
  getFirestore,
  doc,
  getDoc,
  setDoc,
} from "https://www.gstatic.com/firebasejs/10.14.0/firebase-firestore.js";

const auth = getAuth(app);
const db = getFirestore(app);

const PENDING_ACTION_KEY = 'easyjpgtopdf.pendingAction';

function normalizeUrl(url) {
  try {
    const absolute = new URL(url, window.location.href);
    return absolute.toString();
  } catch (error) {
    console.warn('Unable to normalise URL for pending action redirect:', error);
    return url;
  }
}

function loadPendingAction() {
  try {
    const raw = sessionStorage.getItem(PENDING_ACTION_KEY);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw);
  } catch (error) {
    console.warn('Failed to parse stored pending action:', error);
    return null;
  }
}

function savePendingAction(action) {
  if (!action) {
    sessionStorage.removeItem(PENDING_ACTION_KEY);
    return;
  }
  try {
    sessionStorage.setItem(PENDING_ACTION_KEY, JSON.stringify(action));
  } catch (error) {
    console.warn('Failed to persist pending action:', error);
  }
}

function clearPendingActionStorage() {
  try {
    sessionStorage.removeItem(PENDING_ACTION_KEY);
  } catch (error) {
    console.warn('Failed to clear pending action from storage:', error);
  }
}

let pendingAction = loadPendingAction();

export function setPendingAction(action) {
  if (!action || typeof action !== 'object') {
    pendingAction = null;
    clearPendingActionStorage();
    return;
  }
  const enriched = {
    ...action,
    dispatched: false,
  };
  pendingAction = enriched;
  savePendingAction(enriched);
}

export function clearPendingAction() {
  pendingAction = null;
  clearPendingActionStorage();
}

function getCurrentPendingAction() {
  pendingAction = pendingAction || loadPendingAction();
  return pendingAction;
}

function dispatchPendingAction(user) {
  const action = getCurrentPendingAction();
  if (!action) {
    return;
  }

  const redirectTo = action.redirectTo;
  if (redirectTo) {
    const target = normalizeUrl(redirectTo);
    const current = normalizeUrl(window.location.href);
    if (target !== current) {
      savePendingAction({ ...action, dispatched: false });
      window.location.href = target;
      return;
    }
  }

  if (action.dispatched) {
    return;
  }

  document.dispatchEvent(
    new CustomEvent('auth-action-resume', {
      detail: { action, user },
    })
  );

  const updated = { ...action, dispatched: true };
  pendingAction = updated;
  savePendingAction(updated);
}

const loginForms = Array.from(document.querySelectorAll('form[data-auth-form="login"]'));
const signupForms = Array.from(document.querySelectorAll('form[data-auth-form="signup"]'));
const forgotPasswordForms = Array.from(document.querySelectorAll('form[data-auth-form="reset"]'));
const authButtons = document.querySelector('.auth-buttons');
const userMenu = document.querySelector('#user-menu');
const billingForm = document.getElementById('billing-form');
const billingMessage = document.getElementById('billing-message');
const billingSaveButton = document.getElementById('billing-save-button');
const billingSummaryEl = document.querySelector('.user-billing-address');
const billingNameInput = document.getElementById('billing-name');
const billingPhoneInput = document.getElementById('billing-phone');
const billingLine1Input = document.getElementById('billing-line1');
const billingLine2Input = document.getElementById('billing-line2');
const billingCityInput = document.getElementById('billing-city');
const billingStateInput = document.getElementById('billing-state');
const billingPostalInput = document.getElementById('billing-postal');
const billingCountryInput = document.getElementById('billing-country');
const billingNotesInput = document.getElementById('billing-notes');
const defaultBillingSummary = 'Not added yet.';

function showAlert(message) {
  alert(message);
}

function clearBillingMessage() {
  if (!billingMessage) return;
  billingMessage.hidden = true;
  billingMessage.textContent = '';
  billingMessage.classList.remove('success', 'error');
}

function showBillingMessage(message, type = 'success') {
  if (!billingMessage) return;
  billingMessage.hidden = false;
  billingMessage.textContent = message;
  billingMessage.classList.remove('success', 'error');
  billingMessage.classList.add(type === 'error' ? 'error' : 'success');
}

function setInputValue(input, value) {
  if (!input) return;
  if (value !== undefined) {
    input.value = value;
  } else {
    input.value = input.defaultValue || '';
  }
}

function formatBillingSummary(address = {}) {
  const safeValue = (val) => (typeof val === 'string' ? val.trim() : '');
  const lines = [];
  const name = safeValue(address.name);
  const addressLines = [safeValue(address.line1), safeValue(address.line2)]
    .filter(Boolean)
    .join(', ');
  const locality = [safeValue(address.city), safeValue(address.state), safeValue(address.postal)]
    .filter(Boolean)
    .join(', ');
  const country = safeValue(address.country);

  if (name) lines.push(name);
  if (addressLines) lines.push(addressLines);
  if (locality) lines.push(locality);
  if (country) lines.push(country);

  return lines.length ? lines.join(' • ') : defaultBillingSummary;
}

function populateBillingForm(address = {}) {
  setInputValue(billingNameInput, address.name);
  setInputValue(billingPhoneInput, address.phone);
  setInputValue(billingLine1Input, address.line1);
  setInputValue(billingLine2Input, address.line2);
  setInputValue(billingCityInput, address.city);
  setInputValue(billingStateInput, address.state);
  setInputValue(billingPostalInput, address.postal);
  if (billingCountryInput) {
    if (address.country !== undefined) {
      billingCountryInput.value = address.country;
    } else {
      billingCountryInput.value = billingCountryInput.defaultValue || '';
    }
  }
  setInputValue(billingNotesInput, address.notes);
  if (billingSummaryEl) {
    billingSummaryEl.textContent = formatBillingSummary(address);
  }
}

function resetBillingUI() {
  if (billingForm) billingForm.reset();
  if (billingSummaryEl) billingSummaryEl.textContent = defaultBillingSummary;
  clearBillingMessage();
  if (billingSaveButton) billingSaveButton.disabled = false;
}

function collectBillingFormData() {
  if (!billingForm) return null;
  const trim = (val) => (typeof val === 'string' ? val.trim() : '');
  return {
    name: trim(billingNameInput?.value || ''),
    phone: trim(billingPhoneInput?.value || ''),
    line1: trim(billingLine1Input?.value || ''),
    line2: trim(billingLine2Input?.value || ''),
    city: trim(billingCityInput?.value || ''),
    state: trim(billingStateInput?.value || ''),
    postal: trim(billingPostalInput?.value || ''),
    country: trim(billingCountryInput?.value || ''),
    notes: trim(billingNotesInput?.value || ''),
  };
}

async function loadBillingAddress(user) {
  if (!billingForm || !user) return;
  clearBillingMessage();
  try {
    const userDocRef = doc(db, 'users', user.uid);
    const userDoc = await getDoc(userDocRef);
    if (userDoc.exists()) {
      const data = userDoc.data();
      const address = data?.billingAddress || {};
      populateBillingForm(address);
    } else {
      populateBillingForm({});
    }
  } catch (error) {
    console.error('Failed to load billing address:', error);
    populateBillingForm({});
    showBillingMessage('Unable to load billing address. Please try again later.', 'error');
  }
}

async function handleBillingFormSubmit(event) {
  event.preventDefault();
  if (!auth.currentUser) {
    showBillingMessage('Please sign in to save your billing address.', 'error');
    return;
  }

  const addressData = collectBillingFormData();
  if (!addressData) return;

  clearBillingMessage();
  if (billingSaveButton) billingSaveButton.disabled = true;

  const userDocRef = doc(db, 'users', auth.currentUser.uid);
  const payload = {
    billingAddress: {
      ...addressData,
      updatedAt: new Date().toISOString(),
    },
  };

  try {
    await setDoc(userDocRef, payload, { merge: true });
    populateBillingForm(payload.billingAddress);
    showBillingMessage('Billing address saved successfully.');
  } catch (error) {
    console.error('Failed to save billing address:', error);
    showBillingMessage('Unable to save billing address. Please try again.', 'error');
  } finally {
    if (billingSaveButton) billingSaveButton.disabled = false;
  }
}

function calculateAge(dobValue) {
  const dob = new Date(dobValue);
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const monthDiff = today.getMonth() - dob.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
    age--;
  }
  return age;
}

function resetPeerForms(group, sourceForm) {
  const collections = {
    signup: signupForms,
    login: loginForms,
    reset: forgotPasswordForms,
  };

  (collections[group] || []).forEach((form) => {
    if (form !== sourceForm) {
      form.reset();
    }
  });
}

async function handleSignup(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!(form instanceof HTMLFormElement)) {
    return;
  }

  const formData = new FormData(form);
  const name = (formData.get('signup-name') ?? '').toString().trim();
  const email = (formData.get('signup-email') ?? '').toString().trim();
  const password = (formData.get('signup-password') ?? '').toString();
  const confirmPassword = (formData.get('signup-confirm-password') ?? '').toString();
  const dob = (formData.get('signup-dob') ?? '').toString();
  const ageCheckbox = form.querySelector('input[name="confirm-age"]');
  const termsCheckbox = form.querySelector('input[name="agree-terms"]');

  if (password !== confirmPassword) {
    showAlert('Passwords do not match.');
    return;
  }

  if (!(ageCheckbox instanceof HTMLInputElement) || !ageCheckbox.checked) {
    showAlert('You must confirm that you are at least 13 years old.');
    return;
  }

  if (!(termsCheckbox instanceof HTMLInputElement) || !termsCheckbox.checked) {
    showAlert('Please agree to the Terms and Privacy Policy.');
    return;
  }

  const age = calculateAge(dob);
  if (Number.isNaN(age) || age < 13) {
    showAlert('You must be at least 13 years old to create an account.');
    return;
  }

  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    if (name) {
      await updateProfile(userCredential.user, { displayName: name });
    }

    await setDoc(doc(db, 'users', userCredential.user.uid), {
      displayName: name,
      email,
      dob,
      ageVerified: true,
      createdAt: new Date().toISOString(),
      plan: 'free',
      totalConversions: 0,
      lastLogin: new Date().toISOString(),
    });

    showAlert('Account created successfully!');
    form.reset();
    resetPeerForms('signup', form);
    if (typeof window.closeModal === 'function') {
      window.closeModal('signup-modal');
    }
    dispatchPendingAction(userCredential.user);
  } catch (error) {
    console.error('Signup failed:', error);
    showAlert(error.message || 'Unable to create account.');
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!(form instanceof HTMLFormElement)) {
    return;
  }

  const formData = new FormData(form);
  const email = (formData.get('login-email') ?? '').toString().trim();
  const password = (formData.get('login-password') ?? '').toString();

  try {
    await signInWithEmailAndPassword(auth, email, password);
    showAlert('Logged in successfully!');
    form.reset();
    resetPeerForms('login', form);
    if (typeof window.closeModal === 'function') {
      window.closeModal('login-modal');
    }
    dispatchPendingAction(auth.currentUser);
  } catch (error) {
    console.error('Login failed:', error);
    showAlert(error.message || 'Unable to log in.');
  }
}

async function handlePasswordReset(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!(form instanceof HTMLFormElement)) {
    return;
  }

  const formData = new FormData(form);
  const email = (formData.get('reset-email') ?? '').toString().trim();

  if (!email) {
    showAlert('Please enter your email address.');
    return;
  }

  try {
    await sendPasswordResetEmail(auth, email);
    showAlert('Password reset email sent. Check your inbox.');
    form.reset();
    resetPeerForms('reset', form);
    if (typeof window.closeModal === 'function') {
      window.closeModal('forgot-password-modal');
    }
  } catch (error) {
    console.error('Password reset failed:', error);
    showAlert(error.message || 'Unable to send password reset email.');
  }
}

async function handleLogout() {
  try {
    await signOut(auth);
    showAlert('You have been signed out.');
    clearPendingAction();
  } catch (error) {
    console.error('Logout failed:', error);
    showAlert('Unable to sign out. Please try again.');
  }
}

function updateUI(user) {
  const dashboard = document.getElementById('user-dashboard');
  if (user) {
    if (authButtons) authButtons.style.display = 'none';
    if (userMenu) userMenu.style.display = 'flex';
    if (dashboard) {
      dashboard.style.display = 'block';
      const nameEl = dashboard.querySelector('.user-name');
      const emailEl = dashboard.querySelector('.user-email');
      if (nameEl) nameEl.textContent = user.displayName || user.email;
      if (emailEl) emailEl.textContent = user.email;
    }
  } else {
    if (authButtons) authButtons.style.display = 'flex';
    if (userMenu) userMenu.style.display = 'none';
    if (dashboard) {
      dashboard.style.display = 'none';
    }
  }
}

onAuthStateChanged(auth, (user) => {
  updateUI(user);
  if (user) {
    loadBillingAddress(user);
    dispatchPendingAction(user);
  } else {
    resetBillingUI();
  }
});

signupForms.forEach((form) => form.addEventListener('submit', handleSignup));
loginForms.forEach((form) => form.addEventListener('submit', handleLogin));
forgotPasswordForms.forEach((form) => form.addEventListener('submit', handlePasswordReset));
if (billingForm) billingForm.addEventListener('submit', handleBillingFormSubmit);

const logoutButton = document.getElementById('logout-button');
if (logoutButton) {
  logoutButton.addEventListener('click', handleLogout);
}

export { auth };
