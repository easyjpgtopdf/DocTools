#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1. Fix header loading issue on tool pages
2. Fix excel-unlocker link to point to index.html
"""

import re
from pathlib import Path

def fix_header_loading_issue(filepath):
    """Fix header loading - ensure script executes immediately"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if global-header-placeholder exists
        if 'global-header-placeholder' not in content:
            return False, "no header placeholder"
        
        # Find the initialization script
        init_script_pattern = r'// Ensure header loads even if script loads late.*?</script>'
        
        # Replace with a more robust version that executes immediately
        new_init_script = '''    <script>
    // Force header to load immediately
    (function() {
        function initHeader() {
            if (typeof loadGlobalHeader === 'function') {
                loadGlobalHeader();
            } else {
                // Wait for script to load
                setTimeout(initHeader, 100);
            }
        }
        
        // Try immediately
        initHeader();
        
        // Also on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initHeader);
        } else {
            setTimeout(initHeader, 50);
        }
    })();
    </script>'''
        
        # Check if old init script exists
        if re.search(init_script_pattern, content, re.DOTALL):
            content = re.sub(init_script_pattern, new_init_script, content, flags=re.DOTALL)
        else:
            # Add before </body>
            body_end = content.rfind('</body>')
            if body_end > 0:
                content = content[:body_end] + new_init_script + '\n' + content[body_end:]
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "fixed header loading"
        else:
            return False, "no changes needed"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def fix_excel_unlocker_links():
    """Fix excel-unlocker links in global-components.js"""
    filepath = Path('js/global-components.js')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace excel-unlocker/ with excel-unlocker/index.html
        content = re.sub(
            r'href=["\']excel-unlocker/["\']',
            'href="excel-unlocker/index.html"',
            content,
            flags=re.IGNORECASE
        )
        
        # Remove target="_blank" if present
        content = re.sub(
            r'href=["\']excel-unlocker/index\.html["\'][^>]*target=["\']_blank["\']',
            'href="excel-unlocker/index.html"',
            content,
            flags=re.IGNORECASE
        )
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "fixed excel-unlocker links"
        else:
            return False, "no changes needed"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    print("=" * 70)
    print("Fix Header Loading & Excel Unlocker Link")
    print("=" * 70)
    print()
    
    # Fix excel-unlocker links first
    print("1. Fixing excel-unlocker links...")
    success, message = fix_excel_unlocker_links()
    if success:
        print(f"   ✓ {message}")
    else:
        print(f"   - {message}")
    
    print()
    print("2. Fixing header loading on tool pages...")
    
    # Get all HTML files (tool pages)
    skip_pages = ['index', 'blog', 'about', 'contact', 'disclaimer', 'dmca', 
                  'privacy', 'terms', 'refund', 'kyc', 'attributions', 'accounts', 
                  'login', 'signup', 'dashboard', 'pricing', 'payment', 'shipping', 
                  'result', 'feedback']
    
    html_files = [f for f in Path('.').glob('*.html') 
                  if not any(skip in f.name.lower() for skip in skip_pages)]
    
    updated_count = 0
    no_change_count = 0
    error_count = 0
    
    for filepath in sorted(html_files):
        print(f"   Processing: {filepath.name}...", end=' ')
        
        success, message = fix_header_loading_issue(filepath)
        
        if success:
            print(f"[UPDATED]")
            updated_count += 1
        else:
            if "error" in message:
                print(f"[ERROR - {message}]")
                error_count += 1
            else:
                print(f"[OK]")
                no_change_count += 1
    
    print()
    print("=" * 70)
    print("Summary:")
    print(f"  Excel Links Fixed: {fix_excel_unlocker_links()[0]}")
    print(f"  Header Loading Fixed: {updated_count} pages")
    print(f"  No Changes Needed: {no_change_count} pages")
    if error_count > 0:
        print(f"  Errors: {error_count} pages")
    print("=" * 70)

if __name__ == '__main__':
    main()



