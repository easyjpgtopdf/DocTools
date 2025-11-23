#!/usr/bin/env python3
"""
Fix Firebase Version Mismatch - Update all pages from 10.12.2 to 10.14.0
Ensures consistency across all files
"""

import os
import re
import glob

# Firebase version to update from and to
OLD_VERSION = "10.12.2"
NEW_VERSION = "10.14.0"

# Files to update
FILES_TO_UPDATE = [
    "index.html",
    "blog-*.html"
]

def update_firebase_version_in_file(file_path):
    """Update Firebase version in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace all occurrences of old Firebase version
        content = content.replace(
            f"firebasejs/{OLD_VERSION}",
            f"firebasejs/{NEW_VERSION}"
        )
        
        # Check if any changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all files"""
    print("🔄 Updating Firebase versions from 10.12.2 to 10.14.0...\n")
    
    updated_files = []
    
    # Update index.html
    if os.path.exists("index.html"):
        if update_firebase_version_in_file("index.html"):
            updated_files.append("index.html")
            print(f"✅ Updated: index.html")
    
    # Update all blog HTML files
    blog_files = glob.glob("blog-*.html")
    for blog_file in blog_files:
        if update_firebase_version_in_file(blog_file):
            updated_files.append(blog_file)
            print(f"✅ Updated: {blog_file}")
    
    print(f"\n📊 Summary:")
    print(f"   Total files updated: {len(updated_files)}")
    
    if updated_files:
        print(f"\n✅ Successfully updated Firebase version in {len(updated_files)} file(s)")
    else:
        print(f"\nℹ️  No files needed updating (all already at version {NEW_VERSION})")

if __name__ == "__main__":
    main()

