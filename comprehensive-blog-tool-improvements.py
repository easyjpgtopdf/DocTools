#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Blog and Tool Pages Improvement Script
Fixes all AdSense requirements and optimizations
"""

import os
import re
import json
from pathlib import Path

# Blog page mappings with unique content
BLOG_META = {
    'blog-how-to-use-jpg-to-pdf.html': {
        'title': 'How to Convert JPG to PDF - Step by Step Guide | easyjpgtopdf',
        'description': 'Learn how to convert JPG images to PDF documents quickly and efficiently. Complete step-by-step guide with tips and best practices.',
        'keywords': 'jpg to pdf, convert jpg to pdf, image to pdf converter, jpg pdf converter',
        'related_blogs': ['blog-how-to-use-word-to-pdf.html', 'blog-how-to-compress-pdf.html', 'blog-how-to-merge-pdf.html'],
        'related_tools': ['jpg-to-pdf.html', 'word-to-pdf.html', 'compress-pdf.html']
    },
    'blog-how-to-use-word-to-pdf.html': {
        'title': 'How to Convert Word to PDF - Complete Tutorial | easyjpgtopdf',
        'description': 'Step-by-step guide to convert Word documents to PDF format. Learn the best methods and tips for perfect conversions.',
        'keywords': 'word to pdf, convert word to pdf, docx to pdf, word pdf converter',
        'related_blogs': ['blog-how-to-use-jpg-to-pdf.html', 'blog-how-to-edit-pdf.html', 'blog-how-to-protect-pdf.html'],
        'related_tools': ['word-to-pdf.html', 'pdf-to-word.html', 'edit-pdf.html']
    },
    'blog-how-to-use-ppt-to-pdf.html': {
        'title': 'How to Convert PowerPoint to PDF - Easy Guide | easyjpgtopdf',
        'description': 'Complete guide to convert PowerPoint presentations to PDF. Learn how to maintain formatting and quality.',
        'keywords': 'ppt to pdf, powerpoint to pdf, convert ppt to pdf, presentation to pdf',
        'related_blogs': ['blog-how-to-use-word-to-pdf.html', 'blog-how-to-compress-pdf.html', 'blog-how-to-merge-pdf.html'],
        'related_tools': ['ppt-to-pdf.html', 'pdf-to-ppt.html', 'compress-pdf.html']
    },
    'blog-how-to-use-excel-to-pdf.html': {
        'title': 'How to Convert Excel to PDF - Complete Tutorial | easyjpgtopdf',
        'description': 'Learn how to convert Excel spreadsheets to PDF format while preserving formatting and data integrity.',
        'keywords': 'excel to pdf, convert excel to pdf, xlsx to pdf, spreadsheet to pdf',
        'related_blogs': ['blog-how-to-use-word-to-pdf.html', 'blog-how-to-protect-excel.html', 'blog-why-user-pdf-to-excel.html'],
        'related_tools': ['excel-to-pdf.html', 'pdf-to-excel.html', 'protect-excel.html']
    },
    'blog-why-user-pdf-to-word.html': {
        'title': 'Why Convert PDF to Word - Benefits and Methods | easyjpgtopdf',
        'description': 'Discover why converting PDF to Word is essential for editing documents. Learn the benefits and best conversion methods.',
        'keywords': 'pdf to word, convert pdf to word, pdf docx converter, edit pdf in word',
        'related_blogs': ['blog-why-user-pdf-to-excel.html', 'blog-how-to-edit-pdf.html', 'blog-how-to-unlock-pdf.html'],
        'related_tools': ['pdf-to-word.html', 'word-to-pdf.html', 'edit-pdf.html']
    },
    'blog-why-user-pdf-to-excel.html': {
        'title': 'Why Convert PDF to Excel - Complete Guide | easyjpgtopdf',
        'description': 'Learn why converting PDF to Excel is important for data analysis. Discover the benefits and conversion methods.',
        'keywords': 'pdf to excel, convert pdf to excel, pdf xlsx converter, extract data from pdf',
        'related_blogs': ['blog-why-user-pdf-to-word.html', 'blog-how-to-use-excel-to-pdf.html', 'blog-how-to-protect-excel.html'],
        'related_tools': ['pdf-to-excel.html', 'excel-to-pdf.html', 'protect-excel.html']
    },
    'blog-why-user-pdf-to-ppt.html': {
        'title': 'Why Convert PDF to PowerPoint - Benefits Guide | easyjpgtopdf',
        'description': 'Discover the benefits of converting PDF to PowerPoint. Learn how to edit and modify PDF presentations easily.',
        'keywords': 'pdf to ppt, convert pdf to powerpoint, pdf pptx converter, edit pdf presentation',
        'related_blogs': ['blog-why-user-pdf-to-word.html', 'blog-how-to-use-ppt-to-pdf.html', 'blog-how-to-edit-pdf.html'],
        'related_tools': ['pdf-to-ppt.html', 'ppt-to-pdf.html', 'edit-pdf.html']
    },
    'blog-why-user-pdf-to-jpg.html': {
        'title': 'Why Convert PDF to JPG - Image Extraction Guide | easyjpgtopdf',
        'description': 'Learn why and how to convert PDF pages to JPG images. Extract images from PDF documents easily.',
        'keywords': 'pdf to jpg, convert pdf to image, pdf to jpeg, extract images from pdf',
        'related_blogs': ['blog-how-to-use-jpg-to-pdf.html', 'blog-how-to-compress-image.html', 'blog-how-to-resize-image.html'],
        'related_tools': ['pdf-to-jpg.html', 'jpg-to-pdf.html', 'image-compressor.html']
    },
    'blog-how-to-merge-pdf.html': {
        'title': 'How to Merge PDF Files - Complete Guide | easyjpgtopdf',
        'description': 'Step-by-step guide to merge multiple PDF files into one document. Learn the best methods and tips.',
        'keywords': 'merge pdf, combine pdf files, pdf merger, join pdf documents',
        'related_blogs': ['blog-how-to-split-pdf.html', 'blog-how-to-compress-pdf.html', 'blog-how-to-edit-pdf.html'],
        'related_tools': ['merge-pdf.html', 'split-pdf.html', 'compress-pdf.html']
    },
    'blog-how-to-split-pdf.html': {
        'title': 'How to Split PDF Files - Easy Guide | easyjpgtopdf',
        'description': 'Learn how to split PDF files into multiple documents. Complete guide with step-by-step instructions.',
        'keywords': 'split pdf, divide pdf, separate pdf pages, pdf splitter',
        'related_blogs': ['blog-how-to-merge-pdf.html', 'blog-how-to-crop-pdf.html', 'blog-how-to-edit-pdf.html'],
        'related_tools': ['split-pdf.html', 'merge-pdf.html', 'crop-pdf.html']
    },
    'blog-how-to-compress-pdf.html': {
        'title': 'How to Compress PDF Files - Size Reduction Guide | easyjpgtopdf',
        'description': 'Learn how to compress PDF files to reduce file size without losing quality. Complete compression guide.',
        'keywords': 'compress pdf, reduce pdf size, pdf compressor, shrink pdf file',
        'related_blogs': ['blog-how-to-compress-image.html', 'blog-how-to-merge-pdf.html', 'blog-how-to-edit-pdf.html'],
        'related_tools': ['compress-pdf.html', 'image-compressor.html', 'merge-pdf.html']
    },
    'blog-how-to-edit-pdf.html': {
        'title': 'How to Edit PDF Files - Complete Editing Guide | easyjpgtopdf',
        'description': 'Learn how to edit PDF documents easily. Add text, images, annotations, and modify PDF content.',
        'keywords': 'edit pdf, pdf editor, modify pdf, pdf editing tool',
        'related_blogs': ['blog-how-to-watermark-pdf.html', 'blog-how-to-protect-pdf.html', 'blog-how-to-add-page-numbers.html'],
        'related_tools': ['edit-pdf.html', 'watermark-pdf.html', 'protect-pdf.html']
    },
    'blog-how-to-protect-pdf.html': {
        'title': 'How to Protect PDF Files - Security Guide | easyjpgtopdf',
        'description': 'Learn how to protect PDF files with passwords and encryption. Secure your documents from unauthorized access.',
        'keywords': 'protect pdf, password protect pdf, secure pdf, pdf encryption',
        'related_blogs': ['blog-how-to-unlock-pdf.html', 'blog-how-to-edit-pdf.html', 'blog-how-to-watermark-pdf.html'],
        'related_tools': ['protect-pdf.html', 'unlock-pdf.html', 'edit-pdf.html']
    },
    'blog-how-to-unlock-pdf.html': {
        'title': 'How to Unlock PDF Files - Remove Password Guide | easyjpgtopdf',
        'description': 'Learn how to unlock password-protected PDF files. Remove PDF restrictions and passwords easily.',
        'keywords': 'unlock pdf, remove pdf password, unlock protected pdf, pdf unlocker',
        'related_blogs': ['blog-how-to-protect-pdf.html', 'blog-how-to-edit-pdf.html', 'blog-how-to-merge-pdf.html'],
        'related_tools': ['unlock-pdf.html', 'protect-pdf.html', 'edit-pdf.html']
    },
    'blog-how-to-watermark-pdf.html': {
        'title': 'How to Add Watermark to PDF - Complete Guide | easyjpgtopdf',
        'description': 'Learn how to add watermarks to PDF documents. Protect your files with text or image watermarks.',
        'keywords': 'watermark pdf, add watermark to pdf, pdf watermark tool, protect pdf with watermark',
        'related_blogs': ['blog-how-to-watermark-image.html', 'blog-how-to-protect-pdf.html', 'blog-how-to-edit-pdf.html'],
        'related_tools': ['watermark-pdf.html', 'image-watermark.html', 'protect-pdf.html']
    },
    'blog-how-to-crop-pdf.html': {
        'title': 'How to Crop PDF Pages - Complete Guide | easyjpgtopdf',
        'description': 'Learn how to crop PDF pages to remove unwanted margins and areas. Resize PDF pages easily.',
        'keywords': 'crop pdf, crop pdf pages, resize pdf, trim pdf margins',
        'related_blogs': ['blog-how-to-edit-pdf.html', 'blog-how-to-split-pdf.html', 'blog-how-to-resize-image.html'],
        'related_tools': ['crop-pdf.html', 'edit-pdf.html', 'split-pdf.html']
    },
    'blog-how-to-add-page-numbers.html': {
        'title': 'How to Add Page Numbers to PDF - Step by Step | easyjpgtopdf',
        'description': 'Learn how to add page numbers to PDF documents. Number your PDF pages automatically.',
        'keywords': 'add page numbers to pdf, number pdf pages, pdf page numbering, pdf pagination',
        'related_blogs': ['blog-how-to-edit-pdf.html', 'blog-how-to-watermark-pdf.html', 'blog-how-to-merge-pdf.html'],
        'related_tools': ['add-page-numbers.html', 'edit-pdf.html', 'watermark-pdf.html']
    },
    'blog-how-to-compress-image.html': {
        'title': 'How to Compress Images - Size Reduction Guide | easyjpgtopdf',
        'description': 'Learn how to compress images to reduce file size without losing quality. Complete image compression guide.',
        'keywords': 'compress image, reduce image size, image compressor, shrink image file',
        'related_blogs': ['blog-how-to-resize-image.html', 'blog-how-to-compress-pdf.html', 'blog-how-to-edit-image.html'],
        'related_tools': ['image-compressor.html', 'image-resizer.html', 'compress-pdf.html']
    },
    'blog-how-to-resize-image.html': {
        'title': 'How to Resize Images - Complete Guide | easyjpgtopdf',
        'description': 'Learn how to resize images to different dimensions. Change image size while maintaining quality.',
        'keywords': 'resize image, change image size, image resizer, resize photo',
        'related_blogs': ['blog-how-to-compress-image.html', 'blog-how-to-crop-pdf.html', 'blog-how-to-edit-image.html'],
        'related_tools': ['image-resizer.html', 'image-compressor.html', 'crop-pdf.html']
    },
    'blog-how-to-edit-image.html': {
        'title': 'How to Edit Images - Complete Editing Guide | easyjpgtopdf',
        'description': 'Learn how to edit images online. Crop, rotate, adjust colors, and enhance your photos easily.',
        'keywords': 'edit image, image editor, photo editor, edit photo online',
        'related_blogs': ['blog-how-to-resize-image.html', 'blog-how-to-watermark-image.html', 'blog-how-to-remove-background.html'],
        'related_tools': ['image-editor.html', 'image-resizer.html', 'background-remover.html']
    },
    'blog-how-to-watermark-image.html': {
        'title': 'How to Add Watermark to Images - Complete Guide | easyjpgtopdf',
        'description': 'Learn how to add watermarks to images to protect your photos. Add text or logo watermarks easily.',
        'keywords': 'watermark image, add watermark to photo, image watermark tool, protect images',
        'related_blogs': ['blog-how-to-watermark-pdf.html', 'blog-how-to-edit-image.html', 'blog-how-to-resize-image.html'],
        'related_tools': ['image-watermark.html', 'watermark-pdf.html', 'image-editor.html']
    },
    'blog-how-to-remove-background.html': {
        'title': 'How to Remove Image Background - Complete Guide | easyjpgtopdf',
        'description': 'Learn how to remove backgrounds from images automatically. Create transparent backgrounds easily.',
        'keywords': 'remove background, transparent background, background remover, remove image background',
        'related_blogs': ['blog-how-to-edit-image.html', 'blog-how-to-resize-image.html', 'blog-how-to-compress-image.html'],
        'related_tools': ['background-remover.html', 'image-editor.html', 'image-resizer.html']
    },
    'blog-how-to-ocr-image.html': {
        'title': 'How to Extract Text from Images - OCR Guide | easyjpgtopdf',
        'description': 'Learn how to extract text from images using OCR technology. Convert image text to editable format.',
        'keywords': 'ocr image, extract text from image, image to text, ocr converter',
        'related_blogs': ['blog-why-user-pdf-to-word.html', 'blog-how-to-edit-pdf.html', 'blog-how-to-edit-image.html'],
        'related_tools': ['ocr-image.html', 'pdf-to-word.html', 'edit-pdf.html']
    },
    'blog-how-to-make-resume.html': {
        'title': 'How to Make a Resume - Complete Guide | easyjpgtopdf',
        'description': 'Learn how to create a professional resume online. Step-by-step guide to make the perfect resume.',
        'keywords': 'make resume, create resume, resume builder, resume maker online',
        'related_blogs': ['blog-how-to-make-biodata.html', 'blog-how-to-make-marriage-card.html', 'blog-how-to-edit-pdf.html'],
        'related_tools': ['resume-maker.html', 'biodata-maker.html', 'marriage-card.html']
    },
    'blog-how-to-make-biodata.html': {
        'title': 'How to Make Biodata - Complete Guide | easyjpgtopdf',
        'description': 'Learn how to create a professional biodata for marriage. Step-by-step guide to make perfect biodata.',
        'keywords': 'make biodata, create biodata, biodata maker, marriage biodata',
        'related_blogs': ['blog-how-to-make-resume.html', 'blog-how-to-make-marriage-card.html', 'blog-how-to-edit-pdf.html'],
        'related_tools': ['biodata-maker.html', 'resume-maker.html', 'marriage-card.html']
    },
    'blog-how-to-make-marriage-card.html': {
        'title': 'How to Make Marriage Card - Complete Guide | easyjpgtopdf',
        'description': 'Learn how to create beautiful marriage invitation cards online. Design wedding cards easily.',
        'keywords': 'make marriage card, create wedding card, marriage invitation, wedding card maker',
        'related_blogs': ['blog-how-to-make-biodata.html', 'blog-how-to-make-resume.html', 'blog-how-to-edit-image.html'],
        'related_tools': ['marriage-card.html', 'biodata-maker.html', 'image-editor.html']
    },
    'blog-how-to-generate-ai-image.html': {
        'title': 'How to Generate AI Images - Complete Guide | easyjpgtopdf',
        'description': 'Learn how to generate AI images using artificial intelligence. Create unique images from text prompts.',
        'keywords': 'generate ai image, ai image generator, create ai art, text to image ai',
        'related_blogs': ['blog-how-to-edit-image.html', 'blog-how-to-remove-background.html', 'blog-how-to-resize-image.html'],
        'related_tools': ['ai-image-generator.html', 'image-editor.html', 'background-remover.html']
    },
    'blog-how-to-protect-excel.html': {
        'title': 'How to Protect Excel Files - Security Guide | easyjpgtopdf',
        'description': 'Learn how to protect Excel files with passwords and encryption. Secure your spreadsheets from unauthorized access.',
        'keywords': 'protect excel, password protect excel, secure excel, excel encryption',
        'related_blogs': ['blog-how-to-protect-pdf.html', 'blog-how-to-use-excel-to-pdf.html', 'blog-why-user-pdf-to-excel.html'],
        'related_tools': ['protect-excel.html', 'protect-pdf.html', 'excel-to-pdf.html']
    }
}

# Common FAQ templates
FAQ_TEMPLATES = {
    'convert': [
        {
            'q': 'How long does the conversion process take?',
            'a': 'The conversion process is typically completed within seconds. The exact time depends on the file size and complexity of your document.'
        },
        {
            'q': 'Is my data secure during conversion?',
            'a': 'Yes, absolutely. All files are processed securely in the cloud and automatically deleted after conversion. We never store or share your documents.'
        },
        {
            'q': 'What file formats are supported?',
            'a': 'We support all major file formats including JPG, PNG, PDF, Word, Excel, PowerPoint, and more. Check our tool page for the complete list.'
        },
        {
            'q': 'Can I convert multiple files at once?',
            'a': 'Yes, our premium plans support batch conversion, allowing you to process multiple files simultaneously for increased productivity.'
        },
        {
            'q': 'Do I need to install any software?',
            'a': 'No installation required! All our tools work directly in your web browser. Just upload your file and convert instantly.'
        }
    ],
    'edit': [
        {
            'q': 'Can I edit PDF files without Adobe?',
            'a': 'Yes! Our online PDF editor allows you to edit PDFs directly in your browser without any software installation.'
        },
        {
            'q': 'What editing features are available?',
            'a': 'You can add text, images, annotations, highlight text, draw shapes, and more. All editing is done online with instant preview.'
        },
        {
            'q': 'Will my formatting be preserved?',
            'a': 'Yes, our editor maintains all original formatting, fonts, and layout while allowing you to make necessary changes.'
        },
        {
            'q': 'Can I undo changes?',
            'a': 'Yes, our editor includes undo/redo functionality, allowing you to revert changes if needed.'
        }
    ],
    'image': [
        {
            'q': 'What image formats are supported?',
            'a': 'We support all major image formats including JPG, PNG, GIF, BMP, and WebP. Upload any image format and we\'ll process it.'
        },
        {
            'q': 'What is the maximum file size?',
            'a': 'Free users can upload files up to 10MB. Premium users can upload files up to 100MB for faster processing.'
        },
        {
            'q': 'Will image quality be affected?',
            'a': 'Our tools are designed to maintain high quality. For compression, you can choose the quality level to balance size and quality.'
        },
        {
            'q': 'Can I process multiple images at once?',
            'a': 'Yes, premium users can process multiple images simultaneously. Free users can process one image at a time.'
        }
    ]
}

def get_faq_type(filename):
    """Determine FAQ type based on filename"""
    if 'convert' in filename or 'to' in filename or 'pdf-to' in filename:
        return 'convert'
    elif 'edit' in filename or 'watermark' in filename or 'protect' in filename:
        return 'edit'
    elif 'image' in filename or 'jpg' in filename or 'png' in filename or 'resize' in filename or 'compress' in filename or 'background' in filename:
        return 'image'
    else:
        return 'convert'

def add_meta_tags(content, meta_info):
    """Add or update meta tags in HTML"""
    # Update title
    title_pattern = r'<title>.*?</title>'
    new_title = f'<title>{meta_info["title"]}</title>'
    content = re.sub(title_pattern, new_title, content, flags=re.DOTALL)
    
    # Update or add description
    desc_pattern = r'<meta\s+name=["\']description["\']\s+content=["\'].*?["\']\s*/?>'
    new_desc = f'<meta name="description" content="{meta_info["description"]}">'
    if re.search(desc_pattern, content):
        content = re.sub(desc_pattern, new_desc, content)
    else:
        # Add after title
        content = re.sub(r'(<title>.*?</title>)', rf'\1\n    {new_desc}', content, flags=re.DOTALL)
    
    # Add keywords meta tag
    keywords_tag = f'<meta name="keywords" content="{meta_info["keywords"]}">'
    if 'name="keywords"' not in content:
        content = re.sub(r'(<meta name="description".*?>)', rf'\1\n    {keywords_tag}', content)
    
    # Add Open Graph tags
    og_tags = f'''    <meta property="og:title" content="{meta_info["title"]}">
    <meta property="og:description" content="{meta_info["description"]}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://easyjpgtopdf.com/{os.path.basename(meta_info.get("filename", ""))}">'''
    
    if 'property="og:title"' not in content:
        content = re.sub(r'(<meta name="keywords".*?>)', rf'\1\n{og_tags}', content)
    
    # Add Twitter Card tags
    twitter_tags = f'''    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{meta_info["title"]}">
    <meta name="twitter:description" content="{meta_info["description"]}">'''
    
    if 'name="twitter:card"' not in content:
        content = re.sub(r'(<meta property="og:url".*?>)', rf'\1\n{twitter_tags}', content)
    
    return content

def fix_heading_structure(content):
    """Fix heading hierarchy (H1, H2, H3)"""
    # Ensure only one H1
    h1_count = len(re.findall(r'<h1[^>]*>', content))
    if h1_count > 1:
        # Keep first H1, convert others to H2
        h1_matches = list(re.finditer(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL))
        for i, match in enumerate(h1_matches[1:], 1):
            content = content.replace(match.group(0), f'<h2>{match.group(1)}</h2>')
    
    # Ensure proper hierarchy - H2 after H1, H3 after H2
    # This is a basic check - more complex logic can be added
    
    return content

def add_internal_links(content, related_blogs, related_tools):
    """Add internal linking section"""
    if not related_blogs and not related_tools:
        return content
    
    links_section = '''
    <section class="related-content" style="margin-top: 40px; padding: 30px; background: #f8f9ff; border-radius: 16px;">
        <h2 style="font-size: 1.8rem; color: #4361ee; margin-bottom: 20px;">Related Content</h2>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
'''
    
    if related_blogs:
        links_section += '            <div class="related-blogs">\n'
        links_section += '                <h3 style="font-size: 1.3rem; color: #0b1630; margin-bottom: 15px;">Related Articles</h3>\n'
        links_section += '                <ul style="list-style: none; padding: 0;">\n'
        for blog in related_blogs[:5]:  # Limit to 5
            blog_title = blog.replace('blog-', '').replace('.html', '').replace('-', ' ').title()
            links_section += f'                    <li style="margin-bottom: 10px;"><a href="{blog}" style="color: #4361ee; text-decoration: none; font-weight: 500;">{blog_title}</a></li>\n'
        links_section += '                </ul>\n'
        links_section += '            </div>\n'
    
    if related_tools:
        links_section += '            <div class="related-tools">\n'
        links_section += '                <h3 style="font-size: 1.3rem; color: #0b1630; margin-bottom: 15px;">Related Tools</h3>\n'
        links_section += '                <ul style="list-style: none; padding: 0;">\n'
        for tool in related_tools[:5]:  # Limit to 5
            tool_title = tool.replace('.html', '').replace('-', ' ').title()
            links_section += f'                    <li style="margin-bottom: 10px;"><a href="{tool}" style="color: #4361ee; text-decoration: none; font-weight: 500;">{tool_title}</a></li>\n'
        links_section += '                </ul>\n'
        links_section += '            </div>\n'
    
    links_section += '        </div>\n'
    links_section += '    </section>\n'
    
    # Add before closing main or before footer
    if '</main>' in content:
        content = content.replace('</main>', links_section + '</main>')
    elif '<footer' in content:
        content = re.sub(r'(<footer)', links_section + r'\1', content)
    else:
        # Add at end of body content
        content = re.sub(r'(</body>)', links_section + r'\1', content)
    
    return content

def add_faq_section(content, faq_type):
    """Add FAQ section"""
    faqs = FAQ_TEMPLATES.get(faq_type, FAQ_TEMPLATES['convert'])
    
    faq_section = '''
    <section class="faq-section" style="margin-top: 50px; padding: 40px; background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="font-size: 2rem; color: #4361ee; margin-bottom: 30px; text-align: center;">Frequently Asked Questions</h2>
        <div class="faq-container" style="max-width: 800px; margin: 0 auto;">
'''
    
    for i, faq in enumerate(faqs, 1):
        faq_section += f'''
            <div class="faq-item" style="margin-bottom: 20px; padding: 20px; background: #f8f9ff; border-radius: 12px; border-left: 4px solid #4361ee;">
                <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px; cursor: pointer;" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
                    <i class="fas fa-question-circle" style="color: #4361ee; margin-right: 8px;"></i>
                    {faq['q']}
                </h3>
                <p style="font-size: 1rem; color: #56607a; line-height: 1.6; margin-top: 10px; display: block;">
                    {faq['a']}
                </p>
            </div>
'''
    
    faq_section += '        </div>\n'
    faq_section += '    </section>\n'
    
    # Add before related content or before footer
    if 'class="related-content"' in content:
        content = content.replace('class="related-content"', faq_section + '\n    <section class="related-content"')
    elif '</main>' in content:
        content = content.replace('</main>', faq_section + '</main>')
    elif '<footer' in content:
        content = re.sub(r'(<footer)', faq_section + r'\1', content)
    else:
        content = re.sub(r'(</body>)', faq_section + r'\1', content)
    
    return content

def add_lazy_loading(content):
    """Add lazy loading to images"""
    # Add loading="lazy" to all img tags
    content = re.sub(
        r'<img([^>]*?)(src=["\']([^"\']+)["\'])([^>]*?)>',
        r'<img\1\2 loading="lazy"\4>',
        content
    )
    
    # Add lazy loading script
    lazy_script = '''
    <script>
    // Lazy loading enhancement
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(img => {
            img.src = img.dataset.src || img.src;
        });
    } else {
        // Fallback for older browsers
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
        document.body.appendChild(script);
    }
    </script>
'''
    
    if '</body>' in content and 'lazysizes' not in content:
        content = re.sub(r'(</body>)', lazy_script + r'\1', content)
    
    return content

def add_caching_headers(content):
    """Add caching meta tags and optimize loading"""
    cache_meta = '''
    <meta http-equiv="Cache-Control" content="public, max-age=31536000">
    <meta http-equiv="Expires" content="31536000">
'''
    
    if 'Cache-Control' not in content:
        content = re.sub(r'(<meta name="viewport".*?>)', rf'\1\n{cache_meta}', content)
    
    # Add preconnect for external resources
    preconnect = '''
    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <link rel="dns-prefetch" href="https://cdnjs.cloudflare.com">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="dns-prefetch" href="https://fonts.googleapis.com">
'''
    
    if 'preconnect' not in content:
        content = re.sub(r'(<link rel="stylesheet".*?>)', preconnect + r'\1', content, count=1)
    
    return content

def fix_jquery_conflicts(content):
    """Fix jQuery conflicts"""
    # Ensure jQuery is loaded before other scripts
    # Add noConflict if needed
    jquery_fix = '''
    <script>
    // Fix jQuery conflicts
    if (typeof jQuery !== 'undefined') {
        jQuery.noConflict();
        var $j = jQuery;
    }
    </script>
'''
    
    if 'jquery' in content.lower() and 'noConflict' not in content:
        # Add after jQuery script
        content = re.sub(
            r'(<script[^>]*jquery[^>]*></script>)',
            rf'\1\n{jquery_fix}',
            content,
            flags=re.IGNORECASE
        )
    
    return content

def add_cta_section(content):
    """Add Call-to-Action section"""
    cta = '''
    <section class="cta-section" style="margin: 40px 0; padding: 40px; background: linear-gradient(135deg, #4361ee, #3a0ca3); border-radius: 16px; text-align: center; color: white;">
        <h2 style="font-size: 2rem; margin-bottom: 20px; color: white;">Ready to Get Started?</h2>
        <p style="font-size: 1.2rem; margin-bottom: 30px; opacity: 0.9;">Try our tools for free and experience the difference</p>
        <a href="index.html" style="display: inline-block; background: white; color: #4361ee; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 1.1rem; transition: transform 0.3s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
            <i class="fas fa-rocket" style="margin-right: 8px;"></i>Explore All Tools
        </a>
    </section>
'''
    
    # Add before FAQ section
    if 'class="faq-section"' in content:
        content = content.replace('class="faq-section"', cta + '\n    <section class="faq-section"')
    elif '</main>' in content:
        content = content.replace('</main>', cta + '</main>')
    else:
        content = re.sub(r'(</body>)', cta + r'\1', content)
    
    return content

def add_excerpt(content, description):
    """Add excerpt/description section"""
    excerpt = f'''
    <div class="blog-excerpt" style="padding: 20px; background: #f8f9ff; border-left: 4px solid #4361ee; border-radius: 8px; margin: 20px 0;">
        <p style="font-size: 1.1rem; color: #56607a; line-height: 1.8; margin: 0; font-style: italic;">
            {description}
        </p>
    </div>
'''
    
    # Add after first H1
    h1_pattern = r'(<h1[^>]*>.*?</h1>)'
    if re.search(h1_pattern, content):
        content = re.sub(h1_pattern, rf'\1{excerpt}', content, count=1)
    
    return content

def process_blog_file(filepath):
    """Process a single blog file"""
    print(f'Processing: {filepath}')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        filename = os.path.basename(filepath)
        
        # Get meta info
        meta_info = BLOG_META.get(filename, {
            'title': filename.replace('.html', '').replace('-', ' ').title(),
            'description': f'Learn about {filename.replace(".html", "").replace("-", " ")}',
            'keywords': filename.replace('.html', '').replace('-', ', '),
            'related_blogs': [],
            'related_tools': []
        })
        meta_info['filename'] = filename
        
        # Apply all improvements
        content = add_meta_tags(content, meta_info)
        content = fix_heading_structure(content)
        content = add_excerpt(content, meta_info['description'])
        content = add_internal_links(content, meta_info.get('related_blogs', []), meta_info.get('related_tools', []))
        
        faq_type = get_faq_type(filename)
        content = add_faq_section(content, faq_type)
        content = add_cta_section(content)
        content = add_lazy_loading(content)
        content = add_caching_headers(content)
        content = fix_jquery_conflicts(content)
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'✓ Completed: {filename}')
        return True
        
    except Exception as e:
        print(f'✗ Error processing {filepath}: {str(e)}')
        return False

def main():
    """Main function"""
    print('=' * 60)
    print('Comprehensive Blog & Tool Pages Improvement Script')
    print('=' * 60)
    print()
    
    # Find all blog files
    blog_files = []
    for pattern in ['blog-*.html']:
        blog_files.extend(Path('.').glob(pattern))
    
    blog_files = [str(f) for f in blog_files if f.is_file()]
    
    print(f'Found {len(blog_files)} blog files')
    print()
    
    # Process each file
    success_count = 0
    for blog_file in blog_files:
        if process_blog_file(blog_file):
            success_count += 1
        print()
    
    print('=' * 60)
    print(f'Processing complete: {success_count}/{len(blog_files)} files updated')
    print('=' * 60)

if __name__ == '__main__':
    main()

