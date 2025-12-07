#!/usr/bin/env python3
"""
Script to add social media links and search bar to footer in all HTML files
"""
import os
import re
from pathlib import Path

# Social media links
X_LINK = "https://x.com/easyjpgtopdf"
YOUTUBE_LINK = "https://www.youtube.com/@EasyJpgtoPdf"

# Footer pattern to find
FOOTER_PATTERN = r'(<p class="footer-credits">\s*Thanks to every open-source contributor powering this site\.\s*<a href="attributions\.html">See full acknowledgements</a>\.\s*</p>)'

# New footer content with social links and search bar
NEW_FOOTER_CONTENT = '''            <p class="footer-credits">
                Thanks to every open-source contributor powering this site. <a href="attributions.html">See full acknowledgements</a>.
            </p>
            <div class="footer-social-search" style="display: flex; align-items: center; justify-content: space-between; margin-top: 20px; padding-top: 20px; border-top: 1px solid #444; flex-wrap: wrap; gap: 15px;">
                <div class="footer-social-links" style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <a href="''' + X_LINK + '''" target="_blank" rel="noopener noreferrer" title="Follow us on X (Twitter)" style="display: inline-flex; align-items: center; gap: 8px; color: #aaa; text-decoration: none; transition: color 0.3s;" onmouseover="this.style.color='#fff'" onmouseout="this.style.color='#aaa'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                        </svg>
                        <span style="font-size: 0.9rem;">@easyjpgtopdf</span>
                    </a>
                    <a href="''' + YOUTUBE_LINK + '''" target="_blank" rel="noopener noreferrer" title="Subscribe to our YouTube channel" style="display: inline-flex; align-items: center; gap: 8px; color: #aaa; text-decoration: none; transition: color 0.3s;" onmouseover="this.style.color='#fff'" onmouseout="this.style.color='#aaa'">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                        </svg>
                        <span style="font-size: 0.9rem;">@EasyJpgtoPdf</span>
                    </a>
                    <div style="display: inline-flex; align-items: center; gap: 8px; color: #aaa; cursor: default;" title="Mobile App Coming Soon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                            <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.95-3.24-1.44-2.24-1.01-4.33-1.95-5.99-3.22C2.79 14.25.99 12.12.99 9.12c0-2.23 1.21-4.15 3.29-5.19.4-.2.81-.38 1.24-.52.7-.23 1.23-.52 1.62-.82.49-.38.85-.88 1.06-1.46.19-.57.24-1.17.14-1.8-.09-.63-.29-1.24-.58-1.81L7.76.36c.16-.24.35-.45.57-.62.22-.17.46-.3.72-.4.26-.1.54-.15.82-.15.28 0 .56.05.82.15.26.1.5.23.72.4.22.17.41.38.57.62l1.39 2.06c.29.57.49 1.18.58 1.81.1.63.05 1.23-.14 1.8-.21.58-.57 1.08-1.06 1.46-.39.3-.92.59-1.62.82-.43.14-.84.32-1.24.52-2.08 1.04-3.29 2.96-3.29 5.19 0 3 1.8 5.13 4.5 6.5 1.66 1.27 3.75 2.21 5.99 3.22 1.16.49 2.15.94 3.24 1.44 1.03.48 2.1.55 3.08-.4 1.01-.98 1.01-2.4.01-3.38z"/>
                        </svg>
                        <span style="font-size: 0.9rem;">App Coming Soon</span>
                    </div>
                </div>
                <div class="footer-search" style="flex: 1; min-width: 200px; max-width: 300px;">
                    <form action="https://www.google.com/search" method="get" target="_blank" style="display: flex; gap: 5px;">
                        <input type="hidden" name="sitesearch" value="easyjpgtopdf.com">
                        <input type="text" name="q" placeholder="Search our site..." style="flex: 1; padding: 8px 12px; border: 1px solid #555; border-radius: 4px; background: #2a2a2a; color: #fff; font-size: 0.9rem; outline: none;" onfocus="this.style.borderColor='#4361ee'" onblur="this.style.borderColor='#555'">
                        <button type="submit" style="padding: 8px 15px; background: #4361ee; border: none; border-radius: 4px; color: #fff; cursor: pointer; transition: background 0.3s;" onmouseover="this.style.background='#3a0ca3'" onmouseout="this.style.background='#4361ee'">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                            </svg>
                        </button>
                    </form>
                </div>
            </div>'''

def update_footer_in_file(file_path):
    """Update footer in a single HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if footer already has social links (to avoid duplicates)
        if 'footer-social-search' in content:
            print(f"  ⏭️  Skipping {file_path.name} - already updated")
            return False
        
        # Find and replace footer pattern
        pattern = re.compile(FOOTER_PATTERN, re.MULTILINE | re.DOTALL)
        
        if pattern.search(content):
            new_content = pattern.sub(NEW_FOOTER_CONTENT, content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✅ Updated {file_path.name}")
            return True
        else:
            print(f"  ⚠️  Footer pattern not found in {file_path.name}")
            return False
    except Exception as e:
        print(f"  ❌ Error updating {file_path.name}: {e}")
        return False

def main():
    """Main function to update all HTML files"""
    print("🔍 Finding all HTML files with footer...")
    
    # Get all HTML files in the root directory
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

