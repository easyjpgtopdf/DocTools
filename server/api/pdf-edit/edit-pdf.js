/**
 * PDF Editing API
 * Supports text editing, image insertion, and content manipulation
 * Uses pdf-lib for high-quality PDF manipulation
 */

const { PDFDocument, rgb, PDFPage, PDFFont } = require('pdf-lib');
const fs = require('fs');
const path = require('path');

/**
 * Edit text in PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} textEdits - Array of text edit operations
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function editPDFText(pdfBuffer, textEdits) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();
    
    // Process each text edit
    for (const edit of textEdits) {
      const { pageIndex, x, y, text, fontSize = 12, fontColor = [0, 0, 0], fontName = 'Helvetica' } = edit;
      
      if (pageIndex < 0 || pageIndex >= pages.length) {
        throw new Error(`Invalid page index: ${pageIndex}`);
      }
      
      const page = pages[pageIndex];
      
      // Get or embed font
      let font;
      try {
        font = await pdfDoc.embedFont(fontName);
      } catch (e) {
        // Fallback to Helvetica if font embedding fails
        font = await pdfDoc.embedFont('Helvetica');
      }
      
      // Draw text
      page.drawText(text, {
        x: x || 50,
        y: y || page.getHeight() - 50,
        size: fontSize,
        font: font,
        color: rgb(fontColor[0] / 255, fontColor[1] / 255, fontColor[2] / 255),
      });
    }
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error editing PDF text:', error);
    throw new Error(`PDF text editing failed: ${error.message}`);
  }
}

/**
 * Insert image into PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} imageInserts - Array of image insert operations
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function insertImageIntoPDF(pdfBuffer, imageInserts) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();
    
    // Process each image insert
    for (const insert of imageInserts) {
      const { 
        pageIndex, 
        imageData, // Base64 or Buffer
        x, 
        y, 
        width, 
        height,
        opacity = 1.0
      } = insert;
      
      if (pageIndex < 0 || pageIndex >= pages.length) {
        throw new Error(`Invalid page index: ${pageIndex}`);
      }
      
      const page = pages[pageIndex];
      
      // Convert base64 to buffer if needed
      let imageBuffer;
      if (typeof imageData === 'string') {
        if (imageData.startsWith('data:image')) {
          imageData = imageData.split(',')[1];
        }
        imageBuffer = Buffer.from(imageData, 'base64');
      } else {
        imageBuffer = imageData;
      }
      
      // Embed image
      let image;
      const imageType = insert.imageType || 'png'; // png, jpg, jpeg
      
      try {
        if (imageType.toLowerCase() === 'png') {
          image = await pdfDoc.embedPng(imageBuffer);
        } else {
          image = await pdfDoc.embedJpg(imageBuffer);
        }
      } catch (error) {
        // Try PNG if JPG fails
        try {
          image = await pdfDoc.embedPng(imageBuffer);
        } catch (e) {
          throw new Error(`Failed to embed image: ${e.message}`);
        }
      }
      
      // Calculate dimensions
      const imageDims = image.scale(1);
      const finalWidth = width || imageDims.width;
      const finalHeight = height || (width ? (imageDims.height * width / imageDims.width) : imageDims.height);
      
      // Draw image
      page.drawImage(image, {
        x: x || 50,
        y: y || page.getHeight() - finalHeight - 50,
        width: finalWidth,
        height: finalHeight,
        opacity: opacity,
      });
    }
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error inserting image into PDF:', error);
    throw new Error(`PDF image insertion failed: ${error.message}`);
  }
}

/**
 * Combined PDF editing (text + images)
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Object} edits - Edit operations
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function editPDF(pdfBuffer, edits) {
  try {
    let resultBuffer = pdfBuffer;
    
    // Apply text edits first
    if (edits.textEdits && edits.textEdits.length > 0) {
      resultBuffer = await editPDFText(resultBuffer, edits.textEdits);
    }
    
    // Then apply image inserts
    if (edits.imageInserts && edits.imageInserts.length > 0) {
      resultBuffer = await insertImageIntoPDF(resultBuffer, edits.imageInserts);
    }
    
    return resultBuffer;
  } catch (error) {
    console.error('Error editing PDF:', error);
    throw error;
  }
}

/**
 * Replace text in PDF (finds and replaces text)
 * Note: This is complex as PDFs don't store text as editable strings
 * This function adds new text at specified positions
 */
async function replaceTextInPDF(pdfBuffer, replacements) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const pages = pdfDoc.getPages();
    
    for (const replacement of replacements) {
      const { pageIndex, oldText, newText, x, y, fontSize = 12, fontColor = [0, 0, 0] } = replacement;
      
      if (pageIndex < 0 || pageIndex >= pages.length) {
        continue;
      }
      
      const page = pages[pageIndex];
      const font = await pdfDoc.embedFont('Helvetica');
      
      // Draw new text (we can't actually "replace" text, we overlay it)
      // For true replacement, OCR + text layer editing is needed
      page.drawText(newText, {
        x: x || 50,
        y: y || page.getHeight() - 50,
        size: fontSize,
        font: font,
        color: rgb(fontColor[0] / 255, fontColor[1] / 255, fontColor[2] / 255),
      });
    }
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error replacing text in PDF:', error);
    throw new Error(`PDF text replacement failed: ${error.message}`);
  }
}

module.exports = {
  editPDFText,
  insertImageIntoPDF,
  editPDF,
  replaceTextInPDF
};

