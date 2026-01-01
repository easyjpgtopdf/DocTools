/**
 * Shared Feedback Submission Utility
 * Handles comment/feedback submission to MongoDB backend for all pages
 */

// Get API URL dynamically
function getFeedbackApiUrl() {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.')) {
    return 'http://localhost:3000/api/feedback';
  }
  return 'https://pdf-to-word-converter-564572183797.us-central1.run.app/api/feedback';
}

const FEEDBACK_API_URL = getFeedbackApiUrl();

/**
 * Submit feedback to MongoDB backend
 * @param {Object} feedbackData - Feedback data object
 * @param {string} feedbackData.name - User name
 * @param {string} feedbackData.email - User email (optional)
 * @param {number} feedbackData.rating - Rating 1-5 (optional)
 * @param {string} feedbackData.comment - Comment text (required)
 * @param {string} feedbackData.page - Page identifier (e.g., 'pdf-to-excel-convert.html')
 * @param {string} feedbackData.pageName - Display name for page (optional)
 * @returns {Promise<Object>} Response from server
 */
async function submitFeedback(feedbackData) {
  try {
    const pageName = feedbackData.pageName || 
                     (feedbackData.page ? feedbackData.page.replace('.html', '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : '');
    
    const payload = {
      name: feedbackData.name || 'Anonymous',
      email: feedbackData.email || null,
      rating: feedbackData.rating ? parseInt(feedbackData.rating) : null,
      comment: feedbackData.comment || feedbackData.message || '',
      page: feedbackData.page || getCurrentPage(),
      pageName: pageName
    };

    // Validate required fields
    if (!payload.comment || !payload.comment.trim()) {
      throw new Error('Comment is required');
    }

    if (!payload.page) {
      payload.page = getCurrentPage();
    }

    const response = await fetch(FEEDBACK_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Server error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Feedback submission error:', error);
    throw error;
  }
}

/**
 * Get current page identifier
 * @returns {string} Current page filename
 */
function getCurrentPage() {
  return window.location.pathname.split('/').pop() || 'index.html';
}

/**
 * Initialize feedback form handler
 * @param {string} formId - Form element ID
 * @param {Object} options - Options for form handling
 * @param {Function} options.onSuccess - Callback on successful submission
 * @param {Function} options.onError - Callback on error
 */
function initFeedbackForm(formId, options = {}) {
  const form = document.getElementById(formId);
  if (!form) {
    console.warn(`Feedback form with ID "${formId}" not found`);
    return;
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Get form fields (flexible field names)
    const nameField = form.querySelector('[name="name"], [id*="name"], [id*="Name"]');
    const emailField = form.querySelector('[name="email"], [id*="email"], [id*="Email"]');
    const ratingField = form.querySelector('[name="rating"], [id*="rating"], [id*="Rating"]');
    const commentField = form.querySelector('[name="comment"], [name="message"], [id*="comment"], [id*="Comment"], [id*="message"], [id*="Message"]');
    
    const name = nameField ? nameField.value.trim() : '';
    const email = emailField ? emailField.value.trim() : '';
    const rating = ratingField ? ratingField.value : null;
    const comment = commentField ? commentField.value.trim() : '';

    // Validation
    if (!comment) {
      alert('Please enter your comment');
      return;
    }

    // Disable submit button
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.textContent : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';
    }

    try {
      const result = await submitFeedback({
        name,
        email,
        rating,
        comment,
        page: getCurrentPage()
      });

      // Success
      form.reset();
      if (options.onSuccess) {
        options.onSuccess(result);
      } else {
        alert('Thank you for your feedback!');
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      if (options.onError) {
        options.onError(error);
      } else {
        alert('Failed to submit feedback. Please try again.');
      }
    } finally {
      // Re-enable submit button
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
      }
    }
  });
}

// Export for use in modules or global scope
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { submitFeedback, getCurrentPage, initFeedbackForm };
} else {
  window.submitFeedback = submitFeedback;
  window.getCurrentPage = getCurrentPage;
  window.initFeedbackForm = initFeedbackForm;
}

