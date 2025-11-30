#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add FAQ Section to Pages Without FAQ
Places FAQ after Related Tools section, before SSL badge/footer
"""

import os
import re
from pathlib import Path

# FAQ Section HTML
FAQ_SECTION = '''    <section class="faq-section" style="margin: 40px 0; padding: 40px; background: #f8f9ff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="font-size: 2rem; color: #4361ee; margin-bottom: 30px; text-align: center;">
            <i class="fas fa-question-circle" style="margin-right: 10px;"></i>
            Frequently Asked Questions
        </h2>
        <div class="faq-container" style="max-width: 800px; margin: 0 auto;">
            <div class="faq-item" style="margin-bottom: 20px; padding: 20px; background: white; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px; cursor: pointer; display: flex; align-items: center;" onclick="toggleFaq(this)">
                    <i class="fas fa-chevron-right" style="color: #4361ee; margin-right: 10px; transition: transform 0.3s;"></i>
                    How accurate is the conversion?
                </h3>
                <div class="faq-answer" style="font-size: 1rem; color: #56607a; line-height: 1.6; margin-top: 10px; display: none; padding-left: 30px;">
                    Our conversion tools maintain 99% accuracy, preserving all formatting, fonts, and layout from your original files.
                </div>
            </div>
            <div class="faq-item" style="margin-bottom: 20px; padding: 20px; background: white; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px; cursor: pointer; display: flex; align-items: center;" onclick="toggleFaq(this)">
                    <i class="fas fa-chevron-right" style="color: #4361ee; margin-right: 10px; transition: transform 0.3s;"></i>
                    What file sizes are supported?
                </h3>
                <div class="faq-answer" style="font-size: 1rem; color: #56607a; line-height: 1.6; margin-top: 10px; display: none; padding-left: 30px;">
                    Free users can convert files up to 10MB. Premium users can process files up to 100MB with faster processing.
                </div>
            </div>
            <div class="faq-item" style="margin-bottom: 20px; padding: 20px; background: white; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px; cursor: pointer; display: flex; align-items: center;" onclick="toggleFaq(this)">
                    <i class="fas fa-chevron-right" style="color: #4361ee; margin-right: 10px; transition: transform 0.3s;"></i>
                    Will my data be secure?
                </h3>
                <div class="faq-answer" style="font-size: 1rem; color: #56607a; line-height: 1.6; margin-top: 10px; display: none; padding-left: 30px;">
                    Yes, all files are processed securely and automatically deleted after conversion. We never store or share your documents.
                </div>
            </div>
            <div class="faq-item" style="margin-bottom: 20px; padding: 20px; background: white; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px; cursor: pointer; display: flex; align-items: center;" onclick="toggleFaq(this)">
                    <i class="fas fa-chevron-right" style="color: #4361ee; margin-right: 10px; transition: transform 0.3s;"></i>
                    Can I convert multiple files at once?
                </h3>
                <div class="faq-answer" style="font-size: 1rem; color: #56607a; line-height: 1.6; margin-top: 10px; display: none; padding-left: 30px;">
                    Yes, premium users can convert multiple files simultaneously. Free users can process one file at a time.
                </div>
            </div>
            <div class="faq-item" style="margin-bottom: 20px; padding: 20px; background: white; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px; cursor: pointer; display: flex; align-items: center;" onclick="toggleFaq(this)">
                    <i class="fas fa-chevron-right" style="color: #4361ee; margin-right: 10px; transition: transform 0.3s;"></i>
                    What formats are supported?
                </h3>
                <div class="faq-answer" style="font-size: 1rem; color: #56607a; line-height: 1.6; margin-top: 10px; display: none; padding-left: 30px;">
                    We support all major file formats. Check the tool page for specific format compatibility.
                </div>
            </div>
        </div>
    </section>

    <script>
    function toggleFaq(element) {
        const answer = element.nextElementSibling;
        const icon = element.querySelector('i');
        const isOpen = answer.style.display === 'block';

        answer.style.display = isOpen ? 'none' : 'block';
        icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(90deg)';
    }
    </script>'''

# Pages to skip
SKIP_PAGES = [
    'index', 'blog', 'about', 'contact', 'disclaimer', 'dmca', 'privacy', 
    'terms', 'refund', 'kyc', 'attributions', 'accounts', 'login', 'signup', 
    'dashboard', 'pricing', 'payment', 'shipping', 'result'
]

def has_faq(content):
    """Check if page already has FAQ section"""
    return bool(re.search(r'FAQ|faq|Frequently Asked', content, re.IGNORECASE))

def find_insertion_point(content):
    """Find where to insert FAQ section"""
    # Priority 1: After Related Tools section
    related_pattern = r'(</section>[\s\S]*?Related Tools[\s\S]*?</section>)'
    match = re.search(related_pattern, content, re.IGNORECASE)
    if match:
        return match.end(), "after Related Tools section"
    
    # Priority 2: Before SSL badge
    ssl_pattern = r'(<div[^>]*class="trust-badges"|trust-badges|SSL|ssl)'
    match = re.search(ssl_pattern, content, re.IGNORECASE)
    if match:
        return match.start(), "before SSL badge"
    
    # Priority 3: Before footer placeholder
    footer_pattern = r'(<div[^>]*id="global-footer-placeholder"|global-footer-placeholder)'
    match = re.search(footer_pattern, content, re.IGNORECASE)
    if match:
        return match.start(), "before footer"
    
    # Priority 4: Before closing body tag
    body_end = content.rfind('</body>')
    if body_end > 0:
        return body_end, "before </body>"
    
    return None, None

def has_toggle_script(content):
    """Check if toggleFaq function already exists"""
    return bool(re.search(r'function\s+toggleFaq|toggleFaq\s*=', content))

def add_faq_to_page(filepath):
    """Add FAQ section to a single page"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has FAQ
        if has_faq(content):
            return False, "already has FAQ"
        
        # Find insertion point
        insert_pos, location = find_insertion_point(content)
        if insert_pos is None:
            return False, "no insertion point found"
        
        # Insert FAQ section
        faq_to_insert = FAQ_SECTION
        content = content[:insert_pos] + '\n' + faq_to_insert + '\n' + content[insert_pos:]
        
        # Check if toggleFaq script needed
        if not has_toggle_script(content):
            # Add script before closing body tag
            body_end = content.rfind('</body>')
            if body_end > 0:
                toggle_script = '''    <script>
    function toggleFaq(element) {
        const answer = element.nextElementSibling;
        const icon = element.querySelector('i');
        const isOpen = answer.style.display === 'block';

        answer.style.display = isOpen ? 'none' : 'block';
        icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(90deg)';
    }
    </script>'''
                content = content[:body_end] + '\n' + toggle_script + '\n' + content[body_end:]
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, f"added {location}"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    print("=" * 50)
    print("Add FAQ to Pages Without FAQ")
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
        
        success, message = add_faq_to_page(filepath)
        
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
    print(f"  Added FAQ: {fixed_count} pages")
    print(f"  Skipped: {skipped_count} pages")
    if error_count > 0:
        print(f"  Errors: {error_count} pages")
    print("=" * 50)

if __name__ == '__main__':
    main()

