import { app } from "./firebase-init.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
  updateProfile,
  onAuthStateChanged,
  GoogleAuthProvider,
  FacebookAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
} from "https://www.gstatic.com/firebasejs/10.14.0/firebase-auth.js";
import {
  getFirestore,
  doc,
  getDoc,
  setDoc,
} from "https://www.gstatic.com/firebasejs/10.14.0/firebase-firestore.js";

const auth = getAuth(app);
const db = getFirestore(app);

const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: 'select_account' });

const facebookProvider = new FacebookAuthProvider();
facebookProvider.setCustomParameters({ display: 'popup' });

const SOCIAL_PROVIDER_KEY = 'easyjpgtopdf.socialProvider';
const PENDING_ACTION_KEY = 'easyjpgtopdf.pendingAction';
const DASHBOARD_NAV_KEY = 'easyjpgtopdf.dashboardTarget';

const socialProviders = {
  google: googleProvider,
  facebook: facebookProvider,
};

const userMenuPointerListenerOptions = { capture: true };

function normalizeUrl(url) {
  try {
    const absolute = new URL(url, window.location.href);
    return absolute.toString();
  } catch (error) {
    console.warn('Unable to normalise URL for pending action redirect:', error);
    return url;
  }
}

function cancelUserMenuHoverClose() {
  if (userMenuHoverCloseTimeout !== null) {
    clearTimeout(userMenuHoverCloseTimeout);
    userMenuHoverCloseTimeout = null;
  }
}

function scheduleUserMenuHoverClose() {
  if (userMenuHoverCloseTimeout !== null) {
    return;
  }
  userMenuHoverCloseTimeout = window.setTimeout(() => {
    if (userMenu?.dataset.open === 'true') {
      closeUserDropdown();
    }
    userMenuHoverCloseTimeout = null;
  }, 150);
}

function handleGlobalPointerMove(event) {
  if (!userMenu || userMenu.dataset.open !== 'true') {
    return;
  }
  const target = event.target;
  if (target instanceof Node && userMenu.contains(target)) {
    cancelUserMenuHoverClose();
  } else {
    scheduleUserMenuHoverClose();
  }
}

function handleWindowBlur() {
  if (userMenu?.dataset.open === 'true') {
    closeUserDropdown();
  }
}

function getProviderFriendlyName(providerKey = '') {
  const normalized = providerKey.toLowerCase();
  const mapping = {
    google: 'Google',
    'google.com': 'Google',
    facebook: 'Facebook',
    'facebook.com': 'Facebook',
  };
  return mapping[normalized] || providerKey || 'Social Provider';
}

async function ensureUserProfile(user, defaults = {}) {
  if (!user) return;
  try {
    const userDocRef = doc(db, 'users', user.uid);
    const snapshot = await getDoc(userDocRef);
    if (snapshot.exists()) {
      if (Object.keys(defaults).length) {
        await setDoc(
          userDocRef,
          {
            displayName: user.displayName || defaults.displayName || '',
            email: user.email || defaults.email || '',
            lastLogin: new Date().toISOString(),
          },
          { merge: true }
        );
      }
      return;
    }

    await setDoc(userDocRef, {
      displayName: user.displayName || defaults.displayName || '',
      email: user.email || defaults.email || '',
      dob: defaults.dob || '',
      ageVerified: Boolean(defaults.ageVerified),
      createdAt: new Date().toISOString(),
      lastLogin: new Date().toISOString(),
      plan: 'free',
      totalConversions: 0,
    });
  } catch (error) {
    console.error('Failed to ensure user profile:', error);
  }
}

function getAuthErrorMessage(error, fallbackMessage) {
  const code = error?.code;
  switch (code) {
    case 'auth/invalid-email':
      return 'Please enter a valid email address.';
    case 'auth/email-already-in-use':
      return 'That email is already registered. Try signing in instead.';
    case 'auth/weak-password':
      return 'Password should be at least 6 characters long.';
    case 'auth/popup-closed-by-user':
      return 'Sign-in was cancelled before completion.';
    case 'auth/user-disabled':
      return 'This account has been disabled. Contact support for help.';
    case 'auth/user-not-found':
      return 'No account found with that email address.';
    case 'auth/wrong-password':
      return 'Incorrect password. Please try again.';
    default:
      return error?.message || fallbackMessage;
  }
}

function shouldUseRedirect() {
  const isSmallViewport = window.matchMedia('(max-width: 768px)').matches;
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  return isSmallViewport || isStandalone || isIOS;
}

async function restoreRedirectResult() {
  try {
    const result = await getRedirectResult(auth);
    if (result && result.user) {
      const providerId = result.providerId || result._tokenResponse?.providerId;
      const providerKey = sessionStorage.getItem(SOCIAL_PROVIDER_KEY) || providerId || '';
      sessionStorage.removeItem(SOCIAL_PROVIDER_KEY);
      const friendlyName = getProviderFriendlyName(providerKey);
      showAlert(`Signed in with ${friendlyName} successfully!`);
      await ensureUserProfile(result.user, { email: result.user.email || '' });
      dispatchPendingAction(result.user);
    }
  } catch (error) {
    sessionStorage.removeItem(SOCIAL_PROVIDER_KEY);
    console.error('Social login redirect failed:', error);
    showAlert(error.message || 'Unable to complete social sign-in.');
  }
}

async function signInWithProvider(providerKey) {
  const provider = socialProviders[providerKey];
  if (!provider) {
    console.warn('Unknown social provider:', providerKey);
    return;
  }

  try {
    if (shouldUseRedirect()) {
      sessionStorage.setItem(SOCIAL_PROVIDER_KEY, providerKey);
      await signInWithRedirect(auth, provider);
      return;
    }

    const result = await signInWithPopup(auth, provider);
    if (result?.user) {
      const friendlyName = getProviderFriendlyName(providerKey);
      showAlert(`Signed in with ${friendlyName} successfully!`);
      await ensureUserProfile(result.user, {
        email: result.user.email || '',
        displayName: result.user.displayName || '',
        ageVerified: true,
      });
      dispatchPendingAction(result.user);
      window.location.href = 'dashboard.html#dashboard-overview';
    }
  } catch (error) {
    console.error(`Social login with ${providerKey} failed:`, error);
    showAlert(getAuthErrorMessage(error, `Unable to sign in with ${getProviderFriendlyName(providerKey)}.`));
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

function setDashboardNavTarget(targetId) {
  try {
    if (targetId) {
      sessionStorage.setItem(DASHBOARD_NAV_KEY, targetId);
    } else {
      sessionStorage.removeItem(DASHBOARD_NAV_KEY);
    }
  } catch (error) {
    console.warn('Failed to persist dashboard navigation target:', error);
  }
}

function consumeDashboardNavTarget() {
  try {
    const target = sessionStorage.getItem(DASHBOARD_NAV_KEY);
    if (target) {
      sessionStorage.removeItem(DASHBOARD_NAV_KEY);
    }
    return target || '';
  } catch (error) {
    console.warn('Failed to read dashboard navigation target:', error);
    return '';
  }
}

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

function hasPendingAction() {
  return Boolean(getCurrentPendingAction());
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

let loginForms = [];
let signupForms = [];
let forgotPasswordForms = [];
let authButtons = null;
let loginButtons = [];
let signupButtons = [];
let socialButtons = [];
let userMenu = null;
let userMenuToggle = null;
let userDropdown = null;
let dropdownNavLinks = [];
let dashboardNavButtons = [];
let dashboardGuest = null;
let userMenuHoverCloseTimeout = null;
let userMenuPointerHandlersBound = false;
let billingForm = null;
let billingMessage = null;
let billingSaveButton = null;
let billingSummaryEl = null;
let billingNameInput = null;
let billingPhoneInput = null;
let billingLine1Input = null;
let billingLine2Input = null;
let billingCityInput = null;
let billingStateInput = null;
let billingPostalInput = null;
let billingCountryInput = null;
let billingNotesInput = null;
const defaultBillingSummary = 'Not added yet.';

let logoutButton = null;
let authUiInitialized = false;
let documentClickHandlerBound = false;

function initializeAuthUI() {
  if (authUiInitialized) {
    updateUI(auth.currentUser || null);
    return;
  }

  loginForms = Array.from(document.querySelectorAll('form[data-auth-form="login"]'));
  signupForms = Array.from(document.querySelectorAll('form[data-auth-form="signup"]'));
  forgotPasswordForms = Array.from(document.querySelectorAll('form[data-auth-form="reset"]'));
  authButtons = document.querySelector('.auth-buttons');
  loginButtons = [];
  signupButtons = [];
  socialButtons = Array.from(document.querySelectorAll('[data-provider]'));
  userMenu = document.getElementById('user-menu');
  userMenuToggle = document.getElementById('user-menu-toggle');
  userDropdown = document.getElementById('user-dropdown');
  dropdownNavLinks = Array.from(document.querySelectorAll('[data-user-nav]'));
  dashboardNavButtons = Array.from(document.querySelectorAll('.dashboard-nav-btn[data-dashboard-target]'));
  dashboardGuest = document.getElementById('dashboard-guest');
  billingForm = document.getElementById('billing-form');
  billingMessage = document.getElementById('billing-message');
  billingSaveButton = document.getElementById('billing-save-button');
  billingSummaryEl = document.querySelector('.user-billing-address');
  billingNameInput = document.getElementById('billing-name');
  billingPhoneInput = document.getElementById('billing-phone');
  billingLine1Input = document.getElementById('billing-line1');
  billingLine2Input = document.getElementById('billing-line2');
  billingCityInput = document.getElementById('billing-city');
  billingStateInput = document.getElementById('billing-state');
  billingPostalInput = document.getElementById('billing-postal');
  billingCountryInput = document.getElementById('billing-country');
  billingNotesInput = document.getElementById('billing-notes');
  logoutButton = document.getElementById('logout-button');

  signupForms.forEach((form) => form.addEventListener('submit', handleSignup));
  loginForms.forEach((form) => form.addEventListener('submit', handleLogin));
  forgotPasswordForms.forEach((form) => form.addEventListener('submit', handlePasswordReset));
  if (billingForm) {
    billingForm.addEventListener('submit', handleBillingFormSubmit);
  }

  socialButtons.forEach((button) => {
    button.addEventListener('click', (event) => {
      event.preventDefault();
      const providerKey = button.dataset.provider;
      if (!providerKey) return;
      signInWithProvider(providerKey.toLowerCase());
    });
  });

  dropdownNavLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      const rawHref = link.getAttribute('href') || '';
      const targetId = link.dataset.userNav || rawHref.replace('#', '');

      if (!targetId) {
        closeUserDropdown();
        return;
      }

      const hrefUrl = rawHref ? new URL(rawHref, window.location.href) : null;
      const isSamePageHash = hrefUrl && normalizeUrl(hrefUrl.href) === normalizeUrl(window.location.href);

      if (hrefUrl && !isSamePageHash && hrefUrl.origin === window.location.origin && !rawHref.startsWith('#')) {
        setDashboardNavTarget(targetId);
        closeUserDropdown();
        window.location.href = hrefUrl.href;
        return;
      }

      event.preventDefault();
      closeUserDropdown();
      revealDashboardSection(targetId);
    });
  });

  dashboardNavButtons.forEach((button) => {
    const targetId = button.dataset.dashboardTarget;
    if (!targetId) return;
    button.addEventListener('click', () => {
      revealDashboardSection(targetId, { trigger: 'sidebar' });
    });
  });

  if (userMenuToggle) {
    userMenuToggle.addEventListener('click', (event) => {
      event.preventDefault();
      toggleUserDropdown();
    });
  }

  if (userMenu) {
    const hoverTargets = [userMenu, userMenuToggle, userDropdown];
    hoverTargets.forEach((element) => {
      if (!element) return;
      element.addEventListener('mouseenter', cancelUserMenuHoverClose);
      element.addEventListener('pointerenter', cancelUserMenuHoverClose);
      element.addEventListener('mouseleave', scheduleUserMenuHoverClose);
      element.addEventListener('pointerleave', scheduleUserMenuHoverClose);
    });
  }

  if (!documentClickHandlerBound) {
    document.addEventListener('click', (event) => {
      if (!userMenu || userMenu.dataset.open !== 'true') return;
      if (userMenu.contains(event.target)) return;
      closeUserDropdown();
    });

    document.addEventListener('focusin', (event) => {
      if (!userMenu || userMenu.dataset.open !== 'true') return;
      if (userMenu.contains(event.target)) return;
      closeUserDropdown();
    });

    document.addEventListener('keyup', (event) => {
      if (event.key !== 'Escape') return;
      if (!userMenu || userMenu.dataset.open !== 'true') return;
      closeUserDropdown();
    });
    documentClickHandlerBound = true;
  }

  if (logoutButton) {
    logoutButton.addEventListener('click', handleLogout);
  }

  authUiInitialized = true;
  updateUI(auth.currentUser || null);
}

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

function isValidEmail(value) {
  if (typeof value !== 'string') {
    return false;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return false;
  }
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailPattern.test(trimmed);
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

  const hadPendingAction = hasPendingAction();
  const formData = new FormData(form);
  const name = (formData.get('signup-name') ?? '').toString().trim();
  const email = (formData.get('signup-email') ?? '').toString().trim();
  const password = (formData.get('signup-password') ?? '').toString();
  const confirmPassword = (formData.get('signup-confirm-password') ?? '').toString();
  const dob = (formData.get('signup-dob') ?? '').toString();
  const ageCheckbox = form.querySelector('input[name="confirm-age"]');
  const termsCheckbox = form.querySelector('input[name="agree-terms"]');

  if (!isValidEmail(email)) {
    showAlert('Please enter a valid email address.');
    const emailInput = form.querySelector('input[name="signup-email"]');
    if (emailInput instanceof HTMLElement) {
      emailInput.focus({ preventScroll: false });
    }
    return;
  }

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
    if (!hadPendingAction) {
      window.location.href = 'dashboard.html#dashboard-overview';
    }
  } catch (error) {
    console.error('Signup failed:', error);
    showAlert(getAuthErrorMessage(error, 'Unable to create account.'));
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  if (!(form instanceof HTMLFormElement)) {
    return;
  }

  const hadPendingAction = hasPendingAction();
  const formData = new FormData(form);
  const email = (formData.get('login-email') ?? '').toString().trim();
  const password = (formData.get('login-password') ?? '').toString();

  if (!isValidEmail(email)) {
    showAlert('Please enter a valid email address.');
    const emailInput = form.querySelector('input[name="login-email"]');
    if (emailInput instanceof HTMLElement) {
      emailInput.focus({ preventScroll: false });
    }
    return;
  }

  try {
    await signInWithEmailAndPassword(auth, email, password);
    showAlert('Logged in successfully!');
    form.reset();
    resetPeerForms('login', form);
    if (typeof window.closeModal === 'function') {
      window.closeModal('login-modal');
    }
    dispatchPendingAction(auth.currentUser);
    if (!hadPendingAction) {
      window.location.href = 'dashboard.html#dashboard-overview';
    }
  } catch (error) {
    console.error('Login failed:', error);
    showAlert(getAuthErrorMessage(error, 'Unable to log in.'));
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
    showAlert(getAuthErrorMessage(error, 'Unable to send password reset email.'));
  }
}

async function handleLogout() {
  try {
    await signOut(auth);
    showAlert('You have been signed out.');
    clearPendingAction();
  } catch (error) {
    console.error('Logout failed:', error);
    showAlert(getAuthErrorMessage(error, 'Unable to sign out. Please try again.'));
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
    if (dashboardGuest) {
      dashboardGuest.style.display = 'none';
    }
    updateSidebarAvatar(user);
    updateUserMenuBadge(user);
  } else {
    if (authButtons) authButtons.style.display = 'flex';
    if (userMenu) userMenu.style.display = 'none';
    if (dashboard) {
      dashboard.style.display = 'none';
    }
    if (dashboardGuest) {
      dashboardGuest.style.display = 'flex';
    }
    closeUserDropdown();
  }
}

onAuthStateChanged(auth, (user) => {
  updateUI(user);
  if (user) {
    loadBillingAddress(user);
    dispatchPendingAction(user);
    const pendingDashboardTarget = consumeDashboardNavTarget();
    if (pendingDashboardTarget) {
      revealDashboardSection(pendingDashboardTarget, { skipStore: true });
    }
  } else {
    resetBillingUI();
  }
});

function updateUserMenuBadge(user) {
  if (!userMenuToggle) return;
  const initialEl = userMenuToggle.querySelector('.user-initial');
  if (initialEl) {
    const name = user.displayName || user.email || '';
    initialEl.textContent = name.trim().charAt(0).toUpperCase() || 'U';
  }
}

function updateSidebarAvatar(user) {
  const sidebarInitial = document.querySelector('.sidebar-user-initial');
  const sidebarName = document.querySelector('.dashboard-sidebar .user-name');
  const sidebarEmail = document.querySelector('.dashboard-sidebar .user-email');
  const nameSource = user.displayName || user.email || '';
  const initial = nameSource.trim().charAt(0).toUpperCase() || 'U';
  if (sidebarInitial) {
    sidebarInitial.textContent = initial;
  }
  if (sidebarName) {
    sidebarName.textContent = user.displayName || user.email || '—';
  }
  if (sidebarEmail) {
    sidebarEmail.textContent = user.email || ''; // email already shown in menu
  }
}

function toggleUserDropdown(forceState) {
  if (!userMenu || !userDropdown || !userMenuToggle) return;
  const isOpen = typeof forceState === 'boolean' ? forceState : userMenu.dataset.open !== 'true';
  userMenu.dataset.open = isOpen ? 'true' : 'false';
  userMenuToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  userDropdown.hidden = !isOpen;
  if (isOpen) {
    cancelUserMenuHoverClose();
    if (!userMenuPointerHandlersBound) {
      window.addEventListener('pointermove', handleGlobalPointerMove, userMenuPointerListenerOptions);
      window.addEventListener('blur', handleWindowBlur, userMenuPointerListenerOptions);
      userMenuPointerHandlersBound = true;
    }
  } else if (userMenuPointerHandlersBound) {
    window.removeEventListener('pointermove', handleGlobalPointerMove, userMenuPointerListenerOptions);
    window.removeEventListener('blur', handleWindowBlur, userMenuPointerListenerOptions);
    userMenuPointerHandlersBound = false;
    cancelUserMenuHoverClose();
  }
}

function closeUserDropdown() {
  cancelUserMenuHoverClose();
  toggleUserDropdown(false);
  if (userMenuPointerHandlersBound) {
    window.removeEventListener('pointermove', handleGlobalPointerMove, userMenuPointerListenerOptions);
    window.removeEventListener('blur', handleWindowBlur, userMenuPointerListenerOptions);
    userMenuPointerHandlersBound = false;
  }
}

function revealDashboardSection(targetId, options = {}) {
  const { skipStore = false, trigger = '' } = options;

  const targetFragment = (targetId || 'dashboard-overview').trim();
  const dashboardSection = document.getElementById('user-dashboard');

  if (!dashboardSection) {
    if (!skipStore) {
      setDashboardNavTarget(targetFragment);
    }
    const destination = new URL(`dashboard.html#${targetFragment}`, window.location.href);
    if (normalizeUrl(window.location.href) !== normalizeUrl(destination.toString())) {
      window.location.href = destination.toString();
    } else {
      window.location.hash = `#${targetFragment}`;
    }
    return;
  }

  if (typeof window.showPage === 'function') {
    window.showPage('home');
  }

  const panels = Array.from(dashboardSection.querySelectorAll('.dashboard-panel'));
  const navButtons = dashboardNavButtons;
  let targetPanel = null;

  panels.forEach((panel) => {
    const isMatch = panel.id === targetFragment;
    panel.classList.toggle('active', isMatch);
    if (isMatch) {
      targetPanel = panel;
    }
  });

  navButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.dashboardTarget === targetFragment);
  });

  requestAnimationFrame(() => {
    dashboardSection.classList.add('active');
    if (targetPanel) {
      targetPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      dashboardSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
}

function bootstrapAuthUI() {
  document.removeEventListener('DOMContentLoaded', bootstrapAuthUI);
  initializeAuthUI();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootstrapAuthUI);
} else {
  initializeAuthUI();
}

restoreRedirectResult();

export { auth };
