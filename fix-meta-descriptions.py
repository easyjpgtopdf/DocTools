#!/usr/bin/env python3
"""Fix meta descriptions for all blog pages"""

import os
import re

BLOG_FILES = [
    "blog-how-to-use-word-to-pdf.html",
    "blog-how-to-use-excel-to-pdf.html",
    "blog-how-to-use-ppt-to-pdf.html",
    "blog-why-user-pdf-to-jpg.html",
    "blog-why-user-pdf-to-word.html",
    "blog-why-user-pdf-to-excel.html",
    "blog-why-user-pdf-to-ppt.html",
    "blog-how-to-merge-pdf.html",
    "blog-how-to-split-pdf.html",
    "blog-how-to-compress-pdf.html",
    "blog-how-to-edit-pdf.html",
    "blog-how-to-protect-pdf.html",
    "blog-how-to-unlock-pdf.html",
    "blog-how-to-watermark-pdf.html",
    "blog-how-to-crop-pdf.html",
    "blog-how-to-add-page-numbers.html",
    "blog-how-to-compress-image.html",
    "blog-how-to-resize-image.html",
    "blog-how-to-edit-image.html",
    "blog-how-to-remove-background.html",
    "blog-how-to-ocr-image.html",
    "blog-how-to-watermark-image.html",
    "blog-how-to-make-resume.html",
    "blog-how-to-make-biodata.html",
    "blog-how-to-generate-ai-image.html",
    "blog-how-to-make-marriage-card.html",
    "blog-how-to-protect-excel.html"
]

META_DESCRIPTIONS = {
    "blog-how-to-use-word-to-pdf.html": "Learn how to convert Word documents to PDF format quickly and easily. Complete step-by-step guide with tips, best practices, and troubleshooting for Word to PDF conversion.",
    "blog-how-to-use-excel-to-pdf.html": "Master Excel to PDF conversion with our comprehensive guide. Learn step-by-step instructions, formatting tips, and best practices for converting Excel spreadsheets to PDF.",
    "blog-how-to-use-ppt-to-pdf.html": "Convert PowerPoint presentations to PDF format effortlessly. Complete guide with step-by-step instructions, formatting tips, and best practices for PPT to PDF conversion.",
    "blog-why-user-pdf-to-jpg.html": "Discover why converting PDF to JPG is essential for your workflow. Learn the benefits, use cases, and step-by-step guide for PDF to image conversion.",
    "blog-why-user-pdf-to-word.html": "Learn why converting PDF to Word is crucial for document editing. Complete guide with benefits, use cases, and step-by-step instructions for PDF to Word conversion.",
    "blog-why-user-pdf-to-excel.html": "Understand why PDF to Excel conversion is important for data analysis. Learn benefits, use cases, and complete guide for converting PDF tables to Excel spreadsheets.",
    "blog-why-user-pdf-to-ppt.html": "Discover why converting PDF to PowerPoint is valuable for presentations. Learn benefits, use cases, and step-by-step guide for PDF to PPT conversion.",
    "blog-how-to-merge-pdf.html": "Learn how to merge multiple PDF files into one document. Complete guide with step-by-step instructions, tips, and best practices for PDF merging.",
    "blog-how-to-split-pdf.html": "Master PDF splitting with our comprehensive guide. Learn how to split large PDF files into smaller documents with step-by-step instructions and tips.",
    "blog-how-to-compress-pdf.html": "Reduce PDF file size without losing quality. Complete guide on how to compress PDF files, reduce file size, and optimize documents for sharing and storage.",
    "blog-how-to-edit-pdf.html": "Edit PDF documents easily with our comprehensive guide. Learn how to add text, images, annotations, and modify PDF files with step-by-step instructions.",
    "blog-how-to-protect-pdf.html": "Secure your PDF documents with password protection. Learn how to protect PDF files, set permissions, and prevent unauthorized access with our complete guide.",
    "blog-how-to-unlock-pdf.html": "Unlock password-protected PDF files safely. Learn how to remove PDF passwords, unlock restricted documents, and access protected PDF files with our guide.",
    "blog-how-to-watermark-pdf.html": "Add watermarks to PDF documents for branding and security. Complete guide on how to watermark PDF files with text, images, and custom designs.",
    "blog-how-to-crop-pdf.html": "Crop PDF pages to remove unwanted margins and content. Learn how to crop PDF files, adjust page size, and optimize document layout with our guide.",
    "blog-how-to-add-page-numbers.html": "Add page numbers to PDF documents easily. Learn how to number PDF pages, customize numbering format, and add headers/footers with our complete guide.",
    "blog-how-to-compress-image.html": "Reduce image file size without losing quality. Complete guide on how to compress images, optimize photos, and reduce file size for web and storage.",
    "blog-how-to-resize-image.html": "Resize images to any dimension quickly and easily. Learn how to resize photos, change image dimensions, and maintain aspect ratio with our comprehensive guide.",
    "blog-how-to-edit-image.html": "Edit images online with our comprehensive guide. Learn how to crop, rotate, adjust colors, add filters, and enhance photos with step-by-step instructions.",
    "blog-how-to-remove-background.html": "Remove image backgrounds instantly with our guide. Learn how to remove backgrounds from photos, create transparent images, and isolate subjects easily.",
    "blog-how-to-ocr-image.html": "Extract text from images using OCR technology. Learn how to convert image text to editable text, scan documents, and extract text from photos with our guide.",
    "blog-how-to-watermark-image.html": "Add watermarks to images for protection and branding. Complete guide on how to watermark photos, add text overlays, and protect your images online.",
    "blog-how-to-make-resume.html": "Create professional resumes online easily. Learn how to make a resume, choose templates, format documents, and create job-winning resumes with our complete guide.",
    "blog-how-to-make-biodata.html": "Create marriage biodata and profiles online. Learn how to make biodata for marriage, choose templates, format documents, and create attractive biodata profiles.",
    "blog-how-to-generate-ai-image.html": "Generate AI images and artwork with our comprehensive guide. Learn how to create AI images, use prompts, and generate unique artwork with artificial intelligence.",
    "blog-how-to-make-marriage-card.html": "Design beautiful marriage invitation cards online. Learn how to make marriage cards, choose templates, customize designs, and create stunning wedding invitations.",
    "blog-how-to-protect-excel.html": "Protect Excel spreadsheets with passwords and permissions. Learn how to lock Excel files, protect cells, and secure your data with our complete guide."
}

def fix_meta_description(filepath):
    """Fix meta description for a file"""
    if not os.path.exists(filepath):
        return False
    
    filename = os.path.basename(filepath)
    if filename not in META_DESCRIPTIONS:
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_description = META_DESCRIPTIONS[filename]
        
        # Check if meta description exists
        meta_pattern = r'<meta name="description" content="[^"]*"'
        
        if re.search(meta_pattern, content, re.IGNORECASE):
            # Replace existing
            content = re.sub(
                meta_pattern,
                f'<meta name="description" content="{new_description}"',
                content,
                flags=re.IGNORECASE
            )
        else:
            # Add after title
            title_pattern = r'(<title>.*?</title>)'
            replacement = f'\\1\n    <meta name="description" content="{new_description}">'
            content = re.sub(title_pattern, replacement, content, flags=re.IGNORECASE)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"Error fixing {filepath}: {str(e)}")
        return False

def main():
    """Main function"""
    print("=" * 80)
    print("FIXING META DESCRIPTIONS")
    print("=" * 80)
    print()
    
    fixed = 0
    for blog_file in BLOG_FILES:
        if fix_meta_description(blog_file):
            print(f"✅ Fixed: {blog_file}")
            fixed += 1
        else:
            print(f"ℹ️  Skipped: {blog_file}")
    
    print(f"\n✅ Fixed {fixed} files")
    print("=" * 80)

if __name__ == "__main__":
    main()

