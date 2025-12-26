/**
 * Universal Feedback Handler - Firebase Direct Integration
 * Auto-detects and handles ALL feedback/comment forms on ANY page
 * Uses Firebase Firestore directly - NO backend dependency!
 * Future-proof: Works even if PDF backend changes or is deleted
 */

(function() {
  'use strict';

  // Firebase configuration (from firebase-init.js)
  const firebaseConfig = {
    apiKey: "AIzaSyBch3tJoeFqio3IA4MbPoh2GHZE2qKVzGc",
    authDomain: "easyjpgtopdf-de346.firebaseapp.com",
    projectId: "easyjpgtopdf-de346",
    storageBucket: "easyjpgtopdf-de346.appspot.com",
    messagingSenderId: "564572183797",
    appId: "1:564572183797:web:9c204df018c150f02f79bc"
  };

  // Lazy load Firebase modules
  let firebaseApp = null;
  let firestore = null;
  let initialized = false;

  async function initializeFirebase() {
    if (initialized && firestore) return firestore;

    try {
      // Dynamically import Firebase modules
      const { initializeApp, getApp, getApps } = await import('https://www.gstatic.com/firebasejs/10.14.0/firebase-app.js');
      const { getFirestore } = await import('https://www.gstatic.com/firebasejs/10.14.0/firebase-firestore.js');
      const { collection, addDoc, serverTimestamp } = await import('https://www.gstatic.com/firebasejs/10.14.0/firebase-firestore.js');

      // Initialize Firebase app
      firebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig);
      firestore = getFirestore(firebaseApp);
      initialized = true;

      return { firestore, collection, addDoc, serverTimestamp };
    } catch (error) {
      console.error('Failed to initialize Firebase:', error);
      return null;
    }
  }

  // Get current page identifier
  function getCurrentPage() {
    return window.location.pathname.split('/').pop() || 'index.html';
  }

  // Get page display name
  function getPageName(page) {
    if (!page) page = getCurrentPage();
    return page.replace('.html', '')
               .replace(/^.*\//, '') // Remove folder paths
               .replace(/-/g, ' ')
               .replace(/\b\w/g, l => l.toUpperCase());
  }

  // Submit feedback to Firebase Firestore
  async function submitFeedbackToFirebase(feedbackData) {
    try {
      const fb = await initializeFirebase();
      if (!fb) {
        throw new Error('Firebase initialization failed');
      }

      const { firestore, collection, addDoc, serverTimestamp } = fb;

      const payload = {
        name: feedbackData.name || 'Anonymous',
        email: feedbackData.email || null,
        rating: feedbackData.rating ? parseInt(feedbackData.rating) : null,
        comment: feedbackData.comment || feedbackData.message || '',
        page: feedbackData.page || getCurrentPage(),
        pageName: feedbackData.pageName || getPageName(feedbackData.page || getCurrentPage()),
        createdAt: serverTimestamp(),
        replies: []
      };

      if (!payload.comment || !payload.comment.trim()) {
        throw new Error('Comment is required');
      }

      const feedbackRef = collection(firestore, 'feedback');
      const docRef = await addDoc(feedbackRef, payload);

      return { success: true, id: docRef.id };
    } catch (error) {
      console.error('Feedback submission error:', error);
      throw error;
    }
  }

  // Find form fields with flexible matching
  function findFormFields(form) {
    const patterns = {
      name: ['name', 'feedbackName', 'commentName', 'userName', 'authorName'],
      email: ['email', 'feedbackEmail', 'commentEmail', 'userEmail'],
      rating: ['rating', 'feedbackRating', 'starRating'],
      comment: ['comment', 'message', 'feedback', 'feedbackMessage', 'feedbackComment', 'text', 'textarea']
    };

    const fields = {};

    patterns.name.forEach(pattern => {
      if (!fields.name) {
        fields.name = form.querySelector(`[name="${pattern}"], [name*="${pattern}"], [id*="${pattern}"]`);
      }
    });

    patterns.email.forEach(pattern => {
      if (!fields.email) {
        fields.email = form.querySelector(`[name="${pattern}"], [name*="${pattern}"], [id*="${pattern}"]`);
      }
    });

    patterns.rating.forEach(pattern => {
      if (!fields.rating) {
        fields.rating = form.querySelector(`[name="${pattern}"], [name*="${pattern}"], [id*="${pattern}"]`);
      }
    });

    patterns.comment.forEach(pattern => {
      if (!fields.comment) {
        fields.comment = form.querySelector(`[name="${pattern}"], [name*="${pattern}"], [id*="${pattern}"], textarea`);
      }
    });

    return fields;
  }

  // Handle form submission
  async function handleFormSubmit(e, form) {
    e.preventDefault();
    e.stopPropagation();

    const fields = findFormFields(form);
    
    if (!fields.comment) {
      console.warn('No comment field found in form');
      return false;
    }

    const name = fields.name ? fields.name.value.trim() : '';
    const email = fields.email ? fields.email.value.trim() : '';
    const rating = fields.rating ? fields.rating.value : null;
    const comment = fields.comment.value.trim();

    if (!comment) {
      alert('Please enter your comment or feedback');
      return false;
    }

    // Find submit button and disable it
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"], button:not([type])');
    const originalBtnText = submitBtn ? (submitBtn.textContent || submitBtn.value || 'Submit') : '';
    const originalBtnDisabled = submitBtn ? submitBtn.disabled : false;
    
    if (submitBtn) {
      submitBtn.disabled = true;
      if (submitBtn.tagName === 'BUTTON') {
        submitBtn.textContent = 'Submitting...';
      } else {
        submitBtn.value = 'Submitting...';
      }
    }

    try {
      await submitFeedbackToFirebase({
        name,
        email,
        rating,
        comment,
        page: getCurrentPage()
      });

      // Success
      form.reset();
      
      // Show success message
      const successMsg = document.createElement('div');
      successMsg.style.cssText = 'padding: 12px; background: #d4edda; color: #155724; border: 1px solid #c3e6cb; border-radius: 4px; margin-top: 10px; text-align: center;';
      successMsg.textContent = '✓ Thank you for your feedback!';
      
      // Insert after form or submit button
      if (submitBtn && submitBtn.parentNode) {
        submitBtn.parentNode.insertBefore(successMsg, submitBtn.nextSibling);
        setTimeout(() => successMsg.remove(), 5000);
      } else {
        form.appendChild(successMsg);
        setTimeout(() => successMsg.remove(), 5000);
      }

      // Trigger custom event for page-specific handling
      setTimeout(() => {
        const event = new CustomEvent('feedbackSubmitted', { detail: { name, comment, rating, email } });
        document.dispatchEvent(event);
      }, 100);

    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      // Re-enable submit button
      if (submitBtn) {
        submitBtn.disabled = originalBtnDisabled;
        if (submitBtn.tagName === 'BUTTON') {
          submitBtn.textContent = originalBtnText;
        } else {
          submitBtn.value = originalBtnText;
        }
      }
    }

    return false;
  }

  // Auto-detect and initialize all feedback forms
  function initializeAllFeedbackForms() {
    // Common form IDs and class patterns
    const formSelectors = [
      '#feedbackForm',
      '#feedback-form',
      '#commentForm',
      '#comment-form',
      'form[id*="feedback"]',
      'form[id*="comment"]',
      'form[class*="feedback"]',
      'form[class*="comment"]'
    ];

    // Also check for buttons with "Submit Comment" or "Submit Feedback" text
    const submitButtons = document.querySelectorAll('button, input[type="submit"]');
    submitButtons.forEach(btn => {
      const text = (btn.textContent || btn.value || '').toLowerCase();
      if ((text.includes('submit comment') || text.includes('submit feedback') || text.includes('share feedback')) && btn.form) {
        if (!btn.form.dataset.feedbackInitialized) {
          btn.form.dataset.feedbackInitialized = 'true';
          btn.form.addEventListener('submit', (e) => handleFormSubmit(e, btn.form));
        }
      }
    });

    // Initialize forms by selector
    formSelectors.forEach(selector => {
      try {
        const forms = document.querySelectorAll(selector);
        forms.forEach(form => {
          if (form.tagName === 'FORM' && !form.dataset.feedbackInitialized) {
            form.dataset.feedbackInitialized = 'true';
            form.addEventListener('submit', (e) => handleFormSubmit(e, form));
          }
        });
      } catch (e) {
        // Invalid selector, skip
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAllFeedbackForms);
  } else {
    initializeAllFeedbackForms();
  }

  // Also initialize after a short delay (for dynamically loaded content)
  setTimeout(initializeAllFeedbackForms, 1000);

  // Export global function for manual initialization
  window.initFeedbackForms = initializeAllFeedbackForms;
  window.submitFeedbackToFirebase = submitFeedbackToFirebase;

})();

