#!/usr/bin/env python3
"""
Fix comment login issue in all blog pages
- Check login before opening modal
- Auto-open modal after login
"""

import os
import re
import glob

def fix_comment_system(file_path):
    """Fix comment system in a blog page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if this is a blog page with comment system
        if 'openCommentModal' not in content or 'commentModal' not in content:
            print(f"⏭️  Skipping {file_path} - no comment system found")
            return False
        
        # Check if already fixed
        if 'shouldOpenModalAfterLogin' in content:
            print(f"✅ Already fixed: {file_path}")
            return False
        
        # Find the checkUserLogin function and replace it
        old_check_user = r'// Check if user is logged in\s+function checkUserLogin\(\) \{[^}]+\}'
        
        new_check_user = '''// Flag to track if we should open modal after login
            let shouldOpenModalAfterLogin = false;

            // Check if user is logged in
            function checkUserLogin() {
                // Check Firebase auth if available
                if (typeof firebase !== 'undefined' && firebase.auth) {
                    firebase.auth().onAuthStateChanged((user) => {
                        const wasLoggedOut = !currentUser && user;
                        currentUser = user;
                        updateCommentUI();
                        
                        // If user just logged in and we need to open modal
                        if (wasLoggedOut && shouldOpenModalAfterLogin) {
                            shouldOpenModalAfterLogin = false;
                            // Small delay to ensure UI is updated
                            setTimeout(() => {
                                openCommentModal();
                            }, 300);
                        }
                    });
                } else {
                    // Fallback: check localStorage for user session
                    const userSession = localStorage.getItem('userSession');
                    if (userSession) {
                        try {
                            currentUser = JSON.parse(userSession);
                        } catch (e) {
                            currentUser = null;
                        }
                    }
                    updateCommentUI();
                }
            }'''
        
        # Replace checkUserLogin function
        content = re.sub(
            r'// Check if user is logged in\s+function checkUserLogin\(\) \{.*?\n            \}',
            new_check_user,
            content,
            flags=re.DOTALL
        )
        
        # Find and replace openCommentModal function
        old_open_modal = r'// Modal functions\s+function openCommentModal\(\) \{.*?\n            \}'
        
        new_open_modal = '''// Check if user is currently logged in (synchronous check)
            function isUserLoggedIn() {
                if (typeof firebase !== 'undefined' && firebase.auth && firebase.auth().currentUser) {
                    return true;
                }
                // Fallback check
                const userSession = localStorage.getItem('userSession');
                return userSession !== null;
            }

            // Modal functions
            function openCommentModal() {
                // Check if user is logged in before opening
                if (!isUserLoggedIn()) {
                    // User not logged in - redirect to login with return URL
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
                }
            }'''
        
        content = re.sub(
            r'// Modal functions\s+function openCommentModal\(\) \{.*?\n            \}',
            new_open_modal,
            content,
            flags=re.DOTALL
        )
        
        # Find and replace the event listener for triggerBox
        old_listener = r'if \(triggerBox\) \{\s+triggerBox\.addEventListener\(\'click\', openCommentModal\);\s+\}'
        
        new_listener = '''if (triggerBox) {
                    triggerBox.addEventListener('click', function() {
                        if (!isUserLoggedIn()) {
                            shouldOpenModalAfterLogin = true;
                        }
                        openCommentModal();
                    });
                }'''
        
        content = re.sub(
            r'if \(triggerBox\) \{\s+triggerBox\.addEventListener\(\'click\', openCommentModal\);\s+\}',
            new_listener,
            content
        )
        
        # Add check for returning from login
        old_dom_ready = r'document\.addEventListener\(\'DOMContentLoaded\', function\(\) \{\s+checkUserLogin\(\);'
        
        new_dom_ready = '''document.addEventListener('DOMContentLoaded', function() {
                checkUserLogin();

                // Check if we need to open modal after returning from login
                const shouldOpenModal = sessionStorage.getItem('openCommentModalAfterLogin');
                if (shouldOpenModal === 'true') {
                    sessionStorage.removeItem('openCommentModalAfterLogin');
                    // Wait a bit for auth state to update
                    setTimeout(() => {
                        if (isUserLoggedIn()) {
                            openCommentModal();
                        } else {
                            // Still not logged in, set flag to open after login
                            shouldOpenModalAfterLogin = true;
                        }
                    }, 500);
                }'''
        
        content = re.sub(
            r'document\.addEventListener\(\'DOMContentLoaded\', function\(\) \{\s+checkUserLogin\(\);',
            new_dom_ready,
            content
        )
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main function"""
    blog_files = glob.glob('blog-*.html')
    
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in sorted(blog_files):
        # Skip blog-articles.html and blog-tutorials.html (listing pages)
        if 'blog-articles.html' in file_path or 'blog-tutorials.html' in file_path:
            continue
        
        result = fix_comment_system(file_path)
        if result:
            fixed_count += 1
        elif result is False and 'Already fixed' in str(result):
            skipped_count += 1
        else:
            error_count += 1
    
    print(f"\n📊 Summary:")
    print(f"✅ Fixed: {fixed_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")

if __name__ == '__main__':
    main()

