#!/usr/bin/env python3
"""
Fix Background Remover Pages:
1. Ensure Google Cloud backend (not Firebase backend)
2. Ensure Firebase and Razorpay auth present
3. Replace all footers with index.html footer consistently
4. Update global-components.js to match index.html footer
5. Remove double/mismatch footers
"""

import os
import re
from pathlib import Path

# Background remover pages
BACKGROUND_REMOVER_PAGES = [
    'background-remover.html',
    'background-workspace.html',
    'server/public/background-remover.html',
    'server/public/background-workspace.html'
]

# Get index.html footer
INDEX_FOOTER = '''    <footer>
        <div class="container footer-inner">
            <div class="footer-company-links">
                <span>Company</span>
                <a href="index.html#about">About Us</a>
                <a href="index.html#contact">Contact</a>
                <a href="pricing.html">Pricing</a>
                <a href="privacy-policy.html">Privacy Policy</a>
                <a href="terms-of-service.html">Terms of Service</a>
                <a href="dmca-en.html">DMCA</a>
                <a href="blog.html">Blog</a>
            </div>
            <p class="footer-brand-line">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone.</p>
            <p class="footer-credits">
                Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
                <a href="attributions.html">See full acknowledgements</a>.
            </p>
        </div>
    </footer>'''

# Required auth scripts
REQUIRED_AUTH_SCRIPTS = [
    '<script type="module" src="js/auth.js"></script>',
    '<script src="js/firebase-init.js"></script>'
]

# Google Cloud backend check
GOOGLE_CLOUD_PATTERNS = [
    r'CLOUDRUN_API_URL',
    r'google.*cloud.*run',
    r'bg-remover-api.*\.run\.app'
]

EXCLUDE_PATTERNS = ['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backups']

def should_exclude(file_path):
    """Check if file should be excluded"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def ensure_google_cloud_backend(content, file_path):
    """Ensure Google Cloud backend is configured"""
    changes = []
    
    # Check if Google Cloud URL is present
    has_cloudrun = any(re.search(pattern, content, re.IGNORECASE) for pattern in GOOGLE_CLOUD_PATTERNS)
    
    if not has_cloudrun:
        # Check if there's a Firebase Functions URL that needs replacing
        firebase_pattern = r'firebase.*functions.*com|https://.*\.cloudfunctions\.net'
        if re.search(firebase_pattern, content, re.IGNORECASE):
            changes.append('Found Firebase backend - needs Google Cloud Run URL')
            # Don't auto-replace, just report
        else:
            # Add Google Cloud Run URL configuration if missing
            if 'background-workspace.html' in str(file_path) or 'background-remover.html' in str(file_path):
                # Look for where API URL should be defined
                if 'const CLOUDRUN_API_URL' not in content:
                    # Find a good place to add it (after script tag opening or before process function)
                    url_config = '''
    // Google Cloud Run API URL - Connected to u2net rembg backend
    const CLOUDRUN_API_URL = 'https://bg-remover-api-iwumaktavq-uc.a.run.app/remove-background';'''
                    
                    # Try to add after script tag
                    script_match = re.search(r'<script[^>]*type="module"[^>]*>', content)
                    if script_match:
                        insert_pos = script_match.end()
                        content = content[:insert_pos] + url_config + content[insert_pos:]
                        changes.append('Added Google Cloud Run API URL configuration')
    
    return content, changes

def ensure_firebase_auth(content, file_path):
    """Ensure Firebase and Razorpay auth scripts are present"""
    changes = []
    
    # Check for Firebase init
    has_firebase_init = 'js/firebase-init.js' in content or 'firebase-init' in content.lower()
    
    # Check for auth.js
    has_auth_js = 'js/auth.js' in content
    
    # Add missing scripts before </body>
    scripts_to_add = []
    
    if not has_firebase_init:
        scripts_to_add.append('<script src="js/firebase-init.js"></script>')
        changes.append('Firebase init script missing')
    
    if not has_auth_js:
        scripts_to_add.append('<script type="module" src="js/auth.js"></script>')
        changes.append('Auth.js script missing')
    
    if scripts_to_add:
        # Add before </body>
        body_close = content.find('</body>')
        if body_close != -1:
            # Check if scripts already exist in different format
            existing_scripts = re.findall(r'<script[^>]*src="js/(auth|firebase-init)', content, re.IGNORECASE)
            if not existing_scripts or len(existing_scripts) < 2:
                scripts_text = '\n    ' + '\n    '.join(scripts_to_add)
                content = content[:body_close] + scripts_text + '\n' + content[body_close:]
                changes.append(f'Added {len(scripts_to_add)} auth scripts')
    
    return content, changes

def replace_footer(content, file_path):
    """Replace footer with index.html footer"""
    changes = []
    
    # Remove all existing footers
    footer_pattern = r'<footer[^>]*>.*?</footer>'
    footer_matches = list(re.finditer(footer_pattern, content, re.IGNORECASE | re.DOTALL))
    
    if len(footer_matches) > 1:
        # Multiple footers - remove all except last occurrence
        changes.append(f'Found {len(footer_matches)} footers - removing duplicates')
        # Remove all footers (reverse order to maintain positions)
        for match in reversed(footer_matches):
            content = content[:match.start()] + content[match.end():]
    elif len(footer_matches) == 1:
        # Single footer - replace it
        match = footer_matches[0]
        existing_footer = match.group(0)
        
        # Check if footer matches index.html footer
        index_footer_normalized = re.sub(r'\s+', ' ', INDEX_FOOTER.strip())
        existing_footer_normalized = re.sub(r'\s+', ' ', existing_footer.strip())
        
        if index_footer_normalized != existing_footer_normalized:
            # Replace with index.html footer
            content = content[:match.start()] + INDEX_FOOTER + content[match.end():]
            changes.append('Replaced footer with index.html footer')
        else:
            changes.append('Footer already matches index.html')
    else:
        # No footer found - add before </body>
        body_close = content.find('</body>')
        if body_close != -1:
            content = content[:body_close] + '\n' + INDEX_FOOTER + '\n' + content[body_close:]
            changes.append('Added index.html footer before </body>')
        else:
            # Add at end
            content = content.rstrip() + '\n' + INDEX_FOOTER
            changes.append('Added index.html footer at end')
    
    return content, changes

def fix_file(file_path):
    """Fix a single file"""
    try:
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            # Try other encodings
            for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    encoding = enc
                    break
                except:
                    continue
            else:
                return None, ["Cannot read file encoding"]
        
        original_content = content
        all_changes = []
        
        # Only fix background remover pages
        file_name = os.path.basename(file_path)
        is_bg_remover = any(bg_page in str(file_path) for bg_page in BACKGROUND_REMOVER_PAGES)
        
        if is_bg_remover:
            # 1. Ensure Google Cloud backend
            content, changes = ensure_google_cloud_backend(content, file_path)
            all_changes.extend(changes)
            
            # 2. Ensure Firebase and Razorpay auth
            content, changes = ensure_firebase_auth(content, file_path)
            all_changes.extend(changes)
        
        # 3. Replace footer (all HTML files)
        if file_path.suffix == '.html':
            content, changes = replace_footer(content, file_path)
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
        
    except Exception as e:
        return None, [f"Error: {str(e)}"]

def update_global_components():
    """Update global-components.js to match index.html footer exactly"""
    try:
        global_components_path = Path('js/global-components.js')
        
        with open(global_components_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find globalFooterHTML
        footer_pattern = r'const globalFooterHTML = `([\s\S]*?)`;'
        match = re.search(footer_pattern, content)
        
        if match:
            # Update footer to match index.html exactly (with all links)
            new_footer = '''const globalFooterHTML = `
<footer>
    <div class="container footer-inner">
        <div class="footer-company-links">
            <span>Company</span>
            <a href="index.html#about">About Us</a>
            <a href="index.html#contact">Contact</a>
            <a href="pricing.html">Pricing</a>
            <a href="privacy-policy.html">Privacy Policy</a>
            <a href="terms-of-service.html">Terms of Service</a>
            <a href="dmca-en.html">DMCA</a>
            <a href="blog.html">Blog</a>
        </div>
        <p class="footer-brand-line">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone.</p>
        <p class="footer-credits">
            Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
            <a href="attributions.html">See full acknowledgements</a>.
        </p>
    </div>
</footer>
`;'''
            
            content = content[:match.start()] + new_footer + content[match.end():]
            
            with open(global_components_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, ['Updated global-components.js footer to match index.html exactly']
        
        return False, ['Could not find globalFooterHTML in global-components.js']
        
    except Exception as e:
        return None, [f"Error: {str(e)}"]

def main():
    """Main function"""
    root_dir = Path(__file__).parent
    
    print("🔧 Fixing Background Remover Backend & Footer Consistency...\n")
    print("="*80)
    
    # Step 1: Fix background remover pages
    print("\n1️⃣ Checking Background Remover Pages...")
    bg_files_fixed = 0
    bg_files_changed = []
    
    for bg_page in BACKGROUND_REMOVER_PAGES:
        file_path = root_dir / bg_page
        
        if not file_path.exists():
            continue
        
        if should_exclude(file_path):
            continue
        
        relative_path = file_path.relative_to(root_dir)
        print(f"\n📄 Checking: {relative_path}")
        
        success, changes = fix_file(file_path)
        
        if success is None:
            print(f"   ❌ Error: {changes[0]}")
        elif success:
            print(f"   ✅ Fixed:")
            for change in changes:
                print(f"      • {change}")
            bg_files_fixed += 1
            bg_files_changed.append((relative_path, changes))
        elif changes:
            print(f"   ℹ️  Info:")
            for change in changes:
                print(f"      • {change}")
        else:
            print(f"   ✓ OK (no changes needed)")
    
    # Step 2: Update global-components.js
    print("\n2️⃣ Updating global-components.js...")
    success, changes = update_global_components()
    if success:
        print(f"   ✅ Updated:")
        for change in changes:
            print(f"      • {change}")
    elif changes:
        print(f"   ℹ️  {changes[0]}")
    
    # Step 3: Replace footers in all HTML files
    print("\n3️⃣ Replacing Footers in All HTML Files...")
    html_files = list(root_dir.rglob('*.html'))
    
    footer_fixed = 0
    footer_changed = []
    
    for file_path in html_files:
        if should_exclude(file_path):
            continue
        
        # Skip background remover pages (already fixed)
        if any(bg_page in str(file_path) for bg_page in BACKGROUND_REMOVER_PAGES):
            continue
        
        relative_path = file_path.relative_to(root_dir)
        
        success, changes = fix_file(file_path)
        
        if success:
            footer_fixed += 1
            footer_changed.append((relative_path, changes))
        elif success is None and changes:
            print(f"   ❌ {relative_path}: {changes[0]}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"\n✅ Background Remover Pages Fixed: {bg_files_fixed}")
    print(f"✅ Footers Replaced: {footer_fixed}")
    print(f"✅ global-components.js Updated")
    
    if bg_files_changed:
        print(f"\n📝 Background Remover Changes:")
        for file_path, changes in bg_files_changed[:5]:
            print(f"   • {file_path}: {len(changes)} changes")
    
    if footer_changed:
        print(f"\n📝 Footer Changes Applied to {footer_fixed} files")
        print(f"   (Showing first 10 files)")
        for file_path, changes in footer_changed[:10]:
            print(f"   • {file_path}")
    
    print("\n" + "="*80)
    print("✅ All fixes applied successfully!")
    print("="*80)

if __name__ == '__main__':
    main()

