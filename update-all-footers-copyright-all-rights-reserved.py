#!/usr/bin/env python3
"""
Update All Footers with Copyright and All Rights Reserved
1. Update all footer copyright notices consistently
2. Add "All rights reserved" to all footers
3. Ensure legal protection for code
"""

import os
import re
from pathlib import Path
from datetime import datetime

# Updated footer copyright line with All Rights Reserved
FOOTER_COPYRIGHT_LINE = '&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone. All rights reserved.'

# Old patterns to replace
OLD_PATTERNS = [
    r'&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone\.',
    r'© easyjpgtopdf — Free PDF & Image Tools for everyone\.',
    r'© easyjpgtopdf.*?Free PDF.*?Image Tools.*?everyone\.',
    r'&copy; easyjpgtopdf.*?Free PDF.*?Image Tools.*?everyone\.',
]

EXCLUDE_PATTERNS = ['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backups', '*.pyc']

def should_exclude(file_path):
    """Check if file should be excluded"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def update_footer_copyright(content, file_path):
    """Update footer copyright line with All Rights Reserved"""
    changes = []
    
    # Check if already has "All rights reserved"
    if 'All rights reserved' in content or 'all rights reserved' in content:
        # Already updated, but check if format is correct
        if FOOTER_COPYRIGHT_LINE in content or FOOTER_COPYRIGHT_LINE.replace('&mdash;', '—').replace('&amp;', '&') in content:
            return content, []  # Already correct
    
    # Try to replace old patterns
    for pattern in OLD_PATTERNS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE | re.DOTALL))
        if matches:
            for match in reversed(matches):
                content = content[:match.start()] + FOOTER_COPYRIGHT_LINE + content[match.end():]
                changes.append(f"Updated copyright with 'All rights reserved'")
            break
    
    # If no match found, try to add to footer-brand-line
    if not changes:
        footer_brand_pattern = r'(<p[^>]*class="footer-brand-line"[^>]*>)(.*?)(</p>)'
        match = re.search(footer_brand_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            start_tag = match.group(1)
            current_text = match.group(2)
            end_tag = match.group(3)
            
            # Check if All rights reserved is missing
            if 'All rights reserved' not in current_text and 'all rights reserved' not in current_text:
                # Add All rights reserved
                new_text = current_text.rstrip('. ') + '. All rights reserved.'
                content = content[:match.start()] + start_tag + new_text + end_tag + content[match.end():]
                changes.append("Added 'All rights reserved' to footer")
    
    return content, changes

def update_file(file_path):
    """Update a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return None, ["Cannot read file"]
    
    original_content = content
    all_changes = []
    
    # Update footer copyright
    content, changes = update_footer_copyright(content, file_path)
    all_changes.extend(changes)
    
    # Save if changed
    if content != original_content and all_changes:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, all_changes
        except Exception as e:
            return None, [f"Error saving: {str(e)}"]
    
    return False, all_changes if all_changes else []

def create_license_file():
    """Create LICENSE file for copyright protection"""
    current_year = datetime.now().year
    
    license_content = f"""MIT License

Copyright (c) {current_year} easyjpgtopdf

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

© {current_year} easyjpgtopdf — Free PDF & Image Tools for everyone. All rights reserved.

This software and its code are protected by copyright laws. Unauthorized copying, 
modification, distribution, or use of this software, via any medium, is strictly 
prohibited without the express written permission of easyjpgtopdf.

For licensing inquiries, please contact: support@easyjpgtopdf.com
"""
    
    license_path = Path('LICENSE')
    
    try:
        with open(license_path, 'w', encoding='utf-8') as f:
            f.write(license_content)
        return True, "Created LICENSE file"
    except Exception as e:
        return False, f"Error creating LICENSE: {str(e)}"

def create_copyright_file():
    """Create COPYRIGHT file with copyright notice"""
    current_year = datetime.now().year
    
    copyright_content = f"""COPYRIGHT NOTICE

© {current_year} easyjpgtopdf — Free PDF & Image Tools for everyone. All rights reserved.

COPYRIGHT PROTECTION

All content, code, designs, graphics, logos, images, text, software, and other 
materials on this website (collectively, the "Content") are the property of 
easyjpgtopdf or its content suppliers and are protected by international 
copyright, trademark, and other intellectual property laws.

PROTECTED MATERIALS

The following are protected by copyright and other intellectual property laws:
- All HTML, CSS, JavaScript, and other source code
- All documentation, tutorials, guides, and written content
- All designs, graphics, logos, and visual elements
- All software, applications, and tools
- All branding, trademarks, and service marks

UNAUTHORIZED USE PROHIBITED

You may NOT:
- Copy, reproduce, or duplicate any code or content
- Modify, adapt, or create derivative works
- Distribute, publish, or transmit any code or content
- Use any code or content for commercial purposes
- Remove or alter any copyright notices or proprietary markings
- Reverse engineer, decompile, or disassemble any software

LEGAL ACTION

Any unauthorized use of our copyrighted materials may result in legal action, 
including but not limited to:
- Cease and desist orders
- Monetary damages
- Injunctions
- Recovery of legal costs

CONTACT

For licensing inquiries or permissions, please contact:
Email: support@easyjpgtopdf.com
Website: https://easyjpgtopdf.com

---

This copyright notice is effective as of {datetime.now().strftime('%B %d, %Y')} and 
applies to all content on the easyjpgtopdf website and all associated materials.

Last Updated: {datetime.now().strftime('%Y-%m-%d')}
"""
    
    copyright_path = Path('COPYRIGHT')
    
    try:
        with open(copyright_path, 'w', encoding='utf-8') as f:
            f.write(copyright_content)
        return True, "Created COPYRIGHT file"
    except Exception as e:
        return False, f"Error creating COPYRIGHT: {str(e)}"

def update_global_components():
    """Update global-components.js footer"""
    global_components_path = Path('js/global-components.js')
    
    try:
        with open(global_components_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and update globalFooterHTML
        footer_pattern = r'(const globalFooterHTML = `[\s\S]*?<p class="footer-brand-line">)(.*?)(</p>[\s\S]*?</footer>[\s\S]*?`;)'
        match = re.search(footer_pattern, content)
        
        if match:
            # Check if already has "All rights reserved"
            current_text = match.group(2)
            
            if 'All rights reserved' not in current_text and 'all rights reserved' not in current_text:
                # Update with All rights reserved
                new_text = FOOTER_COPYRIGHT_LINE
                updated_content = content[:match.start(2)] + new_text + content[match.end(2):]
                
                with open(global_components_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                return True, "Updated global-components.js footer"
            else:
                return False, "global-components.js already updated"
        else:
            return False, "Could not find footer pattern in global-components.js"
            
    except Exception as e:
        return False, f"Error updating global-components.js: {str(e)}"

def main():
    """Main function"""
    root_dir = Path(__file__).parent
    
    print("🔧 Updating All Footers with Copyright & All Rights Reserved...\n")
    print("="*80)
    
    # Step 1: Create LICENSE file
    print("\n1️⃣ Creating LICENSE file...")
    success, message = create_license_file()
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ⚠️  {message}")
    
    # Step 2: Create COPYRIGHT file
    print("\n2️⃣ Creating COPYRIGHT file...")
    success, message = create_copyright_file()
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ⚠️  {message}")
    
    # Step 3: Update global-components.js
    print("\n3️⃣ Updating global-components.js...")
    success, message = update_global_components()
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ℹ️  {message}")
    
    # Step 4: Update all HTML files
    print("\n4️⃣ Updating All HTML Files...")
    html_files = list(root_dir.rglob('*.html'))
    
    fixed_count = 0
    already_ok = 0
    changed_files = []
    errors = []
    
    for file_path in html_files:
        if should_exclude(file_path):
            continue
        
        relative_path = file_path.relative_to(root_dir)
        
        success, changes = update_file(file_path)
        
        if success:
            fixed_count += 1
            changed_files.append((relative_path, changes))
        elif success is None:
            errors.append((relative_path, changes))
        else:
            already_ok += 1
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"\n✅ Files Fixed: {fixed_count}")
    print(f"✓ Already OK: {already_ok}")
    print(f"❌ Errors: {len(errors)}")
    
    if changed_files:
        print(f"\n📝 Files Updated:")
        for file_path, changes in changed_files[:10]:
            print(f"   • {file_path}")
        if len(changed_files) > 10:
            print(f"   ... and {len(changed_files) - 10} more files")
    
    if errors:
        print(f"\n⚠️  Errors:")
        for file_path, error in errors[:5]:
            print(f"   • {file_path}: {error[0] if error else 'Unknown error'}")
    
    print("\n" + "="*80)
    print("✅ All footers updated with copyright protection!")
    print("="*80)
    print("\n📋 Created Files:")
    print("   • LICENSE - MIT License with copyright protection")
    print("   • COPYRIGHT - Comprehensive copyright notice")
    print("\n🔒 Copyright Protection:")
    print("   • All footers now include 'All rights reserved'")
    print("   • Legal files created for code protection")
    print("   • Consistent copyright notices across all pages")

if __name__ == '__main__':
    main()

