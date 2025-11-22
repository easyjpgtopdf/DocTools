#!/usr/bin/env python3
"""
Remove search bar wrapper from blog pages - search bar now in header
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

def remove_search_wrapper(file_path):
    """Remove search bar wrapper from blog pages"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove blog-filters-wrapper and restore simple blog-filters structure
        wrapper_pattern = r'(<!-- Filter Tabs and Search Bar Wrapper -->\s*<div[^>]*class=["\']blog-filters-wrapper["\'][^>]*>)\s*(<div[^>]*class=["\']blog-filters["\'][^>]*>.*?</div>)\s*(<!-- Search bar will be added here by blog-search\.js -->)\s*(</div>)'
        
        match = re.search(wrapper_pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            # Replace with simple blog-filters div
            filters_content = match.group(2)
            replacement = '            <!-- Filter Tabs -->\n' + filters_content.strip() + '\n'
            content = content[:match.start()] + replacement + content[match.end():]
        
        # Remove blog-page-search-container related CSS if present
        if 'blog-page-search-container' in content:
            # Remove CSS rules for blog page search
            css_patterns = [
                r'(/\* Blog Page Search Bar.*?\*/.*?@media[^}]*}\s*})',
                r'(\.blog-page-search-container[^}]*}\s*})',
                r'(\.blog-filters-wrapper[^}]*}\s*})',
            ]
            
            for pattern in css_patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated {file_path}")
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
            if remove_search_wrapper(file_path):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {blog_file}")
    
    print(f"\n✨ Done! Updated {updated_count} blog pages")

if __name__ == '__main__':
    main()

