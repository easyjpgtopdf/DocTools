#!/usr/bin/env python3
"""
Script to remove 'Coming Soon' sections from all blog pages
and clean up pages for article links
"""

import os
import re
from pathlib import Path

BLOG_PAGES = [
    'blog.html',
    'blog-articles.html',
    'blog-tutorials.html',
    'blog-tips.html',
    'blog-news.html',
    'blog-guides.html'
]

def clean_blog_page(file_path):
    """Remove Coming Soon section and clean up blog page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Remove Coming Soon section HTML
        coming_soon_patterns = [
            r'(<!-- Coming Soon Message -->\s*<div[^>]*class=["\'][^"\']*coming-soon[^"\']*["\'][^>]*>.*?</div>\s*)',
            r'(<!-- Coming Soon Message -->.*?</div>\s*</div>\s*</div>)',
        ]
        
        for pattern in coming_soon_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                content = content[:match.start()] + content[match.end():]
                break
        
        # 2. Remove Coming Soon CSS
        css_patterns = [
            r'(/\* Coming Soon Message \*/.*?\.notify-btn:hover[^}]*}\s*})',
        ]
        
        for pattern in css_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # 3. Update blog grid - remove display:none
        blog_grid_patterns = [
            r'(<div[^>]*class=["\'][^"\']*blog-grid[^"\']*["\'][^>]*style=["\']display:\s*none;["\'][^>]*>)',
            r'(<!-- Sample Blog Grid.*?will be shown when articles are added.*?-->\s*)',
        ]
        
        for pattern in blog_grid_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                # Replace with clean blog grid
                replacement = '<div class="blog-grid" id="blogGrid">'
                content = content[:match.start()] + replacement + content[match.end():]
                break
        
        # 4. Remove notify button onclick handlers if any
        content = re.sub(r'onclick=["\']scrollToNewsletter\(\)["\']', '', content, flags=re.IGNORECASE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Cleaned {file_path}")
            return True
        else:
            print(f"⚠️  No changes needed to {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function"""
    base_dir = Path(__file__).parent
    
    updated_count = 0
    for blog_file in BLOG_PAGES:
        file_path = base_dir / blog_file
        if file_path.exists():
            if clean_blog_page(file_path):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {blog_file}")
    
    print(f"\n✨ Done! Cleaned {updated_count} blog pages")

if __name__ == '__main__':
    main()

