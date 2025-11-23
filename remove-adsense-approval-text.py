#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove AdSense Approval Text from All Files
- Remove from HTML files
- Remove from MD files
- Remove any mentions
"""

import os
import re
import glob

ALL_HTML = glob.glob("*.html")
ALL_MD = glob.glob("*.md")

def remove_adsense_mentions(content, file_path):
    """Remove AdSense approval mentions"""
    
    removed = []
    
    # Patterns to remove
    patterns = [
        (r'adsense\s+approval', 'AdSense approval'),
        (r'AdSense\s+approval', 'AdSense Approval'),
        (r'adsense\s+compliant', 'AdSense compliant'),
        (r'AdSense\s+compliant', 'AdSense Compliant'),
        (r'adsense\s+ready', 'AdSense ready'),
        (r'AdSense\s+ready', 'AdSense Ready'),
        (r'adsense\s+supportive', 'AdSense supportive'),
        (r'AdSense\s+supportive', 'AdSense Supportive'),
        (r'adsense\s+compatible', 'AdSense compatible'),
        (r'AdSense\s+compatible', 'AdSense Compatible'),
        (r'google\s+adsense', 'Google AdSense'),
        (r'Google\s+AdSense', 'Google AdSense'),
        (r'for\s+adsense', 'for AdSense'),
        (r'For\s+AdSense', 'For AdSense'),
    ]
    
    # Remove lines containing these patterns
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        should_keep = True
        for pattern, desc in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                should_keep = False
                removed.append(f"Removed line with {desc}")
                break
        if should_keep:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Also remove from comments
    for pattern, desc in patterns:
        content = re.sub(
            r'<!--\s*[^>]*' + pattern.replace('\\s+', '\\s+') + r'[^>]*-->',
            '',
            content,
            flags=re.IGNORECASE
        )
    
    return content, removed

def main():
    print("🧹 Removing AdSense approval mentions...\n")
    
    total_removed = 0
    all_files = ALL_HTML + ALL_MD
    
    for file_path in all_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original = content
                content, removed = remove_adsense_mentions(content, file_path)
                
                if content != original or removed:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"   ✅ Cleaned {file_path}")
                    for item in removed[:3]:  # Show first 3
                        print(f"      - {item}")
                    if len(removed) > 3:
                        print(f"      ... and {len(removed) - 3} more")
                    total_removed += len(removed)
            except Exception as e:
                print(f"   ❌ Error cleaning {file_path}: {e}")
    
    print(f"\n✅ Removed {total_removed} AdSense mentions!")
    print("\n📝 All AdSense approval text removed from:")
    print("   ✓ HTML files")
    print("   ✓ Markdown files")
    print("   ✓ Comments")
    print("   ✓ Content text")

if __name__ == "__main__":
    main()

