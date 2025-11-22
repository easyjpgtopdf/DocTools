#!/usr/bin/env python3
"""
Remove Coming Soon panel from blog.html
"""

from pathlib import Path

file_path = Path('blog.html')

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and remove Coming Soon section
    output_lines = []
    skip_next = False
    in_coming_soon = False
    div_count = 0
    
    for i, line in enumerate(lines):
        if '<!-- Coming Soon Message -->' in line:
            in_coming_soon = True
            div_count = 0
            skip_next = True
            continue
        
        if skip_next and in_coming_soon:
            if '<div' in line:
                div_count += line.count('<div')
            if '</div>' in line:
                div_count -= line.count('</div>')
            if div_count <= 0 and '</div>' in line:
                skip_next = False
                in_coming_soon = False
                continue
        
        if not skip_next:
            output_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    
    print(f"✅ Removed Coming Soon panel from blog.html")
    
except Exception as e:
    print(f"❌ Error: {e}")

