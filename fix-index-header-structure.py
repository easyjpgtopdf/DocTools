#!/usr/bin/env python3
"""
Fix index.html header - ensure it matches blog pages structure
Remove any duplicate or broken header code
"""

import os
import re

def get_correct_header():
    """Get correct header structure from blog page"""
    blog_file = "blog-how-to-use-jpg-to-pdf.html"
    if not os.path.exists(blog_file):
        return None
    
    with open(blog_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract header section
    header_match = re.search(r'(<header[^>]*>.*?</header>)', content, re.DOTALL | re.IGNORECASE)
    if header_match:
        return header_match.group(1)
    return None

def fix_index_header():
    """Fix index.html header"""
    if not os.path.exists("index.html"):
        print("❌ index.html not found")
        return False
    
    with open("index.html", 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Get correct header from blog page
    correct_header = get_correct_header()
    if not correct_header:
        print("⚠️  Could not get correct header from blog page")
        # Use the existing header but ensure it's correct
        header_match = re.search(r'(<header[^>]*>.*?</header>)', content, re.DOTALL | re.IGNORECASE)
        if header_match:
            existing_header = header_match.group(1)
            # Check if it has proper structure
            if 'navbar' in existing_header and 'nav-links' in existing_header:
                print("✅ Existing header looks correct")
                return False
    
    # Find and replace header in index.html
    header_pattern = r'<header[^>]*>.*?</header>'
    headers = list(re.finditer(header_pattern, content, re.DOTALL | re.IGNORECASE))
    
    if len(headers) > 1:
        print(f"⚠️  Found {len(headers)} headers - removing duplicates")
        # Keep first, remove others
        for header_match in headers[1:]:
            content = content[:header_match.start()] + content[header_match.end():]
        print("✅ Removed duplicate headers")
    
    # Replace header with correct one if needed
    if correct_header:
        header_match = re.search(header_pattern, content, re.DOTALL | re.IGNORECASE)
        if header_match:
            existing_header = header_match.group(0)
            # Compare - if different, replace
            if existing_header != correct_header:
                # But keep mobile menu overlay from index if it exists
                mobile_menu_match = re.search(r'(<!-- Mobile Menu Overlay -->.*?</div>\s*</div>)', content, re.DOTALL)
                mobile_menu = mobile_menu_match.group(1) if mobile_menu_match else ""
                
                # Replace header
                content = content[:header_match.start()] + correct_header + content[header_match.end():]
                
                # Ensure mobile menu is after header
                if mobile_menu and '<!-- Mobile Menu Overlay -->' not in content[header_match.end():header_match.end()+500]:
                    # Add mobile menu after header
                    header_end = content.find('</header>') + len('</header>')
                    content = content[:header_end] + '\n    ' + mobile_menu + '\n' + content[header_end:]
                
                print("✅ Replaced header with correct structure")
    
    # Ensure header.css is linked (should be in head)
    if '<link rel="stylesheet" href="css/header.css">' not in content:
        # Add before closing head
        head_close = content.find('</head>')
        if head_close > 0:
            header_css = '    <link rel="stylesheet" href="css/header.css">\n'
            content = content[:head_close] + header_css + content[head_close:]
            print("✅ Added header.css link")
    
    # Remove any duplicate header.css links
    header_css_pattern = r'<link[^>]*header\.css[^>]*>'
    css_links = list(re.finditer(header_css_pattern, content, re.IGNORECASE))
    if len(css_links) > 1:
        print(f"⚠️  Found {len(css_links)} header.css links - keeping first")
        for css_link in css_links[1:]:
            content = content[:css_link.start()] + content[css_link.end():]
        print("✅ Removed duplicate header.css links")
    
    if content != original_content:
        with open("index.html", 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Fixed index.html header")
        return True
    else:
        print("ℹ️  Header already correct")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("FIXING INDEX.HTML HEADER STRUCTURE")
    print("=" * 80)
    print()
    fix_index_header()
    print()
    print("=" * 80)

