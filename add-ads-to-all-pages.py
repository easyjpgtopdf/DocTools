#!/usr/bin/env python3
"""
Script to add advertisement spaces to all HTML pages
Adds top banner, bottom banner, and CSS link to all HTML files
"""

import os
import re
from pathlib import Path

# Files already updated manually
MANUALLY_UPDATED = {
    'index.html',
    'blog.html',
    'background-workspace.html'
}

def add_ads_to_html_file(file_path):
    """Add advertisement spaces to an HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Skip if already updated manually
        if os.path.basename(file_path) in MANUALLY_UPDATED:
            print(f"⏭️  Skipping {file_path} (already updated manually)")
            return False
        
        # Check if already has ad spaces
        if 'ad-banner-top' in content and 'advertisement.css' in content:
            print(f"✅ {file_path} already has ad spaces")
            return False
        
        # 1. Add advertisement CSS link if not present
        css_link = '<link rel="stylesheet" href="css/advertisement.css">'
        css_patterns = [
            r'(<link[^>]*href=["\']css/theme-modern\.css["\'][^>]*>)',
            r'(<link[^>]*href=["\']css/header\.css["\'][^>]*>)',
            r'(<link[^>]*href=["\']css/footer\.css["\'][^>]*>)'
        ]
        
        if css_link not in content:
            for pattern in css_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    content = content[:match.end()] + '\n    ' + css_link + content[match.end():]
                    break
        
        # 2. Add top banner after header
        if 'ad-banner-top' not in content:
            # Find </header> tag
            header_patterns = [
                r'(</header>\s*)(\n\s*)(<!--.*?-->)?(\n\s*)(<main)',
                r'(</header>\s*)(\n\s*)(<!--.*?-->)?(\n\s*)(<section)',
                r'(</header>\s*)(\n\s*)(<!--.*?-->)?(\n\s*)(<div)',
                r'(</header>\s*)(\n)',
            ]
            
            for pattern in header_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    top_banner = '\n    <!-- Top Advertisement Banner -->\n    <div class="container">\n        <div class="ad-banner-top"></div>\n    </div>\n'
                    content = content[:match.end(0)] + top_banner + content[match.end(0):]
                    break
        
        # 3. Add bottom banner before </body>
        if 'ad-banner-bottom' not in content:
            # Find </body> tag (avoid script tags before it)
            body_patterns = [
                r'(</footer>\s*)(\n\s*)(</body>)',
                r'(</script>\s*)(\n\s*)(</body>)',
                r'(\n\s*)(</body>)',
            ]
            
            for pattern in body_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    bottom_banner = '\n    <!-- Bottom Advertisement Banner -->\n    <div class="container">\n        <div class="ad-banner-bottom"></div>\n    </div>\n'
                    content = content[:match.start(0)] + bottom_banner + content[match.start(0):]
                    break
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated {file_path}")
            return True
        else:
            print(f"⚠️  No changes made to {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all HTML files"""
    # Get current directory
    base_dir = Path(__file__).parent
    
    # Find all HTML files
    html_files = list(base_dir.glob('*.html'))
    html_files.extend(base_dir.glob('**/*.html'))
    
    # Exclude node_modules, server/public/backups, etc.
    excluded_dirs = {'node_modules', '__pycache__', '.git', 'backups', 'server/public/backups'}
    html_files = [
        f for f in html_files 
        if not any(excluded in str(f) for excluded in excluded_dirs)
    ]
    
    # Remove duplicates
    html_files = list(set(html_files))
    
    print(f"📄 Found {len(html_files)} HTML files to process\n")
    
    updated_count = 0
    for html_file in sorted(html_files):
        if add_ads_to_html_file(html_file):
            updated_count += 1
    
    print(f"\n✨ Done! Updated {updated_count} files")

if __name__ == '__main__':
    main()

