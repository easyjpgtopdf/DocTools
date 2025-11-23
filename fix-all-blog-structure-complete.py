#!/usr/bin/env python3
"""
Comprehensive fix for all blog articles:
1. Fix broken CTA sections
2. Add related posts sections
3. Ensure proper structure
4. Fix any broken HTML
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

def get_tool_info(filename):
    """Get tool information from filename"""
    tool_map = {
        "blog-how-to-use-jpg-to-pdf.html": ("JPG to PDF", "jpg-to-pdf.html"),
        "blog-how-to-use-word-to-pdf.html": ("Word to PDF", "word-to-pdf.html"),
        "blog-how-to-use-excel-to-pdf.html": ("Excel to PDF", "excel-to-pdf.html"),
        "blog-how-to-use-ppt-to-pdf.html": ("PowerPoint to PDF", "ppt-to-pdf.html"),
        "blog-why-user-pdf-to-jpg.html": ("PDF to JPG", "pdf-to-jpg.html"),
        "blog-why-user-pdf-to-word.html": ("PDF to Word", "pdf-to-word.html"),
        "blog-why-user-pdf-to-excel.html": ("PDF to Excel", "pdf-to-excel.html"),
        "blog-why-user-pdf-to-ppt.html": ("PDF to PowerPoint", "pdf-to-ppt.html"),
        "blog-how-to-merge-pdf.html": ("Merge PDF", "merge-pdf.html"),
        "blog-how-to-split-pdf.html": ("Split PDF", "split-pdf.html"),
        "blog-how-to-compress-pdf.html": ("Compress PDF", "compress-pdf.html"),
        "blog-how-to-edit-pdf.html": ("Edit PDF", "edit-pdf.html"),
        "blog-how-to-protect-pdf.html": ("Protect PDF", "protect-pdf.html"),
        "blog-how-to-unlock-pdf.html": ("Unlock PDF", "unlock-pdf.html"),
        "blog-how-to-watermark-pdf.html": ("Watermark PDF", "watermark-pdf.html"),
        "blog-how-to-crop-pdf.html": ("Crop PDF", "crop-pdf.html"),
        "blog-how-to-add-page-numbers.html": ("Add Page Numbers", "add-page-numbers.html"),
        "blog-how-to-compress-image.html": ("Compress Image", "image-compressor.html"),
        "blog-how-to-resize-image.html": ("Resize Image", "image-resizer.html"),
        "blog-how-to-edit-image.html": ("Edit Image", "image-editor.html"),
        "blog-how-to-remove-background.html": ("Remove Background", "background-remover.html"),
        "blog-how-to-ocr-image.html": ("OCR Image", "ocr-image.html"),
        "blog-how-to-watermark-image.html": ("Watermark Image", "image-watermark.html"),
        "blog-how-to-make-resume.html": ("Make Resume", "resume-maker.html"),
        "blog-how-to-make-biodata.html": ("Make Biodata", "biodata-maker.html"),
        "blog-how-to-generate-ai-image.html": ("Generate AI Image", "ai-image-generator.html"),
        "blog-how-to-make-marriage-card.html": ("Make Marriage Card", "marriage-card.html"),
        "blog-how-to-protect-excel.html": ("Protect Excel", "protect-excel.html")
    }
    return tool_map.get(filename, ("Tool", "index.html"))

def generate_related_posts(related_articles):
    """Generate related posts HTML"""
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

def fix_blog_file(filepath):
    """Fix a blog file completely"""
    if not os.path.exists(filepath):
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        filename = os.path.basename(filepath)
        tool_name, tool_link = get_tool_info(filename)
        
        # Check if related posts exists
        has_related = 'related-posts' in content or 'Related Articles' in content
        
        # Fix broken CTA section
        broken_cta_pattern = r'<section class="cta-section"[^>]*>.*?<h2[^>]*>Ready to Get Started\?</h2>.*?<h3>Issue:.*?</section>'
        if re.search(broken_cta_pattern, content, re.DOTALL):
            # Replace broken CTA
            proper_cta = f'''    <section class="cta-section" style="margin: 40px 0; padding: 40px; background: linear-gradient(135deg, #4361ee, #3a0ca3); border-radius: 16px; text-align: center; color: white;">
        <h2 style="font-size: 2rem; margin-bottom: 20px; color: white;">Ready to Get Started?</h2>
        <p style="font-size: 1.2rem; margin-bottom: 30px; opacity: 0.9;">Try our free {tool_name} tool and experience the difference</p>
        <a href="{tool_link}" style="display: inline-block; background: white; color: #4361ee; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 1.1rem; transition: transform 0.3s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
            <i class="fas fa-rocket" style="margin-right: 8px;"></i>Try {tool_name} Now
        </a>
    </section>'''
            content = re.sub(broken_cta_pattern, proper_cta, content, flags=re.DOTALL)
        
        # Fix broken author bio (duplicate p tags)
        broken_bio_pattern = r'<p style="font-size: 1\.1rem; color: #56607a; line-height: 1\.8; margin: 0;">\s*<p style="font-size: 1\.1rem; color: #56607a; line-height: 1\.8; margin: 0;">'
        if re.search(broken_bio_pattern, content):
            content = re.sub(broken_bio_pattern, '<p style="font-size: 1.1rem; color: #56607a; line-height: 1.8; margin: 0;">', content)
        
        # Add related posts if missing
        if not has_related and filename in RELATED_ARTICLES:
            related_section = generate_related_posts(RELATED_ARTICLES[filename])
            
            # Find insertion point - before CTA section
            cta_pattern = r'<section class="cta-section"'
            match = re.search(cta_pattern, content)
            if match:
                content = content[:match.start()] + related_section + "\n\n    " + content[match.start():]
        
        # Fix broken section tags
        content = re.sub(r'<section\s+<section', '<section', content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 Fixing all blog articles structure and adding missing elements...\n")
    
    updated_count = 0
    for blog_file in BLOG_FILES:
        if fix_blog_file(blog_file):
            print(f"✅ Fixed: {blog_file}")
            updated_count += 1
        else:
            print(f"ℹ️  No changes needed: {blog_file}")
    
    print(f"\n✨ Completed! Fixed {updated_count} blog files.")

if __name__ == "__main__":
    main()

