#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Schema Markup, Breadcrumbs, and Trust Badges to all pages
"""

import os
import re
from pathlib import Path
from datetime import datetime

def add_schema_markup(content, filename, page_type='WebPage'):
    """Add structured data (Schema.org markup)"""
    if 'application/ld+json' in content:
        return content  # Already has schema
    
    # Extract title and description
    title_match = re.search(r'<title>(.*?)</title>', content)
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content)
    
    title = title_match.group(1) if title_match else 'easyjpgtopdf'
    description = desc_match.group(1) if desc_match else 'Online PDF and image conversion tools'
    
    url = f'https://easyjpgtopdf.com/{filename}'
    
    if page_type == 'Article' or 'blog-' in filename:
        schema = f'''    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "description": "{description}",
      "author": {{
        "@type": "Person",
        "name": "easyjpgtopdf Team"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "easyjpgtopdf",
        "logo": {{
          "@type": "ImageObject",
          "url": "https://easyjpgtopdf.com/images/logo.png"
        }}
      }},
      "datePublished": "{datetime.now().strftime('%Y-%m-%d')}",
      "dateModified": "{datetime.now().strftime('%Y-%m-%d')}"
    }}
    </script>'''
    else:
        schema = f'''    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": "{title}",
      "description": "{description}",
      "url": "{url}",
      "inLanguage": "en-US",
      "isPartOf": {{
        "@type": "WebSite",
        "name": "easyjpgtopdf",
        "url": "https://easyjpgtopdf.com"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "easyjpgtopdf",
        "url": "https://easyjpgtopdf.com"
      }}
    }}
    </script>'''
    
    # Add before closing head tag
    content = re.sub(r'(</head>)', schema + r'\n\1', content)
    return content

def add_breadcrumbs(content, filename):
    """Add breadcrumb navigation"""
    if 'aria-label="Breadcrumb"' in content:
        return content  # Already has breadcrumbs
    
    # Determine breadcrumb items based on filename
    if filename == 'index.html':
        items = [('Home', 'index.html')]
    elif 'blog-' in filename:
        items = [
            ('Home', 'index.html'),
            ('Blog', 'blog.html'),
            (filename.replace('blog-', '').replace('.html', '').replace('-', ' ').title(), filename)
        ]
    elif filename.endswith('.html') and filename != 'index.html':
        tool_name = filename.replace('.html', '').replace('-', ' ').title()
        items = [
            ('Home', 'index.html'),
            (tool_name, filename)
        ]
    else:
        return content  # Skip if can't determine
    
    breadcrumb_html = '''
    <nav aria-label="Breadcrumb" style="padding: 15px 0; background: #f8f9ff; border-bottom: 1px solid #e2e6ff;">
        <div class="container" style="max-width: 1200px; margin: 0 auto; padding: 0 24px;">
            <ol style="list-style: none; display: flex; flex-wrap: wrap; gap: 10px; margin: 0; padding: 0; align-items: center;">
'''
    
    for i, (name, url) in enumerate(items):
        if i == len(items) - 1:
            breadcrumb_html += f'                <li style="color: #56607a; font-weight: 500;">{name}</li>\n'
        else:
            breadcrumb_html += f'                <li><a href="{url}" style="color: #4361ee; text-decoration: none; font-weight: 500;">{name}</a> <span style="margin: 0 8px; color: #9ca3af;">/</span></li>\n'
    
    breadcrumb_html += '''            </ol>
        </div>
    </nav>
'''
    
    # Add after header, before main content
    if '</header>' in content:
        content = re.sub(r'(</header>)', r'\1\n' + breadcrumb_html, content)
    elif '<main' in content:
        content = re.sub(r'(<main[^>]*>)', breadcrumb_html + r'\1', content)
    elif '<body' in content and '<header' not in content:
        # Add after body tag if no header
        content = re.sub(r'(<body[^>]*>)', rf'\1\n{breadcrumb_html}', content)
    
    return content

def add_trust_badges(content):
    """Add trust badges and SSL seal"""
    if 'trust-badges' in content or 'SSL Secured' in content:
        return content  # Already has trust badges
    
    trust_badges = '''
    <div class="trust-badges" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #f8f9ff, #ffffff); border-radius: 12px; margin: 30px 0; border: 2px solid #e2e6ff;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 40px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-shield-alt" style="font-size: 2rem; color: #4361ee;"></i>
                <div style="text-align: left;">
                    <div style="color: #0b1630; font-weight: 600; font-size: 1.1rem;">SSL Secured</div>
                    <div style="color: #56607a; font-size: 0.9rem;">256-bit Encryption</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-lock" style="font-size: 2rem; color: #4361ee;"></i>
                <div style="text-align: left;">
                    <div style="color: #0b1630; font-weight: 600; font-size: 1.1rem;">100% Secure</div>
                    <div style="color: #56607a; font-size: 0.9rem;">Files Auto-Deleted</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-check-circle" style="font-size: 2rem; color: #4361ee;"></i>
                <div style="text-align: left;">
                    <div style="color: #0b1630; font-weight: 600; font-size: 1.1rem;">AdSense Verified</div>
                    <div style="color: #56607a; font-size: 0.9rem;">Google Approved</div>
                </div>
            </div>
        </div>
    </div>
'''
    
    # Add before footer or at end of main
    if '</main>' in content:
        content = content.replace('</main>', trust_badges + '</main>')
    elif '<footer' in content:
        content = re.sub(r'(<footer)', trust_badges + r'\1', content)
    elif '</body>' in content:
        content = re.sub(r'(</body>)', trust_badges + r'\1', content)
    
    return content

def process_file(filepath):
    """Process a single file"""
    filename = os.path.basename(filepath)
    
    # Skip certain files
    if filename.startswith('_') or filename.startswith('.'):
        return False
    
    if not filename.endswith('.html'):
        return False
    
    # Skip convert pages and other utility pages
    if '-convert.html' in filename or filename in ['test-', 'result.html']:
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Determine page type
        page_type = 'Article' if 'blog-' in filename else 'WebPage'
        
        # Add schema markup
        content = add_schema_markup(content, filename, page_type)
        
        # Add breadcrumbs
        content = add_breadcrumbs(content, filename)
        
        # Add trust badges (only for main pages, not blog articles)
        if 'blog-' not in filename:
            content = add_trust_badges(content)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f'✗ Error processing {filename}: {str(e)}')
        return False

def main():
    """Main function"""
    print('=' * 70)
    print('Add Schema Markup, Breadcrumbs, and Trust Badges')
    print('=' * 70)
    print()
    
    # Find all HTML files
    html_files = list(Path('.').glob('*.html'))
    html_files = [f for f in html_files if f.is_file()]
    
    print(f'Found {len(html_files)} HTML files')
    print()
    
    success_count = 0
    for html_file in html_files:
        filename = os.path.basename(html_file)
        if process_file(html_file):
            print(f'✓ Updated: {filename}')
            success_count += 1
    
    print()
    print('=' * 70)
    print(f'Processing complete: {success_count} files updated')
    print('=' * 70)

if __name__ == '__main__':
    main()

