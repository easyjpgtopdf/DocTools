// Share Utilities for easyjpgtopdf

/**
 * Initialize share functionality for a page
 * @param {string} title - Title for sharing
 * @param {string} text - Text description for sharing
 * @param {string} [customUrl] - Custom URL to share (defaults to current page URL)
 */
function initShareButtons(title, text, customUrl) {
    const pageLink = customUrl || window.location.href.split('#')[0];
    const shareText = text || 'Check out this PDF tool';
    
    // Set up share links if elements exist
    const shareWhatsApp = document.getElementById('shareWhatsApp');
    const shareFacebook = document.getElementById('shareFacebook');
    const shareTwitter = document.getElementById('shareTwitter');
    const shareLinkedIn = document.getElementById('shareLinkedIn');
    const shareEmail = document.getElementById('shareEmail');
    const nativeShare = document.getElementById('nativeShare');
    
    // Set up social media share links
    if (shareWhatsApp) {
        shareWhatsApp.href = `https://wa.me/?text=${encodeURIComponent(shareText)}%20${encodeURIComponent(pageLink)}`;
    }
    
    if (shareFacebook) {
        shareFacebook.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(pageLink)}`;
    }
    
    if (shareTwitter) {
        shareTwitter.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(pageLink)}`;
    }
    
    if (shareLinkedIn) {
        shareLinkedIn.href = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(pageLink)}`;
    }
    
    if (shareEmail) {
        shareEmail.href = `mailto:?subject=${encodeURIComponent(shareText)}&body=${encodeURIComponent(`Check this out: ${pageLink}`)}`;
    }
    
    // Native share functionality
    if (nativeShare) {
        nativeShare.addEventListener('click', async () => {
            try {
                if (navigator.share) {
                    await navigator.share({
                        title: title || document.title,
                        text: shareText,
                        url: pageLink
                    });
                } else if (navigator.clipboard) {
                    await navigator.clipboard.writeText(pageLink);
                    showToast('Link copied to clipboard!');
                } else {
                    showToast('Sharing not supported in this browser');
                }
            } catch (err) {
                if (err.name !== 'AbortError') {
                    console.error('Share failed:', err);
                    showToast('Failed to share');
                }
            }
        });
    }
}

/**
 * Show a toast message
 * @param {string} message - Message to display
 * @param {number} [duration=2000] - Duration in milliseconds
 */
function showToast(message, duration = 2000) {
    // Create toast element if it doesn't exist
    let toast = document.getElementById('share-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'share-toast';
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.left = '50%';
        toast.style.transform = 'translateX(-50%)';
        toast.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        toast.style.color = 'white';
        toast.style.padding = '12px 24px';
        toast.style.borderRadius = '25px';
        toast.style.zIndex = '1000';
        toast.style.transition = 'opacity 0.3s';
        toast.style.opacity = '0';
        document.body.appendChild(toast);
    }
    
    // Set message and show
    toast.textContent = message;
    toast.style.opacity = '1';
    
    // Hide after duration
    setTimeout(() => {
        toast.style.opacity = '0';
    }, duration - 300);
    
    // Remove after animation
    setTimeout(() => {
        if (toast.style.opacity === '0') {
            document.body.removeChild(toast);
        }
    }, duration);
}

// Auto-initialize if share buttons are present
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.share-bar')) {
        initShareButtons();
    }
});



