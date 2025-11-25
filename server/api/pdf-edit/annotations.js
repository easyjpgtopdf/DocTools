/**
 * PDF Annotations
 * Highlight, comment, stamp, shapes, etc.
 */

const { PDFDocument, rgb, PDFName } = require('pdf-lib');

/**
 * Add highlight annotation
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} highlights - Array of highlight annotations
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function addHighlights(pdfBuffer, highlights) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();
    
    highlights.forEach(({ pageIndex, x, y, width, height, color = [1, 1, 0] }) => {
      if (pageIndex >= 0 && pageIndex < pages.length) {
        const page = pages[pageIndex];
        const pageHeight = page.getHeight();
        
        // Draw highlight rectangle
        page.drawRectangle({
          x: x,
          y: pageHeight - y - height,
          width: width,
          height: height,
          color: rgb(color[0], color[1], color[2]),
          opacity: 0.3,
        });
      }
    });
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error adding highlights:', error);
    throw new Error(`Highlight annotation failed: ${error.message}`);
  }
}

/**
 * Add comment/note annotation
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} comments - Array of comment annotations
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function addComments(pdfBuffer, comments) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();
    
    comments.forEach(({ pageIndex, x, y, text, author = 'User' }) => {
      if (pageIndex >= 0 && pageIndex < pages.length) {
        const page = pages[pageIndex];
        const pageHeight = page.getHeight();
        
        // Draw comment icon (small square)
        page.drawRectangle({
          x: x,
          y: pageHeight - y - 20,
          width: 20,
          height: 20,
          color: rgb(1, 1, 0),
          borderColor: rgb(0, 0, 0),
          borderWidth: 1,
        });
        
        // Add text near comment (as annotation)
        page.drawText(`[${author}]: ${text}`, {
          x: x + 25,
          y: pageHeight - y - 15,
          size: 10,
          color: rgb(0, 0, 0),
        });
      }
    });
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error adding comments:', error);
    throw new Error(`Comment annotation failed: ${error.message}`);
  }
}

/**
 * Add stamp annotation
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} stamps - Array of stamp annotations
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function addStamps(pdfBuffer, stamps) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();
    
    stamps.forEach(({ pageIndex, x, y, stampType = 'APPROVED', width = 100, height = 50 }) => {
      if (pageIndex >= 0 && pageIndex < pages.length) {
        const page = pages[pageIndex];
        const pageHeight = page.getHeight();
        
        // Draw stamp background
        page.drawRectangle({
          x: x,
          y: pageHeight - y - height,
          width: width,
          height: height,
          color: rgb(1, 0, 0),
          borderColor: rgb(0, 0, 0),
          borderWidth: 2,
        });
        
        // Draw stamp text
        page.drawText(stampType, {
          x: x + 10,
          y: pageHeight - y - height / 2 - 5,
          size: 14,
          color: rgb(1, 1, 1),
        });
      }
    });
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error adding stamps:', error);
    throw new Error(`Stamp annotation failed: ${error.message}`);
  }
}

/**
 * Add shapes (rectangle, circle, line)
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} shapes - Array of shape annotations
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function addShapes(pdfBuffer, shapes) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();
    
    shapes.forEach(({ pageIndex, shapeType, x, y, width, height, color = [0, 0, 0], strokeWidth = 2 }) => {
      if (pageIndex >= 0 && pageIndex < pages.length) {
        const page = pages[pageIndex];
        const pageHeight = page.getHeight();
        const pdfY = pageHeight - y - height;
        
        if (shapeType === 'rectangle') {
          page.drawRectangle({
            x: x,
            y: pdfY,
            width: width,
            height: height,
            borderColor: rgb(color[0], color[1], color[2]),
            borderWidth: strokeWidth,
          });
        } else if (shapeType === 'circle') {
          // Draw circle using rectangle with rounded corners (approximation)
          const radius = Math.min(width, height) / 2;
          page.drawCircle({
            x: x + width / 2,
            y: pdfY + height / 2,
            size: radius,
            borderColor: rgb(color[0], color[1], color[2]),
            borderWidth: strokeWidth,
          });
        } else if (shapeType === 'line') {
          page.drawLine({
            start: { x: x, y: pdfY },
            end: { x: x + width, y: pdfY + height },
            thickness: strokeWidth,
            color: rgb(color[0], color[1], color[2]),
          });
        }
      }
    });
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error adding shapes:', error);
    throw new Error(`Shape annotation failed: ${error.message}`);
  }
}

module.exports = {
  addHighlights,
  addComments,
  addStamps,
  addShapes
};

