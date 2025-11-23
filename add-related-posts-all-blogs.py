#!/usr/bin/env python3
"""
Add related posts section to all blog articles that are missing it
"""

import os
import re

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

def generate_related_posts_html(related_articles):
    """Generate related posts HTML"""
    html = '''    <section class="related-posts" style="margin-top: 50px; padding-top: 40px; border-top: 2px solid #e2e6ff;">
        <h2 style="font-size: 2rem; color: #0b1630; margin-bottom: 30px;">Related Articles</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">'''
    
    for article_link, article_title, tool_link in related_articles:
        tool_name = article_title.replace('How to ', '').replace('Why User ', '')
        html += f'''
            <div style="background: #f8f9ff; padding: 20px; border-radius: 12px; border: 1px solid #e2e6ff; transition: all 0.3s;">
                <a href="{article_link}" style="text-decoration: none; color: inherit;">
                    <h3 style="font-size: 1.3rem; color: #4361ee; margin-bottom: 10px;">{article_title}</h3>
                    <p style="color: #56607a; line-height: 1.6; margin-bottom: 15px;">Learn how to use our <a href="{tool_link}" style="color: #4361ee; text-decoration: underline;">{tool_name}</a> tool effectively with our comprehensive guide.</p>
                    <span style="color: #4361ee; font-weight: 600; display: inline-flex; align-items: center; gap: 5px;">
                        Read More <i class="fas fa-arrow-right"></i>
                    </span>
                </a>
            </div>'''
    
    html += '''
        </div>
    </section>'''
    return html

def add_related_posts_to_file(filepath):
    """Add related posts section to a blog file"""
    if not os.path.exists(filepath):
        return False
    
    filename = os.path.basename(filepath)
    if filename not in RELATED_ARTICLES:
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already exists
        if 'related-posts' in content or 'Related Articles' in content:
            return False
        
        related_html = generate_related_posts_html(RELATED_ARTICLES[filename])
        
        # Find insertion point - after </article> and before CTA
        article_end_pattern = r'</article>\s*\n\s*'
        cta_pattern = r'<section class="cta-section"'
        
        article_match = re.search(article_end_pattern, content)
        cta_match = re.search(cta_pattern, content)
        
        if article_match and cta_match:
            # Insert between article and CTA
            insert_pos = article_match.end()
            content = content[:insert_pos] + "\n" + related_html + "\n\n    " + content[insert_pos:]
        elif article_match:
            # Insert right after article
            insert_pos = article_match.end()
            content = content[:insert_pos] + "\n" + related_html + "\n\n    " + content[insert_pos:]
        else:
            return False
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Adding related posts sections to all blog articles...\n")
    
    updated = 0
    for blog_file in BLOG_FILES:
        if add_related_posts_to_file(blog_file):
            print(f"✅ Added related posts to: {blog_file}")
            updated += 1
        else:
            print(f"ℹ️  Skipped (already exists or error): {blog_file}")
    
    print(f"\n✨ Completed! Added related posts to {updated} blog files.")

if __name__ == "__main__":
    main()

