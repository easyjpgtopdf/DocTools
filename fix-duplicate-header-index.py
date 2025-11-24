#!/usr/bin/env python3
"""
Fix duplicate/broken header in index.html
Keep the original correct header, remove duplicate/broken one
"""

import os
import re

def fix_index_header():
    """Fix duplicate header in index.html"""
    if not os.path.exists("index.html"):
        print("❌ index.html not found")
        return False
    
    with open("index.html", 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Find all header sections
    header_pattern = r'<header[^>]*>.*?</header>'
    headers = list(re.finditer(header_pattern, content, re.DOTALL | re.IGNORECASE))
    
    print(f"Found {len(headers)} header sections")
    
    if len(headers) > 1:
        # Keep the first header (original), remove others
        print("⚠️  Multiple headers found - keeping first, removing duplicates")
        
        # Get the first header (original)
        first_header = headers[0]
        first_header_content = first_header.group(0)
        
        # Check if first header has proper structure
        if 'navbar' in first_header_content and 'nav-links' in first_header_content:
            print("✅ First header looks correct - keeping it")
            
            # Remove all other headers
            for i, header_match in enumerate(headers[1:], 1):
                print(f"   Removing duplicate header #{i+1}")
                content = content[:header_match.start()] + content[header_match.end():]
        else:
            # First header might be broken, check second
            if len(headers) >= 2:
                second_header = headers[1]
                second_header_content = second_header.group(0)
                
                if 'navbar' in second_header_content and 'nav-links' in second_header_content:
                    print("✅ Second header looks correct - keeping it, removing first")
                    # Remove first header, keep second
                    content = content[:first_header.start()] + content[first_header.end():]
                    # Remove remaining headers
                    for i, header_match in enumerate(headers[2:], 2):
                        print(f"   Removing duplicate header #{i+1}")
                        content = content[:header_match.start()] + content[header_match.end():]
    
    # Also check for duplicate header CSS links
    header_css_pattern = r'<link[^>]*header\.css[^>]*>'
    css_links = list(re.finditer(header_css_pattern, content, re.IGNORECASE))
    
    if len(css_links) > 1:
        print(f"⚠️  Found {len(css_links)} header.css links - keeping first")
        # Keep first, remove others
        for css_link in css_links[1:]:
            print(f"   Removing duplicate header.css link")
            content = content[:css_link.start()] + content[css_link.end():]
    
    # Ensure header.css is linked in head section
    if '<link rel="stylesheet" href="css/header.css">' not in content:
        # Add it before closing head tag
        head_close = content.find('</head>')
        if head_close > 0:
            header_css_link = '    <link rel="stylesheet" href="css/header.css">\n'
            content = content[:head_close] + header_css_link + content[head_close:]
            print("✅ Added missing header.css link")
    
    # Check for broken header structure
    # Ensure only one header tag exists
    header_open_count = content.count('<header')
    header_close_count = content.count('</header>')
    
    if header_open_count != header_close_count:
        print(f"⚠️  Header tag mismatch: {header_open_count} opening, {header_close_count} closing")
        # Try to fix
        if header_open_count > header_close_count:
            # Add missing closing tags
            missing = header_open_count - header_close_count
            # Find last header and add closing tags
            last_header_pos = content.rfind('<header')
            if last_header_pos > 0:
                # Find where header should close (before next section)
                next_section = content.find('<main', last_header_pos)
                if next_section < 0:
                    next_section = content.find('<section', last_header_pos)
                if next_section < 0:
                    next_section = content.find('</body', last_header_pos)
                
                if next_section > 0:
                    # Insert closing tags before next section
                    closing_tags = '</div>\n    </header>' * missing
                    content = content[:next_section] + closing_tags + '\n    ' + content[next_section:]
                    print(f"✅ Fixed header tag mismatch")
    
    if content != original_content:
        with open("index.html", 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Fixed index.html header")
        return True
    else:
        print("ℹ️  No changes needed")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("FIXING DUPLICATE/BROKEN HEADER IN INDEX.HTML")
    print("=" * 80)
    print()
    fix_index_header()
    print()
    print("=" * 80)

