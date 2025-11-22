#!/usr/bin/env python3
"""
Add center search bar CSS to all blog pages
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

def add_center_search_css(file_path):
    """Add center search bar CSS to blog page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if center search CSS already exists
        if 'center-search-container' in content:
            print(f"✅ {file_path} already has center search CSS")
            return False
        
        # Find where to add CSS (after blog-search-input::placeholder or before @media)
        css_patterns = [
            r'(\.blog-search-input::placeholder[^}]*\})',
            r'(/\* Blog Page Search Bar[^}]*\})',
            r'(@media.*?max-width.*?768px)',
        ]
        
        center_search_css = '''
        
        /* Center Search Bar - Below Header, Above Titles */
        .center-search-container {
            position: relative;
            width: 100%;
            margin: 30px auto 40px;
            display: flex;
            justify-content: center;
        }
        
        .center-search-wrapper {
            position: relative;
            max-width: 600px;
            width: 100%;
            margin: 0 auto;
        }
        
        .center-search-input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
            background: white;
            border: 2px solid rgba(67, 97, 238, 0.3);
            border-radius: 999px;
            padding: 12px 20px;
            box-shadow: 0 4px 16px rgba(67, 97, 238, 0.15);
            transition: all 0.3s;
        }
        
        .center-search-input-wrapper:focus-within {
            border-color: #4361ee;
            box-shadow: 0 8px 24px rgba(67, 97, 238, 0.25);
            transform: translateY(-2px);
        }
        
        .center-search-container .blog-search-icon {
            color: #4361ee;
            font-size: 1.1rem;
            margin-right: 12px;
            flex-shrink: 0;
        }
        
        .center-search-input {
            flex: 1;
            border: none;
            outline: none;
            font-size: 1rem;
            color: #0b1630;
            background: transparent;
            font-weight: 500;
        }
        
        .center-search-input::placeholder {
            color: #7a8196;
            font-size: 0.95rem;
        }
        
        .center-search-clear {
            background: none;
            border: none;
            color: #7a8196;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 50%;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            margin-left: 8px;
        }
        
        .center-search-clear:hover {
            background: rgba(67, 97, 238, 0.1);
            color: #4361ee;
        }
        
        .center-search-results {
            position: absolute;
            top: calc(100% + 10px);
            left: 0;
            right: 0;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            max-height: 500px;
            overflow-y: auto;
            z-index: 1000;
            margin-top: 8px;
        }
        
        /* Hide header search bar on blog pages */
        header .header-search-container {
            display: none !important;
        }
        
        @media (max-width: 768px) {
            .center-search-container {
                margin: 20px auto 30px;
            }
            
            .center-search-wrapper {
                max-width: 100%;
            }
            
            .center-search-input-wrapper {
                padding: 10px 16px;
            }
        }
'''
        
        for pattern in css_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                content = content[:match.start()] + center_search_css + content[match.start():]
                break
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Added center search CSS to {file_path}")
            return True
        else:
            print(f"⚠️  Could not add CSS to {file_path}")
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
            if add_center_search_css(file_path):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {blog_file}")
    
    print(f"\n✨ Done! Updated {updated_count} blog pages")

if __name__ == '__main__':
    main()

