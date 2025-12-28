#!/usr/bin/env python3
"""
Update Search Database for Jarvis Voice Command, Footer Search Bar, and Search Page
Scans all HTML files and adds missing pages to search databases
"""

import os
import re
from pathlib import Path

# Pages to exclude from search
EXCLUDED_PAGES = {
    'index.html', 'search.html', 'result.html', 'test-backend-connection.html',
    'get-mongodb-connection.html', 'feedback.html', 'accounts.html', 'about.html',
    'contact.html', 'disclaimer.html', 'dmca.html', 'attributions.html',
    'kyc-support.html', 'payment-method.html', 'payment-receipt.html',
    'shipping-billing.html', 'pricing.html', 'refund-policy.html',
    'terms-of-service.html', 'privacy-policy.html', 'dashboard.html',
    'login.html', 'signup.html', 'blog.html', 'pdf-editor-preview.html',
    'background-workspace.html', 'background-style.html', 'image-editor-result.html',
    'image-resizer-result.html', 'Indian-style-Resume-print.html',
    'generate-bg-removal-animations.html', 'image-repair-editor.html',
    'pdf-to-excel-faq.html', 'pdf-to-excel-convert.html', 'pdf-to-word-converter.html'
}

# Pages that end with -convert.html are excluded
# Blog pages are excluded

def extract_title_from_html(filepath):
    """Extract title from HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Try to find title tag
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            # Clean title - remove site name and extra info
            title = re.sub(r'\s*[-|]\s*easyjpgtopdf.*$', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*[-|]\s*Online.*$', '', title, flags=re.IGNORECASE)
            title = title.strip()
            return title if title else None
            
        # Try to find h1 tag
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
        if h1_match:
            h1_text = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            return h1_text if h1_text else None
            
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return None

def generate_keywords(filename, title):
    """Generate keywords from filename and title"""
    keywords = []
    
    # Add filename-based keywords
    base_name = filename.replace('.html', '').replace('-', ' ')
    keywords.append(base_name.lower())
    
    # Add title words
    if title:
        title_words = re.findall(r'\b\w+\b', title.lower())
        keywords.extend([w for w in title_words if len(w) > 2])
    
    # Add common variations
    if 'pdf' in base_name.lower():
        keywords.extend(['pdf', 'document'])
    if 'image' in base_name.lower() or 'jpg' in base_name.lower() or 'png' in base_name.lower():
        keywords.extend(['image', 'photo', 'picture'])
    if 'convert' in base_name.lower() or 'to' in base_name.lower():
        keywords.append('convert')
    if 'merge' in base_name.lower():
        keywords.extend(['combine', 'join'])
    if 'split' in base_name.lower():
        keywords.extend(['divide', 'separate'])
    if 'compress' in base_name.lower():
        keywords.extend(['reduce', 'shrink', 'optimize'])
    if 'protect' in base_name.lower():
        keywords.extend(['password', 'secure', 'lock'])
    if 'unlock' in base_name.lower():
        keywords.extend(['remove password', 'decrypt', 'open'])
    if 'edit' in base_name.lower():
        keywords.extend(['modify', 'change'])
    if 'crop' in base_name.lower():
        keywords.extend(['trim', 'cut'])
    if 'watermark' in base_name.lower():
        keywords.extend(['logo', 'mark', 'stamp'])
    if 'resize' in base_name.lower():
        keywords.extend(['scale', 'dimension', 'size'])
    if 'remove' in base_name.lower() or 'remover' in base_name.lower():
        keywords.append('delete')
    if 'extract' in base_name.lower() or 'extractor' in base_name.lower():
        keywords.extend(['unzip', 'open', 'extract'])
    if 'zip' in base_name.lower():
        keywords.extend(['archive', 'compressed'])
    if 'rar' in base_name.lower():
        keywords.append('archive')
    if 'ocr' in base_name.lower():
        keywords.extend(['text', 'recognition', 'read'])
    if 'ai' in base_name.lower():
        keywords.extend(['artificial intelligence', 'generate', 'create'])
    if 'resume' in base_name.lower():
        keywords.extend(['cv', 'biodata', 'job'])
    if 'biodata' in base_name.lower():
        keywords.extend(['marriage', 'personal', 'bio'])
    if 'marriage' in base_name.lower():
        keywords.extend(['wedding', 'card', 'invitation'])
    
    # Remove duplicates and return
    return list(dict.fromkeys(keywords))[:15]  # Limit to 15 keywords

def get_category(filename, title):
    """Determine category based on filename and title"""
    filename_lower = filename.lower()
    title_lower = (title or '').lower()
    
    if 'pdf' in filename_lower and ('to' in filename_lower or 'convert' in filename_lower):
        return 'PDF Tools'
    elif 'pdf' in filename_lower:
        return 'PDF Tools'
    elif any(x in filename_lower for x in ['jpg', 'png', 'webp', 'image', 'photo', 'bmp', 'tiff', 'svg', 'ico', 'heic', 'cr2', 'raw', 'psd', 'hdr', 'avif', 'eps', 'ai']):
        return 'Image Tools'
    elif any(x in filename_lower for x in ['excel', 'word', 'ppt', 'powerpoint', 'office']):
        return 'Office Tools'
    elif any(x in filename_lower for x in ['epub', 'mobi', 'azw3', 'fb2', 'txt', 'rtf', 'text']):
        return 'E-book Tools'
    elif any(x in filename_lower for x in ['zip', 'rar', '7z', 'tar', 'iso', 'folder', 'archive', 'extract']):
        return 'Archive Tools'
    elif any(x in filename_lower for x in ['ocr', 'ai', 'background', 'remove', 'enhance', 'repair', 'cropper']):
        return 'AI Tools' if 'ai' in filename_lower else 'Image Tools'
    elif any(x in filename_lower for x in ['resume', 'biodata', 'marriage', 'card']):
        return 'Document Tools'
    else:
        return 'Other Tools'

def get_icon(filename, category):
    """Get Font Awesome icon based on category and filename"""
    filename_lower = filename.lower()
    
    if 'pdf' in filename_lower:
        return 'fas fa-file-pdf'
    elif any(x in filename_lower for x in ['jpg', 'png', 'webp', 'image', 'photo']):
        return 'fas fa-file-image'
    elif 'excel' in filename_lower:
        return 'fas fa-file-excel'
    elif 'word' in filename_lower:
        return 'fas fa-file-word'
    elif 'ppt' in filename_lower or 'powerpoint' in filename_lower:
        return 'fas fa-file-powerpoint'
    elif 'zip' in filename_lower or 'rar' in filename_lower or 'archive' in filename_lower:
        return 'fas fa-file-archive'
    elif 'book' in filename_lower or 'epub' in filename_lower or 'mobi' in filename_lower:
        return 'fas fa-book'
    elif 'lock' in filename_lower or 'protect' in filename_lower:
        return 'fas fa-lock'
    elif 'unlock' in filename_lower:
        return 'fas fa-unlock'
    elif 'edit' in filename_lower:
        return 'fas fa-edit'
    elif 'crop' in filename_lower:
        return 'fas fa-crop'
    elif 'watermark' in filename_lower:
        return 'fas fa-tint'
    elif 'compress' in filename_lower:
        return 'fas fa-compress'
    elif 'merge' in filename_lower:
        return 'fas fa-file-pdf'
    elif 'split' in filename_lower:
        return 'fas fa-file-pdf'
    elif 'ocr' in filename_lower:
        return 'fas fa-eye'
    elif 'ai' in filename_lower:
        return 'fas fa-robot'
    elif 'resize' in filename_lower:
        return 'fas fa-expand-arrows-alt'
    elif 'resume' in filename_lower or 'biodata' in filename_lower:
        return 'fas fa-file-alt'
    elif 'marriage' in filename_lower:
        return 'fas fa-heart'
    elif 'background' in filename_lower or 'remover' in filename_lower:
        return 'fas fa-magic'
    elif 'enhance' in filename_lower or 'repair' in filename_lower:
        return 'fas fa-tools'
    else:
        return 'fas fa-file'

def generate_description(filename, title, category):
    """Generate description based on filename, title, and category"""
    base_name = filename.replace('.html', '').replace('-', ' ')
    
    if 'to' in base_name.lower():
        parts = base_name.lower().split(' to ')
        if len(parts) == 2:
            return f'Convert {parts[0].title()} to {parts[1].title()} online for free'
    
    if 'pdf' in base_name.lower():
        if 'merge' in base_name.lower():
            return 'Combine multiple PDF files into one document'
        elif 'split' in base_name.lower():
            return 'Split PDF file into multiple documents'
        elif 'compress' in base_name.lower():
            return 'Reduce PDF file size without losing quality'
        elif 'protect' in base_name.lower():
            return 'Add password protection to PDF files'
        elif 'unlock' in base_name.lower():
            return 'Remove password protection from PDF files'
        elif 'edit' in base_name.lower():
            return 'Edit PDF documents online'
        elif 'crop' in base_name.lower():
            return 'Crop PDF pages to remove unwanted areas'
        elif 'watermark' in base_name.lower():
            return 'Add watermark to PDF documents'
        elif 'page' in base_name.lower() and 'number' in base_name.lower():
            return 'Add page numbers to PDF documents'
    
    if 'image' in base_name.lower() or 'jpg' in base_name.lower() or 'png' in base_name.lower():
        if 'compress' in base_name.lower():
            return 'Compress images to reduce file size'
        elif 'resize' in base_name.lower():
            return 'Resize images to change dimensions'
        elif 'edit' in base_name.lower():
            return 'Edit images online with professional tools'
        elif 'watermark' in base_name.lower():
            return 'Add watermark to images'
        elif 'crop' in base_name.lower():
            return 'Crop images to remove unwanted areas'
        elif 'repair' in base_name.lower():
            return 'Repair and restore damaged images'
        elif 'enhance' in base_name.lower():
            return 'Enhance image quality and appearance'
        elif 'background' in base_name.lower() or 'remover' in base_name.lower():
            return 'Remove background from images automatically'
        elif 'transparent' in base_name.lower():
            return 'Create transparent background images'
        elif 'exif' in base_name.lower():
            return 'Remove EXIF data from images'
    
    if 'ocr' in base_name.lower():
        return 'Extract text from images using OCR technology'
    
    if 'ai' in base_name.lower() and 'image' in base_name.lower():
        return 'Generate images using AI technology'
    
    if 'resume' in base_name.lower():
        return 'Create professional resume online'
    
    if 'biodata' in base_name.lower():
        return 'Create marriage biodata form online'
    
    if 'marriage' in base_name.lower() and 'card' in base_name.lower():
        return 'Create marriage invitation card online'
    
    if 'extract' in base_name.lower() or 'extractor' in base_name.lower():
        return f'Extract files from {base_name.replace("extractor", "").replace("-", " ").title()} archives'
    
    if 'zip' in base_name.lower() or 'rar' in base_name.lower():
        if 'to' in base_name.lower():
            return f'Convert {base_name.replace(" to ", " to ").title()} archives online'
        else:
            return f'Work with {base_name.replace("-", " ").title()} archives online'
    
    # Default description
    return f'{title or base_name.title()} - Online free tool'

def scan_html_files():
    """Scan all HTML files and generate database entries"""
    pages = []
    
    for filepath in Path('.').glob('*.html'):
        filename = filepath.name
        
        # Skip excluded pages
        if filename in EXCLUDED_PAGES:
            continue
        
        # Skip convert pages
        if filename.endswith('-convert.html'):
            continue
        
        # Skip blog pages
        if filename.startswith('blog-'):
            continue
        
        # Extract title
        title = extract_title_from_html(filepath)
        if not title:
            # Generate title from filename
            title = filename.replace('.html', '').replace('-', ' ').title()
        
        # Generate metadata
        keywords = generate_keywords(filename, title)
        category = get_category(filename, title)
        icon = get_icon(filename, category)
        description = generate_description(filename, title, category)
        
        pages.append({
            'filename': filename,
            'title': title,
            'url': filename,
            'keywords': keywords,
            'category': category,
            'icon': icon,
            'description': description
        })
    
    return sorted(pages, key=lambda x: x['title'])

def format_js_entry(page):
    """Format page entry for JavaScript"""
    keywords_str = ', '.join([f"'{k}'" for k in page['keywords']])
    return f"""        {{ 
            title: '{page['title']}', 
            url: '{page['url']}', 
            keywords: [{keywords_str}], 
            category: '{page['category']}', 
            description: '{page['description']}',
            icon: '{page['icon']}'
        }}"""

def format_voice_entry(page):
    """Format page entry for voice assistant"""
    keywords_str = ', '.join([f"'{k}'" for k in page['keywords']])
    return f"""            {{ 
                title: '{page['title']}', 
                url: '{page['url']}', 
                keywords: [{keywords_str}], 
                category: '{page['category']}', 
                description: '{page['description']}'
            }}"""

def format_search_entry(page):
    """Format page entry for search.html"""
    keywords_str = ' '.join(page['keywords'])
    return f'        {{ title: "{page["title"]}", url: "{page["url"]}", description: "{page["description"]}", type: "Tool", keywords: "{keywords_str}" }},'

if __name__ == '__main__':
    print("Scanning HTML files...")
    pages = scan_html_files()
    print(f"Found {len(pages)} pages to add to search database")
    
    # Save to file for review
    with open('search_database_entries.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SEARCH DATABASE ENTRIES\n")
        f.write("=" * 80 + "\n\n")
        
        for page in pages:
            f.write(f"Title: {page['title']}\n")
            f.write(f"URL: {page['url']}\n")
            f.write(f"Category: {page['category']}\n")
            f.write(f"Description: {page['description']}\n")
            f.write(f"Keywords: {', '.join(page['keywords'])}\n")
            f.write(f"Icon: {page['icon']}\n")
            f.write("-" * 80 + "\n\n")
    
    print(f"\nDatabase entries saved to search_database_entries.txt")
    print(f"\nTotal pages: {len(pages)}")
    print("\nSample entries:")
    for page in pages[:5]:
        print(f"  - {page['title']} ({page['url']})")

