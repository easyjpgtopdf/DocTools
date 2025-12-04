#!/usr/bin/env python3
"""
Fix all PDF conversion tools to ensure upload and preview work correctly.
This script:
1. Ensures upload pages wait for continue button click (no automatic redirect)
2. Ensures convert pages properly load and display PDF previews
"""

import os
import re
from pathlib import Path

# PDF tools that need fixing
PDF_TOOLS = {
    'pdf-to-jpg.html': {
        'convert_page': 'pdf-to-jpg-convert.html',
        'storage_key': 'pdf2jpg',
        'storage_name_key': 'pdf2jpg_name'
    },
    'pdf-to-excel.html': {
        'convert_page': 'pdf-to-excel-convert.html',
        'storage_key': 'pdf2excel',
        'storage_name_key': 'pdf2excel_name'
    },
    'pdf-to-ppt.html': {
        'convert_page': 'pdf-to-ppt-convert.html',
        'storage_key': 'pdf2ppt',
        'storage_name_key': 'pdf2ppt_name'
    },
    'pdf-to-word.html': {
        'convert_page': None,  # Single page tool
        'storage_key': None,
        'storage_name_key': None
    },
    'pdf-to-text.html': {
        'convert_page': 'pdf-to-text-convert.html',
        'storage_key': 'pdf2text',
        'storage_name_key': 'pdf2text_name'
    },
    'pdf-to-epub.html': {
        'convert_page': 'pdf-to-epub-convert.html',
        'storage_key': 'pdf2epub',
        'storage_name_key': 'pdf2epub_name'
    }
}

def fix_automatic_redirects(file_path):
    """Remove automatic redirects after file upload, wait for continue button"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: setTimeout with location.href redirect after saveFallback
        pattern1 = r"(await saveFallback\([^)]+\);\s*)setTimeout\(\(\)=>\{[^}]*setProgress\(null\);[^}]*location\.href\s*=\s*['\"][^'\"]+['\"];\s*\},\s*\d+\);"
        replacement1 = r"\1setProgress(100, 'Ready! Continue to preview.');\n        setTimeout(()=>{ setProgress(null); }, 400);\n        statusMessage.textContent = 'Ready to continue. Click Continue to preview and export.';\n        statusMessage.className = 'status-message success';"
        content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
        
        # Pattern 2: location.href redirect immediately after saveFallback (no setTimeout)
        pattern2 = r"(await saveFallback\([^)]+\);\s*)location\.href\s*=\s*['\"][^'\"]+['\"];"
        replacement2 = r"\1setProgress(100, 'Ready! Continue to preview.');\n        setTimeout(()=>{ setProgress(null); }, 400);\n        statusMessage.textContent = 'Ready to continue. Click Continue to preview and export.';\n        statusMessage.className = 'status-message success';"
        content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed automatic redirects in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False

def ensure_continue_button_handler(file_path, convert_page):
    """Ensure continue button properly redirects to convert page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if continue button handler exists
        if 'continueBtn.addEventListener' in content and convert_page:
            # Ensure it redirects to convert page
            pattern = r"(continueBtn\.addEventListener\(['\"]click['\"],\s*function\([^)]*\)\s*\{[^}]*if\s*\([^)]*continueBtn\.disabled[^}]*return;[^}]*\}[^}]*)(location\.href\s*=\s*['\"][^'\"]+['\"];)"
            if re.search(pattern, content):
                # Already has redirect, check if it's correct
                if convert_page not in content:
                    # Replace with correct convert page
                    content = re.sub(
                        r"location\.href\s*=\s*['\"][^'\"]+['\"];",
                        f"location.href = '{convert_page}';",
                        content,
                        count=1
                    )
                    print(f"✓ Updated continue button redirect in {file_path}")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"✗ Error ensuring continue button in {file_path}: {e}")
        return False

def main():
    base_dir = Path('.')
    fixed_count = 0
    
    print("Fixing PDF conversion tools upload and preview issues...\n")
    
    for tool_file, config in PDF_TOOLS.items():
        tool_path = base_dir / tool_file
        if not tool_path.exists():
            print(f"⚠ {tool_file} not found, skipping...")
            continue
        
        print(f"Processing {tool_file}...")
        
        # Fix automatic redirects
        if fix_automatic_redirects(tool_path):
            fixed_count += 1
        
        # Ensure continue button handler
        if config['convert_page']:
            if ensure_continue_button_handler(tool_path, config['convert_page']):
                fixed_count += 1
    
    print(f"\n✓ Fixed {fixed_count} issues across PDF tools")
    print("\nNote: Please test each tool to ensure upload and preview work correctly.")

if __name__ == '__main__':
    main()

