#!/usr/bin/env python3
"""
Fix Blog Pages Layout:
1. Delete "Coming Soon" panels from all blog pages
2. Make search box smaller and compact
3. Reduce margin height
4. Reduce overall frame height
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

def remove_coming_soon_panel(content):
    """Remove Coming Soon panel from content"""
    changes = []
    
    # Remove Coming Soon HTML section
    coming_soon_patterns = [
        r'<div[^>]*class="coming-soon"[^>]*>.*?</div>\s*</div>',  # With closing div
        r'<section[^>]*class="coming-soon"[^>]*>.*?</section>',
        r'<div[^>]*class="coming-soon"[^>]*>.*?</div>',
    ]
    
    for pattern in coming_soon_patterns:
        matches = list(re.finditer(pattern, content, re.IGNORECASE | re.DOTALL))
        if matches:
            # Remove all matches (reverse order to maintain positions)
            for match in reversed(matches):
                content = content[:match.start()] + content[match.end():]
                changes.append(f"Removed Coming Soon panel")
    
    # Remove Coming Soon CSS
    coming_soon_css_patterns = [
        r'/\* Coming Soon Message \*/.*?\.coming-soon\s*\{[^}]*\}.*?\.coming-soon[^{]*\{[^}]*\}.*?\.coming-soon[^{]*\{[^}]*\}',
        r'\.coming-soon\s*\{[^}]*padding[^}]*\}',
    ]
    
    for pattern in coming_soon_css_patterns:
        matches = list(re.finditer(pattern, content, re.IGNORECASE | re.DOTALL))
        if matches:
            for match in reversed(matches):
                content = content[:match.start()] + content[match.end():]
                changes.append(f"Removed Coming Soon CSS")
    
    # Remove individual .coming-soon CSS rules
    css_rules_to_remove = [
        r'\.coming-soon\s*\{[^}]*\}',
        r'\.coming-soon\s+[^{]+\{[^}]*\}',
        r'\.notify-btn\s*\{[^}]*\}',
        r'\.notify-btn\s*:\w+\s*\{[^}]*\}',
    ]
    
    for pattern in css_rules_to_remove:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
    
    return content, changes

def make_search_box_compact(content):
    """Make search box smaller and compact"""
    changes = []
    
    # Reduce search container margin
    search_container_patterns = [
        (r'\.blog-search-container\s*\{[^}]*margin:\s*30px\s+0\s+40px[^}]*\}', 
         r'.blog-search-container {\n            margin: 15px 0 20px;\n            width: 100%;\n        }'),
        (r'\.blog-search-container\s*\{[^}]*margin[^}]*\}', 
         r'.blog-search-container {\n            margin: 15px 0 20px;\n            width: 100%;\n        }'),
    ]
    
    for pattern, replacement in search_container_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            changes.append("Reduced search container margin")
            break
    
    # Reduce search wrapper max-width
    wrapper_pattern = r'\.blog-search-wrapper\s*\{[^}]*max-width:\s*800px[^}]*\}'
    if re.search(wrapper_pattern, content, re.IGNORECASE):
        content = re.sub(
            r'max-width:\s*800px',
            'max-width: 600px',
            content,
            flags=re.IGNORECASE
        )
        changes.append("Reduced search wrapper max-width")
    
    # Reduce search input padding
    input_wrapper_pattern = r'\.blog-search-input-wrapper\s*\{[^}]*padding:\s*12px\s+20px[^}]*\}'
    if re.search(input_wrapper_pattern, content, re.IGNORECASE):
        content = re.sub(
            r'padding:\s*12px\s+20px',
            'padding: 8px 16px',
            content,
            flags=re.IGNORECASE
        )
        changes.append("Reduced search input padding")
    
    # Reduce search icon size and margin
    icon_size_pattern = r'\.blog-search-icon\s*\{[^}]*font-size:\s*1\.2rem[^}]*\}'
    if re.search(icon_size_pattern, content, re.IGNORECASE):
        content = re.sub(
            r'font-size:\s*1\.2rem',
            'font-size: 1rem',
            content,
            flags=re.IGNORECASE
        )
        changes.append("Reduced search icon font size")
    
    icon_margin_pattern = r'\.blog-search-icon\s*\{[^}]*margin-right:\s*12px[^}]*\}'
    if re.search(icon_margin_pattern, content, re.IGNORECASE):
        content = re.sub(
            r'margin-right:\s*12px',
            'margin-right: 10px',
            content,
            flags=re.IGNORECASE
        )
        changes.append("Reduced search icon margin")
    
    # Reduce search input font size
    input_pattern = r'\.blog-search-input\s*\{[^}]*font-size:\s*1rem[^}]*\}'
    if re.search(input_pattern, content, re.IGNORECASE):
        content = re.sub(
            r'font-size:\s*1rem',
            'font-size: 0.9rem',
            content,
            flags=re.IGNORECASE
        )
        changes.append("Reduced search input font size")
    
    return content, changes

def reduce_frame_height(content):
    """Reduce overall frame height and margins"""
    changes = []
    
    # Reduce main padding
    main_pattern = r'main\s*\{[^}]*padding:\s*40px\s+24px[^}]*\}'
    if re.search(main_pattern, content, re.IGNORECASE):
        content = re.sub(
            r'padding:\s*40px\s+24px',
            'padding: 24px 24px',
            content,
            flags=re.IGNORECASE
        )
        changes.append("Reduced main padding")
    
    # Reduce page header margin-bottom
    header_patterns = [
        r'\.page-header\s*\{[^}]*margin-bottom:\s*50px[^}]*\}',
        r'\.blog-header\s*\{[^}]*margin-bottom:\s*50px[^}]*\}',
    ]
    
    for pattern in header_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            content = re.sub(
                r'margin-bottom:\s*50px',
                'margin-bottom: 24px',
                content,
                flags=re.IGNORECASE
            )
            changes.append("Reduced page header margin-bottom")
            break
    
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
    
    # 1. Remove Coming Soon panel
    content, changes = remove_coming_soon_panel(content)
    all_changes.extend(changes)
    
    # 2. Make search box compact
    content, changes = make_search_box_compact(content)
    all_changes.extend(changes)
    
    # 3. Reduce frame height
    content, changes = reduce_frame_height(content)
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
    
    print("🔧 Fixing Blog Pages Layout...\n")
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

if __name__ == '__main__':
    main()

