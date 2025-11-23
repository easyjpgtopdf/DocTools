#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove AI Math Master and Shop Apna Online Links from All Pages
- Remove from header dropdown menus
- Remove from all HTML files
"""

import os
import re
import glob

ALL_HTML = glob.glob("*.html")

def remove_external_links(html_content):
    """Remove AI Math Master and Shop Apna Online links"""
    
    removed = []
    
    # Pattern to match the links
    patterns = [
        (r'<a[^>]*href="https://apnaonlineservic\.com"[^>]*>.*?Shop-ApnaOnline.*?</a>', 'Shop-ApnaOnline link'),
        (r'<a[^>]*href="https://aimathmaster\.com"[^>]*>.*?AI-Math Master.*?</a>', 'AI-Math Master link'),
        (r'<a[^>]*href="https://apnaonlineservic\.com"[^>]*target="_blank"[^>]*>.*?</a>', 'Shop-ApnaOnline link (any text)'),
        (r'<a[^>]*href="https://aimathmaster\.com"[^>]*target="_blank"[^>]*>.*?</a>', 'AI-Math Master link (any text)'),
    ]
    
    for pattern, desc in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if matches:
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL)
            removed.append(f"Removed {desc}")
    
    # Also remove any div or section containing these links
    # Remove empty dropdown items or sections
    html_content = re.sub(r'<div[^>]*>\s*<a[^>]*href="https://(apnaonlineservic|aimathmaster)\.com"[^>]*>.*?</a>\s*</div>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up empty lines
    html_content = re.sub(r'\n{3,}', '\n\n', html_content)
    
    return html_content, removed

def main():
    print("🧹 Removing AI Math Master and Shop Apna Online links from all pages...\n")
    
    total_removed = 0
    files_cleaned = []
    
    for file_path in ALL_HTML:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original = content
                content, removed = remove_external_links(content)
                
                if content != original or removed:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    if removed:
                        files_cleaned.append((file_path, removed))
                        total_removed += len(removed)
                        print(f"   ✅ Cleaned {file_path}")
                        for item in removed:
                            print(f"      - {item}")
            except Exception as e:
                print(f"   ❌ Error cleaning {file_path}: {e}")
    
    print(f"\n✅ Removed {total_removed} links from {len(files_cleaned)} files!")
    print("\n📝 All AI Math Master and Shop Apna Online links removed!")

if __name__ == "__main__":
    main()

