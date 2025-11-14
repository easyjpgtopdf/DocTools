import os
import re

# Main folder ke HTML files
main_folder = r"c:\Users\apnao\Downloads\DocTools"

# Skip files
skip_files = ['test-', 'excel-unlocker\\templates', 'server\\public']

# Image Tools dropdown pattern (without image-repair)
old_pattern = r'(<div class="dropdown">\s*<a href="#">Image Tools <i class="fas fa-chevron-down"></i></a>\s*<div class="dropdown-content">\s*)' \
              r'(<a href="image-compressor\.html">Image Compressor</a>)'

# New pattern (with image-repair at the beginning)
new_content = r'\1<a href="image-repair.html">AI Image Repair</a>\n\2'

# Files to update
files_to_update = []

# Walk through all HTML files
for root, dirs, files in os.walk(main_folder):
    # Skip server/public and backups
    if 'server' in root or 'backup' in root.lower():
        continue
    
    for file in files:
        if file.endswith('.html'):
            # Skip test files
            if any(skip in file for skip in skip_files):
                continue
            
            filepath = os.path.join(root, file)
            files_to_update.append(filepath)

updated_count = 0
already_updated = 0
not_found = 0

for filepath in files_to_update:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has image-repair
        if 'href="image-repair.html"' in content:
            already_updated += 1
            continue
        
        # Check if has Image Tools dropdown
        if 'Image Tools' not in content:
            not_found += 1
            continue
        
        # Simple string replacement for the specific pattern
        old_str = '<div class="dropdown-content">\n<a href="image-compressor.html">Image Compressor</a>'
        new_str = '<div class="dropdown-content">\n<a href="image-repair.html">AI Image Repair</a>\n<a href="image-compressor.html">Image Compressor</a>'
        
        if old_str in content:
            new_content_str = content.replace(old_str, new_str)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content_str)
            
            updated_count += 1
            print(f"✓ Updated: {os.path.basename(filepath)}")
        else:
            # Try with different indentation
            old_str2 = '<div class="dropdown-content"><a class="active" href="image-compressor.html">Image Compressor</a>'
            new_str2 = '<div class="dropdown-content"><a class="active" href="image-repair.html">AI Image Repair</a><a class="active" href="image-compressor.html">Image Compressor</a>'
            
            if old_str2 in content:
                new_content_str = content.replace(old_str2, new_str2)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content_str)
                
                updated_count += 1
                print(f"✓ Updated (inline): {os.path.basename(filepath)}")
            else:
                print(f"⚠ Pattern not found: {os.path.basename(filepath)}")
                not_found += 1
    
    except Exception as e:
        print(f"✗ Error in {os.path.basename(filepath)}: {str(e)}")

print(f"\n{'='*60}")
print(f"Total files processed: {len(files_to_update)}")
print(f"Updated: {updated_count}")
print(f"Already had image-repair: {already_updated}")
print(f"Pattern not found: {not_found}")
print(f"{'='*60}")
