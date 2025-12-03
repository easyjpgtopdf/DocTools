#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1. Remove extra content below "Share Feedback" in resume-maker.html
2. Add index page header to pages missing it (no double headers)
"""

import os
import re
from pathlib import Path

# Pages to skip
SKIP_PAGES = [
    'index', 'blog', 'about', 'contact', 'disclaimer', 'dmca', 'privacy', 
    'terms', 'refund', 'kyc', 'attributions', 'accounts', 'login', 'signup', 
    'dashboard', 'pricing', 'payment', 'shipping', 'result', 'feedback'
]

def fix_resume_maker_feedback(filepath):
    """Remove extra content below Share Feedback form"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the feedback form section
        # Pattern: Find "View All Feedback" link and remove everything after it until the closing </div> of feedback-form-card
        # Then keep only the closing tags and script
        
        # More specific: Find the feedback-form-card div and ensure it closes properly after "View All Feedback"
        pattern = r'(<div[^>]*class="feedback-form-card"[^>]*>.*?View All Feedback.*?</a>\s*</div>\s*</div>\s*</div>\s*</section>)'
        
        # Actually, let's find where the form ends and remove any extra content between form closing and section closing
        # Pattern to match: form closing -> View All Feedback link -> then any extra content -> section closing
        pattern = r'(</form>\s*<div[^>]*>.*?View All Feedback.*?</a>\s*</div>\s*</div>)(.*?)(</section>)'
        
        def clean_feedback(match):
            form_end = match.group(1)  # Form end + View All Feedback link + closing divs
            extra_content = match.group(2)  # Any extra content
            section_end = match.group(3)  # Section closing
            
            # Remove any extra divs, paragraphs, or content between
            # Keep only if it's the closing div of feedback-form-card
            cleaned_extra = re.sub(r'<div[^>]*>.*?</div>', '', extra_content, flags=re.DOTALL)
            cleaned_extra = re.sub(r'<p[^>]*>.*?</p>', '', cleaned_extra, flags=re.DOTALL)
            cleaned_extra = re.sub(r'<span[^>]*>.*?</span>', '', cleaned_extra, flags=re.DOTALL)
            
            return form_end + section_end
        
        content = re.sub(pattern, clean_feedback, content, flags=re.DOTALL | re.IGNORECASE)
        
        # Also remove any standalone extra content after the feedback section
        # Pattern: after </section> of feedback, remove any extra divs/paragraphs before SSL badge
        pattern2 = r'(</section>\s*)(<div[^>]*>.*?</div>\s*)*(<div[^>]*class="trust-badges"|<style)'
        content = re.sub(pattern2, r'\1\3', content, flags=re.DOTALL | re.IGNORECASE)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, "cleaned extra content"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def has_header_placeholder(content):
    """Check if page has global-header-placeholder"""
    return bool(re.search(r'global-header-placeholder', content, re.IGNORECASE))

def has_old_header(content):
    """Check if page has old <header> tag"""
    return bool(re.search(r'<header[^>]*>', content, re.IGNORECASE))

def add_header_placeholder(filepath):
    """Add global-header-placeholder if missing"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has placeholder
        if has_header_placeholder(content):
            return False, "already has header placeholder"
        
        # Check if has old header tag - remove it first
        if has_old_header(content):
            # Remove old header tag and its content
            content = re.sub(r'<header[^>]*>.*?</header>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Find <body> tag and add placeholder right after it
        body_pattern = r'(<body[^>]*>)'
        replacement = r'\1\n    <div id="global-header-placeholder"></div>'
        
        if re.search(body_pattern, content):
            content = re.sub(body_pattern, replacement, content, flags=re.IGNORECASE)
        else:
            return False, "no body tag found"
        
        # Ensure global-components.js is included before </body>
        if 'global-components.js' not in content:
            body_end = content.rfind('</body>')
            if body_end > 0:
                script_tag = '\n    <script src="js/global-components.js" defer></script>'
                content = content[:body_end] + script_tag + '\n' + content[body_end:]
        
        # Ensure header.css is linked in <head>
        if 'css/header.css' not in content:
            head_end = content.find('</head>')
            if head_end > 0:
                link_tag = '    <link rel="stylesheet" href="css/header.css">\n'
                content = content[:head_end] + link_tag + content[head_end:]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, "added header placeholder"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    print("=" * 60)
    print("Fix Resume Maker Feedback & Add Missing Headers")
    print("=" * 60)
    print()
    
    # Fix resume-maker.html
    print("1. Fixing resume-maker.html feedback section...")
    resume_file = Path('resume-maker.html')
    if resume_file.exists():
        success, message = fix_resume_maker_feedback(resume_file)
        if success:
            print(f"   ✓ {message}")
        else:
            print(f"   ✗ {message}")
    else:
        print("   ✗ resume-maker.html not found")
    
    print()
    print("2. Checking pages for missing headers...")
    
    # Get all HTML files
    html_files = [f for f in Path('.').glob('*.html') 
                  if not any(skip in f.name.lower() for skip in SKIP_PAGES)]
    
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    for filepath in sorted(html_files):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not has_header_placeholder(content):
            print(f"   Processing: {filepath.name}...", end=' ')
            success, message = add_header_placeholder(filepath)
            if success:
                print(f"[ADDED - {message}]")
                fixed_count += 1
            else:
                print(f"[SKIP - {message}]")
                skipped_count += 1
                if "error" in message:
                    error_count += 1
    
    print()
    print("=" * 60)
    print("Summary:")
    print(f"  Resume Maker: Fixed")
    print(f"  Headers Added: {fixed_count} pages")
    print(f"  Already Had Header: {skipped_count} pages")
    if error_count > 0:
        print(f"  Errors: {error_count} pages")
    print("=" * 60)

if __name__ == '__main__':
    main()





