#!/usr/bin/env python3
"""
Comprehensive verification and fix script for all AdSense & SEO requirements
Checks and fixes all missing elements across the website
"""

import os
import re
from datetime import datetime

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

MAIN_PAGES = [
    "index.html",
    "contact.html",
    "about.html",
    "blog-articles.html"
]

def check_and_fix_schema(content, filepath):
    """Check and fix schema markup - change Article to BlogPosting for blog pages"""
    if not filepath.startswith("blog-"):
        return content, False
    
    # Check if schema exists
    if '"@type": "Article"' in content:
        # Replace Article with BlogPosting
        content = content.replace('"@type": "Article"', '"@type": "BlogPosting"')
        return content, True
    elif '"@type": "BlogPosting"' in content:
        return content, False  # Already correct
    
    return content, False

def check_and_fix_dmca_link(content):
    """Fix DMCA link in footer"""
    if 'href="dmca-en.html"' in content:
        content = content.replace('href="dmca-en.html"', 'href="dmca.html"')
        return content, True
    return content, False

def check_author_info(content):
    """Check if author info is present"""
    return "Riyaz Mohammad" in content and "Author:" in content

def check_related_posts(content):
    """Check if related posts section exists"""
    return "related-posts" in content or "Related Articles" in content

def check_ssl_badges(content):
    """Check if SSL badges are present"""
    return "ssl-badges" in content or "SSL A+ Rating" in content

def check_testimonials(content):
    """Check if testimonials section exists"""
    return "testimonials-section" in content or "What Our Users Say" in content

def check_h1_tag(content):
    """Check if H1 tag exists"""
    h1_pattern = r'<h1[^>]*>.*?</h1>'
    return bool(re.search(h1_pattern, content, re.DOTALL | re.IGNORECASE))

def check_meta_tags(content):
    """Check if meta tags are present"""
    has_title = '<meta name="title"' in content or '<title>' in content
    has_description = '<meta name="description"' in content
    return has_title and has_description

def check_alt_tags(content):
    """Check if images have ALT tags"""
    img_pattern = r'<img[^>]*>'
    imgs = re.findall(img_pattern, content, re.IGNORECASE)
    if not imgs:
        return True  # No images, so it's fine
    
    for img in imgs:
        if 'alt=' not in img.lower() and 'alt =' not in img.lower():
            return False
    return True

def verify_blog_page(filepath):
    """Verify a blog page has all required elements"""
    if not os.path.exists(filepath):
        return {"exists": False}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    fixes_applied = []
    
    # Check schema
    content, schema_fixed = check_and_fix_schema(content, filepath)
    if schema_fixed:
        fixes_applied.append("Schema changed from Article to BlogPosting")
    elif '"@type": "BlogPosting"' not in content:
        issues.append("Missing BlogPosting schema")
    
    # Check author
    if not check_author_info(content):
        issues.append("Missing author info (Riyaz Mohammad)")
    
    # Check related posts
    if not check_related_posts(content):
        issues.append("Missing related posts section")
    
    # Check SSL badges
    if not check_ssl_badges(content):
        issues.append("Missing SSL badges")
    
    # Check testimonials
    if not check_testimonials(content):
        issues.append("Missing testimonials section")
    
    # Check H1
    if not check_h1_tag(content):
        issues.append("Missing H1 tag")
    
    # Check meta tags
    if not check_meta_tags(content):
        issues.append("Missing meta tags")
    
    # Check ALT tags
    if not check_alt_tags(content):
        issues.append("Some images missing ALT tags")
    
    # Fix DMCA link
    content, dmca_fixed = check_and_fix_dmca_link(content)
    if dmca_fixed:
        fixes_applied.append("DMCA link fixed")
    
    # Write back if fixes were applied
    if fixes_applied:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return {
        "exists": True,
        "issues": issues,
        "fixes_applied": fixes_applied
    }

def verify_main_page(filepath):
    """Verify a main page has all required elements"""
    if not os.path.exists(filepath):
        return {"exists": False}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    fixes_applied = []
    
    # Check H1
    if not check_h1_tag(content):
        issues.append("Missing H1 tag")
    
    # Check meta tags
    if not check_meta_tags(content):
        issues.append("Missing meta tags")
    
    # Check ALT tags
    if not check_alt_tags(content):
        issues.append("Some images missing ALT tags")
    
    # Fix DMCA link
    content, dmca_fixed = check_and_fix_dmca_link(content)
    if dmca_fixed:
        fixes_applied.append("DMCA link fixed")
    
    # For contact and about pages, check for enhanced content
    if "contact.html" in filepath:
        if "Contact Us" not in content or len(content) < 5000:
            issues.append("Contact page may need enhancement")
    
    if "about.html" in filepath:
        if "About Us" not in content or "mission" not in content.lower():
            issues.append("About page may need enhancement")
    
    # Write back if fixes were applied
    if fixes_applied:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return {
        "exists": True,
        "issues": issues,
        "fixes_applied": fixes_applied
    }

def main():
    """Main verification function"""
    print("=" * 80)
    print("COMPREHENSIVE ADSENSE & SEO VERIFICATION")
    print("=" * 80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Verify blog pages
    print("📝 VERIFYING BLOG PAGES (28 pages)")
    print("-" * 80)
    blog_issues_count = 0
    blog_fixes_count = 0
    
    for blog_file in BLOG_FILES:
        result = verify_blog_page(blog_file)
        if not result["exists"]:
            print(f"❌ {blog_file}: FILE NOT FOUND")
            continue
        
        if result["issues"]:
            print(f"⚠️  {blog_file}:")
            for issue in result["issues"]:
                print(f"   - {issue}")
                blog_issues_count += 1
        else:
            print(f"✅ {blog_file}: All checks passed")
        
        if result["fixes_applied"]:
            for fix in result["fixes_applied"]:
                print(f"   🔧 Fixed: {fix}")
                blog_fixes_count += 1
    
    print(f"\n📊 Blog Pages Summary:")
    print(f"   - Issues found: {blog_issues_count}")
    print(f"   - Fixes applied: {blog_fixes_count}")
    
    # Verify main pages
    print("\n\n🌐 VERIFYING MAIN PAGES")
    print("-" * 80)
    main_issues_count = 0
    main_fixes_count = 0
    
    for main_file in MAIN_PAGES:
        result = verify_main_page(main_file)
        if not result["exists"]:
            print(f"❌ {main_file}: FILE NOT FOUND")
            continue
        
        if result["issues"]:
            print(f"⚠️  {main_file}:")
            for issue in result["issues"]:
                print(f"   - {issue}")
                main_issues_count += 1
        else:
            print(f"✅ {main_file}: All checks passed")
        
        if result["fixes_applied"]:
            for fix in result["fixes_applied"]:
                print(f"   🔧 Fixed: {fix}")
                main_fixes_count += 1
    
    print(f"\n📊 Main Pages Summary:")
    print(f"   - Issues found: {main_issues_count}")
    print(f"   - Fixes applied: {main_fixes_count}")
    
    # Check robots.txt and sitemap.xml
    print("\n\n📄 VERIFYING TECHNICAL FILES")
    print("-" * 80)
    
    if os.path.exists("robots.txt"):
        print("✅ robots.txt: EXISTS")
    else:
        print("❌ robots.txt: MISSING")
    
    if os.path.exists("sitemap.xml"):
        print("✅ sitemap.xml: EXISTS")
        # Check if all blog pages are in sitemap
        with open("sitemap.xml", 'r', encoding='utf-8') as f:
            sitemap_content = f.read()
        missing_in_sitemap = []
        for blog_file in BLOG_FILES:
            if blog_file.replace('.html', '') not in sitemap_content:
                missing_in_sitemap.append(blog_file)
        if missing_in_sitemap:
            print(f"⚠️  Missing from sitemap: {len(missing_in_sitemap)} pages")
        else:
            print("✅ All blog pages in sitemap")
    else:
        print("❌ sitemap.xml: MISSING")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    total_issues = blog_issues_count + main_issues_count
    total_fixes = blog_fixes_count + main_fixes_count
    
    print(f"Total Issues Found: {total_issues}")
    print(f"Total Fixes Applied: {total_fixes}")
    
    if total_issues == 0:
        print("\n🎉 ALL CHECKS PASSED! Website is fully compliant.")
    else:
        print(f"\n⚠️  {total_issues} issue(s) need attention.")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()

