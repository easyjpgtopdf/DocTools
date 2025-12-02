#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Reviews & Comments section to match index.html style
Two-column layout: Comments on left, Form on right
Remove all pre-added fake comments
"""

import os
import re
from pathlib import Path

# New Feedback Section HTML (Index page style - two columns)
FEEDBACK_SECTION = '''    <section class="feedback-section" style="margin: 40px 0; padding: 40px; background: #f8f9ff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="font-size: 2rem; color: #4361ee; margin-bottom: 30px; text-align: center;">
            <i class="fas fa-comments" style="margin-right: 10px;"></i>
            Reviews & Comments
        </h2>
        
        <div class="feedback-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: flex-start; max-width: 1200px; margin: 0 auto;">
            <!-- Left Side: Comments List -->
            <div class="feedback-card" style="background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); min-height: 400px; max-height: 600px; overflow-y: auto;">
                <div class="thread-header" style="margin-bottom: 20px; border-bottom: 2px solid #e2e6ff; padding-bottom: 12px;">
                    <h3 style="font-size: 1.3rem; color: #0b1630; margin-bottom: 8px;">Live Comments</h3>
                    <p class="feedback-hint" style="font-size: 0.85rem; color: #9ca3af; margin: 0;">Share your experience and see what others are saying.</p>
                </div>
                <ul class="comment-list" id="feedbackList" style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 16px;">
                    <li class="feedback-muted" id="feedback-empty-state" style="text-align: center; padding: 40px 20px; color: #9ca3af; font-size: 0.95rem;">No comments yet. Start the conversation!</li>
                </ul>
            </div>
            
            <!-- Right Side: Feedback Form -->
            <div class="feedback-form-card" style="background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); position: sticky; top: 20px;">
                <h3 style="font-size: 1.3rem; color: #0b1630; margin-bottom: 20px;">
                    <i class="fas fa-edit" style="color: #4361ee; margin-right: 8px;"></i>
                    Share Your Feedback
                </h3>
                <form id="feedbackForm" style="display: flex; flex-direction: column; gap: 15px;">
                    <div class="form-group">
                        <label for="feedbackName" style="display: block; margin-bottom: 8px; color: #56607a; font-weight: 600; font-size: 0.9rem;">Your Name</label>
                        <input type="text" id="feedbackName" placeholder="Enter your name" required style="width: 100%; padding: 12px 16px; border: 1px solid #e2e6ff; border-radius: 8px; font-size: 0.95rem; transition: border-color 0.3s; box-sizing: border-box;" onfocus="this.style.borderColor='#4361ee'" onblur="this.style.borderColor='#e2e6ff'">
                    </div>
                    <div class="form-group">
                        <label for="feedbackMessage" style="display: block; margin-bottom: 8px; color: #56607a; font-weight: 600; font-size: 0.9rem;">Your Comment</label>
                        <textarea id="feedbackMessage" placeholder="Write your feedback or comment here..." required rows="5" style="width: 100%; padding: 12px 16px; border: 1px solid #e2e6ff; border-radius: 8px; font-size: 0.95rem; resize: vertical; transition: border-color 0.3s; font-family: inherit; box-sizing: border-box;" onfocus="this.style.borderColor='#4361ee'" onblur="this.style.borderColor='#e2e6ff'"></textarea>
                    </div>
                    <button type="submit" style="background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; width: 100%;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(67, 97, 238, 0.3)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        <i class="fas fa-paper-plane" style="margin-right: 8px;"></i>
                        Submit Feedback
                    </button>
                </form>
                <div style="text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e6ff;">
                    <a href="feedback.html" style="color: #4361ee; text-decoration: none; font-weight: 600; font-size: 0.9rem; display: inline-flex; align-items: center; gap: 8px; transition: color 0.3s;" onmouseover="this.style.color='#3a0ca3'" onmouseout="this.style.color='#4361ee'">
                        <i class="fas fa-arrow-right"></i>
                        View All Feedback
                    </a>
                </div>
            </div>
        </div>
    </section>

    <style>
    @media (max-width: 768px) {
        .feedback-grid {
            grid-template-columns: 1fr !important;
        }
        .feedback-form-card {
            position: static !important;
        }
    }
    </style>

    <script>
    // Store feedback in localStorage (in production, use backend API)
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    // Load feedbacks for this page (max 3, only genuine user comments)
    function loadFeedbacks() {
        const storedFeedbacks = JSON.parse(localStorage.getItem('feedbacks') || '{}');
        const pageFeedbacks = (storedFeedbacks[currentPage] || []).slice(0, 3);
        const feedbackList = document.getElementById('feedbackList');
        const emptyState = document.getElementById('feedback-empty-state');
        
        if (!feedbackList) return;
        
        // Clear existing content
        feedbackList.innerHTML = '';
        
        if (pageFeedbacks.length === 0) {
            // Show empty state
            if (emptyState) {
                feedbackList.appendChild(emptyState);
            } else {
                const empty = document.createElement('li');
                empty.className = 'feedback-muted';
                empty.id = 'feedback-empty-state';
                empty.style.cssText = 'text-align: center; padding: 40px 20px; color: #9ca3af; font-size: 0.95rem;';
                empty.textContent = 'No comments yet. Start the conversation!';
                feedbackList.appendChild(empty);
            }
            return;
        }
        
        // Remove empty state
        if (emptyState) {
            emptyState.remove();
        }
        
        // Display genuine user feedbacks
        pageFeedbacks.forEach(fb => {
            const li = document.createElement('li');
            li.className = 'live-comment';
            li.style.cssText = 'background: #f8f9ff; padding: 16px; border-radius: 8px; border-left: 3px solid #4361ee; margin-bottom: 12px;';
            
            const header = document.createElement('div');
            header.style.cssText = 'display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;';
            
            const nameDiv = document.createElement('div');
            const name = document.createElement('h4');
            name.style.cssText = 'font-size: 1rem; color: #0b1630; margin: 0 0 4px 0; font-weight: 600;';
            name.textContent = fb.name || 'Anonymous';
            
            const time = document.createElement('span');
            time.style.cssText = 'font-size: 0.8rem; color: #9ca3af;';
            time.textContent = fb.date || 'Recently';
            
            nameDiv.appendChild(name);
            nameDiv.appendChild(time);
            header.appendChild(nameDiv);
            
            li.appendChild(header);
            
            const body = document.createElement('p');
            body.style.cssText = 'color: #56607a; line-height: 1.6; margin: 0 0 12px 0; font-size: 0.9rem;';
            body.textContent = fb.message || '';
            li.appendChild(body);
            
            // Add reply if exists
            if (fb.reply) {
                const replyDiv = document.createElement('div');
                replyDiv.style.cssText = 'margin-left: 20px; padding: 12px; background: white; border-radius: 6px; margin-top: 10px; border-left: 2px solid #4361ee;';
                
                const replyHeader = document.createElement('div');
                replyHeader.style.cssText = 'display: flex; align-items: center; gap: 8px; margin-bottom: 6px;';
                
                const replyIcon = document.createElement('i');
                replyIcon.className = 'fas fa-reply';
                replyIcon.style.cssText = 'color: #4361ee; font-size: 0.85rem;';
                
                const replyLabel = document.createElement('strong');
                replyLabel.style.cssText = 'color: #4361ee; font-size: 0.85rem;';
                replyLabel.textContent = 'Admin Reply:';
                
                replyHeader.appendChild(replyIcon);
                replyHeader.appendChild(replyLabel);
                replyDiv.appendChild(replyHeader);
                
                const replyText = document.createElement('p');
                replyText.style.cssText = 'color: #56607a; font-size: 0.85rem; line-height: 1.5; margin: 0;';
                replyText.textContent = fb.reply;
                replyDiv.appendChild(replyText);
                
                li.appendChild(replyDiv);
            }
            
            feedbackList.appendChild(li);
        });
    }
    
    // Handle feedback form submission
    const feedbackForm = document.getElementById('feedbackForm');
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const name = document.getElementById('feedbackName').value.trim();
            const message = document.getElementById('feedbackMessage').value.trim();
            
            if (!name || !message) {
                alert('Please fill in all fields');
                return;
            }
            
            const feedback = {
                name: name,
                message: message,
                date: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }),
                page: currentPage
            };
            
            // Store in localStorage
            const storedFeedbacks = JSON.parse(localStorage.getItem('feedbacks') || '{}');
            if (!storedFeedbacks[currentPage]) {
                storedFeedbacks[currentPage] = [];
            }
            storedFeedbacks[currentPage].unshift(feedback);
            localStorage.setItem('feedbacks', JSON.stringify(storedFeedbacks));
            
            // Reset form
            this.reset();
            
            // Reload feedbacks
            loadFeedbacks();
            
            alert('Thank you for your feedback!');
        });
    }
    
    // Load feedbacks on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadFeedbacks);
    } else {
        loadFeedbacks();
    }
    </script>'''

# Pages to skip
SKIP_PAGES = [
    'index', 'blog', 'about', 'contact', 'disclaimer', 'dmca', 'privacy', 
    'terms', 'refund', 'kyc', 'attributions', 'accounts', 'login', 'signup', 
    'dashboard', 'pricing', 'payment', 'shipping', 'result', 'feedback'
]

def has_feedback_section(content):
    """Check if page already has feedback section"""
    return bool(re.search(r'Reviews &amp; Comments|Reviews & Comments|feedback-section', content, re.IGNORECASE))

def find_insertion_point(content):
    """Find where to insert feedback section (before SSL badge)"""
    # Priority 1: Before SSL badge / trust-badges
    ssl_pattern = r'(<div[^>]*class="trust-badges"|trust-badges|SSL.*badge)'
    match = re.search(ssl_pattern, content, re.IGNORECASE)
    if match:
        return match.start(), "before SSL badge"
    
    # Priority 2: Before footer placeholder
    footer_pattern = r'(<div[^>]*id="global-footer-placeholder"|global-footer-placeholder)'
    match = re.search(footer_pattern, content, re.IGNORECASE)
    if match:
        return match.start(), "before footer"
    
    # Priority 3: Before closing body tag
    body_end = content.rfind('</body>')
    if body_end > 0:
        return body_end, "before </body>"
    
    return None, None

def remove_old_feedback_section(content):
    """Remove old feedback section if exists"""
    # Pattern to match the old feedback section
    patterns = [
        r'<section class="feedback-section"[^>]*>.*?</section>\s*<script>.*?loadFeedbacks.*?</script>',
        r'<section class="feedback-section"[^>]*>.*?</section>',
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    return content

def update_feedback_section(filepath):
    """Update feedback section to index page style"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove old feedback section if exists
        content = remove_old_feedback_section(content)
        
        # Find insertion point
        insert_pos, location = find_insertion_point(content)
        if insert_pos is None:
            return False, "no insertion point found"
        
        # Insert new feedback section
        content = content[:insert_pos] + '\n' + FEEDBACK_SECTION + '\n' + content[insert_pos:]
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, f"updated {location}"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    print("=" * 50)
    print("Update Feedback Sections to Index Page Style")
    print("=" * 50)
    print()
    
    # Get all HTML files
    html_files = [f for f in Path('.').glob('*.html') 
                  if not any(skip in f.name.lower() for skip in SKIP_PAGES)]
    
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    for filepath in sorted(html_files):
        print(f"Processing: {filepath.name}...", end=' ')
        
        success, message = update_feedback_section(filepath)
        
        if success:
            print(f"[UPDATED - {message}]")
            fixed_count += 1
        else:
            print(f"[SKIP - {message}]")
            skipped_count += 1
            if "error" in message:
                error_count += 1
    
    print()
    print("=" * 50)
    print("Summary:")
    print(f"  Updated Feedback: {fixed_count} pages")
    print(f"  Skipped: {skipped_count} pages")
    if error_count > 0:
        print(f"  Errors: {error_count} pages")
    print("=" * 50)

if __name__ == '__main__':
    main()




