/**
 * iLovePDF-like FREE Layout Reconstruction
 * Advanced table detection using text + coordinates ONLY
 * NO AI, NO OCR, NO cloud costs
 */

/**
 * Main iLovePDF-like table extraction
 * IMPROVED: Now includes visual element detection for better borders and column detection
 */
async function extractTableILovePDFStyle(page, visualElements = null) {
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
        
        // STEP 4: Column detection with clustering (X-axis) + visual alignment
        const columnBoundaries = detectColumnsWithClustering(rows, visualElements);
        
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
 * IMPROVED: Better row detection with adaptive tolerance
 */
function clusterRowsDynamic(textObjects) {
    if (textObjects.length === 0) return [];
    
    // Sort by Y position (top to bottom)
    const sorted = [...textObjects].sort((a, b) => b.y - a.y);
    
    // Calculate average font size for adaptive tolerance
    const avgFontSize = sorted.reduce((sum, obj) => sum + obj.fontSize, 0) / sorted.length;
    const baseLineHeight = avgFontSize * 1.2;
    
    const rows = [];
    let currentRow = null;
    
    sorted.forEach(obj => {
        if (!currentRow) {
            // Start first row
            currentRow = {
                y: obj.y,
                fontSize: obj.fontSize,
                items: [obj],
                minX: obj.x,
                maxX: obj.x + obj.width
            };
        } else {
            // Calculate Y distance
            const yDistance = currentRow.y - obj.y;
            
            // IMPROVED: Adaptive tolerance based on font size
            // Larger fonts need more tolerance, smaller fonts need less
            const objLineHeight = obj.fontSize * 1.2;
            const rowLineHeight = currentRow.fontSize * 1.2;
            const avgLineHeight = (objLineHeight + rowLineHeight) / 2;
            
            // Tolerance: 25% of average line height, minimum 2px, maximum 10px
            const tolerance = Math.min(Math.max(avgLineHeight * 0.25, 2), 10);
            
            // Check if same row based on:
            // 1. Y distance within adaptive tolerance
            // 2. Font size similarity (within 25% - more lenient)
            // 3. X position overlap (items in similar horizontal region)
            const fontSizeSimilar = Math.abs(currentRow.fontSize - obj.fontSize) / Math.max(currentRow.fontSize, obj.fontSize) < 0.25;
            const xOverlap = (obj.x >= currentRow.minX - 50 && obj.x <= currentRow.maxX + 50);
            
            if (yDistance <= tolerance && fontSizeSimilar && xOverlap) {
                // Same row
                currentRow.items.push(obj);
                // Update row Y to weighted average (by font size)
                const totalFontSize = currentRow.items.reduce((sum, item) => sum + item.fontSize, 0);
                currentRow.y = currentRow.items.reduce((sum, item) => sum + (item.y * item.fontSize), 0) / totalFontSize;
                // Update row bounds
                currentRow.minX = Math.min(currentRow.minX, obj.x);
                currentRow.maxX = Math.max(currentRow.maxX, obj.x + obj.width);
            } else {
                // New row
                rows.push(currentRow);
                currentRow = {
                    y: obj.y,
                    fontSize: obj.fontSize,
                    items: [obj],
                    minX: obj.x,
                    maxX: obj.x + obj.width
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
 * IMPROVED: Better column boundary detection with density analysis + visual alignment
 */
function detectColumnsWithClustering(rows, visualElements = null) {
    if (rows.length === 0) return [];
    
    // Collect all X positions with their frequencies (how many items at each X)
    const xPositionMap = new Map();
    rows.forEach(row => {
        row.items.forEach(item => {
            const x = Math.round(item.x); // Round to nearest pixel for clustering
            xPositionMap.set(x, (xPositionMap.get(x) || 0) + 1);
        });
    });
    
    if (xPositionMap.size === 0) return [];
    
    // Sort X positions
    const sortedX = Array.from(xPositionMap.keys()).sort((a, b) => a - b);
    
    // Calculate average font size for adaptive threshold
    const avgFontSize = rows.reduce((sum, row) => sum + row.fontSize, 0) / rows.length;
    
    // IMPROVED: If visual elements available, use vertical lines as column hints
    let visualColumnHints = [];
    if (visualElements && visualElements.borders && visualElements.borders.vertical) {
        visualColumnHints = visualElements.borders.vertical
            .map(line => line.x)
            .sort((a, b) => a - b);
    }
    
    // IMPROVED: Adaptive clustering with density weighting
    // Columns are detected by finding X positions that appear frequently across rows
    const clusters = [];
    let currentCluster = [{ x: sortedX[0], count: xPositionMap.get(sortedX[0]) }];
    
    // Dynamic threshold: based on font size and character width
    // Typical character width is ~0.6 * font size
    const charWidth = avgFontSize * 0.6;
    // Use smaller threshold if visual hints are available (they're more accurate)
    const clusterThreshold = visualColumnHints.length > 0 
        ? Math.max(charWidth * 2, 10) // Smaller threshold when visual hints exist
        : Math.max(charWidth * 3, 15); // 3 characters or 15px min
    
    for (let i = 1; i < sortedX.length; i++) {
        const currentX = sortedX[i];
        const lastX = currentCluster[currentCluster.length - 1].x;
        const distance = currentX - lastX;
        
        // If visual hints exist, check if we should create a new cluster at visual line
        if (visualColumnHints.length > 0) {
            const nearbyVisualLine = visualColumnHints.find(vx => 
                Math.abs(currentX - vx) < 5 && Math.abs(currentX - lastX) > clusterThreshold / 2
            );
            if (nearbyVisualLine) {
                // Force new cluster at visual line
                clusters.push(currentCluster);
                currentCluster = [{ x: currentX, count: xPositionMap.get(currentX) }];
                continue;
            }
        }
        
        if (distance < clusterThreshold) {
            // Same cluster - add to current cluster
            currentCluster.push({
                x: currentX,
                count: xPositionMap.get(currentX)
            });
        } else {
            // New cluster - save current and start new
            clusters.push(currentCluster);
            currentCluster = [{
                x: currentX,
                count: xPositionMap.get(currentX)
            }];
        }
    }
    
    if (currentCluster.length > 0) {
        clusters.push(currentCluster);
    }
    
    // IMPROVED: Get weighted center of each cluster (by frequency)
    // Columns that appear more frequently get higher weight
    let columnBoundaries = clusters.map(cluster => {
        let weightedSum = 0;
        let totalWeight = 0;
        
        cluster.forEach(({ x, count }) => {
            weightedSum += x * count; // Weight by frequency
            totalWeight += count;
        });
        
        return totalWeight > 0 ? weightedSum / totalWeight : cluster[0].x;
    }).sort((a, b) => a - b);
    
    // IMPROVED: Align column boundaries to visual lines if available
    if (visualColumnHints.length > 0) {
        columnBoundaries = columnBoundaries.map(boundary => {
            const nearbyVisualLine = visualColumnHints.find(vx => Math.abs(boundary - vx) < 10);
            return nearbyVisualLine || boundary; // Use visual line if close, else use text-based boundary
        });
        
        // Add visual lines that don't have nearby text columns
        visualColumnHints.forEach(vx => {
            const hasNearby = columnBoundaries.some(b => Math.abs(b - vx) < 10);
            if (!hasNearby) {
                columnBoundaries.push(vx);
            }
        });
        
        columnBoundaries.sort((a, b) => a - b);
    }
    
    // Filter out columns that appear too infrequently (noise)
    const minFrequency = rows.length * 0.1; // Must appear in at least 10% of rows
    const filteredBoundaries = columnBoundaries.filter((boundary, idx) => {
        // Visual hints are always included
        if (visualColumnHints.includes(boundary)) return true;
        
        // Check frequency for text-based boundaries
        const cluster = clusters[idx];
        if (!cluster) return true; // Keep if no cluster (might be visual-only)
        const totalCount = cluster.reduce((sum, item) => sum + item.count, 0);
        return totalCount >= minFrequency;
    });
    
    return filteredBoundaries.length > 0 ? filteredBoundaries : columnBoundaries;
}

/**
 * STEP 5: Build table with multi-line cell merging
 * IMPROVED: Better cell alignment and text merging
 */
function buildTableWithMerging(rows, columnBoundaries) {
    if (columnBoundaries.length === 0) return [];
    
    const table = [];
    
    // IMPROVED: Adaptive tolerance based on column spacing
    const columnSpacings = [];
    for (let i = 1; i < columnBoundaries.length; i++) {
        columnSpacings.push(columnBoundaries[i] - columnBoundaries[i - 1]);
    }
    const avgSpacing = columnSpacings.length > 0 
        ? columnSpacings.reduce((a, b) => a + b, 0) / columnSpacings.length 
        : 50;
    const tolerance = Math.min(avgSpacing * 0.3, 40); // 30% of spacing or 40px max
    
    rows.forEach((row, rowIndex) => {
        const tableRow = new Array(columnBoundaries.length).fill(null).map(() => ({
            text: '',
            fontSize: row.fontSize || 10,
            isBold: false,
            fontName: 'Arial',
            language: 'unknown'
        }));
        
        row.items.forEach(item => {
            // Find closest column with improved matching
            let minDist = Infinity;
            let closestCol = 0;
            let foundMatch = false;
            
            columnBoundaries.forEach((boundary, idx) => {
                const dist = Math.abs(item.x - boundary);
                if (dist < minDist) {
                    minDist = dist;
                    closestCol = idx;
                    if (dist < tolerance) {
                        foundMatch = true;
                    }
                }
            });
            
            // Only assign to column if within tolerance
            if (foundMatch || minDist < tolerance * 1.5) {
                // Merge text if cell already has content
                if (tableRow[closestCol].text) {
                    // Add space only if needed (not for languages that don't use spaces)
                    const needsSpace = !isLanguageWithoutSpaces(tableRow[closestCol].text, item.text);
                    tableRow[closestCol].text += (needsSpace ? ' ' : '') + item.text;
                } else {
                    tableRow[closestCol].text = item.text;
                    tableRow[closestCol].fontSize = item.fontSize || row.fontSize || 10;
                    tableRow[closestCol].isBold = item.isBold || false;
                    tableRow[closestCol].fontName = item.fontName || 'Arial';
                }
            } else {
                // Item doesn't fit in any column - might be merged cell or overflow
                // Try to add to nearest column anyway if it's close
                if (minDist < tolerance * 2) {
                    if (tableRow[closestCol].text) {
                        tableRow[closestCol].text += ' ' + item.text;
                    } else {
                        tableRow[closestCol].text = item.text;
                        tableRow[closestCol].fontSize = item.fontSize || row.fontSize || 10;
                        tableRow[closestCol].isBold = item.isBold || false;
                        tableRow[closestCol].fontName = item.fontName || 'Arial';
                    }
                }
            }
        });
        
        table.push(tableRow);
    });
    
    // IMPROVED: Multi-line cell merging with better detection
    for (let rowIndex = 0; rowIndex < table.length - 1; rowIndex++) {
        const currentRow = table[rowIndex];
        const nextRow = table[rowIndex + 1];
        
        for (let colIndex = 0; colIndex < currentRow.length; colIndex++) {
            const currentCell = currentRow[colIndex];
            const nextCell = nextRow[colIndex];
            
            // Check if cells should be merged:
            // 1. Current cell has text
            // 2. Next cell in same column has text
            // 3. Current cell doesn't look complete
            if (currentCell.text && nextCell.text) {
                const currentIsHeader = currentCell.isBold || rowIndex === 0;
                const currentEndsWithPunctuation = /[.!?।]$/.test(currentCell.text.trim());
                const currentIsNumber = /^\d+$/.test(currentCell.text.trim());
                const nextIsNumber = /^\d+$/.test(nextCell.text.trim());
                
                // Don't merge if:
                // - Current is header
                // - Current ends with punctuation (complete sentence)
                // - Both are numbers (likely separate data points)
                // - Current is too long (likely complete)
                if (!currentIsHeader && 
                    !currentEndsWithPunctuation && 
                    !(currentIsNumber && nextIsNumber) &&
                    currentCell.text.length < 80) {
                    // Merge with appropriate spacing
                    const needsSpace = !isLanguageWithoutSpaces(currentCell.text, nextCell.text);
                    currentCell.text += (needsSpace ? ' ' : '') + nextCell.text;
                    nextCell.text = ''; // Clear next cell
                }
            }
        }
    }
    
    // Filter out completely empty rows
    return table.filter(row => row.some(cell => cell.text && cell.text.trim()));
}

/**
 * Check if text is in a language that doesn't use spaces (like Thai, Khmer)
 */
function isLanguageWithoutSpaces(text1, text2) {
    // Thai, Khmer, etc. don't use spaces between words
    const noSpaceLanguages = /[\u0E00-\u0E7F\u1780-\u17FF]/; // Thai, Khmer
    return noSpaceLanguages.test(text1) || noSpaceLanguages.test(text2);
}

/**
 * STEP 6: Unicode normalization (NFC + reordering) + Multi-language support
 */
function normalizeUnicodeTable(table) {
    return table.map(row => {
        return row.map(cell => {
            if (!cell || typeof cell !== 'object') return cell;
            
            let normalizedText = cell.text;
            
            // Multi-language Unicode normalization
            if (typeof String.prototype.normalize === 'function' && normalizedText) {
                try {
                    // NFC normalization (canonical composition)
                    normalizedText = normalizedText.normalize('NFC');
                    
                    // Fix common Unicode issues for Hindi/Devanagari
                    // Reorder dependent vowel signs (matras) if needed
                    normalizedText = fixDevanagariReordering(normalizedText);
                    
                    // Fix zero-width joiners and non-joiners
                    normalizedText = normalizedText.replace(/\u200D/g, ''); // Zero-width joiner
                    normalizedText = normalizedText.replace(/\u200C/g, ''); // Zero-width non-joiner
                    
                } catch (e) {
                    console.warn('Unicode normalization failed:', e);
                }
            }
            
            // Detect language and set appropriate font
            const detectedLanguage = detectTextLanguage(normalizedText);
            const fontName = getFontForLanguage(detectedLanguage, cell.fontName);
            
            return {
                ...cell,
                text: normalizedText,
                fontName: fontName,
                language: detectedLanguage
            };
        });
    });
}

/**
 * Fix Devanagari (Hindi) character reordering
 * Ensures proper display of Hindi text
 */
function fixDevanagariReordering(text) {
    if (!text) return text;
    
    // Devanagari range: \u0900-\u097F
    if (!/[\u0900-\u097F]/.test(text)) {
        return text; // Not Devanagari, return as-is
    }
    
    // Common fixes for Hindi text
    // Fix common misordered sequences
    const fixes = [
        // Fix common vowel sign issues
        [/\u093E\u0947/g, '\u0947\u093E'], // ai + aa
        [/\u093E\u0948/g, '\u0948\u093E'], // au + aa
        [/\u0947\u093E/g, '\u093E\u0947'], // aa + ai
    ];
    
    let fixed = text;
    fixes.forEach(([pattern, replacement]) => {
        fixed = fixed.replace(pattern, replacement);
    });
    
    return fixed;
}

/**
 * Detect text language based on Unicode ranges
 */
function detectTextLanguage(text) {
    if (!text) return 'unknown';
    
    // Devanagari (Hindi, Marathi, etc.)
    if (/[\u0900-\u097F]/.test(text)) {
        return 'devanagari';
    }
    
    // Arabic
    if (/[\u0600-\u06FF]/.test(text)) {
        return 'arabic';
    }
    
    // Chinese, Japanese, Korean
    if (/[\u4E00-\u9FFF]/.test(text)) {
        return 'cjk';
    }
    
    // Thai
    if (/[\u0E00-\u0E7F]/.test(text)) {
        return 'thai';
    }
    
    // Latin (English, etc.)
    if (/^[a-zA-Z0-9\s\.,;:!?\-\(\)\[\]{}'"]+$/.test(text)) {
        return 'latin';
    }
    
    // Mixed or unknown
    return 'mixed';
}

/**
 * Get appropriate font for language
 * Excel-compatible fonts that support the language
 */
function getFontForLanguage(language, originalFont) {
    const fontMap = {
        'devanagari': 'Arial Unicode MS', // Best for Hindi
        'arabic': 'Arial Unicode MS',
        'cjk': 'Arial Unicode MS',
        'thai': 'Arial Unicode MS',
        'latin': originalFont || 'Calibri',
        'mixed': 'Arial Unicode MS', // Safe for mixed content
        'unknown': 'Arial Unicode MS'
    };
    
    // If original font already supports Unicode, keep it
    const unicodeFonts = ['Arial Unicode MS', 'Calibri', 'Times New Roman', 'Tahoma'];
    if (unicodeFonts.includes(originalFont)) {
        return originalFont;
    }
    
    return fontMap[language] || 'Arial Unicode MS';
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
        normalizeUnicodeTable,
        fixDevanagariReordering,
        detectTextLanguage,
        getFontForLanguage,
        isLanguageWithoutSpaces
    };
}

