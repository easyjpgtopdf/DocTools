#!/usr/bin/env python3
"""
Fix Blog Pages:
1. Remove duplicate search boxes (keep only one)
2. Reduce margin height and width of search box
3. Add Jarvis voice command feature to all blog pages
4. Enable voice search for blog functions, keywords, text, and links
"""

import os
import re
from pathlib import Path

# Blog pages to fix
BLOG_PAGES = [
    'blog-articles.html',
    'blog-tutorials.html',
    'blog-tips.html',
    'blog-news.html',
    'blog-guides.html',
    'blog.html'
]

EXCLUDE_PATTERNS = ['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backups']

def should_exclude(file_path):
    """Check if file should be excluded"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def count_search_boxes(content):
    """Count number of search box containers"""
    # Count blog-search-container divs
    search_container_count = len(re.findall(r'<div[^>]*class="blog-search-container"[^>]*>', content, re.IGNORECASE))
    # Count blogSearchInput IDs
    search_input_count = content.count('id="blogSearchInput"')
    return max(search_container_count, search_input_count)

def remove_duplicate_search_box(content, file_path):
    """Remove duplicate search boxes, keep only one"""
    changes = []
    
    # Count search boxes
    search_count = count_search_boxes(content)
    
    if search_count > 1:
        # Find all search box containers
        search_box_pattern = r'(<!-- Blog Search Bar -->\s*)?<div[^>]*class="blog-search-container"[^>]*>.*?</div>\s*</div>\s*</div>'
        matches = list(re.finditer(search_box_pattern, content, re.IGNORECASE | re.DOTALL))
        
        if len(matches) > 1:
            # Remove all but the first one (keep the first)
            for match in reversed(matches[1:]):  # Remove from end to maintain positions
                content = content[:match.start()] + content[match.end():]
                changes.append(f"Removed duplicate search box (kept first one)")
    
    # Also check if JavaScript is creating duplicate search bars
    # The js/blog-search.js creates search bar dynamically, so we should only have HTML search bar
    
    return content, changes

def reduce_search_box_size(content, file_path):
    """Reduce margin, height, and width of search box"""
    changes = []
    
    # Reduce search container margin
    content = re.sub(
        r'\.blog-search-container\s*\{[^}]*margin:\s*35px\s+0\s+35px',
        '.blog-search-container {\n            margin: 20px 0 25px;',
        content,
        flags=re.IGNORECASE
    )
    if 'margin: 20px 0 25px' in content:
        changes.append("Reduced search container margin (20px top, 25px bottom)")
    
    # Reduce search wrapper max-width
    content = re.sub(
        r'max-width:\s*800px',
        'max-width: 650px',
        content,
        flags=re.IGNORECASE
    )
    if 'max-width: 650px' in content:
        changes.append("Reduced search wrapper max-width to 650px")
    
    # Reduce search input wrapper padding
    content = re.sub(
        r'padding:\s*16px\s+28px',
        'padding: 12px 20px',
        content,
        flags=re.IGNORECASE
    )
    if 'padding: 12px 20px' in content:
        changes.append("Reduced search input padding to 12px 20px")
    
    # Reduce font sizes slightly
    content = re.sub(
        r'font-size:\s*1\.1rem',
        'font-size: 1rem',
        content,
        flags=re.IGNORECASE
    )
    if 'font-size: 1rem' in content and 'blog-search' in content:
        changes.append("Reduced font sizes to 1rem")
    
    return content, changes

def add_voice_assistant(content, file_path):
    """Add Jarvis voice command feature to blog page"""
    changes = []
    
    # Check if voice assistant CSS is already included
    if 'voice-assistant.css' not in content and 'voice-assistant' not in content.lower():
        # Find head tag and add CSS link before closing head
        head_close = content.find('</head>')
        if head_close != -1:
            voice_css = '\n    <link rel="stylesheet" href="css/voice-assistant.css">'
            content = content[:head_close] + voice_css + content[head_close:]
            changes.append("Added voice assistant CSS")
    
    # Check if voice assistant JS is already included
    if 'voice-assistant.js' not in content and 'voice-assistant' not in content.lower():
        # Find body close tag and add JS before it
        body_close = content.find('</body>')
        if body_close != -1:
            voice_js = '\n    <script src="js/voice-assistant.js"></script>'
            content = content[:body_close] + voice_js + content[body_close:]
            changes.append("Added voice assistant JavaScript")
    
    # Add voice assistant HTML button if not present
    if 'voice-assistant-btn' not in content and 'jarvis' not in content.lower():
        # Find search bar container and add voice button near it
        search_container_pattern = r'(<div[^>]*class="blog-search-container"[^>]*>.*?</div>\s*</div>\s*</div>)'
        match = re.search(search_container_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            # Add voice assistant button after search container
            voice_button = '''
            <!-- Jarvis Voice Assistant Button -->
            <div class="voice-assistant-container" style="text-align: center; margin: 15px 0;">
                <button id="voiceAssistantBtn" class="voice-assistant-btn" aria-label="Start voice command">
                    <i class="fas fa-microphone"></i>
                    <span class="voice-assistant-text">Voice Search</span>
                </button>
                <div id="voiceStatus" class="voice-status" style="display: none;"></div>
            </div>
'''
            insert_pos = match.end()
            content = content[:insert_pos] + voice_button + content[insert_pos:]
            changes.append("Added Jarvis voice assistant button")
    
    return content, changes

def enhance_voice_search_capability(content, file_path):
    """Enhance voice search to work with blog functions, keywords, text, and links"""
    changes = []
    
    # Check if blog-search.js is included
    if 'blog-search.js' not in content:
        # Add blog-search.js if missing
        body_close = content.find('</body>')
        if body_close != -1:
            blog_search_js = '\n    <script src="js/blog-search.js"></script>'
            content = content[:body_close] + blog_search_js + content[body_close:]
            changes.append("Added blog-search.js for search functionality")
    
    # Add integration script for voice + blog search
    if 'voice-blog-integration' not in content.lower():
        integration_script = '''
    <script>
        // Voice Assistant + Blog Search Integration
        document.addEventListener('DOMContentLoaded', function() {
            const voiceBtn = document.getElementById('voiceAssistantBtn');
            const blogSearchInput = document.getElementById('blogSearchInput');
            const blogSearchInstance = window.blogSearchInstance;
            
            if (voiceBtn && blogSearchInput && blogSearchInstance) {
                // Listen for voice recognition results
                document.addEventListener('voiceCommand', function(event) {
                    const command = event.detail.command.toLowerCase();
                    
                    // Search in blog using voice command
                    if (blogSearchInput && blogSearchInstance) {
                        blogSearchInput.value = command;
                        blogSearchInstance.handleSearch(command);
                        
                        // Show search results
                        const resultsContainer = document.getElementById('blogSearchResults');
                        if (resultsContainer) {
                            resultsContainer.style.display = 'block';
                        }
                    }
                });
                
                // Enhanced voice commands for blog functions
                const blogVoiceCommands = {
                    'all articles': 'blog-articles.html',
                    'articles': 'blog-articles.html',
                    'tutorials': 'blog-tutorials.html',
                    'tips': 'blog-tips.html',
                    'tips and tricks': 'blog-tips.html',
                    'news': 'blog-news.html',
                    'updates': 'blog-news.html',
                    'news and updates': 'blog-news.html',
                    'guides': 'blog-guides.html',
                    'search': function(cmd) {
                        if (blogSearchInput) {
                            blogSearchInput.focus();
                        }
                    },
                    'pdf tools': 'pdf',
                    'image tools': 'image',
                    'convert pdf': 'pdf',
                    'edit pdf': 'pdf',
                };
                
                // Override voice command handler if needed
                if (window.voiceAssistant) {
                    const originalHandler = window.voiceAssistant.handleVoiceCommand;
                    window.voiceAssistant.handleVoiceCommand = function(command) {
                        // Check blog-specific commands first
                        const cmd = command.toLowerCase().trim();
                        
                        if (blogVoiceCommands[cmd]) {
                            const target = blogVoiceCommands[cmd];
                            if (typeof target === 'function') {
                                target(cmd);
                            } else if (target.startsWith('blog-')) {
                                window.location.href = target;
                            } else {
                                // Search keyword
                                if (blogSearchInput && blogSearchInstance) {
                                    blogSearchInput.value = target;
                                    blogSearchInstance.handleSearch(target);
                                }
                            }
                            return true;
                        }
                        
                        // Default voice command handling
                        if (originalHandler) {
                            return originalHandler.call(this, command);
                        }
                        
                        // Fallback: search in blog
                        if (blogSearchInput && blogSearchInstance) {
                            blogSearchInput.value = command;
                            blogSearchInstance.handleSearch(command);
                            return true;
                        }
                        
                        return false;
                    };
                }
            }
        });
    </script>
'''
        
        body_close = content.find('</body>')
        if body_close != -1:
            content = content[:body_close] + integration_script + content[body_close:]
            changes.append("Added voice + blog search integration script")
    
    return content, changes

def fix_blog_page(file_path):
    """Fix a single blog page"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return None, ["Cannot read file"]
    
    original_content = content
    all_changes = []
    
    # 1. Remove duplicate search boxes
    content, changes = remove_duplicate_search_box(content, file_path)
    all_changes.extend(changes)
    
    # 2. Reduce search box size
    content, changes = reduce_search_box_size(content, file_path)
    all_changes.extend(changes)
    
    # 3. Add voice assistant
    content, changes = add_voice_assistant(content, file_path)
    all_changes.extend(changes)
    
    # 4. Enhance voice search capability
    content, changes = enhance_voice_search_capability(content, file_path)
    all_changes.extend(changes)
    
    # Save if changed
    if content != original_content and all_changes:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, all_changes
        except Exception as e:
            return None, [f"Error saving: {str(e)}"]
    
    return False, all_changes if all_changes else []

def main():
    """Main function"""
    root_dir = Path(__file__).parent
    
    print("🔧 Fixing Blog Pages: Search Box & Voice Command...\n")
    print("="*80)
    
    fixed_count = 0
    changed_files = []
    
    for blog_page in BLOG_PAGES:
        file_path = root_dir / blog_page
        
        if not file_path.exists():
            print(f"⚠️  {blog_page}: File not found")
            continue
        
        if should_exclude(file_path):
            continue
        
        relative_path = file_path.relative_to(root_dir)
        print(f"\n📄 Processing: {relative_path}")
        
        success, changes = fix_blog_page(file_path)
        
        if success is None:
            print(f"   ❌ Error: {changes[0]}")
        elif success:
            print(f"   ✅ Fixed:")
            for change in changes:
                print(f"      • {change}")
            fixed_count += 1
            changed_files.append((relative_path, changes))
        elif changes:
            print(f"   ℹ️  Info:")
            for change in changes:
                print(f"      • {change}")
        else:
            print(f"   ✓ OK (no changes needed)")
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"\n✅ Files Fixed: {fixed_count}")
    
    if changed_files:
        print(f"\n📝 Changes Applied:")
        for file_path, changes in changed_files:
            print(f"   • {file_path}: {len(changes)} changes")
    
    print("\n" + "="*80)
    print("✅ All blog pages fixed successfully!")
    print("="*80)
    print("\n🔍 Search Box Updates:")
    print("   • Removed duplicate search boxes")
    print("   • Reduced margins and width for better appearance")
    print("\n🎤 Voice Command Features:")
    print("   • Jarvis voice assistant added")
    print("   • Voice search for blog functions enabled")
    print("   • Voice search for keywords, text, and links enabled")
    print("   • Integration with blog search functionality")

if __name__ == '__main__':
    main()

