#!/usr/bin/env python3
"""
Comprehensive AdSense Readiness Audit for easyjpgtopdf.com
Checks all aspects that could cause rejection
"""

import os
import re
from collections import defaultdict
from datetime import datetime
import json

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

MAIN_PAGES = ["index.html", "contact.html", "about.html", "blog-articles.html"]
REQUIRED_PAGES = ["privacy-policy.html", "terms-of-service.html", "disclaimer.html", "dmca.html"]

def extract_text_content(html):
    """Extract text content from HTML"""
    # Remove scripts and styles
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def check_content_length(content):
    """Check if content is long enough"""
    text = extract_text_content(content)
    word_count = len(text.split())
    return word_count >= 1500, word_count

def check_ai_content_indicators(content):
    """Check for AI-generated content indicators"""
    ai_indicators = [
        r'\b(?:In conclusion|To summarize|In summary|Furthermore|Moreover|Additionally)\b',
        r'\b(?:comprehensive guide|step-by-step guide|complete guide)\b',
        r'\b(?:essential|crucial|paramount|vital)\b',
        r'\b(?:leverage|utilize|facilitate|implement)\b',
        r'\b(?:seamless|robust|comprehensive|intuitive)\b',
    ]
    
    text = extract_text_content(content).lower()
    matches = []
    for pattern in ai_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(pattern)
    
    return len(matches) > 10, matches[:5]  # More than 10 indicators = likely AI

def check_duplicate_content():
    """Check for duplicate content across pages"""
    content_hashes = defaultdict(list)
    
    for blog_file in BLOG_FILES:
        if not os.path.exists(blog_file):
            continue
        
        with open(blog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract main content (between article tags or main content area)
        article_match = re.search(r'<article[^>]*>(.*?)</article>', content, re.DOTALL | re.IGNORECASE)
        if article_match:
            article_content = article_match.group(1)
            # Get first 500 chars as hash
            text = extract_text_content(article_content)[:500]
            content_hashes[text].append(blog_file)
    
    duplicates = {k: v for k, v in content_hashes.items() if len(v) > 1}
    return duplicates

def check_copyright_issues(content):
    """Check for copyright issues"""
    copyright_issues = []
    
    # Check for copyright notices
    if '©' in content or 'copyright' in content.lower():
        if 'all rights reserved' not in content.lower():
            copyright_issues.append("Missing 'All Rights Reserved'")
    
    # Check for DMCA link
    if 'dmca' not in content.lower() or 'dmca.html' not in content:
        copyright_issues.append("DMCA link missing or incorrect")
    
    return copyright_issues

def check_adsense_requirements():
    """Check AdSense requirements"""
    issues = []
    passed = []
    
    # Check required pages
    for page in REQUIRED_PAGES:
        if os.path.exists(page):
            passed.append(f"✅ {page} exists")
        else:
            issues.append(f"❌ {page} missing")
    
    # Check contact page
    if os.path.exists("contact.html"):
        with open("contact.html", 'r', encoding='utf-8') as f:
            contact_content = f.read()
        if 'contact' in contact_content.lower() and len(contact_content) > 1000:
            passed.append("✅ Contact page has content")
        else:
            issues.append("❌ Contact page insufficient")
    
    # Check about page
    if os.path.exists("about.html"):
        with open("about.html", 'r', encoding='utf-8') as f:
            about_content = f.read()
        if 'about' in about_content.lower() and len(about_content) > 1000:
            passed.append("✅ About page has content")
        else:
            issues.append("❌ About page insufficient")
    
    return issues, passed

def check_seo_elements(content, filepath):
    """Check SEO elements"""
    issues = []
    
    # Check title
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    if not title_match or len(title_match.group(1)) < 30:
        issues.append("Title missing or too short")
    
    # Check meta description
    meta_desc = re.search(r'<meta name="description" content="([^"]*)"', content, re.IGNORECASE)
    if not meta_desc or len(meta_desc.group(1)) < 120:
        issues.append("Meta description missing or too short")
    
    # Check H1
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL | re.IGNORECASE)
    if not h1_match:
        issues.append("H1 tag missing")
    
    # Check schema
    if filepath.startswith("blog-"):
        if '"@type": "BlogPosting"' not in content:
            issues.append("BlogPosting schema missing")
    
    return issues

def check_code_quality(content):
    """Check for code quality issues"""
    issues = []
    
    # Check for broken HTML
    open_tags = len(re.findall(r'<([a-z]+)[^>]*>', content, re.IGNORECASE))
    close_tags = len(re.findall(r'</([a-z]+)>', content, re.IGNORECASE))
    
    # Check for unclosed tags (basic check)
    if abs(open_tags - close_tags) > 50:
        issues.append("Possible unclosed HTML tags")
    
    # Check for inline styles (too many = bad practice)
    inline_styles = len(re.findall(r'style="[^"]*"', content))
    if inline_styles > 100:
        issues.append(f"Too many inline styles ({inline_styles})")
    
    # Check for console errors
    if 'console.error' in content or 'console.warn' in content:
        issues.append("Console errors/warnings in code")
    
    return issues

def check_testimonials_removed(content):
    """Check if testimonials are removed"""
    if 'testimonial' in content.lower() and 'testimonials-section' in content.lower():
        return False, "Testimonials section still present"
    return True, "Testimonials removed"

def audit_blog_pages():
    """Audit all blog pages"""
    results = {
        'content_length': {'passed': 0, 'failed': 0, 'details': []},
        'ai_indicators': {'high': 0, 'low': 0, 'details': []},
        'seo_issues': {'total': 0, 'details': []},
        'code_quality': {'issues': 0, 'details': []},
        'testimonials': {'removed': 0, 'present': 0}
    }
    
    for blog_file in BLOG_FILES:
        if not os.path.exists(blog_file):
            continue
        
        with open(blog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check content length
        is_long_enough, word_count = check_content_length(content)
        if is_long_enough:
            results['content_length']['passed'] += 1
        else:
            results['content_length']['failed'] += 1
            results['content_length']['details'].append(f"{blog_file}: {word_count} words")
        
        # Check AI indicators
        is_ai_likely, indicators = check_ai_content_indicators(content)
        if is_ai_likely:
            results['ai_indicators']['high'] += 1
            results['ai_indicators']['details'].append(f"{blog_file}: High AI indicators")
        else:
            results['ai_indicators']['low'] += 1
        
        # Check SEO
        seo_issues = check_seo_elements(content, blog_file)
        if seo_issues:
            results['seo_issues']['total'] += len(seo_issues)
            results['seo_issues']['details'].extend([f"{blog_file}: {issue}" for issue in seo_issues])
        
        # Check code quality
        code_issues = check_code_quality(content)
        if code_issues:
            results['code_quality']['issues'] += len(code_issues)
            results['code_quality']['details'].extend([f"{blog_file}: {issue}" for issue in code_issues])
        
        # Check testimonials
        testimonials_removed, msg = check_testimonials_removed(content)
        if testimonials_removed:
            results['testimonials']['removed'] += 1
        else:
            results['testimonials']['present'] += 1
    
    return results

def calculate_readiness_score():
    """Calculate overall AdSense readiness score"""
    score = 0
    max_score = 100
    issues = []
    recommendations = []
    
    # 1. Required Pages (20 points)
    required_pages_score = 0
    for page in REQUIRED_PAGES:
        if os.path.exists(page):
            required_pages_score += 5
        else:
            issues.append(f"Missing required page: {page}")
    score += required_pages_score
    
    # 2. Content Quality (30 points)
    blog_results = audit_blog_pages()
    content_score = 0
    
    # Content length (10 points)
    if blog_results['content_length']['passed'] >= 25:
        content_score += 10
    elif blog_results['content_length']['passed'] >= 20:
        content_score += 7
        recommendations.append("Some blog pages need more content (1500+ words)")
    else:
        issues.append("Many blog pages have insufficient content")
    
    # AI Content (10 points)
    if blog_results['ai_indicators']['high'] <= 5:
        content_score += 10
    elif blog_results['ai_indicators']['high'] <= 10:
        content_score += 5
        recommendations.append("Some content may appear AI-generated - add more personal touch")
    else:
        issues.append("High AI content indicators detected")
    
    # Originality (10 points)
    duplicates = check_duplicate_content()
    if len(duplicates) == 0:
        content_score += 10
    elif len(duplicates) <= 2:
        content_score += 7
        recommendations.append("Some duplicate content detected - make each page unique")
    else:
        issues.append(f"Multiple duplicate content blocks found ({len(duplicates)})")
    
    score += content_score
    
    # 3. SEO Elements (20 points)
    seo_score = 0
    if blog_results['seo_issues']['total'] == 0:
        seo_score = 20
    elif blog_results['seo_issues']['total'] <= 10:
        seo_score = 15
        recommendations.append("Some SEO elements need improvement")
    else:
        issues.append("Multiple SEO issues found")
    score += seo_score
    
    # 4. Technical Requirements (15 points)
    tech_score = 0
    adsense_issues, adsense_passed = check_adsense_requirements()
    if len(adsense_issues) == 0:
        tech_score = 15
    elif len(adsense_issues) <= 2:
        tech_score = 10
    else:
        issues.extend(adsense_issues)
    score += tech_score
    
    # 5. Code Quality (10 points)
    code_score = 0
    if blog_results['code_quality']['issues'] == 0:
        code_score = 10
    elif blog_results['code_quality']['issues'] <= 5:
        code_score = 7
        recommendations.append("Some code quality improvements needed")
    else:
        issues.append("Multiple code quality issues")
    score += code_score
    
    # 6. Testimonials Removed (5 points)
    if blog_results['testimonials']['present'] == 0:
        score += 5
    else:
        issues.append("Testimonials still present in some pages")
    
    return score, issues, recommendations, blog_results

def main():
    """Main audit function"""
    print("=" * 80)
    print("COMPREHENSIVE ADSENSE READINESS AUDIT")
    print("Website: easyjpgtopdf.com")
    print("=" * 80)
    print(f"\nAudit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Calculate readiness score
    score, issues, recommendations, blog_results = calculate_readiness_score()
    
    # Display score
    print("=" * 80)
    print("ADSENSE READINESS SCORE")
    print("=" * 80)
    print(f"\n📊 Overall Score: {score}/100 ({score}%)\n")
    
    # Score interpretation
    if score >= 90:
        status = "🟢 EXCELLENT - Ready for AdSense"
    elif score >= 75:
        status = "🟡 GOOD - Minor improvements needed"
    elif score >= 60:
        status = "🟠 FAIR - Several improvements needed"
    else:
        status = "🔴 POOR - Major improvements required"
    
    print(f"Status: {status}\n")
    
    # Detailed results
    print("=" * 80)
    print("DETAILED AUDIT RESULTS")
    print("=" * 80)
    
    # Content Quality
    print("\n📝 CONTENT QUALITY")
    print("-" * 80)
    print(f"✅ Pages with 1500+ words: {blog_results['content_length']['passed']}/28")
    print(f"❌ Pages with <1500 words: {blog_results['content_length']['failed']}/28")
    if blog_results['content_length']['details']:
        print("\n   Pages needing more content:")
        for detail in blog_results['content_length']['details'][:5]:
            print(f"   - {detail}")
    
    print(f"\n🤖 AI CONTENT INDICATORS")
    print(f"   High indicators: {blog_results['ai_indicators']['high']}/28 pages")
    print(f"   Low indicators: {blog_results['ai_indicators']['low']}/28 pages")
    if blog_results['ai_indicators']['high'] > 10:
        print("   ⚠️  WARNING: High AI content indicators detected")
        print("   Recommendation: Add more personal touch, real examples, unique insights")
    
    # Duplicate Content
    print(f"\n🔄 DUPLICATE CONTENT CHECK")
    duplicates = check_duplicate_content()
    if duplicates:
        print(f"   ⚠️  Found {len(duplicates)} duplicate content blocks")
        for content_hash, files in list(duplicates.items())[:3]:
            print(f"   - Duplicate in {len(files)} files: {', '.join(files[:3])}")
    else:
        print("   ✅ No duplicate content found")
    
    # SEO Issues
    print(f"\n🔍 SEO ELEMENTS")
    print(f"   Total SEO issues: {blog_results['seo_issues']['total']}")
    if blog_results['seo_issues']['details']:
        print("   Issues found:")
        for detail in blog_results['seo_issues']['details'][:10]:
            print(f"   - {detail}")
    else:
        print("   ✅ All SEO elements in place")
    
    # Code Quality
    print(f"\n💻 CODE QUALITY")
    print(f"   Total issues: {blog_results['code_quality']['issues']}")
    if blog_results['code_quality']['details']:
        print("   Issues found:")
        for detail in blog_results['code_quality']['details'][:5]:
            print(f"   - {detail}")
    else:
        print("   ✅ Code quality is good")
    
    # Testimonials
    print(f"\n💬 TESTIMONIALS")
    print(f"   ✅ Removed from: {blog_results['testimonials']['removed']}/28 pages")
    print(f"   ❌ Still present in: {blog_results['testimonials']['present']}/28 pages")
    
    # AdSense Requirements
    print(f"\n📋 ADSENSE REQUIREMENTS")
    adsense_issues, adsense_passed = check_adsense_requirements()
    for item in adsense_passed:
        print(f"   {item}")
    for item in adsense_issues:
        print(f"   {item}")
    
    # Issues Summary
    print("\n" + "=" * 80)
    print("ISSUES THAT COULD CAUSE REJECTION")
    print("=" * 80)
    
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    else:
        print("✅ No critical issues found!")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("✅ All recommendations implemented!")
    
    # Risk Assessment
    print("\n" + "=" * 80)
    print("RISK ASSESSMENT")
    print("=" * 80)
    
    risks = []
    
    if blog_results['ai_indicators']['high'] > 15:
        risks.append("🔴 HIGH RISK: Too many AI content indicators - Google may detect AI-generated content")
    
    if len(duplicates) > 3:
        risks.append("🔴 HIGH RISK: Multiple duplicate content blocks - May be flagged as low-quality")
    
    if blog_results['content_length']['failed'] > 10:
        risks.append("🟠 MEDIUM RISK: Many pages have insufficient content - Need 1500+ words")
    
    if blog_results['testimonials']['present'] > 0:
        risks.append("🟠 MEDIUM RISK: Testimonials still present - May look fake to AdSense")
    
    if len(adsense_issues) > 0:
        risks.append("🟠 MEDIUM RISK: Missing required pages for AdSense compliance")
    
    if not risks:
        risks.append("🟢 LOW RISK: Website appears ready for AdSense approval")
    
    for risk in risks:
        print(f"   {risk}")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"\nReadiness Score: {score}/100 ({score}%)")
    print(f"Status: {status}")
    print(f"\nCritical Issues: {len(issues)}")
    print(f"Recommendations: {len(recommendations)}")
    print(f"Risk Level: {'HIGH' if score < 60 else 'MEDIUM' if score < 75 else 'LOW'}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    
    if score >= 90:
        print("✅ Website is ready for AdSense application!")
        print("   - Submit application")
        print("   - Wait for review (usually 1-2 weeks)")
    elif score >= 75:
        print("⚠️  Address minor issues before applying:")
        for issue in issues[:3]:
            print(f"   - {issue}")
    else:
        print("❌ Address critical issues before applying:")
        for issue in issues[:5]:
            print(f"   - {issue}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

