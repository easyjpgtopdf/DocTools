#!/usr/bin/env python3
"""
Check for duplicate/similar content across blogs
Find similar paragraphs and topics
"""

import os
import re
from difflib import SequenceMatcher

BLOG_FILES = [
    "blog-how-to-use-jpg-to-pdf.html",
    "blog-how-to-use-word-to-pdf.html",
    "blog-how-to-use-excel-to-pdf.html",
    "blog-how-to-use-ppt-to-pdf.html",
]

def extract_paragraphs(content):
    """Extract paragraphs from HTML"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', content)
    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 100]
    return paragraphs

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a, b).ratio()

def check_duplicate_content():
    """Check for duplicate content across blogs"""
    print("=" * 80)
    print("CHECKING FOR DUPLICATE/SIMILAR CONTENT")
    print("=" * 80)
    print()
    
    blog_contents = {}
    
    # Load all blog contents
    for blog_file in BLOG_FILES:
        if os.path.exists(blog_file):
            with open(blog_file, 'r', encoding='utf-8') as f:
                content = f.read()
            paragraphs = extract_paragraphs(content)
            blog_contents[blog_file] = paragraphs
    
    # Compare blogs
    duplicates_found = []
    
    for file1, paras1 in blog_contents.items():
        for file2, paras2 in blog_contents.items():
            if file1 >= file2:  # Avoid duplicate comparisons
                continue
            
            for i, para1 in enumerate(paras1):
                for j, para2 in enumerate(paras2):
                    sim = similarity(para1, para2)
                    if sim > 0.8:  # 80% similar
                        duplicates_found.append({
                            'file1': file1,
                            'file2': file2,
                            'para1_index': i,
                            'para2_index': j,
                            'similarity': sim,
                            'text': para1[:100] + '...'
                        })
    
    if duplicates_found:
        print(f"⚠️  Found {len(duplicates_found)} similar paragraphs:\n")
        for dup in duplicates_found[:10]:  # Show first 10
            print(f"Similarity: {dup['similarity']:.2%}")
            print(f"  {dup['file1']} (para {dup['para1_index']})")
            print(f"  {dup['file2']} (para {dup['para2_index']})")
            print(f"  Text: {dup['text']}")
            print()
    else:
        print("✅ No highly similar paragraphs found")
    
    print("=" * 80)
    print("NOTE: Manual review recommended for content uniqueness")
    print("=" * 80)

if __name__ == "__main__":
    check_duplicate_content()

