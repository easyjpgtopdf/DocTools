#!/usr/bin/env python3
"""
Add voice-assistant.js script to all blog pages
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

def add_voice_assistant_js(file_path):
    """Add voice-assistant.js script if not present"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return None, ["Cannot read file"]
    
    original_content = content
    changes = []
    
    # Check if voice-assistant.js is already loaded
    if 'voice-assistant.js' in content:
        return False, ["Already has voice-assistant.js"]
    
    # Find where to add it (after blog-search.js, before auth.js module)
    pattern = r'(<script src="js/blog-search\.js"></script>)(\s*)(<script type="module">)'
    match = re.search(pattern, content)
    
    if match:
        # Add voice-assistant.js after blog-search.js
        replacement = match.group(1) + '\n    \n    <!-- Voice Assistant Script -->\n    <script src="js/voice-assistant.js"></script>' + match.group(2) + match.group(3)
        content = content[:match.start()] + replacement + content[match.end():]
        changes.append("Added voice-assistant.js script")
    
    # Save if changed
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        except Exception as e:
            return None, [f"Error saving: {str(e)}"]
    
    return False, changes if changes else []

def main():
    """Main function"""
    root_dir = Path(__file__).parent
    
    print("🔧 Adding voice-assistant.js to all blog pages...\n")
    print("="*80)
    
    fixed_count = 0
    
    for blog_page in BLOG_PAGES:
        file_path = root_dir / blog_page
        
        if not file_path.exists():
            print(f"⚠️  {blog_page}: File not found")
            continue
        
        relative_path = file_path.relative_to(root_dir)
        print(f"\n📄 Processing: {relative_path}")
        
        success, changes = add_voice_assistant_js(file_path)
        
        if success is None:
            print(f"   ❌ Error: {changes[0]}")
        elif success:
            print(f"   ✅ Fixed:")
            for change in changes:
                print(f"      • {change}")
            fixed_count += 1
        else:
            print(f"   ✓ {changes[0] if changes else 'OK (no changes needed)'}")
    
    # Summary
    print("\n" + "="*80)
    print(f"✅ Added voice-assistant.js to {fixed_count} files")
    print("="*80)

if __name__ == '__main__':
    main()

