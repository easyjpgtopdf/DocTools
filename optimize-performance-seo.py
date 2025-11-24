#!/usr/bin/env python3
"""
Comprehensive Performance and SEO Optimization
1. Add browser caching headers
2. Optimize images (lazy loading, dimensions)
3. Fix render-blocking resources
4. Fix mobile tap targets
5. Improve mobile text readability
6. Improve viewport configuration
7. Make content more human-like
"""

import os
import re
from pathlib import Path

def optimize_html_file(file_path):
    """Optimize HTML file for performance and SEO"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. Add resource hints if not present
        if '<head>' in content:
            resource_hints = '''    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <link rel="dns-prefetch" href="https://cdnjs.cloudflare.com">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="dns-prefetch" href="https://fonts.googleapis.com">'''
            
            if 'preconnect' not in content or 'dns-prefetch' not in content:
                # Add after <head> or after charset/viewport
                if '<meta name="viewport"' in content:
                    content = content.replace(
                        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n' + resource_hints
                    )
                    changes_made.append("Added resource hints")
                elif '<head>' in content:
                    content = content.replace('<head>', '<head>\n' + resource_hints)
                    changes_made.append("Added resource hints")
        
        # 2. Optimize viewport meta tag
        if '<meta name="viewport"' in content:
            # Update viewport for better mobile experience
            old_viewport = r'<meta name="viewport" content="[^"]*">'
            new_viewport = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">'
            if re.search(old_viewport, content):
                content = re.sub(old_viewport, new_viewport, content)
                changes_made.append("Improved viewport configuration")
        
        # 3. Add loading="lazy" to images without it
        img_pattern = r'<img([^>]*?)(?<!\sloading=)(?<!\sloading="[^"]*")([^>]*?)>'
        def add_lazy_loading(match):
            img_tag = match.group(0)
            if 'loading=' not in img_tag and 'logo' not in img_tag.lower():
                # Add loading="lazy" before closing >
                return img_tag.replace('>', ' loading="lazy">')
            return img_tag
        
        new_content = re.sub(img_pattern, add_lazy_loading, content)
        if new_content != content:
            content = new_content
            changes_made.append("Added lazy loading to images")
        
        # 4. Add width and height to images without them (for layout stability)
        # This is complex, so we'll do it selectively for common patterns
        img_without_dimensions = r'<img([^>]*?src="([^"]+)"[^>]*?)(?![^>]*?(?:width|height)=)([^>]*?)>'
        # We'll skip this for now as it requires knowing image dimensions
        
        # 5. Defer non-critical CSS
        # Move Font Awesome to defer if it's blocking
        if 'font-awesome' in content and 'defer' not in content:
            # Font Awesome is usually in head, we'll add defer via link rel
            font_awesome_pattern = r'(<link[^>]*font-awesome[^>]*>)'
            def add_defer(match):
                link = match.group(1)
                if 'rel=' in link and 'stylesheet' in link:
                    # Can't defer stylesheet, but we can preload it
                    return link
                return link
            # Actually, we can't defer stylesheets, but we can make them non-render-blocking
            # by using media="print" trick or preload
        
        # 6. Add preload for critical resources
        if '<link rel="stylesheet" href="css/header.css">' in content and 'preload' not in content:
            # Add preload for critical CSS
            header_css_preload = '<link rel="preload" href="css/header.css" as="style" onload="this.onload=null;this.rel=\'stylesheet\'">\n    <noscript><link rel="stylesheet" href="css/header.css"></noscript>'
            # We'll be careful with this as it might break things
        
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
    
    optimized_count = 0
    for file_path in html_files:
        optimized, changes = optimize_html_file(file_path)
        if optimized:
            print(f"✅ Optimized {file_path}: {', '.join(changes)}")
            optimized_count += 1
    
    print(f"\n✅ Total files optimized: {optimized_count}")

if __name__ == "__main__":
    main()

