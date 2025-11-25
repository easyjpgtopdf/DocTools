/**
 * PDF Export to Multiple Formats
 * Export PDF to Word, Excel, PPT, Images, etc.
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

/**
 * Export PDF to Word (DOCX)
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @returns {Promise<Buffer>} DOCX file buffer
 */
async function exportToWord(pdfBuffer) {
  try {
    // Save PDF temporarily
    const tempPdfPath = path.join(__dirname, '../../temp', `export-${Date.now()}.pdf`);
    const tempDocxPath = tempPdfPath.replace('.pdf', '.docx');
    
    // Ensure temp directory exists
    const tempDir = path.dirname(tempPdfPath);
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }
    
    fs.writeFileSync(tempPdfPath, pdfBuffer);
    
    // Use LibreOffice to convert
    try {
      await execAsync(`soffice --headless --convert-to docx --outdir "${tempDir}" "${tempPdfPath}"`);
      
      if (fs.existsSync(tempDocxPath)) {
        const docxBuffer = fs.readFileSync(tempDocxPath);
        // Cleanup
        fs.unlinkSync(tempPdfPath);
        fs.unlinkSync(tempDocxPath);
        return docxBuffer;
      }
    } catch (e) {
      // LibreOffice not available
      throw new Error('LibreOffice not installed. Cannot export to Word format.');
    }
    
    throw new Error('Word export failed');
  } catch (error) {
    console.error('Error exporting to Word:', error);
    throw new Error(`Word export failed: ${error.message}`);
  }
}

/**
 * Export PDF to Excel (XLSX)
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @returns {Promise<Buffer>} XLSX file buffer
 */
async function exportToExcel(pdfBuffer) {
  try {
    const tempPdfPath = path.join(__dirname, '../../temp', `export-${Date.now()}.pdf`);
    const tempXlsxPath = tempPdfPath.replace('.pdf', '.xlsx');
    const tempDir = path.dirname(tempPdfPath);
    
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }
    
    fs.writeFileSync(tempPdfPath, pdfBuffer);
    
    try {
      await execAsync(`soffice --headless --convert-to xlsx --outdir "${tempDir}" "${tempPdfPath}"`);
      
      if (fs.existsSync(tempXlsxPath)) {
        const xlsxBuffer = fs.readFileSync(tempXlsxPath);
        fs.unlinkSync(tempPdfPath);
        fs.unlinkSync(tempXlsxPath);
        return xlsxBuffer;
      }
    } catch (e) {
      throw new Error('LibreOffice not installed. Cannot export to Excel format.');
    }
    
    throw new Error('Excel export failed');
  } catch (error) {
    console.error('Error exporting to Excel:', error);
    throw new Error(`Excel export failed: ${error.message}`);
  }
}

/**
 * Export PDF to PowerPoint (PPTX)
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @returns {Promise<Buffer>} PPTX file buffer
 */
async function exportToPowerPoint(pdfBuffer) {
  try {
    const tempPdfPath = path.join(__dirname, '../../temp', `export-${Date.now()}.pdf`);
    const tempPptxPath = tempPdfPath.replace('.pdf', '.pptx');
    const tempDir = path.dirname(tempPdfPath);
    
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }
    
    fs.writeFileSync(tempPdfPath, pdfBuffer);
    
    try {
      await execAsync(`soffice --headless --convert-to pptx --outdir "${tempDir}" "${tempPdfPath}"`);
      
      if (fs.existsSync(tempPptxPath)) {
        const pptxBuffer = fs.readFileSync(tempPptxPath);
        fs.unlinkSync(tempPdfPath);
        fs.unlinkSync(tempPptxPath);
        return pptxBuffer;
      }
    } catch (e) {
      throw new Error('LibreOffice not installed. Cannot export to PowerPoint format.');
    }
    
    throw new Error('PowerPoint export failed');
  } catch (error) {
    console.error('Error exporting to PowerPoint:', error);
    throw new Error(`PowerPoint export failed: ${error.message}`);
  }
}

/**
 * Export PDF pages to images
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Object} options - Export options
 * @returns {Promise<Array>} Array of image buffers
 */
async function exportToImages(pdfBuffer, options = {}) {
  try {
    const { format = 'png', dpi = 150, pageIndices = null } = options;
    const pdfjsLib = require('pdfjs-dist');
    
    const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(pdfBuffer) });
    const pdfDoc = await loadingTask.promise;
    const numPages = pdfDoc.numPages;
    
    const images = [];
    const pagesToExport = pageIndices || Array.from({ length: numPages }, (_, i) => i);
    
    for (const pageIndex of pagesToExport) {
      if (pageIndex >= 0 && pageIndex < numPages) {
        const page = await pdfDoc.getPage(pageIndex + 1);
        const viewport = page.getViewport({ scale: dpi / 72 });
        
        const canvas = require('canvas').createCanvas(viewport.width, viewport.height);
        const context = canvas.getContext('2d');
        
        await page.render({
          canvasContext: context,
          viewport: viewport
        }).promise;
        
        const imageBuffer = canvas.toBuffer(`image/${format}`);
        images.push({
          pageIndex: pageIndex,
          image: imageBuffer,
          format: format
        });
      }
    }
    
    return images;
  } catch (error) {
    console.error('Error exporting to images:', error);
    throw new Error(`Image export failed: ${error.message}`);
  }
}

module.exports = {
  exportToWord,
  exportToExcel,
  exportToPowerPoint,
  exportToImages
};

