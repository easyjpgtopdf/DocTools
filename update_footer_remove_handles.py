#!/usr/bin/env python3
"""
Script to remove handle names from footer social links and update search form
"""
import os
import re
from pathlib import Path

# Pattern to find footer social links with handles
OLD_SOCIAL_PATTERN = r'(<a href="https://x\.com/easyjpgtopdf"[^>]*>.*?<span style="font-size: 0\.9rem;">@easyjpgtopdf</span>.*?</a>)'
OLD_YOUTUBE_PATTERN = r'(<a href="https://www\.youtube\.com/@EasyJpgtoPdf"[^>]*>.*?<span style="font-size: 0\.9rem;">@EasyJpgtoPdf</span>.*?</a>)'

# New social links without handles (only logos)
NEW_X_LINK = '''                    <a href="https://x.com/easyjpgtopdf" target="_blank" rel="noopener noreferrer" title="Follow us on X (Twitter)" style="display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; color: #aaa; text-decoration: none; transition: all 0.3s; border-radius: 50%;" onmouseover="this.style.color='#fff'; this.style.background='rgba(255,255,255,0.1)'" onmouseout="this.style.color='#aaa'; this.style.background='transparent'">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                        </svg>
                    </a>'''

NEW_YOUTUBE_LINK = '''                    <a href="https://www.youtube.com/@EasyJpgtoPdf" target="_blank" rel="noopener noreferrer" title="Subscribe to our YouTube channel" style="display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; color: #aaa; text-decoration: none; transition: all 0.3s; border-radius: 50%;" onmouseover="this.style.color='#fff'; this.style.background='rgba(255,255,255,0.1)'" onmouseout="this.style.color='#aaa'; this.style.background='transparent'">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                        </svg>
                    </a>'''

# Pattern to find old search form
OLD_SEARCH_FORM = r'(<form action="https://www\.google\.com/search"[^>]*>.*?</form>)'

# New search form pointing to search.html
NEW_SEARCH_FORM = '''                    <form action="search.html" method="get" style="display: flex; gap: 5px;">
                        <input type="text" name="q" placeholder="Search our site..." style="flex: 1; padding: 8px 12px; border: 1px solid #555; border-radius: 4px; background: #2a2a2a; color: #fff; font-size: 0.9rem; outline: none;" onfocus="this.style.borderColor='#4361ee'" onblur="this.style.borderColor='#555'">
                        <button type="submit" style="padding: 8px 15px; background: #4361ee; border: none; border-radius: 4px; color: #fff; cursor: pointer; transition: background 0.3s;" onmouseover="this.style.background='#3a0ca3'" onmouseout="this.style.background='#4361ee'">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                            </svg>
                        </button>
                    </form>'''

def update_footer_in_file(file_path):
    """Update footer in a single HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace X.com link
        x_pattern = re.compile(r'<a href="https://x\.com/easyjpgtopdf"[^>]*>.*?<span[^>]*>@easyjpgtopdf</span>.*?</a>', re.DOTALL)
        content = x_pattern.sub(NEW_X_LINK, content)
        
        # Replace YouTube link
        yt_pattern = re.compile(r'<a href="https://www\.youtube\.com/@EasyJpgtoPdf"[^>]*>.*?<span[^>]*>@EasyJpgtoPdf</span>.*?</a>', re.DOTALL)
        content = yt_pattern.sub(NEW_YOUTUBE_LINK, content)
        
        # Replace search form
        search_pattern = re.compile(r'<form action="https://www\.google\.com/search"[^>]*>.*?</form>', re.DOTALL)
        content = search_pattern.sub(NEW_SEARCH_FORM, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Updated {file_path.name}")
            return True
        else:
            print(f"  ⏭️  No changes needed in {file_path.name}")
            return False
    except Exception as e:
        print(f"  ❌ Error updating {file_path.name}: {e}")
        return False

def main():
    """Main function to update all HTML files"""
    print("🔍 Finding all HTML files with footer...")
    
    html_files = []
    root = Path('.')
    
    for html_file in root.glob('*.html'):
        if html_file.is_file():
            html_files.append(html_file)
    
    print(f"📁 Found {len(html_files)} HTML files")
    print("\n🔄 Updating footers...\n")
    
    updated_count = 0
    for html_file in sorted(html_files):
        if update_footer_in_file(html_file):
            updated_count += 1
    
    print(f"\n✨ Done! Updated {updated_count} files")

if __name__ == '__main__':
    main()

