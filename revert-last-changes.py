#!/usr/bin/env python3
"""
Revert Last Applied Changes
- Revert footer replacements
- Revert critical coding fixes
- Restore files to previous state
"""

import os
import subprocess
from pathlib import Path

def check_git_available():
    """Check if git is available"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def revert_with_git():
    """Revert changes using git"""
    try:
        # Get list of modified HTML files
        result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
        if result.returncode != 0:
            return False
        
        modified_files = []
        for line in result.stdout.split('\n'):
            if line.startswith(' M') or line.startswith('M '):
                file_path = line[3:].strip()
                if file_path.endswith('.html'):
                    modified_files.append(file_path)
        
        if not modified_files:
            print("No modified HTML files found")
            return False
        
        print(f"📋 Found {len(modified_files)} modified HTML files")
        print("\n⚠️  WARNING: This will revert all changes to HTML files!")
        print("   Do you want to continue? (This action cannot be undone)")
        
        # Revert all HTML files
        for file_path in modified_files:
            try:
                subprocess.run(['git', 'checkout', '--', file_path], check=True)
                print(f"✅ Reverted: {file_path}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to revert: {file_path}")
        
        # Also revert JS and CSS files if modified
        for ext in ['.js', '.css']:
            result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if (line.startswith(' M') or line.startswith('M ')) and line.endswith(ext):
                    file_path = line[3:].strip()
                    try:
                        subprocess.run(['git', 'checkout', '--', file_path], check=True)
                        print(f"✅ Reverted: {file_path}")
                    except:
                        pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error reverting with git: {e}")
        return False

def main():
    """Main function"""
    print("🔄 Reverting last applied changes...\n")
    print("="*80)
    
    # Check if git is available
    if check_git_available():
        print("✅ Git is available - using git to revert changes\n")
        
        # Check if we're in a git repository
        if not Path('.git').exists():
            print("⚠️  Not a git repository - cannot use git revert")
            print("   Please manually restore files from backup")
            return
        
        # Revert changes
        if revert_with_git():
            print("\n" + "="*80)
            print("✅ Successfully reverted all changes using git!")
            print("="*80)
        else:
            print("\n⚠️  Could not revert all files with git")
            print("   Some files may need manual restoration")
    else:
        print("❌ Git is not available")
        print("   Cannot automatically revert changes")
        print("   Please restore files manually from backup")

if __name__ == '__main__':
    main()

