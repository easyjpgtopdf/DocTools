#!/usr/bin/env python3
"""
Clean and optimize edit-pdf.html and edit-pdf-preview.html
- Remove unused CSS and components
- Optimize SEO with high-volume keywords
- Fix schema markup
- Add proper H1/H2 tags
- Remove duplicate content
"""

import re
import os

# High-volume SEO keywords
EDIT_PDF_KEYWORDS = {
    'title': 'PDF Editor Online Free - Edit PDF Files Online Without Installation | easyjpgtopdf',
    'description': 'Edit PDF files online for free. Add text, images, annotations, modify PDF documents, highlight content - all without software installation. Best free online PDF editor 2024.',
    'keywords': 'pdf editor online free, edit pdf online, free pdf editor, online pdf editor, edit pdf files, pdf editing tool, modify pdf, edit pdf documents, pdf editor free online, best pdf editor online, edit pdf online free no download, pdf editor website, free online pdf editor, edit pdf text, pdf editor tool',
    'h1': 'PDF Editor Online Free - Edit PDF Files Online Without Installation',
    'h2_1': 'How to Edit PDF Files Online for Free',
    'h2_2': 'Features of Our Free PDF Editor',
    'h2_3': 'Why Choose Our Online PDF Editor'
}

PREVIEW_KEYWORDS = {
    'title': 'Advanced PDF Editor Online - Edit PDF Files with Real-Time Preview | easyjpgtopdf',
    'description': 'Advanced PDF editor online with real-time editing, full A4 preview, text editing, image insertion, OCR, and professional editing tools. Edit PDF files online free without installation.',
    'keywords': 'advanced pdf editor online, pdf editor online free, edit pdf online, free pdf editor, online pdf editor, edit pdf files online, pdf editor tool, edit pdf documents, pdf editor software, edit pdf text, pdf editor free online, best pdf editor online, edit pdf online free no download, pdf editor website, edit pdf online tool, free online pdf editor, real-time pdf editor',
    'h1': 'Advanced PDF Editor Online - Edit PDF Files with Real-Time Preview',
    'h2_1': 'Real-Time PDF Editing Features',
    'h2_2': 'Professional PDF Editing Tools',
    'h2_3': 'How to Use Our Advanced PDF Editor'
}

def remove_unused_css(content):
    """Remove unused CSS classes"""
    # Remove unused editor-section, toolbar, tool-group CSS (not used in preview page)
    patterns_to_remove = [
        r'\.editor-section\s*\{[^}]*\}',
        r'\.editor-section\s+h3\s*\{[^}]*\}',
        r'\.editor-container\s*\{[^}]*\}',
        r'\.toolbar\s*\{[^}]*\}',
        r'\.tool-group[^{]*\{[^}]*\}',
        r'\.tool-group-title[^{]*\{[^}]*\}',
        r'\.tool-btn[^{]*\{[^}]*\}',
        r'\.color-picker-container[^{]*\{[^}]*\}',
        r'\.font-controls[^{]*\{[^}]*\}',
        r'\.highlight-controls[^{]*\{[^}]*\}',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove media queries for unused classes
    content = re.sub(r'@media[^{]*\{[^}]*\.toolbar[^}]*\}', '', content, flags=re.MULTILINE | re.DOTALL)
    content = re.sub(r'@media[^{]*\{[^}]*\.tool-group[^}]*\}', '', content, flags=re.MULTILINE | re.DOTALL)
    
    return content

def remove_duplicate_schema(content):
    """Remove duplicate schema markup"""
    # Find all schema blocks
    schema_pattern = r'<script\s+type="application/ld\+json">\s*\{[^<]*\}</script>'
    schemas = re.findall(schema_pattern, content, re.DOTALL)
    
    if len(schemas) > 1:
        # Keep only the first one
        content = re.sub(schema_pattern, '', content, flags=re.DOTALL, count=len(schemas) - 1)
    
    return content

def remove_tesseract_js(content):
    """Remove Tesseract.js script (using backend OCR now)"""
    content = re.sub(r'<script[^>]*tesseract\.js[^<]*</script>', '', content, flags=re.IGNORECASE)
    return content

def update_seo_meta(content, keywords):
    """Update SEO meta tags"""
    # Update title
    content = re.sub(r'<title>.*?</title>', f'<title>{keywords["title"]}</title>', content, flags=re.DOTALL)
    
    # Update description
    content = re.sub(r'<meta\s+name="description"\s+content="[^"]*"', 
                    f'<meta name="description" content="{keywords["description"]}"', content)
    
    # Update keywords
    if re.search(r'<meta\s+name="keywords"', content):
        content = re.sub(r'<meta\s+name="keywords"\s+content="[^"]*"', 
                        f'<meta name="keywords" content="{keywords["keywords"]}"', content)
    else:
        # Add keywords meta if missing
        content = re.sub(r'(<meta\s+name="description"[^>]*>)', 
                        f'\\1\n    <meta name="keywords" content="{keywords["keywords"]}">', content)
    
    return content

def update_schema_markup(content, is_preview=False):
    """Update schema markup to WebApplication type"""
    url = 'https://easyjpgtopdf.com/edit-pdf-preview.html' if is_preview else 'https://easyjpgtopdf.com/edit-pdf.html'
    name = 'Advanced PDF Editor Online' if is_preview else 'PDF Editor Online Free'
    desc = PREVIEW_KEYWORDS['description'] if is_preview else EDIT_PDF_KEYWORDS['description']
    
    new_schema = f'''    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "WebApplication",
      "name": "{name}",
      "description": "{desc}",
      "url": "{url}",
      "applicationCategory": "UtilityApplication",
      "operatingSystem": "Any",
      "offers": {{
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD"
      }},
      "featureList": [
        "Edit PDF text online",
        "Add images to PDF",
        "OCR text recognition",
        "Real-time PDF editing",
        "Full A4 preview",
        "No software installation required"
      ],
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
      }},
      "author": {{
        "@type": "Person",
        "name": "Riyaz Mohammad"
      }}
    }}
    </script>'''
    
    # Replace existing schema
    schema_pattern = r'<script\s+type="application/ld\+json">.*?</script>'
    content = re.sub(schema_pattern, new_schema, content, flags=re.DOTALL)
    
    return content

def update_h1_h2_tags(content, keywords):
    """Update H1 and H2 tags with SEO keywords"""
    # Update H1
    content = re.sub(r'<h1[^>]*>.*?</h1>', f'<h1>{keywords["h1"]}</h1>', content, flags=re.DOTALL)
    
    # Check if H2 tags exist, if not add them in features section
    if not re.search(r'<h2[^>]*>', content):
        # Add H2 tags in features section
        features_pattern = r'(<div class="features">)'
        h2_content = f'''\\1
<h2 style="text-align: center; font-size: 1.8rem; color: var(--primary); margin: 30px 0 20px; font-weight: 700;">{keywords["h2_2"]}</h2>'''
        content = re.sub(features_pattern, h2_content, content)
    
    return content

def remove_unused_js_references(content):
    """Remove unused JavaScript variable references"""
    # Remove editorSection reference if not used
    if 'editorSection' in content and 'getElementById(\'editor-section\')' not in content:
        content = re.sub(r'const\s+editorSection\s*=.*?;', '', content)
    
    return content

def clean_file(file_path, keywords, is_preview=False):
    """Clean and optimize a single file"""
    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print(f"{'='*60}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_size = len(content)
    
    # 1. Remove unused CSS
    print("  ✓ Removing unused CSS...")
    content = remove_unused_css(content)
    
    # 2. Remove duplicate schema
    print("  ✓ Removing duplicate schema markup...")
    content = remove_duplicate_schema(content)
    
    # 3. Remove Tesseract.js (using backend now)
    print("  ✓ Removing Tesseract.js script...")
    content = remove_tesseract_js(content)
    
    # 4. Update SEO meta tags
    print("  ✓ Updating SEO meta tags...")
    content = update_seo_meta(content, keywords)
    
    # 5. Update schema markup
    print("  ✓ Updating schema markup...")
    content = update_schema_markup(content, is_preview)
    
    # 6. Update H1/H2 tags
    print("  ✓ Updating H1/H2 tags...")
    content = update_h1_h2_tags(content, keywords)
    
    # 7. Remove unused JS references
    print("  ✓ Removing unused JS references...")
    content = remove_unused_js_references(content)
    
    # 8. Clean up extra whitespace
    print("  ✓ Cleaning up whitespace...")
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    new_size = len(content)
    reduction = original_size - new_size
    
    print(f"\n  ✅ Complete!")
    print(f"  Original size: {original_size:,} bytes")
    print(f"  New size: {new_size:,} bytes")
    print(f"  Reduced by: {reduction:,} bytes ({reduction/original_size*100:.1f}%)")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return reduction

def main():
    """Main function"""
    print("="*60)
    print("PDF Editor Pages - Clean & Optimize")
    print("="*60)
    
    files = [
        ('edit-pdf.html', EDIT_PDF_KEYWORDS, False),
        ('edit-pdf-preview.html', PREVIEW_KEYWORDS, True)
    ]
    
    total_reduction = 0
    for file_path, keywords, is_preview in files:
        if os.path.exists(file_path):
            reduction = clean_file(file_path, keywords, is_preview)
            total_reduction += reduction
        else:
            print(f"\n❌ File not found: {file_path}")
    
    print("\n" + "="*60)
    print(f"✅ All files processed!")
    print(f"Total size reduction: {total_reduction:,} bytes")
    print("="*60)

if __name__ == '__main__':
    main()

