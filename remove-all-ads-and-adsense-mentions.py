#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove All Advertisement Sections and AdSense Approval Mentions
- Remove ad banner sections
- Remove advertisement placeholders
- Remove AdSense approval text
- Clean up blog pages
"""

import os
import re
import glob

BLOG_PAGES = glob.glob("blog-*.html")
MAIN_PAGES = ["blog-articles.html", "blog-tutorials.html", "blog.html"]

def remove_ads_and_mentions(html_content):
    """Remove all ad sections and AdSense mentions"""
    
    removed_items = []
    
    # 1. Remove advertisement banner sections
    ad_patterns = [
        # Ad banner divs
        (r'<div[^>]*class="[^"]*ad-banner[^"]*"[^>]*>[\s\S]*?</div>', 'Ad banner div'),
        (r'<div[^>]*class="[^"]*advertisement[^"]*"[^>]*>[\s\S]*?</div>', 'Advertisement div'),
        (r'<div[^>]*class="[^"]*ad-space[^"]*"[^>]*>[\s\S]*?</div>', 'Ad space div'),
        (r'<div[^>]*style="[^"]*ad-banner[^"]*"[^>]*>[\s\S]*?</div>', 'Ad banner style'),
        (r'<div[^>]*style="[^"]*advertisement[^"]*"[^>]*>[\s\S]*?</div>', 'Advertisement style'),
        # Ad banner comments
        (r'<!--\s*Advertisement[^>]*-->[\s\S]*?<!--\s*/Advertisement[^>]*-->', 'Ad comment block'),
        (r'<!--\s*Ad[^>]*Banner[^>]*-->[\s\S]*?<!--\s*/Ad[^>]*Banner[^>]*-->', 'Ad banner comment'),
        # Ad placeholder text
        (r'<p[^>]*>[\s\S]*?Advertisement Space[\s\S]*?</p>', 'Ad placeholder text'),
        (r'<p[^>]*>[\s\S]*?Advertisement[\s\S]*?</p>', 'Ad text'),
        (r'<div[^>]*>[\s\S]*?Advertisement Space[\s\S]*?</div>', 'Ad space text'),
    ]
    
    for pattern, description in ad_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)
            removed_items.append(f"Removed {description}")
    
    # 2. Remove AdSense approval mentions
    adsense_patterns = [
        (r'adsense\s+approval', 'AdSense approval text'),
        (r'AdSense\s+approval', 'AdSense Approval text'),
        (r'adsense\s+compliant', 'AdSense compliant text'),
        (r'AdSense\s+compliant', 'AdSense Compliant text'),
        (r'adsense\s+ready', 'AdSense ready text'),
        (r'AdSense\s+ready', 'AdSense Ready text'),
        (r'adsense\s+supportive', 'AdSense supportive text'),
        (r'AdSense\s+supportive', 'AdSense Supportive text'),
        (r'google\s+adsense', 'Google AdSense text'),
        (r'Google\s+AdSense', 'Google AdSense text'),
        (r'adsense\s+compatible', 'AdSense compatible text'),
        (r'AdSense\s+compatible', 'AdSense Compatible text'),
    ]
    
    for pattern, description in adsense_patterns:
        # Find and remove lines containing these patterns
        lines = html_content.split('\n')
        new_lines = []
        for line in lines:
            if not re.search(pattern, line, re.IGNORECASE):
                new_lines.append(line)
            else:
                removed_items.append(f"Removed {description}")
        html_content = '\n'.join(new_lines)
    
    # 3. Remove specific ad banner sections by ID or class
    specific_ads = [
        r'<div[^>]*id="[^"]*ad[^"]*"[^>]*>[\s\S]*?</div>',
        r'<section[^>]*class="[^"]*ad[^"]*"[^>]*>[\s\S]*?</section>',
        r'<div[^>]*class="[^"]*ad-banner-top[^"]*"[^>]*>[\s\S]*?</div>',
        r'<div[^>]*class="[^"]*ad-banner-bottom[^"]*"[^>]*>[\s\S]*?</div>',
    ]
    
    for pattern in specific_ads:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE)
            removed_items.append("Removed specific ad section")
    
    # 4. Remove CSS for ads
    ad_css_patterns = [
        r'\.ad-banner[^\{]*\{[^\}]*\}',
        r'\.advertisement[^\{]*\{[^\}]*\}',
        r'\.ad-space[^\{]*\{[^\}]*\}',
        r'\.ad-banner-top[^\{]*\{[^\}]*\}',
        r'\.ad-banner-bottom[^\{]*\{[^\}]*\}',
    ]
    
    for pattern in ad_css_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            html_content = re.sub(pattern, '', html_content, flags=re.IGNORECASE | re.MULTILINE)
            removed_items.append("Removed ad CSS")
    
    # 5. Clean up empty lines (more than 2 consecutive)
    html_content = re.sub(r'\n{3,}', '\n\n', html_content)
    
    return html_content, removed_items

def main():
    print("🧹 Removing all advertisements and AdSense mentions...\n")
    
    total_removed = 0
    for page_file in BLOG_PAGES + MAIN_PAGES:
        if os.path.exists(page_file):
            try:
                with open(page_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                original = content
                content, removed = remove_ads_and_mentions(content)
                
                if content != original or removed:
                    with open(page_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"   ✅ Cleaned {page_file}")
                    for item in removed:
                        print(f"      - {item}")
                    total_removed += len(removed)
            except Exception as e:
                print(f"   ❌ Error cleaning {page_file}: {e}")
    
    print(f"\n✅ Removed {total_removed} advertisement sections and mentions!")
    print("\n📝 Cleaned:")
    print("   ✓ All ad banner sections")
    print("   ✓ Advertisement placeholders")
    print("   ✓ AdSense approval mentions")
    print("   ✓ Ad-related CSS")
    print("   ✓ Ad-related comments")

if __name__ == "__main__":
    main()

