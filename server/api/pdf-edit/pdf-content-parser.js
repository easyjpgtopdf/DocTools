/**
 * PDF Content Stream Parser
 * Extracts text, fonts, and positions from PDF using pdf.js
 * Adobe Acrobat Pro style - Real PDF structure parsing
 */

// Use pdfjs-dist for server-side PDF parsing
let pdfjsLib;
try {
  // Try different import paths for pdfjs-dist
  pdfjsLib = require('pdfjs-dist');
  // Set worker path if needed
  if (pdfjsLib.GlobalWorkerOptions) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = require.resolve('pdfjs-dist/build/pdf.worker.min.js');
  }
} catch (e) {
  try {
    pdfjsLib = require('pdfjs-dist/legacy/build/pdf.js');
  } catch (e2) {
    console.warn('pdfjs-dist not available, text extraction will be limited');
    pdfjsLib = null;
  }
}

/**
 * Extract text with positions and fonts from PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @returns {Promise<Array>} Array of text items with positions, fonts, and properties
 */
async function extractTextWithPositions(pdfBuffer) {
  try {
    if (!pdfjsLib) {
      throw new Error('pdfjs-dist is not available');
    }
    
    const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(pdfBuffer) });
    const pdfDoc = await loadingTask.promise;
    const numPages = pdfDoc.numPages;
    const allTextItems = [];
    
    // Process each page
    for (let pageNum = 1; pageNum <= numPages; pageNum++) {
      const page = await pdfDoc.getPage(pageNum);
      const viewport = page.getViewport({ scale: 1.0 });
      
      // Get text content with positions
      const textContent = await page.getTextContent();
      
      // Extract fonts from page
      const fonts = await extractFontsFromPage(page);
      
      // Process text items
      textContent.items.forEach((item, index) => {
        if (item.str && item.str.trim()) {
          const transform = item.transform || [1, 0, 0, 1, 0, 0];
          const x = transform[4];
          const y = viewport.height - transform[5]; // Convert to bottom-left origin
          const fontSize = Math.abs(transform[0]) || Math.abs(transform[3]) || 12;
          const fontName = item.fontName || 'Helvetica';
          
          // Get font properties
          const fontInfo = fonts.find(f => f.name === fontName) || {
            name: fontName,
            type: 'standard',
            encoding: 'WinAnsiEncoding'
          };
          
          allTextItems.push({
            pageIndex: pageNum - 1,
            text: item.str,
            x: x,
            y: y,
            width: item.width || (item.str.length * fontSize * 0.6),
            height: fontSize,
            fontSize: fontSize,
            fontName: fontName,
            fontType: fontInfo.type,
            fontEncoding: fontInfo.encoding,
            transform: transform,
            itemIndex: index
          });
        }
      });
    }
    
    return allTextItems;
  } catch (error) {
    console.error('Error extracting text from PDF:', error);
    throw new Error(`PDF text extraction failed: ${error.message}`);
  }
}

/**
 * Extract fonts from PDF page
 * @param {Object} page - PDF.js page object
 * @returns {Promise<Array>} Array of font information
 */
async function extractFontsFromPage(page) {
  try {
    const fonts = [];
    const fontsSet = new Set();
    
    // Get text content to extract font names
    const textContent = await page.getTextContent();
    textContent.items.forEach(item => {
      if (item.fontName) {
        fontsSet.add(item.fontName);
      }
    });
    
    // Convert to array with metadata
    fontsSet.forEach(fontName => {
      fonts.push({
        name: fontName,
        type: 'standard', // Most PDFs use standard fonts
        encoding: 'WinAnsiEncoding',
        baseFont: fontName
      });
    });
    
    return fonts;
  } catch (error) {
    console.warn('Error extracting fonts from page:', error);
    return [];
  }
}

/**
 * Find text in PDF by content
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {string} searchText - Text to search for
 * @returns {Promise<Array>} Array of matches with positions
 */
async function findTextInPDF(pdfBuffer, searchText) {
  try {
    const textItems = await extractTextWithPositions(pdfBuffer);
    const matches = [];
    
    textItems.forEach(item => {
      if (item.text.includes(searchText)) {
        matches.push({
          pageIndex: item.pageIndex,
          text: item.text,
          x: item.x,
          y: item.y,
          width: item.width,
          height: item.height,
          fontSize: item.fontSize,
          fontName: item.fontName,
          matchIndex: item.text.indexOf(searchText)
        });
      }
    });
    
    return matches;
  } catch (error) {
    console.error('Error finding text in PDF:', error);
    throw new Error(`Text search failed: ${error.message}`);
  }
}

/**
 * Get font list from PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @returns {Promise<Array>} Array of available fonts
 */
async function getFontsFromPDF(pdfBuffer) {
  try {
    if (!pdfjsLib) {
      return ['Helvetica', 'Times-Roman', 'Courier']; // Fallback
    }
    
    const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(pdfBuffer) });
    const pdfDoc = await loadingTask.promise;
    const fonts = new Set();
    
    // Process first few pages to get fonts
    const pagesToCheck = Math.min(3, pdfDoc.numPages);
    for (let pageNum = 1; pageNum <= pagesToCheck; pageNum++) {
      const page = await pdfDoc.getPage(pageNum);
      const textContent = await page.getTextContent();
      
      textContent.items.forEach(item => {
        if (item.fontName) {
          fonts.add(item.fontName);
        }
      });
    }
    
    return Array.from(fonts);
  } catch (error) {
    console.error('Error getting fonts from PDF:', error);
    return ['Helvetica', 'Times-Roman', 'Courier']; // Fallback to standard fonts
  }
}

module.exports = {
  extractTextWithPositions,
  extractFontsFromPage,
  findTextInPDF,
  getFontsFromPDF
};

