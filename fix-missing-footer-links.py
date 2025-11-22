#!/usr/bin/env python3
"""
Fix missing Pricing, DMCA, Blog links in footers
"""

import re
from pathlib import Path

def fix_footer_links(file_path):
    """Add missing Pricing, DMCA, Blog links to footer"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return False, "Cannot read file"
    
    original = content
    
    # Find footer-company-links section
    footer_links_pattern = r'(<div class="footer-company-links">.*?<span>Company</span>.*?<a href="index\.html#contact">Contact</a>)(.*?)(</div>)'
    match = re.search(footer_links_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        # Check if Pricing/DMCA/Blog links exist
        footer_section = match.group(0)
        has_pricing = 'pricing.html' in footer_section
        has_dmca = 'dmca-en.html' in footer_section
        has_blog = 'blog.html' in footer_section
        
        if not (has_pricing and has_dmca and has_blog):
            # Add missing links after Contact link
            missing_links = ''
            if not has_pricing:
                missing_links += '\n                <a href="pricing.html">Pricing</a>'
            if not has_dmca:
                missing_links += '\n                <a href="dmca-en.html">DMCA</a>'
            if not has_blog:
                missing_links += '\n                <a href="blog.html">Blog</a>'
            
            # Insert missing links after Contact link
            contact_pattern = r'(<a href="index\.html#contact">Contact</a>)(.*?)(<a href="privacy|</div>)'
            contact_match = re.search(contact_pattern, content, re.IGNORECASE)
            
            if contact_match:
                # Insert missing links after Contact
                insert_pos = contact_match.end(1)
                content = content[:insert_pos] + missing_links + content[insert_pos:]
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return True, f"Added missing links: {missing_links.strip().count(chr(10))} link(s)"
                except Exception as e:
                    return False, f"Error saving: {e}"
        else:
            return False, "All links already present"
    
    # Alternative: Replace entire footer-company-links section
    full_footer_pattern = r'<div class="footer-company-links">.*?</div>'
    footer_match = re.search(full_footer_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if footer_match:
        footer_html = footer_match.group(0)
        # Check if missing links
        if 'pricing.html' not in footer_html or 'dmca-en.html' not in footer_html or 'blog.html' not in footer_html:
            # Replace with complete footer links
            new_footer_links = '''<div class="footer-company-links">
                <span>Company</span>
                <a href="index.html#about">About Us</a>
                <a href="index.html#contact">Contact</a>
                <a href="pricing.html">Pricing</a>
                <a href="privacy-policy.html">Privacy Policy</a>
                <a href="terms-of-service.html">Terms of Service</a>
                <a href="dmca-en.html">DMCA</a>
                <a href="blog.html">Blog</a>
            </div>'''
            
            content = content[:footer_match.start()] + new_footer_links + content[footer_match.end():]
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, "Replaced footer-company-links with complete version"
            except Exception as e:
                return False, f"Error saving: {e}"
    
    return False, "Footer-company-links not found"

def main():
    root_dir = Path(__file__).parent
    
    # Files that need fixing
    files_to_fix = [
        'background-workspace.html',
        'server/public/background-workspace.html'
    ]
    
    print("🔧 Fixing Missing Footer Links...\n")
    print("="*80)
    
    fixed_count = 0
    
    for file_name in files_to_fix:
        file_path = root_dir / file_name
        
        if not file_path.exists():
            continue
        
        relative_path = file_path.relative_to(root_dir)
        print(f"📄 Checking: {relative_path}")
        
        success, message = fix_footer_links(file_path)
        
        if success:
            print(f"   ✅ Fixed: {message}")
            fixed_count += 1
        else:
            print(f"   ℹ️  {message}")
    
    print("\n" + "="*80)
    print(f"✅ Fixed {fixed_count} files")
    print("="*80)

if __name__ == '__main__':
    main()

