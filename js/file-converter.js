// File Converter Utility
// Handles conversion for e-book and image tools

// Store files in sessionStorage
function storeFilesForConversion(files, toolType) {
    const fileData = [];
    const promises = [];
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const promise = new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                // Convert ArrayBuffer to base64 for storage
                const arrayBuffer = e.target.result;
                const uint8Array = new Uint8Array(arrayBuffer);
                const base64 = btoa(String.fromCharCode.apply(null, uint8Array));
                
                fileData.push({
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    data: base64  // Store as base64 string
                });
                resolve();
            };
            reader.onerror = (error) => {
                console.error('Error reading file:', error);
                resolve(); // Continue even if one file fails
            };
            reader.readAsArrayBuffer(file);
        });
        promises.push(promise);
    }
    
    return Promise.all(promises).then(() => {
        try {
            sessionStorage.setItem(`file_${toolType}_files`, JSON.stringify(fileData));
            sessionStorage.setItem(`file_${toolType}_tool`, toolType);
            return fileData;
        } catch (error) {
            console.error('Error storing files in sessionStorage:', error);
            throw new Error('Failed to store files. Please try with fewer or smaller files.');
        }
    });
}

// Get stored files
function getStoredFiles(toolType) {
    try {
        const stored = sessionStorage.getItem(`file_${toolType}_files`);
        if (!stored) return null;
        
        const fileData = JSON.parse(stored);
        // Convert base64 back to ArrayBuffer
        return fileData.map(item => {
            if (typeof item.data === 'string') {
                // Convert base64 string back to ArrayBuffer
                const binaryString = atob(item.data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                return {
                    name: item.name,
                    size: item.size,
                    type: item.type,
                    data: bytes.buffer  // Return as ArrayBuffer
                };
            }
            return item; // Already in correct format
        });
    } catch (error) {
        console.error('Error retrieving stored files:', error);
        return null;
    }
}

// Download file as blob
function downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 100);
}

// Main conversion function
async function convertFile(files, toolType) {
    try {
        // For now, most conversions require server-side processing
        // This is a placeholder that will be implemented based on browser capabilities
        
        switch(toolType) {
            // Image conversions that can work in browser
            case 'webp-to-png':
            case 'png-to-webp':
            case 'jpg-to-webp':
            case 'bmp-to-jpg':
            case 'bmp-to-png':
            case 'tiff-to-png':
            case 'png-to-ico':
            case 'svg-to-png':
            case 'svg-to-jpg':
            case 'avif-to-jpg':
            case 'avif-to-png':
                return await convertImageInBrowser(files, toolType);
            
            // Text to PDF (can work in browser with jsPDF)
            case 'txt-to-pdf':
                return await convertTextToPdf(files);
            
            // PDF to Text (can extract text in browser)
            case 'pdf-to-text':
                return await convertPdfToText(files);
            
            // Image editing tools
            case 'transparent-background-maker':
                return await removeBackground(files);
            case 'exif-data-remove':
                return await removeExifData(files);
            case 'image-cropper':
                return await cropImage(files);
            case 'photo-enhancer':
                return await enhancePhoto(files);
            
            // E-book and other formats require server-side
            default:
                throw new Error(`${toolType} conversion requires server-side processing. This feature will be available soon.`);
        }
    } catch (error) {
        console.error('Conversion error:', error);
        throw error;
    }
}

// Convert images in browser using Canvas API
async function convertImageInBrowser(files, toolType) {
    const convertedFiles = [];
    
    for (const fileData of files) {
        const file = new File([fileData.data], fileData.name, { type: fileData.type });
        const img = await loadImage(file);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        let outputFormat = 'image/png';
        let outputExt = '.png';
        
        // Determine output format based on tool type
        if (toolType.includes('webp')) {
            outputFormat = 'image/webp';
            outputExt = '.webp';
        } else if (toolType.includes('jpg') || toolType.includes('jpeg')) {
            outputFormat = 'image/jpeg';
            outputExt = '.jpg';
        } else if (toolType.includes('ico')) {
            outputFormat = 'image/x-icon';
            outputExt = '.ico';
        }
        
        const blob = await new Promise((resolve) => {
            canvas.toBlob(resolve, outputFormat, 0.95);
        });
        
        const filename = fileData.name.replace(/\.[^.]+$/, outputExt);
        convertedFiles.push({ blob, filename });
    }
    
    return convertedFiles;
}

// Load image from file
function loadImage(file) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(file);
        img.onload = () => {
            URL.revokeObjectURL(url);
            resolve(img);
        };
        img.onerror = reject;
        img.src = url;
    });
}

// Convert text to PDF
async function convertTextToPdf(files) {
    // Load jsPDF dynamically
    if (!window.jspdf) {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
        await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    const { jsPDF } = window.jspdf;
    const convertedFiles = [];
    
    for (const fileData of files) {
        const text = new TextDecoder().decode(fileData.data);
        const pdf = new jsPDF();
        
        // Split text into lines that fit the page
        const lines = pdf.splitTextToSize(text, 180);
        pdf.text(lines, 10, 10);
        
        const blob = pdf.output('blob');
        const filename = fileData.name.replace(/\.txt$/i, '.pdf');
        convertedFiles.push({ blob, filename });
    }
    
    return convertedFiles;
}

// Convert PDF to Text
async function convertPdfToText(files) {
    // Load pdf.js dynamically
    if (!window.pdfjsLib) {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
        await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
        // Also load worker
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }
    
    const convertedFiles = [];
    
    for (const fileData of files) {
        // Ensure data is ArrayBuffer or Uint8Array
        let data;
        if (fileData.data instanceof ArrayBuffer) {
            data = new Uint8Array(fileData.data);
        } else if (fileData.data instanceof Uint8Array) {
            data = fileData.data;
        } else {
            console.error('Invalid file data format:', fileData);
            continue;
        }
        
        const pdf = await window.pdfjsLib.getDocument({ data }).promise;
        let text = '';
        
        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            text += textContent.items.map(item => item.str).join(' ') + '\n';
        }
        
        const blob = new Blob([text], { type: 'text/plain' });
        const filename = fileData.name.replace(/\.pdf$/i, '.txt');
        convertedFiles.push({ blob, filename });
    }
    
    return convertedFiles;
}

// Remove background (simplified - requires advanced processing)
async function removeBackground(files) {
    // This would require a more advanced library or server-side processing
    // For now, return original file with a message
    throw new Error('Background removal requires advanced processing. This feature will be available soon.');
}

// Remove EXIF data
async function removeExifData(files) {
    // Load exif-js or use canvas to strip metadata
    const convertedFiles = [];
    
    for (const fileData of files) {
        const file = new File([fileData.data], fileData.name, { type: fileData.type });
        const img = await loadImage(file);
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        // Canvas automatically strips EXIF data
        const blob = await new Promise((resolve) => {
            canvas.toBlob(resolve, fileData.type || 'image/jpeg', 0.95);
        });
        
        convertedFiles.push({ blob, filename: fileData.name });
    }
    
    return convertedFiles;
}

// Crop image (simplified - would need UI for selection)
async function cropImage(files) {
    throw new Error('Image cropping requires interactive selection. This feature will be available soon.');
}

// Enhance photo (simplified - requires advanced processing)
async function enhancePhoto(files) {
    throw new Error('Photo enhancement requires advanced processing. This feature will be available soon.');
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        storeFilesForConversion,
        getStoredFiles,
        downloadFile,
        convertFile
    };
}

