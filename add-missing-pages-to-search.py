#!/usr/bin/env python3
"""
Add missing pages to search databases
Reads the generated entries and adds them to voice-assistant.js, compact-search.js, and search.html
"""

import re
import json

# Read generated entries
def read_generated_entries():
    """Read entries from search_database_entries.txt"""
    entries = []
    current_entry = {}
    
    with open('search_database_entries.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('Title:'):
                if current_entry:
                    entries.append(current_entry)
                current_entry = {'title': line.replace('Title:', '').strip()}
            elif line.startswith('URL:'):
                current_entry['url'] = line.replace('URL:', '').strip()
            elif line.startswith('Category:'):
                current_entry['category'] = line.replace('Category:', '').strip()
            elif line.startswith('Description:'):
                current_entry['description'] = line.replace('Description:', '').strip()
            elif line.startswith('Keywords:'):
                keywords_str = line.replace('Keywords:', '').strip()
                current_entry['keywords'] = [k.strip() for k in keywords_str.split(',')]
            elif line.startswith('Icon:'):
                current_entry['icon'] = line.replace('Icon:', '').strip()
    
    if current_entry:
        entries.append(current_entry)
    
    return entries

# Get existing URLs from a file
def get_existing_urls(filepath, pattern):
    """Extract existing URLs from a file using regex pattern"""
    existing = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    existing.add(match[0] if match[0] else match[1])
                else:
                    existing.add(match)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return existing

def format_js_entry(entry):
    """Format entry for JavaScript (compact-search.js format)"""
    keywords_str = ', '.join([f"'{k}'" for k in entry['keywords']])
    return f"""        {{ 
            title: '{entry['title'].replace("'", "\\'")}', 
            url: '{entry['url']}', 
            keywords: [{keywords_str}], 
            category: '{entry['category']}', 
            description: '{entry['description'].replace("'", "\\'")}',
            icon: '{entry.get('icon', 'fas fa-file')}'
        }}"""

def format_voice_entry(entry):
    """Format entry for voice assistant (simpler format)"""
    keywords_str = ', '.join([f"'{k}'" for k in entry['keywords']])
    return f"""            {{ 
                title: '{entry['title'].replace("'", "\\'")}', 
                url: '{entry['url']}', 
                keywords: [{keywords_str}], 
                category: '{entry['category']}', 
                description: '{entry['description'].replace("'", "\\'")}'
            }}"""

def format_search_entry(entry):
    """Format entry for search.html"""
    keywords_str = ' '.join(entry['keywords'])
    title = entry['title'].replace('"', '\\"')
    desc = entry['description'].replace('"', '\\"')
    return f'        {{ title: "{title}", url: "{entry["url"]}", description: "{desc}", type: "Tool", keywords: "{keywords_str}" }},'

def update_compact_search(entries, existing_urls):
    """Update compact-search.js"""
    missing = [e for e in entries if e['url'] not in existing_urls]
    
    if not missing:
        print("No missing entries for compact-search.js")
        return
    
    print(f"Adding {len(missing)} entries to compact-search.js")
    
    # Read file
    with open('js/compact-search.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the end of toolDatabase array (before the closing bracket)
    # Look for the last entry before the closing bracket
    pattern = r'(        \];\s*\n)'
    match = re.search(pattern, content)
    
    if match:
        # Insert new entries before the closing bracket
        new_entries = ',\n'.join([format_js_entry(e) for e in missing])
        replacement = f',\n{new_entries}\n        ];'
        content = content[:match.start()] + replacement + content[match.end():]
        
        # Write back
        with open('js/compact-search.js', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated compact-search.js with {len(missing)} entries")
    else:
        print("❌ Could not find insertion point in compact-search.js")

def update_voice_assistant(entries, existing_urls):
    """Update voice-assistant.js"""
    missing = [e for e in entries if e['url'] not in existing_urls]
    
    if not missing:
        print("No missing entries for voice-assistant.js")
        return
    
    print(f"Adding {len(missing)} entries to voice-assistant.js")
    
    # Read file
    with open('js/voice-assistant.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the end of toolDatabase array
    pattern = r'(\s*];\s*\n\s*// Calculate relevance score)'
    match = re.search(pattern, content)
    
    if match:
        # Insert new entries before the closing bracket
        new_entries = ',\n'.join([format_voice_entry(e) for e in missing])
        replacement = f',\n{new_entries}\n        ];'
        content = content[:match.start()] + replacement + content[match.end():]
        
        # Write back
        with open('js/voice-assistant.js', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated voice-assistant.js with {len(missing)} entries")
    else:
        print("❌ Could not find insertion point in voice-assistant.js")

def update_search_html(entries, existing_urls):
    """Update search.html"""
    missing = [e for e in entries if e['url'] not in existing_urls]
    
    if not missing:
        print("No missing entries for search.html")
        return
    
    print(f"Adding {len(missing)} entries to search.html")
    
    # Read file
    with open('search.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the end of searchData array
    pattern = r'(\s*];\s*\n\s*// Get search query from URL)'
    match = re.search(pattern, content)
    
    if match:
        # Insert new entries before the closing bracket
        new_entries = '\n'.join([format_search_entry(e) for e in missing])
        replacement = f',\n{new_entries}\n    ];'
        content = content[:match.start()] + replacement + content[match.end():]
        
        # Write back
        with open('search.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated search.html with {len(missing)} entries")
    else:
        print("❌ Could not find insertion point in search.html")

if __name__ == '__main__':
    print("Reading generated entries...")
    entries = read_generated_entries()
    print(f"Found {len(entries)} total entries")
    
    # Get existing URLs from each file
    print("\nChecking existing entries...")
    
    # compact-search.js pattern: url: 'filename.html'
    compact_existing = get_existing_urls('js/compact-search.js', r"url:\s*'([^']+)'")
    print(f"compact-search.js has {len(compact_existing)} entries")
    
    # voice-assistant.js pattern: url: 'filename.html'
    voice_existing = get_existing_urls('js/voice-assistant.js', r"url:\s*'([^']+)'")
    print(f"voice-assistant.js has {len(voice_existing)} entries")
    
    # search.html pattern: url: "filename.html"
    search_existing = get_existing_urls('search.html', r'url:\s*"([^"]+)"')
    print(f"search.html has {len(search_existing)} entries")
    
    # Update files
    print("\n" + "="*80)
    update_compact_search(entries, compact_existing)
    print("\n" + "="*80)
    update_voice_assistant(entries, voice_existing)
    print("\n" + "="*80)
    update_search_html(entries, search_existing)
    print("\n" + "="*80)
    print("\n✅ All updates complete!")

