#!/usr/bin/env python3
"""
Add FAQ questions to all blog pages
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

FAQ_QUESTIONS = '''
            <div class="faq-item" style="margin-bottom: 20px; padding: 20px; background: #f8f9ff; border-radius: 12px; border-left: 4px solid #4361ee;">
                <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px; cursor: pointer;" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
                    <i class="fas fa-question-circle" style="color: #4361ee; margin-right: 8px;"></i>
                    Is this tool really free?
                </h3>
                <p style="font-size: 1rem; color: #56607a; line-height: 1.6; margin-top: 10px; display: block;">
                    Yes, 100% free! There are no hidden charges and no registration required.
                </p>
            </div>

            <div class="faq-item" style="margin-bottom: 20px; padding: 20px; background: #f8f9ff; border-radius: 12px; border-left: 4px solid #4361ee;">
                <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px; cursor: pointer;" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
                    <i class="fas fa-question-circle" style="color: #4361ee; margin-right: 8px;"></i>
                    How many images can I convert at once?
                </h3>
                <p style="font-size: 1rem; color: #56607a; line-height: 1.6; margin-top: 10px; display: block;">
                    Currently, our tool supports converting one image at a time. But you can use it as many times as you need.
                </p>
            </div>
'''

def add_faq_questions(filepath):
    """Add FAQ questions to a file"""
    if not os.path.exists(filepath):
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if FAQ questions already exist
        if 'Is this tool really free?' in content:
            return False  # Already added
        
        # Find FAQ section
        faq_pattern = r'(<section class="faq-section"[^>]*>.*?<div class="faq-container"[^>]*>)'
        match = re.search(faq_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            # Insert FAQ questions after faq-container opening tag
            insert_pos = match.end()
            content = content[:insert_pos] + '\n\n' + FAQ_QUESTIONS + '\n\n            ' + content[insert_pos:]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            # Try alternative pattern
            faq_pattern2 = r'(<h2[^>]*>Frequently Asked Questions</h2>.*?<div[^>]*faq-container[^>]*>)'
            match2 = re.search(faq_pattern2, content, re.DOTALL | re.IGNORECASE)
            if match2:
                insert_pos = match2.end()
                content = content[:insert_pos] + '\n\n' + FAQ_QUESTIONS + '\n\n            ' + content[insert_pos:]
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {str(e)}")
        return False

def main():
    """Main function"""
    print("=" * 80)
    print("ADDING FAQ QUESTIONS TO ALL BLOG PAGES")
    print("=" * 80)
    print()
    
    added_count = 0
    for blog_file in BLOG_FILES:
        if add_faq_questions(blog_file):
            print(f"✅ Added FAQ questions to: {blog_file}")
            added_count += 1
        else:
            print(f"ℹ️  Checked: {blog_file}")
    
    print(f"\n✅ Added FAQ questions to {added_count} files")
    print("=" * 80)

if __name__ == "__main__":
    main()

