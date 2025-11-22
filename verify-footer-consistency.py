#!/usr/bin/env python3
"""
Verify that all footers are consistent and there are no duplicates
"""

import re
from pathlib import Path

# Index.html footer signature (key parts)
FOOTER_SIGNATURE = [
    'footer-company-links',
    'pricing.html',
    'dmca-en.html',
    'blog.html',
    'All rights reserved',
    'See full acknowledgements',
]

# Files to exclude
EXCLUDE_PATTERNS = [
    'backups',
    'node_modules',
    '__pycache__',
    '.git',
]

def should_exclude_file(file_path):
    """Check if file should be excluded"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def count_footers(content):
    """Count footer tags in content"""
    footer_matches = re.findall(r'<footer[^>]*>', content, re.IGNORECASE)
    return len(footer_matches)

def check_footer_consistency(content):
    """Check if footer matches index.html footer"""
    # Check for key elements
    checks = {
        'has_company_links': 'footer-company-links' in content,
        'has_pricing': 'pricing.html' in content or 'Pricing' in content,
        'has_dmca': 'dmca-en.html' in content or 'DMCA' in content,
        'has_blog': 'blog.html' in content,
        'has_rights': 'All rights reserved' in content or 'all rights reserved' in content,
        'has_attributions': 'attributions.html' in content or 'acknowledgements' in content.lower(),
    }
    
    # Count footer tags
    footer_count = count_footers(content)
    
    return checks, footer_count

def main():
    """Main function"""
    base_dir = Path(__file__).parent
    
    # Get all HTML files
    html_files = list(base_dir.rglob('*.html'))
    html_files = [f for f in html_files if not should_exclude_file(f)]
    
    print(f"🔍 Checking {len(html_files)} files for footer consistency...\n")
    
    issues = []
    consistent_files = []
    
    for file_path in sorted(html_files):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            relative_path = file_path.relative_to(base_dir)
            checks, footer_count = check_footer_consistency(content)
            
            # Check for issues
            file_issues = []
            
            # Check for multiple footers
            if footer_count > 1:
                file_issues.append(f"⚠️  Multiple footers found ({footer_count})")
            
            if footer_count == 0:
                file_issues.append("❌ No footer found")
            elif not all(checks.values()):
                missing = [k for k, v in checks.items() if not v]
                file_issues.append(f"⚠️  Missing elements: {', '.join(missing)}")
            
            if file_issues:
                issues.append((relative_path, file_issues))
            else:
                consistent_files.append(relative_path)
                
        except Exception as e:
            issues.append((file_path.relative_to(base_dir), [f"❌ Error reading file: {e}"]))
    
    # Print results
    print(f"{'='*70}")
    print(f"📊 Footer Consistency Report")
    print(f"{'='*70}\n")
    
    if consistent_files:
        print(f"✅ Consistent Files ({len(consistent_files)}):")
        for f in consistent_files[:5]:  # Show first 5
            print(f"   ✓ {f}")
        if len(consistent_files) > 5:
            print(f"   ... and {len(consistent_files) - 5} more")
        print()
    
    if issues:
        print(f"⚠️  Files with Issues ({len(issues)}):")
        for file_path, file_issues in issues:
            print(f"\n   📄 {file_path}")
            for issue in file_issues:
                print(f"      {issue}")
        print()
    else:
        print("✅ All files have consistent footers!\n")
    
    print(f"{'='*70}")
    print(f"✨ Summary:")
    print(f"   ✅ Consistent: {len(consistent_files)} files")
    print(f"   ⚠️  Issues: {len(issues)} files")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()

