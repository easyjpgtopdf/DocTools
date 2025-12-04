#!/usr/bin/env python3
"""
Fix all HTML pages to have robust header loading script
Ensures header and footer load properly on all pages
"""

import os
import re
from pathlib import Path

# Robust header loading script (from jpg-to-pdf-convert.html)
ROBUST_HEADER_SCRIPT = '''    <script>
    // Ensure header loads - multiple attempts to guarantee it works
    (function() {
        function tryLoadHeader() {
            if (typeof loadGlobalHeader === 'function') {
                try {
                    loadGlobalHeader();
                    return true;
                } catch (e) {
                    console.error('Error calling loadGlobalHeader:', e);
                }
            }
            return false;
        }
        
        // Try immediately if script already loaded
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            if (!tryLoadHeader()) {
                // Script not loaded yet, wait for it
                var attempts = 0;
                var maxAttempts = 60; // 3 seconds total
                var checkHeader = setInterval(function() {
                    attempts++;
                    if (tryLoadHeader() || attempts >= maxAttempts) {
                        clearInterval(checkHeader);
                    }
                }, 50);
            }
        } else {
            // Wait for DOM to be ready
            document.addEventListener('DOMContentLoaded', function() {
                if (!tryLoadHeader()) {
                    var attempts = 0;
                    var maxAttempts = 40;
                    var checkHeader = setInterval(function() {
                        attempts++;
                        if (tryLoadHeader() || attempts >= maxAttempts) {
                            clearInterval(checkHeader);
                        }
                    }, 50);
                }
            });
        }
        
        // Final backup attempt on window load
        window.addEventListener('load', function() {
            setTimeout(function() {
                if (!document.querySelector('header') && typeof loadGlobalHeader === 'function') {
                    loadGlobalHeader();
                }
            }, 100);
        });
    })();
    </script>'''

def has_robust_header_script(content):
    """Check if page has robust header loading script"""
    # Check for the robust script pattern
    robust_patterns = [
        r'// Ensure header loads - multiple attempts',
        r'var maxAttempts = 60.*// 3 seconds total',
        r'window\.addEventListener\([\'"]load[\'"].*loadGlobalHeader'
    ]
    return any(re.search(pattern, content, re.DOTALL) for pattern in robust_patterns)

def fix_page(file_path):
    """Fix a single HTML page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Skip if no header placeholder
        if 'global-header-placeholder' not in content:
            return False, 'No header placeholder'
        
        # Skip if no global-components.js
        if 'global-components.js' not in content:
            return False, 'No global-components.js'
        
        # Check if already has robust script
        if has_robust_header_script(content):
            return False, 'Already has robust script'
        
        # Find where to insert the script (after global-components.js)
        script_pattern = r'(<script\s+src=["\']js/global-components\.js["\']></script>)'
        if re.search(script_pattern, content):
            # Remove old simple header loading scripts
            old_patterns = [
                r'<script>\s*// Ensure.*?loadGlobalHeader.*?</script>',
                r'<script>\s*if\s*\(typeof\s+loadGlobalHeader.*?</script>',
            ]
            
            for pattern in old_patterns:
                content = re.sub(pattern, '', content, flags=re.DOTALL)
            
            # Insert robust script after global-components.js
            replacement = r'\1\n' + ROBUST_HEADER_SCRIPT
            new_content = re.sub(script_pattern, replacement, content)
            
            if new_content != content:
                content = new_content
                modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, 'Fixed'
        else:
            return False, 'No changes needed'
            
    except Exception as e:
        return False, f'Error: {str(e)}'

def main():
    """Main function"""
    root_dir = Path('.')
    html_files = list(root_dir.glob('*.html'))
    
    # Exclude certain files
    exclude_patterns = ['test-', 'backup', 'server/', 'excel-unlocker/']
    html_files = [f for f in html_files if not any(pat in str(f) for pat in exclude_patterns)]
    
    print(f"Found {len(html_files)} HTML files to check\n")
    
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    for html_file in sorted(html_files):
        result, message = fix_page(html_file)
        if result:
            print(f"✅ Fixed: {html_file.name}")
            fixed_count += 1
        elif 'Error' in message:
            print(f"❌ Error: {html_file.name} - {message}")
            error_count += 1
        else:
            skipped_count += 1
    
    print(f"\n{'='*50}")
    print(f"Fixed: {fixed_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()

