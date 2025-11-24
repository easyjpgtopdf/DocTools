#!/usr/bin/env python3
"""
Remove Sign In and Signup buttons from header on all pages
They should only be in breadcrumb navigation, not in header
"""

import os
import re
from pathlib import Path

def remove_auth_buttons_from_header(file_path):
    """Remove auth buttons from header"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Pattern 1: Remove auth-buttons container div
        auth_buttons_pattern = r'<div class="auth-buttons">.*?</div>'
        if re.search(auth_buttons_pattern, content, re.DOTALL):
            content = re.sub(auth_buttons_pattern, '', content, flags=re.DOTALL)
            changes_made.append("Removed auth-buttons container")
        
        # Pattern 2: Remove individual auth-link and auth-btn from nav-links
        # Remove Sign In link from nav-links
        signin_in_nav_pattern = r'<a[^>]*href="login\.html"[^>]*class="[^"]*nav-link[^"]*"[^>]*>Sign In</a>\s*'
        if re.search(signin_in_nav_pattern, content):
            content = re.sub(signin_in_nav_pattern, '', content)
            changes_made.append("Removed Sign In from nav-links")
        
        # Remove Signup link from nav-links
        signup_in_nav_pattern = r'<a[^>]*href="signup\.html"[^>]*class="[^"]*nav-link[^"]*"[^>]*>Signup</a>\s*'
        if re.search(signup_in_nav_pattern, content):
            content = re.sub(signup_in_nav_pattern, '', content)
            changes_made.append("Removed Signup from nav-links")
        
        # Pattern 3: Remove auth-link and auth-btn with their containers
        auth_link_pattern = r'<a[^>]*href="login\.html"[^>]*class="[^"]*auth-link[^"]*"[^>]*>Sign In</a>'
        if re.search(auth_link_pattern, content):
            content = re.sub(auth_link_pattern, '', content)
            changes_made.append("Removed auth-link")
        
        auth_btn_pattern = r'<a[^>]*href="signup\.html"[^>]*class="[^"]*auth-btn[^"]*"[^>]*>.*?Signup.*?</a>'
        if re.search(auth_btn_pattern, content, re.DOTALL):
            content = re.sub(auth_btn_pattern, '', content, flags=re.DOTALL)
            changes_made.append("Removed auth-btn")
        
        # Clean up any empty auth-buttons divs
        empty_auth_div_pattern = r'<div class="auth-buttons">\s*</div>'
        if re.search(empty_auth_div_pattern, content):
            content = re.sub(empty_auth_div_pattern, '', content)
            changes_made.append("Removed empty auth-buttons div")
        
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
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'venv', 'env', 'server/public/backups', '.venv312', 'excel-unlocker']]
        
        for file in files:
            if file.endswith('.html') and not file.startswith('test-'):
                file_path = os.path.join(root, file)
                html_files.append(file_path)
    
    updated_count = 0
    for file_path in html_files:
        updated, changes = remove_auth_buttons_from_header(file_path)
        if updated:
            print(f"✅ Updated {file_path}: {', '.join(changes)}")
            updated_count += 1
    
    print(f"\n✅ Total files updated: {updated_count}")

if __name__ == "__main__":
    main()

