#!/usr/bin/env python3
"""
Create Additional Copyright Protection Files
Creates files for comprehensive copyright protection
"""

import os
from pathlib import Path
from datetime import datetime

current_year = datetime.now().year

# Create COPYRIGHT_NOTICE.txt
copyright_notice = f"""COPYRIGHT NOTICE

© {current_year} easyjpgtopdf — Free PDF & Image Tools for everyone. All rights reserved.

This website and all its content, including but not limited to:
- Source code (HTML, CSS, JavaScript, Python, etc.)
- Designs, graphics, logos, and visual elements
- Documentation, tutorials, and written content
- Software, applications, and tools
- Branding and trademarks

are protected by copyright laws and international intellectual property treaties.

UNAUTHORIZED USE IS PROHIBITED
Any reproduction, distribution, or unauthorized use of any content from this 
website without express written permission is strictly prohibited and may result 
in legal action.

For licensing inquiries: support@easyjpgtopdf.com
Last Updated: {datetime.now().strftime('%Y-%m-%d')}
"""

# Create .gitattributes file for copyright protection
gitattributes = """# Copyright Protection
# Ensure all files maintain copyright information

* text=auto
*.html linguist-detectable=true
*.js linguist-detectable=true
*.css linguist-detectable=true
*.py linguist-detectable=true

# Copyright notices should not be removed
*.html -copyright
*.js -copyright
*.css -copyright
*.py -copyright
"""

# Create NOTICE file (for legal compliance)
notice_file = f"""NOTICE

This software and associated documentation files (the "Software") are 
Copyright © {current_year} easyjpgtopdf. All rights reserved.

The Software includes:

Website Files:
- HTML, CSS, JavaScript source files
- Design files and graphics
- Documentation and content
- Configuration files

Third-Party Components:
- Font Awesome (Icons) - Licensed under Font Awesome Free License
- Google Fonts - Licensed under SIL Open Font License
- jsPDF, pdf.js, pdf-lib - Licensed under Apache 2.0 / MIT
- Other open-source libraries - See attributions.html

Copyright © {current_year} easyjpgtopdf. All rights reserved.

For licensing inquiries, please contact: support@easyjpgtopdf.com
"""

def create_files():
    """Create all copyright protection files"""
    files_created = []
    
    # Create COPYRIGHT_NOTICE.txt
    try:
        with open('COPYRIGHT_NOTICE.txt', 'w', encoding='utf-8') as f:
            f.write(copyright_notice)
        files_created.append('COPYRIGHT_NOTICE.txt')
    except Exception as e:
        print(f"❌ Error creating COPYRIGHT_NOTICE.txt: {e}")
    
    # Create .gitattributes
    try:
        with open('.gitattributes', 'w', encoding='utf-8') as f:
            f.write(gitattributes)
        files_created.append('.gitattributes')
    except Exception as e:
        print(f"❌ Error creating .gitattributes: {e}")
    
    # Create NOTICE
    try:
        with open('NOTICE', 'w', encoding='utf-8') as f:
            f.write(notice_file)
        files_created.append('NOTICE')
    except Exception as e:
        print(f"❌ Error creating NOTICE: {e}")
    
    return files_created

def main():
    """Main function"""
    print("🔧 Creating Additional Copyright Protection Files...\n")
    print("="*80)
    
    files_created = create_files()
    
    print(f"\n✅ Created {len(files_created)} files:")
    for file in files_created:
        print(f"   • {file}")
    
    print("\n" + "="*80)
    print("✅ Additional copyright protection files created!")
    print("="*80)

if __name__ == '__main__':
    main()

