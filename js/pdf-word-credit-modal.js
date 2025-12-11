/**
 * Credit Modal for PDF to Word Conversion
 * Shows credit cost and allows user to proceed or purchase credits
 */

const API_BASE_URL = 'https://pdf-to-word-converter-iwumaktavq-uc.a.run.app';

// Credit Modal HTML
const creditModalHTML = `
<div id="creditModal" class="credit-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.6); z-index: 10000; backdrop-filter: blur(4px); align-items: center; justify-content: center;">
    <div class="credit-modal-content" style="background: white; border-radius: 16px; max-width: 500px; width: 90%; padding: 0; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
        <div class="credit-modal-header" style="padding: 24px; border-bottom: 2px solid #e2e6ff; display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; font-size: 1.3rem; color: #0b1630; font-weight: 700;">
                <i class="fas fa-coins" style="color: #4361ee; margin-right: 8px;"></i>
                Credit Required
            </h3>
            <button id="creditModalClose" style="background: none; border: none; font-size: 1.5rem; color: #56607a; cursor: pointer; padding: 4px 8px; border-radius: 50%; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="credit-modal-body" style="padding: 24px;">
            <div id="creditModalInfo" style="margin-bottom: 20px;">
                <p style="color: #56607a; margin-bottom: 16px;">
                    <strong>File:</strong> <span id="creditFileName"></span><br>
                    <strong>Pages:</strong> <span id="creditPageCount"></span><br>
                    <strong>Estimated Credits:</strong> <span id="creditCost" style="color: #4361ee; font-weight: 700; font-size: 1.1rem;"></span>
                </p>
                <div style="background: #f8f9ff; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                    <p style="margin: 0 0 8px 0; font-size: 0.9rem; color: #56607a;">
                        <i class="fas fa-info-circle" style="color: #4361ee; margin-right: 6px;"></i>
                        <strong>Current Balance:</strong> <span id="creditBalance" style="color: #0b1630; font-weight: 600;"></span> credits
                    </p>
                    <p style="margin: 0; font-size: 0.85rem; color: #999;">
                        Text-based: 0.5 credits/page | Scanned (OCR): 1 credit/page
                    </p>
                </div>
            </div>
            <div id="creditModalInsufficient" style="display: none; background: #fff5f5; padding: 16px; border-radius: 8px; border: 1px solid #fee; margin-bottom: 16px;">
                <p style="margin: 0; color: #dc2626; font-weight: 600;">
                    <i class="fas fa-exclamation-triangle" style="margin-right: 6px;"></i>
                    Insufficient Credits
                </p>
                <p style="margin: 8px 0 0 0; font-size: 0.9rem; color: #721c24;">
                    You need <span id="creditRequired"></span> credits but only have <span id="creditAvailable"></span> credits.
                </p>
            </div>
            <div style="display: flex; gap: 12px;">
                <button id="creditModalProceed" class="btn" style="flex: 1; background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 1rem;">
                    <i class="fas fa-check"></i> Continue
                </button>
                <button id="creditModalBuy" class="btn secondary" style="flex: 1; background: white; color: #4361ee; border: 2px solid #4361ee; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 1rem;">
                    <i class="fas fa-shopping-cart"></i> Buy Credits
                </button>
            </div>
        </div>
    </div>
</div>
`;

// Inject modal HTML into page
function injectCreditModal() {
    if (typeof document !== 'undefined' && document.body && !document.getElementById('creditModal')) {
        document.body.insertAdjacentHTML('beforeend', creditModalHTML);
    }
}

// Inject immediately if DOM ready, otherwise wait
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectCreditModal);
    } else {
        injectCreditModal();
    }
}

/**
 * Show credit modal with file info and cost
 */
export async function showCreditModal(file, pages, estimatedCreditsText, estimatedCreditsOcr) {
    return new Promise(async (resolve, reject) => {
        const modal = document.getElementById('creditModal');
        if (!modal) {
            // Modal not loaded yet, reject
            reject(new Error('Credit modal not available'));
            return;
        }
        
        // Get user credits
        let userCredits = 0;
        try {
            const userId = await getCurrentUserId();
            if (userId) {
                const token = await getAuthToken();
                const response = await fetch(`${API_BASE_URL}/api/user/credits`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    userCredits = data.credits || 0;
                }
            }
        } catch (e) {
            console.warn('Failed to get user credits:', e);
        }
        
        // Use OCR estimate (higher cost) for safety
        const estimatedCredits = estimatedCreditsOcr;
        
        // Update modal content
        document.getElementById('creditFileName').textContent = file.name;
        document.getElementById('creditPageCount').textContent = pages;
        document.getElementById('creditCost').textContent = estimatedCredits + ' credits';
        document.getElementById('creditBalance').textContent = userCredits.toFixed(1);
        
        const insufficientDiv = document.getElementById('creditModalInsufficient');
        const proceedBtn = document.getElementById('creditModalProceed');
        const buyBtn = document.getElementById('creditModalBuy');
        
        if (userCredits < estimatedCredits) {
            insufficientDiv.style.display = 'block';
            document.getElementById('creditRequired').textContent = estimatedCredits;
            document.getElementById('creditAvailable').textContent = userCredits.toFixed(1);
            proceedBtn.disabled = true;
            proceedBtn.style.opacity = '0.5';
            proceedBtn.style.cursor = 'not-allowed';
        } else {
            insufficientDiv.style.display = 'none';
            proceedBtn.disabled = false;
            proceedBtn.style.opacity = '1';
            proceedBtn.style.cursor = 'pointer';
        }
        
        // Show modal
        modal.style.display = 'flex';
        
        // Close button
        document.getElementById('creditModalClose').onclick = () => {
            modal.style.display = 'none';
            reject(new Error('User cancelled'));
        };
        
        // Proceed button
        proceedBtn.onclick = () => {
            modal.style.display = 'none';
            resolve(true);
        };
        
        // Buy credits button
        buyBtn.onclick = () => {
            modal.style.display = 'none';
            window.location.href = '/pricing.html#credits';
            reject(new Error('Redirecting to purchase'));
        };
        
        // Close on backdrop click
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
                reject(new Error('User cancelled'));
            }
        };
    });
}

/**
 * Get current user ID from Firebase Auth
 */
async function getCurrentUserId() {
    try {
        // Import auth from firebase-init
        const { app } = await import('./firebase-init.js');
        const { getAuth } = await import('https://www.gstatic.com/firebasejs/10.14.0/firebase-auth.js');
        const auth = getAuth(app);
        
        if (auth && auth.currentUser) {
            return auth.currentUser.uid;
        }
        
        // Wait for auth state
        return new Promise((resolve) => {
            const { onAuthStateChanged } = require('https://www.gstatic.com/firebasejs/10.14.0/firebase-auth.js');
            const unsubscribe = onAuthStateChanged(auth, (user) => {
                unsubscribe();
                resolve(user ? user.uid : null);
            });
            setTimeout(() => resolve(null), 2000);
        });
    } catch (e) {
        console.warn('Error getting user ID:', e);
        return null;
    }
}

/**
 * Get auth token
 */
async function getAuthToken() {
    try {
        const { app } = await import('./firebase-init.js');
        const { getAuth } = await import('https://www.gstatic.com/firebasejs/10.14.0/firebase-auth.js');
        const auth = getAuth(app);
        
        if (auth && auth.currentUser) {
            return await auth.currentUser.getIdToken();
        }
        return null;
    } catch (e) {
        return null;
    }
}

// Export for use
if (typeof window !== 'undefined') {
    window.showCreditModal = showCreditModal;
}

