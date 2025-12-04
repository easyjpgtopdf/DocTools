#!/usr/bin/env python3
"""
Fix broken progressLabel IDs in PDF conversion tools
"""

import re
from pathlib import Path

files_to_fix = [
    'pdf-to-jpg.html',
    'pdf-to-excel.html',
    'pdf-to-ppt.html'
]

def fix_broken_progress_label(file_path):
    """Fix broken progressLabel ID that's split across lines"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: <div class="muted" id="progre\n    \nssLabel">
        pattern1 = r'<div class="muted" id="progre\s+ssLabel">'
        replacement1 = '<div class="muted" id="progressLabel">'
        content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
        
        # Pattern 2: <span id="progre\n    \nssLabel">
        pattern2 = r'<span id="progre\s+ssLabel">'
        replacement2 = '<span id="progressLabel">'
        content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
        
        # Also add null checks to setProgress functions
        if 'function setProgress' in content:
            # Add null checks for progressLabel, progressBar, progressWrapper, progressPercent
            # Pattern: progressLabel.textContent (without null check)
            pattern3 = r'(progressLabel\.textContent\s*=)'
            replacement3 = r'if (progressLabel) \1'
            content = re.sub(pattern3, replacement3, content)
            
            pattern4 = r'(progressBar\.style\.width\s*=)'
            replacement4 = r'if (progressBar) \1'
            content = re.sub(pattern4, replacement4, content)
            
            pattern5 = r'(progressWrapper\.style\.display\s*=)'
            replacement5 = r'if (progressWrapper) \1'
            content = re.sub(pattern5, replacement5, content)
            
            pattern6 = r'(progressPercent\.textContent\s*=)'
            replacement6 = r'if (progressPercent) \1'
            content = re.sub(pattern6, replacement6, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed {file_path}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False

def main():
    base_dir = Path('.')
    fixed_count = 0
    
    print("Fixing broken progressLabel IDs...\n")
    
    for file_name in files_to_fix:
        file_path = base_dir / file_name
        if not file_path.exists():
            print(f"⚠ {file_name} not found, skipping...")
            continue
        
        if fix_broken_progress_label(file_path):
            fixed_count += 1
    
    print(f"\n✓ Fixed {fixed_count} files")

if __name__ == '__main__':
    main()

