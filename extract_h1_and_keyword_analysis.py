#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to extract H1 tags from all HTML pages and analyze keyword search volumes
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

def extract_h1_from_file(file_path):
    """Extract H1 tag content from a single HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        h1_tags = soup.find_all('h1')
        
        if h1_tags:
            # Get the first/main H1 tag
            main_h1 = h1_tags[0].get_text(strip=True)
            return main_h1, len(h1_tags)
        else:
            return None, 0
        
    except Exception as e:
        return f"ERROR: {str(e)}", 0

def get_title_from_file(file_path):
    """Extract title tag from HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        title_tag = soup.find('title')
        
        if title_tag:
            return title_tag.get_text(strip=True)
        return None
    except:
        return None

def main():
    """Main function to scan all HTML files."""
    # Get all HTML files
    html_files = []
    skip_dirs = {'node_modules', 'backup', 'backups', 'server', 'excel-unlocker', 
                 'bg-removal-backend', 'bg-remover-pytorch', 'pdf-editor-backend', 
                 'image-repair-backend', 'pdf-unlocker', 'api', 'api-handlers', 
                 'frontend', 'services', 'tools', 'scripts', 'css', 'js', 'images'}
    
    for root, dirs, files in os.walk('.'):
        if '.venv' in root or 'venv' in root or root.startswith('./env') or root.startswith('.\\env'):
            continue
        
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.venv') 
                   and not d.startswith('venv') and not d.startswith('env')]
        
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    html_files.sort()
    
    print("=" * 100)
    print("H1 TAG EXTRACTION AND KEYWORD ANALYSIS")
    print("=" * 100)
    print(f"\nTotal HTML files found: {len(html_files)}\n")
    
    results = []
    
    # Extract H1 from each file
    for file_path in html_files:
        relative_path = file_path.replace('\\', '/')
        if relative_path.startswith('./'):
            relative_path = relative_path[2:]
        
        h1_content, h1_count = extract_h1_from_file(file_path)
        title = get_title_from_file(file_path)
        
        if h1_content:
            results.append({
                'file': relative_path,
                'h1': h1_content,
                'h1_count': h1_count,
                'title': title
            })
        else:
            results.append({
                'file': relative_path,
                'h1': 'NO H1 TAG',
                'h1_count': 0,
                'title': title
            })
    
    # Save results to file
    with open('h1_tags_extraction_report.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("H1 TAG EXTRACTION REPORT - ALL PAGES\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Total HTML files analyzed: {len(html_files)}\n\n")
        
        f.write("-" * 100 + "\n")
        f.write(f"{'File Name':<50} {'H1 Tag Content':<60}\n")
        f.write("-" * 100 + "\n")
        
        for item in results:
            h1_display = item['h1'][:58] + "..." if len(item['h1']) > 60 else item['h1']
            file_display = item['file'][:48] + "..." if len(item['file']) > 50 else item['file']
            f.write(f"{file_display:<50} {h1_display:<60}\n")
        
        f.write("\n" + "=" * 100 + "\n")
        f.write("DETAILED H1 TAGS WITH FULL CONTENT\n")
        f.write("=" * 100 + "\n\n")
        
        for item in results:
            f.write(f"\nFile: {item['file']}\n")
            f.write(f"Title: {item['title'] or 'No Title'}\n")
            f.write(f"H1 Tag: {item['h1']}\n")
            f.write(f"H1 Count: {item['h1_count']}\n")
            f.write("-" * 100 + "\n")
    
    # Create CSV for easy analysis
    with open('h1_tags_list.csv', 'w', encoding='utf-8') as f:
        f.write("File,Title,H1 Tag,H1 Count\n")
        for item in results:
            file_clean = item['file'].replace(',', ';')
            title_clean = (item['title'] or 'No Title').replace(',', ';').replace('\n', ' ')
            h1_clean = item['h1'].replace(',', ';').replace('\n', ' ')
            f.write(f'"{file_clean}","{title_clean}","{h1_clean}",{item["h1_count"]}\n')
    
    print(f"\n✅ Report saved to: h1_tags_extraction_report.txt")
    print(f"✅ CSV saved to: h1_tags_list.csv")
    print(f"\nTotal pages with H1: {sum(1 for r in results if r['h1'] != 'NO H1 TAG')}")
    print(f"Total pages without H1: {sum(1 for r in results if r['h1'] == 'NO H1 TAG')}")
    print(f"Total pages with multiple H1: {sum(1 for r in results if r['h1_count'] > 1)}")
    
    return results

if __name__ == '__main__':
    main()




