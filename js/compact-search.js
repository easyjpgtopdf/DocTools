/**
 * Compact Search Bar Functionality
 * Provides real-time search for tools, pages, and blog posts
 * Similar to Jarvis voice command search
 */

(function() {
    'use strict';
    
    // Add CSS styles for search results
    if (!document.getElementById('compact-search-styles')) {
        const style = document.createElement('style');
        style.id = 'compact-search-styles';
        style.textContent = `
            .compact-result-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 16px;
                color: #fff;
                text-decoration: none;
                border-bottom: 1px solid #444;
                transition: background 0.2s;
            }
            .compact-result-item:hover {
                background: rgba(67, 97, 238, 0.1);
            }
            .compact-result-item:last-child {
                border-bottom: none;
            }
            .compact-result-icon {
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(67, 97, 238, 0.1);
                border-radius: 8px;
                color: #4361ee;
                font-size: 1.2rem;
            }
            .compact-result-content {
                flex: 1;
                min-width: 0;
            }
            .compact-result-title {
                font-weight: 600;
                color: #fff;
                margin-bottom: 4px;
                font-size: 0.95rem;
            }
            .compact-result-description {
                font-size: 0.85rem;
                color: #aaa;
            }
            .compact-result-arrow {
                color: #666;
                font-size: 0.9rem;
            }
            #compact-search-results {
                scrollbar-width: thin;
                scrollbar-color: #4361ee #2a2a2a;
            }
            #compact-search-results::-webkit-scrollbar {
                width: 6px;
            }
            #compact-search-results::-webkit-scrollbar-track {
                background: #2a2a2a;
            }
            #compact-search-results::-webkit-scrollbar-thumb {
                background: #4361ee;
                border-radius: 3px;
            }
        `;
        document.head.appendChild(style);
    }

    // Complete tool database (same as voice assistant)
    const toolDatabase = [
        // PDF Conversion Tools
        { 
            title: 'PDF to Word', 
            url: 'pdf-to-word.html', 
            keywords: ['pdf', 'word', 'convert', 'doc', 'docx', 'pdf se word', 'pdf ko word', 'word mein', 'वर्ड', 'document'], 
            category: 'PDF Tools', 
            description: 'Convert PDF to editable Word document',
            icon: 'fas fa-file-word'
        },
        { 
            title: 'PDF to Excel', 
            url: 'pdf-to-excel.html', 
            keywords: ['pdf', 'excel', 'spreadsheet', 'xls', 'xlsx', 'pdf se excel', 'एक्सेल'], 
            category: 'PDF Tools', 
            description: 'Convert PDF to Excel spreadsheet',
            icon: 'fas fa-file-excel'
        },
        { 
            title: 'PDF to PowerPoint', 
            url: 'pdf-to-ppt.html', 
            keywords: ['pdf', 'powerpoint', 'ppt', 'pptx', 'presentation', 'pdf se ppt', 'पीपीटी'], 
            category: 'PDF Tools', 
            description: 'Convert PDF to PowerPoint presentation',
            icon: 'fas fa-file-powerpoint'
        },
        { 
            title: 'PDF to JPG', 
            url: 'pdf-to-jpg.html', 
            keywords: ['pdf', 'jpg', 'jpeg', 'image', 'picture', 'photo', 'pdf se image', 'pdf se jpg', 'तस्वीर'], 
            category: 'PDF Tools', 
            description: 'Convert PDF pages to JPG images',
            icon: 'fas fa-file-image'
        },
        
        // PDF Editing Tools
        { title: 'Merge PDF', url: 'merge-pdf.html', keywords: ['merge', 'combine', 'join', 'pdf', 'milao', 'jodo', 'ek karo', 'मिलाओ'], category: 'PDF Tools', description: 'Combine multiple PDF files into one', icon: 'fas fa-file-pdf' },
        { title: 'Split PDF', url: 'split-pdf.html', keywords: ['split', 'divide', 'separate', 'pdf', 'todo', 'alag karo', 'विभाजित'], category: 'PDF Tools', description: 'Split PDF into multiple files', icon: 'fas fa-file-pdf' },
        { title: 'Compress PDF', url: 'compress-pdf.html', keywords: ['compress', 'reduce', 'size', 'pdf', 'chhota', 'size kam', 'छोटा'], category: 'PDF Tools', description: 'Reduce PDF file size', icon: 'fas fa-file-pdf' },
        { title: 'Protect PDF', url: 'protect-pdf.html', keywords: ['protect', 'password', 'secure', 'lock', 'pdf', 'surakshit', 'tala', 'सुरक्षित'], category: 'PDF Tools', description: 'Add password protection to PDF', icon: 'fas fa-lock' },
        { title: 'Unlock PDF', url: 'unlock-pdf.html', keywords: ['unlock', 'pdf', 'password', 'remove', 'open', 'kholo', 'खोलो'], category: 'PDF Tools', description: 'Remove PDF password protection', icon: 'fas fa-unlock' },
        { title: 'Edit PDF', url: 'edit-pdf.html', keywords: ['edit', 'modify', 'change', 'pdf', 'sudhar', 'badlo', 'संपादित'], category: 'PDF Tools', description: 'Edit PDF content directly', icon: 'fas fa-edit' },
        { title: 'Crop PDF', url: 'crop-pdf.html', keywords: ['crop', 'trim', 'cut', 'pdf', 'kaato', 'काटो'], category: 'PDF Tools', description: 'Crop PDF pages', icon: 'fas fa-crop' },
        { title: 'Watermark PDF', url: 'watermark-pdf.html', keywords: ['watermark', 'pdf', 'logo', 'mark', 'stamp', 'nishaan', 'निशान'], category: 'PDF Tools', description: 'Add watermark to PDF', icon: 'fas fa-tint' },
        { title: 'Add Page Numbers', url: 'add-page-numbers.html', keywords: ['page', 'number', 'pdf', 'add', 'sankhya', 'संख्या'], category: 'PDF Tools', description: 'Add page numbers to PDF', icon: 'fas fa-list-ol' },
        
        // Image to PDF
        { title: 'JPG to PDF', url: 'jpg-to-pdf.html', keywords: ['jpg', 'jpeg', 'image', 'pdf', 'picture', 'photo', 'image se pdf', 'तस्वीर से पीडीएफ'], category: 'Image Tools', description: 'Convert images to PDF', icon: 'fas fa-file-pdf' },
        
        // Image Editing Tools
        { title: 'Compress Image', url: 'image-compressor.html', keywords: ['compress', 'image', 'reduce', 'size', 'photo', 'image chhota', 'size kam', 'छोटा'], category: 'Image Tools', description: 'Reduce image file size', icon: 'fas fa-compress' },
        { title: 'Resize Image', url: 'image-resizer.html', keywords: ['resize', 'scale', 'dimension', 'image', 'photo', 'size badlo', 'आकार'], category: 'Image Tools', description: 'Change image dimensions', icon: 'fas fa-expand-arrows-alt' },
        { title: 'Image Editor', url: 'image-editor.html', keywords: ['edit', 'image', 'photo', 'editor', 'modify', 'sudhar', 'badlo', 'फोटो एडिट'], category: 'Image Tools', description: 'Professional image editing tools', icon: 'fas fa-image' },
        { title: 'Image Repair', url: 'image-repair.html', keywords: ['repair', 'fix', 'restore', 'image', 'photo', 'thik karo', 'ठीक'], category: 'Image Tools', description: 'Repair and restore damaged images', icon: 'fas fa-tools' },
        { title: 'Add Watermark', url: 'image-watermark.html', keywords: ['watermark', 'logo', 'text', 'image', 'mark', 'nishaan', 'निशान'], category: 'Image Tools', description: 'Add watermark to images', icon: 'fas fa-tint' },
        { title: 'Remove Background', url: 'background-remover.html', keywords: ['background', 'remove', 'transparent', 'bg', 'image', 'background hatao', 'बैकग्राउंड हटाओ'], category: 'Image Tools', description: 'Remove image background', icon: 'fas fa-magic' },
        
        // Office to PDF
        { title: 'Excel to PDF', url: 'excel-to-pdf.html', keywords: ['excel', 'pdf', 'spreadsheet', 'xls', 'xlsx', 'xlsx se pdf', 'एक्सेल से पीडीएफ'], category: 'Office Tools', description: 'Convert Excel to PDF', icon: 'fas fa-file-excel' },
        { title: 'PowerPoint to PDF', url: 'ppt-to-pdf.html', keywords: ['powerpoint', 'ppt', 'pdf', 'presentation', 'ppt se pdf', 'प्रेजेंटेशन'], category: 'Office Tools', description: 'Convert PowerPoint to PDF', icon: 'fas fa-file-powerpoint' },
        { title: 'Word to PDF', url: 'word-to-pdf.html', keywords: ['word', 'pdf', 'doc', 'docx', 'word se pdf', 'वर्ड से पीडीएफ'], category: 'Office Tools', description: 'Convert Word to PDF', icon: 'fas fa-file-word' },
        
        // Excel Tools
        { title: 'Unlock Excel', url: 'excel-unlocker.html', keywords: ['unlock', 'excel', 'password', 'remove', 'kholo', 'password hatao', 'एक्सेल खोलो'], category: 'Office Tools', description: 'Remove Excel password protection', icon: 'fas fa-unlock' },
        { title: 'Protect Excel', url: 'protect-excel.html', keywords: ['protect', 'excel', 'password', 'secure', 'lock', 'surakshit', 'सुरक्षित'], category: 'Office Tools', description: 'Add password to Excel file', icon: 'fas fa-lock' },
        
        // AI Tools
        { title: 'OCR Image', url: 'ocr-image.html', keywords: ['ocr', 'text', 'recognition', 'read', 'image', 'scan', 'text nikalo', 'टेक्स्ट निकालो'], category: 'AI Tools', description: 'Extract text from images using AI', icon: 'fas fa-eye' },
        { title: 'AI Image Generator', url: 'ai-image-generator.html', keywords: ['ai', 'generate', 'image', 'create', 'art', 'banao', 'आर्टिफिशियल', 'बनाओ'], category: 'AI Tools', description: 'Generate images using AI', icon: 'fas fa-robot' },
        
        // Document Makers
        { title: 'Resume Maker', url: 'resume-maker.html', keywords: ['resume', 'cv', 'create', 'make', 'job', 'biodata', 'रिज्यूमे'], category: 'Document Tools', description: 'Create professional resume', icon: 'fas fa-file-alt' },
        { title: 'Indian Resume Maker', url: 'Indian-style-Resume-generator.html', keywords: ['indian', 'resume', 'cv', 'bharatiya', 'भारतीय', 'रिज्यूमे'], category: 'Document Tools', description: 'Create Indian-style resume', icon: 'fas fa-file-alt' },
        { title: 'Online Resume Maker', url: 'online_resume_maker.html', keywords: ['online', 'resume', 'cv', 'web', 'ऑनलाइन'], category: 'Document Tools', description: 'Create resume online', icon: 'fas fa-file-alt' },
        { title: 'Marriage Biodata Maker', url: 'biodata-maker.html', keywords: ['marriage biodata', 'biodata', 'create', 'make', 'marriage', 'personal', 'bio', 'बायोडाटा', 'विवाह'], category: 'Document Tools', description: 'Create marriage biodata form', icon: 'fas fa-user' },
        { title: 'Marriage Card', url: 'marriage-card.html', keywords: ['marriage', 'wedding', 'card', 'invitation', 'shadi', 'vivah', 'शादी', 'विवाह'], category: 'Document Tools', description: 'Create marriage invitation card', icon: 'fas fa-heart' },
        
        // Account & Navigation
        { title: 'Dashboard', url: 'dashboard.html', keywords: ['dashboard', 'account', 'profile', 'home', 'khata', 'डैशबोर्ड'], category: 'Navigation', description: 'View your account dashboard', icon: 'fas fa-tachometer-alt' },
        { title: 'Login', url: 'login.html', keywords: ['login', 'signin', 'enter', 'log in', 'प्रवेश'], category: 'Navigation', description: 'Login to your account', icon: 'fas fa-sign-in-alt' },
        { title: 'Sign Up', url: 'signup.html', keywords: ['signup', 'register', 'create account', 'join', 'पंजीकरण'], category: 'Navigation', description: 'Create new account', icon: 'fas fa-user-plus' },
        { title: 'Payment History', url: 'dashboard.html#dashboard-payments', keywords: ['payment', 'history', 'transaction', 'receipt', 'bill', 'lenden', 'भुगतान'], category: 'Navigation', description: 'View payment history', icon: 'fas fa-wallet' },
        { title: 'Billing Details', url: 'shipping-billing.html', keywords: ['billing', 'shipping', 'address', 'details', 'पता'], category: 'Navigation', description: 'Manage billing information', icon: 'fas fa-file-invoice' },
        { title: 'Pricing', url: 'pricing.html', keywords: ['pricing', 'price', 'cost', 'plan', 'subscription', 'कीमत'], category: 'Navigation', description: 'View pricing plans', icon: 'fas fa-tags' },
        { title: 'Blog', url: 'blog.html', keywords: ['blog', 'article', 'post', 'news', 'guide', 'ब्लॉग'], category: 'Navigation', description: 'Read our blog articles', icon: 'fas fa-blog' },
        
        // Legal & Support
        { title: 'Privacy Policy', url: 'privacy-policy.html', keywords: ['privacy', 'policy', 'terms', 'गोपनीयता'], category: 'Legal', description: 'Privacy policy and data protection', icon: 'fas fa-shield-alt' },
        { title: 'Terms of Service', url: 'terms-of-service.html', keywords: ['terms', 'service', 'conditions', 'शर्तें'], category: 'Legal', description: 'Terms and conditions', icon: 'fas fa-file-contract' },
        { title: 'Refund Policy', url: 'refund-policy.html', keywords: ['refund', 'return', 'money back', 'वापसी'], category: 'Legal', description: 'Refund and return policy', icon: 'fas fa-undo' },
        { title: 'KYC Support', url: 'kyc-support.html', keywords: ['kyc', 'support', 'verification', 'help', 'सहायता'], category: 'Support', description: 'KYC verification support', icon: 'fas fa-question-circle' },
        { title: 'Attributions', url: 'attributions.html', keywords: ['attribution', 'credit', 'acknowledgment', 'श्रेय'], category: 'Support', description: 'Third-party attributions', icon: 'fas fa-info-circle' },
        
        // Archive Tools
        { title: 'ZIP to RAR', url: 'zip-to-rar.html', keywords: ['zip', 'rar', 'convert', 'archive', 'zip to rar', 'archive converter'], category: 'Archive Tools', description: 'Convert ZIP archives to RAR format online', icon: 'fas fa-file-archive' },
        { title: 'RAR to ZIP', url: 'rar-to-zip.html', keywords: ['rar', 'zip', 'convert', 'archive', 'rar to zip', 'archive converter'], category: 'Archive Tools', description: 'Convert RAR archives to ZIP format online', icon: 'fas fa-file-archive' },
        { title: 'ZIP Extractor', url: 'zip-extractor.html', keywords: ['zip', 'extract', 'unzip', 'open zip', 'zip extractor', 'extract zip'], category: 'Archive Tools', description: 'Extract files from ZIP archives online', icon: 'fas fa-file-archive' },
        { title: 'RAR Extractor', url: 'rar-extractor.html', keywords: ['rar', 'extract', 'unrar', 'open rar', 'rar extractor', 'extract rar'], category: 'Archive Tools', description: 'Extract files from RAR archives online', icon: 'fas fa-file-archive' },
        { title: '7Z Extractor', url: '7z-extractor.html', keywords: ['7z', 'extract', '7zip', 'open 7z', '7z extractor', 'extract 7z'], category: 'Archive Tools', description: 'Extract files from 7Z archives online', icon: 'fas fa-file-archive' },
        { title: '7Z to ZIP', url: '7z-to-zip.html', keywords: ['7z', 'zip', 'convert', '7zip to zip', 'archive converter'], category: 'Archive Tools', description: 'Convert 7Z archives to ZIP format', icon: 'fas fa-file-archive' },
        { title: 'TAR to ZIP', url: 'tar-to-zip.html', keywords: ['tar', 'zip', 'convert', 'tar to zip', 'archive converter'], category: 'Archive Tools', description: 'Convert TAR archives to ZIP format', icon: 'fas fa-file-archive' },
        { title: 'ISO Extractor', url: 'iso-extractor.html', keywords: ['iso', 'extract', 'iso extractor', 'extract iso', 'disk image'], category: 'Archive Tools', description: 'Extract files from ISO disk images', icon: 'fas fa-compact-disc' },
        { title: 'Folder to ZIP', url: 'folder-to-zip.html', keywords: ['folder', 'zip', 'compress', 'folder to zip', 'create zip'], category: 'Archive Tools', description: 'Compress folders into ZIP archives', icon: 'fas fa-folder' },
        { title: 'Batch ZIP Converter', url: 'batch-zip-converter.html', keywords: ['batch', 'zip', 'convert', 'multiple zip', 'batch converter'], category: 'Archive Tools', description: 'Convert multiple ZIP files in batch mode', icon: 'fas fa-layer-group' },
        
        // Blog Posts (common blog topics)
        { title: 'How to Convert JPG to PDF', url: 'blog-how-to-use-jpg-to-pdf.html', keywords: ['jpg', 'pdf', 'convert', 'image', 'tutorial', 'guide', 'कैसे'], category: 'Blog', description: 'Step-by-step guide to convert images to PDF', icon: 'fas fa-file-pdf' },
        { title: 'How to Convert Word to PDF', url: 'blog-how-to-use-word-to-pdf.html', keywords: ['word', 'pdf', 'convert', 'doc', 'tutorial', 'guide'], category: 'Blog', description: 'Learn how to convert Word documents to PDF', icon: 'fas fa-file-word' },
        { title: 'How to Merge PDF Files', url: 'blog-how-to-merge-pdf.html', keywords: ['merge', 'pdf', 'combine', 'join', 'tutorial', 'guide'], category: 'Blog', description: 'Guide to merging multiple PDF files', icon: 'fas fa-file-pdf' },
        { title: 'How to Compress PDF', url: 'blog-how-to-compress-pdf.html', keywords: ['compress', 'pdf', 'reduce', 'size', 'tutorial', 'guide'], category: 'Blog', description: 'Reduce PDF file size effectively', icon: 'fas fa-compress' },
        { title: 'How to Remove Background from Image', url: 'blog-how-to-remove-background.html', keywords: ['background', 'remove', 'image', 'transparent', 'tutorial', 'guide'], category: 'Blog', description: 'Remove image backgrounds easily', icon: 'fas fa-magic' },
    
        { title: 'EPUB to PDF', url: 'epub-to-pdf.html', keywords: ['epub to pdf', 'convert epub to pdf', 'epub pdf converter', 'ebook converter'], category: 'E-book Tools', description: 'Convert epub to pdf online for free', icon: 'fas fa-book' },
        { title: 'PDF to EPUB', url: 'pdf-to-epub.html', keywords: ['pdf to epub', 'convert pdf to epub', 'pdf epub converter'], category: 'E-book Tools', description: 'Convert pdf to epub online for free', icon: 'fas fa-book' },
        { title: 'EPUB to MOBI', url: 'epub-to-mobi.html', keywords: ['epub to mobi', 'convert epub to mobi', 'kindle converter'], category: 'E-book Tools', description: 'Convert epub to mobi online for free', icon: 'fas fa-book' },
        { title: 'MOBI to EPUB', url: 'mobi-to-epub.html', keywords: ['mobi to epub', 'convert mobi to epub', 'kindle to epub'], category: 'E-book Tools', description: 'Convert mobi to epub online for free', icon: 'fas fa-book' },
        { title: 'AZW3 to EPUB', url: 'azw3-to-epub.html', keywords: ['azw3 to epub', 'convert azw3 to epub', 'kindle to epub'], category: 'E-book Tools', description: 'Convert azw3 to epub online for free', icon: 'fas fa-book' },
        { title: 'FB2 to PDF', url: 'fb2-to-pdf.html', keywords: ['fb2 to pdf', 'convert fb2 to pdf', 'fictionbook to pdf'], category: 'E-book Tools', description: 'Convert fb2 to pdf online for free', icon: 'fas fa-book' },
        { title: 'PDF to Text', url: 'pdf-to-text.html', keywords: ['pdf to text', 'extract text from pdf', 'pdf text converter'], category: 'E-book Tools', description: 'Convert pdf to text online for free', icon: 'fas fa-file-pdf' },
        { title: 'RTF to PDF', url: 'rtf-to-pdf.html', keywords: ['rtf to pdf', 'convert rtf to pdf', 'rich text to pdf'], category: 'E-book Tools', description: 'Convert rtf to pdf online for free', icon: 'fas fa-file-pdf' },
        { title: 'TXT to PDF', url: 'txt-to-pdf.html', keywords: ['txt to pdf', 'convert txt to pdf', 'text to pdf'], category: 'E-book Tools', description: 'Convert txt to pdf online for free', icon: 'fas fa-file-pdf' },
        { title: 'WebP to PNG', url: 'webp-to-png.html', keywords: ['webp to png', 'convert webp to png', 'webp converter'], category: 'Image Tools', description: 'Convert webp to png online for free', icon: 'fas fa-file-image' },
        { title: 'PNG to WebP', url: 'png-to-webp.html', keywords: ['png to webp', 'convert png to webp', 'webp converter'], category: 'Image Tools', description: 'Convert png to webp online for free', icon: 'fas fa-file-image' },
        { title: 'HEIC to JPG', url: 'heic-to-jpg.html', keywords: ['heic to jpg', 'convert heic to jpg', 'heic converter'], category: 'Image Tools', description: 'Convert heic to jpg online for free', icon: 'fas fa-file-image' },
        { title: 'JPG to WebP', url: 'jpg-to-webp.html', keywords: ['jpg to webp', 'convert jpg to webp', 'jpeg to webp'], category: 'Image Tools', description: 'Convert jpg to webp online for free', icon: 'fas fa-file-image' },
        { title: 'TIFF to PNG', url: 'tiff-to-png.html', keywords: ['tiff to png', 'convert tiff to png', 'tif to png'], category: 'Image Tools', description: 'Convert tiff to png online for free', icon: 'fas fa-file-image' },
        { title: 'PNG to ICO', url: 'png-to-ico.html', keywords: ['png to ico', 'convert png to ico', 'icon converter'], category: 'Image Tools', description: 'Convert png to ico online for free', icon: 'fas fa-file-image' },
        { title: 'SVG to PNG', url: 'svg-to-png.html', keywords: ['svg to png', 'convert svg to png', 'vector to raster'], category: 'Image Tools', description: 'Convert svg to png online for free', icon: 'fas fa-file-image' },
        { title: 'SVG to JPG', url: 'svg-to-jpg.html', keywords: ['svg to jpg', 'convert svg to jpg', 'vector to jpg'], category: 'Image Tools', description: 'Convert svg to jpg online for free', icon: 'fas fa-file-image' },
        { title: 'AI to PNG', url: 'ai-to-png.html', keywords: ['ai to png', 'convert ai to png', 'illustrator to png'], category: 'Image Tools', description: 'Convert ai to png online for free', icon: 'fas fa-file-image' },
        { title: 'AI to SVG', url: 'ai-to-svg.html', keywords: ['ai to svg', 'convert ai to svg', 'illustrator to svg'], category: 'Image Tools', description: 'Convert ai to svg online for free', icon: 'fas fa-file-image' },
        { title: 'EPS to PNG', url: 'eps-to-png.html', keywords: ['eps to png', 'convert eps to png', 'postscript to png'], category: 'Image Tools', description: 'Convert eps to png online for free', icon: 'fas fa-file-image' },
        { title: 'BMP to JPG', url: 'bmp-to-jpg.html', keywords: ['bmp to jpg', 'convert bmp to jpg', 'bitmap to jpg'], category: 'Image Tools', description: 'Convert bmp to jpg online for free', icon: 'fas fa-file-image' },
        { title: 'BMP to PNG', url: 'bmp-to-png.html', keywords: ['bmp to png', 'convert bmp to png', 'bitmap to png'], category: 'Image Tools', description: 'Convert bmp to png online for free', icon: 'fas fa-file-image' },
        { title: 'CR2 to JPG', url: 'cr2-to-jpg.html', keywords: ['cr2 to jpg', 'convert cr2 to jpg', 'canon raw to jpg'], category: 'Image Tools', description: 'Convert cr2 to jpg online for free', icon: 'fas fa-file-image' },
        { title: 'RAW to JPG', url: 'raw-to-jpg.html', keywords: ['raw to jpg', 'convert raw to jpg', 'raw image converter'], category: 'Image Tools', description: 'Convert raw to jpg online for free', icon: 'fas fa-file-image' },
        { title: 'PSD to PNG', url: 'psd-to-png.html', keywords: ['psd to png', 'convert psd to png', 'photoshop to png'], category: 'Image Tools', description: 'Convert psd to png online for free', icon: 'fas fa-file-image' },
        { title: 'PSD to JPG', url: 'psd-to-jpg.html', keywords: ['psd to jpg', 'convert psd to jpg', 'photoshop to jpg'], category: 'Image Tools', description: 'Convert psd to jpg online for free', icon: 'fas fa-file-image' },
        { title: 'HDR to JPG', url: 'hdr-to-jpg.html', keywords: ['hdr to jpg', 'convert hdr to jpg', 'high dynamic range to jpg'], category: 'Image Tools', description: 'Convert hdr to jpg online for free', icon: 'fas fa-file-image' },
        { title: 'AVIF to JPG', url: 'avif-to-jpg.html', keywords: ['avif to jpg', 'convert avif to jpg', 'avif converter'], category: 'Image Tools', description: 'Convert avif to jpg online for free', icon: 'fas fa-file-image' },
        { title: 'AVIF to PNG', url: 'avif-to-png.html', keywords: ['avif to png', 'convert avif to png', 'avif converter'], category: 'Image Tools', description: 'Convert avif to png online for free', icon: 'fas fa-file-image' },
        { title: 'Transparent Background Maker', url: 'transparent-background-maker.html', keywords: ['transparent background', 'remove background', 'background remover'], category: 'Image Tools', description: 'Convert transparent background maker online for free', icon: 'fas fa-magic' },
        { title: 'EXIF Data Remove', url: 'exif-data-remove.html', keywords: ['remove exif', 'exif data remover', 'image metadata remover'], category: 'Image Tools', description: 'Convert exif data remove online for free', icon: 'fas fa-shield-alt' },
        { title: 'Image Cropper', url: 'image-cropper.html', keywords: ['crop image', 'image cropper', 'photo cropper'], category: 'Image Tools', description: 'Convert image cropper online for free', icon: 'fas fa-image' },
        { title: 'Photo Enhancer', url: 'photo-enhancer.html', keywords: ['photo enhancer', 'image enhancer', 'improve photo quality'], category: 'Image Tools', description: 'Convert photo enhancer online for free', icon: 'fas fa-image' },
        
        // Additional missing pages
        { title: '7Z Extractor', url: '7z-extractor.html', keywords: ['7z', 'extract', '7zip', 'open 7z', '7z extractor', 'extract 7z'], category: 'Archive Tools', description: 'Extract files from 7Z archives online', icon: 'fas fa-file-archive' },
        { title: '7Z to ZIP', url: '7z-to-zip.html', keywords: ['7z', 'zip', 'convert', '7zip to zip', 'archive converter'], category: 'Archive Tools', description: 'Convert 7Z archives to ZIP format', icon: 'fas fa-file-archive' },
        { title: 'PDF to Text', url: 'pdf-to-text.html', keywords: ['pdf to text', 'extract text from pdf', 'pdf text converter'], category: 'E-book Tools', description: 'Convert pdf to text online for free', icon: 'fas fa-file-pdf' },
        { title: 'PDF to EPUB', url: 'pdf-to-epub.html', keywords: ['pdf to epub', 'convert pdf to epub', 'pdf epub converter'], category: 'E-book Tools', description: 'Convert pdf to epub online for free', icon: 'fas fa-book' },
        { title: 'PDF to Excel Premium', url: 'pdf-to-excel-premium.html', keywords: ['pdf to excel premium', 'premium pdf to excel', 'ocr excel', 'high accuracy'], category: 'PDF Tools', description: 'Premium PDF to Excel conversion with OCR technology', icon: 'fas fa-file-excel' },
        { title: 'PDF to Word Premium', url: 'pdf-to-word-premium.html', keywords: ['pdf to word premium', 'premium pdf to word', 'ocr word'], category: 'PDF Tools', description: 'Premium PDF to Word conversion with OCR technology', icon: 'fas fa-file-word' },
        { title: 'PPT to PDF New', url: 'ppt-to-pdf-new.html', keywords: ['ppt to pdf new', 'powerpoint to pdf', 'presentation to pdf'], category: 'Office Tools', description: 'Convert PowerPoint to PDF with new improved tool', icon: 'fas fa-file-powerpoint' },
];

    // Search function (same logic as voice assistant)
    function smartSearch(query) {
        const results = [];
        const queryLower = query.toLowerCase().trim();
        
        if (!queryLower) {
            return [];
        }
        
        // Calculate relevance score
        for (const tool of toolDatabase) {
            let score = 0;
            const queryWords = queryLower.split(' ').filter(w => w.length > 0);
            const titleLower = tool.title.toLowerCase();
            const descLower = tool.description.toLowerCase();
            
            // Exact title match
            if (titleLower === queryLower) {
                score += 100;
            }
            
            // Title contains full query
            if (titleLower.includes(queryLower)) {
                score += 50;
            }
            
            // Title contains query words
            for (const word of queryWords) {
                if (word.length > 2 && titleLower.includes(word)) {
                    score += 15;
                }
            }
            
            // Keyword matching - exact match
            for (const keyword of tool.keywords) {
                const keywordLower = keyword.toLowerCase();
                if (queryLower === keywordLower) {
                    score += 30;
                } else if (queryLower.includes(keywordLower)) {
                    score += 20;
                } else if (keywordLower.includes(queryLower)) {
                    score += 15;
                }
            }
            
            // Partial word matching in keywords
            for (const word of queryWords) {
                if (word.length > 2) {
                    for (const keyword of tool.keywords) {
                        const keywordLower = keyword.toLowerCase();
                        if (keywordLower.includes(word) || word.includes(keywordLower)) {
                            score += 10;
                        }
                    }
                }
            }
            
            // Description matching
            for (const word of queryWords) {
                if (word.length > 2 && descLower.includes(word)) {
                    score += 5;
                }
            }
            
            if (score > 0) {
                results.push({ ...tool, score });
            }
        }
        
        // Sort by relevance score
        results.sort((a, b) => b.score - a.score);
        
        // Return top 8 results
        return results.slice(0, 8);
    }

    // Display search results
    function displayResults(results, query) {
        const resultsContainer = document.getElementById('compact-search-results');
        if (!resultsContainer) return;

        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #6b7280;">
                    <i class="fas fa-search" style="font-size: 2rem; margin-bottom: 10px; opacity: 0.5;"></i>
                    <div>No results found for "${query}"</div>
                    <div style="font-size: 0.85rem; margin-top: 5px;">Try different keywords</div>
                </div>
            `;
            resultsContainer.style.display = 'block';
            return;
        }

        resultsContainer.innerHTML = results.map(result => {
            const icon = result.icon || 'fas fa-file';
            return `
                <a href="${result.url}" class="compact-result-item">
                    <div class="compact-result-icon">
                        <i class="${icon}"></i>
                    </div>
                    <div class="compact-result-content">
                        <div class="compact-result-title">${highlightMatch(result.title, query)}</div>
                        <div class="compact-result-description">${result.description} • ${result.category}</div>
                    </div>
                    <div class="compact-result-arrow">
                        <i class="fas fa-chevron-right"></i>
                    </div>
                </a>
            `;
        }).join('');

        resultsContainer.style.display = 'block';
    }

    // Highlight matching text
    function highlightMatch(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark style="background: rgba(67, 97, 238, 0.2); padding: 2px 4px; border-radius: 3px;">$1</mark>');
    }

    // Hide results
    function hideResults() {
        const resultsContainer = document.getElementById('compact-search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
    }

    // Initialize search functionality
    function initSearch() {
        const searchInput = document.getElementById('compact-search-input');
        const resultsContainer = document.getElementById('compact-search-results');
        
        if (!searchInput || !resultsContainer) {
            // Retry after a short delay if elements not found
            setTimeout(initSearch, 100);
            return;
        }

        let searchTimeout;

        // Handle input
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.trim();
            
            clearTimeout(searchTimeout);
            
            if (query.length === 0) {
                hideResults();
                return;
            }

            // Debounce search
            searchTimeout = setTimeout(() => {
                const results = smartSearch(query);
                displayResults(results, query);
            }, 150);
        });

        // Handle focus
        searchInput.addEventListener('focus', function(e) {
            const query = e.target.value.trim();
            if (query.length > 0) {
                const results = smartSearch(query);
                displayResults(results, query);
            }
        });

        // Hide results when clicking outside
        document.addEventListener('click', function(e) {
            const searchBar = document.querySelector('.compact-search-bar');
            if (searchBar && !searchBar.contains(e.target)) {
                hideResults();
            }
        });

        // Handle search button click
        const searchBtn = document.getElementById('compact-search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', function() {
                const query = searchInput.value.trim();
                if (query.length > 0) {
                    const results = smartSearch(query);
                    if (results.length > 0) {
                        window.location.href = results[0].url;
                    } else {
                        // If no results, go to search page
                        window.location.href = `search.html?q=${encodeURIComponent(query)}`;
                    }
                }
            });
        }
        
        // Handle Enter key
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = e.target.value.trim();
                if (query.length > 0) {
                    const results = smartSearch(query);
                    if (results.length > 0) {
                        window.location.href = results[0].url;
                    } else {
                        // If no results, go to search page
                        window.location.href = `search.html?q=${encodeURIComponent(query)}`;
                    }
                }
            } else if (e.key === 'Escape') {
                hideResults();
                searchInput.blur();
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSearch);
    } else {
        initSearch();
    }

    // Also try after page load
    window.addEventListener('load', function() {
        setTimeout(initSearch, 100);
    });

})();

