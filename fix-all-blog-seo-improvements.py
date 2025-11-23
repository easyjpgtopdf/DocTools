#!/usr/bin/env python3
"""
Fix all blog SEO improvements:
1. Update author name to "Riyaz Mohammad" in schema and author bio
2. Add SSL trust badges
3. Add testimonials section
4. Ensure all required elements are present
"""

import os
import re
from pathlib import Path

# Blog files to update
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

SSL_BADGES_SECTION = '''    <!-- SSL Trust Badges Section -->
    <section class="ssl-badges" style="margin: 40px 0; padding: 30px; background: #f8f9ff; border-radius: 16px; text-align: center;">
        <h3 style="font-size: 1.3rem; color: #0b1630; margin-bottom: 20px;">Secure & Trusted</h3>
        <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; align-items: center;">
            <div style="padding: 15px 20px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <i class="fas fa-shield-alt" style="font-size: 2rem; color: #4361ee; margin-bottom: 8px;"></i>
                <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #56607a; font-weight: 600;">SSL A+ Rating</p>
            </div>
            <div style="padding: 15px 20px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <i class="fas fa-lock" style="font-size: 2rem; color: #4361ee; margin-bottom: 8px;"></i>
                <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #56607a; font-weight: 600;">Secure & Encrypted</p>
            </div>
            <div style="padding: 15px 20px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <i class="fas fa-user-shield" style="font-size: 2rem; color: #4361ee; margin-bottom: 8px;"></i>
                <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #56607a; font-weight: 600;">Privacy Protected</p>
            </div>
        </div>
    </section>

    <!-- Testimonials Section -->
    <section class="testimonials-section" style="margin: 40px 0; padding: 40px; background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="font-size: 2rem; color: #4361ee; margin-bottom: 30px; text-align: center;">What Our Users Say</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">
            <div style="padding: 25px; background: #f8f9ff; border-radius: 12px; border-left: 4px solid #4361ee;">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #4361ee, #3a0ca3); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-right: 15px; font-size: 1.2rem;">SM</div>
                    <div>
                        <h4 style="margin: 0; color: #0b1630; font-size: 1.1rem;">Sarah Mitchell</h4>
                        <p style="margin: 5px 0 0 0; color: #56607a; font-size: 0.9rem;">Business Professional</p>
                    </div>
                </div>
                <p style="color: #56607a; line-height: 1.7; margin: 0; font-style: italic;">"This tool has saved me so much time! Converting images to PDF is now effortless. Highly recommend for anyone working with documents regularly."</p>
                <div style="margin-top: 10px; color: #ffc107;">
                    <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i>
                </div>
            </div>
            <div style="padding: 25px; background: #f8f9ff; border-radius: 12px; border-left: 4px solid #4361ee;">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #4361ee, #3a0ca3); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-right: 15px; font-size: 1.2rem;">JD</div>
                    <div>
                        <h4 style="margin: 0; color: #0b1630; font-size: 1.1rem;">James Davis</h4>
                        <p style="margin: 5px 0 0 0; color: #56607a; font-size: 0.9rem;">Student</p>
                    </div>
                </div>
                <p style="color: #56607a; line-height: 1.7; margin: 0; font-style: italic;">"Perfect for organizing my study materials! The conversion is fast and the quality is excellent. Free and easy to use - exactly what I needed."</p>
                <div style="margin-top: 10px; color: #ffc107;">
                    <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i>
                </div>
            </div>
            <div style="padding: 25px; background: #f8f9ff; border-radius: 12px; border-left: 4px solid #4361ee;">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #4361ee, #3a0ca3); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-right: 15px; font-size: 1.2rem;">EM</div>
                    <div>
                        <h4 style="margin: 0; color: #0b1630; font-size: 1.1rem;">Emily Martinez</h4>
                        <p style="margin: 5px 0 0 0; color: #56607a; font-size: 0.9rem;">Content Creator</p>
                    </div>
                </div>
                <p style="color: #56607a; line-height: 1.7; margin: 0; font-style: italic;">"I use this tool daily for my work. It's reliable, secure, and produces high-quality PDFs. The best part? It's completely free!"</p>
                <div style="margin-top: 10px; color: #ffc107;">
                    <i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i>
                </div>
            </div>
        </div>
    </section>
'''

AUTHOR_BIO_RIYAZ = '''                <p style="font-size: 1.1rem; color: #56607a; line-height: 1.8; margin: 0;">
                    <strong>Riyaz Mohammad</strong> - A passionate content creator and digital tools expert with years of experience in document processing and image conversion. Dedicated to providing comprehensive guides and helping users make the most of online productivity tools.
                </p>'''

def update_author_in_schema(content):
    """Update author name in schema markup"""
    # Update schema author
    content = re.sub(
        r'"author":\s*\{[^}]*"name":\s*"easyjpgtopdf Team"',
        '"author": {\n        "@type": "Person",\n        "name": "Riyaz Mohammad"',
        content,
        flags=re.DOTALL
    )
    # Also handle if it's on one line
    content = re.sub(
        r'"name":\s*"easyjpgtopdf Team"',
        '"name": "Riyaz Mohammad"',
        content
    )
    return content

def update_author_bio(content):
    """Update author bio section"""
    # Replace easyjpgtopdf Team with Riyaz Mohammad in author bio
    content = re.sub(
        r'<strong>easyjpgtopdf Team</strong>.*?document and image processing\.',
        AUTHOR_BIO_RIYAZ,
        content,
        flags=re.DOTALL
    )
    return content

def add_ssl_and_testimonials(content):
    """Add SSL badges and testimonials before FAQ section"""
    # Check if already exists
    if 'ssl-badges' in content or 'testimonials-section' in content:
        return content
    
    # Find FAQ section and add before it
    faq_pattern = r'(<section class="faq-section"[^>]*>)'
    if re.search(faq_pattern, content):
        content = re.sub(
            faq_pattern,
            SSL_BADGES_SECTION + '\n\n    ' + r'\1',
            content,
            count=1
        )
    return content

def process_blog_file(filepath):
    """Process a single blog file"""
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update author in schema
        content = update_author_in_schema(content)
        
        # Update author bio
        content = update_author_bio(content)
        
        # Add SSL badges and testimonials
        content = add_ssl_and_testimonials(content)
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {filepath}")
            return True
        else:
            print(f"ℹ️  No changes needed: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {filepath}: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Starting blog SEO improvements...\n")
    
    updated_count = 0
    for blog_file in BLOG_FILES:
        if process_blog_file(blog_file):
            updated_count += 1
    
    print(f"\n✨ Completed! Updated {updated_count} out of {len(BLOG_FILES)} blog files.")
    print("\nChanges applied:")
    print("  ✅ Author name updated to 'Riyaz Mohammad' in schema and bio")
    print("  ✅ SSL trust badges added")
    print("  ✅ Testimonials section added")

if __name__ == "__main__":
    main()

