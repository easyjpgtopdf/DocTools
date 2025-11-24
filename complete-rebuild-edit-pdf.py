#!/usr/bin/env python3
"""
Complete rebuild of edit-pdf.html middle section
Keep header and footer, remove ALL old middle content, add fresh clean code
"""

import re

def complete_rebuild():
    print("Reading edit-pdf.html...")
    with open('edit-pdf.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find header end (after breadcrumb nav, before page-wrap)
    header_end_pattern = r'(</nav>\s*<div class="container page-wrap">)'
    header_match = re.search(header_end_pattern, content)
    if not header_match:
        print("❌ Could not find header end")
        return
    
    header_end_pos = header_match.end()
    
    # Find footer start
    footer_start_pattern = r'(<footer>)'
    footer_match = re.search(footer_start_pattern, content)
    if not footer_match:
        print("❌ Could not find footer start")
        return
    
    footer_start_pos = footer_match.start()
    
    # Extract header and footer
    header = content[:header_end_pos]
    footer = content[footer_start_pos:]
    
    # Fresh clean middle section
    fresh_middle = '''<div class="editor-header">
<h1>PDF Editor Online Free - Edit PDF Files Online Without Installation</h1>
<p>Edit PDF files online for free with our advanced PDF editor tool. Add text, images, annotations, highlight content, modify PDF documents, and more - all without software installation. Best free online PDF editor 2024.</p>
</div>

<div class="editor-card">
<div aria-label="Upload your PDF" class="upload-area" id="upload-area" role="button" tabindex="0">
<div class="upload-icon"><i class="fas fa-file-pdf"></i></div>
<h3>Upload Your PDF File</h3>
<p>Drag &amp; drop your PDF file here</p>
<p>or click to browse files</p>
<div style="margin-top:10px">
<label class="btn btn-secondary" for="file-input" id="browse-btn"><i class="fas fa-folder-open"></i> Choose PDF</label>
</div>
<input accept="application/pdf,.pdf" class="file-input" id="file-input" type="file"/>
</div>

<div class="file-info" id="file-info" style="display: none;">
<div class="file-details">
<div class="file-icon"><i class="fas fa-file-pdf"></i></div>
<div class="file-text">
<h4 id="file-name">document.pdf</h4>
<p id="file-size">0 KB</p>
</div>
</div>
</div>

<h2 style="text-align: center; font-size: 1.8rem; color: var(--primary); margin: 30px 0 20px; font-weight: 700;">Features of Our Free PDF Editor</h2>
<div class="features">
<div class="feature-card">
<div class="feature-icon"><i class="fas fa-edit"></i></div>
<h3>Direct Text Editing</h3>
<p>Click and edit text directly on the PDF with real-time preview</p>
</div>
<div class="feature-card">
<div class="feature-icon"><i class="fas fa-palette"></i></div>
<h3>Font Customization</h3>
<p>Change font family, size, color and apply highlights to text</p>
</div>
<div class="feature-card">
<div class="feature-icon"><i class="fas fa-text-height"></i></div>
<h3>Add New Text</h3>
<p>Insert new text anywhere on the PDF document</p>
</div>
<div class="feature-card">
<div class="feature-icon"><i class="fas fa-shield-alt"></i></div>
<h3>Secure &amp; Private</h3>
<p>Your files stay in your browser - no server uploads</p>
</div>
</div>
</div>

<script>
// Set PDF.js worker path
if (typeof pdfjsLib !== 'undefined') {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

// DOM elements
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Handle file selection
function handleFile(file) {
    console.log("File selected:", file);
    
    // Validate file type
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please select a valid PDF file');
        return;
    }
    
    // Check file size (50MB limit)
    if (file.size > 50 * 1024 * 1024) {
        if(!confirm('This file is larger than 50MB. It may be slow to load. Continue?')){ 
            return; 
        }
    }
    
    // Show file info
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.style.display = 'block';
    
    // Store file data and redirect to preview page
    const reader = new FileReader();
    reader.onload = function(e) {
        // Use IndexedDB for large files (better than sessionStorage)
        const request = indexedDB.open('PDFEditorDB', 1);
        
        request.onerror = function() {
            // Fallback: use blob URL if IndexedDB fails
            const blob = new Blob([e.target.result], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            sessionStorage.setItem('pdfFileURL', url);
            sessionStorage.setItem('pdfFileName', file.name);
            sessionStorage.setItem('pdfFileSize', file.size.toString());
            window.location.href = 'edit-pdf-preview.html';
        };
        
        request.onsuccess = function() {
            const db = request.result;
            
            // Create object store if it doesn't exist
            if (!db.objectStoreNames.contains('pdfFiles')) {
                db.close();
                const upgradeRequest = indexedDB.open('PDFEditorDB', 2);
                upgradeRequest.onupgradeneeded = function(event) {
                    const db = event.target.result;
                    if (!db.objectStoreNames.contains('pdfFiles')) {
                        db.createObjectStore('pdfFiles', { keyPath: 'id', autoIncrement: true });
                    }
                };
                upgradeRequest.onsuccess = function() {
                    storeFileAndRedirect(upgradeRequest.result, e.target.result, file);
                };
            } else {
                storeFileAndRedirect(db, e.target.result, file);
            }
        };
        
        request.onupgradeneeded = function(event) {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('pdfFiles')) {
                db.createObjectStore('pdfFiles', { keyPath: 'id', autoIncrement: true });
            }
        };
    };
    
    reader.readAsArrayBuffer(file);
}

// Store file in IndexedDB and redirect
function storeFileAndRedirect(db, fileData, file) {
    const transaction = db.transaction(['pdfFiles'], 'readwrite');
    const store = transaction.objectStore('pdfFiles');
    
    // Clear old files
    store.clear().onsuccess = function() {
        // Store new file
        const request = store.add({
            data: fileData,
            name: file.name,
            size: file.size,
            type: file.type,
            timestamp: Date.now()
        });
        
        request.onsuccess = function() {
            // Store metadata in sessionStorage for quick access
            sessionStorage.setItem('pdfFileId', request.result.toString());
            sessionStorage.setItem('pdfFileName', file.name);
            sessionStorage.setItem('pdfFileSize', file.size.toString());
            sessionStorage.setItem('pdfFileType', file.type);
            
            // Redirect to preview page
            window.location.href = 'edit-pdf-preview.html';
        };
        
        request.onerror = function() {
            console.error('Failed to store file in IndexedDB');
            // Fallback to blob URL
            const blob = new Blob([fileData], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            sessionStorage.setItem('pdfFileURL', url);
            sessionStorage.setItem('pdfFileName', file.name);
            sessionStorage.setItem('pdfFileSize', file.size.toString());
            window.location.href = 'edit-pdf-preview.html';
        };
    };
}

// Event listeners
if (fileInput) {
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    });
}

if (uploadArea) {
    // Click to browse
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Keyboard support
    uploadArea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInput.click();
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFile(file);
        }
    });
}
</script>

<script src="js/auth.js" type="module"></script>
'''
    
    # Rebuild file
    new_content = header + fresh_middle + footer
    
    # Write back
    with open('edit-pdf.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ edit-pdf.html completely rebuilt!")
    print(f"   Header: {len(header):,} bytes")
    print(f"   Middle: {len(fresh_middle):,} bytes")
    print(f"   Footer: {len(footer):,} bytes")
    print(f"   Total: {len(new_content):,} bytes")
    print(f"   Reduction: {len(content) - len(new_content):,} bytes")

if __name__ == '__main__':
    complete_rebuild()

