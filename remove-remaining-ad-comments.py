#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove remaining advertisement comments"""

import os
import re
import glob

BLOG_PAGES = glob.glob("blog-*.html")

def remove_ad_comments(html_content):
    """Remove all advertisement comments"""
    
    removed = []
    
    # Remove HTML comments with advertisement
    patterns = [
        r'<!--\s*Advertisement[^>]*-->',
        r'<!--\s*Ad[^>]*Banner[^>]*-->',
        r'<!--\s*Ad[^>]*Space[^>]*-->',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)
            removed.append(f"Removed {len(matches)} ad comment(s)")
    
    return html_content, removed

def main():
    print("🧹 Removing remaining advertisement comments...\n")
    
    total_removed = 0
    for page_file in BLOG_PAGES:
        if os.path.exists(page_file):
            try:
                with open(page_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original = content
                content, removed = remove_ad_comments(content)
                
                if content != original or removed:
                    with open(page_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    if removed:
                        print(f"   ✅ Cleaned {page_file}")
                        for item in removed:
                            print(f"      - {item}")
                        total_removed += len(removed)
            except Exception as e:
                print(f"   ❌ Error cleaning {page_file}: {e}")
    
    print(f"\n✅ Removed {total_removed} advertisement comments!")

if __name__ == "__main__":
    main()

