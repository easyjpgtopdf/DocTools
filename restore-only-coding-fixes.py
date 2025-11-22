#!/usr/bin/env python3
"""
Restore Only Coding Fixes (Selectively)
Restores:
1. Extra closing </link> tags (link is self-closing, should NOT have closing tag)
2. Extra closing </input> tags (input is self-closing, should NOT have closing tag)
3. Missing closing </script> tags
4. Duplicate headers (keep only first)
5. Template files cleanup (excel-unlocker templates)

Does NOT affect:
- Footer changes
- Copyright updates
- Competitor references removal
"""

import os
import re
from pathlib import Path

# Files that had coding fixes applied (from the fix script)
FILES_WITH_CODING_FIXES = [
    # Extra closing link tags removed
    'add-page-numbers-convert.html',
    'attributions.html',
    'excel-to-pdf-convert.html',
    'image-editor-result.html',
    'image-resizer-result.html',
    'kyc-support.html',
    'ppt-to-pdf-convert.html',
    'privacy-policy.html',
    'refund-policy.html',
    'result.html',
    'shipping-billing.html',
    'split-pdf-convert.html',
    'terms-of-service.html',
    'watermark-pdf-convert.html',
    'watermark-pdf.html',  # Also had extra </input>
    'word-to-pdf-convert.html',
    
    # Missing closing script tags added
    'edit-pdf.html',
    'image-watermark-convert.html',
    'online_resume_maker.html',
    'ppt-to-pdf-new.html',
    'ppt-to-pdf.html',
    
    # Duplicate headers removed
    'background-style.html',  # Had 2 headers
    'crop-pdf.html',  # Had 3 headers
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

def restore_extra_closing_link_tags(content):
    """Restore extra closing </link> tags - REMOVE them (they shouldn't exist)"""
    # Link tags are self-closing, </link> should not exist
    link_close_count = len(re.findall(r'</link>', content, re.IGNORECASE))
    
    if link_close_count > 0:
        # Remove all </link> tags (restore the fix)
        content = re.sub(r'</link>', '', content, flags=re.IGNORECASE)
        return content, True, f"Removed {link_close_count} extra </link> tags (restored fix)"
    
    return content, False, None

def restore_extra_closing_input_tags(content):
    """Restore extra closing </input> tags - REMOVE them (they shouldn't exist)"""
    input_close_count = len(re.findall(r'</input>', content, re.IGNORECASE))
    
    if input_close_count > 0:
        content = re.sub(r'</input>', '', content, flags=re.IGNORECASE)
        return content, True, f"Removed {input_close_count} extra </input> tags (restored fix)"
    
    return content, False, None

def restore_missing_closing_script_tags(content):
    """Restore missing closing </script> tags - ADD them back"""
    script_open_matches = list(re.finditer(r'<script[^>]*>', content, re.IGNORECASE))
    script_close_matches = list(re.finditer(r'</script>', content, re.IGNORECASE))
    
    if len(script_open_matches) > len(script_close_matches):
        missing = len(script_open_matches) - len(script_close_matches)
        
        # Find position before </body> or at end
        body_close = re.search(r'</body>', content, re.IGNORECASE)
        if body_close:
            insert_pos = body_close.start()
        else:
            insert_pos = len(content.rstrip())
        
        # Add missing closing script tags
        for i in range(missing):
            content = content[:insert_pos] + '\n    </script>' + content[insert_pos:]
        
        return content, True, f"Added {missing} missing </script> tags (restored fix)"
    
    return content, False, None

def restore_duplicate_headers(content):
    """Restore duplicate headers fix - REMOVE duplicates, keep only first"""
    header_matches = list(re.finditer(r'<header[^>]*>.*?</header>', content, re.IGNORECASE | re.DOTALL))
    
    if len(header_matches) > 1:
        # Keep the first header, remove others (restore the fix)
        for header_match in reversed(header_matches[1:]):  # Reverse to maintain positions
            content = content[:header_match.start()] + content[header_match.end():]
        
        return content, True, f"Removed {len(header_matches) - 1} duplicate header(s) (restored fix)"
    
    return content, False, None

def restore_template_cleanup(file_path, content):
    """Restore template cleanup - Remove footer from result.html (it extends base.html)"""
    if 'excel-unlocker/templates/result.html' in str(file_path):
        # Remove footer that was added (it extends base.html, footer is in base.html)
        footer_match = re.search(r'<footer[^>]*>.*?</footer>', content, re.IGNORECASE | re.DOTALL)
        if footer_match and '{% endblock %}' in content:
            # Check if footer is after {% endblock %}
            endblock_pos = content.find('{% endblock %}')
            footer_pos = footer_match.start()
            
            if footer_pos > endblock_pos:
                # Remove footer after {% endblock %}
                content = content[:footer_match.start()] + content[footer_match.end():]
                return content, True, "Removed footer from template (restored fix - extends base.html)"
    
    return content, False, None

def restore_coding_fixes(file_path):
    """Restore coding fixes for a single file"""
    try:
        # Try UTF-8 first
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            # Try other encodings
            for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    encoding = enc
                    break
                except:
                    continue
            else:
                return None, ["Cannot read file encoding"]
        
        original_content = content
        fixes_applied = []
        
        # Apply fixes
        # 1. Restore extra closing link tags fix (remove them)
        content, fixed, fix_msg = restore_extra_closing_link_tags(content)
        if fixed:
            fixes_applied.append(fix_msg)
        
        # 2. Restore extra closing input tags fix (remove them)
        content, fixed, fix_msg = restore_extra_closing_input_tags(content)
        if fixed:
            fixes_applied.append(fix_msg)
        
        # 3. Restore missing closing script tags fix (add them)
        content, fixed, fix_msg = restore_missing_closing_script_tags(content)
        if fixed:
            fixes_applied.append(fix_msg)
        
        # 4. Restore duplicate headers fix (remove duplicates)
        content, fixed, fix_msg = restore_duplicate_headers(content)
        if fixed:
            fixes_applied.append(fix_msg)
        
        # 5. Restore template cleanup (remove footer from result.html)
        content, fixed, fix_msg = restore_template_cleanup(file_path, content)
        if fixed:
            fixes_applied.append(fix_msg)
        
        # Only save if changes were made
        if content != original_content:
            # Try to save as UTF-8
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, fixes_applied
            except:
                # If UTF-8 fails, use original encoding
                with open(file_path, 'w', encoding=encoding, errors='replace') as f:
                    f.write(content)
                return True, fixes_applied
        
        return False, fixes_applied
        
    except Exception as e:
        return None, [f"Error: {str(e)}"]

def main():
    """Main function"""
    base_dir = Path(__file__).parent
    
    print("🔧 Restoring ONLY coding fixes (preserving footer/copyright changes)...\n")
    print("="*80)
    
    fixed_files = []
    no_change_files = []
    failed_files = []
    total_fixes = 0
    
    # Process files that had coding fixes
    for file_name in FILES_WITH_CODING_FIXES:
        file_path = base_dir / file_name
        
        if not file_path.exists():
            continue
        
        if should_exclude_file(file_path):
            continue
        
        relative_path = file_path.relative_to(base_dir)
        
        success, fixes = restore_coding_fixes(file_path)
        
        if success is None:
            print(f"❌ Failed: {relative_path}")
            print(f"   {fixes[0]}")
            failed_files.append((relative_path, fixes))
        elif success:
            print(f"✅ Fixed: {relative_path}")
            for fix in fixes:
                print(f"   • {fix}")
            fixed_files.append((relative_path, fixes))
            total_fixes += len(fixes)
        else:
            # File was checked but no fixes needed
            no_change_files.append(relative_path)
    
    print("\n" + "="*80)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Files fixed: {len(fixed_files)}")
    print(f"   ⏭️  Files unchanged: {len(no_change_files)}")
    print(f"   ❌ Files failed: {len(failed_files)}")
    print(f"   🔧 Total fixes restored: {total_fixes}")
    print("="*80)
    
    if fixed_files:
        print(f"\n✅ Successfully restored coding fixes in {len(fixed_files)} files!")
        print(f"📝 Note: Footer, copyright, and competitor reference changes are preserved")

if __name__ == '__main__':
    main()

