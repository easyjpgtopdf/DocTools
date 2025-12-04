#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix all pages to have index page's header toolbar properly
- Remove old header tags and inline header styles
- Ensure global-header-placeholder exists
- Ensure global-components.js is loaded
- Ensure css/header.css is linked
"""

import os
import re
from pathlib import Path

# Pages to skip
SKIP_PAGES = [
    'index', 'blog', 'about', 'contact', 'disclaimer', 'dmca', 'privacy', 
    'terms', 'refund', 'kyc', 'attributions', 'accounts', 'login', 'signup', 
    'dashboard', 'pricing', 'payment', 'shipping', 'result', 'feedback'
]

def remove_old_header_tags(content):
    """Remove old <header> tags and their content"""
    # Remove complete header tags
    content = re.sub(r'<header[^>]*>.*?</header>', '', content, flags=re.DOTALL | re.IGNORECASE)
    return content

def remove_inline_header_styles(content):
    """Remove inline header-related CSS from <style> tags"""
    # Patterns for header-related CSS
    header_patterns = [
        r'header\s*\{[^}]*\}',
        r'\.navbar\s*\{[^}]*\}',
        r'\.nav-links\s*\{[^}]*\}',
        r'\.nav-links\s+a\s*\{[^}]*\}',
        r'\.logo\s*\{[^}]*\}',
        r'\.dropdown\s*\{[^}]*\}',
        r'\.dropdown-content\s*\{[^}]*\}',
        r'\.mobile-menu-toggle\s*\{[^}]*\}',
        r'@media[^{]*\{[^}]*\.nav-links[^}]*\}',
    ]
    
    # Find style tags
    style_pattern = r'(<style[^>]*>)(.*?)(</style>)'
    
    def clean_style(match):
        style_open = match.group(1)
        style_content = match.group(2)
        style_close = match.group(3)
        
        # Remove header-related CSS
        for pattern in header_patterns:
            style_content = re.sub(pattern, '', style_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Clean up multiple empty lines
        style_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', style_content)
        
        return style_open + style_content + style_close
    
    content = re.sub(style_pattern, clean_style, content, flags=re.DOTALL | re.IGNORECASE)
    return content

def ensure_header_placeholder(content):
    """Ensure global-header-placeholder exists right after <body>"""
    # Check if placeholder exists
    if 'global-header-placeholder' in content:
        # Make sure it's right after <body>
        body_pattern = r'(<body[^>]*>)(\s*)(<div[^>]*id="global-header-placeholder"[^>]*>)'
        if not re.search(body_pattern, content, re.IGNORECASE):
            # Remove existing placeholder
            content = re.sub(r'<div[^>]*id="global-header-placeholder"[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
            # Add it after body
            content = re.sub(r'(<body[^>]*>)', r'\1\n    <div id="global-header-placeholder"></div>', content, flags=re.IGNORECASE)
    else:
        # Add placeholder after body
        content = re.sub(r'(<body[^>]*>)', r'\1\n    <div id="global-header-placeholder"></div>', content, flags=re.IGNORECASE)
    
    return content

def ensure_global_components_script(content):
    """Ensure global-components.js is loaded before </body>"""
    # Check if script exists
    if 'global-components.js' not in content:
        # Add before </body>
        body_end = content.rfind('</body>')
        if body_end > 0:
            # Check if there's already a script tag before </body>
            before_body = content[:body_end].rstrip()
            if not before_body.endswith('</script>'):
                script_tag = '\n    <script src="js/global-components.js" defer></script>'
                content = content[:body_end] + script_tag + '\n' + content[body_end:]
    else:
        # Make sure it's before </body> and has defer attribute
        script_pattern = r'<script[^>]*src=["\']js/global-components\.js["\'][^>]*>'
        if not re.search(script_pattern, content, re.IGNORECASE):
            # Script exists but might be malformed, fix it
            content = re.sub(
                r'<script[^>]*src=["\']js/global-components\.js["\'][^>]*>',
                '<script src="js/global-components.js" defer></script>',
                content,
                flags=re.IGNORECASE
            )
    
    return content

def ensure_header_css(content):
    """Ensure css/header.css is linked in <head>"""
    if 'css/header.css' not in content:
        # Add before </head>
        head_end = content.find('</head>')
        if head_end > 0:
            link_tag = '    <link rel="stylesheet" href="css/header.css">\n'
            content = content[:head_end] + link_tag + content[head_end:]
    return content

def fix_page(filepath):
    """Fix a single page"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Step 1: Remove old header tags
        content = remove_old_header_tags(content)
        
        # Step 2: Remove inline header styles
        content = remove_inline_header_styles(content)
        
        # Step 3: Ensure header placeholder
        content = ensure_header_placeholder(content)
        
        # Step 4: Ensure global-components.js
        content = ensure_global_components_script(content)
        
        # Step 5: Ensure header.css
        content = ensure_header_css(content)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "updated"
        else:
            return False, "no changes needed"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    print("=" * 70)
    print("Fix All Pages - Index Page Header Toolbar")
    print("=" * 70)
    print()
    
    # Get all HTML files
    html_files = [f for f in Path('.').glob('*.html') 
                  if not any(skip in f.name.lower() for skip in SKIP_PAGES)]
    
    updated_count = 0
    no_change_count = 0
    error_count = 0
    
    for filepath in sorted(html_files):
        print(f"Processing: {filepath.name}...", end=' ')
        
        success, message = fix_page(filepath)
        
        if success:
            print(f"[UPDATED - {message}]")
            updated_count += 1
        else:
            if "error" in message:
                print(f"[ERROR - {message}]")
                error_count += 1
            else:
                print(f"[OK - {message}]")
                no_change_count += 1
    
    print()
    print("=" * 70)
    print("Summary:")
    print(f"  Updated: {updated_count} pages")
    print(f"  No Changes Needed: {no_change_count} pages")
    if error_count > 0:
        print(f"  Errors: {error_count} pages")
    print("=" * 70)

if __name__ == '__main__':
    main()






