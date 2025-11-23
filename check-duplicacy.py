#!/usr/bin/env python3
"""
Check for duplicacy across all pages - duplicate content, sections, schema, etc.
"""

import os
import re
from collections import defaultdict

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

def extract_schema(content):
    """Extract schema markup"""
    schema_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
    if schema_match:
        return schema_match.group(1).strip()
    return None

def extract_ssl_badges(content):
    """Extract SSL badges section"""
    ssl_match = re.search(r'<!-- SSL Trust Badges Section -->(.*?)</section>', content, re.DOTALL)
    if ssl_match:
        return ssl_match.group(1).strip()[:200]  # First 200 chars
    return None

def extract_testimonials(content):
    """Extract testimonials section"""
    testimonial_match = re.search(r'<!-- Testimonials Section -->(.*?)</section>', content, re.DOTALL)
    if testimonial_match:
        return testimonial_match.group(1).strip()[:200]  # First 200 chars
    return None

def extract_related_posts(content):
    """Extract related posts section"""
    related_match = re.search(r'<section class="related-posts"(.*?)</section>', content, re.DOTALL)
    if related_match:
        return related_match.group(1).strip()[:200]  # First 200 chars
    return None

def extract_h1(content):
    """Extract H1 tag content"""
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    if h1_match:
        return h1_match.group(1).strip()
    return None

def extract_meta_description(content):
    """Extract meta description"""
    meta_match = re.search(r'<meta name="description" content="([^"]*)"', content)
    if meta_match:
        return meta_match.group(1)
    return None

def extract_title(content):
    """Extract page title"""
    title_match = re.search(r'<title>(.*?)</title>', content)
    if title_match:
        return title_match.group(1)
    return None

def check_duplicates():
    """Check for duplicates across all pages"""
    print("=" * 80)
    print("DUPLICACY CHECK - Checking for duplicate content, sections, and code")
    print("=" * 80)
    print()
    
    issues = []
    schema_contents = defaultdict(list)
    ssl_contents = defaultdict(list)
    testimonial_contents = defaultdict(list)
    h1_contents = defaultdict(list)
    meta_descriptions = defaultdict(list)
    titles = defaultdict(list)
    
    # Collect all content
    for blog_file in BLOG_FILES:
        if not os.path.exists(blog_file):
            continue
        
        with open(blog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check schema
        schema = extract_schema(content)
        if schema:
            schema_contents[schema].append(blog_file)
        
        # Check SSL badges
        ssl = extract_ssl_badges(content)
        if ssl:
            ssl_contents[ssl].append(blog_file)
        
        # Check testimonials
        testimonial = extract_testimonials(content)
        if testimonial:
            testimonial_contents[testimonial].append(blog_file)
        
        # Check H1
        h1 = extract_h1(content)
        if h1:
            h1_contents[h1].append(blog_file)
        
        # Check meta description
        meta_desc = extract_meta_description(content)
        if meta_desc:
            meta_descriptions[meta_desc].append(blog_file)
        
        # Check title
        title = extract_title(content)
        if title:
            titles[title].append(blog_file)
    
    # Report duplicates
    print("📋 CHECKING FOR DUPLICATES\n")
    
    # Schema duplicates
    schema_duplicates = {k: v for k, v in schema_contents.items() if len(v) > 1}
    if schema_duplicates:
        print("⚠️  SCHEMA MARKUP DUPLICATES FOUND:")
        for schema, files in schema_duplicates.items():
            print(f"   Found in {len(files)} files:")
            for f in files:
                print(f"      - {f}")
        print()
        issues.append(f"Schema duplicates: {len(schema_duplicates)}")
    else:
        print("✅ Schema markup: No duplicates (each page has unique schema)")
        print()
    
    # SSL badges duplicates (should be same across all - this is OK)
    ssl_duplicates = {k: v for k, v in ssl_contents.items() if len(v) > 1}
    if ssl_duplicates:
        print("ℹ️  SSL BADGES: Same across all pages (This is OK - standard trust badges)")
        print(f"   Found in {len(ssl_duplicates)} unique variations across {sum(len(v) for v in ssl_duplicates.values())} pages")
        print()
    
    # Testimonials duplicates (should be same across all - this is OK)
    testimonial_duplicates = {k: v for k, v in testimonial_contents.items() if len(v) > 1}
    if testimonial_duplicates:
        print("ℹ️  TESTIMONIALS: Same across all pages (This is OK - standard social proof)")
        print(f"   Found in {len(testimonial_duplicates)} unique variations across {sum(len(v) for v in testimonial_duplicates.values())} pages")
        print()
    
    # H1 duplicates (should be unique)
    h1_duplicates = {k: v for k, v in h1_contents.items() if len(v) > 1}
    if h1_duplicates:
        print("⚠️  H1 TAG DUPLICATES FOUND:")
        for h1, files in h1_duplicates.items():
            print(f"   '{h1[:60]}...' found in {len(files)} files:")
            for f in files:
                print(f"      - {f}")
        print()
        issues.append(f"H1 duplicates: {len(h1_duplicates)}")
    else:
        print("✅ H1 tags: All unique")
        print()
    
    # Meta description duplicates (should be unique)
    meta_duplicates = {k: v for k, v in meta_descriptions.items() if len(v) > 1}
    if meta_duplicates:
        print("⚠️  META DESCRIPTION DUPLICATES FOUND:")
        for desc, files in meta_duplicates.items():
            print(f"   '{desc[:60]}...' found in {len(files)} files:")
            for f in files:
                print(f"      - {f}")
        print()
        issues.append(f"Meta description duplicates: {len(meta_duplicates)}")
    else:
        print("✅ Meta descriptions: All unique")
        print()
    
    # Title duplicates (should be unique)
    title_duplicates = {k: v for k, v in titles.items() if len(v) > 1}
    if title_duplicates:
        print("⚠️  TITLE DUPLICATES FOUND:")
        for title, files in title_duplicates.items():
            print(f"   '{title}' found in {len(files)} files:")
            for f in files:
                print(f"      - {f}")
        print()
        issues.append(f"Title duplicates: {len(title_duplicates)}")
    else:
        print("✅ Titles: All unique")
        print()
    
    # Check for duplicate sections within same file
    print("📄 CHECKING FOR DUPLICATE SECTIONS WITHIN FILES\n")
    duplicate_sections = []
    for blog_file in BLOG_FILES:
        if not os.path.exists(blog_file):
            continue
        
        with open(blog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for multiple SSL badge sections
        ssl_count = content.count('<!-- SSL Trust Badges Section -->')
        if ssl_count > 1:
            duplicate_sections.append(f"{blog_file}: {ssl_count} SSL badge sections")
        
        # Check for multiple testimonial sections
        testimonial_count = content.count('<!-- Testimonials Section -->')
        if testimonial_count > 1:
            duplicate_sections.append(f"{blog_file}: {testimonial_count} Testimonial sections")
        
        # Check for multiple related posts sections
        related_count = content.count('class="related-posts"')
        if related_count > 1:
            duplicate_sections.append(f"{blog_file}: {related_count} Related posts sections")
        
        # Check for multiple schema blocks
        schema_count = content.count('type="application/ld+json"')
        if schema_count > 1:
            duplicate_sections.append(f"{blog_file}: {schema_count} Schema blocks")
        
        # Check for multiple H1 tags
        h1_count = len(re.findall(r'<h1[^>]*>', content))
        if h1_count > 1:
            duplicate_sections.append(f"{blog_file}: {h1_count} H1 tags")
    
    if duplicate_sections:
        print("⚠️  DUPLICATE SECTIONS WITHIN FILES FOUND:")
        for issue in duplicate_sections:
            print(f"   - {issue}")
        print()
        issues.append(f"Duplicate sections: {len(duplicate_sections)}")
    else:
        print("✅ No duplicate sections within files")
        print()
    
    # Final summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if issues:
        print(f"⚠️  Found {len(issues)} type(s) of duplicacy issues:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ NO DUPLICACY FOUND!")
        print()
        print("All pages have:")
        print("   ✅ Unique H1 tags")
        print("   ✅ Unique meta descriptions")
        print("   ✅ Unique titles")
        print("   ✅ Unique schema markup")
        print("   ✅ No duplicate sections within files")
        print()
        print("Standard elements (same across pages - this is OK):")
        print("   ✅ SSL badges (standard trust signals)")
        print("   ✅ Testimonials (standard social proof)")
    
    print("=" * 80)
    
    return len(issues) == 0

if __name__ == "__main__":
    check_duplicates()

