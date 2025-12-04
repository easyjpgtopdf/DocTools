/**
 * Usage Limits Management
 * Check and enforce usage limits for PDF operations
 */

/**
 * Check if user can perform PDF operation
 * @param {string} operationType - 'pdf', 'storage', 'api'
 * @returns {Promise<{allowed: boolean, message?: string}>}
 */
export async function checkUsageLimit(operationType = 'pdf') {
    try {
        // Get auth token
        const { auth } = await import('./firebase-init.js');
        const user = auth.currentUser;
        
        if (!user) {
            // Guest users have limited access
            return { allowed: true, message: 'Guest access - limits may apply' };
        }
        
        const token = await user.getIdToken();
        const apiBaseUrl = window.location.origin;
        
        const response = await fetch(`${apiBaseUrl}/api/subscription/check-limit`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: operationType })
        });
        
        if (!response.ok) {
            const error = await response.json();
            return {
                allowed: false,
                message: error.message || 'Usage limit reached. Please upgrade your plan.'
            };
        }
        
        const data = await response.json();
        
        if (data.success && !data.limitReached) {
            return { allowed: true };
        } else {
            return {
                allowed: false,
                message: data.message || 'Usage limit reached. Please upgrade your plan.'
            };
        }
    } catch (error) {
        console.error('Error checking usage limit:', error);
        // Allow operation if check fails (fail-open for better UX)
        return { allowed: true, message: 'Unable to verify usage limits' };
    }
}

/**
 * Increment usage counter after successful operation
 * @param {string} operationType - 'pdf', 'storage', 'api'
 * @param {number} amount - Amount to increment (default: 1)
 */
export async function incrementUsage(operationType = 'pdf', amount = 1) {
    try {
        const { auth } = await import('./firebase-init.js');
        const user = auth.currentUser;
        
        if (!user) {
            return; // Guest users don't track usage
        }
        
        const token = await user.getIdToken();
        const apiBaseUrl = window.location.origin;
        
        await fetch(`${apiBaseUrl}/api/subscription/increment-usage`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: operationType, amount: amount })
        });
    } catch (error) {
        console.error('Error incrementing usage:', error);
        // Don't block operation if increment fails
    }
}

/**
 * Show usage limit warning/error
 * @param {string} message - Message to display
 * @param {boolean} isError - If true, show as error; otherwise as warning
 */
export function showUsageLimitMessage(message, isError = false) {
    // Create or update usage limit notification
    let notification = document.getElementById('usage-limit-notification');
    
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'usage-limit-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${isError ? '#dc3545' : '#ff9800'};
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 400px;
            display: flex;
            align-items: center;
            gap: 12px;
        `;
        document.body.appendChild(notification);
    }
    
    notification.innerHTML = `
        <i class="fas fa-${isError ? 'exclamation-triangle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: white; cursor: pointer; margin-left: auto;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (notification && notification.parentElement) {
            notification.remove();
        }
    }, 10000);
}

// Export for use in other files
window.usageLimits = {
    checkUsageLimit,
    incrementUsage,
    showUsageLimitMessage
};







