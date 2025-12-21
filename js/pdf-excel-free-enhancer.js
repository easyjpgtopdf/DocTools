/**
 * FREE Pipeline Enhancer - Maximum Usability Without AI
 * Real-world improvements for FREE users using only client-side tools
 */

/**
 * Enhanced table detection with alignment-based row/column grouping
 */
function detectAlignedTable(textItems) {
    if (!textItems || textItems.length === 0) return null;
    
    // Group items by Y position (rows) with tolerance
    const yTolerance = 3;
    const rows = {};
    
    textItems.forEach(item => {
        if (!item.transform || item.transform.length < 6) return;
        
        const y = Math.round(item.transform[5] / yTolerance) * yTolerance;
        const x = Math.round(item.transform[4]);
        const text = (item.str || '').trim();
        
        if (!text) return;
        
        if (!rows[y]) {
            rows[y] = [];
        }
        rows[y].push({ x, text, transform: item.transform });
    });
    
    // Sort rows by Y position (top to bottom)
    const sortedRows = Object.keys(rows)
        .map(y => parseFloat(y))
        .sort((a, b) => b - a) // Top to bottom (higher Y = top)
        .map(y => {
            // Sort items in row by X position (left to right)
            return rows[y].sort((a, b) => a.x - b.x);
        });
    
    if (sortedRows.length < 2) return null; // Need at least header + 1 row
    
    // Detect column boundaries by analyzing X positions
    const columnBoundaries = detectColumnBoundaries(sortedRows);
    
    // Reconstruct table with aligned columns
    const table = reconstructTable(sortedRows, columnBoundaries);
    
    return table;
}

/**
 * Detect column boundaries by analyzing X positions across rows
 */
function detectColumnBoundaries(rows) {
    const allXPositions = new Set();
    rows.forEach(row => {
        row.forEach(item => allXPositions.add(item.x));
    });
    
    // Cluster nearby X positions
    const sortedX = Array.from(allXPositions).sort((a, b) => a - b);
    const clusters = [];
    let currentCluster = [sortedX[0]];
    
    for (let i = 1; i < sortedX.length; i++) {
        if (sortedX[i] - currentCluster[currentCluster.length - 1] < 50) {
            // Same cluster (within 50px)
            currentCluster.push(sortedX[i]);
        } else {
            // New cluster
            clusters.push(currentCluster);
            currentCluster = [sortedX[i]];
        }
    }
    if (currentCluster.length > 0) clusters.push(currentCluster);
    
    // Get center of each cluster (column position)
    return clusters.map(cluster => {
        const sum = cluster.reduce((a, b) => a + b, 0);
        return Math.round(sum / cluster.length);
    }).sort((a, b) => a - b);
}

/**
 * Reconstruct table with aligned columns
 */
function reconstructTable(rows, columnBoundaries) {
    const table = [];
    const tolerance = 30; // Pixel tolerance for column alignment
    
    rows.forEach(row => {
        const tableRow = new Array(columnBoundaries.length).fill('');
        
        row.forEach(item => {
            // Find closest column boundary
            let minDist = Infinity;
            let closestCol = 0;
            
            columnBoundaries.forEach((boundary, idx) => {
                const dist = Math.abs(item.x - boundary);
                if (dist < minDist && dist < tolerance) {
                    minDist = dist;
                    closestCol = idx;
                }
            });
            
            // If cell already has content, append (for multi-word cells)
            if (tableRow[closestCol]) {
                tableRow[closestCol] += ' ' + item.text;
            } else {
                tableRow[closestCol] = item.text;
            }
        });
        
        table.push(tableRow);
    });
    
    return table;
}

/**
 * Detect merged cells heuristically
 */
function detectMergedCells(table) {
    if (!table || table.length === 0) return [];
    
    const mergedCells = [];
    
    // Check for horizontal merges (same text spanning multiple columns)
    for (let row = 0; row < table.length; row++) {
        let currentText = '';
        let startCol = -1;
        
        for (let col = 0; col < table[row].length; col++) {
            const cellText = (table[row][col] || '').trim();
            
            if (cellText && cellText === currentText && currentText.length > 5) {
                // Potential horizontal merge
                if (startCol === -1) {
                    startCol = col - 1;
                }
            } else {
                if (startCol !== -1 && col - startCol > 1) {
                    // Found a merge
                    mergedCells.push({
                        row,
                        startCol,
                        endCol: col - 1,
                        type: 'horizontal'
                    });
                }
                currentText = cellText;
                startCol = -1;
            }
        }
    }
    
    // Check for vertical merges (same text in consecutive rows, same column)
    for (let col = 0; col < (table[0] || []).length; col++) {
        let currentText = '';
        let startRow = -1;
        
        for (let row = 0; row < table.length; row++) {
            const cellText = (table[row] && table[row][col] ? table[row][col].trim() : '');
            
            if (cellText && cellText === currentText && currentText.length > 3) {
                if (startRow === -1) {
                    startRow = row - 1;
                }
            } else {
                if (startRow !== -1 && row - startRow > 1) {
                    mergedCells.push({
                        startRow,
                        endRow: row - 1,
                        col,
                        type: 'vertical'
                    });
                }
                currentText = cellText;
                startRow = -1;
            }
        }
    }
    
    return mergedCells;
}

/**
 * Split merged cells into separate cells (for better Excel compatibility)
 */
function splitMergedCells(table, mergedCells) {
    // For FREE version, we'll split merged cells by distributing text
    // Premium version can handle actual merged cells
    const newTable = table.map(row => [...row]); // Deep copy
    
    mergedCells.forEach(merge => {
        if (merge.type === 'horizontal') {
            const text = newTable[merge.row][merge.startCol] || '';
            const numCells = merge.endCol - merge.startCol + 1;
            const textPerCell = Math.ceil(text.length / numCells);
            
            // Distribute text across cells
            for (let col = merge.startCol; col <= merge.endCol; col++) {
                const startIdx = (col - merge.startCol) * textPerCell;
                const endIdx = Math.min(startIdx + textPerCell, text.length);
                newTable[merge.row][col] = text.substring(startIdx, endIdx);
            }
        }
        // Vertical merges are kept as-is for simplicity
    });
    
    return newTable;
}

/**
 * Detect if document looks like an ID card
 */
function detectIdCardLayout(table, textItems) {
    if (!table || table.length < 2) return false;
    
    const allText = textItems.map(item => item.str || '').join(' ').toLowerCase();
    const idKeywords = ['name', 'id', 'dob', 'date of birth', 'address', 'photo', 'signature'];
    const foundKeywords = idKeywords.filter(keyword => allText.includes(keyword));
    
    // If 3+ ID keywords found, likely an ID card
    if (foundKeywords.length >= 3) {
        return true;
    }
    
    // Check layout: typically 2 columns (label : value)
    const hasTwoColumnLayout = table.some(row => {
        const nonEmptyCells = row.filter(cell => cell && cell.trim());
        return nonEmptyCells.length === 2;
    });
    
    return hasTwoColumnLayout && foundKeywords.length >= 2;
}

/**
 * Generate ID card template (structured Excel/CSV)
 */
function generateIdCardTemplate(table, textItems) {
    const template = {
        headers: ['Field', 'Value'],
        rows: []
    };
    
    // Try to extract key-value pairs
    table.forEach(row => {
        if (row.length >= 2) {
            const field = (row[0] || '').trim();
            const value = row.slice(1).filter(cell => cell && cell.trim()).join(' ').trim();
            
            if (field && value) {
                template.rows.push([field, value]);
            }
        }
    });
    
    // If no structure found, create empty template
    if (template.rows.length === 0) {
        template.rows = [
            ['Name', ''],
            ['ID Number', ''],
            ['Date of Birth', ''],
            ['Address', ''],
            ['Photo', '(Please add photo manually)']
        ];
    }
    
    return template;
}

/**
 * Enhance Excel workbook with FREE improvements
 * Note: SheetJS (XLSX) must be loaded before this function is called
 */
function enhanceExcelWorkbook(workbook, table, isFirstSheet = true) {
    if (!workbook || !table) return workbook;
    
    // Check if XLSX is available
    if (typeof XLSX === 'undefined') {
        console.warn('XLSX not available, skipping enhancement');
        return workbook;
    }
    
    // Get first sheet
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    
    if (!worksheet) return workbook;
    
    // Auto-bold headers (first row) - using SheetJS style format
    if (table.length > 0) {
        for (let col = 0; col < table[0].length; col++) {
            const cellAddress = XLSX.utils.encode_cell({ r: 0, c: col });
            if (!worksheet[cellAddress]) worksheet[cellAddress] = {};
            if (!worksheet[cellAddress].s) worksheet[cellAddress].s = {};
            if (!worksheet[cellAddress].s.font) worksheet[cellAddress].s.font = {};
            worksheet[cellAddress].s.font.bold = true;
        }
    }
    
    // Add notes sheet for FREE users
    if (isFirstSheet && workbook.SheetNames.indexOf('Notes') === -1) {
        const notesSheet = XLSX.utils.aoa_to_sheet([
            ['Notes'],
            [''],
            ['This Excel file was generated using basic (FREE) conversion.'],
            [''],
            ['Limitations:'],
            ['- Scanned PDFs may not convert accurately'],
            ['- Complex tables may need manual adjustment'],
            ['- Merged cells have been split'],
            [''],
            ['For high-accuracy conversion with OCR:'],
            ['- Upgrade to Premium'],
            ['- Supports scanned PDFs'],
            ['- Handles complex tables'],
            ['- Preserves exact layout'],
            [''],
            ['Visit: https://easyjpgtopdf.com/pricing.html']
        ]);
        
        XLSX.utils.book_append_sheet(workbook, notesSheet, 'Notes');
    }
    
    return workbook;
}

/**
 * Export partial table (first N rows or first table only)
 */
function exportPartialTable(table, maxRows = 100) {
    if (!table || table.length === 0) return null;
    
    if (table.length <= maxRows) {
        return table; // Full table fits
    }
    
    // Return first maxRows rows
    return table.slice(0, maxRows);
}

// Export functions
if (typeof window !== 'undefined') {
    window.PDFExcelFreeEnhancer = {
        detectAlignedTable,
        detectColumnBoundaries,
        reconstructTable,
        detectMergedCells,
        splitMergedCells,
        detectIdCardLayout,
        generateIdCardTemplate,
        enhanceExcelWorkbook,
        exportPartialTable
    };
}

