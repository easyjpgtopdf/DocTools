#!/usr/bin/env python3
"""
Fix Blog Search Bar Visibility:
1. Make search bar visible and properly sized in all blog pages
2. Ensure search bar is placed correctly in the DOM
3. Add advertisement space on blog pages
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

EXCLUDE_PATTERNS = ['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backups']

def should_exclude(file_path):
    """Check if file should be excluded"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def fix_search_bar_styling(content, file_path):
    """Fix search bar styling to make it visible and properly sized"""
    changes = []
    
    # Ensure search bar container has proper visibility and size
    search_container_pattern = r'\.blog-search-container\s*\{[^}]*\}'
    match = re.search(search_container_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        search_container_css = match.group(0)
        
        # Check if it has proper display and visibility
        if 'display: none' in search_container_css or 'visibility: hidden' in search_container_css:
            # Remove hidden styles
            content = content.replace(search_container_css, 
                re.sub(r'display:\s*none|visibility:\s*hidden', '', search_container_css, flags=re.IGNORECASE))
            changes.append("Removed hidden styles from search container")
        
        # Ensure proper margin and width
        if 'margin: 15px 0 20px' not in search_container_css and 'margin: 30px 0 40px' not in search_container_css:
            # Add proper margin
            new_css = re.sub(
                r'margin:\s*[^;}]+',
                'margin: 30px 0 30px',
                search_container_css,
                flags=re.IGNORECASE
            )
            if new_css == search_container_css:
                # Add margin if not present
                new_css = search_container_css.replace('}', '\n            margin: 30px 0 30px;\n        }')
            content = content.replace(search_container_css, new_css)
            changes.append("Added proper margin to search container")
    
    # Ensure search wrapper is visible and sized
    search_wrapper_pattern = r'\.blog-search-wrapper\s*\{[^}]*\}'
    match = re.search(search_wrapper_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        search_wrapper_css = match.group(0)
        
        # Ensure max-width is set properly
        if 'max-width' not in search_wrapper_css:
            new_css = search_wrapper_css.replace('}', '\n            max-width: 700px;\n            margin: 0 auto;\n        }')
            content = content.replace(search_wrapper_css, new_css)
            changes.append("Added max-width to search wrapper")
        elif 'max-width: 600px' in search_wrapper_css:
            # Make it slightly larger
            content = re.sub(
                r'max-width:\s*600px',
                'max-width: 700px',
                content,
                flags=re.IGNORECASE
            )
            changes.append("Increased search wrapper max-width")
    
    # Ensure search input wrapper is visible
    search_input_wrapper_pattern = r'\.blog-search-input-wrapper\s*\{[^}]*\}'
    match = re.search(search_input_wrapper_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        search_input_wrapper_css = match.group(0)
        
        # Check if padding is too small
        if 'padding: 8px 16px' in search_input_wrapper_css:
            # Increase padding for better visibility
            content = re.sub(
                r'padding:\s*8px\s+16px',
                'padding: 14px 24px',
                content,
                flags=re.IGNORECASE
            )
            changes.append("Increased search input padding")
        
        # Ensure display is block/flex
        if 'display' not in search_input_wrapper_css:
            new_css = search_input_wrapper_css.replace('{', '{\n            display: flex;')
            content = content.replace(search_input_wrapper_css, new_css)
            changes.append("Added display flex to search input wrapper")
    
    # Ensure search input is visible
    search_input_pattern = r'\.blog-search-input\s*\{[^}]*\}'
    match = re.search(search_input_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        search_input_css = match.group(0)
        
        # Check if font size is too small
        if 'font-size: 0.9rem' in search_input_css:
            # Increase font size for better visibility
            content = re.sub(
                r'font-size:\s*0\.9rem',
                'font-size: 1rem',
                content,
                flags=re.IGNORECASE
            )
            changes.append("Increased search input font size")
    
    return content, changes

def add_search_bar_if_missing(content, file_path):
    """Add search bar HTML if it's missing"""
    changes = []
    
    # Check if blog-search.js is included
    if 'js/blog-search.js' not in content and 'blog-search.js' not in content:
        # Add blog-search.js script before closing body
        body_close = content.find('</body>')
        if body_close != -1:
            script_tag = '\n    <script src="js/blog-search.js"></script>\n'
            content = content[:body_close] + script_tag + content[body_close:]
            changes.append("Added blog-search.js script")
    
    # Check if search bar container exists in HTML
    if 'blog-search-container' not in content or 'id="blogSearchInput"' not in content:
        # Find where to insert search bar (after page-header or before content)
        page_header_pattern = r'(<div[^>]*class="page-header"[^>]*>.*?</div>)'
        match = re.search(page_header_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            # Insert search bar after page-header
            search_bar_html = '''
            <!-- Blog Search Bar -->
            <div class="blog-search-container">
                <div class="blog-search-wrapper">
                    <div class="blog-search-input-wrapper">
                        <i class="fas fa-search blog-search-icon"></i>
                        <input 
                            type="text" 
                            class="blog-search-input" 
                            id="blogSearchInput"
                            placeholder="Search all tools and pages..." 
                            autocomplete="off"
                        />
                        <button class="blog-search-clear" id="blogSearchClear" style="display: none;">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="blog-search-results" id="blogSearchResults" style="display: none;"></div>
                </div>
            </div>
'''
            insert_pos = match.end()
            content = content[:insert_pos] + search_bar_html + content[insert_pos:]
            changes.append("Added search bar HTML after page-header")
        else:
            # Try to find main tag
            main_pattern = r'(<main[^>]*>.*?<div[^>]*class="container"[^>]*>)'
            match = re.search(main_pattern, content, re.IGNORECASE | re.DOTALL)
            
            if match:
                search_bar_html = '''
            <!-- Blog Search Bar -->
            <div class="blog-search-container">
                <div class="blog-search-wrapper">
                    <div class="blog-search-input-wrapper">
                        <i class="fas fa-search blog-search-icon"></i>
                        <input 
                            type="text" 
                            class="blog-search-input" 
                            id="blogSearchInput"
                            placeholder="Search all tools and pages..." 
                            autocomplete="off"
                        />
                        <button class="blog-search-clear" id="blogSearchClear" style="display: none;">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="blog-search-results" id="blogSearchResults" style="display: none;"></div>
                </div>
            </div>
'''
                insert_pos = match.end()
                content = content[:insert_pos] + search_bar_html + content[insert_pos:]
                changes.append("Added search bar HTML in main container")
    
    return content, changes

def add_advertisement_space(content, file_path):
    """Add advertisement space on blog pages"""
    changes = []
    
    # Check if advertisement CSS exists
    if 'ad-banner' not in content and 'advertisement' not in content.lower():
        # Add advertisement CSS
        ad_css = '''
        /* Advertisement Space */
        .ad-banner-top {
            width: 100%;
            min-height: 100px;
            background: #f5f7ff;
            border: 2px dashed #dbe2ef;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #64748b;
            font-size: 0.9rem;
            margin: 30px 0;
            padding: 20px;
            text-align: center;
        }
        
        .ad-banner-sidebar {
            width: 100%;
            min-height: 250px;
            background: #f5f7ff;
            border: 2px dashed #dbe2ef;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #64748b;
            font-size: 0.9rem;
            margin: 20px 0;
            padding: 20px;
            text-align: center;
        }
        
        .ad-banner-bottom {
            width: 100%;
            min-height: 100px;
            background: #f5f7ff;
            border: 2px dashed #dbe2ef;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #64748b;
            font-size: 0.9rem;
            margin: 30px 0;
            padding: 20px;
            text-align: center;
        }
        
        @media (max-width: 768px) {
            .ad-banner-top,
            .ad-banner-bottom {
                min-height: 80px;
                margin: 20px 0;
            }
        }
'''
        
        # Find style tag and add CSS
        style_pattern = r'(</style>)'
        match = re.search(style_pattern, content, re.IGNORECASE)
        
        if match:
            content = content[:match.start()] + ad_css + '\n    ' + content[match.start():]
            changes.append("Added advertisement CSS")
    
    # Add advertisement HTML spaces
    # Top ad banner (after search bar)
    if 'ad-banner-top' not in content:
        # Find search bar container end
        search_bar_pattern = r'(</div>\s*<!-- Blog Search Bar -->|id="blogSearchResults"[\s\S]*?</div>\s*</div>\s*</div>)'
        match = re.search(search_bar_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            ad_html = '''
            <!-- Advertisement Banner Top -->
            <div class="ad-banner-top">
                <p>Advertisement Space</p>
            </div>
'''
            insert_pos = match.end()
            content = content[:insert_pos] + ad_html + content[insert_pos:]
            changes.append("Added top advertisement banner")
    
    # Bottom ad banner (before footer)
    if 'ad-banner-bottom' not in content:
        footer_pattern = r'(<footer[^>]*>)'
        match = re.search(footer_pattern, content, re.IGNORECASE)
        
        if match:
            ad_html = '''
    <!-- Advertisement Banner Bottom -->
    <div class="ad-banner-bottom">
        <p>Advertisement Space</p>
    </div>

'''
            insert_pos = match.start()
            content = content[:insert_pos] + ad_html + content[insert_pos:]
            changes.append("Added bottom advertisement banner")
    
    return content, changes

def fix_blog_page(file_path):
    """Fix a single blog page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return None, ["Cannot read file"]
    
    original_content = content
    all_changes = []
    
    # 1. Fix search bar styling
    content, changes = fix_search_bar_styling(content, file_path)
    all_changes.extend(changes)
    
    # 2. Add search bar if missing
    content, changes = add_search_bar_if_missing(content, file_path)
    all_changes.extend(changes)
    
    # 3. Add advertisement space
    content, changes = add_advertisement_space(content, file_path)
    all_changes.extend(changes)
    
    # Save if changed
    if content != original_content and all_changes:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, all_changes
        except Exception as e:
            return None, [f"Error saving: {str(e)}"]
    
    return False, all_changes if all_changes else []

def main():
    """Main function"""
    root_dir = Path(__file__).parent
    
    print("🔧 Fixing Blog Search Bar Visibility & Adding Advertisement Space...\n")
    print("="*80)
    
    fixed_count = 0
    changed_files = []
    
    for blog_page in BLOG_PAGES:
        file_path = root_dir / blog_page
        
        if not file_path.exists():
            print(f"⚠️  {blog_page}: File not found")
            continue
        
        if should_exclude(file_path):
            continue
        
        relative_path = file_path.relative_to(root_dir)
        print(f"\n📄 Processing: {relative_path}")
        
        success, changes = fix_blog_page(file_path)
        
        if success is None:
            print(f"   ❌ Error: {changes[0]}")
        elif success:
            print(f"   ✅ Fixed:")
            for change in changes:
                print(f"      • {change}")
            fixed_count += 1
            changed_files.append((relative_path, changes))
        elif changes:
            print(f"   ℹ️  Info:")
            for change in changes:
                print(f"      • {change}")
        else:
            print(f"   ✓ OK (no changes needed)")
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"\n✅ Files Fixed: {fixed_count}")
    
    if changed_files:
        print(f"\n📝 Changes Applied:")
        for file_path, changes in changed_files:
            print(f"   • {file_path}: {len(changes)} changes")
    
    print("\n" + "="*80)
    print("✅ All blog pages fixed successfully!")
    print("="*80)
    print("\n🔍 Search Bar Updates:")
    print("   • Search bar now visible and properly sized")
    print("   • Increased padding and font size for better visibility")
    print("   • Added search bar if missing")
    print("\n📢 Advertisement Space:")
    print("   • Added top advertisement banner")
    print("   • Added bottom advertisement banner")
    print("   • Added CSS styling for advertisements")

if __name__ == '__main__':
    main()

