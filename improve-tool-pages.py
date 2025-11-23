#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool Pages Improvement Script
Adds FAQ, How-to guides, and explanatory content to tool pages
"""

import os
import re
from pathlib import Path

# Tool page mappings
TOOL_PAGES = {
    'jpg-to-pdf.html': {
        'name': 'JPG to PDF Converter',
        'description': 'Convert JPG images to PDF documents quickly and easily. Merge multiple images into a single PDF file.',
        'faq_type': 'convert',
        'how_to_steps': [
            'Click the "Choose Files" button or drag and drop your JPG images',
            'Select one or multiple JPG images from your device',
            'Wait for the upload and conversion process to complete',
            'Preview your PDF and click "Download" to save it',
            'Your PDF is ready to use!'
        ],
        'related_tools': ['pdf-to-jpg.html', 'word-to-pdf.html', 'compress-pdf.html']
    },
    'word-to-pdf.html': {
        'name': 'Word to PDF Converter',
        'description': 'Convert Word documents (DOC, DOCX) to PDF format while preserving formatting and layout.',
        'faq_type': 'convert',
        'how_to_steps': [
            'Upload your Word document using the file picker',
            'Our system will automatically convert it to PDF',
            'Preview the converted PDF to ensure quality',
            'Download your PDF file instantly',
            'Share or print your PDF as needed'
        ],
        'related_tools': ['pdf-to-word.html', 'excel-to-pdf.html', 'edit-pdf.html']
    },
    'pdf-to-word.html': {
        'name': 'PDF to Word Converter',
        'description': 'Convert PDF files to editable Word documents. Extract text and maintain formatting.',
        'faq_type': 'convert',
        'how_to_steps': [
            'Upload your PDF file (up to 10MB for free users)',
            'Wait for the OCR and conversion process',
            'Review the converted Word document',
            'Download and edit in Microsoft Word or Google Docs',
            'Make changes and save your document'
        ],
        'related_tools': ['word-to-pdf.html', 'pdf-to-excel.html', 'edit-pdf.html']
    },
    'merge-pdf.html': {
        'name': 'PDF Merger',
        'description': 'Merge multiple PDF files into one document. Combine PDFs in any order you want.',
        'faq_type': 'edit',
        'how_to_steps': [
            'Upload multiple PDF files using the file picker',
            'Arrange files in your desired order',
            'Click "Merge PDFs" to combine them',
            'Preview the merged PDF',
            'Download your combined PDF file'
        ],
        'related_tools': ['split-pdf.html', 'compress-pdf.html', 'edit-pdf.html']
    },
    'split-pdf.html': {
        'name': 'PDF Splitter',
        'description': 'Split PDF files into multiple documents. Extract specific pages or divide by page ranges.',
        'faq_type': 'edit',
        'how_to_steps': [
            'Upload the PDF file you want to split',
            'Choose pages to extract or set page ranges',
            'Select split method (by pages, by range, or extract all)',
            'Click "Split PDF" to process',
            'Download individual PDF files'
        ],
        'related_tools': ['merge-pdf.html', 'crop-pdf.html', 'edit-pdf.html']
    },
    'compress-pdf.html': {
        'name': 'PDF Compressor',
        'description': 'Reduce PDF file size without losing quality. Compress large PDFs for easy sharing.',
        'faq_type': 'edit',
        'how_to_steps': [
            'Upload your PDF file (large files are supported)',
            'Choose compression level (low, medium, high)',
            'Click "Compress PDF" to start processing',
            'Preview the compressed file size',
            'Download your optimized PDF'
        ],
        'related_tools': ['image-compressor.html', 'merge-pdf.html', 'edit-pdf.html']
    },
    'edit-pdf.html': {
        'name': 'PDF Editor',
        'description': 'Edit PDF documents online. Add text, images, annotations, and modify content.',
        'faq_type': 'edit',
        'how_to_steps': [
            'Upload the PDF file you want to edit',
            'Use the editing tools to add or modify content',
            'Add text, images, shapes, or annotations',
            'Preview your changes in real-time',
            'Download your edited PDF'
        ],
        'related_tools': ['watermark-pdf.html', 'protect-pdf.html', 'add-page-numbers.html']
    },
    'image-compressor.html': {
        'name': 'Image Compressor',
        'description': 'Compress images to reduce file size. Maintain quality while optimizing for web or storage.',
        'faq_type': 'image',
        'how_to_steps': [
            'Upload one or multiple images',
            'Select compression quality (high, medium, low)',
            'Choose output format (JPG, PNG, WebP)',
            'Click "Compress Images" to process',
            'Download your optimized images'
        ],
        'related_tools': ['image-resizer.html', 'compress-pdf.html', 'image-editor.html']
    },
    'image-resizer.html': {
        'name': 'Image Resizer',
        'description': 'Resize images to any dimensions. Change image size while maintaining aspect ratio.',
        'faq_type': 'image',
        'how_to_steps': [
            'Upload your image file',
            'Enter desired width and height (or use presets)',
            'Choose to maintain aspect ratio or custom size',
            'Preview the resized image',
            'Download your resized image'
        ],
        'related_tools': ['image-compressor.html', 'image-editor.html', 'crop-pdf.html']
    },
    'background-remover.html': {
        'name': 'Background Remover',
        'description': 'Remove backgrounds from images automatically. Create transparent PNG images with AI.',
        'faq_type': 'image',
        'how_to_steps': [
            'Upload your image with a background',
            'Wait for AI to detect and remove the background',
            'Preview the result with transparent background',
            'Apply additional styles or colors if needed',
            'Download your image with transparent background'
        ],
        'related_tools': ['image-editor.html', 'image-resizer.html', 'image-compressor.html']
    }
}

FAQ_TEMPLATES = {
    'convert': [
        {'q': 'How accurate is the conversion?', 'a': 'Our conversion tools maintain 99% accuracy, preserving all formatting, fonts, and layout from your original files.'},
        {'q': 'What file sizes are supported?', 'a': 'Free users can convert files up to 10MB. Premium users can process files up to 100MB with faster processing.'},
        {'q': 'Will my data be secure?', 'a': 'Yes, all files are processed securely and automatically deleted after conversion. We never store or share your documents.'},
        {'q': 'Can I convert multiple files at once?', 'a': 'Yes, premium users can convert multiple files simultaneously. Free users can process one file at a time.'},
        {'q': 'What formats are supported?', 'a': 'We support all major file formats. Check the tool page for specific format compatibility.'}
    ],
    'edit': [
        {'q': 'Can I edit PDFs without Adobe?', 'a': 'Yes! Our online PDF editor works in any browser without requiring software installation.'},
        {'q': 'What editing features are available?', 'a': 'You can add text, images, annotations, highlight, draw shapes, and more. All editing is done online.'},
        {'q': 'Will formatting be preserved?', 'a': 'Yes, our editor maintains all original formatting, fonts, and layout while allowing edits.'},
        {'q': 'Can I undo changes?', 'a': 'Yes, our editor includes undo/redo functionality for easy editing.'},
        {'q': 'Is there a file size limit?', 'a': 'Free users can edit PDFs up to 10MB. Premium users can edit files up to 100MB.'}
    ],
    'image': [
        {'q': 'What image formats are supported?', 'a': 'We support JPG, PNG, GIF, BMP, WebP, and all major image formats.'},
        {'q': 'Will image quality be affected?', 'a': 'Our tools are designed to maintain high quality. You can choose quality settings to balance size and quality.'},
        {'q': 'What is the maximum file size?', 'a': 'Free users can upload images up to 10MB. Premium users can process images up to 100MB.'},
        {'q': 'Can I process multiple images?', 'a': 'Yes, premium users can process multiple images simultaneously for batch operations.'},
        {'q': 'Are my images secure?', 'a': 'Yes, all images are processed securely and automatically deleted after processing. We never store your files.'}
    ]
}

def get_tool_info(filename):
    """Get tool information"""
    return TOOL_PAGES.get(filename, {
        'name': filename.replace('.html', '').replace('-', ' ').title(),
        'description': f'Use our {filename.replace(".html", "").replace("-", " ")} tool',
        'faq_type': 'convert',
        'how_to_steps': [
            'Upload your file',
            'Process using our tool',
            'Download the result'
        ],
        'related_tools': []
    })

def add_how_to_guide(content, tool_info):
    """Add How-to guide section"""
    how_to = f'''
    <section class="how-to-guide" style="margin: 40px 0; padding: 40px; background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="font-size: 2rem; color: #4361ee; margin-bottom: 30px; text-align: center;">
            <i class="fas fa-book-open" style="margin-right: 10px;"></i>
            How to Use {tool_info['name']}
        </h2>
        <div class="steps-container" style="max-width: 800px; margin: 0 auto;">
            <ol style="list-style: none; padding: 0; counter-reset: step-counter;">
'''
    
    for i, step in enumerate(tool_info['how_to_steps'], 1):
        how_to += f'''
                <li style="counter-increment: step-counter; margin-bottom: 25px; padding: 20px; background: #f8f9ff; border-radius: 12px; border-left: 4px solid #4361ee; position: relative; padding-left: 60px;">
                    <span style="position: absolute; left: 15px; top: 20px; background: #4361ee; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.1rem;">
                        {i}
                    </span>
                    <p style="font-size: 1.1rem; color: #0b1630; line-height: 1.6; margin: 0;">
                        {step}
                    </p>
                </li>
'''
    
    how_to += '''
            </ol>
        </div>
    </section>
'''
    
    # Add after main tool section, before FAQ
    if 'class="faq-section"' in content:
        content = content.replace('class="faq-section"', how_to + '\n    <section class="faq-section"')
    elif '</main>' in content:
        content = content.replace('</main>', how_to + '</main>')
    elif '<footer' in content:
        content = re.sub(r'(<footer)', how_to + r'\1', content)
    else:
        content = re.sub(r'(</body>)', how_to + r'\1', content)
    
    return content

def add_faq_section(content, faq_type):
    """Add FAQ section"""
    faqs = FAQ_TEMPLATES.get(faq_type, FAQ_TEMPLATES['convert'])
    
    faq_section = '''
    <section class="faq-section" style="margin: 40px 0; padding: 40px; background: #f8f9ff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="font-size: 2rem; color: #4361ee; margin-bottom: 30px; text-align: center;">
            <i class="fas fa-question-circle" style="margin-right: 10px;"></i>
            Frequently Asked Questions
        </h2>
        <div class="faq-container" style="max-width: 800px; margin: 0 auto;">
'''
    
    for i, faq in enumerate(faqs, 1):
        faq_section += f'''
            <div class="faq-item" style="margin-bottom: 20px; padding: 20px; background: white; border-radius: 12px; border-left: 4px solid #4361ee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px; cursor: pointer; display: flex; align-items: center;" onclick="toggleFaq(this)">
                    <i class="fas fa-chevron-right" style="color: #4361ee; margin-right: 10px; transition: transform 0.3s;"></i>
                    {faq['q']}
                </h3>
                <div class="faq-answer" style="font-size: 1rem; color: #56607a; line-height: 1.6; margin-top: 10px; display: none; padding-left: 30px;">
                    {faq['a']}
                </div>
            </div>
'''
    
    faq_section += '''
        </div>
    </section>
    
    <script>
    function toggleFaq(element) {
        const answer = element.nextElementSibling;
        const icon = element.querySelector('i');
        const isOpen = answer.style.display === 'block';
        
        answer.style.display = isOpen ? 'none' : 'block';
        icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(90deg)';
    }
    </script>
'''
    
    # Add before footer or at end
    if '</main>' in content:
        content = content.replace('</main>', faq_section + '</main>')
    elif '<footer' in content:
        content = re.sub(r'(<footer)', faq_section + r'\1', content)
    else:
        content = re.sub(r'(</body>)', faq_section + r'\1', content)
    
    return content

def add_explanatory_content(content, tool_info):
    """Add explanatory content section"""
    explanatory = f'''
    <section class="explanatory-content" style="margin: 40px 0; padding: 40px; background: linear-gradient(135deg, #f8f9ff, #ffffff); border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <div class="container" style="max-width: 900px; margin: 0 auto;">
            <h2 style="font-size: 2rem; color: #4361ee; margin-bottom: 20px; text-align: center;">
                <i class="fas fa-info-circle" style="margin-right: 10px;"></i>
                About {tool_info['name']}
            </h2>
            <div class="content-text" style="font-size: 1.1rem; color: #56607a; line-height: 1.8; text-align: center; margin-bottom: 30px;">
                <p>{tool_info['description']}</p>
            </div>
            
            <div class="features-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px;">
                <div class="feature-item" style="padding: 20px; background: white; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <i class="fas fa-bolt" style="font-size: 2rem; color: #4361ee; margin-bottom: 10px;"></i>
                    <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px;">Fast Processing</h3>
                    <p style="color: #56607a; font-size: 0.95rem;">Process files in seconds with our optimized algorithms</p>
                </div>
                
                <div class="feature-item" style="padding: 20px; background: white; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <i class="fas fa-shield-alt" style="font-size: 2rem; color: #4361ee; margin-bottom: 10px;"></i>
                    <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px;">Secure & Private</h3>
                    <p style="color: #56607a; font-size: 0.95rem;">Your files are processed securely and deleted automatically</p>
                </div>
                
                <div class="feature-item" style="padding: 20px; background: white; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <i class="fas fa-mobile-alt" style="font-size: 2rem; color: #4361ee; margin-bottom: 10px;"></i>
                    <h3 style="font-size: 1.2rem; color: #0b1630; margin-bottom: 10px;">Works Everywhere</h3>
                    <p style="color: #56607a; font-size: 0.95rem;">Use on desktop, tablet, or mobile - no installation needed</p>
                </div>
            </div>
        </div>
    </section>
'''
    
    # Add after main tool, before how-to guide
    if 'class="how-to-guide"' in content:
        content = content.replace('class="how-to-guide"', explanatory + '\n    <section class="how-to-guide"')
    elif '</main>' in content:
        content = content.replace('</main>', explanatory + '</main>')
    else:
        content = re.sub(r'(</body>)', explanatory + r'\1', content)
    
    return content

def add_related_tools(content, related_tools):
    """Add related tools section"""
    if not related_tools:
        return content
    
    related = '''
    <section class="related-tools" style="margin: 40px 0; padding: 40px; background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <h2 style="font-size: 2rem; color: #4361ee; margin-bottom: 30px; text-align: center;">
            <i class="fas fa-tools" style="margin-right: 10px;"></i>
            Related Tools
        </h2>
        <div class="tools-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
'''
    
    for tool in related_tools[:6]:  # Limit to 6
        tool_name = tool.replace('.html', '').replace('-', ' ').title()
        related += f'''
            <a href="{tool}" style="display: block; padding: 20px; background: #f8f9ff; border-radius: 12px; text-decoration: none; text-align: center; transition: transform 0.3s, box-shadow 0.3s; border: 2px solid transparent;" 
               onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 8px 16px rgba(67,97,238,0.2)'; this.style.borderColor='#4361ee';"
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'; this.style.borderColor='transparent';">
                <i class="fas fa-file-alt" style="font-size: 2rem; color: #4361ee; margin-bottom: 10px;"></i>
                <h3 style="font-size: 1.1rem; color: #0b1630; margin: 0;">{tool_name}</h3>
            </a>
'''
    
    related += '''
        </div>
    </section>
'''
    
    # Add before FAQ section
    if 'class="faq-section"' in content:
        content = content.replace('class="faq-section"', related + '\n    <section class="faq-section"')
    elif '</main>' in content:
        content = content.replace('</main>', related + '</main>')
    else:
        content = re.sub(r'(</body>)', related + r'\1', content)
    
    return content

def process_tool_file(filepath):
    """Process a single tool file"""
    print(f'Processing: {filepath}')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        filename = os.path.basename(filepath)
        tool_info = get_tool_info(filename)
        
        # Apply all improvements
        content = add_explanatory_content(content, tool_info)
        content = add_how_to_guide(content, tool_info)
        content = add_faq_section(content, tool_info['faq_type'])
        content = add_related_tools(content, tool_info.get('related_tools', []))
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'✓ Completed: {filename}')
        return True
        
    except Exception as e:
        print(f'✗ Error processing {filepath}: {str(e)}')
        return False

def main():
    """Main function"""
    print('=' * 60)
    print('Tool Pages Improvement Script')
    print('=' * 60)
    print()
    
    # Find all tool files (main tool pages, not convert pages)
    tool_files = []
    tool_patterns = [
        'jpg-to-pdf.html', 'word-to-pdf.html', 'excel-to-pdf.html', 'ppt-to-pdf.html',
        'pdf-to-word.html', 'pdf-to-excel.html', 'pdf-to-ppt.html', 'pdf-to-jpg.html',
        'merge-pdf.html', 'split-pdf.html', 'compress-pdf.html', 'edit-pdf.html',
        'protect-pdf.html', 'unlock-pdf.html', 'watermark-pdf.html', 'crop-pdf.html',
        'add-page-numbers.html', 'image-compressor.html', 'image-resizer.html',
        'image-editor.html', 'background-remover.html', 'image-watermark.html',
        'ocr-image.html', 'resume-maker.html', 'biodata-maker.html', 'marriage-card.html',
        'ai-image-generator.html', 'protect-excel.html'
    ]
    
    for pattern in tool_patterns:
        filepath = Path('.') / pattern
        if filepath.exists():
            tool_files.append(str(filepath))
    
    print(f'Found {len(tool_files)} tool files')
    print()
    
    # Process each file
    success_count = 0
    for tool_file in tool_files:
        if process_tool_file(tool_file):
            success_count += 1
        print()
    
    print('=' * 60)
    print(f'Processing complete: {success_count}/{len(tool_files)} files updated')
    print('=' * 60)

if __name__ == '__main__':
    main()

