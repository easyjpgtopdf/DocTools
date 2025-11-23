#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove AdSense Verified and Google Approved Badges from All Pages
"""

import os
import re
import glob

ALL_HTML = glob.glob("*.html")

def remove_adsense_badge_div(html_content):
    """Remove the entire AdSense Verified badge div"""
    
    # Pattern to match the entire badge div
    # This matches the div containing "AdSense Verified" and "Google Approved"
    pattern = r'<div[^>]*style="[^"]*display:\s*flex[^"]*align-items:\s*center[^"]*gap:\s*10px[^"]*">\s*<i[^>]*class="[^"]*fa-check-circle[^"]*"[^>]*>.*?</i>\s*<div[^>]*style="[^"]*text-align:\s*left[^"]*">\s*<div[^>]*style="[^"]*color:\s*#0b1630[^"]*font-weight:\s*600[^"]*font-size:\s*1\.1rem[^"]*">\s*AdSense\s+Verified\s*</div>\s*<div[^>]*style="[^"]*color:\s*#56607a[^"]*font-size:\s*0\.9rem[^"]*">\s*Google\s+Approved\s*</div>\s*</div>\s*</div>'
    
    # Try multiline match
    matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
    if matches:
        html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
        return html_content, len(matches)
    
    # Simpler pattern - match the div structure more flexibly
    # Match from <div with display:flex to </div> containing AdSense Verified
    simpler_pattern = r'<div[^>]*style="[^"]*display:\s*flex[^"]*align-items:\s*center[^"]*gap:\s*10px[^"]*"[^>]*>[\s\S]*?AdSense\s+Verified[\s\S]*?Google\s+Approved[\s\S]*?</div>\s*</div>'
    
    matches = re.findall(simpler_pattern, html_content, re.IGNORECASE | re.DOTALL)
    if matches:
        html_content = re.sub(simpler_pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL)
        return html_content, len(matches)
    
    # Even simpler - just find the div containing both texts
    very_simple = r'<div[^>]*>[\s\S]*?AdSense\s+Verified[\s\S]*?Google\s+Approved[\s\S]*?</div>'
    matches = re.findall(very_simple, html_content, re.IGNORECASE | re.DOTALL)
    if matches:
        # Be more careful - only remove if it's the trust badge div
        for match in matches:
            if 'fa-check-circle' in match or 'trust-badges' in html_content[:html_content.find(match)+1000]:
                html_content = re.sub(re.escape(match), '', html_content, flags=re.IGNORECASE | re.DOTALL)
                return html_content, 1
    
    return html_content, 0

def main():
    print("🧹 Removing AdSense Verified and Google Approved badges from all pages...\n")
    
    total_removed = 0
    files_cleaned = []
    
    for file_path in ALL_HTML:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original = content
                content, removed_count = remove_adsense_badge_div(content)
                
                if content != original and removed_count > 0:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    files_cleaned.append((file_path, removed_count))
                    total_removed += removed_count
                    print(f"   ✅ Cleaned {file_path} ({removed_count} badge(s) removed)")
            except Exception as e:
                print(f"   ❌ Error cleaning {file_path}: {e}")
    
    print(f"\n✅ Removed {total_removed} AdSense badges from {len(files_cleaned)} files!")
    print("\n📝 All AdSense Verified and Google Approved badges removed!")

if __name__ == "__main__":
    main()

