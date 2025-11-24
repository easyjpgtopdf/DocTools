/**
 * Global Header & Footer Component Loader
 * Dynamically loads header and footer across all pages
 * Auto-updates all pages when header/footer changes
 */

// Prevent multiple executions
if (window.globalComponentsLoaded) {
    console.warn('Global components already loaded, skipping duplicate execution');
} else {
    window.globalComponentsLoaded = true;
}

// Get current page filename for active link highlighting
const currentPage = window.location.pathname.split('/').pop() || 'index.html';

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
            <div class="nav-links">
                <a href="index.html" class="nav-link">Home</a>
                <a href="login.html" class="nav-link">Sign In</a>
                <a href="signup.html" class="nav-link">Signup</a>
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
                    </div>
                </div>
                <div class="dropdown">
                    <a href="#">Other Tools <i class="fas fa-chevron-down"></i></a>
                    <div class="dropdown-content">
                        <a href="excel-unlocker/" target="_blank">Excel Unlocker</a>
                        <a href="protect-excel.html">Protect Excel Sheet</a>
                    </div>
                </div>
            </div>
            <div id="user-menu" class="user-menu" data-open="false">
                <button id="user-menu-toggle" class="user-menu-toggle" type="button" aria-haspopup="true" aria-expanded="false" aria-label="Account menu">
                    <span class="user-initial" aria-hidden="true">U</span>
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
                        <a href="excel-unlocker/" target="_blank">Excel Unlocker</a>
                        <a href="protect-excel.html">Protect Excel Sheet</a>
                    </div>
                </div>
                <div class="mobile-menu-auth">
                    <a href="login.html" class="mobile-auth-link">Sign In</a>
                    <a href="signup.html" class="mobile-auth-btn">Signup</a>
                </div>
            </nav>
        </div>
    </div>
</header>
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
        </div>
        <p class="footer-brand-line">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone. All rights reserved.</p>
        <p class="footer-credits">
            Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
            <a href="attributions.html">See full acknowledgements</a>.
        </p>
    </div>
</footer>
`;

// Function to load header
function loadGlobalHeader() {
    const headerPlaceholder = document.getElementById('global-header-placeholder');
    if (headerPlaceholder) {
        headerPlaceholder.outerHTML = globalHeaderHTML;
        highlightActiveLink();
        initializeMobileMenu();
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

// Auto-initialize when DOM is ready (only if not already loaded)
if (!window.globalComponentsInitialized) {
    window.globalComponentsInitialized = true;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            loadGlobalHeader();
            loadGlobalFooter();
        });
    } else {
        loadGlobalHeader();
        loadGlobalFooter();
    }
}

// Export functions for manual use if needed
window.loadGlobalHeader = loadGlobalHeader;
window.loadGlobalFooter = loadGlobalFooter;
