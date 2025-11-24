#!/usr/bin/env python3
"""
Remove Sign In and Signup buttons from header navigation on all HTML pages.
These buttons should only be in breadcrumb navigation, not in the header.
"""

import re
import os
from pathlib import Path

# Files to skip (test files, backups, server/public, etc.)
SKIP_PATTERNS = [
    'test-',
    'backup',
    'server/public',
    'excel-unlocker/templates',
    'result.html',
    'convert.html',
    '-convert.html',
    '-result.html',
    'workspace.html',
    'style.html'
]

def should_skip_file(file_path):
    """Check if file should be skipped."""
    file_str = str(file_path)
    return any(pattern in file_str for pattern in SKIP_PATTERNS)

def remove_auth_buttons_from_header(content):
    """Remove auth-buttons div from header section only."""
    # Pattern to match auth-buttons div in header (before user-menu or closing nav tag)
    # This pattern matches the entire auth-buttons div with its content
    patterns = [
        # Pattern 1: Standard auth-buttons div with Sign In and Signup
        (
            r'(\s*)<div\s+class=["\']auth-buttons["\']>.*?<a\s+href=["\']login\.html["\'].*?Sign\s+In.*?</a>.*?<a\s+href=["\']signup\.html["\'].*?Signup.*?</a>.*?</div>(\s*)',
            re.DOTALL
        ),
        # Pattern 2: Auth buttons with different structure
        (
            r'(\s*)<div\s+class=["\']auth-buttons["\']>.*?<a\s+class=["\']auth-link["\'].*?href=["\']login\.html["\'].*?Sign\s+In.*?</a>.*?<a\s+class=["\']auth-btn["\'].*?href=["\']signup\.html["\'].*?Signup.*?</a>.*?</div>(\s*)',
            re.DOTALL
        ),
        # Pattern 3: Auth buttons with Create Account text
        (
            r'(\s*)<div\s+class=["\']auth-buttons["\']>.*?<a\s+class=["\']auth-link["\'].*?href=["\']login\.html["\'].*?Sign\s+In.*?</a>.*?<a\s+class=["\']auth-btn["\'].*?href=["\']signup\.html["\'].*?Create\s+Account.*?</a>.*?</div>(\s*)',
            re.DOTALL
        ),
    ]
    
    original_content = content
    modified = False
    
    for pattern, flags in patterns:
        matches = list(re.finditer(pattern, content, flags))
        if matches:
            # Only remove if it's in the header section (before </nav> or </header>)
            for match in reversed(matches):  # Process in reverse to maintain positions
                start_pos = match.start()
                end_pos = match.end()
                
                # Check if this is in the header section
                # Look backwards for <header> or <nav class="navbar">
                before_match = content[:start_pos]
                after_match = content[end_pos:]
                
                # Check if we're inside a header/nav section
                header_start = max(
                    before_match.rfind('<header'),
                    before_match.rfind('<nav class="navbar"'),
                    before_match.rfind('<nav class=\'navbar\'')
                )
                
                # Check if we're before the closing nav/header tag
                nav_close = after_match.find('</nav>')
                header_close = after_match.find('</header>')
                
                # If we found header/nav start and we're before the closing tag, remove it
                if header_start != -1 and (nav_close != -1 or header_close != -1):
                    content = content[:start_pos] + content[end_pos:]
                    modified = True
                    print(f"   ✅ Removed auth-buttons from header")
                    break
    
    # Also remove any standalone auth-link or auth-btn that might be in header nav-links
    # But be careful - only remove if they're direct children of nav-links or navbar
    # This is a more conservative approach - only remove if clearly in header structure
    
    return content, modified

def process_file(file_path):
    """Process a single HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content, modified = remove_auth_buttons_from_header(content)
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"   ❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all HTML files."""
    html_files = list(Path('.').rglob('*.html'))
    processed = 0
    modified = 0
    
    print("Removing auth-buttons from headers...")
    print("=" * 60)
    
    for html_file in html_files:
        if should_skip_file(html_file):
            continue
        
        processed += 1
        print(f"\n[{processed}] Processing: {html_file}")
        
        if process_file(html_file):
            modified += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Processed: {processed} files")
    print(f"✅ Modified: {modified} files")
    print("=" * 60)

if __name__ == '__main__':
    main()
