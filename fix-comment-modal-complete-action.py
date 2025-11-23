#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Fix for Comment Modal Action
- Fix syntax errors in blog pages
- Ensure modal opens after login
- Fix login.html to handle comment modal
- Ensure comment box works after login
- Fix modal close functionality
"""

import os
import re
import glob

BLOG_PAGES = glob.glob("blog-*.html")

def fix_blog_comment_modal(html_content):
    """Fix comment modal issues in blog pages"""
    
    fixes = []
    
    # 1. Fix syntax error - duplicate else statements
    if '} else {\n                // DOM already loaded\n                initializeCommentSystem(); else {' in html_content:
        html_content = re.sub(
            r'\} else \{\s*// DOM already loaded\s*initializeCommentSystem\(\); else \{\s*// DOM already loaded\s*initializeCommentSystem\(\);',
            '} else {\n                // DOM already loaded\n                initializeCommentSystem();',
            html_content
        )
        fixes.append("Fixed duplicate else statement")
    
    # 2. Ensure modal opens immediately after page load if flag is set
    init_pattern = r'(function initializeCommentSystem\(\) \{[\s\S]*?checkUserLogin\(\);[\s\S]*?// Check if we need to open modal after returning from login[\s\S]*?const shouldOpenModal = sessionStorage\.getItem\([\'"]openCommentModalAfterLogin[\'"]\);[\s\S]*?if \(shouldOpenModal === [\'"]true[\'"]\) \{[\s\S]*?sessionStorage\.removeItem\([\'"]openCommentModalAfterLogin[\'"]\);[\s\S]*?setTimeout\(\(\) => \{[\s\S]*?if \(isUserLoggedIn\(\)\) \{[\s\S]*?openCommentModal\(\);[\s\S]*?\} else \{[\s\S]*?shouldOpenModalAfterLogin = true;[\s\S]*?\}[\s\S]*?\}, 500\);[\s\S]*?\}[\s\S]*?\})'
    
    if not re.search(init_pattern, html_content):
        # Add improved initialization
        improved_init = '''
            function initializeCommentSystem() {
                attachEventListeners();
                checkUserLogin();

                // Check if we need to open modal after returning from login
                const shouldOpenModal = sessionStorage.getItem('openCommentModalAfterLogin');
                if (shouldOpenModal === 'true') {
                    sessionStorage.removeItem('openCommentModalAfterLogin');
                    // Wait a bit for auth state to update
                    setTimeout(() => {
                        // Check login status again
                        const userSession = localStorage.getItem('userSession');
                        if (userSession) {
                            try {
                                const user = JSON.parse(userSession);
                                if (user && user.uid) {
                                    currentUser = user;
                                    openCommentModal();
                                }
                            } catch (e) {
                                console.error('Error parsing user session:', e);
                            }
                        }
                        // Also check Firebase auth
                        if (typeof isUserLoggedIn === 'function' && isUserLoggedIn()) {
                            openCommentModal();
                        }
                    }, 800);
                }
            }
'''
        # Replace existing function
        html_content = re.sub(
            r'function initializeCommentSystem\(\) \{[\s\S]*?checkUserLogin\(\);[\s\S]*?// Check if we need to open modal after returning from login[\s\S]*?\}',
            improved_init.strip(),
            html_content
        )
        fixes.append("Improved modal auto-open after login")
    
    # 3. Ensure openCommentModal works even if user just logged in
    open_modal_pattern = r'function openCommentModal\(\) \{[\s\S]*?// Check if user is logged in before opening[\s\S]*?if \(!isUserLoggedIn\(\)\) \{'
    
    if re.search(open_modal_pattern, html_content):
        # Improve openCommentModal to check multiple sources
        improved_open = '''
            function openCommentModal() {
                // Check login status from multiple sources
                let isLoggedIn = false;
                
                // Check Firebase auth
                if (typeof isUserLoggedIn === 'function') {
                    isLoggedIn = isUserLoggedIn();
                }
                
                // Also check localStorage
                if (!isLoggedIn) {
                    const userSession = localStorage.getItem('userSession');
                    if (userSession) {
                        try {
                            const user = JSON.parse(userSession);
                            if (user && user.uid) {
                                isLoggedIn = true;
                                currentUser = user;
                            }
                        } catch (e) {
                            console.error('Error parsing user session:', e);
                        }
                    }
                }
                
                // If not logged in, redirect to login
                if (!isLoggedIn) {
                    const currentUrl = window.location.href;
                    sessionStorage.setItem('openCommentModalAfterLogin', 'true');
                    sessionStorage.setItem('returnUrl', currentUrl);
                    window.location.href = 'login.html?returnUrl=' + encodeURIComponent(currentUrl);
                    return;
                }

                // User is logged in, open modal
                scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
                const modal = document.getElementById('commentModal');
                if (modal) {
                    modal.classList.add('active');
                    document.body.style.overflow = 'hidden';
                    loadComments();
                } else {
                    console.error('Comment modal not found!');
                }
            }
'''
        html_content = re.sub(
            r'function openCommentModal\(\) \{[\s\S]*?if \(!isUserLoggedIn\(\)\) \{[\s\S]*?window\.location\.href = [\'"]login\.html\?returnUrl=[\'"] \+ encodeURIComponent\(currentUrl\);[\s\S]*?return;[\s\S]*?\}[\s\S]*?scrollPosition = window\.pageYOffset \|\| document\.documentElement\.scrollTop;[\s\S]*?const modal = document\.getElementById\([\'"]commentModal[\'"]\);[\s\S]*?if \(modal\) \{[\s\S]*?modal\.classList\.add\([\'"]active[\'"]\);[\s\S]*?document\.body\.style\.overflow = [\'"]hidden[\'"];[\s\S]*?loadComments\(\);[\s\S]*?\}[\s\S]*?\}',
            improved_open.strip(),
            html_content
        )
        fixes.append("Improved login check in openCommentModal")
    
    # 4. Ensure closeCommentModal restores scroll position
    close_pattern = r'function closeCommentModal\(\) \{[\s\S]*?const modal = document\.getElementById\([\'"]commentModal[\'"]\);[\s\S]*?if \(modal\) \{[\s\S]*?modal\.classList\.remove\([\'"]active[\'"]\);[\s\S]*?document\.body\.style\.overflow = [\'"]\'\';[\s\S]*?window\.scrollTo\(0, scrollPosition\);[\s\S]*?\}[\s\S]*?\}'
    
    if not re.search(close_pattern, html_content):
        improved_close = '''
            function closeCommentModal() {
                const modal = document.getElementById('commentModal');
                if (modal) {
                    modal.classList.remove('active');
                    document.body.style.overflow = '';
                    // Restore scroll position
                    if (typeof scrollPosition !== 'undefined') {
                        window.scrollTo(0, scrollPosition);
                    }
                }
            }
'''
        html_content = re.sub(
            r'function closeCommentModal\(\) \{[\s\S]*?\}',
            improved_close.strip(),
            html_content
        )
        fixes.append("Improved closeCommentModal")
    
    # 5. Ensure scrollPosition is defined
    if 'let scrollPosition' not in html_content and 'var scrollPosition' not in html_content:
        # Add scrollPosition variable
        if '// Modal functions' in html_content:
            html_content = html_content.replace(
                '// Modal functions',
                '// Modal functions\n            let scrollPosition = 0;'
            )
            fixes.append("Added scrollPosition variable")
    
    return html_content, fixes

def fix_login_redirect(html_content):
    """Fix login.html to handle comment modal opening"""
    
    fixes = []
    
    # Check if login.html handles openCommentModalAfterLogin
    if 'openCommentModalAfterLogin' not in html_content:
        # Add handling for comment modal
        # Find where returnUrl is handled
        pattern = r'(if \(storedReturnUrl\) \{[\s\S]*?sessionStorage\.removeItem\([\'"]returnUrl[\'"]\);[\s\S]*?window\.location\.href = storedReturnUrl;)'
        
        replacement = r'''if (storedReturnUrl) {
                    sessionStorage.removeItem('returnUrl');
                    // Check if we need to open comment modal
                    const shouldOpenCommentModal = sessionStorage.getItem('openCommentModalAfterLogin');
                    if (shouldOpenCommentModal === 'true') {
                        // Keep the flag, will be handled by the blog page
                        // Just redirect
                    }
                    window.location.href = storedReturnUrl;'''
        
        html_content = re.sub(pattern, replacement, html_content)
        fixes.append("Added comment modal handling in login redirect")
    
    return html_content, fixes

def main():
    print("🔧 Fixing complete comment modal action...\n")
    
    # Fix blog pages
    blog_fixed = 0
    for blog_file in BLOG_PAGES:
        if os.path.exists(blog_file):
            try:
                with open(blog_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if 'commentTriggerBox' in content:
                    original = content
                    content, fixes = fix_blog_comment_modal(content)
                    
                    if content != original or fixes:
                        with open(blog_file, "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"   ✅ Fixed {blog_file}")
                        for fix in fixes:
                            print(f"      - {fix}")
                        blog_fixed += 1
            except Exception as e:
                print(f"   ❌ Error fixing {blog_file}: {e}")
    
    # Fix login.html
    if os.path.exists("login.html"):
        try:
            with open("login.html", "r", encoding="utf-8") as f:
                content = f.read()
            
            original = content
            content, fixes = fix_login_redirect(content)
            
            if content != original or fixes:
                with open("login.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"\n   ✅ Fixed login.html")
                for fix in fixes:
                    print(f"      - {fix}")
        except Exception as e:
            print(f"   ❌ Error fixing login.html: {e}")
    
    print(f"\n✅ Fixed {blog_fixed} blog pages and login.html!")
    print("\n📝 How it works now:")
    print("   1. User clicks comment box → Redirects to login if not logged in")
    print("   2. User logs in → Returns to blog page")
    print("   3. Modal opens automatically → User can comment/reply")
    print("   4. Click X or outside → Modal closes, stays on same page")
    print("   5. Click comment box again → Modal opens immediately")

if __name__ == "__main__":
    main()

