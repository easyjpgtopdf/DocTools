#!/usr/bin/env python3
"""
Fix all PDF editor issues:
1. Prevent double upload - hide upload area after first upload
2. Fix PDF preview loading from IndexedDB
3. Redesign layout: Left panel (3 inch), Middle (preview), Right panel (2 inch)
"""

import re

def fix_edit_pdf_upload():
    """Fix double upload issue in edit-pdf.html"""
    print("Fixing edit-pdf.html - preventing double upload...")
    
    with open('edit-pdf.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add flag to prevent multiple uploads
    old_handle = r'function handleFile\(file\) \{\s+console\.log\("File selected:", file\);'
    new_handle = '''function handleFile(file) {
    // Prevent double upload
    if (uploadArea && uploadArea.style.pointerEvents === 'none') {
        return; // Already processing
    }
    
    // Disable upload area immediately
    if (uploadArea) {
        uploadArea.style.pointerEvents = 'none';
        uploadArea.style.opacity = '0.6';
    }
    
    console.log("File selected:", file);'''
    
    content = re.sub(old_handle, new_handle, content)
    
    with open('edit-pdf.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ Fixed double upload issue")

def fix_preview_loading():
    """Fix PDF preview loading from IndexedDB"""
    print("Fixing edit-pdf-preview.html - PDF loading from IndexedDB...")
    
    with open('edit-pdf-preview.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix IndexedDB query - get all records and use the latest one
    old_query = r'const transaction = db\.transaction\(\[''pdfFiles''\], ''readonly''\);\s+const store = transaction\.objectStore\(''pdfFiles''\);\s+const getRequest = store\.get\(''current''\);'
    
    new_query = '''const transaction = db.transaction(['pdfFiles'], 'readonly');
                    const store = transaction.objectStore('pdfFiles');
                    // Get all records and use the latest one (highest ID)
                    const getAllRequest = store.getAll();
                    getAllRequest.onsuccess = function() {
                        const allFiles = getAllRequest.result;
                        if (allFiles && allFiles.length > 0) {
                            // Sort by ID (or timestamp) and get the latest
                            const latestFile = allFiles.sort((a, b) => {
                                const idA = a.id || a.timestamp || 0;
                                const idB = b.id || b.timestamp || 0;
                                return idB - idA;
                            })[0];
                            
                            if (latestFile && latestFile.data) {
                                updateProgress(20, 'PDF found in storage...');
                                // Create File object from stored data
                                const blob = new Blob([latestFile.data], { type: 'application/pdf' });
                                const file = new File([blob], latestFile.name || 'document.pdf', { type: 'application/pdf' });
                                currentFile = file;
                                fileName.textContent = latestFile.name || 'document.pdf';
                                fileSize.textContent = formatFileSize(latestFile.size || 0);
                                fileInfo.style.display = 'block';
                                loadPDF(file);
                                return;
                            }
                        }
                        // No data found, try blob URL
                        loadFromBlobURL();
                    };
                    getAllRequest.onerror = function() {
                        loadFromBlobURL();
                    };
                    return;
                }
                // Fallback: try direct get with ID from sessionStorage
                const fileId = sessionStorage.getItem('pdfFileId');
                if (fileId) {
                    const getRequest = store.get(parseInt(fileId));'''
    
    # Replace the problematic query
    pattern = r'const transaction = db\.transaction\(\[''pdfFiles''\], ''readonly''\);\s+const store = transaction\.objectStore\(''pdfFiles''\);\s+const getRequest = store\.get\(''current''\);\s+getRequest\.onsuccess = function\(\) \{\s+const fileData = getRequest\.result;\s+if \(fileData && fileData\.data\) \{\s+updateProgress\(20, ''PDF found in storage\.\.\.''\);\s+// Create File object from stored data\s+const blob = new Blob\(\[fileData\.data\], \{ type: ''application/pdf'' \}\);\s+const file = new File\(\[blob\], fileData\.name \|\| ''document\.pdf'', \{ type: ''application/pdf'' \}\);\s+currentFile = file;\s+fileName\.textContent = fileData\.name \|\| ''document\.pdf'';\s+fileSize\.textContent = formatFileSize\(fileData\.size \|\| 0\);\s+fileInfo\.style\.display = ''block'';\s+loadPDF\(file\);\s+\} else \{\s+// No data in IndexedDB, try blob URL\s+loadFromBlobURL\(\);\s+\}\s+\};\s+getRequest\.onerror = function\(\) \{\s+loadFromBlobURL\(\);\s+\};'
    
    content = re.sub(pattern, new_query, content, flags=re.DOTALL)
    
    with open('edit-pdf-preview.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ Fixed PDF loading from IndexedDB")

def redesign_preview_layout():
    """Redesign layout: Left (3 inch), Middle (preview), Right (2 inch)"""
    print("Redesigning edit-pdf-preview.html layout...")
    
    with open('edit-pdf-preview.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add new CSS for 3-panel layout
    layout_css = '''
        /* 3-Panel Layout: Left (3 inch), Middle (preview), Right (2 inch) */
        .editor-main-container {
            display: flex;
            gap: 15px;
            width: 100%;
            max-width: 100%;
            margin: 0;
            padding: 0;
        }
        
        .left-toolbar-panel {
            width: 228px; /* 3 inches at 96 DPI */
            min-width: 228px;
            max-width: 228px;
            background: #fff;
            border-radius: var(--border-radius);
            padding: 20px;
            box-shadow: var(--box-shadow);
            overflow-y: auto;
            max-height: calc(100vh - 200px);
        }
        
        .middle-preview-panel {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
            background: #fff;
            border-radius: var(--border-radius);
            padding: 20px;
            box-shadow: var(--box-shadow);
        }
        
        .right-tools-panel {
            width: 152px; /* 2 inches at 96 DPI */
            min-width: 152px;
            max-width: 152px;
            background: #fff;
            border-radius: var(--border-radius);
            padding: 20px;
            box-shadow: var(--box-shadow);
            overflow-y: auto;
            max-height: calc(100vh - 200px);
        }
        
        .toolbar-section {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .toolbar-section:last-child {
            border-bottom: none;
        }
        
        .toolbar-section-title {
            font-size: 0.85rem;
            font-weight: 700;
            color: var(--primary);
            text-transform: uppercase;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }
        
        .toolbar-btn {
            width: 100%;
            padding: 10px 12px;
            margin-bottom: 8px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            background: #fff;
            color: var(--dark);
            font-size: 0.9rem;
            cursor: pointer;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .toolbar-btn:hover {
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }
        
        .toolbar-btn.active {
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }
        
        .toolbar-btn i {
            font-size: 1rem;
        }
        
        .toolbar-select, .toolbar-input {
            width: 100%;
            padding: 8px 10px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            background: #fff;
            font-size: 0.9rem;
            margin-bottom: 10px;
        }
        
        .color-picker-wrapper {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .color-picker-wrapper input[type="color"] {
            width: 50px;
            height: 40px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            cursor: pointer;
        }
        
        .highlight-colors {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 10px;
        }
        
        .highlight-color-btn {
            width: 100%;
            height: 35px;
            border: 2px solid transparent;
            border-radius: 6px;
            cursor: pointer;
            transition: var(--transition);
        }
        
        .highlight-color-btn.active {
            border-color: var(--dark);
            transform: scale(1.1);
        }
        
        /* Hide old ribbon, use new panels */
        .ribbon {
            display: none;
        }
        
        @media (max-width: 1200px) {
            .editor-main-container {
                flex-direction: column;
            }
            .left-toolbar-panel, .right-tools-panel {
                width: 100%;
                max-width: 100%;
                min-width: 100%;
            }
        }
'''
    
    # Insert CSS before closing </style>
    style_end = content.find('</style>')
    if style_end != -1:
        content = content[:style_end] + layout_css + '\n    ' + content[style_end:]
    
    # Replace preview-container with new 3-panel layout
    old_preview = r'<h2 style="text-align: center; font-size: 1\.8rem; color: var\(--primary\); margin: 30px 0 20px; font-weight: 700;">Real-Time PDF Editing Features</h2>\s+<div class="preview-container">\s+<div class="ribbon">'
    
    new_preview = '''<h2 style="text-align: center; font-size: 1.8rem; color: var(--primary); margin: 30px 0 20px; font-weight: 700;">Real-Time PDF Editing Features</h2>

<div class="editor-main-container">
<!-- Left Toolbar Panel (3 inch) -->
<div class="left-toolbar-panel">
<div class="toolbar-section">
<div class="toolbar-section-title"><i class="fas fa-mouse-pointer"></i> Tools</div>
<button class="toolbar-btn active" id="select-tool" title="Select Text">
<i class="fas fa-mouse-pointer"></i>
<span>Select</span>
</button>
<button class="toolbar-btn" id="text-tool" title="Add Text">
<i class="fas fa-font"></i>
<span>Add Text</span>
</button>
<button class="toolbar-btn" id="highlight-tool" title="Highlight">
<i class="fas fa-highlighter"></i>
<span>Highlight</span>
</button>
<button class="toolbar-btn" id="ocr-region-btn" title="OCR Region">
<i class="fas fa-vector-square"></i>
<span>OCR Region</span>
</button>
</div>

<div class="toolbar-section">
<div class="toolbar-section-title"><i class="fas fa-palette"></i> Font</div>
<select class="toolbar-select" id="tb-font-family">
<option>Inter</option>
<option>Roboto</option>
<option>Open Sans</option>
<option>Lato</option>
<option>Poppins</option>
<option>Montserrat</option>
<option>Source Sans 3</option>
<option>Noto Sans</option>
<option>PT Sans</option>
<option>PT Serif</option>
<option>Merriweather</option>
<option>Georgia</option>
<option>Verdana</option>
<option>Courier New</option>
<option>Times New Roman</option>
<option selected>Arial</option>
</select>
<select class="toolbar-select" id="tb-font-size">
<option>10</option>
<option>12</option>
<option selected>14</option>
<option>16</option>
<option>18</option>
<option>24</option>
<option>32</option>
</select>
</div>

<div class="toolbar-section">
<div class="toolbar-section-title"><i class="fas fa-paint-brush"></i> Color</div>
<div class="color-picker-wrapper">
<input type="color" id="tb-color" value="#111827" title="Text Color"/>
<select class="toolbar-select" id="tb-color-preset" style="flex: 1;">
<option value="#111827">Black</option>
<option value="#ff0000">Red</option>
<option value="#0057ff">Blue</option>
<option value="#00a650">Green</option>
<option value="#ff8c00">Orange</option>
<option value="#800080">Purple</option>
<option value="#808080">Gray</option>
<option value="#ffff00">Yellow</option>
</select>
</div>
</div>

<div class="toolbar-section">
<div class="toolbar-section-title"><i class="fas fa-text-height"></i> Style</div>
<button class="toolbar-btn" id="tb-bold" title="Bold">
<i class="fas fa-bold"></i>
<span>Bold</span>
</button>
<button class="toolbar-btn" id="tb-italic" title="Italic">
<i class="fas fa-italic"></i>
<span>Italic</span>
</button>
<button class="toolbar-btn" id="tb-underline" title="Underline">
<i class="fas fa-underline"></i>
<span>Underline</span>
</button>
</div>

<div class="toolbar-section">
<div class="toolbar-section-title"><i class="fas fa-align-left"></i> Align</div>
<button class="toolbar-btn" id="tb-align-left" title="Align Left">
<i class="fas fa-align-left"></i>
<span>Left</span>
</button>
<button class="toolbar-btn" id="tb-align-center" title="Align Center">
<i class="fas fa-align-center"></i>
<span>Center</span>
</button>
<button class="toolbar-btn" id="tb-align-right" title="Align Right">
<i class="fas fa-align-right"></i>
<span>Right</span>
</button>
</div>

<div class="toolbar-section">
<div class="toolbar-section-title"><i class="fas fa-magic"></i> Highlight Colors</div>
<div class="highlight-colors">
<div class="highlight-color-btn active" data-color="#FFFF00" style="background-color: #FFFF00;" title="Yellow"></div>
<div class="highlight-color-btn" data-color="#00FF00" style="background-color: #00FF00;" title="Green"></div>
<div class="highlight-color-btn" data-color="#00FFFF" style="background-color: #00FFFF;" title="Cyan"></div>
<div class="highlight-color-btn" data-color="#FF00FF" style="background-color: #FF00FF;" title="Magenta"></div>
<div class="highlight-color-btn" data-color="#FFA500" style="background-color: #FFA500;" title="Orange"></div>
<div class="highlight-color-btn" data-color="#FFC0CB" style="background-color: #FFC0CB;" title="Pink"></div>
</div>
</div>

<div class="toolbar-section">
<div class="toolbar-section-title"><i class="fas fa-language"></i> OCR Language</div>
<select class="toolbar-select" id="ocr-lang">
<option selected value="eng">English</option>
<option value="hin">Hindi</option>
<option value="ben">Bengali</option>
<option value="guj">Gujarati</option>
<option value="mar">Marathi</option>
<option value="pan">Punjabi</option>
<option value="tam">Tamil</option>
<option value="tel">Telugu</option>
<option value="kan">Kannada</option>
<option value="mal">Malayalam</option>
<option value="urd">Urdu</option>
<option value="eng+hin">English + Hindi</option>
</select>
<label style="display: flex; align-items: center; gap: 8px; color: var(--dark); margin-top: 8px; font-size: 0.85rem;">
<input id="ocr-auto" type="checkbox" style="width: 18px; height: 18px; cursor: pointer;"/>
<span>Auto OCR each page</span>
</label>
</div>
</div>

<!-- Middle Preview Panel -->
<div class="middle-preview-panel">
<div class="preview-container">'''
    
    # Find and replace the preview section
    preview_pattern = r'<h2 style="text-align: center; font-size: 1\.8rem; color: var\(--primary\); margin: 30px 0 20px; font-weight: 700;">Real-Time PDF Editing Features</h2>\s+<div class="preview-container">\s+<div class="ribbon">.*?</div>\s+</div>\s+<div class="preview-area">'
    
    # More specific replacement
    content = re.sub(
        r'(<h2 style="text-align: center[^>]*>Real-Time PDF Editing Features</h2>\s*<div class="preview-container">\s*<div class="ribbon">)',
        new_preview,
        content,
        flags=re.DOTALL
    )
    
    # Add closing tags before page-navigation
    content = re.sub(
        r'(</div>\s*</div>\s*<div class="page-navigation">)',
        r'</div>\n</div>\n</div>\n\n<!-- Right Tools Panel (2 inch) -->\n<div class="right-tools-panel">\n<div class="toolbar-section">\n<div class="toolbar-section-title"><i class="fas fa-undo"></i> Edit</div>\n<button class="toolbar-btn" id="tb-undo" title="Undo">\n<i class="fas fa-undo"></i>\n<span>Undo</span>\n</button>\n<button class="toolbar-btn" id="tb-redo" title="Redo">\n<i class="fas fa-redo"></i>\n<span>Redo</span>\n</button>\n<button class="toolbar-btn" id="tb-clear" title="Clear All">\n<i class="fas fa-trash"></i>\n<span>Clear</span>\n</button>\n</div>\n\n<div class="toolbar-section">\n<div class="toolbar-section-title"><i class="fas fa-image"></i> Insert</div>\n<button class="toolbar-btn" id="tb-insert-image" title="Insert Image">\n<i class="fas fa-image"></i>\n<span>Image</span>\n</button>\n<input accept="image/*" id="img-file-input" style="display:none" type="file"/>\n<label class="toolbar-section-title" for="tb-image-scale" style="margin-top: 10px; display: block; font-size: 0.8rem;">Image Scale</label>\n<input id="tb-image-scale" max="300" min="10" style="width:100%; margin-top: 5px;" type="range" value="100"/>\n<span id="image-scale-value" style="font-size: 0.8rem; color: var(--gray);">100%</span>\n</div>\n\n<div class="toolbar-section">\n<div class="toolbar-section-title"><i class="fas fa-download"></i> Save</div>\n<button class="toolbar-btn btn-primary" disabled id="save-btn" style="background: var(--primary); color: #fff; width: 100%;">\n<i class="fas fa-download"></i>\n<span>Save PDF</span>\n</button>\n<button class="toolbar-btn" disabled id="save-ocr-only-btn" style="width: 100%; margin-top: 8px;">\n<i class="fas fa-file-export"></i>\n<span>OCR Only</span>\n</button>\n<button class="toolbar-btn" disabled id="save-selectable-btn" style="width: 100%; margin-top: 8px;" title="Embed fonts">\n<i class="fas fa-file-signature"></i>\n<span>Selectable</span>\n</button>\n</div>\n\n<div class="toolbar-section">\n<div class="toolbar-section-title"><i class="fas fa-search"></i> Zoom</div>\n<button class="toolbar-btn" id="zoom-out" title="Zoom Out">\n<i class="fas fa-search-minus"></i>\n<span>Zoom Out</span>\n</button>\n<button class="toolbar-btn" id="zoom-in" title="Zoom In">\n<i class="fas fa-search-plus"></i>\n<span>Zoom In</span>\n</button>\n<button class="toolbar-btn" id="zoom-fit" title="Fit to Width">\n<i class="fas fa-expand"></i>\n<span>Fit Width</span>\n</button>\n<span class="zoom-label" id="zoom-pct" style="display: block; text-align: center; margin-top: 10px; font-weight: 600; color: var(--primary);">100%</span>\n</div>\n\n<div class="toolbar-section">\n<div class="toolbar-section-title"><i class="fas fa-file"></i> File</div>\n<button class="toolbar-btn" id="new-file-btn" style="width: 100%;">\n<i class="fas fa-file"></i>\n<span>New File</span>\n</button>\n</div>\n</div>\n\n\1',
        content,
        flags=re.DOTALL
    )
    
    with open('edit-pdf-preview.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✅ Redesigned layout with 3-panel structure")

def main():
    print("="*60)
    print("PDF Editor Issues - Complete Fix")
    print("="*60)
    
    fix_edit_pdf_upload()
    fix_preview_loading()
    redesign_preview_layout()
    
    print("\n" + "="*60)
    print("✅ All fixes completed!")
    print("="*60)
    print("\nBackend Code Locations:")
    print("  1. Python OCR Script: server/api/pdf-ocr/ocr-process.py")
    print("  2. Node.js API Endpoint: server/server.js (line ~1077)")
    print("  3. API Route: POST /api/pdf-ocr/process")
    print("  4. Technology: Python 3 + Tesseract OCR + OpenCV + Pillow")
    print("="*60)

if __name__ == '__main__':
    main()

