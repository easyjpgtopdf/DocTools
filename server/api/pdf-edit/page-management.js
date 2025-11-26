/**
 * PDF Page Management
 * Rotate, delete, reorder, extract pages
 */

const { PDFDocument } = require('pdf-lib');

/**
 * Rotate pages in PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} rotations - Array of {pageIndex, angle} where angle is 90, 180, or 270
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function rotatePages(pdfBuffer, rotations) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();
    
    rotations.forEach(({ pageIndex, angle }) => {
      if (pageIndex >= 0 && pageIndex < pages.length) {
        const page = pages[pageIndex];
        const currentRotation = page.getRotation().angle;
        page.setRotation({ angle: currentRotation + angle });
      }
    });
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error rotating pages:', error);
    throw new Error(`Page rotation failed: ${error.message}`);
  }
}

/**
 * Delete pages from PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} pageIndices - Array of page indices to delete (0-based)
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function deletePages(pdfBuffer, pageIndices) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const totalPages = pdfDoc.getPageCount();
    
    // Sort indices in descending order to delete from end
    const sortedIndices = [...pageIndices].sort((a, b) => b - a);
    
    sortedIndices.forEach(pageIndex => {
      if (pageIndex >= 0 && pageIndex < totalPages) {
        pdfDoc.removePage(pageIndex);
      }
    });
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error deleting pages:', error);
    throw new Error(`Page deletion failed: ${error.message}`);
  }
}

/**
 * Reorder pages in PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} newOrder - Array of page indices in new order (0-based)
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function reorderPages(pdfBuffer, newOrder) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const totalPages = pdfDoc.getPageCount();
    
    // Validate new order
    if (newOrder.length !== totalPages) {
      throw new Error(`New order must contain ${totalPages} pages`);
    }
    
    // Create new PDF with reordered pages
    const newPdf = await PDFDocument.create();
    const pages = await newPdf.copyPages(pdfDoc, newOrder);
    pages.forEach(page => newPdf.addPage(page));
    
    const editedPdfBytes = await newPdf.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error reordering pages:', error);
    throw new Error(`Page reordering failed: ${error.message}`);
  }
}

/**
 * Extract pages from PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} pageIndices - Array of page indices to extract (0-based)
 * @returns {Promise<Buffer>} New PDF with extracted pages
 */
async function extractPages(pdfBuffer, pageIndices) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const newPdf = await PDFDocument.create();
    
    const pages = await newPdf.copyPages(pdfDoc, pageIndices);
    pages.forEach(page => newPdf.addPage(page));
    
    const editedPdfBytes = await newPdf.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error extracting pages:', error);
    throw new Error(`Page extraction failed: ${error.message}`);
  }
}

/**
 * Add a new page to PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Number} pageIndex - Index where to insert (0-based), or -1 to append
 * @param {Boolean} insertAfter - If true, insert after pageIndex; if false, insert before
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function addPage(pdfBuffer, pageIndex = -1, insertAfter = true) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const totalPages = pdfDoc.getPageCount();
    
    if (pageIndex === -1 || pageIndex >= totalPages) {
      // Append at the end - create blank page
      const newPage = pdfDoc.addPage();
      // Set default size (A4)
      newPage.setSize(595, 842);
    } else {
      // Insert at specific position
      const insertIndex = insertAfter ? pageIndex + 1 : pageIndex;
      if (insertIndex >= 0 && insertIndex <= totalPages) {
        // Create a blank page
        const newPage = pdfDoc.insertPage(insertIndex);
        // Set default size (A4)
        newPage.setSize(595, 842);
      }
    }
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error adding page:', error);
    throw new Error(`Page addition failed: ${error.message}`);
  }
}

module.exports = {
  rotatePages,
  deletePages,
  reorderPages,
  extractPages,
  addPage
};

