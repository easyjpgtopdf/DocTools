#!/usr/bin/env python3
"""
Update all footer copyright notices to include "All rights reserved"
Format: "© easyjpgtopdf — Free PDF & Image Tools for everyone. All rights reserved."
"""

import os
import re
from pathlib import Path

# Standard copyright text
NEW_COPYRIGHT = "© easyjpgtopdf — Free PDF & Image Tools for everyone. All rights reserved."

# Patterns to match and replace
COPYRIGHT_PATTERNS = [
    # Current format without "All rights reserved"
    r'©\s*easyjpgtopdf\s*—\s*Free\s+PDF\s+&\s+Image\s+Tools\s+for\s+everyone\.',
    r'&copy;\s*easyjpgtopdf\s*&mdash;\s*Free\s+PDF\s+&amp;\s+Image\s+Tools\s+for\s+everyone\.',
    r'©\s*easyjpgtopdf\s*—\s*Free\s+PDF\s+&amp;\s+Image\s+Tools\s+for\s+everyone\.',
    r'&copy;\s*easyjpgtopdf\s*—\s*Free\s+PDF\s+&amp;\s+Image\s+Tools\s+for\s+everyone\.',
    # With HTML entities variations
    r'©\s*easyjpgtopdf\s*—\s*Free\s+PDF\s+&amp;\s+Image\s+Tools\s+for\s+everyone\.',
]

# Files to exclude
EXCLUDE_PATTERNS = [
    'backups',
    'node_modules',
    '__pycache__',
    '.git',
]

def should_exclude_file(file_path):
    """Check if file should be excluded"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def update_footer_copyright(content):
    """Update copyright notice in content"""
    updated = False
    original_content = content
    
    # Pattern 1: Standard format without "All rights reserved"
    patterns_to_replace = [
        (r'(©\s*easyjpgtopdf\s*—\s*Free\s+PDF\s+&\s+Image\s+Tools\s+for\s+everyone\.)(?!\s*All\s+rights\s+reserved)', 
         r'\1 All rights reserved.'),
        (r'(&copy;\s*easyjpgtopdf\s*&mdash;\s*Free\s+PDF\s+&amp;\s+Image\s+Tools\s+for\s+everyone\.)(?!\s*All\s+rights\s+reserved)', 
         r'&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone. All rights reserved.'),
        (r'(©\s*easyjpgtopdf\s*—\s*Free\s+PDF\s+&amp;\s+Image\s+Tools\s+for\s+everyone\.)(?!\s*All\s+rights\s+reserved)', 
         r'© easyjpgtopdf — Free PDF &amp; Image Tools for everyone. All rights reserved.'),
    ]
    
    for pattern, replacement in patterns_to_replace:
        if re.search(pattern, content, re.IGNORECASE):
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            updated = True
    
    # Also update payment-receipt format to match
    # Current: "© 2024 easyjpgtopdf. All rights reserved."
    # New: "© easyjpgtopdf — Free PDF & Image Tools for everyone. All rights reserved."
    payment_pattern = r'©\s*<span[^>]*>.*?</span>\s*easyjpgtopdf\.\s*All\s+rights\s+reserved\.'
    if re.search(payment_pattern, content, re.IGNORECASE):
        content = re.sub(payment_pattern, NEW_COPYRIGHT, content, flags=re.IGNORECASE)
        updated = True
    
    # Also handle dynamic year pattern
    dynamic_year_pattern = r'©\s*<span[^>]*id=["\']current-year["\'][^>]*>.*?</span>\s*easyjpgtopdf\.\s*All\s+rights\s+reserved\.'
    if re.search(dynamic_year_pattern, content, re.IGNORECASE):
        content = re.sub(dynamic_year_pattern, NEW_COPYRIGHT, content, flags=re.IGNORECASE)
        updated = True
    
    return content, updated

def update_file(file_path):
    """Update copyright in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        content, updated = update_footer_copyright(content)
        
        if updated and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function"""
    base_dir = Path(__file__).parent
    
    # Get all HTML files
    html_files = list(base_dir.rglob('*.html'))
    js_files = [
        base_dir / 'js' / 'global-components.js',
        base_dir / 'api' / 'send-receipt-email.js',
    ]
    
    # Filter out excluded files
    html_files = [f for f in html_files if not should_exclude_file(f)]
    
    all_files = html_files + [f for f in js_files if f.exists()]
    
    print(f"📋 Found {len(all_files)} files to process\n")
    
    updated_count = 0
    skipped_count = 0
    
    for file_path in all_files:
        if should_exclude_file(file_path):
            skipped_count += 1
            continue
            
        relative_path = file_path.relative_to(base_dir)
        
        if update_file(file_path):
            print(f"✅ Updated: {relative_path}")
            updated_count += 1
        else:
            # Check if already has "All rights reserved"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'All rights reserved' in content or 'All rights reserved' in content.lower():
                    print(f"⏭️  Already updated: {relative_path}")
                else:
                    print(f"⚠️  No copyright found: {relative_path}")
            except:
                pass
    
    print(f"\n{'='*60}")
    print(f"✨ Complete!")
    print(f"   ✅ Updated: {updated_count} files")
    print(f"   ⏭️  Skipped: {skipped_count} files")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

