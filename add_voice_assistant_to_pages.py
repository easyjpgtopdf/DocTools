#!/usr/bin/env python3
"""
Add voice assistant (Jarvis) to all pages that don't have it
"""

import os
import re
import glob

# Files to check
HTML_FILES = glob.glob('*.html') + glob.glob('*-convert.html')

# Voice assistant includes
VOICE_CSS = '<link rel="stylesheet" href="css/voice-assistant.css">'
VOICE_JS = '<script src="js/voice-assistant.js" defer></script>'

def has_voice_assistant(content):
    """Check if page already has voice assistant"""
    return 'voice-assistant.css' in content and 'voice-assistant.js' in content

def add_voice_assistant(filepath):
    """Add voice assistant to a page if missing"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has voice assistant
        if has_voice_assistant(content):
            return False
        
        # Find where to insert (after theme-modern.css or header.css)
        # Look for theme-modern.css or header.css link
        pattern1 = r'(<link[^>]*href=["\']css/theme-modern\.css["\'][^>]*>)'
        pattern2 = r'(<link[^>]*href=["\']css/header\.css["\'][^>]*>)'
        
        insert_pos = -1
        insert_after = None
        
        # Try to find theme-modern.css first
        match = re.search(pattern1, content)
        if match:
            insert_pos = match.end()
            insert_after = match.group(0)
        else:
            # Try header.css
            match = re.search(pattern2, content)
            if match:
                insert_pos = match.end()
                insert_after = match.group(0)
        
        if insert_pos == -1:
            # If neither found, try to find any CSS link before schema
            pattern3 = r'(<link[^>]*href=["\'][^"\']*\.css["\'][^>]*>)'
            matches = list(re.finditer(pattern3, content))
            if matches:
                # Get the last CSS link before schema
                schema_pos = content.find('<script type="application/ld+json">')
                for match in reversed(matches):
                    if match.end() < schema_pos:
                        insert_pos = match.end()
                        insert_after = match.group(0)
                        break
        
        if insert_pos == -1:
            # Last resort: find </head> and insert before it
            head_end = content.find('</head>')
            if head_end != -1:
                insert_pos = head_end
                insert_after = None
            else:
                print(f"  ⚠️  Could not find insertion point in {filepath}")
                return False
        
        # Insert voice assistant includes
        insertion = f'\n{VOICE_CSS}\n{VOICE_JS}'
        
        if insert_after:
            # Insert after the found CSS link
            new_content = content[:insert_pos] + insertion + content[insert_pos:]
        else:
            # Insert before </head>
            new_content = content[:insert_pos] + insertion + '\n' + content[insert_pos:]
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error processing {filepath}: {e}")
        return False

def main():
    print("Adding voice assistant to pages...\n")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for filepath in sorted(HTML_FILES):
        # Skip index.html (already has it)
        if 'index.html' in filepath:
            continue
        
        filename = os.path.basename(filepath)
        print(f"Checking {filename}...", end=' ')
        
        try:
            if add_voice_assistant(filepath):
                print("✅ Added")
                updated_count += 1
            else:
                print("⏭️  Already has it or skipped")
                skipped_count += 1
        except Exception as e:
            print(f"❌ Error: {e}")
            error_count += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Updated: {updated_count} pages")
    print(f"⏭️  Skipped: {skipped_count} pages")
    if error_count > 0:
        print(f"❌ Errors: {error_count} pages")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()

