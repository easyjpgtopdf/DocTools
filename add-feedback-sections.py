#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Reviews & Comments Feedback Section to Tool Pages
Places feedback section before SSL security badge
Only adds to pages that don't already have it
"""

import os
import re
from pathlib import Path

# Feedback Section HTML (shows only 3 feedbacks per page)
FEEDBACK_SECTION = '''    <section class="feedback-section" style="margin: 40px 0; padding: 40px; background: #f8f9ff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="font-size: 2rem; color: #4361ee; margin-bottom: 30px; text-align: center;">
            <i class="fas fa-comments" style="margin-right: 10px;"></i>
            Reviews & Comments
        </h2>
        
        <div class="feedback-container" style="max-width: 900px; margin: 0 auto;">
            <!-- Share Feedback Form -->
            <div class="feedback-form-card" style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h3 style="font-size: 1.3rem; color: #0b1630; margin-bottom: 20px;">
                    <i class="fas fa-edit" style="color: #4361ee; margin-right: 8px;"></i>
                    Share Your Feedback
                </h3>
                <form id="feedbackForm" style="display: flex; flex-direction: column; gap: 15px;">
                    <div class="form-group">
                        <label for="feedbackName" style="display: block; margin-bottom: 8px; color: #56607a; font-weight: 600;">Your Name</label>
                        <input type="text" id="feedbackName" placeholder="Enter your name" required style="width: 100%; padding: 12px 16px; border: 1px solid #e2e6ff; border-radius: 8px; font-size: 0.95rem; transition: border-color 0.3s;" onfocus="this.style.borderColor='#4361ee'" onblur="this.style.borderColor='#e2e6ff'">
                    </div>
                    <div class="form-group">
                        <label for="feedbackMessage" style="display: block; margin-bottom: 8px; color: #56607a; font-weight: 600;">Your Comment</label>
                        <textarea id="feedbackMessage" placeholder="Write your feedback or comment here..." required rows="4" style="width: 100%; padding: 12px 16px; border: 1px solid #e2e6ff; border-radius: 8px; font-size: 0.95rem; resize: vertical; transition: border-color 0.3s; font-family: inherit;" onfocus="this.style.borderColor='#4361ee'" onblur="this.style.borderColor='#e2e6ff'"></textarea>
                    </div>
                    <button type="submit" style="background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; align-self: flex-start;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(67, 97, 238, 0.3)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                        <i class="fas fa-paper-plane" style="margin-right: 8px;"></i>
                        Submit Feedback
                    </button>
                </form>
            </div>
            
            <!-- Display Feedback (Only 3 per page) -->
            <div id="feedbackList" class="feedback-list" style="display: flex; flex-direction: column; gap: 20px;">
                <!-- Feedback items will be loaded here (max 3) -->
                <div class="feedback-item" style="background: white; padding: 20px; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div>
                            <h4 style="font-size: 1.1rem; color: #0b1630; margin-bottom: 4px;">John Doe</h4>
                            <span style="font-size: 0.85rem; color: #9ca3af;">2 days ago</span>
                        </div>
                        <div style="color: #fbbf24;">
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                        </div>
                    </div>
                    <p style="color: #56607a; line-height: 1.6; margin-bottom: 15px;">Great tool! Very easy to use and the conversion quality is excellent.</p>
                    
                    <!-- Reply Section -->
                    <div class="feedback-reply" style="margin-left: 30px; padding: 15px; background: #f8f9ff; border-radius: 8px; margin-top: 10px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <i class="fas fa-reply" style="color: #4361ee; font-size: 0.9rem;"></i>
                            <strong style="color: #4361ee; font-size: 0.9rem;">Admin Reply:</strong>
                        </div>
                        <p style="color: #56607a; font-size: 0.9rem; line-height: 1.5;">Thank you for your feedback! We're glad you found the tool helpful.</p>
                    </div>
                </div>
                
                <div class="feedback-item" style="background: white; padding: 20px; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div>
                            <h4 style="font-size: 1.1rem; color: #0b1630; margin-bottom: 4px;">Sarah Smith</h4>
                            <span style="font-size: 0.85rem; color: #9ca3af;">5 days ago</span>
                        </div>
                        <div style="color: #fbbf24;">
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="far fa-star"></i>
                        </div>
                    </div>
                    <p style="color: #56607a; line-height: 1.6; margin-bottom: 15px;">Works perfectly for my needs. Quick and reliable conversion.</p>
                </div>
                
                <div class="feedback-item" style="background: white; padding: 20px; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div>
                            <h4 style="font-size: 1.1rem; color: #0b1630; margin-bottom: 4px;">Mike Johnson</h4>
                            <span style="font-size: 0.85rem; color: #9ca3af;">1 week ago</span>
                        </div>
                        <div style="color: #fbbf24;">
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                            <i class="fas fa-star"></i>
                        </div>
                    </div>
                    <p style="color: #56607a; line-height: 1.6; margin-bottom: 15px;">Excellent service! Highly recommend this tool to everyone.</p>
                </div>
            </div>
            
            <!-- Link to All Feedback Page -->
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e6ff;">
                <a href="feedback.html" style="color: #4361ee; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; transition: color 0.3s;" onmouseover="this.style.color='#3a0ca3'" onmouseout="this.style.color='#4361ee'">
                    <i class="fas fa-arrow-right"></i>
                    View All Feedback & Comments
                </a>
            </div>
        </div>
    </section>

    <script>
    // Store feedback in localStorage (in production, use backend API)
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    // Load feedbacks for this page (max 3)
    function loadFeedbacks() {
        const storedFeedbacks = JSON.parse(localStorage.getItem('feedbacks') || '{}');
        const pageFeedbacks = (storedFeedbacks[currentPage] || []).slice(0, 3);
        const feedbackList = document.getElementById('feedbackList');
        
        if (pageFeedbacks.length === 0) {
            // Show default feedbacks if none exist
            return;
        }
        
        feedbackList.innerHTML = pageFeedbacks.map(fb => `
            <div class="feedback-item" style="background: white; padding: 20px; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                    <div>
                        <h4 style="font-size: 1.1rem; color: #0b1630; margin-bottom: 4px;">${fb.name}</h4>
                        <span style="font-size: 0.85rem; color: #9ca3af;">${fb.date}</span>
                    </div>
                    <div style="color: #fbbf24;">
                        ${'<i class="fas fa-star"></i>'.repeat(fb.rating || 5)}
                        ${'<i class="far fa-star"></i>'.repeat(5 - (fb.rating || 5))}
                    </div>
                </div>
                <p style="color: #56607a; line-height: 1.6; margin-bottom: 15px;">${fb.message}</p>
                ${fb.reply ? `
                    <div class="feedback-reply" style="margin-left: 30px; padding: 15px; background: #f8f9ff; border-radius: 8px; margin-top: 10px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <i class="fas fa-reply" style="color: #4361ee; font-size: 0.9rem;"></i>
                            <strong style="color: #4361ee; font-size: 0.9rem;">Admin Reply:</strong>
                        </div>
                        <p style="color: #56607a; font-size: 0.9rem; line-height: 1.5;">${fb.reply}</p>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    // Handle feedback form submission
    document.getElementById('feedbackForm').addEventListener('submit', function(e) {
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
            rating: 5,
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
    return bool(re.search(r'Reviews &amp; Comments|Reviews & Comments|feedback-section|Share Feedback', content, re.IGNORECASE))

def find_insertion_point(content):
    """Find where to insert feedback section (before SSL badge)"""
    # Priority 1: Before SSL badge / trust-badges
    ssl_pattern = r'(<div[^>]*class="trust-badges"|trust-badges|SSL|ssl.*badge)'
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

def add_feedback_to_page(filepath):
    """Add feedback section to a single page"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has feedback
        if has_feedback_section(content):
            return False, "already has feedback section"
        
        # Find insertion point
        insert_pos, location = find_insertion_point(content)
        if insert_pos is None:
            return False, "no insertion point found"
        
        # Insert feedback section
        content = content[:insert_pos] + '\n' + FEEDBACK_SECTION + '\n' + content[insert_pos:]
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, f"added {location}"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    print("=" * 50)
    print("Add Feedback Sections to Tool Pages")
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
        
        success, message = add_feedback_to_page(filepath)
        
        if success:
            print(f"[ADDED - {message}]")
            fixed_count += 1
        elif "already has" in message:
            print(f"[SKIP - {message}]")
            skipped_count += 1
        else:
            print(f"[SKIP - {message}]")
            skipped_count += 1
            if "error" in message:
                error_count += 1
    
    print()
    print("=" * 50)
    print("Summary:")
    print(f"  Added Feedback: {fixed_count} pages")
    print(f"  Skipped: {skipped_count} pages")
    if error_count > 0:
        print(f"  Errors: {error_count} pages")
    print("=" * 50)

if __name__ == '__main__':
    main()






