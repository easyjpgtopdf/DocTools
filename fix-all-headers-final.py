#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix header loading on all tool pages - remove defer and add proper initialization
"""

import re
from pathlib import Path

def fix_header_script(filepath):
    """Fix header script loading"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove defer attribute from global-components.js
        content = re.sub(
            r'<script src="js/global-components\.js" defer></script>',
            '<script src="js/global-components.js"></script>',
            content,
            flags=re.IGNORECASE
        )
        
        # Replace the initialization script with a simpler, more reliable version
        old_init_pattern = r'<script>\s*// Force header to load immediately.*?</script>'
        new_init_script = '''    <script>
    // Ensure header loads - call after script loads
    if (typeof loadGlobalHeader === 'function') {
        loadGlobalHeader();
    } else {
        // Wait for script to load
        var checkHeader = setInterval(function() {
            if (typeof loadGlobalHeader === 'function') {
                loadGlobalHeader();
                clearInterval(checkHeader);
            }
        }, 50);
        // Stop checking after 2 seconds
        setTimeout(function() { clearInterval(checkHeader); }, 2000);
    }
    </script>'''
        
        if re.search(old_init_pattern, content, re.DOTALL):
            content = re.sub(old_init_pattern, new_init_script, content, flags=re.DOTALL)
        else:
            # Add before </body> if not exists
            body_end = content.rfind('</body>')
            if body_end > 0 and 'loadGlobalHeader' not in content:
                content = content[:body_end] + new_init_script + '\n' + content[body_end:]
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "fixed"
        else:
            return False, "no changes"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    skip_pages = ['index', 'blog', 'about', 'contact', 'disclaimer', 'dmca', 
                  'privacy', 'terms', 'refund', 'kyc', 'attributions', 'accounts', 
                  'login', 'signup', 'dashboard', 'pricing', 'payment', 'shipping', 
                  'result', 'feedback']
    
    html_files = [f for f in Path('.').glob('*.html') 
                  if not any(skip in f.name.lower() for skip in skip_pages)]
    
    fixed_count = 0
    for filepath in sorted(html_files):
        success, message = fix_header_script(filepath)
        if success:
            fixed_count += 1
            print(f"Fixed: {filepath.name}")
    
    print(f"\nTotal fixed: {fixed_count} pages")

if __name__ == '__main__':
    main()






