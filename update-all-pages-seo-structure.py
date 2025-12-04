#!/usr/bin/env python3
"""
Update all HTML pages (except index.html) to match jpg-to-pdf.html structure
Add SEO elements: H1, H2, keywords, schema, canonical URL, meta tags
"""

import os
import re
from pathlib import Path
from urllib.parse import quote

# SEO keywords mapping for each tool/page
SEO_DATA = {
    'word-to-pdf': {
        'title': 'Word to PDF Converter - DOC to PDF Online Free | Convert Word Documents',
        'description': 'Convert Word documents (DOC, DOCX) to PDF format online for free. Fast, secure conversion with preserved formatting. No registration required.',
        'keywords': 'word to pdf, convert word to pdf, doc to pdf, docx to pdf, word pdf converter, free word to pdf, online word to pdf converter',
        'h1': 'Word to PDF Converter - Convert DOC/DOCX to PDF Online Free',
        'h2': 'Upload Word Document',
        'slug': 'word-to-pdf'
    },
    'pdf-to-word': {
        'title': 'PDF to Word Converter - Convert PDF to DOC Online Free | Extract Text from PDF',
        'description': 'Convert PDF to Word documents online for free. Extract and edit text from PDF files. High-quality conversion with preserved formatting.',
        'keywords': 'pdf to word, convert pdf to word, pdf to doc, pdf to docx, extract text from pdf, pdf word converter, free pdf to word',
        'h1': 'PDF to Word Converter - Convert PDF to DOC/DOCX Online Free',
        'h2': 'Upload PDF File',
        'slug': 'pdf-to-word'
    },
    'excel-to-pdf': {
        'title': 'Excel to PDF Converter - Convert XLS to PDF Online Free | Excel PDF Converter',
        'description': 'Convert Excel spreadsheets (XLS, XLSX) to PDF format online for free. Preserve formatting, charts, and layouts. Fast and secure conversion.',
        'keywords': 'excel to pdf, convert excel to pdf, xls to pdf, xlsx to pdf, excel pdf converter, free excel to pdf, online excel to pdf',
        'h1': 'Excel to PDF Converter - Convert XLS/XLSX to PDF Online Free',
        'h2': 'Upload Excel File',
        'slug': 'excel-to-pdf'
    },
    'pdf-to-excel': {
        'title': 'PDF to Excel Converter - Convert PDF to XLS Online Free | Extract Tables from PDF',
        'description': 'Convert PDF to Excel spreadsheets online for free. Extract tables and data from PDF files. Maintain formatting and structure.',
        'keywords': 'pdf to excel, convert pdf to excel, pdf to xls, pdf to xlsx, extract tables from pdf, pdf excel converter, free pdf to excel',
        'h1': 'PDF to Excel Converter - Convert PDF to XLS/XLSX Online Free',
        'h2': 'Upload PDF File',
        'slug': 'pdf-to-excel'
    },
    'ppt-to-pdf': {
        'title': 'PowerPoint to PDF Converter - Convert PPT to PDF Online Free | PPT PDF Converter',
        'description': 'Convert PowerPoint presentations (PPT, PPTX) to PDF format online for free. Preserve slides, animations, and formatting. Fast conversion.',
        'keywords': 'ppt to pdf, powerpoint to pdf, convert ppt to pdf, pptx to pdf, powerpoint pdf converter, free ppt to pdf, online ppt to pdf',
        'h1': 'PowerPoint to PDF Converter - Convert PPT/PPTX to PDF Online Free',
        'h2': 'Upload PowerPoint File',
        'slug': 'ppt-to-pdf'
    },
    'pdf-to-ppt': {
        'title': 'PDF to PowerPoint Converter - Convert PDF to PPT Online Free | PDF PPT Converter',
        'description': 'Convert PDF to PowerPoint presentations online for free. Extract content and create editable PPT files. High-quality conversion.',
        'keywords': 'pdf to ppt, pdf to powerpoint, convert pdf to ppt, pdf to pptx, pdf powerpoint converter, free pdf to ppt, online pdf to ppt',
        'h1': 'PDF to PowerPoint Converter - Convert PDF to PPT/PPTX Online Free',
        'h2': 'Upload PDF File',
        'slug': 'pdf-to-ppt'
    },
    'merge-pdf': {
        'title': 'Merge PDF Files - Combine Multiple PDFs Online Free | PDF Merger Tool',
        'description': 'Merge multiple PDF files into one document online for free. Combine PDFs in any order. Fast, secure, and no file size limits.',
        'keywords': 'merge pdf, combine pdf files, join pdf, pdf merger, merge pdf online, free pdf merger, combine multiple pdfs',
        'h1': 'Merge PDF Files - Combine Multiple PDFs Online Free',
        'h2': 'Upload PDF Files',
        'slug': 'merge-pdf'
    },
    'split-pdf': {
        'title': 'Split PDF - Split PDF Pages Online Free | PDF Splitter Tool',
        'description': 'Split PDF files into separate pages or documents online for free. Extract specific pages from PDF. Fast and easy PDF splitting.',
        'keywords': 'split pdf, split pdf pages, pdf splitter, divide pdf, extract pdf pages, free pdf splitter, online pdf splitter',
        'h1': 'Split PDF - Split PDF Pages Online Free',
        'h2': 'Upload PDF File',
        'slug': 'split-pdf'
    },
    'compress-pdf': {
        'title': 'Compress PDF - Reduce PDF File Size Online Free | PDF Compressor',
        'description': 'Compress PDF files to reduce file size online for free. Maintain quality while reducing size. Fast PDF compression tool.',
        'keywords': 'compress pdf, reduce pdf size, pdf compressor, shrink pdf, optimize pdf, free pdf compressor, online pdf compression',
        'h1': 'Compress PDF - Reduce PDF File Size Online Free',
        'h2': 'Upload PDF File',
        'slug': 'compress-pdf'
    },
    'pdf-to-jpg': {
        'title': 'PDF to JPG Converter - Convert PDF to Images Online Free | Extract Images from PDF',
        'description': 'Convert PDF pages to JPG images online for free. Extract images from PDF documents. High-quality conversion with no watermarks.',
        'keywords': 'pdf to jpg, convert pdf to jpg, pdf to image, extract images from pdf, pdf jpg converter, free pdf to jpg, online pdf to jpg',
        'h1': 'PDF to JPG Converter - Convert PDF to Images Online Free',
        'h2': 'Upload PDF File',
        'slug': 'pdf-to-jpg'
    },
    'edit-pdf': {
        'title': 'Edit PDF Online - PDF Editor Free | Edit PDF Files Online',
        'description': 'Edit PDF files online for free. Add text, images, annotations, and more. No software installation required.',
        'keywords': 'edit pdf, pdf editor, edit pdf online, modify pdf, pdf editing tool, free pdf editor, online pdf editor',
        'h1': 'Edit PDF Online - Free PDF Editor',
        'h2': 'Upload PDF File',
        'slug': 'edit-pdf'
    },
    'protect-pdf': {
        'title': 'Protect PDF - Password Protect PDF Online Free | Secure PDF Files',
        'description': 'Protect PDF files with password online for free. Add encryption and security to your documents. Secure PDF protection tool.',
        'keywords': 'protect pdf, password protect pdf, secure pdf, encrypt pdf, pdf security, free pdf protection, online pdf protection',
        'h1': 'Protect PDF - Password Protect PDF Online Free',
        'h2': 'Upload PDF File',
        'slug': 'protect-pdf'
    },
    'unlock-pdf': {
        'title': 'Unlock PDF - Remove PDF Password Online Free | PDF Password Remover',
        'description': 'Unlock password-protected PDF files online for free. Remove PDF password and restrictions. Fast and secure PDF unlocking.',
        'keywords': 'unlock pdf, remove pdf password, pdf password remover, unlock protected pdf, free pdf unlocker, online pdf unlocker',
        'h1': 'Unlock PDF - Remove PDF Password Online Free',
        'h2': 'Upload PDF File',
        'slug': 'unlock-pdf'
    },
    'watermark-pdf': {
        'title': 'Watermark PDF - Add Watermark to PDF Online Free | PDF Watermark Tool',
        'description': 'Add watermark to PDF files online for free. Text or image watermarks. Protect your documents with custom watermarks.',
        'keywords': 'watermark pdf, add watermark to pdf, pdf watermark, pdf watermarking tool, free pdf watermark, online pdf watermark',
        'h1': 'Watermark PDF - Add Watermark to PDF Online Free',
        'h2': 'Upload PDF File',
        'slug': 'watermark-pdf'
    },
    'crop-pdf': {
        'title': 'Crop PDF - Crop PDF Pages Online Free | PDF Cropping Tool',
        'description': 'Crop PDF pages online for free. Remove unwanted margins and adjust page size. Precise PDF cropping tool.',
        'keywords': 'crop pdf, crop pdf pages, pdf cropping tool, trim pdf, free pdf cropper, online pdf cropping',
        'h1': 'Crop PDF - Crop PDF Pages Online Free',
        'h2': 'Upload PDF File',
        'slug': 'crop-pdf'
    },
    'image-compressor': {
        'title': 'Image Compressor - Compress Images Online Free | Reduce Image File Size',
        'description': 'Compress images online for free. Reduce image file size without losing quality. Support for JPG, PNG, and more formats.',
        'keywords': 'compress image, image compressor, reduce image size, optimize image, image optimization, free image compressor, online image compression',
        'h1': 'Image Compressor - Compress Images Online Free',
        'h2': 'Upload Image',
        'slug': 'image-compressor'
    },
    'image-resizer': {
        'title': 'Image Resizer - Resize Images Online Free | Change Image Size',
        'description': 'Resize images online for free. Change image dimensions and file size. Support for multiple image formats.',
        'keywords': 'resize image, image resizer, change image size, image size converter, free image resizer, online image resizing',
        'h1': 'Image Resizer - Resize Images Online Free',
        'h2': 'Upload Image',
        'slug': 'image-resizer'
    },
    'background-remover': {
        'title': 'Remove Background from Image - Background Remover Online Free | AI Background Removal',
        'description': 'Remove background from images online for free using AI. Automatic background removal tool. High-quality results.',
        'keywords': 'remove background, background remover, remove image background, ai background removal, free background remover, online background removal',
        'h1': 'Remove Background from Image - AI Background Remover Online Free',
        'h2': 'Upload Image',
        'slug': 'background-remover'
    },
    'ocr-image': {
        'title': 'OCR Image - Extract Text from Image Online Free | Image to Text Converter',
        'description': 'Extract text from images online for free using OCR. Convert image to text. Support for multiple languages.',
        'keywords': 'ocr image, extract text from image, image to text, ocr online, free ocr, image text extractor, online ocr tool',
        'h1': 'OCR Image - Extract Text from Image Online Free',
        'h2': 'Upload Image',
        'slug': 'ocr-image'
    }
}

def get_seo_data(filename):
    """Get SEO data for a file based on its name"""
    base_name = filename.replace('.html', '').replace('-convert', '').lower()
    
    # Try exact match first
    if base_name in SEO_DATA:
        return SEO_DATA[base_name]
    
    # Try partial matches
    for key, data in SEO_DATA.items():
        if key in base_name or base_name in key:
            return data
    
    # Generate default SEO data
    tool_name = base_name.replace('-', ' ').title()
    return {
        'title': f'{tool_name} - Online Free Tool | easyjpgtopdf',
        'description': f'Use our free {tool_name} tool online. Fast, secure, and easy to use.',
        'keywords': f'{base_name}, {base_name.replace("-", " ")}, free {base_name}, online {base_name}',
        'h1': f'{tool_name} - Online Free Tool',
        'h2': 'Upload File',
        'slug': base_name
    }

def generate_schema_json(seo_data, filename):
    """Generate schema.org JSON-LD"""
    url = f'https://easyjpgtopdf.com/{filename}'
    return f'''    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": "{seo_data['title']}",
      "description": "{seo_data['description']}",
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

def update_page(file_path):
    """Update a single HTML page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        filename = Path(file_path).name
        
        # Skip index.html
        if filename == 'index.html':
            return False, 'Skipped index.html'
        
        # Get SEO data
        seo_data = get_seo_data(filename)
        
        # Update title
        title_pattern = r'<title>.*?</title>'
        new_title = f'<title>{seo_data["title"]}</title>'
        if re.search(title_pattern, content):
            content = re.sub(title_pattern, new_title, content, flags=re.DOTALL)
        else:
            # Insert after <head>
            content = re.sub(r'(<head>)', r'\1\n' + new_title, content)
        
        # Update meta description
        desc_pattern = r'<meta\s+name=["\']description["\']\s+content=["\'].*?["\']\s*/?>'
        new_desc = f'<meta name="description" content="{seo_data["description"]}">'
        if re.search(desc_pattern, content):
            content = re.sub(desc_pattern, new_desc, content)
        else:
            # Insert after title
            content = re.sub(r'(</title>)', r'\1\n    ' + new_desc, content)
        
        # Update meta keywords
        keywords_pattern = r'<meta\s+name=["\']keywords["\']\s+content=["\'].*?["\']\s*/?>'
        new_keywords = f'<meta name="keywords" content="{seo_data["keywords"]}">'
        if re.search(keywords_pattern, content):
            content = re.sub(keywords_pattern, new_keywords, content)
        else:
            # Insert after description
            content = re.sub(r'(<meta name="description"[^>]*>)', r'\1\n    ' + new_keywords, content)
        
        # Add robots meta if not present
        robots_pattern = r'<meta\s+name=["\']robots["\']'
        if not re.search(robots_pattern, content):
            content = re.sub(r'(<meta name="keywords"[^>]*>)', r'\1\n    <meta name="robots" content="index, follow">', content)
        
        # Add canonical URL
        canonical_pattern = r'<link\s+rel=["\']canonical["\']\s+href=["\'].*?["\']\s*/?>'
        canonical_url = f'https://easyjpgtopdf.com/{filename}'
        new_canonical = f'<link rel="canonical" href="{canonical_url}">'
        if re.search(canonical_pattern, content):
            content = re.sub(canonical_pattern, new_canonical, content)
        else:
            # Insert after robots
            content = re.sub(r'(<meta name="robots"[^>]*>)', r'\1\n    ' + new_canonical, content)
        
        # Update or add schema JSON-LD
        schema_pattern = r'<script\s+type=["\']application/ld\+json["\']>.*?</script>'
        new_schema = generate_schema_json(seo_data, filename)
        if re.search(schema_pattern, content, re.DOTALL):
            content = re.sub(schema_pattern, new_schema, content, flags=re.DOTALL)
        else:
            # Insert before </head>
            content = re.sub(r'(</head>)', new_schema + '\n' + r'\1', content)
        
        # Ensure breadcrumb navigation exists (like jpg-to-pdf.html)
        breadcrumb_pattern = r'<nav\s+aria-label=["\']Breadcrumb["\']'
        if not re.search(breadcrumb_pattern, content):
            # Insert after header placeholder
            breadcrumb = '''    <nav aria-label="Breadcrumb" style="padding: 15px 0; background: #f8f9ff; border-bottom: 1px solid #e2e6ff;">
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
            content = re.sub(r'(<div id="global-header-placeholder"></div>)', r'\1\n\n' + breadcrumb, content)
        
        # Update H1 in hero section
        h1_pattern = r'<h1[^>]*>.*?</h1>'
        new_h1 = f'<h1>{seo_data["h1"]}</h1>'
        # Look for H1 in hero section first
        hero_h1_pattern = r'(<section[^>]*class=["\']hero["\'][^>]*>.*?<h1[^>]*>)(.*?)(</h1>)'
        if re.search(hero_h1_pattern, content, re.DOTALL):
            content = re.sub(hero_h1_pattern, r'\1' + seo_data['h1'] + r'\3', content, flags=re.DOTALL)
        elif re.search(h1_pattern, content):
            content = re.sub(h1_pattern, new_h1, content, count=1)
        
        # Update or add H2 (first H2 in main content)
        h2_pattern = r'<h2[^>]*>.*?</h2>'
        if re.search(h2_pattern, content):
            # Update first H2
            content = re.sub(h2_pattern, f'<h2>{seo_data["h2"]}</h2>', content, count=1)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, 'Updated'
        else:
            return False, 'No changes needed'
            
    except Exception as e:
        return False, f'Error: {str(e)}'

def main():
    """Main function"""
    root_dir = Path('.')
    html_files = list(root_dir.glob('*.html'))
    
    # Exclude certain files
    exclude_files = ['index.html', 'test-', 'backup']
    html_files = [f for f in html_files if not any(ex in str(f) for ex in exclude_files)]
    
    print(f"Found {len(html_files)} HTML files to update\n")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for html_file in sorted(html_files):
        result, message = update_page(html_file)
        if result:
            print(f"[OK] Updated: {html_file.name}")
            updated_count += 1
        elif 'Error' in message:
            print(f"[ERROR] Error: {html_file.name} - {message}")
            error_count += 1
        else:
            skipped_count += 1
    
    print(f"\n{'='*50}")
    print(f"Updated: {updated_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()

