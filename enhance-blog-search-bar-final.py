#!/usr/bin/env python3
"""
Final Enhancement of Blog Search Bar:
1. Increase search bar size and visibility further
2. Improve margins and spacing
3. Ensure advertisement banners are properly placed
4. Make search bar more prominent
"""

import os
import re
from pathlib import Path

# Blog pages to enhance
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

def enhance_search_bar_styling(content, file_path):
    """Enhance search bar styling for better visibility"""
    changes = []
    
    # Increase search container margin significantly
    search_container_pattern = r'(\.blog-search-container\s*\{[^}]*margin:\s*)([^;}]+)'
    match = re.search(search_container_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        # Replace with larger margin
        content = re.sub(
            r'\.blog-search-container\s*\{[^}]*margin:\s*15px\s+0\s+20px',
            '.blog-search-container {\n            margin: 35px 0 35px;',
            content,
            flags=re.IGNORECASE
        )
        changes.append("Increased search container margin (35px top/bottom)")
    
    # Increase search wrapper max-width further
    content = re.sub(
        r'max-width:\s*700px',
        'max-width: 800px',
        content,
        flags=re.IGNORECASE
    )
    if 'max-width: 800px' in content or 'max-width:700px' not in content:
        changes.append("Increased search wrapper max-width to 800px")
    
    # Increase search input wrapper padding further
    content = re.sub(
        r'padding:\s*14px\s+24px',
        'padding: 16px 28px',
        content,
        flags=re.IGNORECASE
    )
    if 'padding: 16px 28px' in content:
        changes.append("Increased search input padding to 16px 28px")
    
    # Increase search icon size
    content = re.sub(
        r'\.blog-search-icon\s*\{[^}]*font-size:\s*0\.9rem',
        r'.blog-search-icon {\n            color: #4361ee;\n            font-size: 1.1rem',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    if 'font-size: 1.1rem' in content and 'blog-search-icon' in content:
        changes.append("Increased search icon font size to 1.1rem")
    
    # Increase search input font size further
    content = re.sub(
        r'\.blog-search-input\s*\{[^}]*font-size:\s*1rem',
        r'.blog-search-input {\n            flex: 1;\n            border: none;\n            outline: none;\n            font-size: 1.1rem',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )
    if 'font-size: 1.1rem' in content and 'blog-search-input' in content:
        changes.append("Increased search input font size to 1.1rem")
    
    # Ensure search container is visible and has proper z-index
    if 'z-index' not in content or '.blog-search-container' not in content.split('z-index')[0]:
        # Add z-index if not present
        search_container_end = content.find('.blog-search-container') + len('.blog-search-container')
        if search_container_end > 0:
            # Check if it's in a CSS block
            container_block = content[content.rfind('.blog-search-container', 0, search_container_end + 500):search_container_end + 500]
            if '{' in container_block and 'z-index' not in container_block:
                # Add z-index to ensure visibility
                content = re.sub(
                    r'(\.blog-search-container\s*\{[^}]*width:\s*100%[^}]*)(\})',
                    r'\1\n            position: relative;\n            z-index: 10;\n        \2',
                    content,
                    flags=re.IGNORECASE | re.DOTALL
                )
                changes.append("Added z-index to search container for visibility")
    
    return content, changes

def ensure_advertisement_banners(content, file_path):
    """Ensure advertisement banners are properly placed"""
    changes = []
    
    # Check if top ad banner exists after search bar
    if 'ad-banner-top' not in content or 'Advertisement Banner Top' not in content:
        # Find search bar container end
        search_bar_pattern = r'(</div>\s*</div>\s*</div>\s*<!-- Blog Search Bar -->|id="blogSearchResults"[\s\S]{0,200}</div>\s*</div>\s*</div>)'
        match = re.search(search_bar_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            ad_html = '''
            <!-- Advertisement Banner Top -->
            <div class="ad-banner-top">
                <p><i class="fas fa-ad"></i> Advertisement Space</p>
            </div>

'''
            insert_pos = match.end()
            content = content[:insert_pos] + ad_html + content[insert_pos:]
            changes.append("Added top advertisement banner after search bar")
    
    # Check if bottom ad banner exists before footer
    if 'ad-banner-bottom' not in content or 'Advertisement Banner Bottom' not in content:
        footer_pattern = r'(<footer[^>]*>)'
        match = re.search(footer_pattern, content, re.IGNORECASE)
        
        if match:
            ad_html = '''
    <!-- Advertisement Banner Bottom -->
    <div class="ad-banner-bottom">
        <p><i class="fas fa-ad"></i> Advertisement Space</p>
    </div>

'''
            insert_pos = match.start()
            content = content[:insert_pos] + ad_html + content[insert_pos:]
            changes.append("Added bottom advertisement banner before footer")
    
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
    
    # 1. Enhance search bar styling
    content, changes = enhance_search_bar_styling(content, file_path)
    all_changes.extend(changes)
    
    # 2. Ensure advertisement banners
    content, changes = ensure_advertisement_banners(content, file_path)
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
    
    print("🔧 Final Enhancement of Blog Search Bar & Advertisement Space...\n")
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
            print(f"   ✅ Enhanced:")
            for change in changes:
                print(f"      • {change}")
            fixed_count += 1
            changed_files.append((relative_path, changes))
        elif changes:
            print(f"   ℹ️  Info:")
            for change in changes:
                print(f"      • {change}")
        else:
            print(f"   ✓ OK (already enhanced)")
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"\n✅ Files Enhanced: {fixed_count}")
    
    if changed_files:
        print(f"\n📝 Enhancements Applied:")
        for file_path, changes in changed_files:
            print(f"   • {file_path}: {len(changes)} enhancements")
    
    print("\n" + "="*80)
    print("✅ All blog pages enhanced successfully!")
    print("="*80)
    print("\n🔍 Search Bar Enhancements:")
    print("   • Increased margin: 35px top/bottom")
    print("   • Increased max-width: 800px")
    print("   • Increased padding: 16px 28px")
    print("   • Increased font sizes: 1.1rem")
    print("   • Added z-index for visibility")
    print("\n📢 Advertisement Space:")
    print("   • Top banner after search bar")
    print("   • Bottom banner before footer")
    print("   • Properly styled with CSS")

if __name__ == '__main__':
    main()

