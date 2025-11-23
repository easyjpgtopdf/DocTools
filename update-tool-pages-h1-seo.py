#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update Tool Pages H1 Tags and SEO Meta Tags
Optimized for Google SEO and AdSense compliance
"""

import os
import re
from pathlib import Path

# Tool page H1 and meta tag mappings
TOOL_SEO_DATA = {
    'jpg-to-pdf.html': {
        'h1': 'JPG to PDF Converter - Convert Images to PDF Online Free',
        'title': 'JPG to PDF Converter - Convert Images to PDF Online Free | easyjpgtopdf',
        'description': 'Convert JPG images to PDF documents online for free. Merge multiple images into a single PDF file instantly. No registration required.',
        'keywords': 'jpg to pdf, convert jpg to pdf, image to pdf converter, jpg pdf converter, free jpg to pdf'
    },
    'pdf-to-jpg.html': {
        'h1': 'PDF to JPG Converter - Extract Images from PDF Free Online',
        'title': 'PDF to JPG Converter - Extract Images from PDF Free Online | easyjpgtopdf',
        'description': 'Convert PDF pages to JPG images online for free. Extract images from PDF documents instantly. High-quality conversion with no watermarks.',
        'keywords': 'pdf to jpg, convert pdf to jpg, pdf to image, extract images from pdf, pdf jpg converter'
    },
    'image-compressor.html': {
        'h1': 'Image Compressor - Reduce JPG, PNG File Size Online Free',
        'title': 'Image Compressor - Reduce JPG, PNG File Size Online Free | easyjpgtopdf',
        'description': 'Compress images online for free. Reduce JPG, PNG, and other image file sizes without losing quality. Fast and secure image compression tool.',
        'keywords': 'image compressor, compress image, reduce image size, jpg compressor, png compressor, image optimizer'
    },
    'compress-pdf.html': {
        'h1': 'PDF Compressor - Reduce PDF File Size Online Free',
        'title': 'PDF Compressor - Reduce PDF File Size Online Free | easyjpgtopdf',
        'description': 'Compress PDF files online for free. Reduce PDF file size without losing quality. Fast PDF compression tool with no file size limits.',
        'keywords': 'pdf compressor, compress pdf, reduce pdf size, pdf file compressor, shrink pdf file'
    },
    'merge-pdf.html': {
        'h1': 'PDF Merger - Combine Multiple PDF Files Online Free',
        'title': 'PDF Merger - Combine Multiple PDF Files Online Free | easyjpgtopdf',
        'description': 'Merge multiple PDF files into one document online for free. Combine PDFs in any order. Fast and secure PDF merger tool.',
        'keywords': 'pdf merger, merge pdf, combine pdf files, join pdf, pdf combiner, merge pdf online'
    },
    'split-pdf.html': {
        'h1': 'PDF Splitter - Split PDF Pages Online Free Tool',
        'title': 'PDF Splitter - Split PDF Pages Online Free Tool | easyjpgtopdf',
        'description': 'Split PDF files into multiple documents online for free. Extract specific pages or divide PDF by page ranges. Free PDF splitter tool.',
        'keywords': 'pdf splitter, split pdf, divide pdf, separate pdf pages, pdf page extractor, split pdf online'
    },
    'word-to-pdf.html': {
        'h1': 'Word to PDF Converter - DOC to PDF Online Free',
        'title': 'Word to PDF Converter - DOC to PDF Online Free | easyjpgtopdf',
        'description': 'Convert Word documents (DOC, DOCX) to PDF format online for free. Preserve formatting and layout. Fast and secure conversion.',
        'keywords': 'word to pdf, convert word to pdf, doc to pdf, docx to pdf, word pdf converter, free word to pdf'
    },
    'ppt-to-pdf.html': {
        'h1': 'PPT to PDF Converter - PowerPoint to PDF Online Free',
        'title': 'PPT to PDF Converter - PowerPoint to PDF Online Free | easyjpgtopdf',
        'description': 'Convert PowerPoint presentations (PPT, PPTX) to PDF format online for free. Maintain slide formatting and quality. Free PPT to PDF converter.',
        'keywords': 'ppt to pdf, convert ppt to pdf, powerpoint to pdf, pptx to pdf, presentation to pdf, free ppt to pdf'
    },
    'excel-to-pdf.html': {
        'h1': 'Excel to PDF Converter - XLS to PDF Online Free',
        'title': 'Excel to PDF Converter - XLS to PDF Online Free | easyjpgtopdf',
        'description': 'Convert Excel spreadsheets (XLS, XLSX) to PDF format online for free. Preserve data and formatting. Fast Excel to PDF conversion.',
        'keywords': 'excel to pdf, convert excel to pdf, xls to pdf, xlsx to pdf, spreadsheet to pdf, free excel to pdf'
    },
    'pdf-to-word.html': {
        'h1': 'PDF to Word Converter - Convert PDF to DOC Online Free',
        'title': 'PDF to Word Converter - Convert PDF to DOC Online Free | easyjpgtopdf',
        'description': 'Convert PDF files to editable Word documents online for free. Extract text and maintain formatting. Free PDF to Word converter.',
        'keywords': 'pdf to word, convert pdf to word, pdf to doc, pdf to docx, pdf word converter, free pdf to word'
    },
    'pdf-to-excel.html': {
        'h1': 'PDF to Excel Converter - Convert PDF to XLS Online Free',
        'title': 'PDF to Excel Converter - Convert PDF to XLS Online Free | easyjpgtopdf',
        'description': 'Convert PDF files to Excel spreadsheets online for free. Extract data from PDF to editable Excel format. Free PDF to Excel converter.',
        'keywords': 'pdf to excel, convert pdf to excel, pdf to xls, pdf to xlsx, pdf excel converter, free pdf to excel'
    },
    'pdf-to-ppt.html': {
        'h1': 'PDF to PPT Converter - Convert PDF to PowerPoint Online Free',
        'title': 'PDF to PPT Converter - Convert PDF to PowerPoint Online Free | easyjpgtopdf',
        'description': 'Convert PDF files to PowerPoint presentations online for free. Transform PDF pages into editable PPT slides. Free PDF to PPT converter.',
        'keywords': 'pdf to ppt, convert pdf to ppt, pdf to powerpoint, pdf to pptx, pdf ppt converter, free pdf to ppt'
    },
    'edit-pdf.html': {
        'h1': 'PDF Editor - Edit PDF Documents Online Free',
        'title': 'PDF Editor - Edit PDF Documents Online Free | easyjpgtopdf',
        'description': 'Edit PDF files online for free. Add text, images, annotations, and modify PDF content. No software installation required.',
        'keywords': 'pdf editor, edit pdf, edit pdf online, pdf editing tool, modify pdf, free pdf editor'
    },
    'protect-pdf.html': {
        'h1': 'PDF Password Protector - Secure PDF Files Online Free',
        'title': 'PDF Password Protector - Secure PDF Files Online Free | easyjpgtopdf',
        'description': 'Protect PDF files with password encryption online for free. Secure your documents from unauthorized access. Free PDF protection tool.',
        'keywords': 'protect pdf, password protect pdf, secure pdf, pdf encryption, pdf password, lock pdf'
    },
    'unlock-pdf.html': {
        'h1': 'PDF Unlocker - Remove PDF Password Online Free',
        'title': 'PDF Unlocker - Remove PDF Password Online Free | easyjpgtopdf',
        'description': 'Unlock password-protected PDF files online for free. Remove PDF restrictions and passwords. Free PDF unlocker tool.',
        'keywords': 'unlock pdf, remove pdf password, unlock protected pdf, pdf unlocker, remove pdf restrictions'
    },
    'watermark-pdf.html': {
        'h1': 'PDF Watermark Tool - Add Watermark to PDF Online Free',
        'title': 'PDF Watermark Tool - Add Watermark to PDF Online Free | easyjpgtopdf',
        'description': 'Add watermarks to PDF documents online for free. Protect your files with text or image watermarks. Free PDF watermark tool.',
        'keywords': 'watermark pdf, add watermark to pdf, pdf watermark tool, protect pdf with watermark, pdf watermarker'
    },
    'crop-pdf.html': {
        'h1': 'PDF Cropper - Crop PDF Pages Online Free',
        'title': 'PDF Cropper - Crop PDF Pages Online Free | easyjpgtopdf',
        'description': 'Crop PDF pages online for free. Remove unwanted margins and areas. Resize PDF pages easily. Free PDF cropping tool.',
        'keywords': 'crop pdf, crop pdf pages, resize pdf, trim pdf margins, pdf cropper, edit pdf size'
    },
    'add-page-numbers.html': {
        'h1': 'Add Page Numbers to PDF - Number PDF Pages Online Free',
        'title': 'Add Page Numbers to PDF - Number PDF Pages Online Free | easyjpgtopdf',
        'description': 'Add page numbers to PDF documents online for free. Number your PDF pages automatically. Free PDF page numbering tool.',
        'keywords': 'add page numbers to pdf, number pdf pages, pdf page numbering, pdf pagination, page numbers pdf'
    },
    'image-resizer.html': {
        'h1': 'Image Resizer - Resize Images Online Free',
        'title': 'Image Resizer - Resize Images Online Free | easyjpgtopdf',
        'description': 'Resize images online for free. Change image dimensions while maintaining quality. Free image resizer tool for JPG, PNG, and more.',
        'keywords': 'resize image, change image size, image resizer, resize photo, image size changer, free image resizer'
    },
    'image-editor.html': {
        'h1': 'Image Editor - Edit Photos Online Free',
        'title': 'Image Editor - Edit Photos Online Free | easyjpgtopdf',
        'description': 'Edit images online for free. Crop, rotate, adjust colors, and enhance your photos. Free online image editor tool.',
        'keywords': 'edit image, image editor, photo editor, edit photo online, image editing tool, free image editor'
    },
    'background-remover.html': {
        'h1': 'Background Remover - Remove Image Background Online Free',
        'title': 'Background Remover - Remove Image Background Online Free | easyjpgtopdf',
        'description': 'Remove backgrounds from images online for free. Create transparent PNG images with AI. Free background remover tool.',
        'keywords': 'remove background, transparent background, background remover, remove image background, ai background remover'
    },
    'image-watermark.html': {
        'h1': 'Image Watermark Tool - Add Watermark to Photos Online Free',
        'title': 'Image Watermark Tool - Add Watermark to Photos Online Free | easyjpgtopdf',
        'description': 'Add watermarks to images online for free. Protect your photos with text or logo watermarks. Free image watermark tool.',
        'keywords': 'watermark image, add watermark to photo, image watermark tool, protect images, photo watermark'
    },
    'ocr-image.html': {
        'h1': 'OCR Image to Text - Extract Text from Images Online Free',
        'title': 'OCR Image to Text - Extract Text from Images Online Free | easyjpgtopdf',
        'description': 'Extract text from images using OCR technology online for free. Convert image text to editable format. Free OCR tool.',
        'keywords': 'ocr image, extract text from image, image to text, ocr converter, text recognition, image ocr'
    },
    'resume-maker.html': {
        'h1': 'Resume Maker - Create Professional Resume Online Free',
        'title': 'Resume Maker - Create Professional Resume Online Free | easyjpgtopdf',
        'description': 'Create professional resumes online for free. Build your perfect resume with our easy-to-use resume maker tool. Free resume builder.',
        'keywords': 'resume maker, create resume, resume builder, make resume online, professional resume, free resume maker'
    },
    'biodata-maker.html': {
        'h1': 'Biodata Maker - Create Marriage Biodata Online Free',
        'title': 'Biodata Maker - Create Marriage Biodata Online Free | easyjpgtopdf',
        'description': 'Create professional biodata for marriage online for free. Design beautiful marriage biodata with our free biodata maker tool.',
        'keywords': 'biodata maker, create biodata, marriage biodata, biodata creator, make biodata online, free biodata maker'
    },
    'marriage-card.html': {
        'h1': 'Marriage Card Maker - Create Wedding Invitation Online Free',
        'title': 'Marriage Card Maker - Create Wedding Invitation Online Free | easyjpgtopdf',
        'description': 'Create beautiful marriage invitation cards online for free. Design wedding cards with our free marriage card maker tool.',
        'keywords': 'marriage card, wedding card, marriage invitation, wedding invitation maker, create marriage card, free marriage card'
    },
    'ai-image-generator.html': {
        'h1': 'AI Image Generator - Generate Images from Text Online Free',
        'title': 'AI Image Generator - Generate Images from Text Online Free | easyjpgtopdf',
        'description': 'Generate AI images from text prompts online for free. Create unique images using artificial intelligence. Free AI image generator.',
        'keywords': 'ai image generator, generate ai image, text to image ai, ai art generator, create ai art, free ai image generator'
    },
    'protect-excel.html': {
        'h1': 'Excel Password Protector - Secure Excel Files Online Free',
        'title': 'Excel Password Protector - Secure Excel Files Online Free | easyjpgtopdf',
        'description': 'Protect Excel files with password encryption online for free. Secure your spreadsheets from unauthorized access. Free Excel protection tool.',
        'keywords': 'protect excel, password protect excel, secure excel, excel encryption, excel password, lock excel'
    }
}

def update_h1_tag(content, new_h1):
    """Update or add H1 tag"""
    # Try to find existing H1
    h1_pattern = r'<h1[^>]*>(.*?)</h1>'
    h1_matches = list(re.finditer(h1_pattern, content, re.DOTALL | re.IGNORECASE))
    
    if h1_matches:
        # Replace first H1
        first_h1 = h1_matches[0]
        new_h1_tag = f'<h1>{new_h1}</h1>'
        content = content[:first_h1.start()] + new_h1_tag + content[first_h1.end():]
    else:
        # Add H1 if not found - try to add after opening main or after hero section
        if '<main' in content:
            content = re.sub(
                r'(<main[^>]*>)',
                rf'\1\n        <h1>{new_h1}</h1>',
                content,
                count=1
            )
        elif '.hero' in content or 'class="hero"' in content:
            content = re.sub(
                r'(</div>\s*<!--.*?hero.*?-->)',
                rf'\1\n        <h1>{new_h1}</h1>',
                content,
                count=1,
                flags=re.IGNORECASE
            )
        elif '<body' in content:
            # Add after body tag
            content = re.sub(
                r'(<body[^>]*>)',
                rf'\1\n        <h1>{new_h1}</h1>',
                content,
                count=1
            )
    
    return content

def update_meta_tags(content, seo_data):
    """Update meta title and description"""
    # Update title tag
    title_pattern = r'<title>.*?</title>'
    new_title = f'<title>{seo_data["title"]}</title>'
    if re.search(title_pattern, content):
        content = re.sub(title_pattern, new_title, content, flags=re.DOTALL)
    else:
        # Add title if not found
        content = re.sub(r'(<head[^>]*>)', rf'\1\n    {new_title}', content)
    
    # Update or add description meta tag
    desc_pattern = r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>'
    new_desc = f'<meta name="description" content="{seo_data["description"]}">'
    if re.search(desc_pattern, content):
        content = re.sub(desc_pattern, new_desc, content)
    else:
        # Add after title
        content = re.sub(r'(<title>.*?</title>)', rf'\1\n    {new_desc}', content, flags=re.DOTALL)
    
    # Update or add keywords meta tag
    keywords_pattern = r'<meta\s+name=["\']keywords["\']\s+content=["\'][^"\']*["\']\s*/?>'
    new_keywords = f'<meta name="keywords" content="{seo_data["keywords"]}">'
    if re.search(keywords_pattern, content):
        content = re.sub(keywords_pattern, new_keywords, content)
    else:
        # Add after description
        content = re.sub(r'(<meta name="description".*?>)', rf'\1\n    {new_keywords}', content)
    
    return content

def process_tool_file(filepath):
    """Process a single tool file"""
    filename = os.path.basename(filepath)
    
    if filename not in TOOL_SEO_DATA:
        print(f'⚠ Skipping {filename} (not in SEO data mapping)')
        return False
    
    print(f'Processing: {filename}')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        seo_data = TOOL_SEO_DATA[filename]
        
        # Update H1 tag
        content = update_h1_tag(content, seo_data['h1'])
        
        # Update meta tags
        content = update_meta_tags(content, seo_data)
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'✓ Updated H1: {seo_data["h1"]}')
        print(f'✓ Updated title and meta tags')
        return True
        
    except Exception as e:
        print(f'✗ Error processing {filepath}: {str(e)}')
        return False

def main():
    """Main function"""
    print('=' * 70)
    print('Tool Pages H1 & SEO Meta Tags Update Script')
    print('=' * 70)
    print()
    
    # Find all tool files
    tool_files = []
    for filename in TOOL_SEO_DATA.keys():
        filepath = Path('.') / filename
        if filepath.exists():
            tool_files.append(str(filepath))
        else:
            print(f'⚠ File not found: {filename}')
    
    print(f'Found {len(tool_files)} tool files to update')
    print()
    
    # Process each file
    success_count = 0
    for tool_file in tool_files:
        if process_tool_file(tool_file):
            success_count += 1
        print()
    
    print('=' * 70)
    print(f'Processing complete: {success_count}/{len(tool_files)} files updated')
    print('=' * 70)
    print()
    print('All H1 tags and meta tags have been updated for Google SEO optimization.')
    print('Changes are AdSense compliant and optimized for global user search.')

if __name__ == '__main__':
    main()

