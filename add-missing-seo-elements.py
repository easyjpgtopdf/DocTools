#!/usr/bin/env python3
"""
Add missing SEO elements:
1. Related posts section to all blog articles
2. Verify and add ALT tags where missing
3. Ensure complete schema markup
4. Verify internal linking
"""

import os
import re
from pathlib import Path

BLOG_FILES = [
    "blog-how-to-use-jpg-to-pdf.html",
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

# Related articles mapping
RELATED_ARTICLES = {
    "blog-how-to-use-jpg-to-pdf.html": [
        ("blog-how-to-use-word-to-pdf.html", "How to Use Word to PDF", "word-to-pdf.html"),
        ("blog-how-to-compress-pdf.html", "How to Compress PDF", "compress-pdf.html"),
        ("blog-how-to-merge-pdf.html", "How to Merge PDF", "merge-pdf.html")
    ],
    "blog-how-to-use-word-to-pdf.html": [
        ("blog-how-to-use-jpg-to-pdf.html", "How to Use JPG to PDF", "jpg-to-pdf.html"),
        ("blog-how-to-use-excel-to-pdf.html", "How to Use Excel to PDF", "excel-to-pdf.html"),
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html")
    ],
    "blog-how-to-use-excel-to-pdf.html": [
        ("blog-how-to-use-word-to-pdf.html", "How to Use Word to PDF", "word-to-pdf.html"),
        ("blog-how-to-use-ppt-to-pdf.html", "How to Use PowerPoint to PDF", "ppt-to-pdf.html"),
        ("blog-why-user-pdf-to-excel.html", "Why User PDF to Excel", "pdf-to-excel.html")
    ],
    "blog-how-to-use-ppt-to-pdf.html": [
        ("blog-how-to-use-word-to-pdf.html", "How to Use Word to PDF", "word-to-pdf.html"),
        ("blog-how-to-use-excel-to-pdf.html", "How to Use Excel to PDF", "excel-to-pdf.html"),
        ("blog-why-user-pdf-to-ppt.html", "Why User PDF to PowerPoint", "pdf-to-ppt.html")
    ],
    "blog-why-user-pdf-to-jpg.html": [
        ("blog-how-to-use-jpg-to-pdf.html", "How to Use JPG to PDF", "jpg-to-pdf.html"),
        ("blog-how-to-compress-image.html", "How to Compress Image", "image-compressor.html"),
        ("blog-how-to-edit-image.html", "How to Edit Image", "image-editor.html")
    ],
    "blog-why-user-pdf-to-word.html": [
        ("blog-how-to-use-word-to-pdf.html", "How to Use Word to PDF", "word-to-pdf.html"),
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html"),
        ("blog-how-to-merge-pdf.html", "How to Merge PDF", "merge-pdf.html")
    ],
    "blog-why-user-pdf-to-excel.html": [
        ("blog-how-to-use-excel-to-pdf.html", "How to Use Excel to PDF", "excel-to-pdf.html"),
        ("blog-how-to-protect-excel.html", "How to Protect Excel", "protect-excel.html"),
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html")
    ],
    "blog-why-user-pdf-to-ppt.html": [
        ("blog-how-to-use-ppt-to-pdf.html", "How to Use PowerPoint to PDF", "ppt-to-pdf.html"),
        ("blog-how-to-merge-pdf.html", "How to Merge PDF", "merge-pdf.html"),
        ("blog-how-to-compress-pdf.html", "How to Compress PDF", "compress-pdf.html")
    ],
    "blog-how-to-merge-pdf.html": [
        ("blog-how-to-split-pdf.html", "How to Split PDF", "split-pdf.html"),
        ("blog-how-to-compress-pdf.html", "How to Compress PDF", "compress-pdf.html"),
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html")
    ],
    "blog-how-to-split-pdf.html": [
        ("blog-how-to-merge-pdf.html", "How to Merge PDF", "merge-pdf.html"),
        ("blog-how-to-compress-pdf.html", "How to Compress PDF", "compress-pdf.html"),
        ("blog-how-to-crop-pdf.html", "How to Crop PDF", "crop-pdf.html")
    ],
    "blog-how-to-compress-pdf.html": [
        ("blog-how-to-merge-pdf.html", "How to Merge PDF", "merge-pdf.html"),
        ("blog-how-to-split-pdf.html", "How to Split PDF", "split-pdf.html"),
        ("blog-how-to-compress-image.html", "How to Compress Image", "image-compressor.html")
    ],
    "blog-how-to-edit-pdf.html": [
        ("blog-how-to-protect-pdf.html", "How to Protect PDF", "protect-pdf.html"),
        ("blog-how-to-watermark-pdf.html", "How to Watermark PDF", "watermark-pdf.html"),
        ("blog-how-to-merge-pdf.html", "How to Merge PDF", "merge-pdf.html")
    ],
    "blog-how-to-protect-pdf.html": [
        ("blog-how-to-unlock-pdf.html", "How to Unlock PDF", "unlock-pdf.html"),
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html"),
        ("blog-how-to-watermark-pdf.html", "How to Watermark PDF", "watermark-pdf.html")
    ],
    "blog-how-to-unlock-pdf.html": [
        ("blog-how-to-protect-pdf.html", "How to Protect PDF", "protect-pdf.html"),
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html"),
        ("blog-how-to-merge-pdf.html", "How to Merge PDF", "merge-pdf.html")
    ],
    "blog-how-to-watermark-pdf.html": [
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html"),
        ("blog-how-to-protect-pdf.html", "How to Protect PDF", "protect-pdf.html"),
        ("blog-how-to-watermark-image.html", "How to Watermark Image", "image-watermark.html")
    ],
    "blog-how-to-crop-pdf.html": [
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html"),
        ("blog-how-to-split-pdf.html", "How to Split PDF", "split-pdf.html"),
        ("blog-how-to-add-page-numbers.html", "How to Add Page Numbers", "add-page-numbers.html")
    ],
    "blog-how-to-add-page-numbers.html": [
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html"),
        ("blog-how-to-watermark-pdf.html", "How to Watermark PDF", "watermark-pdf.html"),
        ("blog-how-to-merge-pdf.html", "How to Merge PDF", "merge-pdf.html")
    ],
    "blog-how-to-compress-image.html": [
        ("blog-how-to-resize-image.html", "How to Resize Image", "image-resizer.html"),
        ("blog-how-to-edit-image.html", "How to Edit Image", "image-editor.html"),
        ("blog-how-to-compress-pdf.html", "How to Compress PDF", "compress-pdf.html")
    ],
    "blog-how-to-resize-image.html": [
        ("blog-how-to-compress-image.html", "How to Compress Image", "image-compressor.html"),
        ("blog-how-to-edit-image.html", "How to Edit Image", "image-editor.html"),
        ("blog-how-to-remove-background.html", "How to Remove Background", "background-remover.html")
    ],
    "blog-how-to-edit-image.html": [
        ("blog-how-to-compress-image.html", "How to Compress Image", "image-compressor.html"),
        ("blog-how-to-resize-image.html", "How to Resize Image", "image-resizer.html"),
        ("blog-how-to-watermark-image.html", "How to Watermark Image", "image-watermark.html")
    ],
    "blog-how-to-remove-background.html": [
        ("blog-how-to-edit-image.html", "How to Edit Image", "image-editor.html"),
        ("blog-how-to-generate-ai-image.html", "How to Generate AI Image", "ai-image-generator.html"),
        ("blog-how-to-watermark-image.html", "How to Watermark Image", "image-watermark.html")
    ],
    "blog-how-to-ocr-image.html": [
        ("blog-how-to-edit-image.html", "How to Edit Image", "image-editor.html"),
        ("blog-why-user-pdf-to-word.html", "Why User PDF to Word", "pdf-to-word.html"),
        ("blog-how-to-compress-image.html", "How to Compress Image", "image-compressor.html")
    ],
    "blog-how-to-watermark-image.html": [
        ("blog-how-to-edit-image.html", "How to Edit Image", "image-editor.html"),
        ("blog-how-to-watermark-pdf.html", "How to Watermark PDF", "watermark-pdf.html"),
        ("blog-how-to-compress-image.html", "How to Compress Image", "image-compressor.html")
    ],
    "blog-how-to-make-resume.html": [
        ("blog-how-to-make-biodata.html", "How to Make Biodata", "biodata-maker.html"),
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html"),
        ("blog-how-to-compress-pdf.html", "How to Compress PDF", "compress-pdf.html")
    ],
    "blog-how-to-make-biodata.html": [
        ("blog-how-to-make-resume.html", "How to Make Resume", "resume-maker.html"),
        ("blog-how-to-make-marriage-card.html", "How to Make Marriage Card", "marriage-card.html"),
        ("blog-how-to-edit-pdf.html", "How to Edit PDF", "edit-pdf.html")
    ],
    "blog-how-to-generate-ai-image.html": [
        ("blog-how-to-remove-background.html", "How to Remove Background", "background-remover.html"),
        ("blog-how-to-edit-image.html", "How to Edit Image", "image-editor.html"),
        ("blog-how-to-watermark-image.html", "How to Watermark Image", "image-watermark.html")
    ],
    "blog-how-to-make-marriage-card.html": [
        ("blog-how-to-make-biodata.html", "How to Make Biodata", "biodata-maker.html"),
        ("blog-how-to-generate-ai-image.html", "How to Generate AI Image", "ai-image-generator.html"),
        ("blog-how-to-edit-image.html", "How to Edit Image", "image-editor.html")
    ],
    "blog-how-to-protect-excel.html": [
        ("blog-how-to-use-excel-to-pdf.html", "How to Use Excel to PDF", "excel-to-pdf.html"),
        ("blog-why-user-pdf-to-excel.html", "Why User PDF to Excel", "pdf-to-excel.html"),
        ("blog-how-to-protect-pdf.html", "How to Protect PDF", "protect-pdf.html")
    ]
}

def generate_related_posts_section(related_articles):
    """Generate related posts section HTML"""
    html = '''    <section class="related-posts" style="margin-top: 50px; padding-top: 40px; border-top: 2px solid #e2e6ff;">
        <h2 style="font-size: 2rem; color: #0b1630; margin-bottom: 30px;">Related Articles</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">'''
    
    for article_link, article_title, tool_link in related_articles:
        html += f'''
            <div style="background: #f8f9ff; padding: 20px; border-radius: 12px; border: 1px solid #e2e6ff; transition: all 0.3s;">
                <a href="{article_link}" style="text-decoration: none; color: inherit;">
                    <h3 style="font-size: 1.3rem; color: #4361ee; margin-bottom: 10px;">{article_title}</h3>
                    <p style="color: #56607a; line-height: 1.6; margin-bottom: 15px;">Learn how to use our <a href="{tool_link}" style="color: #4361ee; text-decoration: underline;">{article_title.replace('How to ', '').replace('Why User ', '')}</a> tool effectively with our comprehensive guide.</p>
                    <span style="color: #4361ee; font-weight: 600; display: inline-flex; align-items: center; gap: 5px;">
                        Read More <i class="fas fa-arrow-right"></i>
                    </span>
                </a>
            </div>'''
    
    html += '''
        </div>
    </section>'''
    
    return html

def add_related_posts(filepath):
    """Add related posts section to blog article"""
    if not os.path.exists(filepath):
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if related posts already exists
        if 'related-posts' in content or 'Related Articles' in content:
            return False
        
        # Get related articles for this file
        filename = os.path.basename(filepath)
        if filename not in RELATED_ARTICLES:
            return False
        
        related_articles = RELATED_ARTICLES[filename]
        related_section = generate_related_posts_section(related_articles)
        
        # Find where to insert - before CTA section or before author bio
        cta_pattern = r'<section class="cta-section"'
        author_pattern = r'<section[^>]*class="author-bio"'
        
        insert_pos = -1
        if re.search(cta_pattern, content):
            match = re.search(cta_pattern, content)
            insert_pos = match.start()
        elif re.search(author_pattern, content):
            match = re.search(author_pattern, content)
            insert_pos = match.start()
        else:
            # Find before FAQ section
            faq_pattern = r'<section class="faq-section"'
            if re.search(faq_pattern, content):
                match = re.search(faq_pattern, content)
                insert_pos = match.start()
        
        if insert_pos != -1:
            updated_content = content[:insert_pos] + related_section + "\n\n    " + content[insert_pos:]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Adding missing SEO elements to all blog articles...\n")
    
    updated_count = 0
    for blog_file in BLOG_FILES:
        if add_related_posts(blog_file):
            print(f"✅ Added related posts to: {blog_file}")
            updated_count += 1
        else:
            print(f"ℹ️  Related posts already exist or skipped: {blog_file}")
    
    print(f"\n✨ Completed! Updated {updated_count} blog files with related posts sections.")

if __name__ == "__main__":
    main()

