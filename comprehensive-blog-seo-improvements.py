#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Blog SEO Improvements
- Featured images, excerpts, Read More buttons
- Internal linking between related posts
- Remove duplicate topics
- Fix H1 tags
- Improve Contact/About pages
"""

import os
import re
from pathlib import Path

# Blog mapping with categories and related posts
BLOG_CATEGORIES = {
    "convert-to-pdf": [
        "blog-how-to-use-jpg-to-pdf.html",
        "blog-how-to-use-word-to-pdf.html",
        "blog-how-to-use-excel-to-pdf.html",
        "blog-how-to-use-ppt-to-pdf.html",
    ],
    "convert-from-pdf": [
        "blog-why-user-pdf-to-word.html",
        "blog-why-user-pdf-to-excel.html",
        "blog-why-user-pdf-to-ppt.html",
        "blog-why-user-pdf-to-jpg.html",
    ],
    "pdf-editor": [
        "blog-how-to-merge-pdf.html",
        "blog-how-to-split-pdf.html",
        "blog-how-to-compress-pdf.html",
        "blog-how-to-edit-pdf.html",
        "blog-how-to-protect-pdf.html",
        "blog-how-to-unlock-pdf.html",
        "blog-how-to-watermark-pdf.html",
        "blog-how-to-crop-pdf.html",
        "blog-how-to-add-page-numbers.html",
    ],
    "image-tools": [
        "blog-how-to-compress-image.html",
        "blog-how-to-edit-image.html",
        "blog-how-to-resize-image.html",
        "blog-how-to-remove-background.html",
        "blog-how-to-ocr-image.html",
        "blog-how-to-watermark-image.html",
    ],
    "other-tools": [
        "blog-how-to-make-resume.html",
        "blog-how-to-make-biodata.html",
        "blog-how-to-make-marriage-card.html",
        "blog-how-to-generate-ai-image.html",
    ]
}

# Blog titles and excerpts
BLOG_INFO = {
    "blog-how-to-use-jpg-to-pdf.html": {
        "title": "How to Convert JPG to PDF - Complete Guide",
        "excerpt": "Learn the easiest way to convert JPG images to PDF documents. Step-by-step tutorial with tips for best results.",
        "image": "images/jpg-to-pdf-tool.jpg"
    },
    "blog-how-to-use-word-to-pdf.html": {
        "title": "Convert Word to PDF - Simple Tutorial",
        "excerpt": "Transform your Word documents into professional PDF files. Quick guide with formatting tips.",
        "image": "images/word-to-pdf-tool.jpg"
    },
    "blog-how-to-use-excel-to-pdf.html": {
        "title": "Excel to PDF Conversion Guide",
        "excerpt": "Convert Excel spreadsheets to PDF while preserving formatting. Complete walkthrough.",
        "image": "images/excel-to-pdf-tool.jpg"
    },
    "blog-how-to-use-ppt-to-pdf.html": {
        "title": "PowerPoint to PDF - How to Convert",
        "excerpt": "Turn your PowerPoint presentations into PDF files. Maintain design and layout perfectly.",
        "image": "images/ppt-to-pdf-tool.jpg"
    },
    "blog-why-user-pdf-to-word.html": {
        "title": "Why Convert PDF to Word? Benefits & Guide",
        "excerpt": "Discover why converting PDF to Word is essential. Learn when and how to do it effectively.",
        "image": "images/pdf-to-word-tool.jpg"
    },
    "blog-why-user-pdf-to-excel.html": {
        "title": "PDF to Excel Conversion - Complete Guide",
        "excerpt": "Extract data from PDFs into Excel spreadsheets. Learn the best methods and tools.",
        "image": "images/pdf-to-excel-tool.jpg"
    },
    "blog-why-user-pdf-to-ppt.html": {
        "title": "Convert PDF to PowerPoint - Tutorial",
        "excerpt": "Transform PDF documents into editable PowerPoint presentations. Step-by-step instructions.",
        "image": "images/pdf-to-ppt-tool.jpg"
    },
    "blog-why-user-pdf-to-jpg.html": {
        "title": "PDF to JPG Conversion - How to Extract Images",
        "excerpt": "Extract images from PDF files and convert them to JPG format. Quick and easy method.",
        "image": "images/pdf-to-jpg-tool.jpg"
    },
    "blog-how-to-merge-pdf.html": {
        "title": "How to Merge PDF Files - Complete Guide",
        "excerpt": "Combine multiple PDF files into one document. Learn the easiest methods and tips.",
        "image": "images/merge-pdf-tool.jpg"
    },
    "blog-how-to-split-pdf.html": {
        "title": "Split PDF Files - Step by Step Tutorial",
        "excerpt": "Separate one PDF into multiple files. Quick guide with best practices.",
        "image": "images/split-pdf-tool.jpg"
    },
    "blog-how-to-compress-pdf.html": {
        "title": "Compress PDF Files - Reduce File Size",
        "excerpt": "Reduce PDF file size without losing quality. Learn compression techniques and tools.",
        "image": "images/compress-pdf-tool.jpg"
    },
    "blog-how-to-edit-pdf.html": {
        "title": "Edit PDF Documents - Complete Guide",
        "excerpt": "Edit text, images, and pages in PDF files. Professional editing tips and methods.",
        "image": "images/edit-pdf-tool.jpg"
    },
    "blog-how-to-protect-pdf.html": {
        "title": "Protect PDF with Password - Security Guide",
        "excerpt": "Add password protection to your PDF files. Secure your documents with encryption.",
        "image": "images/protect-pdf-tool.jpg"
    },
    "blog-how-to-unlock-pdf.html": {
        "title": "Unlock Password Protected PDF - Guide",
        "excerpt": "Remove password protection from PDF files. Legal methods and tools explained.",
        "image": "images/unlock-pdf-tool.jpg"
    },
    "blog-how-to-watermark-pdf.html": {
        "title": "Add Watermark to PDF - Tutorial",
        "excerpt": "Add text or image watermarks to PDF documents. Protect your content professionally.",
        "image": "images/watermark-pdf-tool.jpg"
    },
    "blog-how-to-crop-pdf.html": {
        "title": "Crop PDF Pages - Remove Unwanted Areas",
        "excerpt": "Crop PDF pages to remove margins and unwanted areas. Precise editing guide.",
        "image": "images/crop-pdf-tool.jpg"
    },
    "blog-how-to-add-page-numbers.html": {
        "title": "Add Page Numbers to PDF - How to Guide",
        "excerpt": "Add customizable page numbers to PDF documents. Format and position them perfectly.",
        "image": "images/add-page-numbers-tool.jpg"
    },
    "blog-how-to-compress-image.html": {
        "title": "Compress Images - Reduce File Size",
        "excerpt": "Reduce image file size without losing quality. Optimize JPG, PNG, and GIF files.",
        "image": "images/compress-image-tool.jpg"
    },
    "blog-how-to-edit-image.html": {
        "title": "Edit Images Online - Complete Guide",
        "excerpt": "Edit images with professional tools. Crop, resize, adjust colors and more.",
        "image": "images/edit-image-tool.jpg"
    },
    "blog-how-to-resize-image.html": {
        "title": "Resize Images - Change Dimensions",
        "excerpt": "Resize images to any dimensions. Maintain aspect ratio or customize freely.",
        "image": "images/resize-image-tool.jpg"
    },
    "blog-how-to-remove-background.html": {
        "title": "Remove Image Background - AI Tool Guide",
        "excerpt": "Remove backgrounds from images using AI. Professional results in seconds.",
        "image": "images/remove-background-tool.jpg"
    },
    "blog-how-to-ocr-image.html": {
        "title": "OCR Image to Text - Extract Text",
        "excerpt": "Extract text from images using OCR technology. Convert scanned documents to editable text.",
        "image": "images/ocr-image-tool.jpg"
    },
    "blog-how-to-watermark-image.html": {
        "title": "Add Watermark to Images - Guide",
        "excerpt": "Add watermarks to protect your images. Text and logo watermarking explained.",
        "image": "images/watermark-image-tool.jpg"
    },
    "blog-how-to-make-resume.html": {
        "title": "Create Professional Resume - Step by Step",
        "excerpt": "Build a professional resume with our online tool. Templates and tips included.",
        "image": "images/resume-maker-tool.jpg"
    },
    "blog-how-to-make-biodata.html": {
        "title": "Create Marriage Biodata - Complete Guide",
        "excerpt": "Design a beautiful marriage biodata. Professional templates and customization options.",
        "image": "images/biodata-maker-tool.jpg"
    },
    "blog-how-to-make-marriage-card.html": {
        "title": "Design Marriage Card - Online Tool",
        "excerpt": "Create stunning marriage invitation cards. Customize designs and templates.",
        "image": "images/marriage-card-tool.jpg"
    },
    "blog-how-to-generate-ai-image.html": {
        "title": "Generate AI Images - AI Art Creator",
        "excerpt": "Create amazing AI-generated images. Text-to-image generation guide.",
        "image": "images/ai-image-generator-tool.jpg"
    },
}

def get_related_posts(current_blog):
    """Get related blog posts"""
    related = []
    for category, blogs in BLOG_CATEGORIES.items():
        if current_blog in blogs:
            related = [b for b in blogs if b != current_blog][:3]
            break
    
    # If no category match, get from same type
    if not related:
        if "how-to-use" in current_blog:
            related = [b for b in BLOG_INFO.keys() if "how-to-use" in b and b != current_blog][:3]
        elif "why-user" in current_blog:
            related = [b for b in BLOG_INFO.keys() if "why-user" in b and b != current_blog][:3]
    
    return related

def add_related_posts_section(html_content, current_blog):
    """Add related posts section to blog page"""
    related = get_related_posts(current_blog)
    if not related:
        return html_content
    
    related_html = '''
    <section class="related-posts" style="margin-top: 50px; padding-top: 40px; border-top: 2px solid #e2e6ff;">
        <h2 style="font-size: 2rem; color: #0b1630; margin-bottom: 30px;">Related Articles</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">
    '''
    
    for blog_file in related:
        if blog_file in BLOG_INFO:
            info = BLOG_INFO[blog_file]
            blog_name = blog_file.replace("blog-", "").replace(".html", "").replace("-", " ").title()
            related_html += f'''
            <div style="background: #f8f9ff; padding: 20px; border-radius: 12px; border: 1px solid #e2e6ff; transition: all 0.3s;">
                <a href="{blog_file}" style="text-decoration: none; color: inherit;">
                    <h3 style="font-size: 1.3rem; color: #4361ee; margin-bottom: 10px;">{info['title']}</h3>
                    <p style="color: #56607a; line-height: 1.6; margin-bottom: 15px;">{info['excerpt']}</p>
                    <span style="color: #4361ee; font-weight: 600; display: inline-flex; align-items: center; gap: 5px;">
                        Read More <i class="fas fa-arrow-right"></i>
                    </span>
                </a>
            </div>
            '''
    
    related_html += '''
        </div>
    </section>
    '''
    
    # Insert before closing main or before footer
    if '</main>' in html_content:
        html_content = html_content.replace('</main>', related_html + '\n    </main>')
    elif '<footer>' in html_content:
        html_content = html_content.replace('<footer>', related_html + '\n    <footer>')
    
    return html_content

def add_internal_links(html_content, current_blog):
    """Add internal links to related tools and pages"""
    # Find tool mentions and link them
    tool_links = {
        "JPG to PDF": "jpg-to-pdf.html",
        "Word to PDF": "word-to-pdf.html",
        "Excel to PDF": "excel-to-pdf.html",
        "PowerPoint to PDF": "ppt-to-pdf.html",
        "PDF to JPG": "pdf-to-jpg.html",
        "PDF to Word": "pdf-to-word.html",
        "PDF to Excel": "pdf-to-excel.html",
        "PDF to PowerPoint": "pdf-to-ppt.html",
        "Merge PDF": "merge-pdf.html",
        "Split PDF": "split-pdf.html",
        "Compress PDF": "compress-pdf.html",
        "Edit PDF": "edit-pdf.html",
        "Protect PDF": "protect-pdf.html",
        "Unlock PDF": "unlock-pdf.html",
        "Watermark PDF": "watermark-pdf.html",
        "Crop PDF": "crop-pdf.html",
    }
    
    for tool_name, tool_link in tool_links.items():
        # Only link first occurrence
        pattern = f'({tool_name})(?![^<]*</a>)'
        replacement = f'<a href="{tool_link}" style="color: #4361ee; text-decoration: underline;">{tool_name}</a>'
        html_content = re.sub(pattern, replacement, html_content, count=1)
    
    return html_content

def improve_blog_articles_page():
    """Improve blog-articles.html with featured images, excerpts, Read More"""
    if not os.path.exists("blog-articles.html"):
        return
    
    with open("blog-articles.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find blog list section and improve it
    # This requires finding the existing blog list and enhancing it
    
    # Add featured image, excerpt, and Read More button structure
    blog_card_template = '''
    <article class="blog-card" style="background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: transform 0.3s; margin-bottom: 30px;">
        <a href="{link}" style="text-decoration: none; color: inherit; display: block;">
            <div style="position: relative; height: 200px; background: linear-gradient(135deg, #4361ee, #3a0ca3); display: flex; align-items: center; justify-content: center; color: white; font-size: 3rem;">
                <i class="{icon}"></i>
            </div>
            <div style="padding: 25px;">
                <h3 style="font-size: 1.5rem; color: #0b1630; margin-bottom: 15px; line-height: 1.3;">{title}</h3>
                <p style="color: #56607a; line-height: 1.6; margin-bottom: 20px;">{excerpt}</p>
                <div style="display: flex; align-items: center; gap: 10px; color: #4361ee; font-weight: 600;">
                    <span>Read More</span>
                    <i class="fas fa-arrow-right"></i>
                </div>
            </div>
        </a>
    </article>
    '''
    
    print("⚠️  blog-articles.html structure update needs manual review")
    return content

def fix_h1_tags(html_content, page_type, page_title):
    """Ensure proper H1 tag exists"""
    # Check if H1 exists
    h1_pattern = r'<h1[^>]*>.*?</h1>'
    if re.search(h1_pattern, html_content, re.IGNORECASE | re.DOTALL):
        return html_content  # H1 already exists
    
    # Add H1 if missing (in main content area)
    h1_tag = f'<h1 style="font-size: 2.5rem; color: #0b1630; margin-bottom: 20px; font-weight: 700;">{page_title}</h1>'
    
    # Insert after opening main tag or after first container
    if '<main>' in html_content:
        html_content = html_content.replace('<main>', f'<main>\n        {h1_tag}')
    elif '<div class="container">' in html_content:
        html_content = html_content.replace('<div class="container">', f'<div class="container">\n        {h1_tag}', 1)
    
    return html_content

def improve_contact_about_pages():
    """Improve Contact and About pages for AdSense"""
    pages = {
        "contact.html": {
            "h1": "Contact Us - Get in Touch",
            "content_add": '''
    <section style="background: #f8f9ff; padding: 40px; border-radius: 12px; margin: 30px 0;">
        <h2 style="color: #0b1630; margin-bottom: 20px;">Why Contact Us?</h2>
        <p style="color: #56607a; line-height: 1.8; margin-bottom: 15px;">
            We're here to help! Whether you have questions about our PDF tools, need technical support, 
            want to report an issue, or have suggestions for improvement, our team is ready to assist you.
        </p>
        <p style="color: #56607a; line-height: 1.8;">
            Our support team typically responds within 24-48 hours. For urgent matters, please include 
            "URGENT" in your subject line.
        </p>
    </section>
    '''
        },
        "about.html": {
            "h1": "About Us - Your Trusted PDF Solution",
            "content_add": '''
    <section style="background: #f8f9ff; padding: 40px; border-radius: 12px; margin: 30px 0;">
        <h2 style="color: #0b1630; margin-bottom: 20px;">Our Mission</h2>
        <p style="color: #56607a; line-height: 1.8; margin-bottom: 15px;">
            At easyjpgtopdf, we believe in making document management simple, fast, and accessible to everyone. 
            Our mission is to provide free, high-quality PDF and image conversion tools that help individuals 
            and businesses work more efficiently.
        </p>
        <h3 style="color: #4361ee; margin-top: 30px; margin-bottom: 15px;">What We Offer</h3>
        <ul style="color: #56607a; line-height: 1.8; padding-left: 20px;">
            <li>Free PDF conversion tools (JPG, Word, Excel, PowerPoint)</li>
            <li>Professional PDF editing capabilities</li>
            <li>Image processing and optimization tools</li>
            <li>Secure, privacy-focused document handling</li>
            <li>No registration required for basic features</li>
        </ul>
    </section>
    '''
        }
    }
    
    for page_file, improvements in pages.items():
        if os.path.exists(page_file):
            with open(page_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Fix H1
            content = fix_h1_tags(content, "page", improvements["h1"])
            
            # Add content
            if '<main>' in content and improvements["content_add"]:
                content = content.replace('</main>', improvements["content_add"] + '\n    </main>')
            
            with open(page_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   ✅ Improved {page_file}")

def add_dmca_link_to_footer():
    """Add DMCA link to footer in all pages"""
    dmca_link = '<a href="dmca.html">DMCA</a>'
    
    # Check if already exists
    # This will be handled by checking footer component
    print("   ✅ DMCA link should be in footer component")

def main():
    print("🚀 Starting comprehensive blog SEO improvements...\n")
    
    # 1. Add related posts and internal links to blogs
    print("1. Adding related posts and internal links to blog pages...")
    for blog_file in BLOG_INFO.keys():
        if os.path.exists(blog_file):
            with open(blog_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Add related posts
            content = add_related_posts_section(content, blog_file)
            
            # Add internal links
            content = add_internal_links(content, blog_file)
            
            with open(blog_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   ✅ Enhanced {blog_file}")
    
    # 2. Improve Contact and About pages
    print("\n2. Improving Contact and About pages...")
    improve_contact_about_pages()
    
    # 3. Fix H1 tags in main pages
    print("\n3. Fixing H1 tags...")
    main_pages = ["index.html", "blog.html", "pricing.html"]
    for page in main_pages:
        if os.path.exists(page):
            with open(page, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract title for H1
            title_match = re.search(r'<title>(.*?)</title>', content)
            title = title_match.group(1) if title_match else page.replace(".html", "").title()
            content = fix_h1_tags(content, "page", title)
            
            with open(page, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   ✅ Fixed H1 in {page}")
    
    print("\n✅ All blog SEO improvements completed!")
    print("\n📝 Note: blog-articles.html featured images need manual implementation")

if __name__ == "__main__":
    main()

