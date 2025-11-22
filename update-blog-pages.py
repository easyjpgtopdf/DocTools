#!/usr/bin/env python3
"""
Script to add voice assistant and search bar to all blog pages
Adds voice assistant CSS/JS and updates search bar structure
"""

import os
import re
from pathlib import Path

# Blog pages to update
BLOG_PAGES = [
    'blog.html',
    'blog-articles.html',
    'blog-tutorials.html',
    'blog-tips.html',
    'blog-news.html',
    'blog-guides.html'
]

def update_blog_page(file_path):
    """Update a blog page with voice assistant and search bar"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Add voice assistant CSS if not present
        if 'voice-assistant.css' not in content:
            css_patterns = [
                r'(<link[^>]*href=["\']css/advertisement\.css["\'][^>]*>)',
                r'(<link[^>]*href=["\']css/theme-modern\.css["\'][^>]*>)',
            ]
            
            for pattern in css_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    voice_css = '<link rel="stylesheet" href="css/voice-assistant.css">'
                    content = content[:match.end()] + '\n    ' + voice_css + content[match.end():]
                    break
        
        # 2. Add voice assistant JS if not present
        if 'voice-assistant.js' not in content:
            # Find first script tag or before closing head
            script_patterns = [
                r'(</head>)',
                r'(<script[^>]*src=["\'][^"]*["\'][^>]*>)',
            ]
            
            for pattern in script_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    voice_js = '<script src="js/voice-assistant.js" defer></script>'
                    if '</head>' in match.group(0):
                        content = content[:match.start()] + '    ' + voice_js + '\n' + content[match.start():]
                    else:
                        content = content[:match.end()] + '\n    ' + voice_js + content[match.end():]
                    break
        
        # 3. Add blog-search.js if not present
        if 'blog-search.js' not in content:
            # Add before auth.js or at end of scripts
            script_patterns = [
                r'(<script[^>]*src=["\']js/auth\.js["\'][^>]*>)',
                r'(<!-- Auth Script -->)',
                r'(</body>)',
            ]
            
            for pattern in script_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    blog_search_js = '    <!-- Blog Search Script -->\n    <script src="js/blog-search.js" defer></script>\n\n    '
                    content = content[:match.start()] + blog_search_js + content[match.start():]
                    break
        
        # 4. Update filter tabs structure if needed
        if 'blog-filters-wrapper' not in content:
            # Find blog-filters div
            filters_pattern = r'(<div[^>]*class=["\'][^"\']*blog-filters[^"\']*["\'][^>]*>.*?</div>\s*</div>)'
            match = re.search(filters_pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                filters_html = match.group(0)
                # Wrap with blog-filters-wrapper
                wrapper_html = '            <!-- Filter Tabs and Search Bar Wrapper -->\n            <div class="blog-filters-wrapper">\n' + filters_html + '\n                <!-- Search bar will be added here by blog-search.js -->\n            </div>'
                content = content[:match.start()] + wrapper_html + content[match.end():]
        
        # 5. Add CSS for blog page search bar if not present
        if 'blog-page-search-container' not in content:
            # Find where to add CSS (before closing style tag or in head)
            css_patterns = [
                r'(</style>)',
                r'(\.blog-search-input::placeholder[^}]*\})',
            ]
            
            for pattern in css_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    blog_search_css = '''
        
        /* Blog Page Search Bar - Next to Filter Tabs */
        .blog-page-search-container {
            position: relative;
            flex: 1;
            min-width: 250px;
            max-width: 400px;
        }
        
        .blog-page-search-input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
            background: white;
            border: 2px solid rgba(67, 97, 238, 0.2);
            border-radius: 999px;
            padding: 10px 16px;
            box-shadow: 0 4px 12px rgba(67, 97, 238, 0.1);
            transition: all 0.3s;
        }
        
        .blog-page-search-input-wrapper:focus-within {
            border-color: #4361ee;
            box-shadow: 0 6px 20px rgba(67, 97, 238, 0.2);
            transform: translateY(-2px);
        }
        
        .blog-page-search-container .blog-search-icon {
            color: #4361ee;
            font-size: 1rem;
            margin-right: 10px;
        }
        
        .blog-page-search-input {
            flex: 1;
            border: none;
            outline: none;
            font-size: 0.9rem;
            color: #0b1630;
            background: transparent;
            font-weight: 500;
        }
        
        .blog-page-search-input::placeholder {
            color: #7a8196;
            font-size: 0.9rem;
        }
        
        .blog-page-search-results {
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
        
        /* Filter tabs and search bar wrapper */
        .blog-filters-wrapper {
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }
        
        @media (max-width: 768px) {
            .blog-page-search-container {
                width: 100%;
                max-width: 100%;
            }
            
            .blog-filters-wrapper {
                flex-direction: column;
                align-items: stretch;
            }
        }
'''
                    content = content[:match.start()] + blog_search_css + content[match.start():]
                    break
        
        # Only write if content changed
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
    """Main function to process all blog pages"""
    base_dir = Path(__file__).parent
    
    updated_count = 0
    for blog_file in BLOG_PAGES:
        file_path = base_dir / blog_file
        if file_path.exists():
            if update_blog_page(file_path):
                updated_count += 1
        else:
            print(f"⚠️  File not found: {blog_file}")
    
    print(f"\n✨ Done! Updated {updated_count} blog pages")

if __name__ == '__main__':
    main()

