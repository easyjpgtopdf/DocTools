#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix header loading on all tool pages - ensure global-components.js loads properly
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

def fix_page_header_loading(filepath):
    """Fix header loading for a single page"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to find global-components.js script
        script_pattern = r'<script[^>]*src=["\']js/global-components\.js["\'][^>]*>'
        
        # Check if script exists
        if re.search(script_pattern, content, re.IGNORECASE):
            # Ensure it has defer attribute
            if 'defer' not in re.search(script_pattern, content, re.IGNORECASE).group(0):
                content = re.sub(
                    r'(<script[^>]*src=["\']js/global-components\.js["\'])([^>]*>)',
                    r'\1 defer\2',
                    content,
                    flags=re.IGNORECASE
                )
            
            # Check if initialization script already exists
            if 'loadGlobalHeader' not in content or '// Ensure header loads' not in content:
                # Add initialization script right after global-components.js
                # Find the script tag and add init script after it
                body_end = content.rfind('</body>')
                if body_end > 0:
                    # Check if there's already an init script
                    before_body = content[:body_end]
                    if '// Ensure header loads' not in before_body:
                        init_script = '''
    <script>
    // Ensure header loads even if script loads late
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof loadGlobalHeader === 'function') {
                loadGlobalHeader();
            }
        });
    } else {
        if (typeof loadGlobalHeader === 'function') {
            loadGlobalHeader();
        }
    }
    </script>'''
                        content = content[:body_end] + init_script + '\n' + content[body_end:]
        else:
            # Script doesn't exist, add it
            body_end = content.rfind('</body>')
            if body_end > 0:
                script_tag = '\n    <script src="js/global-components.js" defer></script>'
                init_script = '''
    <script>
    // Ensure header loads even if script loads late
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof loadGlobalHeader === 'function') {
                loadGlobalHeader();
            }
        });
    } else {
        if (typeof loadGlobalHeader === 'function') {
            loadGlobalHeader();
        }
    }
    </script>'''
                content = content[:body_end] + script_tag + init_script + '\n' + content[body_end:]
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "fixed header loading"
        else:
            return False, "no changes needed"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    print("=" * 70)
    print("Fix Header Loading on All Tool Pages")
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
        
        success, message = fix_page_header_loading(filepath)
        
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






