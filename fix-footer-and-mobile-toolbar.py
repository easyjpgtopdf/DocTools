#!/usr/bin/env python3
"""
Fix Footer Issues and Mobile Header Toolbar
1. Remove content after </footer> tag
2. Ensure all pages have proper footer
3. Fix mobile header toolbar functionality
"""

import os
import re
from pathlib import Path

# Standard footer HTML (from global-components.js)
STANDARD_FOOTER = '''    <footer>
        <div class="container footer-inner">
            <div class="footer-company-links">
                <span>Company</span>
                <a href="index.html#about">About Us</a>
                <a href="index.html#contact">Contact</a>
                <a href="pricing.html">Pricing</a>
                <a href="privacy-policy.html">Privacy Policy</a>
                <a href="terms-of-service.html">Terms of Service</a>
                <a href="dmca.html">DMCA</a>
                <a href="blog.html">Blog</a>
            </div>
            <p class="footer-brand-line">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone. All rights reserved.</p>
            <p class="footer-credits">
                Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
                <a href="attributions.html">See full acknowledgements</a>.
            </p>
        </div>
    </footer>'''

def fix_footer_issues(file_path):
    """Fix footer issues in HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. Remove content between </footer> and </body> (except whitespace)
        # Find </footer> tag
        footer_close_pattern = r'</footer>'
        body_close_pattern = r'</body>'
        
        if re.search(footer_close_pattern, content) and re.search(body_close_pattern, content):
            # Find everything between </footer> and </body>
            pattern = r'(</footer>)(.*?)(</body>)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                footer_close = match.group(1)
                between_content = match.group(2).strip()
                body_close = match.group(3)
                
                # If there's non-whitespace content between </footer> and </body>, remove it
                if between_content and between_content.strip():
                    # Check if it's just SSL badges or trust badges (common issue)
                    if 'ssl' in between_content.lower() or 'trust' in between_content.lower() or 'badge' in between_content.lower():
                        # Move SSL badges inside footer before closing </footer>
                        # Extract the badges content
                        badges_match = re.search(r'(<div[^>]*style[^>]*>.*?</div>)', between_content, re.DOTALL)
                        if badges_match:
                            badges_html = badges_match.group(1)
                            # Remove badges from between footer and body
                            content = re.sub(pattern, r'\1\n' + body_close, content, flags=re.DOTALL)
                            # Add badges inside footer (before </footer>)
                            content = re.sub(r'(</footer>)', badges_html + '\n    \\1', content, count=1)
                            changes_made.append("Moved SSL badges inside footer")
                        else:
                            # Just remove the content
                            content = re.sub(pattern, r'\1\n' + body_close, content, flags=re.DOTALL)
                            changes_made.append("Removed content after footer")
                    else:
                        # Remove the content
                        content = re.sub(pattern, r'\1\n' + body_close, content, flags=re.DOTALL)
                        changes_made.append("Removed content after footer")
        
        # 2. Check if footer exists, if not add it
        if '</footer>' not in content and '</body>' in content:
            # Add footer before </body>
            content = re.sub(r'</body>', STANDARD_FOOTER + '\n</body>', content)
            changes_made.append("Added missing footer")
        
        # 3. Fix footer structure if it's malformed
        # Check if footer has proper structure
        if '<footer>' in content and '</footer>' in content:
            # Ensure footer has proper class structure
            if 'footer-inner' not in content[content.find('<footer>'):content.find('</footer>')]:
                # Try to fix footer structure
                footer_section = re.search(r'<footer>.*?</footer>', content, re.DOTALL)
                if footer_section:
                    # Check if it needs fixing
                    footer_content = footer_section.group(0)
                    if 'footer-inner' not in footer_content:
                        # Replace with standard footer
                        content = content.replace(footer_content, STANDARD_FOOTER)
                        changes_made.append("Fixed footer structure")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        
        return False, []
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, []

def main():
    """Process all HTML files"""
    html_files = []
    
    # Find all HTML files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'venv', 'env', 'server/public/backups', '.venv312']]
        
        for file in files:
            if file.endswith('.html') and not file.startswith('test-'):
                file_path = os.path.join(root, file)
                html_files.append(file_path)
    
    fixed_count = 0
    for file_path in html_files:
        fixed, changes = fix_footer_issues(file_path)
        if fixed:
            print(f"✅ Fixed {file_path}: {', '.join(changes)}")
            fixed_count += 1
    
    print(f"\n✅ Total files fixed: {fixed_count}")

if __name__ == "__main__":
    main()

