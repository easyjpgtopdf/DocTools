#!/usr/bin/env python3
"""
Fix comment box click issue - Ensure event listeners are properly attached
"""

import os
import re
import glob

def fix_comment_click_issue(file_path):
    """Fix comment box click issue in a blog page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if this is a blog page with comment system
        if 'openCommentModal' not in content or 'commentModal' not in content:
            print(f"[SKIP] Skipping {file_path} - no comment system found")
            return False
        
        # Check if already fixed
        if 'attachEventListeners()' in content and 'initializeCommentSystem' in content:
            print(f"[OK] Already fixed: {file_path}")
            return False
        
        # Find and fix the Firebase initialization with error handling
        old_init_pattern = r'// Import Firebase modules\s+const.*?commentsCollection = collection\(db, storageKey\);'
        
        new_init = '''// Try to initialize Firebase
            try {
                // Import Firebase modules
                const { initializeApp, getApp, getApps } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
                const {
                    getFirestore,
                    collection,
                    addDoc,
                    serverTimestamp,
                    query,
                    orderBy,
                    limit,
                    onSnapshot,
                    doc,
                    updateDoc,
                    arrayUnion
                } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
                const {
                    getAuth,
                    onAuthStateChanged
                } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");

                // Initialize Firebase
                const firebaseConfig = window.FIREBASE_CONFIG || {};
                const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
                db = getFirestore(app);
                auth = getAuth(app);
                commentsCollection = collection(db, storageKey);
                firebaseInitialized = true;
            } catch (error) {
                console.error('Firebase initialization error:', error);
                firebaseInitialized = false;
            }'''
        
        # Add firebaseInitialized variable
        if 'let firebaseInitialized = false;' not in content:
            content = re.sub(
                r'(let unsubscribeComments = null;)',
                r'\1\n            let firebaseInitialized = false;',
                content
            )
        
        # Replace Firebase initialization
        content = re.sub(
            r'// Import Firebase modules.*?commentsCollection = collection\(db, storageKey\);',
            new_init,
            content,
            flags=re.DOTALL
        )
        
        # Fix checkUserLogin to handle Firebase not initialized
        old_check_login = r'// Check if user is logged in\s+function checkUserLogin\(\) \{\s+onAuthStateChanged\(auth,'
        
        new_check_login = '''// Check if user is logged in
            function checkUserLogin() {
                if (!firebaseInitialized || !auth) {
                    // Fallback: check localStorage
                    const userSession = localStorage.getItem('userSession');
                    if (userSession) {
                        try {
                            currentUser = JSON.parse(userSession);
                        } catch (e) {
                            currentUser = null;
                        }
                    }
                    updateCommentUI();
                    return;
                }
                
                onAuthStateChanged(auth,'''
        
        content = re.sub(
            r'// Check if user is logged in\s+function checkUserLogin\(\) \{\s+onAuthStateChanged\(auth,',
            new_check_login,
            content,
            flags=re.DOTALL
        )
        
        # Fix loadComments to handle Firebase not initialized
        if 'if (!firebaseInitialized || !commentsCollection)' not in content:
            content = re.sub(
                r'(function loadComments\(\) \{\s+const commentList = document\.getElementById\(\'commentList\'\);\s+if \(!commentList\) return;)',
                r'''\1

                if (!firebaseInitialized || !commentsCollection) {
                    commentList.innerHTML = '<li class="empty-comments">Comments unavailable. Please refresh the page.</li>';
                    return;
                }

                // Unsubscribe from previous listener
                if (unsubscribeComments) {
                    unsubscribeComments();
                }

                try {''',
                content,
                flags=re.DOTALL
            )
            
            # Close the try block
            content = re.sub(
                r'(}, \(error\) => \{\s+console\.error\(\'Error loading comments:\', error\);\s+commentList\.innerHTML = \'<li class="empty-comments">Error loading comments\. Please refresh the page\.</li>\';\s+\}\);)\s+\}',
                r'''\1
                } catch (error) {
                    console.error('Error setting up comment listener:', error);
                    commentList.innerHTML = '<li class="empty-comments">Error loading comments. Please refresh the page.</li>';
                }
            }''',
                content,
                flags=re.DOTALL
            )
        
        # Fix submitComment and submitReply to check Firebase
        if 'if (!firebaseInitialized || !commentsCollection)' not in content or 'if (!firebaseInitialized || !db)' not in content:
            # Fix submitComment
            content = re.sub(
                r'(async function submitComment\(\) \{\s+if \(!currentUser\) \{\s+alert\(\'Please sign in to comment\'\);\s+return;\s+\})',
                r'''\1

                if (!firebaseInitialized || !commentsCollection) {
                    alert('Comments unavailable. Please refresh the page.');
                    return;
                }''',
                content
            )
            
            # Fix submitReply
            content = re.sub(
                r'(async function submitReply\(commentId\) \{\s+if \(!currentUser\) \{\s+alert\(\'Please sign in to reply\'\);\s+return;\s+\})',
                r'''\1

                if (!firebaseInitialized || !db) {
                    alert('Comments unavailable. Please refresh the page.');
                    return;
                }''',
                content
            )
        
        # Fix event listeners - find the pattern and replace
        old_event_listeners = r'// Event listeners\s+document\.addEventListener\(\'DOMContentLoaded\', function\(\) \{\s+checkUserLogin\(\);'
        
        # Check if attachEventListeners function exists
        if 'function attachEventListeners()' not in content:
            # Add attachEventListeners function before event listeners
            attach_function = '''            // Event listeners - Attach immediately, don't wait for Firebase
            function attachEventListeners() {
                const triggerBox = document.getElementById('commentTriggerBox');
                const modal = document.getElementById('commentModal');
                const closeBtn = document.getElementById('commentModalClose');
                const submitBtn = document.getElementById('commentSubmitBtn');
                const commentText = document.getElementById('commentText');

                if (triggerBox) {
                    triggerBox.addEventListener('click', function(e) {
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

            // Initialize event listeners and check login
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

            // Event listeners - Attach when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeCommentSystem);
            } else {
                // DOM already loaded
                initializeCommentSystem();
            }'''
            
            # Replace the old event listener code
            content = re.sub(
                r'// Event listeners.*?checkUserLogin\(\);.*?\);\s+\)\}',
                attach_function,
                content,
                flags=re.DOTALL
            )
        
        # Add error handling catch block
        if '})().catch(error =>' not in content:
            content = re.sub(
                r'(\}\);)\s+</script>',
                r'''\1.catch(error => {
            console.error('Comment system initialization error:', error);
            // Still attach event listeners even if Firebase fails
            function attachEventListenersFallback() {
                const triggerBox = document.getElementById('commentTriggerBox');
                if (triggerBox) {
                    triggerBox.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Comment trigger clicked (fallback)');
                        alert('Please refresh the page to enable comments.');
                    });
                }
            }
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', attachEventListenersFallback);
            } else {
                attachEventListenersFallback();
            }
        });
    </script>''',
                content,
                flags=re.DOTALL
            )
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[FIXED] Fixed: {file_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error fixing {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    blog_files = glob.glob('blog-*.html')
    
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in sorted(blog_files):
        # Skip listing pages
        if 'blog-articles.html' in file_path or 'blog-tutorials.html' in file_path:
            continue
        
        result = fix_comment_click_issue(file_path)
        if result:
            fixed_count += 1
        elif result is False:
            if 'Already fixed' in str(result) or 'Skipping' in str(result):
                skipped_count += 1
            else:
                error_count += 1
    
    print(f"\n[SUMMARY]")
    print(f"[OK] Fixed: {fixed_count}")
    print(f"[SKIP] Skipped: {skipped_count}")
    print(f"[ERROR] Errors: {error_count}")

if __name__ == '__main__':
    main()

