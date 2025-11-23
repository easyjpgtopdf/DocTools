#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove AdSense Verified and Google Approved Badges
- Remove from trust-badges section
- Remove from all pages
"""

import os
import re
import glob

ALL_HTML = glob.glob("*.html")

def remove_adsense_badges(html_content):
    """Remove AdSense Verified and Google Approved badges"""
    
    removed = []
    
    # Pattern to match the entire AdSense Verified badge div
    adsense_badge_pattern = r'<div[^>]*style="[^"]*display:\s*flex[^"]*align-items:\s*center[^"]*gap:\s*10px[^"]*">\s*<i[^>]*class="[^"]*fa-check-circle[^"]*"[^>]*>.*?</i>\s*<div[^>]*style="[^"]*text-align:\s*left[^"]*">\s*<div[^>]*style="[^"]*color:\s*#0b1630[^"]*font-weight:\s*600[^"]*font-size:\s*1\.1rem[^"]*">\s*AdSense\s+Verified\s*</div>\s*<div[^>]*style="[^"]*color:\s*#56607a[^"]*font-size:\s*0\.9rem[^"]*">\s*Google\s+Approved\s*</div>\s*</div>\s*</div>'
    
    # Try to match and remove
    if re.search(adsense_badge_pattern, html_content, re.IGNORECASE | re.DOTALL):
        html_content = re.sub(adsense_badge_pattern, '', html_content, flags=re.IGNORECASE | re.DOTALL)
        removed.append("Removed AdSense Verified badge")
    
    # Also try simpler pattern - just the text
    simple_patterns = [
        (r'AdSense\s+Verified', 'AdSense Verified text'),
        (r'Google\s+Approved', 'Google Approved text'),
    ]
    
    for pattern, desc in simple_patterns:
        if re.search(pattern, html_content, re.IGNORECASE):
            # Remove the entire badge div containing this text
            # Match div with AdSense Verified or Google Approved
            badge_div_pattern = r'<div[^>]*>[\s\S]*?' + pattern + r'[\s\S]*?</div>'
            matches = re.findall(badge_div_pattern, html_content, re.IGNORECASE)
            if matches:
                html_content = re.sub(badge_div_pattern, '', html_content, flags=re.IGNORECASE)
                removed.append(f"Removed {desc}")
    
    # More specific: Remove the third badge in trust-badges (AdSense one)
    # This is a more targeted approach
    trust_badges_pattern = r'(<div class="trust-badges"[^>]*>[\s\S]*?)(<div[^>]*style="[^"]*display:\s*flex[^"]*align-items:\s*center[^"]*gap:\s*10px[^"]*">[\s\S]*?AdSense\s+Verified[\s\S]*?</div>)([\s\S]*?</div>)'
    
    def remove_adsense_from_trust_badges(match):
        before = match.group(1)
        adsense_badge = match.group(2)
        after = match.group(3)
        # Remove the AdSense badge but keep the structure
        return before + after
    
    if re.search(trust_badges_pattern, html_content, re.IGNORECASE | re.DOTALL):
        html_content = re.sub(trust_badges_pattern, remove_adsense_from_trust_badges, html_content, flags=re.IGNORECASE | re.DOTALL)
        removed.append("Removed AdSense badge from trust-badges section")
    
    return html_content, removed

def main():
    print("🧹 Removing AdSense Verified and Google Approved badges...\n")
    
    total_removed = 0
    for file_path in ALL_HTML:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original = content
                content, removed = remove_adsense_badges(content)
                
                if content != original or removed:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    if removed:
                        print(f"   ✅ Cleaned {file_path}")
                        for item in removed:
                            print(f"      - {item}")
                        total_removed += len(removed)
            except Exception as e:
                print(f"   ❌ Error cleaning {file_path}: {e}")
    
    print(f"\n✅ Removed {total_removed} AdSense badges!")
    print("\n📝 All AdSense Verified and Google Approved badges removed!")

if __name__ == "__main__":
    main()

