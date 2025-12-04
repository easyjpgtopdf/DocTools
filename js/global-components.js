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

// Global Account Section HTML (Above Header)
const globalAccountSectionHTML = `
<div id="account-section" class="account-section" style="display: none; visibility: hidden;">
    <div class="container">
        <div id="user-menu" class="user-menu" data-open="false">
            <button id="user-menu-toggle" class="user-menu-toggle" type="button" aria-haspopup="true" aria-expanded="false" aria-label="Account menu">
                <span class="account-label">Account</span>
                <span class="user-id" id="user-id-display"></span>
                <i class="fas fa-chevron-down" aria-hidden="true"></i>
            </button>
            <div class="user-dropdown" id="user-dropdown" hidden>
                <a href="dashboard.html#dashboard-overview" data-user-nav="dashboard-overview"><i class="fas fa-user-circle"></i> Account Dashboard</a>
                <a href="dashboard.html#dashboard-billing" data-user-nav="dashboard-billing"><i class="fas fa-file-invoice"></i> Billing Details</a>
                <a href="dashboard.html#dashboard-payments" data-user-nav="dashboard-payments"><i class="fas fa-wallet"></i> Payment History</a>
                <a href="dashboard.html#dashboard-orders" data-user-nav="dashboard-orders"><i class="fas fa-clipboard-list"></i> Orders & Subscriptions</a>
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
                <a href="index.html" class="mobile-logo"><img src="images/logo.png" alt="Logo" style="height:40px;"></a>
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

// Global Breadcrumb HTML
const globalBreadcrumbHTML = `
    <nav aria-label="Breadcrumb" style="padding: 15px 0; background: #f8f9ff; border-bottom: 1px solid #e2e6ff;">
        <div class="container" style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
            <ol style="list-style: none; display: flex; flex-wrap: wrap; gap: 10px; margin: 0; padding: 0; align-items: center;">
                <li><a href="index.html" style="color: #4361ee; text-decoration: none; font-weight: 500; transition: color 0.3s;" onmouseover="this.style.color='#3a0ca3'" onmouseout="this.style.color='#4361ee'">Home</a></li>
                <li><span style="margin: 0 8px; color: #9ca3af;">|</span></li>
                <li><a href="login.html" style="color: #56607a; font-weight: 500; text-decoration: none; transition: color 0.3s;" onmouseover="this.style.color='#4361ee'" onmouseout="this.style.color='#56607a'">Sign In</a></li>
                <li><span style="margin: 0 8px; color: #9ca3af;">|</span></li>
                <li><a href="signup.html" style="color: #56607a; font-weight: 500; text-decoration: none; transition: color 0.3s;" onmouseover="this.style.color='#4361ee'" onmouseout="this.style.color='#56607a'">Signup</a></li>
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
    </div>
</footer>
`;

// Function to load account section
function loadAccountSection() {
    // Check if account section already exists
    const existingAccountSection = document.getElementById('account-section');
    if (existingAccountSection) {
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
    // Prevent duplicate breadcrumbs
    const existingBreadcrumbs = document.querySelectorAll('nav[aria-label="Breadcrumb"]');
    if (existingBreadcrumbs.length > 0) {
        console.warn('Breadcrumb already exists, skipping duplicate load');
        return;
    }
    
    const breadcrumbPlaceholder = document.getElementById('global-breadcrumb-placeholder');
    if (breadcrumbPlaceholder) {
        breadcrumbPlaceholder.outerHTML = globalBreadcrumbHTML;
    } else {
        // If no placeholder, try to add breadcrumb after header
        const header = document.querySelector('header');
        if (header && !document.querySelector('nav[aria-label="Breadcrumb"]')) {
            const breadcrumbDiv = document.createElement('div');
            breadcrumbDiv.innerHTML = globalBreadcrumbHTML.trim();
            header.insertAdjacentElement('afterend', breadcrumbDiv.firstElementChild);
        }
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
        // Ensure account section is loaded
        loadAccountSection();
    });
}

// Export functions for manual use if needed
window.loadGlobalHeader = loadGlobalHeader;
window.loadGlobalFooter = loadGlobalFooter;
window.loadGlobalBreadcrumb = loadGlobalBreadcrumb;
window.loadAccountSection = loadAccountSection;
window.highlightActiveAccountLink = highlightActiveAccountLink;

// Make function available globally immediately
if (typeof window !== 'undefined') {
    window.loadGlobalHeader = loadGlobalHeader;
    window.loadGlobalFooter = loadGlobalFooter;
    window.loadGlobalBreadcrumb = loadGlobalBreadcrumb;
    window.loadAccountSection = loadAccountSection;
    window.highlightActiveAccountLink = highlightActiveAccountLink;
}

})(); // Close IIFE to prevent duplicate execution
