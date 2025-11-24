#!/usr/bin/env python3
"""
Add consistent breadcrumb navigation to all HTML pages
Layout: Home | Sign In | Signup
Should be below header on all pages
"""

import os
import re
from pathlib import Path

# Standard breadcrumb HTML
BREADCRUMB_HTML = '''    <nav aria-label="Breadcrumb" style="padding: 15px 0; background: #f8f9ff; border-bottom: 1px solid #e2e6ff;">
        <div class="container" style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
            <ol style="list-style: none; display: flex; flex-wrap: wrap; gap: 10px; margin: 0; padding: 0; align-items: center;">
                <li><a href="index.html" style="color: #4361ee; text-decoration: none; font-weight: 500; transition: color 0.3s;" onmouseover="this.style.color='#3a0ca3'" onmouseout="this.style.color='#4361ee'">Home</a></li>
                <li><span style="margin: 0 8px; color: #9ca3af;">|</span></li>
                <li><a href="login.html" style="color: #56607a; font-weight: 500; text-decoration: none; transition: color 0.3s;" onmouseover="this.style.color='#4361ee'" onmouseout="this.style.color='#56607a'">Sign In</a></li>
                <li><span style="margin: 0 8px; color: #9ca3af;">|</span></li>
                <li><a href="signup.html" style="color: #56607a; font-weight: 500; text-decoration: none; transition: color 0.3s;" onmouseover="this.style.color='#4361ee'" onmouseout="this.style.color='#56607a'">Signup</a></li>
            </ol>
        </div>
    </nav>'''

def get_page_name_from_path(file_path):
    """Get page name from file path for breadcrumb"""
    filename = os.path.basename(file_path)
    if filename == 'index.html':
        return 'Home'
    # Remove .html and convert to readable format
    name = filename.replace('.html', '').replace('-', ' ').replace('_', ' ')
    # Capitalize first letter of each word
    name = ' '.join(word.capitalize() for word in name.split())
    return name

def add_breadcrumb_to_page(file_path):
    """Add or update breadcrumb navigation in HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Check if breadcrumb already exists
        breadcrumb_pattern = r'<nav[^>]*aria-label="Breadcrumb"[^>]*>.*?</nav>'
        existing_breadcrumb = re.search(breadcrumb_pattern, content, re.DOTALL)
        
        # Find where to insert breadcrumb (after </header> or after <body>)
        header_close_pattern = r'</header>'
        body_pattern = r'<body[^>]*>'
        
        if existing_breadcrumb:
            # Replace existing breadcrumb with standard one
            content = re.sub(breadcrumb_pattern, BREADCRUMB_HTML, content, flags=re.DOTALL)
            changes_made.append("Updated breadcrumb navigation")
        else:
            # Add breadcrumb after header
            if re.search(header_close_pattern, content):
                content = re.sub(
                    header_close_pattern,
                    header_close_pattern + '\n' + BREADCRUMB_HTML,
                    content,
                    count=1
                )
                changes_made.append("Added breadcrumb navigation after header")
            # Or add after body if no header
            elif re.search(body_pattern, content):
                # Find first element after body
                body_match = re.search(body_pattern, content)
                if body_match:
                    insert_pos = body_match.end()
                    # Find next tag after body
                    next_tag_match = re.search(r'<[^/]', content[insert_pos:])
                    if next_tag_match:
                        actual_pos = insert_pos + next_tag_match.start()
                        content = content[:actual_pos] + '\n' + BREADCRUMB_HTML + '\n    ' + content[actual_pos:]
                        changes_made.append("Added breadcrumb navigation after body")
        
        # Remove auth buttons from header if they exist in nav-links
        # Check for Sign In and Signup in nav-links
        nav_links_pattern = r'(<div class="nav-links">.*?)(<a[^>]*href="login\.html"[^>]*>Sign In</a>.*?)(<a[^>]*href="signup\.html"[^>]*>Signup</a>.*?)(</div>)'
        if re.search(nav_links_pattern, content, re.DOTALL):
            # Remove Sign In and Signup from nav-links
            content = re.sub(
                r'<a[^>]*href="login\.html"[^>]*class="nav-link"[^>]*>Sign In</a>\s*',
                '',
                content
            )
            content = re.sub(
                r'<a[^>]*href="signup\.html"[^>]*class="nav-link"[^>]*>Signup</a>\s*',
                '',
                content
            )
            changes_made.append("Removed Sign In/Signup from header nav-links")
        
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
        updated, changes = add_breadcrumb_to_page(file_path)
        if updated:
            print(f"✅ Updated {file_path}: {', '.join(changes)}")
            updated_count += 1
        else:
            print(f"⏭️  Skipped: {file_path} (already has breadcrumb or no header found)")
    
    print(f"\n✅ Total files updated: {updated_count}")

if __name__ == "__main__":
    main()

