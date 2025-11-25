/**
 * PDF Compression
 * Compress PDF files to reduce size
 */

const { PDFDocument } = require('pdf-lib');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

/**
 * Compress PDF using Ghostscript (best quality)
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Object} options - Compression options
 * @returns {Promise<Buffer>} Compressed PDF buffer
 */
async function compressPDF(pdfBuffer, options = {}) {
  try {
    const {
      quality = 'medium', // 'low', 'medium', 'high'
      dpi = 150
    } = options;
    
    // Quality settings
    const qualitySettings = {
      low: { dpi: 72, quality: '/screen' },
      medium: { dpi: 150, quality: '/ebook' },
      high: { dpi: 300, quality: '/printer' }
    };
    
    const settings = qualitySettings[quality] || qualitySettings.medium;
    
    // Save PDF temporarily
    const tempDir = path.join(__dirname, '../../temp');
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }
    
    const inputPath = path.join(tempDir, `compress-input-${Date.now()}.pdf`);
    const outputPath = path.join(tempDir, `compress-output-${Date.now()}.pdf`);
    
    fs.writeFileSync(inputPath, pdfBuffer);
    
    // Try Ghostscript compression
    try {
      const gsCmd = process.platform === 'win32' 
        ? 'gswin64c' 
        : 'gs';
      
      const gsCommand = `"${gsCmd}" -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=${settings.quality} -dNOPAUSE -dQUIET -dBATCH -dDetectDuplicateImages=true -dCompressFonts=true -r${settings.dpi} -sOutputFile="${outputPath}" "${inputPath}"`;
      
      await execAsync(gsCommand);
      
      if (fs.existsSync(outputPath)) {
        const compressedBuffer = fs.readFileSync(outputPath);
        const originalSize = pdfBuffer.length;
        const compressedSize = compressedBuffer.length;
        const compressionRatio = ((1 - compressedSize / originalSize) * 100).toFixed(1);
        
        // Cleanup
        try {
          fs.unlinkSync(inputPath);
          fs.unlinkSync(outputPath);
        } catch (e) {
          // Ignore cleanup errors
        }
        
        return {
          buffer: compressedBuffer,
          originalSize: originalSize,
          compressedSize: compressedSize,
          compressionRatio: compressionRatio
        };
      }
    } catch (gsError) {
      console.warn('Ghostscript compression failed, using pdf-lib:', gsError.message);
    }
    
    // Fallback: Use pdf-lib (basic compression)
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const compressedBytes = await pdfDoc.save({
      useObjectStreams: true,
      addDefaultPage: false
    });
    
    const compressedBuffer = Buffer.from(compressedBytes);
    const originalSize = pdfBuffer.length;
    const compressedSize = compressedBuffer.length;
    const compressionRatio = ((1 - compressedSize / originalSize) * 100).toFixed(1);
    
    // Cleanup
    try {
      fs.unlinkSync(inputPath);
    } catch (e) {
      // Ignore
    }
    
    return {
      buffer: compressedBuffer,
      originalSize: originalSize,
      compressedSize: compressedSize,
      compressionRatio: compressionRatio
    };
  } catch (error) {
    console.error('Error compressing PDF:', error);
    throw new Error(`PDF compression failed: ${error.message}`);
  }
}

module.exports = {
  compressPDF
};

