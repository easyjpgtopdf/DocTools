#!/usr/bin/env python3
"""
Add mobile menu initialization script to all HTML pages
Ensures mobile header works properly on all pages
"""

import os
import re
from pathlib import Path

def add_mobile_menu_script(file_path):
    """Add mobile menu init script to HTML file if not present"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if mobile-menu-init.js is already included
        if 'js/mobile-menu-init.js' in content:
            return False
        
        # Check if mobile-menu-toggle exists in the file
        if 'mobile-menu-toggle' not in content:
            return False
        
        # Find the closing body tag
        body_close_pattern = r'</body>'
        
        if re.search(body_close_pattern, content):
            # Add script before </body>
            script_tag = '    <script src="js/mobile-menu-init.js"></script>\n</body>'
            content = re.sub(body_close_pattern, script_tag, content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Process all HTML files"""
    html_files = []
    
    # Find all HTML files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'venv', 'env']]
        
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                html_files.append(file_path)
    
    updated_count = 0
    for file_path in html_files:
        if add_mobile_menu_script(file_path):
            print(f"✅ Updated: {file_path}")
            updated_count += 1
        else:
            print(f"⏭️  Skipped: {file_path}")
    
    print(f"\n✅ Total files updated: {updated_count}")

if __name__ == "__main__":
    main()

