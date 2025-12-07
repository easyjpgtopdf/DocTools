/**
 * PDF Editor API Client
 * Connects frontend to FastAPI backend for native PDF editing
 */

// Get backend URL
export function getBackendUrl() {
  const hostname = window.location.hostname;
  const isDevelopment = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.');
  if (isDevelopment) {
    return 'http://localhost:8080';
  }
  // Production: Use Cloud Run URL from environment or default
  // Set this in your deployment environment
  const envUrl = window.PDF_EDITOR_BACKEND_URL || 
                 (typeof process !== 'undefined' && process.env && process.env.PDF_EDITOR_BACKEND_URL) ||
                 'https://pdf-editor-backend-564572183797.us-central1.run.app';
  return envUrl;
}

const BACKEND_URL = getBackendUrl();

// Get current user ID
async function getCurrentUserId() {
  try {
    const { auth } = await import('./firebase-init.js');
    if (auth && auth.currentUser) {
      return auth.currentUser.uid;
    }
  } catch (e) {
    console.warn('Firebase not available');
  }
  return sessionStorage.getItem('userId') || null;
}

// Get user credit info from backend
export async function getUserCreditInfo() {
  const userId = await getCurrentUserId();
  if (!userId) {
    // For non-logged-in users, return free tier info
    return { credits: 0, unlimited: false, isPremium: false };
  }
  
  try {
    // Try backend API first
    const backendUrl = getBackendUrl();
    const response = await fetch(`${backendUrl}/user/credits?userId=${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return {
        credits: data.credits || 0,
        unlimited: data.unlimited || false,
        isPremium: data.isPremium || false
      };
    }
  } catch (e) {
    console.warn('Backend credits API not available, trying fallback:', e);
    
    // Fallback to frontend API if backend not available
    try {
      const apiBase = window.location.origin;
      const response = await fetch(`${apiBase}/api/credits/balance?userId=${userId}`);
      if (response.ok) {
        const data = await response.json();
        return {
          credits: data.credits || 0,
          unlimited: data.unlimited || false,
          isPremium: data.isPremium || false
        };
      }
    } catch (fallbackError) {
      console.error('Error fetching credit info from fallback:', fallbackError);
    }
  }
  
  // Default: free tier
  return { credits: 0, unlimited: false, isPremium: false };
}

// Check free limits
function checkFreeLimit(wordCount, action) {
  const FREE_LIMIT = 7;
  return {
    allowed: wordCount <= FREE_LIMIT,
    remaining: Math.max(0, FREE_LIMIT - wordCount),
    limit: FREE_LIMIT
  };
}

// Get device ID
async function getDeviceId() {
  try {
    const { getDeviceId } = await import('./device-fingerprint.js');
    return await getDeviceId();
  } catch (e) {
    // Fallback to localStorage
    let deviceId = localStorage.getItem('deviceId');
    if (!deviceId) {
      deviceId = 'device_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('deviceId', deviceId);
    }
    return deviceId;
  }
}

/**
 * Start a new PDF editing session
 */
export async function startSession(pdfFile) {
  try {
    const formData = new FormData();
    formData.append('file', pdfFile);
    
    const userId = await getCurrentUserId();
    if (userId) {
      formData.append('userId', userId);
    }
    
    const deviceId = await getDeviceId();
    formData.append('deviceId', deviceId);
    
    const response = await fetch(`${BACKEND_URL}/session/start`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start session');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error starting session:', error);
    throw error;
  }
}

/**
 * Render a PDF page as PNG
 */
export async function renderPage(sessionId, pageNumber, zoom = 1.5) {
  try {
    const response = await fetch(`${BACKEND_URL}/page/render`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        page_number: pageNumber,
        zoom: zoom
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to render page');
    }
    
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  } catch (error) {
    console.error('Error rendering page:', error);
    throw error;
  }
}

/**
 * Search for text in PDF
 */
export async function searchText(sessionId, query) {
  try {
    const response = await fetch(`${BACKEND_URL}/text/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        query: query
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to search text');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error searching text:', error);
    throw error;
  }
}

/**
 * Edit/replace text in PDF
 */
export async function editText(sessionId, pageNumber, oldText, newText, maxReplacements = 1, userId = null) {
  try {
    const deviceId = await getDeviceId();
    
    const response = await fetch(`${BACKEND_URL}/text/edit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        page_number: pageNumber,
        old_text: oldText,
        new_text: newText,
        max_replacements: maxReplacements,
        userId: userId,
        deviceId: deviceId
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to edit text');
    }
    
    const data = await response.json();
    
    // Show credit usage notification
    if (data.credits_used > 0) {
      showCreditNotification(data.credits_used, 'Text edited');
    }
    
    // Show daily limit info
    if (data.daily_limit) {
      showDailyLimitInfo(data.daily_limit);
    }
    
    return data;
  } catch (error) {
    console.error('Error editing text:', error);
    throw error;
  }
}

/**
 * Add new text to PDF
 */
export async function addText(sessionId, pageNumber, x, y, text, fontName, fontSize, color, userId) {
  try {
    const deviceId = await getDeviceId();
    
    const response = await fetch(`${BACKEND_URL}/text/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        page_number: pageNumber,
        x: x,
        y: y,
        text: text,
        font_name: fontName || 'Helvetica',
        font_size: fontSize || 12,
        color: color || [0, 0, 0],
        userId: userId,
        deviceId: deviceId
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to add text');
    }
    
    const data = await response.json();
    
    // Show credit usage notification
    if (data.credits_used > 0) {
      showCreditNotification(data.credits_used, 'Text added');
    }
    
    // Show daily limit info
    if (data.daily_limit) {
      showDailyLimitInfo(data.daily_limit);
    }
    
    return data;
  } catch (error) {
    console.error('Error adding text:', error);
    throw error;
  }
}

/**
 * Delete text from PDF
 */
export async function deleteText(sessionId, pageNumber, bbox, userId) {
  try {
    const deviceId = await getDeviceId();
    
    const response = await fetch(`${BACKEND_URL}/text/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        page_number: pageNumber,
        bbox: bbox,
        userId: userId,
        deviceId: deviceId
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete text');
    }
    
    const data = await response.json();
    
    // Show credit usage notification
    if (data.credits_used > 0) {
      showCreditNotification(data.credits_used, 'Text deleted');
    }
    
    // Show daily limit info
    if (data.daily_limit) {
      showDailyLimitInfo(data.daily_limit);
    }
    
    return data;
  } catch (error) {
    console.error('Error deleting text:', error);
    throw error;
  }
}

/**
 * Run OCR on a PDF page
 */
export async function ocrPage(sessionId, pageNumber, userId) {
  try {
    const response = await fetch(`${BACKEND_URL}/ocr/page`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        page_number: pageNumber,
        userId: userId
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to run OCR');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error running OCR:', error);
    throw error;
  }
}

/**
 * Export PDF to different formats
 */
export async function exportPDF(sessionId, format, userId) {
  try {
    const response = await fetch(`${BACKEND_URL}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId,
        format: format,
        userId: userId
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to export PDF');
    }
    
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `exported.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    return { success: true };
  } catch (error) {
    console.error('Error exporting PDF:', error);
    throw error;
  }
}

/**
 * Validate that exported PDF contains expected text objects (not images)
 * @param {Blob|string} pdfBlob - PDF blob or base64 string
 * @param {string[]} expectedTexts - Array of text strings that should exist in PDF
 * @param {number|null} pageNumber - Optional page number to validate
 * @returns {Promise<Object>} Validation result with pass/fail
 */
export async function validatePDF(pdfBlob, expectedTexts, pageNumber = null) {
  try {
    // Convert blob to base64 if needed
    let pdfBase64;
    if (pdfBlob instanceof Blob) {
      pdfBase64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          // Convert ArrayBuffer to base64
          const bytes = new Uint8Array(reader.result);
          let binary = '';
          for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
          }
          resolve(btoa(binary));
        };
        reader.onerror = reject;
        reader.readAsArrayBuffer(pdfBlob);
      });
    } else if (typeof pdfBlob === 'string') {
      // Already base64 or data URL
      if (pdfBlob.startsWith('data:application/pdf;base64,')) {
        pdfBase64 = pdfBlob.split(',')[1];
      } else {
        pdfBase64 = pdfBlob;
      }
    } else {
      throw new Error('Invalid PDF format. Expected Blob or base64 string.');
    }
    
    // Call validation endpoint
    const response = await fetch(`${BACKEND_URL}/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        pdf_bytes: pdfBase64,
        expected_texts: expectedTexts,
        page_number: pageNumber
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Validation failed');
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error validating PDF:', error);
    throw error;
  }
}

/**
 * Show credit usage notification
 */
function showCreditNotification(creditsUsed, action) {
  // Create or update notification element
  let notification = document.getElementById('credit-notification');
  if (!notification) {
    notification = document.createElement('div');
    notification.id = 'credit-notification';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #4361ee;
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10000;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
    `;
    document.body.appendChild(notification);
  }
  
  notification.innerHTML = `
    <i class="fas fa-coins"></i>
    <span>${action}: ${creditsUsed} credits used</span>
  `;
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    if (notification) {
      notification.style.opacity = '0';
      notification.style.transition = 'opacity 0.3s';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 300);
    }
  }, 3000);
}

/**
 * Show daily limit info
 */
function showDailyLimitInfo(limitInfo) {
  if (limitInfo.remaining === -1) return; // Premium user
  
  const remaining = limitInfo.remaining;
  const limit = limitInfo.limit;
  const pagesUsed = limitInfo.pages_used;
  
  if (remaining <= 2 && remaining > 0) {
    // Warning when low
    const warning = document.createElement('div');
    warning.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #ff6b6b;
      color: white;
      padding: 16px 24px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10000;
      font-size: 14px;
      max-width: 300px;
    `;
    warning.innerHTML = `
      <div style="font-weight: 600; margin-bottom: 8px;">
        <i class="fas fa-exclamation-triangle"></i> Daily Limit Warning
      </div>
      <div>You have ${remaining} page${remaining === 1 ? '' : 's'} remaining out of ${limit} free pages today.</div>
      <div style="margin-top: 12px;">
        <a href="pricing.html" style="color: white; text-decoration: underline; font-weight: 600;">
          Upgrade to Premium for Unlimited
        </a>
      </div>
    `;
    document.body.appendChild(warning);
    
    setTimeout(() => {
      warning.style.opacity = '0';
      warning.style.transition = 'opacity 0.3s';
      setTimeout(() => {
        if (warning.parentNode) {
          warning.parentNode.removeChild(warning);
        }
      }, 300);
    }, 5000);
  }
  
  // Update free limit panel if exists
  const freeLimitPanel = document.getElementById('free-limit-panel');
  if (freeLimitPanel) {
    const addLimit = freeLimitPanel.querySelector('#free-limit-add');
    const editLimit = freeLimitPanel.querySelector('#free-limit-edit');
    const deleteLimit = freeLimitPanel.querySelector('#free-limit-delete');
    
    if (addLimit) addLimit.textContent = remaining;
    if (editLimit) editLimit.textContent = remaining;
    if (deleteLimit) deleteLimit.textContent = remaining;
  }
}

/**
 * Show free limit warning (deprecated - use showDailyLimitInfo)
 */
export function showFreeLimitWarning(remaining, limit) {
  showDailyLimitInfo({ remaining, limit, pages_used: limit - remaining });
}

