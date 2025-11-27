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
 * Extract fonts from PDF page with detailed information
 * @param {Object} page - PDF.js page object
 * @returns {Promise<Array>} Array of font information with metrics
 */
async function extractFontsFromPage(page) {
  try {
    const fonts = [];
    const fontsMap = new Map();
    
    // Get text content to extract font names and properties
    const textContent = await page.getTextContent();
    textContent.items.forEach(item => {
      if (item.fontName) {
        if (!fontsMap.has(item.fontName)) {
          fontsMap.set(item.fontName, {
            name: item.fontName,
            type: item.fontName.includes('+') ? 'embedded' : 'standard',
            encoding: item.transform ? 'WinAnsiEncoding' : 'Unicode',
            baseFont: item.fontName.split('+').pop() || item.fontName,
            // Extract font properties from item
            size: Math.abs(item.transform?.[0] || item.transform?.[3] || 12),
            width: item.width || 0,
            height: item.height || 0
          });
        }
      }
    });
    
    // Convert map to array
    fontsMap.forEach(font => {
      fonts.push(font);
    });
    
    return fonts;
  } catch (error) {
    console.warn('Error extracting fonts from page:', error);
    return [];
  }
}

/**
 * Extract font metrics for accurate text width calculation
 * @param {Object} page - PDF.js page object
 * @param {string} fontName - Font name
 * @param {number} fontSize - Font size
 * @returns {Promise<Object>} Font metrics {width, height, ascent, descent}
 */
async function getFontMetrics(page, fontName, fontSize) {
  try {
    const textContent = await page.getTextContent();
    let totalWidth = 0;
    let count = 0;
    
    // Calculate average character width from actual text items
    textContent.items.forEach(item => {
      if (item.fontName === fontName && item.width) {
        totalWidth += item.width;
        count++;
      }
    });
    
    const avgCharWidth = count > 0 ? totalWidth / count : fontSize * 0.6;
    
    return {
      avgCharWidth: avgCharWidth,
      fontSize: fontSize,
      lineHeight: fontSize * 1.2,
      // Estimate metrics based on font size
      ascent: fontSize * 0.8,
      descent: fontSize * 0.2
    };
  } catch (error) {
    console.warn('Error getting font metrics:', error);
    // Fallback to estimated metrics
    return {
      avgCharWidth: fontSize * 0.6,
      fontSize: fontSize,
      lineHeight: fontSize * 1.2,
      ascent: fontSize * 0.8,
      descent: fontSize * 0.2
    };
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

/**
 * Calculate accurate text width using font metrics
 * @param {string} text - Text to measure
 * @param {string} fontName - Font name
 * @param {number} fontSize - Font size
 * @param {Object} fontMetrics - Font metrics object
 * @returns {number} Text width in points
 */
function calculateTextWidth(text, fontName, fontSize, fontMetrics) {
  if (!text || text.length === 0) return 0;
  
  if (fontMetrics && fontMetrics.avgCharWidth) {
    // Use actual font metrics if available
    return text.length * fontMetrics.avgCharWidth;
  }
  
  // Fallback: estimate based on font size
  // Different fonts have different character widths
  const widthMultipliers = {
    'Courier': 0.6,      // Monospace
    'Times-Roman': 0.5,  // Narrow
    'Helvetica': 0.55,   // Medium
    'Arial': 0.55,
    'default': 0.6
  };
  
  const multiplier = widthMultipliers[fontName] || widthMultipliers[fontName?.split('-')[0]] || widthMultipliers['default'];
  return text.length * fontSize * multiplier;
}

module.exports = {
  extractTextWithPositions,
  extractFontsFromPage,
  findTextInPDF,
  getFontsFromPDF,
  getFontMetrics,
  calculateTextWidth
};

