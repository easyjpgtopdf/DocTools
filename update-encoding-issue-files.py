#!/usr/bin/env python3
"""
Update files with encoding issues to add "All rights reserved"
Uses different encodings to handle problematic files
"""

import os
import re
from pathlib import Path

# Files with encoding issues that need manual update
PROBLEMATIC_FILES = [
    'payment-receipt.html',
    'add-page-numbers-convert.html',
    'add-page-numbers.html',
    'ai-image-generator.html',
    'attributions.html',
    'background-remover.html',
    'background-style.html',
    'biodata-maker.html',
    'compress-pdf.html',
    'edit-pdf.html',
    'excel-to-pdf-convert.html',
    'excel-to-pdf.html',
    'image-editor-result.html',
    'image-resizer-result.html',
    'image-watermark-convert.html',
    'jpg-to-pdf-convert.html',
    'jpg-to-pdf.html',
    'kyc-support.html',
    'marriage-card.html',
    'merge-pdf-convert.html',
    'merge-pdf.html',
    'ocr-image.html',
    'online_resume_maker.html',
    'pdf-to-excel-convert.html',
    'pdf-to-excel.html',
    'pdf-to-jpg-convert.html',
    'pdf-to-jpg.html',
    'pdf-to-ppt-convert.html',
    'pdf-to-ppt.html',
    'pdf-to-word.html',
    'ppt-to-pdf-convert.html',
    'ppt-to-pdf-new.html',
    'ppt-to-pdf.html',
    'privacy-policy.html',
    'protect-pdf.html',
    'refund-policy.html',
    'shipping-billing.html',
    'split-pdf-convert.html',
    'split-pdf.html',
    'terms-of-service.html',
    'watermark-pdf-convert.html',
    'watermark-pdf.html',
    'word-to-pdf-convert.html',
    'word-to-pdf.html',
]

# Encodings to try
ENCODINGS = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']

def update_file_with_encoding(file_path):
    """Try to update file with different encodings"""
    for encoding in ENCODINGS:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            original_content = content
            
            # Pattern to match copyright without "All rights reserved"
            patterns = [
                (r'(©\s*easyjpgtopdf\s*—\s*Free\s+PDF\s+&\s+Image\s+Tools\s+for\s+everyone\.)(?!\s*All\s+rights\s+reserved)', 
                 r'\1 All rights reserved.'),
                (r'(&copy;\s*easyjpgtopdf\s*&mdash;\s*Free\s+PDF\s+&amp;\s+Image\s+Tools\s+for\s+everyone\.)(?!\s*All\s+rights\s+reserved)', 
                 r'&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone. All rights reserved.'),
            ]
            
            updated = False
            for pattern, replacement in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                    updated = True
            
            if updated and content != original_content:
                # Try to save with UTF-8 first
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return True, encoding
                except:
                    # If UTF-8 fails, use original encoding
                    with open(file_path, 'w', encoding=encoding, errors='replace') as f:
                        f.write(content)
                    return True, encoding
                    
        except Exception as e:
            continue
    
    return False, None

def main():
    """Main function"""
    base_dir = Path(__file__).parent
    
    updated_count = 0
    failed_count = 0
    
    for file_name in PROBLEMATIC_FILES:
        file_path = base_dir / file_name
        
        if not file_path.exists():
            continue
        
        relative_path = file_path.relative_to(base_dir)
        success, encoding = update_file_with_encoding(file_path)
        
        if success:
            print(f"✅ Updated: {relative_path} (encoding: {encoding})")
            updated_count += 1
        else:
            print(f"⚠️  Failed: {relative_path}")
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"✨ Complete!")
    print(f"   ✅ Updated: {updated_count} files")
    print(f"   ⚠️  Failed: {failed_count} files")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

