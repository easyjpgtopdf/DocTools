#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive H1 Tag and Keyword Search Volume Analysis
Extracts H1 tags and provides keyword search volume estimates
"""

import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict

# Estimated monthly search volumes based on industry data (approximate)
KEYWORD_VOLUMES = {
    # PDF Tools - High Volume
    "pdf converter": 450000,
    "jpg to pdf": 165000,
    "word to pdf": 135000,
    "pdf to word": 110000,
    "merge pdf": 90000,
    "split pdf": 74000,
    "compress pdf": 60500,
    "edit pdf": 49500,
    "pdf to jpg": 49500,
    "pdf to excel": 40500,
    "excel to pdf": 33100,
    "pdf to ppt": 27100,
    "ppt to pdf": 22200,
    "protect pdf": 18100,
    "unlock pdf": 14800,
    "watermark pdf": 12100,
    "crop pdf": 9900,
    "add page numbers pdf": 8100,
    
    # Image Tools
    "remove background": 135000,
    "image converter": 49500,
    "resize image": 33100,
    "compress image": 27100,
    "image editor": 22200,
    "image repair": 18100,
    "watermark image": 14800,
    "ocr image": 12100,
    "image to text": 9900,
    
    # Resume/CV Tools
    "resume maker": 110000,
    "resume builder": 90500,
    "cv maker": 49500,
    "online resume": 33100,
    "resume generator": 27100,
    "biodata maker": 14800,
    
    # Archive Tools
    "zip converter": 18100,
    "rar extractor": 12100,
    "7z extractor": 8100,
    
    # Other Tools
    "ai image generator": 22200,
    "background remover": 135000,
}

def extract_main_keyword(h1_text):
    """Extract main keyword from H1 text."""
    if not h1_text or h1_text == "NO H1 TAG":
        return None
    
    # Common patterns to extract keywords
    h1_lower = h1_text.lower()
    
    # Check for high-volume keywords
    for keyword, volume in sorted(KEYWORD_VOLUMES.items(), key=lambda x: x[1], reverse=True):
        if keyword in h1_lower:
            return keyword
    
    # Extract first meaningful words
    words = h1_text.split()
    if len(words) >= 2:
        # Take first 2-3 words as keyword
        keyword = " ".join(words[:3]).lower()
        # Remove common words
        stop_words = ['online', 'free', 'tool', 'convert', 'converter', 'the', 'a', 'an']
        keyword_parts = [w for w in keyword.split() if w not in stop_words]
        if keyword_parts:
            return " ".join(keyword_parts[:3])
    
    return h1_text.lower()[:50]

def estimate_search_volume(keyword):
    """Estimate search volume for a keyword."""
    if not keyword:
        return 0
    
    keyword_lower = keyword.lower()
    
    # Direct match
    for kw, volume in KEYWORD_VOLUMES.items():
        if kw in keyword_lower or keyword_lower in kw:
            return volume
    
    # Partial match
    for kw, volume in sorted(KEYWORD_VOLUMES.items(), key=lambda x: x[1], reverse=True):
        if any(word in keyword_lower for word in kw.split() if len(word) > 3):
            return int(volume * 0.3)  # 30% of exact match
    
    # Default estimates based on keyword type
    if any(word in keyword_lower for word in ['pdf', 'convert', 'merge', 'split']):
        return 5000  # Medium volume for PDF tools
    elif any(word in keyword_lower for word in ['image', 'photo', 'picture']):
        return 3000  # Medium volume for image tools
    elif any(word in keyword_lower for word in ['resume', 'cv', 'biodata']):
        return 2000  # Lower volume for resume tools
    else:
        return 500  # Low volume for others

def suggest_better_keywords(h1_text, current_keyword):
    """Suggest better keywords with higher search volume."""
    suggestions = []
    h1_lower = h1_text.lower()
    
    # PDF-related suggestions
    if 'pdf' in h1_lower:
        if 'merge' in h1_lower or 'combine' in h1_lower:
            suggestions.append(("merge pdf online free", 90000))
            suggestions.append(("combine pdf files", 49500))
        elif 'split' in h1_lower:
            suggestions.append(("split pdf online free", 74000))
            suggestions.append(("divide pdf", 18100))
        elif 'compress' in h1_lower:
            suggestions.append(("compress pdf online free", 60500))
            suggestions.append(("reduce pdf size", 33100))
        elif 'edit' in h1_lower:
            suggestions.append(("edit pdf online free", 49500))
            suggestions.append(("pdf editor online", 33100))
        elif 'protect' in h1_lower or 'password' in h1_lower:
            suggestions.append(("password protect pdf", 18100))
            suggestions.append(("secure pdf", 12100))
        elif 'unlock' in h1_lower or 'remove password' in h1_lower:
            suggestions.append(("unlock pdf online free", 14800))
            suggestions.append(("remove pdf password", 12100))
        elif 'watermark' in h1_lower:
            suggestions.append(("add watermark to pdf", 12100))
            suggestions.append(("pdf watermark", 9900))
        elif 'crop' in h1_lower:
            suggestions.append(("crop pdf pages", 9900))
            suggestions.append(("pdf cropper", 8100))
        elif 'page numbers' in h1_lower:
            suggestions.append(("add page numbers to pdf", 8100))
            suggestions.append(("number pdf pages", 6600))
    
    # Image-related suggestions
    if 'image' in h1_lower or 'photo' in h1_lower:
        if 'background' in h1_lower and 'remove' in h1_lower:
            suggestions.append(("remove background from image", 135000))
            suggestions.append(("background remover online", 90500))
        elif 'resize' in h1_lower:
            suggestions.append(("resize image online free", 33100))
            suggestions.append(("image resizer", 22200))
        elif 'compress' in h1_lower:
            suggestions.append(("compress image online free", 27100))
            suggestions.append(("image compressor", 18100))
        elif 'edit' in h1_lower:
            suggestions.append(("edit image online free", 22200))
            suggestions.append(("online image editor", 14800))
        elif 'repair' in h1_lower or 'fix' in h1_lower:
            suggestions.append(("repair damaged image", 18100))
            suggestions.append(("fix corrupted image", 12100))
        elif 'watermark' in h1_lower:
            suggestions.append(("add watermark to image", 14800))
            suggestions.append(("image watermark", 12100))
        elif 'ocr' in h1_lower or 'text' in h1_lower:
            suggestions.append(("ocr image to text", 12100))
            suggestions.append(("image to text converter", 9900))
    
    # Resume-related suggestions
    if 'resume' in h1_lower or 'cv' in h1_lower or 'biodata' in h1_lower:
        suggestions.append(("resume maker online free", 110000))
        suggestions.append(("resume builder", 90500))
        suggestions.append(("online resume creator", 33100))
        suggestions.append(("free resume generator", 27100))
    
    # Converter suggestions
    if 'to pdf' in h1_lower:
        if 'jpg' in h1_lower or 'image' in h1_lower:
            suggestions.append(("jpg to pdf converter", 165000))
            suggestions.append(("image to pdf", 90500))
        elif 'word' in h1_lower or 'doc' in h1_lower:
            suggestions.append(("word to pdf converter", 135000))
            suggestions.append(("doc to pdf", 90500))
        elif 'excel' in h1_lower or 'xls' in h1_lower:
            suggestions.append(("excel to pdf converter", 33100))
            suggestions.append(("xls to pdf", 22200))
        elif 'ppt' in h1_lower or 'powerpoint' in h1_lower:
            suggestions.append(("ppt to pdf converter", 22200))
            suggestions.append(("powerpoint to pdf", 18100))
    
    if 'pdf to' in h1_lower:
        if 'word' in h1_lower or 'doc' in h1_lower:
            suggestions.append(("pdf to word converter", 110000))
            suggestions.append(("pdf to doc", 90500))
        elif 'jpg' in h1_lower or 'image' in h1_lower:
            suggestions.append(("pdf to jpg converter", 49500))
            suggestions.append(("pdf to image", 33100))
        elif 'excel' in h1_lower or 'xls' in h1_lower:
            suggestions.append(("pdf to excel converter", 40500))
            suggestions.append(("pdf to xls", 27100))
        elif 'ppt' in h1_lower or 'powerpoint' in h1_lower:
            suggestions.append(("pdf to ppt converter", 27100))
            suggestions.append(("pdf to powerpoint", 22200))
    
    # Sort by volume and return top 3
    suggestions.sort(key=lambda x: x[1], reverse=True)
    return suggestions[:3]

def main():
    """Main analysis function."""
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
    
    results = []
    
    for file_path in html_files:
        relative_path = file_path.replace('\\', '/')
        if relative_path.startswith('./'):
            relative_path = relative_path[2:]
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            h1_tags = soup.find_all('h1')
            title_tag = soup.find('title')
            
            if h1_tags:
                h1_text = h1_tags[0].get_text(strip=True)
                main_keyword = extract_main_keyword(h1_text)
                search_volume = estimate_search_volume(main_keyword)
                suggestions = suggest_better_keywords(h1_text, main_keyword)
                
                results.append({
                    'file': relative_path,
                    'h1': h1_text,
                    'title': title_tag.get_text(strip=True) if title_tag else 'No Title',
                    'main_keyword': main_keyword,
                    'search_volume': search_volume,
                    'suggestions': suggestions
                })
            else:
                results.append({
                    'file': relative_path,
                    'h1': 'NO H1 TAG',
                    'title': title_tag.get_text(strip=True) if title_tag else 'No Title',
                    'main_keyword': None,
                    'search_volume': 0,
                    'suggestions': []
                })
        except Exception as e:
            results.append({
                'file': relative_path,
                'h1': f'ERROR: {str(e)}',
                'title': 'Error',
                'main_keyword': None,
                'search_volume': 0,
                'suggestions': []
            })
    
    # Generate comprehensive report
    with open('H1_KEYWORD_SEARCH_VOLUME_ANALYSIS.md', 'w', encoding='utf-8') as f:
        f.write("# H1 Tag और Keyword Search Volume Analysis\n\n")
        f.write("## 📊 Overview\n\n")
        f.write(f"- **Total Pages Analyzed:** {len(results)}\n")
        f.write(f"- **Pages with H1:** {sum(1 for r in results if r['h1'] != 'NO H1 TAG')}\n")
        f.write(f"- **Pages without H1:** {sum(1 for r in results if r['h1'] == 'NO H1 TAG')}\n\n")
        
        f.write("---\n\n")
        f.write("## 📋 Detailed Analysis\n\n")
        f.write("| File Name | H1 Tag | Main Keyword | Current Search Volume | Better Keywords (Higher Volume) |\n")
        f.write("|-----------|--------|--------------|----------------------|----------------------------------|\n")
        
        for item in results:
            file_display = item['file'][:40] + "..." if len(item['file']) > 43 else item['file']
            h1_display = item['h1'][:50] + "..." if len(item['h1']) > 53 else item['h1']
            keyword_display = item['main_keyword'][:30] + "..." if item['main_keyword'] and len(item['main_keyword']) > 33 else (item['main_keyword'] or 'N/A')
            volume_display = f"{item['search_volume']:,}" if item['search_volume'] > 0 else "0"
            
            suggestions_text = ""
            if item['suggestions']:
                for sug_keyword, sug_volume in item['suggestions']:
                    suggestions_text += f"{sug_keyword} ({sug_volume:,}/month), "
                suggestions_text = suggestions_text.rstrip(", ")
            else:
                suggestions_text = "N/A"
            
            f.write(f"| {file_display} | {h1_display} | {keyword_display} | {volume_display} | {suggestions_text} |\n")
        
        f.write("\n---\n\n")
        f.write("## 🔍 Top Keywords by Search Volume\n\n")
        
        # Sort by search volume
        sorted_results = sorted([r for r in results if r['search_volume'] > 0], 
                               key=lambda x: x['search_volume'], reverse=True)
        
        f.write("| Rank | File | H1 Tag | Keyword | Monthly Searches |\n")
        f.write("|------|------|--------|---------|------------------|\n")
        
        for idx, item in enumerate(sorted_results[:50], 1):  # Top 50
            file_display = item['file'][:35] + "..." if len(item['file']) > 38 else item['file']
            h1_display = item['h1'][:45] + "..." if len(item['h1']) > 48 else item['h1']
            keyword_display = item['main_keyword'][:25] + "..." if item['main_keyword'] and len(item['main_keyword']) > 28 else (item['main_keyword'] or 'N/A')
            f.write(f"| {idx} | {file_display} | {h1_display} | {keyword_display} | {item['search_volume']:,} |\n")
    
    # Generate CSV
    with open('h1_keyword_analysis.csv', 'w', encoding='utf-8') as f:
        f.write("File,H1 Tag,Main Keyword,Search Volume,Better Keyword 1,Volume 1,Better Keyword 2,Volume 2,Better Keyword 3,Volume 3\n")
        for item in results:
            file_clean = item['file'].replace(',', ';')
            h1_clean = item['h1'].replace(',', ';').replace('\n', ' ')
            keyword_clean = (item['main_keyword'] or 'N/A').replace(',', ';')
            
            sug1 = item['suggestions'][0] if len(item['suggestions']) > 0 else ('N/A', 0)
            sug2 = item['suggestions'][1] if len(item['suggestions']) > 1 else ('N/A', 0)
            sug3 = item['suggestions'][2] if len(item['suggestions']) > 2 else ('N/A', 0)
            
            f.write(f'"{file_clean}","{h1_clean}","{keyword_clean}",{item["search_volume"]},"{sug1[0]}",{sug1[1]},"{sug2[0]}",{sug2[1]},"{sug3[0]}",{sug3[1]}\n')
    
    print("\n" + "=" * 100)
    print("H1 KEYWORD SEARCH VOLUME ANALYSIS COMPLETE")
    print("=" * 100)
    print(f"\n✅ Report saved to: H1_KEYWORD_SEARCH_VOLUME_ANALYSIS.md")
    print(f"✅ CSV saved to: h1_keyword_analysis.csv")
    print(f"\n📊 Summary:")
    print(f"   - Total pages: {len(results)}")
    print(f"   - Pages with H1: {sum(1 for r in results if r['h1'] != 'NO H1 TAG')}")
    print(f"   - Pages with search volume > 10K: {sum(1 for r in results if r['search_volume'] > 10000)}")
    print(f"   - Pages with search volume > 50K: {sum(1 for r in results if r['search_volume'] > 50000)}")
    print(f"   - Pages with search volume > 100K: {sum(1 for r in results if r['search_volume'] > 100000)}")

if __name__ == '__main__':
    main()



