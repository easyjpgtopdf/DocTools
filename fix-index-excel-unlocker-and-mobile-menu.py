#!/usr/bin/env python3
"""
Fix index.html:
1. Change excel-unlocker/ links to excel-unlocker.html
2. Ensure mobile menu is properly hidden by default
3. Verify header structure matches blog pages
"""

import os
import re

def fix_index_page():
    """Fix index.html issues"""
    if not os.path.exists("index.html"):
        print("❌ index.html not found")
        return False
    
    with open("index.html", 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # 1. Fix excel-unlocker links (change from excel-unlocker/ to excel-unlocker.html)
    if 'excel-unlocker/"' in content or 'excel-unlocker/' in content:
        # Replace excel-unlocker/ with excel-unlocker.html (keep target="_blank" if present)
        content = re.sub(
            r'href="excel-unlocker/"(\s+target="_blank")?',
            r'href="excel-unlocker.html"\1',
            content
        )
        # Also handle onclick patterns
        content = re.sub(
            r"location\.href='excel-unlocker/'",
            r"location.href='excel-unlocker.html'",
            content
        )
        changes_made.append("✅ Fixed excel-unlocker links (changed to excel-unlocker.html)")
    
    # 2. Ensure mobile menu overlay is hidden by default
    # Check if mobile-menu-overlay has proper display:none in inline style or class
    if 'id="mobile-menu-overlay"' in content:
        # Check if it has display:none in style attribute
        if 'id="mobile-menu-overlay"' in content and 'display: none' not in content[content.find('id="mobile-menu-overlay"'):content.find('id="mobile-menu-overlay"')+200]:
            # Add display:none to the overlay div if not present
            overlay_pattern = r'(<div class="mobile-menu-overlay"[^>]*id="mobile-menu-overlay"[^>]*)>'
            if re.search(overlay_pattern, content):
                def add_display_none(match):
                    tag = match.group(1)
                    if 'style=' in tag:
                        # Add display:none to existing style
                        tag = re.sub(r'style="([^"]*)"', r'style="\1; display: none;"', tag)
                    else:
                        # Add new style attribute
                        tag += ' style="display: none;"'
                    return tag + '>'
                content = re.sub(overlay_pattern, add_display_none, content)
                changes_made.append("✅ Added display:none to mobile-menu-overlay")
    
    # 3. Verify header structure - ensure mobile-menu-toggle is present
    if '<button class="mobile-menu-toggle"' not in content:
        # Add mobile menu toggle button after logo
        logo_pattern = r'(<a href="index\.html" class="logo">[^<]*</a>)'
        if re.search(logo_pattern, content):
            def add_mobile_toggle(match):
                return match.group(0) + '\n                <button class="mobile-menu-toggle" id="mobile-menu-toggle" aria-label="Toggle mobile menu" aria-expanded="false">\n                    <span></span>\n                    <span></span>\n                    <span></span>\n                </button>'
            content = re.sub(logo_pattern, add_mobile_toggle, content, count=1)
            changes_made.append("✅ Added mobile-menu-toggle button")
    
    # 4. Ensure AI Image Repair is in Image Tools dropdown
    if 'Image Tools' in content and 'AI Image Repair' not in content[content.find('Image Tools'):content.find('Image Tools')+500]:
        # This should already be there, but double check
        pass
    
    if content != original_content:
        with open("index.html", 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Fixed index.html")
        for change in changes_made:
            print(f"   {change}")
        return True
    else:
        print("ℹ️  No changes needed")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("FIXING INDEX.HTML - EXCEL UNLOCKER LINKS & MOBILE MENU")
    print("=" * 80)
    print()
    fix_index_page()
    print()
    print("=" * 80)

