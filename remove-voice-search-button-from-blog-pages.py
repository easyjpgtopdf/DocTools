#!/usr/bin/env python3
"""
Remove Voice Search Button from All Blog Pages
Keep only Jarvis Voice Assistant (main voice assistant button)
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

def remove_voice_search_button(content, file_path):
    """Remove voice search button container, keep only Jarvis voice assistant"""
    changes = []
    
    # Find and remove the voice search button container
    # This is the container with "Voice Search" text that we added
    voice_search_pattern = r'<!-- Jarvis Voice Assistant Button -->\s*<div class="voice-assistant-container"[^>]*style="text-align: center; margin: 15px 0;">.*?</div>\s*</div>'
    
    match = re.search(voice_search_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        content = content[:match.start()] + content[match.end():]
        changes.append("Removed voice search button container")
    
    # Also check for simpler pattern - the voice assistant container with Voice Search text
    voice_search_pattern2 = r'<div class="voice-assistant-container"[^>]*style="text-align: center; margin: 15px 0;">\s*<button id="voiceAssistantBtn"[^>]*>.*?Voice Search.*?</button>.*?</div>'
    
    match = re.search(voice_search_pattern2, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        content = content[:match.start()] + content[match.end():]
        if "Removed voice search button container" not in changes:
            changes.append("Removed voice search button container (pattern 2)")
    
    # Alternative: Remove the specific voice search button with text "Voice Search"
    # Keep the main Jarvis voice assistant button (which is loaded via voice-assistant.js)
    # The main voice assistant button is created by voice-assistant.js and doesn't need HTML
    
    # Remove any HTML button with "Voice Search" text that we manually added
    voice_search_html = r'<!-- Jarvis Voice Assistant Button -->\s*<div[^>]*voice-assistant-container[^>]*>.*?Voice Search.*?</button>.*?</div>\s*</div>'
    
    match = re.search(voice_search_html, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        content = content[:match.start()] + content[match.end():]
        if "Removed voice search button container" not in changes:
            changes.append("Removed voice search button HTML")
    
    # Make sure we're not removing the main voice assistant (which is added by JS)
    # The main voice assistant is created dynamically by voice-assistant.js
    # We only want to remove the manual "Voice Search" button we added
    
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
    
    # Remove voice search button
    content, changes = remove_voice_search_button(content, file_path)
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
    
    print("🔧 Removing Voice Search Button from Blog Pages...\n")
    print("="*80)
    print("Keeping only Jarvis Voice Assistant (main voice assistant)\n")
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
            print(f"   ✓ OK (no voice search button found)")
    
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
    print("✅ Voice search button removed successfully!")
    print("="*80)
    print("\n🎤 Voice Assistant Status:")
    print("   ✅ Jarvis Voice Assistant (main) - KEPT")
    print("   ❌ Voice Search Button - REMOVED")
    print("\n📝 Note:")
    print("   • Jarvis Voice Assistant is loaded via voice-assistant.js")
    print("   • It creates the main voice assistant button automatically")
    print("   • No additional HTML button needed")

if __name__ == '__main__':
    main()

