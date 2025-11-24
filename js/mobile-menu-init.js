/**
 * Mobile Menu Initialization
 * Ensures mobile menu works properly on all pages
 */

(function() {
    'use strict';
    
    function initializeMobileMenu() {
        const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
        const mobileMenuClose = document.getElementById('mobile-menu-close');
        const mobileMenuOverlay = document.getElementById('mobile-menu-overlay');
        const mobileDropdownToggles = document.querySelectorAll('.mobile-dropdown-toggle');
        
        if (!mobileMenuToggle || !mobileMenuOverlay) {
            return; // Elements not found, skip initialization
        }
        
        // Toggle mobile menu - support both click and touch
        ['click', 'touchend'].forEach(eventType => {
            mobileMenuToggle.addEventListener(eventType, function(e) {
                e.preventDefault();
                e.stopPropagation();
                const isExpanded = mobileMenuToggle.getAttribute('aria-expanded') === 'true';
                
                if (isExpanded) {
                    // Close menu
                    mobileMenuOverlay.classList.remove('active');
                    mobileMenuToggle.setAttribute('aria-expanded', 'false');
                    document.body.style.overflow = '';
                } else {
                    // Open menu
                    mobileMenuOverlay.classList.add('active');
                    mobileMenuToggle.setAttribute('aria-expanded', 'true');
                    document.body.style.overflow = 'hidden';
                }
            }, { passive: false });
        });
        
        // Close mobile menu - support both click and touch
        if (mobileMenuClose) {
            ['click', 'touchend'].forEach(eventType => {
                mobileMenuClose.addEventListener(eventType, function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    mobileMenuOverlay.classList.remove('active');
                    mobileMenuToggle.setAttribute('aria-expanded', 'false');
                    document.body.style.overflow = '';
                }, { passive: false });
            });
        }
        
        // Close menu when clicking overlay
        mobileMenuOverlay.addEventListener('click', function(e) {
            if (e.target === mobileMenuOverlay) {
                mobileMenuOverlay.classList.remove('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
                document.body.style.overflow = '';
            }
        });
        
        // Mobile dropdown toggles (touch-friendly)
        mobileDropdownToggles.forEach(toggle => {
            // Use both click and touchstart for better mobile support
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
            if (e.key === 'Escape' && mobileMenuOverlay.classList.contains('active')) {
                mobileMenuOverlay.classList.remove('active');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
                document.body.style.overflow = '';
            }
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeMobileMenu);
    } else {
        initializeMobileMenu();
    }
    
    // Also initialize after a short delay to catch dynamically loaded headers
    setTimeout(initializeMobileMenu, 500);
})();

