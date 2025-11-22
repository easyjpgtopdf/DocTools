#!/usr/bin/env python3
"""
Fix blog.html - Remove Coming Soon panel and update search box styling
"""

from pathlib import Path
import re

file_path = Path('blog.html')

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Remove Coming Soon HTML section
    coming_soon_pattern = r'<!-- Coming Soon Message -->.*?</div>\s*\n\s*'
    content = re.sub(coming_soon_pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Fix search icon size
    content = re.sub(r'font-size:\s*1\.2rem', 'font-size: 0.9rem', content, flags=re.IGNORECASE)
    content = re.sub(r'margin-right:\s*12px', 'margin-right: 10px', content, flags=re.IGNORECASE)
    
    # Fix search input size
    content = re.sub(r'font-size:\s*1rem(?!\s*color)', 'font-size: 0.9rem', content, flags=re.IGNORECASE)
    
    # Fix padding
    content = re.sub(r'padding:\s*12px\s+20px', 'padding: 8px 16px', content, flags=re.IGNORECASE)
    
    # Fix main padding
    content = re.sub(r'padding:\s*40px\s+24px', 'padding: 24px 24px', content, flags=re.IGNORECASE)
    
    # Fix header margin
    content = re.sub(r'margin-bottom:\s*50px', 'margin-bottom: 24px', content, flags=re.IGNORECASE)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed blog.html")
        print(f"   • Removed Coming Soon panel")
        print(f"   • Updated search box styling")
        print(f"   • Reduced margins and padding")
    else:
        print("✓ blog.html already fixed")
        
except Exception as e:
    print(f"❌ Error: {e}")

