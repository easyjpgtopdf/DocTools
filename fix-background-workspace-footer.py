#!/usr/bin/env python3
"""
Fix background-workspace.html footer to match index.html exactly
"""

from pathlib import Path

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

file_path = Path('background-workspace.html')

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find footer section
    import re
    footer_pattern = r'<footer[^>]*>.*?</footer>'
    footer_match = re.search(footer_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if footer_match:
        # Replace footer
        content = content[:footer_match.start()] + INDEX_FOOTER + content[footer_match.end():]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed background-workspace.html footer")
        print(f"   Added: Pricing, DMCA, Blog links")
    else:
        print("⚠️ Footer not found in background-workspace.html")
        
except Exception as e:
    print(f"❌ Error: {e}")

