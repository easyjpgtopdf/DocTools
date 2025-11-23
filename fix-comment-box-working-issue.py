#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Blog Comment Box Not Working Issue
- Ensure event listeners attach immediately
- Fix timing issues
- Add better error handling
- Ensure modal opens correctly
"""

import os
import re
import glob

BLOG_PAGES = glob.glob("blog-*.html")

def fix_comment_box_issue(html_content):
    """Fix comment box not working"""
    
    issues_found = []
    fixes_applied = []
    
    # 1. Check if comment trigger box exists in HTML
    if 'id="commentTriggerBox"' not in html_content:
        issues_found.append("Comment trigger box missing")
        return html_content, issues_found
    
    # 2. Ensure event listener attaches immediately, not waiting for Firebase
    # Find the initialization code and ensure it runs immediately
    if 'initializeCommentSystem' in html_content:
        # Check if it's called on DOM ready
        if 'document.addEventListener(\'DOMContentLoaded\', initializeCommentSystem)' in html_content:
            # Good, but also add immediate call if DOM already loaded
            if 'else {\n                initializeCommentSystem();' not in html_content:
                # Add immediate initialization
                pattern = r'(if \(document\.readyState === [\'"]loading[\'"]\) \{[\s\S]*?document\.addEventListener\([\'"]DOMContentLoaded[\'"], initializeCommentSystem\);[\s\S]*?\})'
                replacement = r'\1\n            } else {\n                // DOM already loaded\n                initializeCommentSystem();'
                html_content = re.sub(pattern, replacement, html_content)
                fixes_applied.append("Added immediate initialization for already-loaded DOM")
    
    # 3. Ensure attachEventListeners is called even if Firebase fails
    # Check if there's a fallback
    if 'attachEventListenersFallback' in html_content:
        # Good, but ensure it's also called in main flow
        pass
    else:
        # Add fallback that always attaches listeners
        fallback_code = '''
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
                        
                        // Check login status
                        const userSession = localStorage.getItem('userSession');
                        const isLoggedIn = userSession !== null;
                        
                        if (!isLoggedIn) {
                            const currentUrl = window.location.href;
                            sessionStorage.setItem('openCommentModalAfterLogin', 'true');
                            sessionStorage.setItem('returnUrl', currentUrl);
                            window.location.href = 'login.html?returnUrl=' + encodeURIComponent(currentUrl);
                            return;
                        }
                        
                        // Open modal
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
                    closeBtn.addEventListener('click', function() {
                        const modal = document.getElementById('commentModal');
                        if (modal) {
                            modal.classList.remove('active');
                            document.body.style.overflow = '';
                        }
                    });
                }
                
                // Close on outside click
                const modal = document.getElementById('commentModal');
                if (modal) {
                    modal.addEventListener('click', function(e) {
                        if (e.target === modal) {
                            modal.classList.remove('active');
                            document.body.style.overflow = '';
                        }
                    });
                }
            }
            
            // Attach listeners immediately
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', attachEventListenersAlways);
            } else {
                attachEventListenersAlways();
            }
'''
        
        # Insert before closing script tag
        if '</script>' in html_content and 'Comment System Script' in html_content:
            # Find the script section and add fallback
            script_end = html_content.rfind('</script>', 0, html_content.find('</body>'))
            if script_end > 0:
                html_content = html_content[:script_end] + fallback_code + '\n    ' + html_content[script_end:]
                fixes_applied.append("Added immediate event listener attachment")
    
    # 4. Ensure modal CSS is correct (check if active class works)
    if '.comment-modal.active' not in html_content:
        issues_found.append("Modal active class CSS might be missing")
    
    # 5. Add console logging for debugging
    if 'console.log(\'Comment trigger clicked\')' not in html_content:
        # Add logging to openCommentModal
        pattern = r'(function openCommentModal\(\) \{[\s\S]*?if \(!isUserLoggedIn\(\)\) \{)'
        replacement = r'\1\n                console.log(\'Opening comment modal - user not logged in\');'
        html_content = re.sub(pattern, replacement, html_content)
        
        pattern = r'(scrollPosition = window\.pageYOffset)'
        replacement = r'console.log(\'Opening comment modal\');\n                \1'
        html_content = re.sub(pattern, replacement, html_content)
        fixes_applied.append("Added debug logging")
    
    return html_content, issues_found, fixes_applied

def main():
    print("🔧 Fixing blog comment box issues...\n")
    
    fixed_count = 0
    for blog_file in BLOG_PAGES:
        if os.path.exists(blog_file):
            try:
                with open(blog_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Only process if it has comment system
                if 'commentTriggerBox' in content and 'commentModal' in content:
                    original_content = content
                    content, issues, fixes = fix_comment_box_issue(content)
                    
                    if content != original_content or fixes:
                        with open(blog_file, "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"   ✅ Fixed {blog_file}")
                        if fixes:
                            for fix in fixes:
                                print(f"      - {fix}")
                        if issues:
                            for issue in issues:
                                print(f"      ⚠️  {issue}")
                        fixed_count += 1
                    else:
                        print(f"   ✓ {blog_file} - No changes needed")
            except Exception as e:
                print(f"   ❌ Error fixing {blog_file}: {e}")
    
    print(f"\n✅ Fixed {fixed_count} blog comment systems!")
    print("\n📝 Testing Instructions:")
    print("   1. Open any blog page")
    print("   2. Click on 'Add a comment...' box")
    print("   3. If not logged in, should redirect to login")
    print("   4. After login, modal should open automatically")
    print("   5. Check browser console for any errors")

if __name__ == "__main__":
    main()

