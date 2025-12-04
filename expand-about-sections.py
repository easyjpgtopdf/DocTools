#!/usr/bin/env python3
"""
Script to expand about sections in all tool pages to 400+ keywords with detailed descriptions
"""

import os
import re
from pathlib import Path

# Tool descriptions with 400+ keywords
TOOL_DESCRIPTIONS = {
    'jpg-to-pdf': """Our JPG to PDF converter is a powerful, free online tool that transforms your JPEG and JPG image files into professional PDF documents instantly. Whether you need to convert a single photo or merge multiple images into one comprehensive PDF file, our converter handles it all with precision and speed. This tool is perfect for creating photo albums, document archives, presentations, and portfolios. The converter supports all standard JPG and JPEG formats, maintains high image quality, and allows you to customize page sizes including A4, Letter, Legal, and custom dimensions. You can choose between portrait and landscape orientations, adjust margins, and control image positioning. The conversion process is completely secure - your files are processed in the cloud and automatically deleted after conversion. No registration is required, and there are no watermarks on your converted PDFs. Our advanced algorithms ensure that colors, resolution, and image clarity are preserved throughout the conversion process. The tool works seamlessly on all devices including Windows, Mac, Linux, tablets, and smartphones. Whether you're a student creating study materials, a professional archiving documents, or a photographer organizing portfolios, our JPG to PDF converter provides a reliable, fast, and free solution for all your image to PDF conversion needs.""",
    
    'word-to-pdf': """Our Word to PDF converter is an advanced online tool designed to transform Microsoft Word documents (DOC and DOCX formats) into high-quality PDF files with complete formatting preservation. This professional-grade converter maintains all elements from your original Word document including fonts, images, tables, headers, footers, page breaks, hyperlinks, and styling. Whether you're converting resumes, reports, letters, contracts, or academic papers, our tool ensures that your document looks exactly as intended in PDF format. The conversion process is lightning-fast, typically completing in just a few seconds even for large documents. Our converter supports all Word document versions from older .doc files to the latest .docx format. The tool is completely free to use with no file size limits for basic conversions, and premium users can process even larger files with priority processing. All conversions happen securely in the cloud with SSL encryption, and files are automatically deleted after processing to ensure your privacy. The converted PDFs are compatible with all PDF readers including Adobe Acrobat, web browsers, and mobile PDF apps. No software installation is required - simply upload your Word document and download your PDF instantly. This tool is perfect for professionals, students, businesses, and anyone who needs to share documents in the universal PDF format while maintaining professional appearance and formatting.""",
    
    'excel-to-pdf': """Our Excel to PDF converter is a comprehensive online solution for transforming Microsoft Excel spreadsheets (XLS and XLSX formats) into professional PDF documents while preserving all data, formatting, charts, graphs, and formulas. This powerful tool is essential for accountants, data analysts, business professionals, and students who need to share spreadsheets in a universal format. The converter maintains cell formatting, colors, borders, merged cells, and conditional formatting exactly as they appear in your original Excel file. Charts, graphs, and pivot tables are rendered with precision, ensuring that your data visualizations look professional in the PDF output. The tool supports multiple worksheets, allowing you to convert entire workbooks or select specific sheets. Page orientation, scaling, and print area settings are all preserved during conversion. Our advanced conversion engine handles complex spreadsheets with thousands of rows and columns, maintaining data integrity throughout the process. The conversion is completely free for standard file sizes, with premium options available for larger files and batch processing. All files are processed securely with enterprise-grade encryption, and your data is automatically deleted after conversion to protect your privacy. The tool works on all devices and operating systems - no Microsoft Excel installation required. Whether you're creating financial reports, data analysis documents, inventory lists, or academic spreadsheets, our Excel to PDF converter provides a reliable, fast, and professional solution for all your spreadsheet conversion needs.""",
    
    'ppt-to-pdf': """Our PowerPoint to PDF converter is a professional-grade online tool that transforms Microsoft PowerPoint presentations (PPT and PPTX formats) into high-quality PDF documents while maintaining all slides, animations, transitions, and formatting. This essential tool is perfect for educators, business professionals, students, and anyone who needs to share presentations in a universal format. The converter preserves all slide layouts, backgrounds, fonts, images, charts, tables, and multimedia elements exactly as they appear in your original presentation. Whether you're converting a simple slide deck or a complex presentation with animations and transitions, our tool ensures that every element is accurately rendered in the PDF output. The conversion process supports all PowerPoint versions from older .ppt files to the latest .pptx format with Office 365 compatibility. Our advanced rendering engine maintains slide aspect ratios, handles multiple slide sizes, and preserves speaker notes when needed. The tool is completely free to use with no watermarks, and premium users can process larger files with priority support. All conversions happen securely in the cloud with SSL encryption, and your files are automatically deleted after processing. No software installation is required - simply upload your PowerPoint file and receive your PDF instantly. The converted PDFs are compatible with all PDF readers and can be easily shared via email, cloud storage, or printed for physical distribution. Whether you're archiving presentations, sharing slides with clients, or creating presentation portfolios, our PowerPoint to PDF converter provides a reliable, fast, and professional solution for all your presentation conversion needs.""",
    
    'pdf-to-jpg': """Our PDF to JPG converter is a versatile online tool that extracts images from PDF documents and converts them into high-quality JPEG image files. This powerful converter is perfect for photographers, designers, content creators, and anyone who needs to extract images from PDF files for editing, sharing, or printing purposes. The tool supports all PDF formats including scanned documents, image-based PDFs, and text-based PDFs with embedded graphics. Our advanced extraction engine can convert entire PDF pages into JPG images or extract specific images embedded within PDF documents. The converter maintains high image quality with customizable resolution settings, allowing you to choose between standard quality for web use or high resolution for printing. You can convert single pages or batch convert multiple pages from a PDF document. The tool supports various output formats and quality settings to meet your specific needs. All conversions happen securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks or file size restrictions for basic conversions. Premium users can process larger files with faster processing speeds. No software installation is required - simply upload your PDF and download your JPG images instantly. Whether you're extracting photos from digital magazines, converting PDF pages for social media, or extracting images for design projects, our PDF to JPG converter provides a reliable, fast, and professional solution for all your PDF to image conversion needs.""",
    
    'pdf-to-word': """Our PDF to Word converter is an advanced online tool that transforms PDF documents into editable Microsoft Word files (DOCX format) while preserving formatting, fonts, images, tables, and layout. This professional-grade converter uses advanced OCR (Optical Character Recognition) technology to extract text from scanned PDFs and image-based documents, making them fully editable in Word. Whether you're working with text-based PDFs, scanned documents, or complex layouts with tables and images, our tool ensures accurate conversion with minimal formatting loss. The converter maintains paragraph structure, headings, bullet points, numbered lists, and basic formatting elements. Images and graphics are preserved and embedded in the Word document, and tables are converted with their structure intact. Our intelligent conversion engine handles various PDF types including native PDFs, scanned documents, and password-protected files (when unlocked). The tool is completely free to use with no watermarks, and premium users can process larger files with enhanced OCR accuracy. All conversions happen securely in the cloud with SSL encryption, and your files are automatically deleted after processing. No software installation is required - simply upload your PDF and download your editable Word document. The converted Word files are compatible with all Microsoft Word versions and alternative word processors. Whether you're editing documents, extracting content, or converting forms for editing, our PDF to Word converter provides a reliable, accurate, and professional solution for all your PDF to document conversion needs.""",
    
    'pdf-to-excel': """Our PDF to Excel converter is a sophisticated online tool that extracts data from PDF documents and converts them into editable Microsoft Excel spreadsheets (XLSX format). This powerful converter is essential for accountants, data analysts, business professionals, and anyone who needs to extract tabular data from PDF files for analysis and manipulation. The tool uses advanced OCR technology to recognize and extract data from scanned PDFs, image-based documents, and native PDF files. Our intelligent conversion engine automatically detects tables, columns, rows, and data structures within PDF documents, preserving the layout and organization in Excel format. The converter maintains cell formatting, handles merged cells, and preserves numerical data with proper formatting. Whether you're working with financial statements, invoices, reports, or data tables, our tool ensures accurate data extraction and conversion. The tool supports various PDF types including scanned documents, image-based PDFs, and text-based PDFs with embedded tables. All conversions happen securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can process larger files with enhanced accuracy. No software installation is required - simply upload your PDF and download your Excel spreadsheet. The converted Excel files are fully editable and compatible with all Microsoft Excel versions and alternative spreadsheet applications. Whether you're extracting financial data, converting invoices, or analyzing reports, our PDF to Excel converter provides a reliable, accurate, and professional solution for all your PDF to spreadsheet conversion needs.""",
    
    'pdf-to-ppt': """Our PDF to PowerPoint converter is a professional online tool that transforms PDF documents into editable Microsoft PowerPoint presentations (PPTX format) while preserving layout, images, and text structure. This advanced converter is perfect for educators, business professionals, and content creators who need to convert PDF documents into presentation format. The tool uses intelligent page-to-slide conversion, automatically detecting page breaks and organizing content into appropriate slides. Our conversion engine maintains images, graphics, and text formatting, ensuring that your presentation looks professional and polished. The converter supports various PDF types including documents, reports, brochures, and multi-page documents. Whether you're converting a PDF report into a presentation, transforming documents into slides, or creating presentations from existing PDF content, our tool ensures accurate conversion with minimal manual editing required. The tool is completely free to use with no watermarks, and premium users can process larger files with enhanced layout preservation. All conversions happen securely in the cloud with SSL encryption, and your files are automatically deleted after processing. No software installation is required - simply upload your PDF and download your PowerPoint presentation. The converted PPTX files are fully editable and compatible with all Microsoft PowerPoint versions and alternative presentation software. Whether you're creating presentations from reports, converting documents into slides, or transforming PDF content for presentations, our PDF to PowerPoint converter provides a reliable, fast, and professional solution for all your PDF to presentation conversion needs.""",
    
    'compress-pdf': """Our PDF compressor is a powerful online tool that reduces PDF file sizes without compromising quality or readability. This essential tool is perfect for anyone who needs to share PDFs via email, upload to websites, or store documents with limited storage space. The compressor uses advanced compression algorithms to optimize PDF files by removing redundant data, compressing images, and optimizing document structure. The tool maintains text quality and readability while significantly reducing file size, making it ideal for sharing documents via email attachments or uploading to websites with file size restrictions. Our intelligent compression engine analyzes your PDF and applies the most effective compression techniques, including image optimization, font subsetting, and object compression. You can choose between different compression levels to balance file size reduction with quality preservation. The tool supports all PDF types including text-based PDFs, image-heavy documents, scanned documents, and complex layouts with embedded graphics. All compressions happen securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can process larger files with faster compression speeds. No software installation is required - simply upload your PDF and download your compressed file. Whether you're reducing file sizes for email, optimizing documents for web upload, or saving storage space, our PDF compressor provides a reliable, fast, and professional solution for all your PDF compression needs.""",
    
    'merge-pdf': """Our PDF merger is a comprehensive online tool that combines multiple PDF files into a single, organized document. This powerful tool is essential for professionals, students, and anyone who needs to consolidate multiple PDF documents into one file. The merger allows you to upload multiple PDF files and arrange them in your desired order before combining them into a single document. You can easily reorder pages, remove unwanted pages, and organize your documents exactly as needed. The tool maintains all formatting, images, and text from your original PDFs, ensuring that the merged document looks professional and complete. Whether you're combining reports, merging invoices, consolidating research papers, or organizing documents, our PDF merger provides a seamless solution. The tool supports unlimited PDF files for merging, and you can process large documents with multiple pages. All merging happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can process larger files with faster merging speeds. No software installation is required - simply upload your PDFs, arrange them, and download your merged document. Whether you're consolidating documents, organizing files, or creating comprehensive reports, our PDF merger provides a reliable, fast, and professional solution for all your PDF merging needs.""",
    
    'split-pdf': """Our PDF splitter is an advanced online tool that divides large PDF documents into smaller, manageable files. This powerful tool is perfect for anyone who needs to extract specific pages, create separate documents from a single PDF, or organize large files into smaller sections. The splitter allows you to extract individual pages, select page ranges, or split PDFs at specific page numbers. You can create multiple PDF files from a single document, making it easy to share specific sections, organize content, or extract pages for separate use. The tool maintains all formatting, images, and text from your original PDF, ensuring that split documents look professional and complete. Whether you're extracting pages from reports, splitting large documents, or organizing content, our PDF splitter provides a seamless solution. The tool supports PDFs with hundreds or thousands of pages, and you can split them into as many separate files as needed. All splitting happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can process larger files with faster splitting speeds. No software installation is required - simply upload your PDF, select pages or ranges, and download your split documents. Whether you're extracting specific pages, dividing large files, or organizing documents, our PDF splitter provides a reliable, fast, and professional solution for all your PDF splitting needs.""",
    
    'image-compressor': """Our image compressor is a powerful online tool that reduces image file sizes without significant quality loss. This essential tool is perfect for photographers, web designers, content creators, and anyone who needs to optimize images for web use, email sharing, or storage optimization. The compressor supports all major image formats including JPEG, PNG, WebP, and more. Our advanced compression algorithms analyze your images and apply the most effective compression techniques while maintaining visual quality. You can choose between different compression levels to balance file size reduction with image quality. The tool maintains image dimensions and aspect ratios while reducing file size, making it ideal for optimizing images for websites, social media, or email attachments. Whether you're compressing photos, optimizing graphics, or reducing image sizes for faster loading, our image compressor provides a seamless solution. The tool supports batch processing, allowing you to compress multiple images simultaneously. All compressions happen securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can process larger files with faster compression speeds. No software installation is required - simply upload your images and download your compressed files. Whether you're optimizing images for web, reducing file sizes for email, or saving storage space, our image compressor provides a reliable, fast, and professional solution for all your image compression needs.""",
    
    'image-resizer': """Our image resizer is a versatile online tool that changes image dimensions while maintaining aspect ratios or allowing custom sizing. This powerful tool is perfect for photographers, web designers, social media managers, and anyone who needs to resize images for specific requirements. The resizer supports all major image formats including JPEG, PNG, GIF, WebP, and more. You can resize images to specific dimensions, scale images by percentage, or use preset sizes for common use cases like social media posts, profile pictures, or website banners. Our advanced resizing algorithms maintain image quality during the resizing process, using intelligent interpolation techniques to ensure sharp, clear results. Whether you're resizing photos for social media, adjusting images for websites, or preparing graphics for print, our image resizer provides a seamless solution. The tool supports batch processing, allowing you to resize multiple images simultaneously with consistent settings. All resizing happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can process larger files with faster resizing speeds. No software installation is required - simply upload your images, choose your dimensions, and download your resized files. Whether you're preparing images for social media, optimizing graphics for websites, or resizing photos for print, our image resizer provides a reliable, fast, and professional solution for all your image resizing needs.""",
    
    'image-editor': """Our image editor is a comprehensive online tool that provides professional photo editing capabilities without requiring expensive software. This powerful editor is perfect for photographers, designers, content creators, and anyone who needs to enhance, edit, or manipulate images. The editor includes a wide range of editing tools including crop, rotate, flip, brightness, contrast, saturation, sharpness, and color adjustments. You can apply filters, add text, draw shapes, and use various effects to enhance your images. The tool supports all major image formats and maintains high image quality throughout the editing process. Whether you're enhancing photos, creating graphics, or editing images for social media, our image editor provides a comprehensive solution. The editor features an intuitive interface that's easy to use for beginners while offering advanced features for professional users. All editing happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can access additional advanced features and faster processing. No software installation is required - simply upload your image, edit it using our tools, and download your enhanced file. Whether you're enhancing photos, creating graphics, or editing images for various purposes, our image editor provides a reliable, fast, and professional solution for all your image editing needs.""",
    
    'ocr-image': """Our OCR (Optical Character Recognition) tool is an advanced online service that extracts text from images and scanned documents. This powerful tool is essential for digitizing documents, extracting text from photos, and converting image-based content into editable text. The OCR engine uses advanced machine learning algorithms to recognize text in various languages, fonts, and styles. Whether you're working with scanned documents, photos of text, screenshots, or handwritten text, our OCR tool provides accurate text extraction. The tool supports multiple languages and can handle various image formats including JPEG, PNG, PDF, and more. Our intelligent recognition engine maintains formatting, detects paragraphs, and preserves text structure during extraction. All OCR processing happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can process larger files with enhanced accuracy and faster processing. No software installation is required - simply upload your image or document and receive your extracted text. Whether you're digitizing documents, extracting text from images, or converting scanned content into editable text, our OCR tool provides a reliable, accurate, and professional solution for all your text extraction needs.""",
    
    'crop-pdf': """Our PDF cropper is a specialized online tool that allows you to remove unwanted margins, trim pages, and crop specific areas from PDF documents. This powerful tool is perfect for anyone who needs to adjust PDF page sizes, remove white space, or focus on specific content areas. The cropper provides precise control over cropping areas, allowing you to select exact regions to keep or remove. You can crop individual pages or apply the same crop settings to multiple pages simultaneously. The tool maintains all formatting, images, and text within the cropped area, ensuring that your final document looks professional and complete. Whether you're removing margins, trimming pages, or focusing on specific content, our PDF cropper provides a seamless solution. The tool supports all PDF types and maintains high quality throughout the cropping process. All cropping happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can process larger files with faster cropping speeds. No software installation is required - simply upload your PDF, select your crop area, and download your cropped document. Whether you're adjusting page sizes, removing margins, or focusing on specific content, our PDF cropper provides a reliable, fast, and professional solution for all your PDF cropping needs.""",
    
    'protect-pdf': """Our PDF protector is a comprehensive online tool that secures your PDF documents with password protection and encryption. This essential tool is perfect for anyone who needs to protect sensitive documents, confidential information, or private files from unauthorized access. The protector allows you to set user passwords and owner passwords, control printing permissions, copying restrictions, and editing limitations. You can choose from various security levels and encryption standards to meet your specific security requirements. The tool uses advanced encryption algorithms to ensure that your PDFs are protected with industry-standard security measures. Whether you're protecting confidential documents, securing sensitive information, or restricting access to private files, our PDF protector provides a comprehensive solution. All protection happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can process larger files with faster protection speeds. No software installation is required - simply upload your PDF, set your security options, and download your protected document. Whether you're securing confidential documents, protecting sensitive information, or restricting access to private files, our PDF protector provides a reliable, fast, and professional solution for all your PDF security needs.""",
    
    'biodata-maker': """Our biodata maker is a professional online tool that helps you create impressive biodata, resumes, and CVs with ease. This comprehensive tool is perfect for job seekers, professionals, and students who need to create professional biodata documents quickly and effectively. The biodata maker provides various templates, formats, and layouts to suit different industries and career levels. You can customize fonts, colors, sections, and layouts to create a biodata that reflects your personality and professional style. The tool includes sections for personal information, education, work experience, skills, achievements, and more. Whether you're creating a resume, CV, or biodata for job applications, our biodata maker provides a comprehensive solution. The tool allows you to export your biodata in PDF format for easy sharing and printing. All biodata creation happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can access additional templates and advanced customization options. No software installation is required - simply use our online editor to create your biodata and download your professional document. Whether you're creating resumes, CVs, or biodata for job applications, our biodata maker provides a reliable, fast, and professional solution for all your biodata creation needs.""",
    
    'ai-image-generator': """Our AI image generator is an advanced online tool that creates stunning images from text descriptions using artificial intelligence. This powerful tool is perfect for designers, content creators, marketers, and anyone who needs to generate unique images quickly and easily. The generator uses state-of-the-art AI technology to understand your text prompts and create high-quality images that match your descriptions. You can generate images in various styles, themes, and artistic approaches to suit your specific needs. Whether you're creating graphics for social media, generating illustrations for content, or producing artwork for projects, our AI image generator provides a comprehensive solution. The tool supports various image formats and resolutions, allowing you to generate images suitable for different purposes. All image generation happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can generate higher resolution images with faster processing speeds. No software installation is required - simply enter your text description and receive your generated image. Whether you're creating graphics, generating illustrations, or producing artwork, our AI image generator provides a reliable, fast, and professional solution for all your image generation needs.""",
    
    'marriage-card': """Our marriage card maker is a specialized online tool that helps you create beautiful, personalized marriage invitation cards and wedding cards with ease. This comprehensive tool is perfect for couples, wedding planners, and anyone organizing marriage ceremonies who need to create professional invitation cards. The marriage card maker provides various templates, designs, and layouts to suit different wedding styles and cultural preferences. You can customize colors, fonts, images, text, and layouts to create a marriage card that reflects your unique style and personality. The tool includes sections for couple names, wedding dates, venue information, and special messages. Whether you're creating traditional marriage cards, modern wedding invitations, or personalized ceremony cards, our marriage card maker provides a comprehensive solution. The tool allows you to export your marriage card in high-quality PDF format for printing or digital sharing. All card creation happens securely in the cloud with automatic file deletion after processing. The tool is completely free to use with no watermarks, and premium users can access additional templates and advanced customization options. No software installation is required - simply use our online editor to create your marriage card and download your professional invitation. Whether you're creating traditional cards, modern invitations, or personalized marriage cards, our marriage card maker provides a reliable, fast, and professional solution for all your marriage card creation needs."""
}

def get_tool_name(filename):
    """Extract tool name from filename"""
    # Remove common suffixes and paths
    name = os.path.basename(filename).replace('-convert.html', '').replace('.html', '').lower()
    
    # Handle special cases - check in order of specificity
    if 'jpg-to-pdf' in name or 'jpeg-to-pdf' in name:
        return 'jpg-to-pdf'
    elif 'word-to-pdf' in name:
        return 'word-to-pdf'
    elif 'excel-to-pdf' in name or 'xls-to-pdf' in name:
        return 'excel-to-pdf'
    elif 'ppt-to-pdf' in name or 'powerpoint-to-pdf' in name:
        return 'ppt-to-pdf'
    elif 'pdf-to-jpg' in name or 'pdf-to-jpeg' in name:
        return 'pdf-to-jpg'
    elif 'pdf-to-word' in name:
        return 'pdf-to-word'
    elif 'pdf-to-excel' in name or 'pdf-to-xls' in name:
        return 'pdf-to-excel'
    elif 'pdf-to-ppt' in name or 'pdf-to-powerpoint' in name:
        return 'pdf-to-ppt'
    elif 'compress-pdf' in name or 'pdf-compressor' in name:
        return 'compress-pdf'
    elif 'merge-pdf' in name:
        return 'merge-pdf'
    elif 'split-pdf' in name:
        return 'split-pdf'
    elif 'image-compressor' in name:
        return 'image-compressor'
    elif 'image-resizer' in name:
        return 'image-resizer'
    elif 'image-editor' in name:
        return 'image-editor'
    elif 'ocr' in name:
        return 'ocr-image'
    elif 'crop-pdf' in name:
        return 'crop-pdf'
    elif 'protect-pdf' in name:
        return 'protect-pdf'
    elif 'biodata' in name:
        return 'biodata-maker'
    elif 'ai-image' in name or 'image-generator' in name:
        return 'ai-image-generator'
    elif 'marriage' in name or 'wedding-card' in name:
        return 'marriage-card'
    return None

def update_about_section(filepath):
    """Update the about section in an HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has explanatory-content section
        if 'explanatory-content' not in content:
            return False
        
        # Get tool name
        filename = os.path.basename(filepath)
        tool_name = get_tool_name(filename)
        
        if not tool_name or tool_name not in TOOL_DESCRIPTIONS:
            print(f"  ⚠️  No description found for: {filename} (tool: {tool_name})")
            return False
        
        description = TOOL_DESCRIPTIONS[tool_name]
        
        # Find and replace the short description in content-text div
        pattern = r'(<div class="content-text"[^>]*>)\s*<p>.*?</p>\s*(</div>)'
        replacement = f'\\1\n                <p>{description}</p>\n            \\2'
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        if new_content == content:
            # Try alternative pattern
            pattern2 = r'(<div class="content-text"[^>]*>)\s*<p>([^<]+)</p>\s*(</div>)'
            new_content = re.sub(pattern2, f'\\1\n                <p>{description}</p>\n            \\3', content)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        else:
            print(f"  ⚠️  Could not find content-text pattern in: {filename}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing {filepath}: {e}")
        return False

def main():
    """Main function to process all HTML files"""
    print("🔍 Finding tool pages with about sections...")
    
    # Find all HTML files with explanatory-content
    html_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if 'node_modules' in root or '.git' in root or 'backups' in root or 'server' in root:
            continue
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                # Check if file has explanatory-content section
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'explanatory-content' in content:
                            html_files.append(filepath)
                except:
                    pass
    
    print(f"📄 Found {len(html_files)} tool pages with about sections")
    
    updated_count = 0
    for filepath in html_files:
        filename = os.path.basename(filepath)
        print(f"\n📝 Processing: {filename}")
        if update_about_section(filepath):
            print(f"  ✅ Updated about section")
            updated_count += 1
        else:
            print(f"  ⏭️  Skipped (no changes or not applicable)")
    
    print(f"\n✨ Done! Updated {updated_count} files")

if __name__ == '__main__':
    main()

