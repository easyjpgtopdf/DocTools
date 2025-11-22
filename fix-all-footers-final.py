#!/usr/bin/env python3
"""
Final Footer Fix - Replace all footers with index.html footer exactly
Ensures Pricing, DMCA, Blog links in all footers
"""

import os
import re
from pathlib import Path

# Index.html footer template (exact)
INDEX_FOOTER_HTML = '''    <footer>
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
            <p class="footer-brand-line">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone.</p>
            <p class="footer-credits">
                Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
                <a href="attributions.html">See full acknowledgements</a>.
            </p>
        </div>
    </footer>'''

EXCLUDE_PATTERNS = ['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backups', 'server/node_modules']

def should_exclude(file_path):
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def replace_footer_in_file(file_path):
    """Replace footer with index.html footer"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return False, "Cannot read file"
    
    original_content = content
    
    # Remove all footers
    footer_pattern = r'<footer[^>]*>.*?</footer>'
    footers = list(re.finditer(footer_pattern, content, re.IGNORECASE | re.DOTALL))
    
    if not footers:
        # No footer found - add before </body>
        body_close = content.find('</body>')
        if body_close != -1:
            content = content[:body_close] + '\n' + INDEX_FOOTER_HTML + '\n' + content[body_close:]
            changes = "Added footer before </body>"
        else:
            content = content.rstrip() + '\n' + INDEX_FOOTER_HTML
            changes = "Added footer at end"
    else:
        # Replace all footers with single footer
        # Remove all footers (reverse order)
        for match in reversed(footers):
            content = content[:match.start()] + content[match.end():]
        
        # Add single footer before </body>
        body_close = content.find('</body>')
        if body_close != -1:
            content = content[:body_close] + '\n' + INDEX_FOOTER_HTML + '\n' + content[body_close:]
            changes = f"Replaced {len(footers)} footer(s) with index.html footer"
        else:
            content = content.rstrip() + '\n' + INDEX_FOOTER_HTML
            changes = f"Replaced {len(footers)} footer(s), added at end"
    
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        except Exception as e:
            return False, f"Error saving: {e}"
    
    # Check if footer already matches
    if footers:
        footer_text = footers[0].group(0)
        # Normalize whitespace for comparison
        normalized_footer = re.sub(r'\s+', ' ', footer_text.strip())
        normalized_index = re.sub(r'\s+', ' ', INDEX_FOOTER_HTML.strip())
        
        # Check for required links
        has_pricing = 'pricing.html' in footer_text
        has_dmca = 'dmca-en.html' in footer_text
        has_blog = 'blog.html' in footer_text
        
        if has_pricing and has_dmca and has_blog:
            return False, "Footer already matches index.html"
        else:
            # Missing links - replace
            if content == original_content:
                # Replace footer
                footer_match = footers[0]
                content = content[:footer_match.start()] + INDEX_FOOTER_HTML + content[footer_match.end():]
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return True, "Added missing Pricing/DMCA/Blog links"
                except Exception as e:
                    return False, f"Error saving: {e}"
    
    return False, "No changes needed"

def main():
    root_dir = Path(__file__).parent
    
    print("🔧 Final Footer Fix - Ensuring all footers match index.html exactly...\n")
    print("="*80)
    
    # Get all HTML files
    html_files = list(root_dir.rglob('*.html'))
    
    fixed_count = 0
    already_ok = 0
    errors = []
    
    for file_path in html_files:
        if should_exclude(file_path):
            continue
        
        relative_path = file_path.relative_to(root_dir)
        
        success, message = replace_footer_in_file(file_path)
        
        if success:
            print(f"✅ {relative_path}: {message}")
            fixed_count += 1
        elif "already matches" in message or "No changes" in message:
            already_ok += 1
        elif "Error" in message:
            print(f"❌ {relative_path}: {message}")
            errors.append((relative_path, message))
    
    print("\n" + "="*80)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Files Fixed: {fixed_count}")
    print(f"   ✓ Already OK: {already_ok}")
    print(f"   ❌ Errors: {len(errors)}")
    print("="*80)
    
    if fixed_count > 0:
        print(f"\n✅ Successfully fixed {fixed_count} files!")
        print("📝 All footers now match index.html footer exactly")

if __name__ == '__main__':
    main()

