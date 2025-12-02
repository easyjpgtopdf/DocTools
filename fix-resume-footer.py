#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove duplicate footers from resume-maker.html
Keep only global-footer-placeholder (which loads index page footer)
"""

import re
from pathlib import Path

def fix_resume_footer():
    """Remove all hardcoded footers and keep only global-footer-placeholder"""
    filepath = Path('resume-maker.html')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove all hardcoded <footer> tags and their content
        # Pattern to match footer tags (including nested content)
        footer_pattern = r'<footer[^>]*>.*?</footer>'
        content = re.sub(footer_pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove any standalone footer closing tags
        content = re.sub(r'</footer>', '', content, flags=re.IGNORECASE)
        
        # Ensure global-footer-placeholder exists before </body>
        if 'global-footer-placeholder' not in content:
            # Add it before </body>
            body_end = content.rfind('</body>')
            if body_end > 0:
                footer_placeholder = '\n    <div id="global-footer-placeholder"></div>'
                content = content[:body_end] + footer_placeholder + '\n' + content[body_end:]
        else:
            # Make sure there's only one global-footer-placeholder
            # Count occurrences
            count = len(re.findall(r'global-footer-placeholder', content, re.IGNORECASE))
            if count > 1:
                # Keep only the first one, remove others
                first_match = re.search(r'<div[^>]*id="global-footer-placeholder"[^>]*>', content, re.IGNORECASE)
                if first_match:
                    # Remove all occurrences
                    content = re.sub(r'<div[^>]*id="global-footer-placeholder"[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    # Add back one before </body>
                    body_end = content.rfind('</body>')
                    if body_end > 0:
                        footer_placeholder = '\n    <div id="global-footer-placeholder"></div>'
                        content = content[:body_end] + footer_placeholder + '\n' + content[body_end:]
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "removed duplicate footers"
        else:
            return False, "no changes needed"
    
    except Exception as e:
        return False, f"error: {str(e)}"

def main():
    print("=" * 60)
    print("Fix Resume Maker Footer - Remove Duplicates")
    print("=" * 60)
    print()
    
    success, message = fix_resume_footer()
    
    if success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    main()




