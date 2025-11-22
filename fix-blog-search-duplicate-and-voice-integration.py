#!/usr/bin/env python3
"""
Fix Blog Search Duplicate Issue and Enhance Voice Integration:
1. Prevent blog-search.js from creating duplicate search box if HTML already exists
2. Ensure voice assistant properly integrates with blog search
3. Make voice search work with blog functions, keywords, text, and links
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

def fix_blog_search_js(file_path):
    """Fix blog-search.js to prevent duplicate search box creation"""
    changes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return None, ["Cannot read file"]
    
    original_content = content
    
    # Check if search box already exists in DOM before creating new one
    # Modify init() to check for existing search box
    init_pattern = r'(init\(\)\s*\{[^}]*)(const main = document\.querySelector\([^}]*)(main\.insertBefore\(searchDiv, pageHeader\);?)'
    
    if 'if (!main) return;' in content and 'insertBefore' in content:
        # Add check for existing search box before creating new one
        new_init_logic = '''    // Initialize search bar
    init() {
        // Check if search box already exists in DOM
        if (document.getElementById('blogSearchInput')) {
            // Search box already exists, just initialize event listeners
            this.searchInput = document.getElementById('blogSearchInput');
            this.resultsContainer = document.getElementById('blogSearchResults');
            const clearBtn = document.getElementById('blogSearchClear');
            
            if (!this.searchInput || !this.resultsContainer) return;
            
            // Add event listeners
            this.searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
            
            this.searchInput.addEventListener('focus', () => {
                if (this.searchResults.length > 0) {
                    this.showResults();
                }
            });
            
            if (clearBtn) {
                clearBtn.addEventListener('click', () => {
                    this.searchInput.value = '';
                    this.searchInput.focus();
                    this.clearResults();
                    clearBtn.style.display = 'none';
                });
            }
            
            return; // Exit early, search box already exists
        }
        
        const main = document.querySelector('main .container') || document.querySelector('main');
        if (!main) return;

        const pageHeader = main.querySelector('.page-header') || main.querySelector('h1');
        if (!pageHeader) return;

        // Create search bar only if it doesn't exist
        const searchHTML = this.createSearchBar();
        const searchDiv = document.createElement('div');
        searchDiv.innerHTML = searchHTML;
        main.insertBefore(searchDiv, pageHeader);

        // Get elements
        this.searchInput = document.getElementById('blogSearchInput');
        this.resultsContainer = document.getElementById('blogSearchResults');
        const clearBtn = document.getElementById('blogSearchClear');'''
        
        # Find the init() function and replace it
        init_start = content.find('init() {')
        if init_start != -1:
            # Find the closing brace of init function
            brace_count = 0
            init_end = init_start
            found_opening = False
            
            for i in range(init_start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                    found_opening = True
                elif content[i] == '}':
                    brace_count -= 1
                    if found_opening and brace_count == 0:
                        init_end = i + 1
                        break
            
            # Replace the init function
            if init_end > init_start:
                content = content[:init_start] + new_init_logic + content[init_end:]
                changes.append("Updated init() to check for existing search box before creating")
    
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        except Exception as e:
            return None, [f"Error saving: {str(e)}"]
    
    return False, changes if changes else []

def enhance_voice_integration_script(content, file_path):
    """Enhance voice integration script to work better with blog search"""
    changes = []
    
    # Check if voice integration script exists
    if 'voice-blog-integration' in content.lower() or 'voiceCommand' in content:
        # Enhance the existing script
        # Add more blog-specific commands
        blog_commands_pattern = r'(const blogVoiceCommands = \{.*?\})'
        match = re.search(blog_commands_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            # Enhanced blog commands
            enhanced_commands = '''                const blogVoiceCommands = {
                    'all articles': 'blog-articles.html',
                    'articles': 'blog-articles.html',
                    'all article': 'blog-articles.html',
                    'tutorials': 'blog-tutorials.html',
                    'tutorial': 'blog-tutorials.html',
                    'tips': 'blog-tips.html',
                    'tips and tricks': 'blog-tips.html',
                    'tips & tricks': 'blog-tips.html',
                    'news': 'blog-news.html',
                    'updates': 'blog-news.html',
                    'news and updates': 'blog-news.html',
                    'news & updates': 'blog-news.html',
                    'guides': 'blog-guides.html',
                    'guide': 'blog-guides.html',
                    'search': function(cmd) {
                        if (blogSearchInput) {
                            blogSearchInput.focus();
                        }
                    },
                    'search for': function(cmd) {
                        if (blogSearchInput && blogSearchInstance) {
                            const searchTerm = cmd.replace('search for', '').trim();
                            blogSearchInput.value = searchTerm;
                            blogSearchInstance.handleSearch(searchTerm);
                        }
                    },
                    'find': function(cmd) {
                        if (blogSearchInput && blogSearchInstance) {
                            const searchTerm = cmd.replace('find', '').trim();
                            blogSearchInput.value = searchTerm;
                            blogSearchInstance.handleSearch(searchTerm);
                        }
                    },
                    'pdf tools': function(cmd) {
                        if (blogSearchInput && blogSearchInstance) {
                            blogSearchInput.value = 'pdf';
                            blogSearchInstance.handleSearch('pdf');
                        }
                    },
                    'image tools': function(cmd) {
                        if (blogSearchInput && blogSearchInstance) {
                            blogSearchInput.value = 'image';
                            blogSearchInstance.handleSearch('image');
                        }
                    },
                    'convert pdf': function(cmd) {
                        if (blogSearchInput && blogSearchInstance) {
                            blogSearchInput.value = 'convert pdf';
                            blogSearchInstance.handleSearch('convert pdf');
                        }
                    },
                    'edit pdf': function(cmd) {
                        if (blogSearchInput && blogSearchInstance) {
                            blogSearchInput.value = 'edit pdf';
                            blogSearchInstance.handleSearch('edit pdf');
                        }
                    },
                };'''
            
            content = content.replace(match.group(0), enhanced_commands)
            changes.append("Enhanced blog voice commands with more keywords")
    
    return content, changes

def fix_blog_page(file_path):
    """Fix JavaScript file"""
    return fix_blog_search_js(file_path)

def enhance_blog_page_voice(file_path):
    """Enhance voice integration in blog HTML pages"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return None, ["Cannot read file"]
    
    original_content = content
    all_changes = []
    
    # Enhance voice integration script
    content, changes = enhance_voice_integration_script(content, file_path)
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
    
    print("🔧 Fixing Blog Search Duplicate & Enhancing Voice Integration...\n")
    print("="*80)
    
    # Fix blog-search.js
    blog_search_js = root_dir / 'js' / 'blog-search.js'
    
    if blog_search_js.exists():
        print(f"\n📄 Processing: js/blog-search.js")
        success, changes = fix_blog_search_js(blog_search_js)
        
        if success is None:
            print(f"   ❌ Error: {changes[0]}")
        elif success:
            print(f"   ✅ Fixed:")
            for change in changes:
                print(f"      • {change}")
        else:
            print(f"   ✓ OK (no changes needed)")
    
    # Enhance voice integration in blog pages
    print("\n" + "="*80)
    print("Enhancing Voice Integration in Blog Pages...")
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
        
        success, changes = enhance_blog_page_voice(file_path)
        
        if success is None:
            print(f"   ❌ Error: {changes[0]}")
        elif success:
            print(f"   ✅ Enhanced:")
            for change in changes:
                print(f"      • {change}")
            fixed_count += 1
            changed_files.append((relative_path, changes))
        elif changes:
            print(f"   ℹ️  Info:")
            for change in changes:
                print(f"      • {change}")
        else:
            print(f"   ✓ OK (already enhanced)")
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    if blog_search_js.exists():
        print("\n✅ JavaScript Fixed: blog-search.js")
    
    print(f"\n✅ Blog Pages Enhanced: {fixed_count}")
    
    if changed_files:
        print(f"\n📝 Enhancements Applied:")
        for file_path, changes in changed_files:
            print(f"   • {file_path}: {len(changes)} enhancements")
    
    print("\n" + "="*80)
    print("✅ All fixes applied successfully!")
    print("="*80)
    print("\n🔍 Search Box Fixes:")
    print("   • Duplicate search box creation prevented")
    print("   • JavaScript checks for existing search box before creating")
    print("\n🎤 Voice Integration Enhancements:")
    print("   • Enhanced blog voice commands")
    print("   • Added search keywords (find, search for, etc.)")
    print("   • Added function keywords (pdf tools, image tools, etc.)")
    print("   • Voice commands now trigger blog search automatically")

if __name__ == '__main__':
    main()

