/**
 * iLovePDF-like FREE Layout Reconstruction
 * Advanced table detection using text + coordinates ONLY
 * NO AI, NO OCR, NO cloud costs
 */

/**
 * Main iLovePDF-like table extraction
 */
async function extractTableILovePDFStyle(page) {
    try {
        const viewport = page.getViewport({ scale: 1.0 });
        const textContent = await page.getTextContent();
        
        if (!textContent || !textContent.items || textContent.items.length === 0) {
            return null;
        }
        
        // STEP 1: Collect all text objects with full metadata
        const textObjects = collectTextObjects(textContent.items, viewport);
        
        if (textObjects.length === 0) {
            return null;
        }
        
        // STEP 2: Suppress headers/footers
        const filteredObjects = suppressHeadersFooters(textObjects, viewport);
        
        // STEP 3: Dynamic row clustering (Y-axis with font similarity)
        const rows = clusterRowsDynamic(filteredObjects);
        
        if (rows.length < 2) {
            return null; // Need at least header + 1 row
        }
        
        // STEP 4: Column detection with clustering (X-axis)
        const columnBoundaries = detectColumnsWithClustering(rows);
        
        if (columnBoundaries.length === 0) {
            return null;
        }
        
        // STEP 5: Build table with multi-line cell merging
        const table = buildTableWithMerging(rows, columnBoundaries);
        
        // STEP 6: Apply Unicode normalization
        const normalizedTable = normalizeUnicodeTable(table);
        
        return normalizedTable;
        
    } catch (error) {
        console.error('iLovePDF-style extraction error:', error);
        return null;
    }
}

/**
 * STEP 1: Collect text objects with full metadata
 */
function collectTextObjects(items, viewport) {
    const textObjects = [];
    
    items.forEach(item => {
        if (!item.transform || item.transform.length < 6) return;
        
        const text = (item.str || '').trim();
        if (!text) return;
        
        // Extract position
        const x = item.transform[4] || 0;
        const y = viewport.height - (item.transform[5] || 0); // Convert to top-left origin
        
        // Extract font info
        const fontName = item.fontName || 'Arial';
        const fontSize = calculateFontSizeFromTransform(item.transform);
        const isBold = detectBoldFromFontName(fontName);
        
        // Calculate width/height
        const width = item.width || (text.length * fontSize * 0.6);
        const height = fontSize * 1.2;
        
        textObjects.push({
            text: text,
            x: x,
            y: y,
            width: width,
            height: height,
            fontSize: fontSize,
            fontName: fontName,
            isBold: isBold,
            transform: item.transform
        });
    });
    
    return textObjects;
}

/**
 * STEP 2: Suppress headers/footers (top 10% and bottom 10%)
 */
function suppressHeadersFooters(textObjects, viewport) {
    const pageHeight = viewport.height;
    const topThreshold = pageHeight * 0.1; // Top 10%
    const bottomThreshold = pageHeight * 0.9; // Bottom 10%
    
    // Find repeating text in header/footer regions
    const headerTexts = new Map();
    const footerTexts = new Map();
    
    textObjects.forEach(obj => {
        if (obj.y < topThreshold) {
            const key = obj.text.toLowerCase().trim();
            headerTexts.set(key, (headerTexts.get(key) || 0) + 1);
        } else if (obj.y > bottomThreshold) {
            const key = obj.text.toLowerCase().trim();
            footerTexts.set(key, (footerTexts.get(key) || 0) + 1);
        }
    });
    
    // Filter out frequently repeating header/footer text
    const filtered = textObjects.filter(obj => {
        const key = obj.text.toLowerCase().trim();
        const inHeader = obj.y < topThreshold;
        const inFooter = obj.y > bottomThreshold;
        
        if (inHeader && headerTexts.get(key) > 2) {
            return false; // Suppress repeating header
        }
        if (inFooter && footerTexts.get(key) > 2) {
            return false; // Suppress repeating footer
        }
        
        return true;
    });
    
    return filtered;
}

/**
 * STEP 3: Dynamic row clustering (Y-axis with font similarity)
 */
function clusterRowsDynamic(textObjects) {
    if (textObjects.length === 0) return [];
    
    // Sort by Y position (top to bottom)
    const sorted = [...textObjects].sort((a, b) => b.y - a.y);
    
    const rows = [];
    let currentRow = null;
    
    sorted.forEach(obj => {
        if (!currentRow) {
            // Start first row
            currentRow = {
                y: obj.y,
                fontSize: obj.fontSize,
                items: [obj]
            };
        } else {
            // Calculate Y distance
            const yDistance = currentRow.y - obj.y;
            
            // Calculate relative line height (based on font size)
            const lineHeight = currentRow.fontSize * 1.2;
            const tolerance = Math.max(lineHeight * 0.3, 3); // 30% of line height or 3px min
            
            // Check if same row based on:
            // 1. Y distance within tolerance
            // 2. Font size similarity (within 20%)
            const fontSizeSimilar = Math.abs(currentRow.fontSize - obj.fontSize) / currentRow.fontSize < 0.2;
            
            if (yDistance <= tolerance && fontSizeSimilar) {
                // Same row
                currentRow.items.push(obj);
                // Update row Y to average
                currentRow.y = (currentRow.y + obj.y) / 2;
            } else {
                // New row
                rows.push(currentRow);
                currentRow = {
                    y: obj.y,
                    fontSize: obj.fontSize,
                    items: [obj]
                };
            }
        }
    });
    
    if (currentRow) {
        rows.push(currentRow);
    }
    
    // Sort items in each row by X position
    rows.forEach(row => {
        row.items.sort((a, b) => a.x - b.x);
    });
    
    return rows;
}

/**
 * STEP 4: Column detection with clustering (X-axis)
 */
function detectColumnsWithClustering(rows) {
    // Collect all X positions
    const allXPositions = new Set();
    rows.forEach(row => {
        row.items.forEach(item => {
            allXPositions.add(item.x);
        });
    });
    
    if (allXPositions.size === 0) return [];
    
    // Sort X positions
    const sortedX = Array.from(allXPositions).sort((a, b) => a - b);
    
    // Cluster nearby X positions
    const clusters = [];
    let currentCluster = [sortedX[0]];
    
    // Dynamic threshold based on average font size
    const avgFontSize = rows.reduce((sum, row) => sum + row.fontSize, 0) / rows.length;
    const clusterThreshold = Math.max(avgFontSize * 2, 20); // 2x font size or 20px min
    
    for (let i = 1; i < sortedX.length; i++) {
        const distance = sortedX[i] - currentCluster[currentCluster.length - 1];
        
        if (distance < clusterThreshold) {
            // Same cluster
            currentCluster.push(sortedX[i]);
        } else {
            // New cluster
            clusters.push(currentCluster);
            currentCluster = [sortedX[i]];
        }
    }
    
    if (currentCluster.length > 0) {
        clusters.push(currentCluster);
    }
    
    // Get center of each cluster (column boundary)
    const columnBoundaries = clusters.map(cluster => {
        const sum = cluster.reduce((a, b) => a + b, 0);
        return sum / cluster.length;
    }).sort((a, b) => a - b);
    
    return columnBoundaries;
}

/**
 * STEP 5: Build table with multi-line cell merging
 */
function buildTableWithMerging(rows, columnBoundaries) {
    const table = [];
    const tolerance = 30; // Pixel tolerance for column alignment
    
    rows.forEach((row, rowIndex) => {
        const tableRow = new Array(columnBoundaries.length).fill(null).map(() => ({
            text: '',
            fontSize: row.fontSize,
            isBold: false
        }));
        
        row.items.forEach(item => {
            // Find closest column
            let minDist = Infinity;
            let closestCol = 0;
            
            columnBoundaries.forEach((boundary, idx) => {
                const dist = Math.abs(item.x - boundary);
                if (dist < minDist && dist < tolerance) {
                    minDist = dist;
                    closestCol = idx;
                }
            });
            
            // Merge text if cell already has content
            if (tableRow[closestCol].text) {
                tableRow[closestCol].text += ' ' + item.text;
            } else {
                tableRow[closestCol].text = item.text;
                tableRow[closestCol].fontSize = item.fontSize;
                tableRow[closestCol].isBold = item.isBold;
            }
        });
        
        table.push(tableRow);
    });
    
    // Multi-line cell merging: Check adjacent rows for same column + small Y-gap
    for (let rowIndex = 0; rowIndex < table.length - 1; rowIndex++) {
        const currentRow = table[rowIndex];
        const nextRow = table[rowIndex + 1];
        
        for (let colIndex = 0; colIndex < currentRow.length; colIndex++) {
            const currentCell = currentRow[colIndex];
            const nextCell = nextRow[colIndex];
            
            // Check if cells should be merged:
            // 1. Current cell has text
            // 2. Next cell in same column has text
            // 3. Current cell text doesn't look like a complete sentence/header
            if (currentCell.text && nextCell.text) {
                const currentIsHeader = currentCell.isBold || rowIndex === 0;
                const currentIsComplete = currentCell.text.match(/[.!?]$/);
                
                // If current cell is not a header and not complete, merge with next
                if (!currentIsHeader && !currentIsComplete && currentCell.text.length < 50) {
                    currentCell.text += ' ' + nextCell.text;
                    nextCell.text = ''; // Clear next cell
                }
            }
        }
    }
    
    // Filter out completely empty rows
    return table.filter(row => row.some(cell => cell.text && cell.text.trim()));
}

/**
 * STEP 6: Unicode normalization (NFC + reordering)
 */
function normalizeUnicodeTable(table) {
    return table.map(row => {
        return row.map(cell => {
            if (!cell || typeof cell !== 'object') return cell;
            
            let normalizedText = cell.text;
            
            // NFC normalization
            if (typeof String.prototype.normalize === 'function') {
                try {
                    normalizedText = normalizedText.normalize('NFC');
                } catch (e) {
                    // Fallback if normalize fails
                }
            }
            
            return {
                ...cell,
                text: normalizedText
            };
        });
    });
}

/**
 * Helper: Calculate font size from transformation matrix
 */
function calculateFontSizeFromTransform(transform) {
    if (!transform || transform.length < 6) return 10;
    const a = transform[0] || 1;
    const b = transform[1] || 0;
    const size = Math.sqrt(a * a + b * b);
    return Math.round(size * 10) / 10;
}

/**
 * Helper: Detect bold from font name
 */
function detectBoldFromFontName(fontName) {
    if (!fontName) return false;
    const boldKeywords = ['Bold', 'bold', 'Bd', 'bd', 'Black', 'black', 'Heavy', 'heavy'];
    return boldKeywords.some(keyword => fontName.includes(keyword));
}

// Export
if (typeof window !== 'undefined') {
    window.PDFExcelILovePDFLayout = {
        extractTableILovePDFStyle,
        collectTextObjects,
        suppressHeadersFooters,
        clusterRowsDynamic,
        detectColumnsWithClustering,
        buildTableWithMerging,
        normalizeUnicodeTable
    };
}

