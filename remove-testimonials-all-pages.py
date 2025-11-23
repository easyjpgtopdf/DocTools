#!/usr/bin/env python3
"""
Remove testimonials section from all HTML pages
Only removes testimonials, nothing else
"""

import os
import re
from glob import glob

def remove_testimonials_from_file(filepath):
    """Remove testimonials section from a file"""
    if not os.path.exists(filepath):
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: Full testimonials section with comment
        pattern1 = r'<!-- Testimonials Section -->.*?</section>\s*'
        content = re.sub(pattern1, '', content, flags=re.DOTALL)
        
        # Pattern 2: Testimonials section without comment (if exists)
        pattern2 = r'<section class="testimonials-section"[^>]*>.*?</section>\s*'
        content = re.sub(pattern2, '', content, flags=re.DOTALL)
        
        # Pattern 3: Testimonials section with different class names
        pattern3 = r'<section[^>]*testimonial[^>]*>.*?</section>\s*'
        content = re.sub(pattern3, '', content, flags=re.DOTALL)
        
        # Check if anything was removed
        if content != original_content:
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
    print("REMOVING TESTIMONIALS FROM ALL PAGES")
    print("=" * 80)
    print()
    
    # Find all HTML files
    html_files = []
    
    # Get all .html files in current directory
    html_files.extend(glob("*.html"))
    
    # Also check blog files specifically
    blog_files = [
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
    
    # Add main pages
    main_pages = [
        "index.html",
        "contact.html",
        "about.html",
        "blog-articles.html"
    ]
    
    # Combine all files
    all_files = list(set(html_files + blog_files + main_pages))
    
    print(f"Found {len(all_files)} HTML files to process\n")
    
    removed_count = 0
    skipped_count = 0
    
    for filepath in sorted(all_files):
        if remove_testimonials_from_file(filepath):
            print(f"✅ Removed testimonials from: {filepath}")
            removed_count += 1
        else:
            # Check if file exists and has testimonials
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'testimonial' in content.lower():
                    print(f"⚠️  {filepath}: Testimonials found but pattern didn't match")
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Testimonials removed from: {removed_count} files")
    print(f"ℹ️  Skipped (no testimonials or not found): {skipped_count} files")
    print()
    print("✅ Only testimonials section removed, nothing else deleted!")
    print("=" * 80)

if __name__ == "__main__":
    main()

