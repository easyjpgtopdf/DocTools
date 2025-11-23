#!/usr/bin/env python3
"""
Fix blog comment system to use Firebase Firestore
- Replace localStorage with Firestore
- Add proper Firebase imports
- Each page gets its own Firestore collection
- Fix login check and comment submission
"""

import os
import re
import glob

def get_page_id_from_filename(filename):
    """Extract page ID from filename"""
    # blog-how-to-use-jpg-to-pdf.html -> blog-jpg-to-pdf
    # blog-why-user-pdf-to-word.html -> blog-pdf-to-word
    name = os.path.basename(filename).replace('.html', '')
    # Remove 'blog-' prefix and 'how-to-' or 'why-user-' parts
    name = name.replace('blog-how-to-', 'blog-')
    name = name.replace('blog-why-user-', 'blog-')
    return name

def fix_blog_comment_system(file_path):
    """Fix comment system in a blog page to use Firebase"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if this is a blog page with comment system
        if 'openCommentModal' not in content or 'commentModal' not in content:
            print(f"⏭️  Skipping {file_path} - no comment system found")
            return False
        
        # Check if already fixed with Firebase
        if 'getFirestore' in content and 'blog-comments' in content:
            print(f"✅ Already fixed with Firebase: {file_path}")
            return False
        
        page_id = get_page_id_from_filename(file_path)
        collection_name = f'blog-comments-{page_id}'
        
        # Find the comment system script section
        # Replace the entire comment system script
        old_script_pattern = r'<!-- Comment System Script -->\s*<script>\s*\(function\(\) \{.*?\}\)\(\);\s*</script>'
        
        new_script = f'''<!-- Comment System Script -->
    <script>
        // Firebase configuration
        window.FIREBASE_CONFIG = window.FIREBASE_CONFIG || {{
            apiKey: "AIzaSyBch3tJoeFqio3IA4MbPoh2GHZE2qKVzGc",
            authDomain: "easyjpgtopdf-de346.firebaseapp.com",
            projectId: "easyjpgtopdf-de346",
            storageBucket: "easyjpgtopdf-de346.appspot.com",
            messagingSenderId: "564572183797",
            appId: "1:564572183797:web:9c204df018c150f02f79bc"
        }};
    </script>
    
    <script type="module">
        (async function() {{
            const storageKey = '{collection_name}';
            let scrollPosition = 0;
            let currentUser = null;
            let activeReplyTarget = null;
            let db = null;
            let commentsCollection = null;
            let unsubscribeComments = null;

            // Import Firebase modules
            const {{ initializeApp, getApp, getApps }} = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
            const {{
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
            }} = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
            const {{
                getAuth,
                onAuthStateChanged
            }} = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");

            // Initialize Firebase
            const firebaseConfig = window.FIREBASE_CONFIG || {{}};
            const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
            db = getFirestore(app);
            const auth = getAuth(app);
            commentsCollection = collection(db, storageKey);

            // Flag to track if we should open modal after login
            let shouldOpenModalAfterLogin = false;

            // Check if user is logged in
            function checkUserLogin() {{
                onAuthStateChanged(auth, (user) => {{
                    const wasLoggedOut = !currentUser && user;
                    currentUser = user;
                    updateCommentUI();
                    
                    // If user just logged in and we need to open modal
                    if (wasLoggedOut && shouldOpenModalAfterLogin) {{
                        shouldOpenModalAfterLogin = false;
                        setTimeout(() => {{
                            openCommentModal();
                        }}, 300);
                    }}
                }});
            }}

            function updateCommentUI() {{
                const commentInputBox = document.getElementById('commentInputBox');
                const loginPrompt = document.getElementById('loginPrompt');
                
                if (currentUser) {{
                    if (commentInputBox) commentInputBox.style.display = 'block';
                    if (loginPrompt) loginPrompt.style.display = 'none';
                }} else {{
                    if (commentInputBox) commentInputBox.style.display = 'none';
                    if (loginPrompt) loginPrompt.style.display = 'block';
                }}
            }}

            // Check if user is currently logged in (synchronous check)
            function isUserLoggedIn() {{
                return currentUser !== null;
            }}

            // Modal functions
            function openCommentModal() {{
                // Check if user is logged in before opening
                if (!isUserLoggedIn()) {{
                    const currentUrl = window.location.href;
                    sessionStorage.setItem('openCommentModalAfterLogin', 'true');
                    sessionStorage.setItem('returnUrl', currentUrl);
                    window.location.href = 'login.html?returnUrl=' + encodeURIComponent(currentUrl);
                    return;
                }}

                scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
                const modal = document.getElementById('commentModal');
                if (modal) {{
                    modal.classList.add('active');
                    document.body.style.overflow = 'hidden';
                    loadComments();
                }}
            }}

            function closeCommentModal() {{
                const modal = document.getElementById('commentModal');
                if (modal) {{
                    modal.classList.remove('active');
                    document.body.style.overflow = '';
                    window.scrollTo(0, scrollPosition);
                }}
            }}

            // Load comments from Firestore
            function loadComments() {{
                const commentList = document.getElementById('commentList');
                if (!commentList) return;

                // Unsubscribe from previous listener
                if (unsubscribeComments) {{
                    unsubscribeComments();
                }}

                // Set up real-time listener
                const commentsQuery = query(commentsCollection, orderBy('createdAt', 'desc'), limit(50));
                
                unsubscribeComments = onSnapshot(commentsQuery, (snapshot) => {{
                    const comments = [];
                    snapshot.forEach((doc) => {{
                        const data = doc.data();
                        comments.push({{
                            id: doc.id,
                            author: data.author || data.name || 'Anonymous User',
                            text: data.text || data.comment || '',
                            timestamp: data.createdAt?.toMillis() || data.timestamp || Date.now(),
                            createdAt: data.createdAt?.toMillis() || data.createdAt || Date.now(),
                            replies: data.replies || []
                        }});
                    }});

                    if (comments.length === 0) {{
                        commentList.innerHTML = '<li class="empty-comments">No comments yet. Be the first to comment!</li>';
                        return;
                    }}

                    commentList.innerHTML = '';
                    comments.forEach(comment => {{
                        const li = createCommentElement(comment);
                        commentList.appendChild(li);
                    }});
                }}, (error) => {{
                    console.error('Error loading comments:', error);
                    commentList.innerHTML = '<li class="empty-comments">Error loading comments. Please refresh the page.</li>';
                }});
            }}

            function createCommentElement(comment) {{
                const li = document.createElement('li');
                li.className = 'comment-item';
                li.dataset.commentId = comment.id;

                const author = document.createElement('div');
                author.className = 'comment-author';
                author.textContent = comment.author || comment.name || 'Anonymous User';

                const text = document.createElement('div');
                text.className = 'comment-text';
                text.textContent = comment.text || comment.comment;

                const meta = document.createElement('div');
                meta.className = 'comment-meta';
                const time = document.createElement('span');
                time.textContent = formatTime(comment.createdAt || comment.timestamp);
                meta.appendChild(time);

                const replyBtn = document.createElement('button');
                replyBtn.className = 'comment-reply-btn';
                replyBtn.innerHTML = '<i class="fas fa-reply"></i> Reply';
                replyBtn.onclick = () => toggleReplyInput(comment.id);
                meta.appendChild(replyBtn);

                li.appendChild(author);
                li.appendChild(text);
                li.appendChild(meta);

                // Add replies if any
                if (comment.replies && comment.replies.length > 0) {{
                    const repliesDiv = document.createElement('div');
                    repliesDiv.className = 'comment-replies';
                    comment.replies.forEach(reply => {{
                        const replyDiv = document.createElement('div');
                        replyDiv.className = 'reply-item';
                        const replyAuthor = document.createElement('div');
                        replyAuthor.className = 'reply-author';
                        replyAuthor.textContent = reply.author || reply.name || 'User';
                        const replyText = document.createElement('div');
                        replyText.className = 'reply-text';
                        replyText.textContent = reply.text || reply.comment;
                        const replyMeta = document.createElement('div');
                        replyMeta.className = 'reply-meta';
                        replyMeta.textContent = formatTime(reply.createdAt || reply.timestamp);
                        replyDiv.appendChild(replyAuthor);
                        replyDiv.appendChild(replyText);
                        replyDiv.appendChild(replyMeta);
                        repliesDiv.appendChild(replyDiv);
                    }});
                    li.appendChild(repliesDiv);
                }}

                // Add reply input box
                const replyInputBox = document.createElement('div');
                replyInputBox.className = 'reply-input-box';
                replyInputBox.id = `reply-input-${{comment.id}}`;
                const replyTextarea = document.createElement('textarea');
                replyTextarea.placeholder = 'Write a reply...';
                replyTextarea.id = `reply-text-${{comment.id}}`;
                const replySubmitBtn = document.createElement('button');
                replySubmitBtn.className = 'reply-submit-btn';
                replySubmitBtn.textContent = 'Reply';
                replySubmitBtn.onclick = () => submitReply(comment.id);
                replyInputBox.appendChild(replyTextarea);
                replyInputBox.appendChild(replySubmitBtn);
                li.appendChild(replyInputBox);

                return li;
            }}

            function toggleReplyInput(commentId) {{
                if (!currentUser) {{
                    alert('Please sign in to reply');
                    return;
                }}
                const replyInputBox = document.getElementById(`reply-input-${{commentId}}`);
                if (replyInputBox) {{
                    replyInputBox.classList.toggle('active');
                    if (replyInputBox.classList.contains('active')) {{
                        const textarea = document.getElementById(`reply-text-${{commentId}}`);
                        if (textarea) textarea.focus();
                    }}
                }}
            }}

            async function submitReply(commentId) {{
                if (!currentUser) {{
                    alert('Please sign in to reply');
                    return;
                }}

                const textarea = document.getElementById(`reply-text-${{commentId}}`);
                if (!textarea || !textarea.value.trim()) return;

                try {{
                    const replyData = {{
                        author: currentUser.displayName || currentUser.email || 'User',
                        text: textarea.value.trim(),
                        createdAt: serverTimestamp(),
                        timestamp: Date.now()
                    }};

                    const commentDoc = doc(db, storageKey, commentId);
                    await updateDoc(commentDoc, {{
                        replies: arrayUnion(replyData)
                    }});

                    textarea.value = '';
                    const replyInputBox = document.getElementById(`reply-input-${{commentId}}`);
                    if (replyInputBox) replyInputBox.classList.remove('active');
                }} catch (error) {{
                    console.error('Error submitting reply:', error);
                    alert('Failed to submit reply. Please try again.');
                }}
            }}

            function formatTime(timestamp) {{
                if (!timestamp) return 'Just now';
                const date = new Date(timestamp);
                const now = new Date();
                const diff = now - date;
                const minutes = Math.floor(diff / 60000);
                const hours = Math.floor(diff / 3600000);
                const days = Math.floor(diff / 86400000);

                if (minutes < 1) return 'Just now';
                if (minutes < 60) return `${{minutes}}m ago`;
                if (hours < 24) return `${{hours}}h ago`;
                if (days < 7) return `${{days}}d ago`;
                return date.toLocaleDateString();
            }}

            // Submit comment
            async function submitComment() {{
                if (!currentUser) {{
                    alert('Please sign in to comment');
                    return;
                }}

                const textarea = document.getElementById('commentText');
                if (!textarea || !textarea.value.trim()) return;

                try {{
                    const commentData = {{
                        author: currentUser.displayName || currentUser.email || 'User',
                        text: textarea.value.trim(),
                        createdAt: serverTimestamp(),
                        timestamp: Date.now(),
                        replies: []
                    }};

                    await addDoc(commentsCollection, commentData);
                    textarea.value = '';
                }} catch (error) {{
                    console.error('Error submitting comment:', error);
                    alert('Failed to submit comment. Please try again.');
                }}
            }}

            // Event listeners
            document.addEventListener('DOMContentLoaded', function() {{
                checkUserLogin();

                // Check if we need to open modal after returning from login
                const shouldOpenModal = sessionStorage.getItem('openCommentModalAfterLogin');
                if (shouldOpenModal === 'true') {{
                    sessionStorage.removeItem('openCommentModalAfterLogin');
                    setTimeout(() => {{
                        if (isUserLoggedIn()) {{
                            openCommentModal();
                        }} else {{
                            shouldOpenModalAfterLogin = true;
                        }}
                    }}, 500);
                }}

                const triggerBox = document.getElementById('commentTriggerBox');
                const modal = document.getElementById('commentModal');
                const closeBtn = document.getElementById('commentModalClose');
                const submitBtn = document.getElementById('commentSubmitBtn');
                const commentText = document.getElementById('commentText');

                if (triggerBox) {{
                    triggerBox.addEventListener('click', function() {{
                        if (!isUserLoggedIn()) {{
                            shouldOpenModalAfterLogin = true;
                        }}
                        openCommentModal();
                    }});
                }}

                if (closeBtn) {{
                    closeBtn.addEventListener('click', closeCommentModal);
                }}

                if (modal) {{
                    modal.addEventListener('click', function(e) {{
                        if (e.target === modal) {{
                            closeCommentModal();
                        }}
                    }});
                }}

                if (submitBtn) {{
                    submitBtn.addEventListener('click', submitComment);
                }}

                if (commentText) {{
                    commentText.addEventListener('keydown', function(e) {{
                        if (e.ctrlKey && e.key === 'Enter') {{
                            submitComment();
                        }}
                    }});
                }}

                // Close on Escape key
                document.addEventListener('keydown', function(e) {{
                    if (e.key === 'Escape') {{
                        const modal = document.getElementById('commentModal');
                        if (modal && modal.classList.contains('active')) {{
                            closeCommentModal();
                        }}
                    }}
                }});
            }});
        }})();
    </script>'''
        
        # Find and replace the comment system script
        if re.search(r'<!-- Comment System Script -->', content):
            # Replace the script section
            content = re.sub(
                r'<!-- Comment System Script -->.*?</script>',
                new_script,
                content,
                flags=re.DOTALL
            )
        else:
            # If pattern not found, find where to insert
            # Look for voice assistant script and add before it
            voice_pattern = r'(<!-- Voice Assistant Script -->)'
            if re.search(voice_pattern, content):
                content = re.sub(voice_pattern, new_script + r'\n    \1', content)
            else:
                # Add before closing body tag
                content = re.sub(r'(</body>)', new_script + r'\n    \1', content)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed with Firebase: {file_path} (Collection: {collection_name})")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
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
        
        result = fix_blog_comment_system(file_path)
        if result:
            fixed_count += 1
        elif result is False:
            if 'Already fixed' in str(result):
                skipped_count += 1
            else:
                error_count += 1
    
    print(f"\n📊 Summary:")
    print(f"✅ Fixed: {fixed_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")

if __name__ == '__main__':
    main()

