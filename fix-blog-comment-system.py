#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Blog Comment System Issues
- Ensure Firebase imports are correct
- Fix event listener attachment
- Ensure modal functions work
- Add error handling
"""

import os
import re
import glob

BLOG_PAGES = glob.glob("blog-*.html")

def fix_comment_system(html_content):
    """Fix comment system issues"""
    
    # 1. Ensure Firebase imports are using correct version
    html_content = re.sub(
        r'firebasejs/10\.\d+\.\d+/firebase',
        r'firebasejs/10.14.0/firebase',
        html_content
    )
    
    # 2. Ensure comment trigger box has proper event handling
    # Check if event listener is properly attached
    if 'attachEventListeners' in html_content and 'commentTriggerBox' in html_content:
        # Ensure event listener attaches even if DOM is ready
        pattern = r'(function attachEventListeners\(\) \{[\s\S]*?if \(triggerBox\) \{[\s\S]*?triggerBox\.addEventListener\([\'"]click[\'"], function\(e\) \{[\s\S]*?e\.preventDefault\(\);[\s\S]*?e\.stopPropagation\(\);[\s\S]*?console\.log\([\'"]Comment trigger clicked[\'"]\);[\s\S]*?if \(!isUserLoggedIn\(\)\) \{[\s\S]*?shouldOpenModalAfterLogin = true;[\s\S]*?\}[\s\S]*?openCommentModal\(\);[\s\S]*?\}\);[\s\S]*?\} else \{[\s\S]*?console\.error\([\'"]Comment trigger box not found![\'"]\);[\s\S]*?\})'
        
        # If pattern not found, add proper event listener
        if not re.search(pattern, html_content):
            # Find attachEventListeners function and ensure it's correct
            attach_pattern = r'(function attachEventListeners\(\) \{[\s\S]*?const triggerBox = document\.getElementById\([\'"]commentTriggerBox[\'"]\);[\s\S]*?const modal = document\.getElementById\([\'"]commentModal[\'"]\);[\s\S]*?const closeBtn = document\.getElementById\([\'"]commentModalClose[\'"]\);[\s\S]*?const submitBtn = document\.getElementById\([\'"]commentSubmitBtn[\'"]\);[\s\S]*?const commentText = document\.getElementById\([\'"]commentText[\'"]\);[\s\S]*?if \(triggerBox\) \{[\s\S]*?triggerBox\.addEventListener\([\'"]click[\'"], function\(e\) \{[\s\S]*?e\.preventDefault\(\);[\s\S]*?e\.stopPropagation\(\);[\s\S]*?console\.log\([\'"]Comment trigger clicked[\'"]\);[\s\S]*?if \(!isUserLoggedIn\(\)\) \{[\s\S]*?shouldOpenModalAfterLogin = true;[\s\S]*?\}[\s\S]*?openCommentModal\(\);[\s\S]*?\}\);[\s\S]*?\} else \{[\s\S]*?console\.error\([\'"]Comment trigger box not found![\'"]\);[\s\S]*?\})'
            
            if not re.search(attach_pattern, html_content):
                # Add improved event listener
                improved_listener = '''
            function attachEventListeners() {
                const triggerBox = document.getElementById('commentTriggerBox');
                const modal = document.getElementById('commentModal');
                const closeBtn = document.getElementById('commentModalClose');
                const submitBtn = document.getElementById('commentSubmitBtn');
                const commentText = document.getElementById('commentText');

                if (triggerBox) {
                    // Remove any existing listeners
                    const newTriggerBox = triggerBox.cloneNode(true);
                    triggerBox.parentNode.replaceChild(newTriggerBox, triggerBox);
                    
                    newTriggerBox.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Comment trigger clicked');
                        if (!isUserLoggedIn()) {
                            shouldOpenModalAfterLogin = true;
                        }
                        openCommentModal();
                    });
                } else {
                    console.error('Comment trigger box not found!');
                }

                if (closeBtn) {
                    closeBtn.addEventListener('click', closeCommentModal);
                }

                if (modal) {
                    modal.addEventListener('click', function(e) {
                        if (e.target === modal) {
                            closeCommentModal();
                        }
                    });
                }

                if (submitBtn) {
                    submitBtn.addEventListener('click', submitComment);
                }

                if (commentText) {
                    commentText.addEventListener('keydown', function(e) {
                        if (e.ctrlKey && e.key === 'Enter') {
                            submitComment();
                        }
                    });
                }

                // Close on Escape key
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'Escape') {
                        const modal = document.getElementById('commentModal');
                        if (modal && modal.classList.contains('active')) {
                            closeCommentModal();
                        }
                    }
                });
            }
'''
                # Replace existing attachEventListeners
                html_content = re.sub(
                    r'function attachEventListeners\(\) \{[\s\S]*?\n            \}',
                    improved_listener.strip(),
                    html_content
                )
    
    # 3. Ensure initializeCommentSystem is called properly
    init_pattern = r'function initializeCommentSystem\(\) \{[\s\S]*?attachEventListeners\(\);[\s\S]*?checkUserLogin\(\);'
    if not re.search(init_pattern, html_content):
        # Add proper initialization
        init_code = '''
            function initializeCommentSystem() {
                attachEventListeners();
                checkUserLogin();

                // Check if we need to open modal after returning from login
                const shouldOpenModal = sessionStorage.getItem('openCommentModalAfterLogin');
                if (shouldOpenModal === 'true') {
                    sessionStorage.removeItem('openCommentModalAfterLogin');
                    setTimeout(() => {
                        if (isUserLoggedIn()) {
                            openCommentModal();
                        } else {
                            shouldOpenModalAfterLogin = true;
                        }
                    }, 500);
                }
            }
'''
        # Find where to insert
        if '// Initialize event listeners and check login' in html_content:
            html_content = html_content.replace(
                '// Initialize event listeners and check login',
                init_code.strip() + '\n            // Initialize event listeners and check login'
            )
    
    # 4. Ensure openCommentModal function handles errors
    open_modal_pattern = r'function openCommentModal\(\) \{[\s\S]*?if \(!isUserLoggedIn\(\)\) \{[\s\S]*?const currentUrl = window\.location\.href;[\s\S]*?sessionStorage\.setItem\([\'"]openCommentModalAfterLogin[\'"], [\'"]true[\'"]\);[\s\S]*?sessionStorage\.setItem\([\'"]returnUrl[\'"], currentUrl\);[\s\S]*?window\.location\.href = [\'"]login\.html\?returnUrl=[\'"] \+ encodeURIComponent\(currentUrl\);[\s\S]*?return;[\s\S]*?\}[\s\S]*?scrollPosition = window\.pageYOffset \|\| document\.documentElement\.scrollTop;[\s\S]*?const modal = document\.getElementById\([\'"]commentModal[\'"]\);[\s\S]*?if \(modal\) \{[\s\S]*?modal\.classList\.add\([\'"]active[\'"]\);[\s\S]*?document\.body\.style\.overflow = [\'"]hidden[\'"];[\s\S]*?loadComments\(\);[\s\S]*?\}[\s\S]*?\}'
    
    if not re.search(open_modal_pattern, html_content):
        # Add improved openCommentModal
        improved_open = '''
            function openCommentModal() {
                try {
                    // Check if user is logged in before opening
                    if (!isUserLoggedIn()) {
                        const currentUrl = window.location.href;
                        sessionStorage.setItem('openCommentModalAfterLogin', 'true');
                        sessionStorage.setItem('returnUrl', currentUrl);
                        window.location.href = 'login.html?returnUrl=' + encodeURIComponent(currentUrl);
                        return;
                    }

                    scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
                    const modal = document.getElementById('commentModal');
                    if (modal) {
                        modal.classList.add('active');
                        document.body.style.overflow = 'hidden';
                        loadComments();
                    } else {
                        console.error('Comment modal not found!');
                        alert('Comment system unavailable. Please refresh the page.');
                    }
                } catch (error) {
                    console.error('Error opening comment modal:', error);
                    alert('Unable to open comments. Please refresh the page.');
                }
            }
'''
        html_content = re.sub(
            r'function openCommentModal\(\) \{[\s\S]*?\n            \}',
            improved_open.strip(),
            html_content
        )
    
    # 5. Ensure DOM ready check works
    dom_ready_pattern = r'if \(document\.readyState === [\'"]loading[\'"]\) \{[\s\S]*?document\.addEventListener\([\'"]DOMContentLoaded[\'"], initializeCommentSystem\);[\s\S]*?\} else \{[\s\S]*?initializeCommentSystem\(\);[\s\S]*?\}'
    
    if not re.search(dom_ready_pattern, html_content):
        # Add proper DOM ready check
        dom_ready_code = '''
            // Event listeners - Attach when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeCommentSystem);
            } else {
                // DOM already loaded
                initializeCommentSystem();
            }
'''
        # Find where to insert (before catch block)
        if '})().catch(error =>' in html_content:
            html_content = html_content.replace(
                '})().catch(error =>',
                dom_ready_code + '\n        })().catch(error =>'
            )
    
    return html_content

def main():
    print("🔧 Fixing blog comment systems...\n")
    
    fixed_count = 0
    for blog_file in BLOG_PAGES:
        if os.path.exists(blog_file):
            try:
                with open(blog_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Only process if it has comment system
                if 'commentTriggerBox' in content and 'commentModal' in content:
                    original_content = content
                    content = fix_comment_system(content)
                    
                    if content != original_content:
                        with open(blog_file, "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"   ✅ Fixed {blog_file}")
                        fixed_count += 1
                    else:
                        print(f"   ✓ Already OK {blog_file}")
            except Exception as e:
                print(f"   ❌ Error fixing {blog_file}: {e}")
    
    print(f"\n✅ Fixed {fixed_count} blog comment systems!")

if __name__ == "__main__":
    main()

