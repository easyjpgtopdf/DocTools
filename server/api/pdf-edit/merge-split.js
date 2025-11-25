/**
 * PDF Merge and Split
 * Merge multiple PDFs or split PDF into multiple files
 */

const { PDFDocument } = require('pdf-lib');

/**
 * Merge multiple PDFs
 * @param {Array<Buffer>} pdfBuffers - Array of PDF file buffers
 * @returns {Promise<Buffer>} Merged PDF buffer
 */
async function mergePDFs(pdfBuffers) {
  try {
    const mergedPdf = await PDFDocument.create();
    
    for (const pdfBuffer of pdfBuffers) {
      const pdfDoc = await PDFDocument.load(pdfBuffer);
      const pages = await mergedPdf.copyPages(pdfDoc, pdfDoc.getPageIndices());
      pages.forEach(page => mergedPdf.addPage(page));
    }
    
    const mergedBytes = await mergedPdf.save();
    return Buffer.from(mergedBytes);
  } catch (error) {
    console.error('Error merging PDFs:', error);
    throw new Error(`PDF merge failed: ${error.message}`);
  }
}

/**
 * Split PDF into multiple files
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} splitRanges - Array of {start, end} page ranges (1-based)
 * @returns {Promise<Array<Buffer>>} Array of split PDF buffers
 */
async function splitPDF(pdfBuffer, splitRanges) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const totalPages = pdfDoc.getPageCount();
    const splitPdfs = [];
    
    for (const range of splitRanges) {
      const { start, end } = range;
      const startIndex = Math.max(0, start - 1); // Convert to 0-based
      const endIndex = Math.min(totalPages, end); // Keep 1-based for slice
      
      if (startIndex < endIndex && startIndex < totalPages) {
        const pageIndices = Array.from({ length: endIndex - startIndex }, (_, i) => startIndex + i);
        const newPdf = await PDFDocument.create();
        const pages = await newPdf.copyPages(pdfDoc, pageIndices);
        pages.forEach(page => newPdf.addPage(page));
        
        const splitBytes = await newPdf.save();
        splitPdfs.push(Buffer.from(splitBytes));
      }
    }
    
    return splitPdfs;
  } catch (error) {
    console.error('Error splitting PDF:', error);
    throw new Error(`PDF split failed: ${error.message}`);
  }
}

/**
 * Split PDF by page count (each file has N pages)
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {number} pagesPerFile - Number of pages per split file
 * @returns {Promise<Array<Buffer>>} Array of split PDF buffers
 */
async function splitPDFByPageCount(pdfBuffer, pagesPerFile) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const totalPages = pdfDoc.getPageCount();
    const splitPdfs = [];
    
    for (let i = 0; i < totalPages; i += pagesPerFile) {
      const endIndex = Math.min(i + pagesPerFile, totalPages);
      const pageIndices = Array.from({ length: endIndex - i }, (_, j) => i + j);
      
      const newPdf = await PDFDocument.create();
      const pages = await newPdf.copyPages(pdfDoc, pageIndices);
      pages.forEach(page => newPdf.addPage(page));
      
      const splitBytes = await newPdf.save();
      splitPdfs.push(Buffer.from(splitBytes));
    }
    
    return splitPdfs;
  } catch (error) {
    console.error('Error splitting PDF by page count:', error);
    throw new Error(`PDF split failed: ${error.message}`);
  }
}

module.exports = {
  mergePDFs,
  splitPDF,
  splitPDFByPageCount
};

