#!/usr/bin/env python3
"""
Comprehensive Coding Issues Check for All HTML Pages
Checks for:
1. HTML syntax errors (unclosed tags)
2. Duplicate footers/headers
3. Missing closing tags
4. Encoding issues
5. Common errors
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Files to exclude
EXCLUDE_PATTERNS = [
    'backups',
    'node_modules',
    '__pycache__',
    '.git',
    '.venv',
    'venv',
    'server/public/backups',
]

def should_exclude_file(file_path):
    """Check if file should be excluded"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def check_unclosed_tags(content):
    """Check for unclosed HTML tags"""
    issues = []
    
    # Self-closing tags that don't need closing
    self_closing = ['img', 'br', 'hr', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr']
    
    # Find all opening tags
    opening_tags = re.findall(r'<(\w+)[^>]*>', content)
    # Find all closing tags
    closing_tags = re.findall(r'</(\w+)>', content)
    
    # Count occurrences
    opening_count = defaultdict(int)
    closing_count = defaultdict(int)
    
    for tag in opening_tags:
        if tag.lower() not in self_closing:
            opening_count[tag.lower()] += 1
    
    for tag in closing_tags:
        closing_count[tag.lower()] += 1
    
    # Check for mismatches
    all_tags = set(list(opening_count.keys()) + list(closing_count.keys()))
    for tag in all_tags:
        if opening_count[tag] != closing_count[tag]:
            diff = opening_count[tag] - closing_count[tag]
            if diff > 0:
                issues.append(f"⚠️  Unclosed <{tag}> tag ({diff} missing closing)")
            elif diff < 0:
                issues.append(f"⚠️  Extra closing </{tag}> tag ({abs(diff)} extra)")
    
    return issues

def check_duplicate_footers(content):
    """Check for duplicate footer tags"""
    footer_count = len(re.findall(r'<footer[^>]*>', content, re.IGNORECASE))
    if footer_count > 1:
        return [f"❌ Duplicate footers found ({footer_count} footer tags)"]
    return []

def check_duplicate_headers(content):
    """Check for duplicate header tags"""
    header_count = len(re.findall(r'<header[^>]*>', content, re.IGNORECASE))
    if header_count > 1:
        return [f"⚠️  Duplicate headers found ({header_count} header tags)"]
    return []

def check_missing_body_tags(content):
    """Check for missing body tags"""
    has_body = re.search(r'<body[^>]*>', content, re.IGNORECASE)
    has_closing_body = re.search(r'</body>', content, re.IGNORECASE)
    
    issues = []
    if not has_body:
        issues.append("❌ Missing <body> tag")
    if not has_closing_body:
        issues.append("❌ Missing </body> tag")
    return issues

def check_missing_html_tags(content):
    """Check for missing HTML tags"""
    has_html = re.search(r'<html[^>]*>', content, re.IGNORECASE)
    has_closing_html = re.search(r'</html>', content, re.IGNORECASE)
    
    issues = []
    if not has_html:
        issues.append("⚠️  Missing <html> tag")
    if not has_closing_html:
        issues.append("⚠️  Missing </html> tag")
    return issues

def check_script_tags(content):
    """Check for unclosed script tags"""
    script_open = len(re.findall(r'<script[^>]*>', content, re.IGNORECASE))
    script_close = len(re.findall(r'</script>', content, re.IGNORECASE))
    
    if script_open != script_close:
        return [f"⚠️  Unclosed <script> tags ({script_open} opening, {script_close} closing)"]
    return []

def check_style_tags(content):
    """Check for unclosed style tags"""
    style_open = len(re.findall(r'<style[^>]*>', content, re.IGNORECASE))
    style_close = len(re.findall(r'</style>', content, re.IGNORECASE))
    
    if style_open != style_close:
        return [f"⚠️  Unclosed <style> tags ({style_open} opening, {style_close} closing)"]
    return []

def check_common_errors(content):
    """Check for common coding errors"""
    issues = []
    
    # Check for double </footer>
    if content.count('</footer></footer>') > 0:
        issues.append("❌ Double closing footer tag found")
    
    # Check for footer inside footer
    if re.search(r'<footer[^>]*>.*<footer[^>]*>', content, re.IGNORECASE | re.DOTALL):
        issues.append("❌ Footer nested inside footer")
    
    # Check for broken HTML entities
    if re.search(r'&[^#\w]', content):
        issues.append("⚠️  Possible broken HTML entities")
    
    # Check for unclosed div tags (basic check)
    div_open = len(re.findall(r'<div[^>]*>', content, re.IGNORECASE))
    div_close = len(re.findall(r'</div>', content, re.IGNORECASE))
    if abs(div_open - div_close) > 5:  # Allow some tolerance
        issues.append(f"⚠️  Div tag mismatch ({div_open} opening, {div_close} closing, diff: {div_open - div_close})")
    
    return issues

def check_encoding_issues(file_path, content):
    """Check for encoding issues"""
    issues = []
    
    # Check for common encoding problems
    if '\ufffd' in content:
        issues.append("⚠️  Encoding issues detected (replacement character found)")
    
    # Check for mojibake patterns
    if re.search(r'â€™|ÃƒÆ|â€œ|â€|Â', content):
        issues.append("⚠️  Possible encoding/mojibake issues detected")
    
    return issues

def analyze_file(file_path):
    """Analyze a single file for issues"""
    try:
        # Try UTF-8 first
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            # Try other encodings
            for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    encoding = enc
                    break
                except:
                    continue
            else:
                return {
                    'file': file_path,
                    'errors': ["❌ Cannot read file encoding"],
                    'encoding': 'unknown'
                }
        
        all_issues = []
        
        # Run all checks
        all_issues.extend(check_unclosed_tags(content))
        all_issues.extend(check_duplicate_footers(content))
        all_issues.extend(check_duplicate_headers(content))
        all_issues.extend(check_missing_body_tags(content))
        all_issues.extend(check_missing_html_tags(content))
        all_issues.extend(check_script_tags(content))
        all_issues.extend(check_style_tags(content))
        all_issues.extend(check_common_errors(content))
        all_issues.extend(check_encoding_issues(file_path, content))
        
        return {
            'file': file_path,
            'issues': all_issues,
            'encoding': encoding,
            'has_issues': len(all_issues) > 0
        }
        
    except Exception as e:
        return {
            'file': file_path,
            'errors': [f"❌ Error analyzing file: {str(e)}"],
            'encoding': 'unknown',
            'has_issues': True
        }

def main():
    """Main function"""
    base_dir = Path(__file__).parent
    
    # Get all HTML files
    html_files = list(base_dir.rglob('*.html'))
    html_files = [f for f in html_files if not should_exclude_file(f)]
    
    print(f"🔍 Checking {len(html_files)} HTML files for coding issues...\n")
    print("="*80)
    
    files_with_issues = []
    files_clean = []
    total_issues = 0
    
    for file_path in sorted(html_files):
        relative_path = file_path.relative_to(base_dir)
        result = analyze_file(file_path)
        
        if result.get('has_issues', False) or result.get('errors'):
            issues = result.get('issues', []) + result.get('errors', [])
            if issues:
                files_with_issues.append((relative_path, issues))
                total_issues += len(issues)
        else:
            files_clean.append(relative_path)
    
    # Print results
    print("\n📊 CODING ISSUES REPORT\n")
    print("="*80)
    
    if files_clean:
        print(f"\n✅ CLEAN FILES ({len(files_clean)} files):")
        for f in files_clean[:10]:  # Show first 10
            print(f"   ✓ {f}")
        if len(files_clean) > 10:
            print(f"   ... and {len(files_clean) - 10} more clean files")
    
    if files_with_issues:
        print(f"\n⚠️  FILES WITH ISSUES ({len(files_with_issues)} files, {total_issues} total issues):\n")
        for file_path, issues in files_with_issues:
            print(f"   📄 {file_path}")
            for issue in issues:
                print(f"      {issue}")
            print()
    else:
        print("\n✅ No coding issues found! All files are clean.\n")
    
    print("="*80)
    print(f"\n📈 SUMMARY:")
    print(f"   ✅ Clean files: {len(files_clean)}")
    print(f"   ⚠️  Files with issues: {len(files_with_issues)}")
    print(f"   📊 Total issues found: {total_issues}")
    print("="*80)
    
    if files_with_issues:
        print(f"\n💡 Next steps:")
        print(f"   1. Review the issues above")
        print(f"   2. Fix critical issues (marked with ❌)")
        print(f"   3. Review warnings (marked with ⚠️)")
        print(f"   4. Re-run this script to verify fixes")

if __name__ == '__main__':
    main()

