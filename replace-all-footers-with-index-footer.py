#!/usr/bin/env python3
"""
Replace all footer instances with index.html footer
Ensures consistency across all pages and removes duplicate footers
"""

import os
import re
from pathlib import Path

# Index.html footer (exact copy)
INDEX_FOOTER = '''    <footer>
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

# Files to exclude
EXCLUDE_PATTERNS = [
    'backups',
    'node_modules',
    '__pycache__',
    '.git',
    '.venv',
    'venv',
    'server/public/backups',
]

def should_exclude_file(file_path):
    """Check if file should be excluded"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def remove_all_footers(content):
    """Remove all footer tags and their content"""
    # Remove footer placeholders
    content = re.sub(r'<div[^>]*id=["\']global-footer-placeholder["\'][^>]*></div>\s*', '', content, flags=re.IGNORECASE)
    
    # Remove all footer tags (multiline match)
    # This regex matches from <footer> to </footer> including all content inside
    content = re.sub(r'<footer[^>]*>.*?</footer>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Also remove footer if it's split across lines with whitespace
    content = re.sub(r'<footer\b[^>]*>[\s\S]*?</footer>', '', content, flags=re.IGNORECASE)
    
    return content

def add_footer_before_closing_body(content):
    """Add footer before closing </body> tag"""
    # Find </body> tag
    body_match = re.search(r'</body>', content, re.IGNORECASE)
    
    if body_match:
        # Insert footer before </body>
        insert_pos = body_match.start()
        content = content[:insert_pos] + INDEX_FOOTER + '\n\n    ' + content[insert_pos:]
        return content
    else:
        # If no </body> tag, append before closing </html>
        html_match = re.search(r'</html>', content, re.IGNORECASE)
        if html_match:
            insert_pos = html_match.start()
            content = content[:insert_pos] + INDEX_FOOTER + '\n\n    ' + content[insert_pos:]
        else:
            # Just append at end
            content = content.rstrip() + '\n\n' + INDEX_FOOTER + '\n'
        return content

def ensure_global_components_script(content):
    """Ensure global-components.js script is included before closing </body>"""
    script_tag = '    <script src="js/global-components.js"></script>'
    
    # Check if script already exists
    if 'global-components.js' in content or 'js/global-components.js' in content:
        return content
    
    # Add before </body>
    body_match = re.search(r'</body>', content, re.IGNORECASE)
    if body_match:
        insert_pos = body_match.start()
        content = content[:insert_pos] + script_tag + '\n    ' + content[insert_pos:]
    
    return content

def update_file(file_path):
    """Update a single file"""
    try:
        # Try UTF-8 first
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            encoding = 'utf-8'
        except:
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
                print(f"⚠️  Cannot read encoding: {file_path}")
                return False
        
        original_content = content
        
        # Remove all existing footers
        content = remove_all_footers(content)
        
        # Add index footer before </body>
        content = add_footer_before_closing_body(content)
        
        # Ensure global-components.js script is included (for dynamic footer updates)
        # But only if not index.html (index.html has its own footer)
        if 'index.html' not in str(file_path):
            content = ensure_global_components_script(content)
        
        # Only write if changed
        if content != original_content:
            # Try to save as UTF-8
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except:
                # If UTF-8 fails, use original encoding
                with open(file_path, 'w', encoding=encoding, errors='replace') as f:
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
    
    # Filter out excluded files
    html_files = [f for f in html_files if not should_exclude_file(f)]
    
    print(f"📋 Found {len(html_files)} HTML files to process\n")
    print("🔄 Replacing all footers with index.html footer...\n")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in sorted(html_files):
        relative_path = file_path.relative_to(base_dir)
        
        # Skip index.html itself (it's our source)
        if file_path.name == 'index.html':
            skipped_count += 1
            print(f"⏭️  Skipped (source): {relative_path}")
            continue
        
        if update_file(file_path):
            print(f"✅ Updated: {relative_path}")
            updated_count += 1
        else:
            print(f"⏭️  No changes: {relative_path}")
            skipped_count += 1
    
    print(f"\n{'='*70}")
    print(f"✨ Footer Replacement Complete!")
    print(f"   ✅ Updated: {updated_count} files")
    print(f"   ⏭️  Skipped: {skipped_count} files")
    print(f"   ❌ Errors: {error_count} files")
    print(f"{'='*70}")
    print(f"\n📝 All footers now match index.html footer!")
    print(f"📝 Future updates: Modify index.html footer or js/global-components.js")

if __name__ == '__main__':
    main()

