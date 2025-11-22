#!/usr/bin/env python3
"""
Script to remove all 'Coming Soon' sections from blog pages
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

def remove_coming_soon(file_path):
    """Remove Coming Soon section from blog page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove Coming Soon div section
        coming_soon_pattern = r'(<div[^>]*class=["\'][^"\']*coming-soon[^"\']*["\'][^>]*>.*?</div>\s*</div>\s*</div>)'
        
        match = re.search(coming_soon_pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            content = content[:match.start()] + content[match.end():]
        
        # Remove Coming Soon CSS
        coming_soon_css = r'(/\* Coming Soon.*?\*/.*?\.coming-soon[^}]*}\s*\.coming-soon[^}]*}\s*\.coming-soon[^}]*}\s*\.coming-soon[^}]*}\s*\.notify-btn[^}]*}\s*\.notify-btn:hover[^}]*}\s*)'
        content = re.sub(coming_soon_css, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Also remove simpler CSS patterns
        coming_soon_css_simple = r'(\.coming-soon[^}]*}\s*\.coming-soon[^}]*}\s*\.coming-soon[^}]*}\s*\.coming-soon[^}]*}\s*)'
        content = re.sub(coming_soon_css_simple, '', content, flags=re.IGNORECASE | re.DOTALL)
        
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
            if remove_coming_soon(file_path):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {blog_file}")
    
    print(f"\n✨ Done! Cleaned {updated_count} blog pages")

if __name__ == '__main__':
    main()

