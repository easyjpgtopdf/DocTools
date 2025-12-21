/**
 * Premium Activator for PDF to Excel
 * Sets user type to PREMIUM after successful payment/subscription
 */

/**
 * Activate premium access for PDF to Excel
 * Called after successful payment/subscription purchase
 */
function activatePdfExcelPremium() {
    try {
        if (window.PDFExcelUserType) {
            window.PDFExcelUserType.setUserType('premium');
            console.log('✅ PDF to Excel Premium activated');
            
            // Dispatch event for UI update
            window.dispatchEvent(new CustomEvent('pdfExcelPremiumActivated', {
                detail: { timestamp: Date.now() }
            }));
            
            return true;
        } else {
            // Fallback: Set directly in localStorage
            localStorage.setItem('pdf_excel_user_type', 'premium');
            console.log('✅ PDF to Excel Premium activated (fallback)');
            return true;
        }
    } catch (error) {
        console.error('Error activating premium:', error);
        return false;
    }
}

/**
 * Check if user should get premium access based on credits
 * If credits >= 15, automatically activate premium
 */
async function checkAndActivatePremium() {
    try {
        if (window.PDFExcelUserType) {
            const credits = await window.PDFExcelUserType.getCreditBalance();
            const MIN_PREMIUM_CREDITS = window.PDFExcelUserType.MIN_PREMIUM_CREDITS || 15;
            
            if (credits >= MIN_PREMIUM_CREDITS) {
                // User has enough credits, activate premium
                activatePdfExcelPremium();
                return true;
            }
        }
    } catch (error) {
        console.warn('Error checking premium eligibility:', error);
    }
    return false;
}

/**
 * Listen for payment success events
 */
function setupPremiumActivationListeners() {
    // Listen for credit purchase success
    window.addEventListener('creditsUpdated', async (event) => {
        const credits = event.detail.credits;
        const MIN_PREMIUM_CREDITS = 15;
        
        if (credits >= MIN_PREMIUM_CREDITS) {
            // User has enough credits, activate premium
            activatePdfExcelPremium();
        }
    });
    
    // Listen for subscription activation
    window.addEventListener('subscriptionActivated', (event) => {
        const plan = event.detail.plan;
        if (plan === 'pro' || plan === 'proplus' || plan === 'business') {
            // Premium plan purchased, activate premium
            activatePdfExcelPremium();
        }
    });
    
    // Listen for payment success (from payment-method.html)
    window.addEventListener('paymentSuccess', (event) => {
        // Payment successful, check credits and activate if eligible
        setTimeout(() => {
            checkAndActivatePremium();
        }, 2000); // Wait 2 seconds for credits to be updated
    });
}

// Auto-setup listeners when script loads
if (typeof window !== 'undefined') {
    // Wait for DOM and other modules
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupPremiumActivationListeners);
    } else {
        setupPremiumActivationListeners();
    }
    
    // Also check on load (in case user already has credits)
    window.addEventListener('load', () => {
        setTimeout(() => {
            checkAndActivatePremium();
        }, 1000);
    });
}

// Export functions
if (typeof window !== 'undefined') {
    window.PDFExcelPremiumActivator = {
        activatePdfExcelPremium,
        checkAndActivatePremium,
        setupPremiumActivationListeners
    };
}

