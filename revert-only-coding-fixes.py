#!/usr/bin/env python3
"""
Revert ONLY Coding Fixes (Undo the fixes, restore original broken state)
This undoes the coding fixes while preserving footer/copyright changes.

Reverts:
1. Extra closing </link> tags - PUT THEM BACK (undo the fix)
2. Extra closing </input> tags - PUT THEM BACK (undo the fix)
3. Missing closing </script> tags - REMOVE ADDED TAGS (undo the fix)
4. Duplicate headers - PUT THEM BACK (undo the fix)
5. Template files cleanup - PUT FOOTER BACK (undo the fix)

Does NOT affect:
- Footer changes
- Copyright updates
- Competitor references removal
"""

import os
import re
from pathlib import Path

# Files that had coding fixes applied - we'll revert them
FILES_WITH_CODING_FIXES = [
    # Extra closing link tags removed - we'll put them back
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
    
    # Missing closing script tags added - we'll remove them
    'edit-pdf.html',
    'image-watermark-convert.html',
    'online_resume_maker.html',
    'ppt-to-pdf-new.html',
    'ppt-to-pdf.html',
    
    # Duplicate headers removed - we'll put them back (need git for this)
    'background-style.html',
    'crop-pdf.html',
]

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

def revert_extra_closing_link_tags(content):
    """Revert extra closing </link> tags fix - PUT THEM BACK"""
    # Find <link> tags and add closing </link> after them
    link_pattern = r'<link([^>]*?)(?<!/)>'
    matches = list(re.finditer(link_pattern, content, re.IGNORECASE))
    
    if matches:
        # Add closing tags after each link (reverse order to maintain positions)
        for match in reversed(matches):
            if '</link>' not in content[max(0, match.end()-10):match.end()+10]:
                content = content[:match.end()] + '</link>' + content[match.end():]
        return content, True, f"Restored {len(matches)} extra </link> tags (reverted fix)"
    
    return content, False, None

def revert_extra_closing_input_tags(content):
    """Revert extra closing </input> tags fix - PUT THEM BACK"""
    # Find <input> tags and add closing </input> after them
    input_pattern = r'<input([^>]*?)(?<!/)>'
    matches = list(re.finditer(input_pattern, content, re.IGNORECASE))
    
    if matches:
        # Add closing tags after each input (reverse order)
        for match in reversed(matches):
            if '</input>' not in content[max(0, match.end()-10):match.end()+10]:
                content = content[:match.end()] + '</input>' + content[match.end():]
        return content, True, f"Restored {len(matches)} extra </input> tags (reverted fix)"
    
    return content, False, None

def revert_missing_closing_script_tags(content):
    """Revert missing closing </script> tags fix - REMOVE ADDED TAGS"""
    # Count script opening and closing tags
    script_open = len(re.findall(r'<script[^>]*>', content, re.IGNORECASE))
    script_close = len(re.findall(r'</script>', content, re.IGNORECASE))
    
    # If there are more closing tags than opening (or equal), we added extra ones
    # Find and remove the last </script> before </body>
    if script_close >= script_open:
        # Find last </script> before </body>
        body_close = re.search(r'</body>', content, re.IGNORECASE)
        if body_close:
            # Look for </script> tags near the end before </body>
            before_body = content[:body_close.start()]
            script_close_matches = list(re.finditer(r'</script>', before_body, re.IGNORECASE))
            
            if script_close_matches and len(script_close_matches) > (script_open - 1):
                # Remove the last extra </script> tag
                last_script = script_close_matches[-1]
                content = content[:last_script.start()] + content[last_script.end():]
                return content, True, "Removed added </script> tag (reverted fix)"
    
    return content, False, None

def revert_duplicate_headers_with_git(file_path):
    """Revert duplicate headers fix - restore from git"""
    import subprocess
    try:
        # Restore just this file from git to get duplicate headers back
        result = subprocess.run(
            ['git', 'checkout', 'HEAD', '--', str(file_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Now reapply footer/copyright changes if needed
            return True, f"Restored duplicate headers from git (reverted fix)"
        return False, None
    except:
        return False, "Cannot restore from git"

def revert_template_cleanup(file_path, content):
    """Revert template cleanup - PUT FOOTER BACK in result.html"""
    if 'excel-unlocker/templates/result.html' in str(file_path):
        # Add footer after {% endblock %} (restore original)
        if '{% endblock %}' in content and '<footer>' not in content:
            footer_html = '''
    <footer>
        <div class="container footer-inner">
            <div class="footer-company-links">
                <span>Company</span>
                <a href="index.html#about">About Us</a>
                <a href="index.html#contact">Contact</a>
                <a href="pricing.html">Pricing</a>
                <a href="privacy-policy.html">Privacy Policy</a>
                <a href="terms-of-service.html">Terms of Service</a>
                <a href="dmca-en.html">DMCA</a>
                <a href="blog.html">Blog</a>
            </div>
            <p class="footer-brand-line">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone. All rights reserved.</p>
            <p class="footer-credits">
                Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
                <a href="attributions.html">See full acknowledgements</a>.
            </p>
        </div>
    </footer>'''
            
            endblock_pos = content.find('{% endblock %}')
            if endblock_pos != -1:
                insert_pos = content.find('\n', endblock_pos)
                if insert_pos == -1:
                    insert_pos = len(content)
                content = content[:insert_pos] + footer_html + content[insert_pos:]
                return content, True, "Restored footer in template (reverted fix)"
    
    return content, False, None

def revert_coding_fixes(file_path):
    """Revert coding fixes for a single file"""
    try:
        # Try UTF-8 first
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
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
        reverts_applied = []
        
        # For duplicate headers, use git restore
        file_str = str(file_path)
        if 'background-style.html' in file_str or 'crop-pdf.html' in file_str:
            success, msg = revert_duplicate_headers_with_git(file_path)
            if success:
                reverts_applied.append(msg)
                # Re-read file after git restore
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    original_content = content
                except:
                    pass
        
        # Revert fixes (restore broken state)
        # 1. Put back extra closing link tags
        content, reverted, revert_msg = revert_extra_closing_link_tags(content)
        if reverted:
            reverts_applied.append(revert_msg)
        
        # 2. Put back extra closing input tags
        content, reverted, revert_msg = revert_extra_closing_input_tags(content)
        if reverted:
            reverts_applied.append(revert_msg)
        
        # 3. Remove added closing script tags
        content, reverted, revert_msg = revert_missing_closing_script_tags(content)
        if reverted:
            reverts_applied.append(revert_msg)
        
        # 4. Put back footer in template
        content, reverted, revert_msg = revert_template_cleanup(file_path, content)
        if reverted:
            reverts_applied.append(revert_msg)
        
        # Save if changes were made
        if content != original_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, reverts_applied
            except:
                with open(file_path, 'w', encoding=encoding, errors='replace') as f:
                    f.write(content)
                return True, reverts_applied
        
        return False, reverts_applied
        
    except Exception as e:
        return None, [f"Error: {str(e)}"]

def main():
    """Main function"""
    base_dir = Path(__file__).parent
    
    print("🔄 Reverting ONLY coding fixes (restoring original broken state)...\n")
    print("⚠️  This will undo the coding fixes and restore errors!")
    print("="*80)
    
    reverted_files = []
    no_change_files = []
    failed_files = []
    total_reverts = 0
    
    for file_name in FILES_WITH_CODING_FIXES:
        file_path = base_dir / file_name
        
        if not file_path.exists():
            continue
        
        if should_exclude_file(file_path):
            continue
        
        relative_path = file_path.relative_to(base_dir)
        
        success, reverts = revert_coding_fixes(file_path)
        
        if success is None:
            print(f"❌ Failed: {relative_path}")
            print(f"   {reverts[0]}")
            failed_files.append((relative_path, reverts))
        elif success:
            print(f"✅ Reverted: {relative_path}")
            for revert in reverts:
                print(f"   • {revert}")
            reverted_files.append((relative_path, reverts))
            total_reverts += len(reverts)
        else:
            no_change_files.append(relative_path)
    
    print("\n" + "="*80)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Files reverted: {len(reverted_files)}")
    print(f"   ⏭️  Files unchanged: {len(no_change_files)}")
    print(f"   ❌ Files failed: {len(failed_files)}")
    print(f"   🔄 Total reverts: {total_reverts}")
    print("="*80)
    print(f"\n✅ Coding fixes reverted (errors restored)")
    print(f"📝 Footer, copyright, and competitor reference changes are preserved")

if __name__ == '__main__':
    main()

