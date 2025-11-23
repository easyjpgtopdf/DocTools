#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create SVG placeholders and image structure for blogs
Since we can't create actual GIF/PNG files, we'll create:
1. SVG graphics (code-based, can be created)
2. Proper image tag structure with placeholders
3. CSS-based visual elements
"""

import os

# Blog to icon mapping
BLOG_ICONS = {
    "blog-how-to-use-jpg-to-pdf.html": "fa-file-image",
    "blog-how-to-use-word-to-pdf.html": "fa-file-word",
    "blog-how-to-use-excel-to-pdf.html": "fa-file-excel",
    "blog-how-to-use-ppt-to-pdf.html": "fa-file-powerpoint",
    "blog-why-user-pdf-to-word.html": "fa-file-word",
    "blog-why-user-pdf-to-excel.html": "fa-file-excel",
    "blog-why-user-pdf-to-ppt.html": "fa-file-powerpoint",
    "blog-why-user-pdf-to-jpg.html": "fa-image",
    "blog-how-to-merge-pdf.html": "fa-object-group",
    "blog-how-to-split-pdf.html": "fa-cut",
    "blog-how-to-compress-pdf.html": "fa-compress-alt",
    "blog-how-to-compress-image.html": "fa-compress",
    "blog-how-to-edit-pdf.html": "fa-edit",
    "blog-how-to-edit-image.html": "fa-paint-brush",
    "blog-how-to-protect-pdf.html": "fa-lock",
    "blog-how-to-protect-excel.html": "fa-lock",
    "blog-how-to-unlock-pdf.html": "fa-unlock",
    "blog-how-to-watermark-pdf.html": "fa-tint",
    "blog-how-to-watermark-image.html": "fa-tint",
    "blog-how-to-crop-pdf.html": "fa-crop-alt",
    "blog-how-to-add-page-numbers.html": "fa-sort-numeric-up",
    "blog-how-to-resize-image.html": "fa-expand-arrows-alt",
    "blog-how-to-remove-background.html": "fa-magic",
    "blog-how-to-ocr-image.html": "fa-eye",
    "blog-how-to-make-resume.html": "fa-file-alt",
    "blog-how-to-make-biodata.html": "fa-id-card",
    "blog-how-to-make-marriage-card.html": "fa-envelope",
    "blog-how-to-generate-ai-image.html": "fa-robot",
}

def create_svg_placeholder(title, icon_class):
    """Create SVG placeholder image"""
    svg = f'''<svg width="400" height="250" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4361ee;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#3a0ca3;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="400" height="250" fill="url(#grad)"/>
  <text x="200" y="120" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="white" text-anchor="middle">{title}</text>
  <text x="200" y="150" font-family="Arial, sans-serif" font-size="14" fill="rgba(255,255,255,0.9)" text-anchor="middle">easyjpgtopdf.com</text>
</svg>'''
    return svg

def add_featured_images_to_blog_articles():
    """Add featured image structure to blog-articles.html"""
    if not os.path.exists("blog-articles.html"):
        return
    
    with open("blog-articles.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find article items and add featured image structure
    # Pattern: article-item with h3 and p
    pattern = r'(<div class="article-item"[^>]*>)\s*(<h3[^>]*>.*?</h3>)'
    
    def add_image(match):
        item_start = match.group(1)
        h3_tag = match.group(2)
        
        # Extract href to determine icon
        href_match = re.search(r'href="([^"]+)"', h3_tag)
        if href_match:
            blog_file = href_match.group(1)
            icon = BLOG_ICONS.get(blog_file, "fa-file")
            
            # Create featured image div with Font Awesome icon as placeholder
            image_html = f'''
                        <div class="article-featured-image" style="width: 100%; height: 180px; background: linear-gradient(135deg, #4361ee, #3a0ca3); border-radius: 8px; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; color: white; font-size: 3rem; overflow: hidden;">
                            <i class="fas {icon}"></i>
                        </div>
            '''
            return item_start + image_html + "\n                        " + h3_tag
        return match.group(0)
    
    import re
    content = re.sub(pattern, add_image, content, flags=re.DOTALL)
    
    with open("blog-articles.html", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Added featured image placeholders to blog-articles.html")

def create_svg_images_directory():
    """Create SVG images for blog posts"""
    if not os.path.exists("images/blog-featured"):
        os.makedirs("images/blog-featured")
    
    for blog_file, icon in BLOG_ICONS.items():
        blog_name = blog_file.replace("blog-", "").replace(".html", "").replace("-", " ").title()
        svg_content = create_svg_placeholder(blog_name, icon)
        
        svg_file = f"images/blog-featured/{blog_file.replace('.html', '.svg')}"
        with open(svg_file, "w", encoding="utf-8") as f:
            f.write(svg_content)
        
        print(f"   ✅ Created {svg_file}")
    
    print(f"\n✅ Created {len(BLOG_ICONS)} SVG placeholder images")

def main():
    print("🎨 Creating image placeholders and structure...\n")
    
    print("1. Creating SVG placeholder images...")
    create_svg_images_directory()
    
    print("\n2. Adding featured image structure to blog-articles.html...")
    add_featured_images_to_blog_articles()
    
    print("\n✅ Image placeholders created!")
    print("\n📝 Note:")
    print("   - SVG images are created (code-based, work immediately)")
    print("   - Featured image structure added to blog-articles.html")
    print("   - For actual GIF/PNG images, you'll need to:")
    print("     * Create them using image editing software")
    print("     * Or use online tools like Canva, Figma")
    print("     * Or hire a designer")
    print("   - SVG placeholders will work until real images are added")

if __name__ == "__main__":
    import re
    main()

