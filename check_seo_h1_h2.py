#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to check all HTML pages for:
1. Missing SEO elements (meta description, title)
2. Missing H1 tags
3. Multiple H1 tags (more than 1)
4. Multiple H2 tags (more than 1)
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

def check_html_file(file_path):
    """Check a single HTML file for SEO and heading issues."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        issues = {
            'missing_seo': [],
            'missing_h1': False,
            'multiple_h1': False,
            'multiple_h2': False,
            'h1_count': 0,
            'h2_count': 0
        }
        
        # Check for SEO elements
        title_tag = soup.find('title')
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        meta_og_title = soup.find('meta', attrs={'property': 'og:title'})
        meta_og_description = soup.find('meta', attrs={'property': 'og:description'})
        
        if not title_tag or not title_tag.string or not title_tag.string.strip():
            issues['missing_seo'].append('Title tag missing or empty')
        
        if not meta_description or not meta_description.get('content', '').strip():
            issues['missing_seo'].append('Meta description missing or empty')
        
        # Check for H1 tags
        h1_tags = soup.find_all('h1')
        issues['h1_count'] = len(h1_tags)
        
        if len(h1_tags) == 0:
            issues['missing_h1'] = True
        elif len(h1_tags) > 1:
            issues['multiple_h1'] = True
        
        # Check for H2 tags
        h2_tags = soup.find_all('h2')
        issues['h2_count'] = len(h2_tags)
        
        if len(h2_tags) > 1:
            issues['multiple_h2'] = True
        
        return issues
        
    except Exception as e:
        return {'error': str(e)}

def main():
    """Main function to scan all HTML files."""
    # Get all HTML files in the current directory and subdirectories
    html_files = []
    skip_dirs = {'node_modules', 'backup', 'backups', 'server', 'excel-unlocker', 'bg-removal-backend', 
                 'bg-remover-pytorch', 'pdf-editor-backend', 'image-repair-backend', 'pdf-unlocker', 
                 'api', 'api-handlers', 'frontend', 'services', 'tools', 'scripts', 'css', 'js', 'images'}
    
    for root, dirs, files in os.walk('.'):
        # Skip virtual environment paths
        if '.venv' in root or 'venv' in root or root.startswith('./env') or root.startswith('.\\env'):
            continue
        
        # Filter out directories to skip
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.venv') and not d.startswith('venv') and not d.startswith('env')]
        
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    # Sort files for consistent output
    html_files.sort()
    
    # Results storage
    missing_seo_h1 = []  # Pages missing SEO or H1
    multiple_h1 = []     # Pages with more than 1 H1
    multiple_h2 = []     # Pages with more than 1 H2
    
    print("=" * 80)
    print("HTML PAGES SEO & HEADING ANALYSIS")
    print("=" * 80)
    print(f"\nTotal HTML files found: {len(html_files)}\n")
    
    # Analyze each file
    for file_path in html_files:
        relative_path = file_path.replace('\\', '/')
        if relative_path.startswith('./'):
            relative_path = relative_path[2:]
        
        issues = check_html_file(file_path)
        
        if 'error' in issues:
            print(f"ERROR processing {relative_path}: {issues['error']}")
            continue
        
        # Check if page has issues
        has_seo_issue = len(issues['missing_seo']) > 0
        has_h1_issue = issues['missing_h1']
        
        if has_seo_issue or has_h1_issue:
            missing_seo_h1.append({
                'file': relative_path,
                'missing_seo': issues['missing_seo'],
                'missing_h1': issues['missing_h1']
            })
        
        if issues['multiple_h1']:
            multiple_h1.append({
                'file': relative_path,
                'count': issues['h1_count']
            })
        
        if issues['multiple_h2']:
            multiple_h2.append({
                'file': relative_path,
                'count': issues['h2_count']
            })
    
    # Print results
    print("\n" + "=" * 80)
    print("1. PAGES WITH MISSING SEO OR H1 TAGS")
    print("=" * 80)
    if missing_seo_h1:
        for item in missing_seo_h1:
            print(f"\n📄 {item['file']}")
            if item['missing_seo']:
                print("   ❌ Missing SEO:")
                for seo_issue in item['missing_seo']:
                    print(f"      - {seo_issue}")
            if item['missing_h1']:
                print("   ❌ Missing H1 tag")
        print(f"\nTotal: {len(missing_seo_h1)} pages")
    else:
        print("\n✅ All pages have SEO and H1 tags!")
    
    print("\n" + "=" * 80)
    print("2. PAGES WITH MORE THAN 1 H1 TAG")
    print("=" * 80)
    if multiple_h1:
        for item in multiple_h1:
            print(f"📄 {item['file']} - {item['count']} H1 tags")
        print(f"\nTotal: {len(multiple_h1)} pages")
    else:
        print("\n✅ No pages have multiple H1 tags!")
    
    print("\n" + "=" * 80)
    print("3. PAGES WITH MORE THAN 1 H2 TAG")
    print("=" * 80)
    if multiple_h2:
        for item in multiple_h2:
            print(f"📄 {item['file']} - {item['count']} H2 tags")
        print(f"\nTotal: {len(multiple_h2)} pages")
    else:
        print("\n✅ No pages have multiple H2 tags!")
    
    # Save results to file
    with open('seo_h1_h2_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("HTML PAGES SEO & HEADING ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total HTML files analyzed: {len(html_files)}\n\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("1. PAGES WITH MISSING SEO OR H1 TAGS\n")
        f.write("=" * 80 + "\n")
        if missing_seo_h1:
            for item in missing_seo_h1:
                f.write(f"\n{item['file']}\n")
                if item['missing_seo']:
                    f.write("Missing SEO:\n")
                    for seo_issue in item['missing_seo']:
                        f.write(f"  - {seo_issue}\n")
                if item['missing_h1']:
                    f.write("Missing H1 tag\n")
            f.write(f"\nTotal: {len(missing_seo_h1)} pages\n")
        else:
            f.write("\nAll pages have SEO and H1 tags!\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("2. PAGES WITH MORE THAN 1 H1 TAG\n")
        f.write("=" * 80 + "\n")
        if multiple_h1:
            for item in multiple_h1:
                f.write(f"{item['file']} - {item['count']} H1 tags\n")
            f.write(f"\nTotal: {len(multiple_h1)} pages\n")
        else:
            f.write("\nNo pages have multiple H1 tags!\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("3. PAGES WITH MORE THAN 1 H2 TAG\n")
        f.write("=" * 80 + "\n")
        if multiple_h2:
            for item in multiple_h2:
                f.write(f"{item['file']} - {item['count']} H2 tags\n")
            f.write(f"\nTotal: {len(multiple_h2)} pages\n")
        else:
            f.write("\nNo pages have multiple H2 tags!\n")
    
    print("\n" + "=" * 80)
    print(f"✅ Report saved to: seo_h1_h2_analysis_report.txt")
    print("=" * 80)

if __name__ == '__main__':
    main()

