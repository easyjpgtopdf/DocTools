#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add "View All Comments" link below "Reviews & Comments" heading in all HTML pages
Updates all pages that have the Reviews & Comments section
"""

import os
import re
from pathlib import Path

# Pattern to find Reviews & Comments heading
REVIEWS_PATTERN = r'(<h2[^>]*style="[^"]*font-size:\s*2rem[^"]*color:\s*#4361ee[^"]*margin-bottom:\s*30px[^"]*text-align:\s*center[^"]*">\s*<i[^>]*class="[^"]*fa-comments[^"]*"[^>]*></i>\s*Reviews\s*&\s*Comments\s*</h2>)'

# Replacement with View All Comments link
REPLACEMENT = r'''\1
        <div style="text-align: center; margin-bottom: 30px;">
            <a href="feedback.html" style="display: inline-flex; align-items: center; gap: 8px; color: #4361ee; text-decoration: none; font-weight: 600; font-size: 1rem; transition: color 0.3s;" onmouseover="this.style.color='#3a0ca3'" onmouseout="this.style.color='#4361ee'">
                <i class="fas fa-external-link-alt"></i>
                View All Comments
            </a>
        </div>'''

def update_file(file_path):
    """Update a single HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has Reviews & Comments section
        if 'Reviews & Comments' not in content:
            return False
        
        # Check if View All Comments link already exists
        if 'View All Comments' in content or 'view all comments' in content.lower():
            # Check if it's in the right place (after heading)
            if re.search(r'Reviews\s*&\s*Comments.*?View All Comments', content, re.DOTALL | re.IGNORECASE):
                return False  # Already exists in correct location
        
        # Replace the heading with heading + link
        new_content = re.sub(
            REVIEWS_PATTERN,
            REPLACEMENT,
            content,
            flags=re.IGNORECASE | re.DOTALL
        )
        
        # If no change, try a simpler pattern
        if new_content == content:
            # Try simpler pattern - just find the heading and add link after it
            pattern_simple = r'(<h2[^>]*>.*?Reviews\s*&\s*Comments.*?</h2>)'
            new_content = re.sub(
                pattern_simple + r'(\s*</h2>\s*<div[^>]*class="feedback-grid")',
                r'\1\n        <div style="text-align: center; margin-bottom: 30px;">\n            <a href="feedback.html" style="display: inline-flex; align-items: center; gap: 8px; color: #4361ee; text-decoration: none; font-weight: 600; font-size: 1rem; transition: color 0.3s;" onmouseover="this.style.color=\'#3a0ca3\'" onmouseout="this.style.color=\'#4361ee\'">\n                <i class="fas fa-external-link-alt"></i>\n                View All Comments\n            </a>\n        </div>\2',
                content,
                flags=re.IGNORECASE | re.DOTALL
            )
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to update all HTML files"""
    base_dir = Path(__file__).parent
    html_files = list(base_dir.glob('*.html'))
    
    updated_count = 0
    skipped_count = 0
    
    for html_file in html_files:
        if html_file.name in ['index.html', 'feedback.html']:
            continue  # Skip index and feedback page
        
        if update_file(html_file):
            print(f"✅ Updated: {html_file.name}")
            updated_count += 1
        else:
            skipped_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Updated: {updated_count} files")
    print(f"   Skipped: {skipped_count} files")

if __name__ == '__main__':
    main()

