/**
 * User Type Detection for PDF to Excel Converter
 * FREE vs PREMIUM architecture (iLovePDF style)
 * 
 * Rules:
 * - FREE users: ZERO AI cost, browser-based only
 * - PREMIUM users: Google Document AI (heavy OCR)
 * - Minimum 15 credits required for premium conversion
 */

// User types
const USER_TYPE = {
    FREE: 'free',
    PREMIUM: 'premium'
};

// Minimum credits required for premium features (UPDATED: 30 credits)
const MIN_PREMIUM_CREDITS = 30;

/**
 * Get current user type from localStorage
 * Defaults to FREE if not set
 */
function getUserType() {
    try {
        const userType = localStorage.getItem('pdf_excel_user_type');
        if (userType === USER_TYPE.PREMIUM || userType === USER_TYPE.FREE) {
            return userType;
        }
    } catch (e) {
        console.warn('Error reading user type:', e);
    }
    return USER_TYPE.FREE; // Default to FREE
}

/**
 * Set user type (typically after payment/subscription)
 */
function setUserType(type) {
    try {
        if (type === USER_TYPE.PREMIUM || type === USER_TYPE.FREE) {
            localStorage.setItem('pdf_excel_user_type', type);
            return true;
        }
    } catch (e) {
        console.error('Error setting user type:', e);
    }
    return false;
}

/**
 * Check if user has premium access
 * Premium access is granted if credits >= MIN_PREMIUM_CREDITS (30)
 * User type in localStorage is not required - credits are the primary check
 */
async function hasPremiumAccess() {
    // Check credits via API - this is the primary check
    try {
        const API_BASE_URL = 'https://pdf-to-excel-backend-iwumaktavq-uc.a.run.app';
        const userId = await getUserId(); // Use async getUserId to get Firebase user ID
        const response = await fetch(`${API_BASE_URL}/api/credits`, {
            method: 'GET',
            headers: {
                'X-User-ID': userId
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const hasCredits = data.credits >= MIN_PREMIUM_CREDITS;
            
            // If user has sufficient credits, automatically set user type to premium
            if (hasCredits) {
                setUserType(USER_TYPE.PREMIUM);
            }
            
            return hasCredits;
        }
    } catch (e) {
        console.warn('Error checking credits:', e);
    }
    
    // Fallback: check localStorage user type (for backward compatibility)
    const userType = getUserType();
    return userType === USER_TYPE.PREMIUM;
}

/**
 * Get user ID - prefers Firebase authenticated user ID, falls back to localStorage
 */
async function getUserId() {
    try {
        // Try importing Firebase auth from firebase-init.js (most reliable method)
        try {
            const { auth } = await import("./firebase-init.js");
            if (auth && auth.currentUser && auth.currentUser.uid) {
                return auth.currentUser.uid;
            }
            // If not immediately available, wait for auth state
            if (auth) {
                const { onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.14.0/firebase-auth.js");
                return new Promise((resolve) => {
                    const unsubscribe = onAuthStateChanged(auth, (user) => {
                        unsubscribe();
                        if (user && user.uid) {
                            resolve(user.uid);
                        } else {
                            // Fallback to localStorage
                            resolve(getLocalStorageUserId());
                        }
                    });
                    // Timeout after 1 second if auth doesn't resolve
                    setTimeout(() => {
                        unsubscribe();
                        resolve(getLocalStorageUserId());
                    }, 1000);
                });
            }
        } catch (e) {
            // Firebase not available, continue to fallback
        }
        
        // Fallback to localStorage
        return getLocalStorageUserId();
    } catch (e) {
        // Final fallback to session-based ID
        return 'anonymous_' + Date.now();
    }
}

/**
 * Get user ID from localStorage or generate one
 * 
 * WARNING: This should only be used as a fallback.
 * Real credits require Firebase authentication.
 */
function getLocalStorageUserId() {
    try {
        let userId = localStorage.getItem('pdf_excel_user_id');
        if (!userId) {
            // Generate a unique ID
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('pdf_excel_user_id', userId);
            console.warn(`Generated localStorage user_id: ${userId}. This will NOT have real credits!`);
            console.warn('User must log in with Firebase to access real credits.');
        } else {
            console.warn(`Using localStorage user_id: ${userId}. This may not match Firebase UID!`);
        }
        return userId;
    } catch (e) {
        const fallbackId = 'anonymous_' + Date.now();
        console.error(`Error getting localStorage user_id, using fallback: ${fallbackId}`);
        return fallbackId;
    }
}

/**
 * Get current credit balance
 */
async function getCreditBalance() {
    try {
        const API_BASE_URL = 'https://pdf-to-excel-backend-iwumaktavq-uc.a.run.app';
        const userId = await getUserId(); // Use async getUserId to get Firebase user ID
        const response = await fetch(`${API_BASE_URL}/api/credits`, {
            method: 'GET',
            headers: {
                'X-User-ID': userId
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.credits || 0;
        }
    } catch (e) {
        console.warn('Error fetching credits:', e);
    }
    return 0;
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.PDFExcelUserType = {
        USER_TYPE,
        getUserType,
        setUserType,
        hasPremiumAccess,
        getUserId,
        getCreditBalance,
        MIN_PREMIUM_CREDITS
    };
}

