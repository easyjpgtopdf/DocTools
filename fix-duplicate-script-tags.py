#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix duplicate script tags in HTML files
"""

import re
from pathlib import Path

def fix_duplicate_script_tags(filepath):
    """Remove duplicate script tags"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix duplicate <script> tags
        content = re.sub(r'<script>\s*<script>', '<script>', content)
        content = re.sub(r'</script>\s*</script>', '</script>', content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "fixed duplicate script tags"
        else:
            return False, "no changes needed"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    skip_pages = ['index', 'blog', 'about', 'contact', 'disclaimer', 'dmca', 
                  'privacy', 'terms', 'refund', 'kyc', 'attributions', 'accounts', 
                  'login', 'signup', 'dashboard', 'pricing', 'payment', 'shipping', 
                  'result', 'feedback']
    
    html_files = [f for f in Path('.').glob('*.html') 
                  if not any(skip in f.name.lower() for skip in skip_pages)]
    
    fixed_count = 0
    for filepath in html_files:
        success, message = fix_duplicate_script_tags(filepath)
        if success:
            fixed_count += 1
    
    print(f"Fixed duplicate script tags in {fixed_count} files")

if __name__ == '__main__':
    main()

