/**
 * Global Header & Footer Component Loader
 * Dynamically loads header and footer across all pages
 * Auto-updates all pages when header/footer changes
 */

// Prevent multiple executions - wrap entire script
(function() {
    'use strict';
    
    // Prevent duplicate script execution
    if (window.globalComponentsLoaded) {
        console.warn('Global components already loaded, skipping duplicate execution');
        return; // Exit early if already loaded
    }
    window.globalComponentsLoaded = true;

// Get current page filename for active link highlighting
// Use window property to avoid duplicate declaration errors
var currentPage;
if (typeof window.currentPage === 'undefined') {
    window.currentPage = window.location.pathname.split('/').pop() || 'index.html';
}
currentPage = window.currentPage;

// Global Account Section HTML (Above Header) - with O logo
const globalAccountSectionHTML = `
<div id="account-section" class="account-section" style="display: none; visibility: hidden;">
    <div class="container">
        <div id="user-menu" class="user-menu" data-open="false">
            <button id="user-menu-toggle" class="user-menu-toggle" type="button" aria-haspopup="true" aria-expanded="false" aria-label="Account menu">
                <img src="images/user-logo-o.svg" alt="User Account" class="user-logo-o" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';">
                <span class="user-logo-fallback" style="display: none; width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem;">O</span>
                <span class="user-id" id="user-id-display"></span>
                <span id="credit-balance-nav" style="display: none; margin-left: 8px; padding: 2px 8px; background: rgba(67,97,238,0.1); border-radius: 12px; font-size: 0.85rem; color: #4361ee; font-weight: 600;">
                    <i class="fas fa-coins" style="margin-right: 4px;"></i>
                    <span id="credit-balance-value">0</span>
                </span>
                <i class="fas fa-chevron-down" aria-hidden="true"></i>
            </button>
            <div class="user-dropdown" id="user-dropdown" hidden>
                <a href="dashboard.html#dashboard-overview" data-user-nav="dashboard-overview"><i class="fas fa-user-circle"></i> Account Dashboard</a>
                <a href="dashboard.html#dashboard-billing" data-user-nav="dashboard-billing"><i class="fas fa-file-invoice"></i> Billing Details</a>
                <a href="dashboard.html#dashboard-payments" data-user-nav="dashboard-payments"><i class="fas fa-wallet"></i> Payment History</a>
                <a href="dashboard.html#dashboard-orders" data-user-nav="dashboard-orders"><i class="fas fa-clipboard-list"></i> Orders & Subscriptions</a>
                <a href="dashboard.html#dashboard-credits" data-user-nav="dashboard-credits"><i class="fas fa-coins"></i> Credit History</a>
                <a href="accounts.html#login"><i class="fas fa-user-cog"></i> Account Center</a>
                <button type="button" id="logout-button" class="dropdown-logout"><i class="fas fa-sign-out-alt"></i> Sign out</button>
            </div>
        </div>
    </div>
</div>
`;

// Global Header HTML
const globalHeaderHTML = `
<header>
    <div class="container">
        <nav class="navbar">
            <a href="index.html" class="logo"><img src="images/logo.png" alt="Logo" style="height:54px;"></a>
            <button class="mobile-menu-toggle" id="mobile-menu-toggle" aria-label="Toggle mobile menu" aria-expanded="false">
                <span></span>
                <span></span>
                <span></span>
            </button>
            <!-- Mobile Tool Summary - Shows tool categories in header -->
            <div class="nav-links-summary" style="display: none;">
                <a href="jpg-to-pdf.html">JPG to PDF</a>
                <a href="word-to-pdf.html">Word to PDF</a>
                <a href="merge-pdf.html">Merge PDF</a>
                <a href="split-pdf.html">Split PDF</a>
                <a href="compress-pdf.html">Compress PDF</a>
                <a href="image-compressor.html">Image Tools</a>
                <a href="pricing.html">Pricing</a>
            </div>
            <div class="nav-links">
                <div class="dropdown">
                    <a href="#">Convert to PDF <i class="fas fa-chevron-down"></i></a>
                    <div class="dropdown-content">
                        <a href="jpg-to-pdf.html">JPG to PDF</a>
                        <a href="word-to-pdf.html">Word to PDF</a>
                        <a href="excel-to-pdf.html">Excel to PDF</a>
                        <a href="ppt-to-pdf.html">PowerPoint to PDF</a>
                    </div>
                </div>
                <div class="dropdown">
                    <a href="#">Convert from PDF <i class="fas fa-chevron-down"></i></a>
                    <div class="dropdown-content">
                        <a href="pdf-to-jpg.html">PDF to JPG</a>
                        <a href="pdf-to-word.html">PDF to Word</a>
                        <a href="pdf-to-excel.html">PDF to Excel</a>
                        <a href="pdf-to-ppt.html">PDF to PowerPoint</a>
                    </div>
                </div>
                <div class="dropdown">
                    <a href="#">Pdf Editor <i class="fas fa-chevron-down"></i></a>
                    <div class="dropdown-content">
                        <a href="merge-pdf.html">Merge PDF</a>
                        <a href="split-pdf.html">Split PDF</a>
                        <a href="compress-pdf.html">Compress PDF</a>
                        <a href="edit-pdf.html">Pdf Editor</a>
                        <a href="protect-pdf.html">Protect PDF</a>
                        <a href="unlock-pdf.html">Unlock PDF</a>
                        <a href="watermark-pdf.html">Watermark PDF</a>
                        <a href="crop-pdf.html">Crop PDF</a>
                        <a href="add-page-numbers.html">Add Page Numbers</a>
                    </div>
                </div>
                <div class="dropdown">
                    <a href="#">Image Tools <i class="fas fa-chevron-down"></i></a>
                    <div class="dropdown-content">
                        <a href="image-compressor.html">Image Compressor</a>
                        <a href="image-resizer.html">Image Resizer</a>
                        <a href="image-editor.html">Image Editor</a>
                        <a href="background-remover.html">Image Background Remover</a>
                        <a href="ocr-image.html">OCR Image</a>
                        <a href="image-watermark.html">Image Watermark Tool</a>
                    </div>
                </div>
                <div class="dropdown">
                    <a href="#">Other Tools <i class="fas fa-chevron-down"></i></a>
                    <div class="dropdown-content">
                        <a href="resume-maker.html">Resume Maker</a>
                        <a href="biodata-maker.html">Marrige Biodata-Data Maker</a>
                        <a href="ai-image-generator.html">AI Image Generator</a>
                        <a href="marriage-card.html">Marriage Card</a>
                        <a href="excel-unlocker/index.html">Excel Unlocker</a>
                        <a href="protect-excel.html">Protect Excel Sheet</a>
                    </div>
                </div>
                <div class="dropdown">
                    <a href="#">More <i class="fas fa-chevron-down"></i></a>
                    <div class="dropdown-content">
                        <a href="pricing.html">Pricing</a>
                        <a href="blog.html">Blog / Articles</a>
                    </div>
                </div>
            </div>
        </nav>
    </div>
    <!-- Mobile Menu Overlay -->
    <div class="mobile-menu-overlay" id="mobile-menu-overlay">
        <div class="mobile-menu-content">
            <div class="mobile-menu-header">
                <a href="/" class="mobile-logo"><img src="/images/logo.png" alt="Logo" style="height:40px;"></a>
                <button class="mobile-menu-close" id="mobile-menu-close" aria-label="Close mobile menu">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <nav class="mobile-nav-links">
                <div class="mobile-dropdown">
                    <button class="mobile-dropdown-toggle" aria-expanded="false">
                        Convert to PDF <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="mobile-dropdown-content">
                        <a href="jpg-to-pdf.html">JPG to PDF</a>
                        <a href="word-to-pdf.html">Word to PDF</a>
                        <a href="excel-to-pdf.html">Excel to PDF</a>
                        <a href="ppt-to-pdf.html">PowerPoint to PDF</a>
                    </div>
                </div>
                <div class="mobile-dropdown">
                    <button class="mobile-dropdown-toggle" aria-expanded="false">
                        Convert from PDF <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="mobile-dropdown-content">
                        <a href="pdf-to-jpg.html">PDF to JPG</a>
                        <a href="pdf-to-word.html">PDF to Word</a>
                        <a href="pdf-to-excel.html">PDF to Excel</a>
                        <a href="pdf-to-ppt.html">PDF to PowerPoint</a>
                    </div>
                </div>
                <div class="mobile-dropdown">
                    <button class="mobile-dropdown-toggle" aria-expanded="false">
                        Pdf Editor <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="mobile-dropdown-content">
                        <a href="merge-pdf.html">Merge PDF</a>
                        <a href="split-pdf.html">Split PDF</a>
                        <a href="compress-pdf.html">Compress PDF</a>
                        <a href="edit-pdf.html">Pdf Editor</a>
                        <a href="protect-pdf.html">Protect PDF</a>
                        <a href="unlock-pdf.html">Unlock PDF</a>
                        <a href="watermark-pdf.html">Watermark PDF</a>
                        <a href="crop-pdf.html">Crop PDF</a>
                        <a href="add-page-numbers.html">Add Page Numbers</a>
                    </div>
                </div>
                <div class="mobile-dropdown">
                    <button class="mobile-dropdown-toggle" aria-expanded="false">
                        Image Tools <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="mobile-dropdown-content">
                        <a href="image-compressor.html">Image Compressor</a>
                        <a href="image-resizer.html">Image Resizer</a>
                        <a href="image-editor.html">Image Editor</a>
                        <a href="background-remover.html">Image Background Remover</a>
                        <a href="ocr-image.html">OCR Image</a>
                        <a href="image-watermark.html">Image Watermark Tool</a>
                    </div>
                </div>
                <div class="mobile-dropdown">
                    <button class="mobile-dropdown-toggle" aria-expanded="false">
                        Other Tools <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="mobile-dropdown-content">
                        <a href="resume-maker.html">Resume Maker</a>
                        <a href="biodata-maker.html">Marrige Biodata-Data Maker</a>
                        <a href="ai-image-generator.html">AI Image Generator</a>
                        <a href="marriage-card.html">Marriage Card</a>
                        <a href="excel-unlocker/index.html">Excel Unlocker</a>
                        <a href="protect-excel.html">Protect Excel Sheet</a>
                    </div>
                </div>
                <div class="mobile-dropdown">
                    <button class="mobile-dropdown-toggle" aria-expanded="false">
                        More <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="mobile-dropdown-content">
                        <a href="pricing.html">Pricing</a>
                        <a href="blog.html">Blog / Articles</a>
                    </div>
                </div>
            </nav>
        </div>
    </div>
</header>
`;

// Global Breadcrumb HTML - with dynamic Sign In/Signup buttons
const globalBreadcrumbHTML = `
    <nav aria-label="Breadcrumb" style="padding: 15px 0; background: #f8f9ff; border-bottom: 1px solid #e2e6ff;">
        <div class="container" style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
            <ol style="list-style: none; display: flex; flex-wrap: wrap; gap: 10px; margin: 0; padding: 0; align-items: center;">
                <li><a href="index.html" style="color: #4361ee; text-decoration: none; font-weight: 500; transition: color 0.3s;" onmouseover="this.style.color='#3a0ca3'" onmouseout="this.style.color='#4361ee'">Home</a></li>
                <li class="breadcrumb-auth-separator" style="margin: 0 8px; color: #9ca3af;">|</li>
                <li class="breadcrumb-signin-item"><a href="login.html" class="breadcrumb-signin-link" style="color: #56607a; font-weight: 500; text-decoration: none; transition: color 0.3s;" onmouseover="this.style.color='#4361ee'" onmouseout="this.style.color='#56607a'">Sign In</a></li>
                <li class="breadcrumb-auth-separator" style="margin: 0 8px; color: #9ca3af;">|</li>
                <li class="breadcrumb-signup-item"><a href="signup.html" class="breadcrumb-signup-link" style="color: #56607a; font-weight: 500; text-decoration: none; transition: color 0.3s;" onmouseover="this.style.color='#4361ee'" onmouseout="this.style.color='#56607a'">Signup</a></li>
            </ol>
        </div>
    </nav>
`;

// Global Footer HTML
const globalFooterHTML = `
<footer>
    <div class="container footer-inner">
        <div class="footer-company-links">
            <span>Company</span>
            <a href="about.html">About Us</a>
            <a href="contact.html">Contact</a>
            <a href="pricing.html">Pricing</a>
            <a href="privacy-policy.html">Privacy Policy</a>
            <a href="terms-of-service.html">Terms of Service</a>
            <a href="disclaimer.html">Disclaimer</a>
            <a href="dmca.html">DMCA</a>
            <a href="blog.html">Blog</a>
            <a href="feedback.html">Feedback</a>
        </div>
        <p class="footer-brand-line">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone. All rights reserved.</p>
        <p class="footer-credits">
            Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
            <a href="attributions.html">See full acknowledgements</a>.
        </p>
        <div class="footer-social-search" style="display: flex; align-items: center; justify-content: space-between; margin-top: 20px; padding-top: 20px; border-top: 1px solid #444; flex-wrap: wrap; gap: 15px;">
            <div class="footer-social-links" style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                <a href="https://x.com/easyjpgtopdf" target="_blank" rel="noopener noreferrer" title="Follow us on X (Twitter)" style="display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; color: #aaa; text-decoration: none; transition: all 0.3s; border-radius: 50%;" onmouseover="this.style.color='#fff'; this.style.background='rgba(255,255,255,0.1)'" onmouseout="this.style.color='#aaa'; this.style.background='transparent'">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <a href="https://www.youtube.com/@EasyJpgtoPdf" target="_blank" rel="noopener noreferrer" title="Subscribe to our YouTube channel" style="display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; color: #aaa; text-decoration: none; transition: all 0.3s; border-radius: 50%;" onmouseover="this.style.color='#fff'; this.style.background='rgba(255,255,255,0.1)'" onmouseout="this.style.color='#aaa'; this.style.background='transparent'">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                    </svg>
                </a>
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; color: #aaa; cursor: default;" title="Mobile App Coming Soon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                        <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.95-3.24-1.44-2.24-1.01-4.33-1.95-5.99-3.22C2.79 14.25.99 12.12.99 9.12c0-2.23 1.21-4.15 3.29-5.19.4-.2.81-.38 1.24-.52.7-.23 1.23-.52 1.62-.82.49-.38.85-.88 1.06-1.46.19-.57.24-1.17.14-1.8-.09-.63-.29-1.24-.58-1.81L7.76.36c.16-.24.35-.45.57-.62.22-.17.46-.3.72-.4.26-.1.54-.15.82-.15.28 0 .56.05.82.15.26.1.5.23.72.4.22.17.41.38.57.62l1.39 2.06c.29.57.49 1.18.58 1.81.1.63.05 1.23-.14 1.8-.21.58-.57 1.08-1.06 1.46-.39.3-.92.59-1.62.82-.43.14-.84.32-1.24.52-2.08 1.04-3.29 2.96-3.29 5.19 0 3 1.8 5.13 4.5 6.5 1.66 1.27 3.75 2.21 5.99 3.22 1.16.49 2.15.94 3.24 1.44 1.03.48 2.1.55 3.08-.4 1.01-.98 1.01-2.4.01-3.38z"/>
                    </svg>
                </div>
            </div>
            <div class="footer-search" style="flex: 1; min-width: 200px; max-width: 300px;">
                <form action="search.html" method="get" style="display: flex; gap: 5px;">
                    <input type="text" name="q" placeholder="Search our site..." style="flex: 1; padding: 8px 12px; border: 1px solid #555; border-radius: 4px; background: #2a2a2a; color: #fff; font-size: 0.9rem; outline: none;" onfocus="this.style.borderColor='#4361ee'" onblur="this.style.borderColor='#555'">
                    <button type="submit" style="padding: 8px 15px; background: #4361ee; border: none; border-radius: 4px; color: #fff; cursor: pointer; transition: background 0.3s;" onmouseover="this.style.background='#3a0ca3'" onmouseout="this.style.background='#4361ee'">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                            <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                        </svg>
                    </button>
                </form>
            </div>
        </div>
    </div>
</footer>
`;

// Function to load account section - Enhanced to work on ALL pages
function loadAccountSection() {
    // Check if account section already exists
    let existingAccountSection = document.getElementById('account-section');
    if (existingAccountSection) {
        // If it's an empty div (like in index.html), replace it with proper content
        if (existingAccountSection.children.length === 0) {
            try {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = globalAccountSectionHTML.trim();
                const accountElement = tempDiv.firstElementChild;
                if (accountElement) {
                    existingAccountSection.outerHTML = accountElement.outerHTML;
                    // Re-initialize auth UI after account section is loaded
                    if (typeof window.initializeAuthUI === 'function') {
                        setTimeout(() => {
                            window.initializeAuthUI();
                        }, 100);
                    }
                }
            } catch (error) {
                console.error('Error replacing empty account section:', error);
            }
        } else {
            // Ensure it's properly positioned
            const header = document.querySelector('header');
            if (header && existingAccountSection.nextSibling !== header && existingAccountSection.parentNode !== header.parentNode) {
                try {
                    header.parentNode.insertBefore(existingAccountSection, header);
                } catch (e) {
                    console.warn('Could not reposition account section:', e);
                }
            }
        }
        return;
    }
    
    // Try to insert account section before header
    const header = document.querySelector('header');
    if (header) {
        try {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = globalAccountSectionHTML.trim();
            const accountElement = tempDiv.firstElementChild;
            if (accountElement) {
                header.parentNode.insertBefore(accountElement, header);
                // Re-initialize auth UI after account section is loaded
                if (typeof window.initializeAuthUI === 'function') {
                    setTimeout(() => {
                        window.initializeAuthUI();
                    }, 100);
                }
            }
        } catch (error) {
            console.error('Error adding account section:', error);
        }
    } else {
        // If no header yet, try to insert at body start
        const body = document.body;
        if (body) {
            try {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = globalAccountSectionHTML.trim();
                const accountElement = tempDiv.firstElementChild;
                if (accountElement) {
                    body.insertBefore(accountElement, body.firstChild);
                    // Re-initialize auth UI after account section is loaded
                    if (typeof window.initializeAuthUI === 'function') {
                        setTimeout(() => {
                            window.initializeAuthUI();
                        }, 100);
                    }
                }
            } catch (error) {
                console.error('Error adding account section to body:', error);
            }
        }
    }
    
    // Retry mechanism - ensure it loads even if header loads later
    setTimeout(() => {
        existingAccountSection = document.getElementById('account-section');
        if (!existingAccountSection) {
            loadAccountSection();
        }
    }, 500);
}

// Function to load header
function loadGlobalHeader() {
    // Check if header already exists and is properly loaded
    const existingHeader = document.querySelector('header');
    if (existingHeader && existingHeader.querySelector('.navbar')) {
        // Header already loaded, just initialize mobile menu if needed
        const mobileToggle = document.getElementById('mobile-menu-toggle');
        if (mobileToggle && !mobileToggle.hasAttribute('data-initialized')) {
            initializeMobileMenu();
            mobileToggle.setAttribute('data-initialized', 'true');
        }
        // Also ensure account section is loaded
        loadAccountSection();
        return;
    }
    
    console.log('loadGlobalHeader called - attempting to load header...');
    
    // Load account section first
    loadAccountSection();
    
    // Try to find placeholder
    let headerPlaceholder = document.getElementById('global-header-placeholder');
    
    // If placeholder exists and is a div, replace it
    if (headerPlaceholder && (headerPlaceholder.tagName === 'DIV' || headerPlaceholder.tagName === 'div')) {
        try {
            // Replace placeholder with header HTML
            headerPlaceholder.outerHTML = globalHeaderHTML;
            
            // Wait for DOM to update, then initialize
            requestAnimationFrame(function() {
                highlightActiveLink();
                initializeMobileMenu();
                loadGlobalBreadcrumb();
                loadAccountSection();
                updateBreadcrumbAuthButtons();
                console.log('Header loaded successfully!');
            });
            return;
        } catch (error) {
            console.error('Error replacing header placeholder:', error);
        }
    }
    
    // Fallback: If no placeholder or replacement failed, try to insert at body start
    if (!document.querySelector('header')) {
        try {
            const body = document.body;
            if (body) {
                // Remove placeholder if it exists but wasn't replaced
                if (headerPlaceholder && headerPlaceholder.parentNode) {
                    headerPlaceholder.parentNode.removeChild(headerPlaceholder);
                }
                
                // Create and insert header
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = globalHeaderHTML.trim();
                const headerElement = tempDiv.firstElementChild;
                if (headerElement) {
                    body.insertBefore(headerElement, body.firstChild);
                    requestAnimationFrame(function() {
                        highlightActiveLink();
                        initializeMobileMenu();
                        loadGlobalBreadcrumb();
                        loadAccountSection();
                        updateBreadcrumbAuthButtons();
                        console.log('Header loaded successfully (fallback method)!');
                    });
                }
            }
        } catch (error) {
            console.error('Error adding global header to body:', error);
        }
    }
}

// Function to load breadcrumb
function loadGlobalBreadcrumb() {
    // Check for existing breadcrumbs
    const existingBreadcrumbs = document.querySelectorAll('nav[aria-label="Breadcrumb"]');
    if (existingBreadcrumbs.length > 0) {
        // If breadcrumb exists but doesn't have the required classes, replace it
        const firstBreadcrumb = existingBreadcrumbs[0];
        const hasAuthClasses = firstBreadcrumb.querySelector('.breadcrumb-signin-item') !== null;
        
        if (!hasAuthClasses) {
            // Replace with new breadcrumb that has proper classes
            try {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = globalBreadcrumbHTML.trim();
                const newBreadcrumb = tempDiv.firstElementChild;
                if (newBreadcrumb) {
                    firstBreadcrumb.outerHTML = newBreadcrumb.outerHTML;
                    updateBreadcrumbAuthButtons();
                }
            } catch (error) {
                console.error('Error replacing breadcrumb:', error);
            }
        } else {
            // Update existing breadcrumb auth buttons visibility
            updateBreadcrumbAuthButtons();
        }
        return;
    }
    
    const breadcrumbPlaceholder = document.getElementById('global-breadcrumb-placeholder');
    if (breadcrumbPlaceholder) {
        breadcrumbPlaceholder.outerHTML = globalBreadcrumbHTML;
        // Wait a bit for DOM to update
        setTimeout(() => {
            updateBreadcrumbAuthButtons();
        }, 50);
    } else {
        // If no placeholder, try to add breadcrumb after header
        const header = document.querySelector('header');
        if (header && !document.querySelector('nav[aria-label="Breadcrumb"]')) {
            const breadcrumbDiv = document.createElement('div');
            breadcrumbDiv.innerHTML = globalBreadcrumbHTML.trim();
            header.insertAdjacentElement('afterend', breadcrumbDiv.firstElementChild);
            setTimeout(() => {
                updateBreadcrumbAuthButtons();
            }, 50);
        }
    }
}

// Function to update breadcrumb Sign In/Signup buttons based on auth state
function updateBreadcrumbAuthButtons() {
    try {
        let userLoggedIn = false;
        
        // Check if Firebase auth is available and user is logged in
        if (typeof firebase !== 'undefined' && firebase.auth) {
            try {
                const currentUser = firebase.auth().currentUser;
                userLoggedIn = currentUser !== null;
            } catch (e) {
                // Firebase not initialized yet
            }
        }
        
        // Also check if auth.js has initialized and user exists
        if (!userLoggedIn && typeof window !== 'undefined' && window.auth) {
            try {
                userLoggedIn = window.auth.currentUser !== null;
            } catch (e) {
                // Auth not initialized yet
            }
        }
        
        // Find all breadcrumb auth elements (both new format with classes and old format)
        const signInItems = document.querySelectorAll('.breadcrumb-signin-item');
        const signUpItems = document.querySelectorAll('.breadcrumb-signup-item');
        const authSeparators = document.querySelectorAll('.breadcrumb-auth-separator');
        
        // Also find old format breadcrumb items (for backward compatibility)
        const allBreadcrumbs = document.querySelectorAll('nav[aria-label="Breadcrumb"]');
        allBreadcrumbs.forEach(breadcrumb => {
            const signInLinks = breadcrumb.querySelectorAll('a[href*="login.html"]');
            const signUpLinks = breadcrumb.querySelectorAll('a[href*="signup.html"]');
            const allListItems = breadcrumb.querySelectorAll('li');
            
            if (userLoggedIn) {
                // Hide Sign In and Signup links in old format
                signInLinks.forEach(link => {
                    const listItem = link.closest('li');
                    if (listItem && !listItem.classList.contains('breadcrumb-signin-item')) {
                        listItem.style.display = 'none';
                    }
                });
                signUpLinks.forEach(link => {
                    const listItem = link.closest('li');
                    if (listItem && !listItem.classList.contains('breadcrumb-signup-item')) {
                        listItem.style.display = 'none';
                    }
                });
                // Hide separators before/after auth links
                allListItems.forEach((li, index) => {
                    const prevLi = allListItems[index - 1];
                    const nextLi = allListItems[index + 1];
                    if ((prevLi && (prevLi.querySelector('a[href*="login.html"]') || prevLi.querySelector('a[href*="signup.html"]'))) ||
                        (nextLi && (nextLi.querySelector('a[href*="login.html"]') || nextLi.querySelector('a[href*="signup.html"]')))) {
                        if (li.textContent.trim() === '|') {
                            li.style.display = 'none';
                        }
                    }
                });
            } else {
                // Show Sign In and Signup links in old format
                signInLinks.forEach(link => {
                    const listItem = link.closest('li');
                    if (listItem && !listItem.classList.contains('breadcrumb-signin-item')) {
                        listItem.style.display = 'list-item';
                    }
                });
                signUpLinks.forEach(link => {
                    const listItem = link.closest('li');
                    if (listItem && !listItem.classList.contains('breadcrumb-signup-item')) {
                        listItem.style.display = 'list-item';
                    }
                });
            }
        });
        
        // Update new format breadcrumb elements
        if (userLoggedIn) {
            // Hide Sign In and Signup buttons when user is logged in
            signInItems.forEach(item => {
                if (item) item.style.display = 'none';
            });
            signUpItems.forEach(item => {
                if (item) item.style.display = 'none';
            });
            authSeparators.forEach(sep => {
                if (sep) sep.style.display = 'none';
            });
        } else {
            // Show Sign In and Signup buttons when user is not logged in
            signInItems.forEach(item => {
                if (item) item.style.display = 'list-item';
            });
            signUpItems.forEach(item => {
                if (item) item.style.display = 'list-item';
            });
            // Show separators only if there are visible items
            authSeparators.forEach(sep => {
                if (sep) sep.style.display = '';
            });
        }
    } catch (error) {
        console.warn('Error updating breadcrumb auth buttons:', error);
    }
}

// Initialize mobile menu functionality
function initializeMobileMenu() {
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenuClose = document.getElementById('mobile-menu-close');
    const mobileMenuOverlay = document.getElementById('mobile-menu-overlay');
    const mobileDropdownToggles = document.querySelectorAll('.mobile-dropdown-toggle');
    
    // Toggle mobile menu
    if (mobileMenuToggle && mobileMenuOverlay) {
        mobileMenuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            mobileMenuOverlay.classList.add('active');
            mobileMenuToggle.setAttribute('aria-expanded', 'true');
            document.body.style.overflow = 'hidden'; // Prevent body scroll
        });
    }
    
    // Close mobile menu
    if (mobileMenuClose && mobileMenuOverlay) {
        mobileMenuClose.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            mobileMenuOverlay.classList.remove('active');
            if (mobileMenuToggle) mobileMenuToggle.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = ''; // Restore body scroll
        });
    }
    
    // Close menu when clicking overlay
    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener('click', function(e) {
            if (e.target === mobileMenuOverlay) {
                mobileMenuOverlay.classList.remove('active');
                if (mobileMenuToggle) mobileMenuToggle.setAttribute('aria-expanded', 'false');
                document.body.style.overflow = ''; // Restore body scroll
            }
        });
    }
    
    // Mobile dropdown toggles (touch-friendly) - support both click and touch
    mobileDropdownToggles.forEach(toggle => {
        ['click', 'touchstart'].forEach(eventType => {
            toggle.addEventListener(eventType, function(e) {
                e.preventDefault();
                e.stopPropagation();
                const dropdown = this.parentElement;
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                
                // Close all other dropdowns
                mobileDropdownToggles.forEach(otherToggle => {
                    if (otherToggle !== this) {
                        otherToggle.setAttribute('aria-expanded', 'false');
                        otherToggle.parentElement.classList.remove('active');
                    }
                });
                
                // Toggle current dropdown
                const newState = !isExpanded;
                this.setAttribute('aria-expanded', newState);
                dropdown.classList.toggle('active', newState);
                
                // Ensure dropdown content is visible when active
                const dropdownContent = dropdown.querySelector('.mobile-dropdown-content');
                if (dropdownContent) {
                    if (newState) {
                        dropdownContent.style.display = 'block';
                    } else {
                        // Use setTimeout to allow transition to complete
                        setTimeout(() => {
                            if (!dropdown.classList.contains('active')) {
                                dropdownContent.style.display = '';
                            }
                        }, 300);
                    }
                }
            }, { passive: false });
        });
    });
    
    // Close menu on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && mobileMenuOverlay && mobileMenuOverlay.classList.contains('active')) {
            mobileMenuOverlay.classList.remove('active');
            if (mobileMenuToggle) mobileMenuToggle.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = '';
        }
    });
}

// Function to load footer
function loadGlobalFooter() {
    const footerPlaceholder = document.getElementById('global-footer-placeholder');
    if (footerPlaceholder) {
        footerPlaceholder.outerHTML = globalFooterHTML;
    }
}

// Function to highlight active navigation link
function highlightActiveLink() {
    const navLinks = document.querySelectorAll('.navbar a[href]');
    navLinks.forEach(link => {
        const linkHref = link.getAttribute('href');
        if (linkHref === currentPage || (currentPage === '' && linkHref === 'index.html')) {
            link.classList.add('active');
        }
    });
}

// Function to highlight active account dropdown link
function highlightActiveAccountLink() {
    const accountLinks = document.querySelectorAll('#user-dropdown a[data-user-nav]');
    const currentHash = window.location.hash || '#dashboard-overview';
    accountLinks.forEach(link => {
        const linkHash = '#' + link.getAttribute('data-user-nav');
        if (linkHash === currentHash) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Auto-initialize when DOM is ready (only if not already loaded)
if (!window.globalComponentsInitialized) {
    window.globalComponentsInitialized = true;
    
    function initializeComponents() {
        loadGlobalHeader();
        loadGlobalFooter();
    }
    
    // Multiple initialization strategies to ensure header loads
    function forceLoadHeader() {
        const placeholder = document.getElementById('global-header-placeholder');
        const existingHeader = document.querySelector('header');
        
        // If placeholder exists but no header, force load
        if (placeholder && !existingHeader) {
            try {
                placeholder.outerHTML = globalHeaderHTML;
                setTimeout(function() {
                    highlightActiveLink();
                    initializeMobileMenu();
                    loadGlobalBreadcrumb();
                    loadAccountSection();
                    updateBreadcrumbAuthButtons();
                }, 10);
            } catch (e) {
                console.error('Force load header error:', e);
            }
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initializeComponents();
            // Also try after a delay
            setTimeout(forceLoadHeader, 100);
            setTimeout(forceLoadHeader, 500);
        });
    } else {
        // DOM already ready
        initializeComponents();
        setTimeout(forceLoadHeader, 50);
        setTimeout(forceLoadHeader, 200);
        setTimeout(forceLoadHeader, 500);
    }
    
    // Final attempt after page fully loads
    window.addEventListener('load', function() {
        if (!document.querySelector('header')) {
            forceLoadHeader();
        }
        // Ensure account section is loaded on ALL pages
        loadAccountSection();
        // Update breadcrumb auth buttons
        updateBreadcrumbAuthButtons();
        // Monitor auth state changes to update breadcrumb
        if (typeof firebase !== 'undefined' && firebase.auth) {
            firebase.auth().onAuthStateChanged(function(user) {
                setTimeout(() => {
                    updateBreadcrumbAuthButtons();
                }, 100);
            });
        }
    });
}

// Export functions for manual use if needed
window.loadGlobalHeader = loadGlobalHeader;
window.loadGlobalFooter = loadGlobalFooter;
window.loadGlobalBreadcrumb = loadGlobalBreadcrumb;
window.loadAccountSection = loadAccountSection;
window.highlightActiveAccountLink = highlightActiveAccountLink;
window.updateBreadcrumbAuthButtons = updateBreadcrumbAuthButtons;

// Make function available globally immediately
if (typeof window !== 'undefined') {
    window.loadGlobalHeader = loadGlobalHeader;
    window.loadGlobalFooter = loadGlobalFooter;
    window.loadGlobalBreadcrumb = loadGlobalBreadcrumb;
    window.loadAccountSection = loadAccountSection;
    window.highlightActiveAccountLink = highlightActiveAccountLink;
    window.updateBreadcrumbAuthButtons = updateBreadcrumbAuthButtons;
}

})(); // Close IIFE to prevent duplicate execution
