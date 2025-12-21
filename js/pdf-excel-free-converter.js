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
                    tables.forEach((table, tableIndex) => {
                        const ws = XLSX.utils.aoa_to_sheet(table);
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
        
        // Generate Excel file
        const excelBuffer = XLSX.write(wb, { type: 'array', bookType: 'xlsx' });
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
 * Returns: Array of 2D arrays (tables)
 */
async function extractTablesFromPage(page) {
    try {
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
            
            if (!rowsMap.has(y)) {
                rowsMap.set(y, []);
            }
            
            rowsMap.get(y).push({ x, text });
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
        
        // Build table: Map each row to columns
        const table = sortedRows.map(row => {
            // Sort cells in row by X position
            const sortedCells = row.sort((a, b) => a.x - b.x);
            
            // Create array matching column positions
            const rowArray = new Array(columns.length).fill('');
            
            sortedCells.forEach(cell => {
                // Find closest column index
                const colIndex = columns.reduce((closest, col, idx) => {
                    return Math.abs(col - cell.x) < Math.abs(columns[closest] - cell.x) ? idx : closest;
                }, 0);
                
                // Merge text if cell already has content
                if (rowArray[colIndex]) {
                    rowArray[colIndex] += ' ' + cell.text;
                } else {
                    rowArray[colIndex] = cell.text;
                }
            });
            
            return rowArray;
        });
        
        // Filter out completely empty rows
        const filteredTable = table.filter(row => row.some(cell => cell.trim()));
        
        if (filteredTable.length === 0) {
            return [];
        }
        
        return [filteredTable];
        
    } catch (error) {
        console.error('Error extracting tables from page:', error);
        return [];
    }
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.PDFExcelFreeConverter = {
        convertPdfToExcelFree,
        extractTablesFromPage
    };
}

