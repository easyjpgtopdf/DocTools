// Archive Converter Utility
// Handles conversion for all archive tools

// Load JSZip library dynamically
function loadJSZip() {
    return new Promise((resolve, reject) => {
        if (window.JSZip) {
            resolve(window.JSZip);
            return;
        }
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
        script.onload = () => resolve(window.JSZip);
        script.onerror = () => reject(new Error('Failed to load JSZip'));
        document.head.appendChild(script);
    });
}

// Store files in sessionStorage
function storeFilesForConversion(files, toolType) {
    const fileData = [];
    const promises = [];
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const promise = new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                fileData.push({
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    data: e.target.result
                });
                resolve();
            };
            reader.readAsArrayBuffer(file);
        });
        promises.push(promise);
    }
    
    return Promise.all(promises).then(() => {
        sessionStorage.setItem(`archive_${toolType}_files`, JSON.stringify(fileData));
        sessionStorage.setItem(`archive_${toolType}_tool`, toolType);
        return fileData;
    });
}

// Get stored files
function getStoredFiles(toolType) {
    const stored = sessionStorage.getItem(`archive_${toolType}_files`);
    return stored ? JSON.parse(stored) : null;
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

// Convert ZIP to RAR (Note: RAR creation requires server-side, so we'll create a ZIP with .rar extension as fallback)
async function convertZipToRar(zipFile) {
    const JSZip = await loadJSZip();
    const zip = await JSZip.loadAsync(zipFile.data);
    
    // Since we can't create RAR in browser, we'll create a ZIP file
    // In production, this should call a server-side API
    const newZip = new JSZip();
    
    // Copy all files from original ZIP
    zip.forEach((relativePath, file) => {
        if (!file.dir) {
            newZip.file(relativePath, file.async('arraybuffer'));
        } else {
            newZip.folder(relativePath);
        }
    });
    
    const blob = await newZip.generateAsync({ type: 'blob', compression: 'DEFLATE' });
    const filename = zipFile.name.replace(/\.zip$/i, '.rar');
    return { blob, filename };
}

// Convert RAR to ZIP (Extract and re-zip)
async function convertRarToZip(rarFile) {
    // Note: RAR extraction in browser is limited. For now, we'll show a message.
    // In production, use a server-side API or library like unrar.js
    throw new Error('RAR to ZIP conversion requires server-side processing. Please use a server API.');
}

// Extract ZIP files
async function extractZip(zipFile) {
    const JSZip = await loadJSZip();
    const zip = await JSZip.loadAsync(zipFile.data);
    const extractedFiles = [];
    
    for (const relativePath of Object.keys(zip.files)) {
        const file = zip.files[relativePath];
        if (!file.dir) {
            const content = await file.async('blob');
            extractedFiles.push({
                name: relativePath,
                blob: content,
                size: content.size
            });
        }
    }
    
    return extractedFiles;
}

// Extract RAR (requires server-side)
async function extractRar(rarFile) {
    throw new Error('RAR extraction requires server-side processing. Please use a server API.');
}

// Extract 7Z (requires server-side)
async function extract7z(sevenZFile) {
    throw new Error('7Z extraction requires server-side processing. Please use a server API.');
}

// Extract ISO (requires server-side)
async function extractISO(isoFile) {
    throw new Error('ISO extraction requires server-side processing. Please use a server API.');
}

// Convert 7Z to ZIP
async function convert7zToZip(sevenZFile) {
    throw new Error('7Z to ZIP conversion requires server-side processing. Please use a server API.');
}

// Convert TAR to ZIP
async function convertTarToZip(tarFile) {
    // TAR extraction in browser is possible with libraries, but for now we'll use server-side
    throw new Error('TAR to ZIP conversion requires server-side processing. Please use a server API.');
}

// Create ZIP from folder
async function folderToZip(folderFiles) {
    const JSZip = await loadJSZip();
    const zip = new JSZip();
    
    for (const fileData of folderFiles) {
        // Handle both File objects and stored file data
        let file, path;
        if (fileData instanceof File) {
            file = fileData;
            path = file.webkitRelativePath || file.name;
        } else {
            // Stored file data from sessionStorage
            file = new File([fileData.data], fileData.name, { type: fileData.type });
            path = fileData.webkitRelativePath || fileData.name;
        }
        
        // Read file content
        const content = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsArrayBuffer(file);
        });
        
        zip.file(path, content);
    }
    
    const blob = await zip.generateAsync({ type: 'blob', compression: 'DEFLATE' });
    const folderName = folderFiles[0]?.webkitRelativePath?.split('/')[0] || 
                      (folderFiles[0]?.name ? folderFiles[0].name.split('/')[0] : 'folder');
    const filename = `${folderName.replace(/[^a-zA-Z0-9]/g, '_')}.zip`;
    return { blob, filename };
}

// Batch ZIP converter
async function batchConvertZip(files, targetFormat) {
    const JSZip = await loadJSZip();
    const convertedFiles = [];
    
    for (const file of files) {
        if (/\.zip$/i.test(file.name)) {
            const zip = await JSZip.loadAsync(file.data);
            // For now, just re-zip (in production, convert to target format)
            const newZip = new JSZip();
            zip.forEach((relativePath, zipFile) => {
                if (!zipFile.dir) {
                    newZip.file(relativePath, zipFile.async('arraybuffer'));
                }
            });
            const blob = await newZip.generateAsync({ type: 'blob' });
            const ext = targetFormat === 'rar' ? '.rar' : '.zip';
            const filename = file.name.replace(/\.zip$/i, ext);
            convertedFiles.push({ blob, filename });
        }
    }
    
    return convertedFiles;
}

// Main conversion function
async function convertArchive(files, toolType) {
    try {
        const JSZip = await loadJSZip();
        
        switch(toolType) {
            case 'zip-to-rar':
                if (files.length === 0) throw new Error('No files to convert');
                const rarResult = await convertZipToRar(files[0]);
                return [rarResult];
                
            case 'rar-to-zip':
                throw new Error('RAR to ZIP conversion requires server-side processing. This feature will be available soon.');
                
            case 'zip-extractor':
                if (files.length === 0) throw new Error('No files to extract');
                const extracted = await extractZip(files[0]);
                // Return extracted files with proper structure
                return extracted.map(f => ({ 
                    blob: f.blob, 
                    filename: f.name,
                    isExtracted: true 
                }));
                
            case 'rar-extractor':
                throw new Error('RAR extraction requires server-side processing. This feature will be available soon.');
                
            case '7z-extractor':
                throw new Error('7Z extraction requires server-side processing. This feature will be available soon.');
                
            case '7z-to-zip':
                throw new Error('7Z to ZIP conversion requires server-side processing. This feature will be available soon.');
                
            case 'tar-to-zip':
                throw new Error('TAR to ZIP conversion requires server-side processing. This feature will be available soon.');
                
            case 'iso-extractor':
                throw new Error('ISO extraction requires server-side processing. This feature will be available soon.');
                
            case 'folder-to-zip':
                if (files.length === 0) throw new Error('No folder selected');
                const folderResult = await folderToZip(files);
                return [folderResult];
                
            case 'batch-zip-converter':
                if (files.length === 0) throw new Error('No files to convert');
                return await batchConvertZip(files, 'zip');
                
            default:
                throw new Error('Unknown conversion type');
        }
    } catch (error) {
        console.error('Conversion error:', error);
        throw error;
    }
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        loadJSZip,
        storeFilesForConversion,
        getStoredFiles,
        downloadFile,
        convertArchive
    };
}

