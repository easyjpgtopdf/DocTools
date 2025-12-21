/**
 * FREE PDF to Excel Converter (Browser-based, NO AI)
 * 
 * Rules:
 * - ZERO cloud OCR cost
 * - Browser-only processing (PDF.js + SheetJS)
 * - Simple tables only
 * - Text-based PDFs only
 */

/**
 * Convert PDF to Excel using browser-based extraction
 * Returns: { success: boolean, blob: Blob, error?: string }
 */
async function convertPdfToExcelFree(pdfDoc, selectedPages = null) {
    try {
        // Get pages to process
        const totalPages = pdfDoc.numPages;
        const pagesToProcess = selectedPages || Array.from({ length: totalPages }, (_, i) => i + 1);
        
        // Create workbook
        const wb = XLSX.utils.book_new();
        
        // Process each page
        for (const pageNum of pagesToProcess) {
            try {
                const page = await pdfDoc.getPage(pageNum);
                const tables = await extractTablesFromPage(page);
                
                if (tables && tables.length > 0) {
                    // Create worksheet for each table
                    tables.forEach((tableObj, tableIndex) => {
                        // Handle both old format (2D array) and new format (object with data)
                        let table = null;
                        let hasFormatting = false;
                        
                        if (Array.isArray(tableObj)) {
                            // Old format: direct 2D array
                            table = tableObj;
                            hasFormatting = false;
                        } else if (tableObj && tableObj.data) {
                            // New format: object with data property
                            table = tableObj.data;
                            hasFormatting = tableObj.hasFormatting || false;
                        } else {
                            table = tableObj;
                        }
                        
                        // Convert to simple 2D array for XLSX
                        const tableArray = table.map(row => {
                            if (hasFormatting && Array.isArray(row) && row.length > 0 && row[0] && typeof row[0] === 'object' && 'text' in row[0]) {
                                // Row has formatting objects {text, fontName, fontSize, isBold}
                                return row.map(cell => cell.text || (typeof cell === 'string' ? cell : ''));
                            }
                            return row;
                        });
                        
                        const ws = XLSX.utils.aoa_to_sheet(tableArray);
                        
                        // Apply formatting if available
                        if (hasFormatting && Array.isArray(table) && table.length > 0 && table[0] && Array.isArray(table[0]) && table[0][0] && typeof table[0][0] === 'object' && 'text' in table[0][0]) {
                            applyFormattingToWorksheet(ws, table);
                        }
                        
                        // Auto-size columns based on content
                        if (!ws['!cols']) ws['!cols'] = [];
                        const maxCols = Math.max(...tableArray.map(row => row ? row.length : 0), 1);
                        for (let i = 0; i < maxCols; i++) {
                            // Calculate column width based on content
                            let maxWidth = 10;
                            tableArray.forEach(row => {
                                if (row && row[i]) {
                                    const cellText = String(row[i] || '');
                                    maxWidth = Math.max(maxWidth, Math.min(cellText.length + 2, 50));
                                }
                            });
                            ws['!cols'][i] = { wch: maxWidth };
                        }
                        
                        const sheetName = tables.length > 1 
                            ? `Page${pageNum}_Table${tableIndex + 1}` 
                            : `Page${pageNum}`;
                        XLSX.utils.book_append_sheet(wb, ws, sheetName);
                    });
                } else {
                    // Empty page - create empty sheet
                    const ws = XLSX.utils.aoa_to_sheet([['No tables detected on this page']]);
                    XLSX.utils.book_append_sheet(wb, ws, `Page${pageNum}`);
                }
            } catch (pageError) {
                console.warn(`Error processing page ${pageNum}:`, pageError);
                // Create error sheet
                const ws = XLSX.utils.aoa_to_sheet([['Error processing this page']]);
                XLSX.utils.book_append_sheet(wb, ws, `Page${pageNum}_Error`);
            }
        }
        
        // If no sheets created, create one empty sheet
        if (wb.SheetNames.length === 0) {
            const ws = XLSX.utils.aoa_to_sheet([['No data extracted']]);
            XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
        }
        
        // Generate Excel file with cell styles enabled
        const excelBuffer = XLSX.write(wb, { 
            type: 'array', 
            bookType: 'xlsx',
            cellStyles: true // Enable cell styles
        });
        const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        
        return {
            success: true,
            blob: blob,
            pagesProcessed: pagesToProcess.length
        };
        
    } catch (error) {
        console.error('Free conversion error:', error);
        return {
            success: false,
            error: error.message || 'Conversion failed'
        };
    }
}

/**
 * Extract tables from a PDF page using text positioning
 * Uses iLovePDF-like layout reconstruction if available
 * Returns: Array of objects with table data and cell formatting
 */
async function extractTablesFromPage(page) {
    try {
        // Try iLovePDF-style extraction first (if available)
        if (window.PDFExcelILovePDFLayout && window.PDFExcelILovePDFLayout.extractTableILovePDFStyle) {
            try {
                const ilovepdfTable = await window.PDFExcelILovePDFLayout.extractTableILovePDFStyle(page);
                if (ilovepdfTable && ilovepdfTable.length > 0) {
                    return [{ data: ilovepdfTable, hasFormatting: true }];
                }
            } catch (e) {
                console.warn('iLovePDF-style extraction failed, falling back to basic:', e);
            }
        }
        
        // Fallback to basic extraction
        const textContent = await page.getTextContent();
        if (!textContent || !textContent.items || textContent.items.length === 0) {
            return [];
        }
        
        // Group text items by Y position (rows)
        const rowsMap = new Map();
        
        textContent.items.forEach(item => {
            if (!item.transform || item.transform.length < 6) return;
            
            const y = Math.round(item.transform[5] * 10) / 10; // Round to 1 decimal
            const x = Math.round(item.transform[4] * 10) / 10;
            const text = (item.str || '').trim();
            
            if (!text) return;
            
            // Extract font information
            const fontName = item.fontName || 'Arial';
            const fontSize = calculateFontSize(item.transform) || 10;
            const isBold = detectBoldFont(fontName);
            
            if (!rowsMap.has(y)) {
                rowsMap.set(y, []);
            }
            
            rowsMap.get(y).push({ 
                x, 
                text,
                fontName: fontName,
                fontSize: fontSize,
                isBold: isBold
            });
        });
        
        // Sort rows by Y position (top to bottom)
        const sortedRows = Array.from(rowsMap.entries())
            .sort((a, b) => b[0] - a[0]) // Descending (top to bottom)
            .map(entry => entry[1]);
        
        if (sortedRows.length === 0) {
            return [];
        }
        
        // Detect columns (X positions)
        const allXPositions = new Set();
        sortedRows.forEach(row => {
            row.forEach(cell => allXPositions.add(cell.x));
        });
        
        const columns = Array.from(allXPositions).sort((a, b) => a - b);
        
        // Build table: Map each row to columns with formatting
        const table = sortedRows.map((row, rowIndex) => {
            // Sort cells in row by X position
            const sortedCells = row.sort((a, b) => a.x - b.x);
            
            // Create array matching column positions
            const rowArray = new Array(columns.length).fill(null).map(() => ({ text: '', fontName: 'Arial', fontSize: 10, isBold: false }));
            
            sortedCells.forEach(cell => {
                // Find closest column index
                const colIndex = columns.reduce((closest, col, idx) => {
                    return Math.abs(col - cell.x) < Math.abs(columns[closest] - cell.x) ? idx : closest;
                }, 0);
                
                // Merge text if cell already has content
                if (rowArray[colIndex].text) {
                    rowArray[colIndex].text += ' ' + cell.text;
                    // Use the first cell's formatting for merged content
                } else {
                    rowArray[colIndex] = {
                        text: cell.text,
                        fontName: cell.fontName || 'Arial',
                        fontSize: cell.fontSize || 10,
                        isBold: cell.isBold || false
                    };
                }
            });
            
            return rowArray;
        });
        
        // Filter out completely empty rows
        const filteredTable = table.filter(row => row.some(cell => cell.text && cell.text.trim()));
        
        if (filteredTable.length === 0) {
            return [];
        }
        
        return [{ data: filteredTable, hasFormatting: true }];
        
    } catch (error) {
        console.error('Error extracting tables from page:', error);
        return [];
    }
}

/**
 * Calculate font size from transformation matrix
 */
function calculateFontSize(transform) {
    if (!transform || transform.length < 6) return 10;
    // Font size is typically sqrt(a^2 + b^2) or sqrt(c^2 + d^2)
    const a = transform[0] || 1;
    const b = transform[1] || 0;
    const size = Math.sqrt(a * a + b * b);
    return Math.round(size * 10) / 10; // Round to 1 decimal
}

/**
 * Detect if font is bold based on font name
 */
function detectBoldFont(fontName) {
    if (!fontName) return false;
    const boldKeywords = ['Bold', 'bold', 'Bd', 'bd', 'Black', 'black', 'Heavy', 'heavy'];
    return boldKeywords.some(keyword => fontName.includes(keyword));
}

/**
 * Apply formatting to Excel worksheet cells
 * IMPROVED: Better font support for multi-language Unicode
 */
function applyFormattingToWorksheet(ws, table) {
    try {
        // XLSX uses cell addresses like 'A1', 'B1', etc.
        const range = ws['!ref'] ? XLSX.utils.decode_range(ws['!ref']) : { s: { r: 0, c: 0 }, e: { r: table.length - 1, c: 0 } };
        
        // Initialize styles array if not exists
        if (!ws['!styles']) {
            ws['!styles'] = {};
        }
        
        for (let rowIndex = 0; rowIndex < table.length; rowIndex++) {
            const row = table[rowIndex];
            if (!Array.isArray(row)) continue;
            
            for (let colIndex = 0; colIndex < row.length; colIndex++) {
                const cellObj = row[colIndex];
                if (!cellObj || typeof cellObj !== 'object') continue;
                
                const cellAddress = XLSX.utils.encode_cell({ r: rowIndex, c: colIndex });
                
                // Get or ensure cell exists
                if (!ws[cellAddress]) {
                    // Cell should already exist from aoa_to_sheet, but ensure it does
                    continue;
                }
                
                // Extract font info from cell object
                let fontName = cellObj.fontName || 'Arial';
                const fontSize = cellObj.fontSize || 10;
                let isBold = cellObj.isBold || false;
                const language = cellObj.language || 'unknown';
                
                // IMPROVED: Use Unicode-supporting font for multi-language text
                // Check if cell text contains non-Latin characters
                const cellText = ws[cellAddress].v || '';
                if (typeof cellText === 'string' && /[^\x00-\x7F]/.test(cellText)) {
                    // Contains non-ASCII characters - use Unicode font
                    const unicodeFonts = ['Arial Unicode MS', 'Calibri', 'Tahoma', 'Microsoft Sans Serif'];
                    if (!unicodeFonts.includes(fontName)) {
                        fontName = 'Arial Unicode MS'; // Best Unicode support
                    }
                } else if (language && language !== 'latin' && language !== 'unknown') {
                    // Language detected - use appropriate font
                    fontName = getFontForLanguage(language, fontName);
                }
                
                // First row is typically header - make it bold
                if (rowIndex === 0) {
                    isBold = true;
                }
                
                // Apply cell style using XLSX style format
                if (!ws[cellAddress].s) {
                    ws[cellAddress].s = {};
                }
                
                // Font styling (XLSX style format)
                ws[cellAddress].s.font = ws[cellAddress].s.font || {};
                ws[cellAddress].s.font.name = fontName;
                ws[cellAddress].s.font.sz = fontSize;
                if (isBold) {
                    ws[cellAddress].s.font.bold = true;
                }
                
                // IMPROVED: Set cell alignment for better readability
                ws[cellAddress].s.alignment = ws[cellAddress].s.alignment || {};
                // Numbers right-align, text left-align
                if (/^\d+([.,]\d+)?$/.test(cellText)) {
                    ws[cellAddress].s.alignment.horizontal = 'right';
                } else {
                    ws[cellAddress].s.alignment.horizontal = 'left';
                }
                ws[cellAddress].s.alignment.vertical = 'top';
                ws[cellAddress].s.alignment.wrapText = true; // Wrap long text
            }
        }
    } catch (error) {
        console.warn('Error applying formatting to worksheet:', error);
        // Continue without formatting if there's an error
    }
}

/**
 * Get appropriate font for language (helper function)
 */
function getFontForLanguage(language, originalFont) {
    const fontMap = {
        'devanagari': 'Arial Unicode MS', // Hindi, Marathi, etc.
        'arabic': 'Arial Unicode MS',
        'cjk': 'Arial Unicode MS', // Chinese, Japanese, Korean
        'thai': 'Arial Unicode MS',
        'latin': originalFont || 'Calibri',
        'mixed': 'Arial Unicode MS',
        'unknown': 'Arial Unicode MS'
    };
    
    // If original font already supports Unicode, keep it
    const unicodeFonts = ['Arial Unicode MS', 'Calibri', 'Times New Roman', 'Tahoma', 'Microsoft Sans Serif'];
    if (unicodeFonts.includes(originalFont)) {
        return originalFont;
    }
    
    return fontMap[language] || 'Arial Unicode MS';
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.PDFExcelFreeConverter = {
        convertPdfToExcelFree,
        extractTablesFromPage,
        applyFormattingToWorksheet,
        calculateFontSize,
        detectBoldFont,
        getFontForLanguage: typeof getFontForLanguage !== 'undefined' ? getFontForLanguage : function(lang, orig) { return 'Arial Unicode MS'; }
    };
}

