/**
 * Upgrade Popup for Premium Features
 * Upgrade prompts for premium features
 */

/**
 * Show upgrade popup for premium features
 */
function showUpgradePopup(reason = 'This file requires OCR for accurate Excel conversion.') {
    // Remove existing popup if any
    const existingPopup = document.getElementById('pdf-excel-upgrade-popup');
    if (existingPopup) {
        existingPopup.remove();
    }
    
    // Create popup overlay
    const overlay = document.createElement('div');
    overlay.id = 'pdf-excel-upgrade-popup';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.3s ease;
    `;
    
    // Create popup content
    const popup = document.createElement('div');
    popup.style.cssText = `
        background: white;
        border-radius: 16px;
        padding: 32px;
        max-width: 480px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        animation: slideUp 0.3s ease;
        position: relative;
    `;
    
    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.style.cssText = `
        position: absolute;
        top: 16px;
        right: 16px;
        background: none;
        border: none;
        font-size: 32px;
        color: #9ca3af;
        cursor: pointer;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: all 0.2s;
    `;
    closeBtn.onmouseover = () => {
        closeBtn.style.background = '#f3f4f6';
        closeBtn.style.color = '#374151';
    };
    closeBtn.onmouseout = () => {
        closeBtn.style.background = 'none';
        closeBtn.style.color = '#9ca3af';
    };
    closeBtn.onclick = () => overlay.remove();
    
    // Icon
    const icon = document.createElement('div');
    icon.innerHTML = '🔒';
    icon.style.cssText = `
        font-size: 48px;
        text-align: center;
        margin-bottom: 16px;
    `;
    
    // Title
    const title = document.createElement('h2');
    title.textContent = 'Upgrade to Premium';
    title.style.cssText = `
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 12px 0;
        text-align: center;
    `;
    
    // Message
    const message = document.createElement('p');
    message.textContent = reason;
    message.style.cssText = `
        font-size: 16px;
        color: #6b7280;
        margin: 0 0 24px 0;
        text-align: center;
        line-height: 1.6;
    `;
    
    // Features list
    const features = document.createElement('div');
    features.innerHTML = `
        <div style="margin-bottom: 24px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="color: #0f9d58; font-size: 20px;">✓</span>
                <span style="color: #374151;">High-accuracy OCR for scanned PDFs</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="color: #0f9d58; font-size: 20px;">✓</span>
                <span style="color: #374151;">Complex table extraction</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="color: #0f9d58; font-size: 20px;">✓</span>
                <span style="color: #374151;">Multi-page processing</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #0f9d58; font-size: 20px;">✓</span>
                <span style="color: #374151;">Enterprise-level accuracy</span>
            </div>
        </div>
    `;
    
    // Buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
        display: flex;
        gap: 12px;
        flex-direction: column;
    `;
    
    // Upgrade button
    const upgradeBtn = document.createElement('button');
    upgradeBtn.textContent = 'Upgrade to Premium';
    upgradeBtn.style.cssText = `
        background: linear-gradient(135deg, #4361ee, #3a0ca3);
        color: white;
        border: none;
        padding: 14px 24px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        width: 100%;
    `;
    upgradeBtn.onmouseover = () => {
        upgradeBtn.style.transform = 'translateY(-2px)';
        upgradeBtn.style.boxShadow = '0 8px 20px rgba(67, 97, 238, 0.3)';
    };
    upgradeBtn.onmouseout = () => {
        upgradeBtn.style.transform = 'translateY(0)';
        upgradeBtn.style.boxShadow = 'none';
    };
    upgradeBtn.onclick = () => {
        window.location.href = 'pricing.html?feature=pdf-excel-premium';
    };
    
    // Cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Maybe Later';
    cancelBtn.style.cssText = `
        background: #f3f4f6;
        color: #374151;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
        width: 100%;
    `;
    cancelBtn.onmouseover = () => {
        cancelBtn.style.background = '#e5e7eb';
    };
    cancelBtn.onmouseout = () => {
        cancelBtn.style.background = '#f3f4f6';
    };
    cancelBtn.onclick = () => overlay.remove();
    
    buttonContainer.appendChild(upgradeBtn);
    buttonContainer.appendChild(cancelBtn);
    
    // Assemble popup
    popup.appendChild(closeBtn);
    popup.appendChild(icon);
    popup.appendChild(title);
    popup.appendChild(message);
    popup.appendChild(features);
    popup.appendChild(buttonContainer);
    
    overlay.appendChild(popup);
    document.body.appendChild(overlay);
    
    // Close on overlay click
    overlay.onclick = (e) => {
        if (e.target === overlay) {
            overlay.remove();
        }
    };
    
    // Close on ESC key
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            overlay.remove();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    // Add animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Show credit insufficient popup
 */
function showCreditInsufficientPopup(required, available) {
    showUpgradePopup(
        `You need ${required} credits but only have ${available}. ` +
        `Please purchase credits or upgrade to Premium to continue.`
    );
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.PDFExcelUpgradePopup = {
        showUpgradePopup,
        showCreditInsufficientPopup
    };
}

