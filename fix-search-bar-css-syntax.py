#!/usr/bin/env python3
"""
Fix CSS Syntax Error in Blog Pages
Remove double semicolons from search container margin
"""

import os
import re
from pathlib import Path

# Blog pages to fix
BLOG_PAGES = [
    'blog-articles.html',
    'blog-tutorials.html',
    'blog-tips.html',
    'blog-news.html',
    'blog-guides.html',
    'blog.html'
]

def fix_double_semicolon(file_path):
    """Fix double semicolon in CSS"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return False, "Cannot read file"
    
    original = content
    
    # Fix double semicolon
    content = content.replace(';;', ';')
    
    # Also ensure icon font size is 1.1rem
    content = re.sub(
        r'\.blog-search-icon\s*\{[^}]*font-size:\s*1rem',
        r'.blog-search-icon {\n            color: #4361ee;\n            font-size: 1.1rem',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, "Fixed double semicolon and updated icon size"
    else:
        return False, "No changes needed"

def main():
    """Main function"""
    root_dir = Path(__file__).parent
    
    print("🔧 Fixing CSS Syntax Errors...\n")
    print("="*80)
    
    fixed_count = 0
    
    for blog_page in BLOG_PAGES:
        file_path = root_dir / blog_page
        
        if not file_path.exists():
            continue
        
        relative_path = file_path.relative_to(root_dir)
        print(f"📄 {relative_path}")
        
        success, message = fix_double_semicolon(file_path)
        
        if success:
            print(f"   ✅ {message}")
            fixed_count += 1
        else:
            print(f"   ✓ {message}")
    
    print("\n" + "="*80)
    print(f"✅ Fixed {fixed_count} files")
    print("="*80)

if __name__ == '__main__':
    main()

