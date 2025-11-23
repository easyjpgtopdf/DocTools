#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Comment Modal Fix - Final
- Ensure fallback listeners work
- Fix modal open/close
- Ensure it works after login
- Fix X button and outside click
"""

import os
import re
import glob

BLOG_PAGES = glob.glob("blog-*.html")

def complete_modal_fix(html_content):
    """Complete fix for comment modal"""
    
    fixes = []
    
    # 1. Ensure fallback listener opens modal correctly
    fallback_pattern = r'function attachEventListenersAlways\(\) \{[\s\S]*?newBox\.addEventListener\([\'"]click[\'"], function\(e\) \{[\s\S]*?e\.preventDefault\(\);[\s\S]*?e\.stopPropagation\(\);[\s\S]*?console\.log\([\'"]Comment box clicked[\'"]\);[\s\S]*?// Check login status[\s\S]*?const userSession = localStorage\.getItem\([\'"]userSession[\'"]\);[\s\S]*?const isLoggedIn = userSession !== null;[\s\S]*?if \(!isLoggedIn\) \{[\s\S]*?const currentUrl = window\.location\.href;[\s\S]*?sessionStorage\.setItem\([\'"]openCommentModalAfterLogin[\'"], [\'"]true[\'"]\);[\s\S]*?sessionStorage\.setItem\([\'"]returnUrl[\'"], currentUrl\);[\s\S]*?window\.location\.href = [\'"]login\.html\?returnUrl=[\'"] \+ encodeURIComponent\(currentUrl\);[\s\S]*?return;[\s\S]*?\}[\s\S]*?// Open modal[\s\S]*?const modal = document\.getElementById\([\'"]commentModal[\'"]\);[\s\S]*?if \(modal\) \{[\s\S]*?modal\.classList\.add\([\'"]active[\'"]\);[\s\S]*?document\.body\.style\.overflow = [\'"]hidden[\'"];[\s\S]*?// Try to load comments if Firebase is ready[\s\S]*?if \(typeof loadComments === [\'"]function[\'"]\) \{[\s\S]*?try \{[\s\S]*?loadComments\(\);[\s\S]*?\} catch \(err\) \{[\s\S]*?console\.error\([\'"]Error loading comments:[\'"], err\);[\s\S]*?\}[\s\S]*?\}[\s\S]*?\} else \{[\s\S]*?console\.error\([\'"]Comment modal not found[\'"]\);[\s\S]*?alert\([\'"]Comment system unavailable\. Please refresh the page\.[\'"]\);[\s\S]*?\}[\s\S]*?\}\);'
    
    if not re.search(fallback_pattern, html_content):
        # Add complete fallback listener
        complete_fallback = '''
            // Always attach event listeners, even if Firebase fails
            function attachEventListenersAlways() {
                const triggerBox = document.getElementById('commentTriggerBox');
                if (triggerBox) {
                    // Remove existing listeners by cloning
                    const newBox = triggerBox.cloneNode(true);
                    triggerBox.parentNode.replaceChild(newBox, triggerBox);
                    
                    newBox.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Comment box clicked');
                        
                        // Check login status from multiple sources
                        let isLoggedIn = false;
                        
                        // Check localStorage
                        const userSession = localStorage.getItem('userSession');
                        if (userSession) {
                            try {
                                const user = JSON.parse(userSession);
                                if (user && user.uid) {
                                    isLoggedIn = true;
                                }
                            } catch (e) {
                                console.error('Error parsing user session:', e);
                            }
                        }
                        
                        // Also check if currentUser is set
                        if (!isLoggedIn && typeof currentUser !== 'undefined' && currentUser !== null) {
                            isLoggedIn = true;
                        }
                        
                        if (!isLoggedIn) {
                            const currentUrl = window.location.href;
                            sessionStorage.setItem('openCommentModalAfterLogin', 'true');
                            sessionStorage.setItem('returnUrl', currentUrl);
                            window.location.href = 'login.html?returnUrl=' + encodeURIComponent(currentUrl);
                            return;
                        }
                        
                        // User is logged in, open modal
                        const scrollPos = window.pageYOffset || document.documentElement.scrollTop;
                        if (typeof scrollPosition !== 'undefined') {
                            scrollPosition = scrollPos;
                        }
                        
                        const modal = document.getElementById('commentModal');
                        if (modal) {
                            modal.classList.add('active');
                            document.body.style.overflow = 'hidden';
                            
                            // Try to load comments if Firebase is ready
                            if (typeof loadComments === 'function') {
                                try {
                                    loadComments();
                                } catch (err) {
                                    console.error('Error loading comments:', err);
                                }
                            }
                        } else {
                            console.error('Comment modal not found');
                            alert('Comment system unavailable. Please refresh the page.');
                        }
                    });
                }
                
                // Close button
                const closeBtn = document.getElementById('commentModalClose');
                if (closeBtn) {
                    // Remove existing listeners
                    const newCloseBtn = closeBtn.cloneNode(true);
                    closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
                    
                    newCloseBtn.addEventListener('click', function() {
                        const modal = document.getElementById('commentModal');
                        if (modal) {
                            modal.classList.remove('active');
                            document.body.style.overflow = '';
                            // Restore scroll position
                            const scrollPos = typeof scrollPosition !== 'undefined' ? scrollPosition : 0;
                            window.scrollTo(0, scrollPos);
                        }
                    });
                }
                
                // Close on outside click
                const modal = document.getElementById('commentModal');
                if (modal) {
                    // Remove existing listeners
                    const newModal = modal.cloneNode(true);
                    modal.parentNode.replaceChild(newModal, modal);
                    
                    newModal.addEventListener('click', function(e) {
                        if (e.target === newModal) {
                            newModal.classList.remove('active');
                            document.body.style.overflow = '';
                            const scrollPos = typeof scrollPosition !== 'undefined' ? scrollPosition : 0;
                            window.scrollTo(0, scrollPos);
                        }
                    });
                }
                
                // Close on Escape key
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        const modal = document.getElementById('commentModal');
                        if (modal && modal.classList.contains('active')) {
                            modal.classList.remove('active');
                            document.body.style.overflow = '';
                            const scrollPos = typeof scrollPosition !== 'undefined' ? scrollPosition : 0;
                            window.scrollTo(0, scrollPos);
                        }
                    }
                });
            }
            
            // Attach listeners immediately
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', attachEventListenersAlways);
            } else {
                attachEventListenersAlways();
            }
'''
        
        # Find where to insert (before closing script tag, after fallback section)
        if '})().catch(error =>' in html_content and 'attachEventListenersFallback' in html_content:
            # Replace the fallback section
            html_content = re.sub(
                r'function attachEventListenersFallback\(\) \{[\s\S]*?attachEventListenersFallback\(\);[\s\S]*?\}',
                complete_fallback.strip(),
                html_content
            )
            fixes.append("Added complete fallback event listeners")
        elif '</script>' in html_content and 'Comment System Script' in html_content:
            # Insert before closing script
            script_end = html_content.rfind('</script>', 0, html_content.find('</body>'))
            if script_end > 0:
                html_content = html_content[:script_end] + complete_fallback + '\n    ' + html_content[script_end:]
                fixes.append("Added complete fallback event listeners")
    
    # 2. Ensure scrollPosition is defined at the top
    if 'let scrollPosition = 0;' not in html_content and 'var scrollPosition = 0;' not in html_content:
        # Add at the beginning of the script
        if '// Firebase configuration' in html_content:
            html_content = html_content.replace(
                '// Firebase configuration',
                '// Scroll position for modal\n        let scrollPosition = 0;\n\n        // Firebase configuration'
            )
            fixes.append("Added scrollPosition variable")
    
    # 3. Ensure modal CSS has proper z-index
    if '.comment-modal.active' in html_content:
        # Check z-index
        if 'z-index: 10000' not in html_content and 'z-index: 9999' not in html_content:
            # Add z-index to modal
            modal_css_pattern = r'(\.comment-modal \{[\s\S]*?position: fixed;)'
            replacement = r'\1\n            z-index: 10000;'
            html_content = re.sub(modal_css_pattern, replacement, html_content)
            fixes.append("Added z-index to modal")
    
    return html_content, fixes

def main():
    print("🔧 Completing comment modal fix...\n")
    
    fixed_count = 0
    for blog_file in BLOG_PAGES:
        if os.path.exists(blog_file):
            try:
                with open(blog_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if 'commentTriggerBox' in content:
                    original = content
                    content, fixes = complete_modal_fix(content)
                    
                    if content != original or fixes:
                        with open(blog_file, "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"   ✅ Fixed {blog_file}")
                        for fix in fixes:
                            print(f"      - {fix}")
                        fixed_count += 1
            except Exception as e:
                print(f"   ❌ Error fixing {blog_file}: {e}")
    
    print(f"\n✅ Completed fix for {fixed_count} blog pages!")
    print("\n✅ Complete Action Flow:")
    print("   1. User clicks 'Add a comment...' box")
    print("   2. If not logged in → Redirects to login page")
    print("   3. User logs in → Returns to blog page")
    print("   4. Modal opens automatically (popup on same page)")
    print("   5. User can comment and reply in modal")
    print("   6. Click X button → Modal closes, stays on page")
    print("   7. Click outside modal → Modal closes, stays on page")
    print("   8. Press Escape → Modal closes, stays on page")
    print("   9. Click comment box again → Modal opens immediately")

if __name__ == "__main__":
    main()

