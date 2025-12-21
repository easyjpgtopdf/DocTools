/**
 * PDF Visual Element Detector (FREE Version)
 * Detects borders, boxes, rectangles, and images from PDF using canvas rendering
 * NO AI, NO OCR - Pure browser-based visual detection
 */

/**
 * Detect visual elements (borders, boxes, images) from PDF page
 * Uses canvas rendering and image processing techniques
 */
async function detectVisualElements(page) {
    try {
        const viewport = page.getViewport({ scale: 2.0 }); // Higher scale for better detection
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        // Render PDF page to canvas
        await page.render({
            canvasContext: ctx,
            viewport: viewport
        }).promise;
        
        // Get image data from canvas
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        // Detect visual elements
        const boxes = detectBoxes(imageData, canvas.width, canvas.height);
        const borders = detectBorders(imageData, canvas.width, canvas.height);
        const images = detectImages(imageData, canvas.width, canvas.height);
        
        return {
            boxes: boxes,
            borders: borders,
            images: images,
            viewport: viewport
        };
        
    } catch (error) {
        console.error('Error detecting visual elements:', error);
        return { boxes: [], borders: [], images: [], viewport: null };
    }
}

/**
 * Detect boxes/rectangles in the image
 * Uses edge detection and rectangle detection algorithm
 */
function detectBoxes(imageData, width, height) {
    const boxes = [];
    const data = imageData.data;
    
    // Convert to grayscale and detect edges
    const grayData = new Uint8Array(width * height);
    const edgeData = new Uint8Array(width * height);
    
    // Convert to grayscale
    for (let i = 0; i < data.length; i += 4) {
        const gray = (data[i] + data[i + 1] + data[i + 2]) / 3;
        grayData[i / 4] = gray < 200 ? 0 : 255; // Threshold for white/black
    }
    
    // Simple edge detection (Sobel operator simplified)
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            const idx = y * width + x;
            const left = grayData[idx - 1];
            const right = grayData[idx + 1];
            const top = grayData[(y - 1) * width + x];
            const bottom = grayData[(y + 1) * width + x];
            
            // Edge if there's a significant difference
            if (Math.abs(left - right) > 50 || Math.abs(top - bottom) > 50) {
                edgeData[idx] = 255;
            }
        }
    }
    
    // Detect horizontal and vertical lines (potential box borders)
    const horizontalLines = detectHorizontalLines(edgeData, width, height);
    const verticalLines = detectVerticalLines(edgeData, width, height);
    
    // Find rectangles formed by intersecting lines
    const rectangles = findRectangles(horizontalLines, verticalLines, width, height);
    
    return rectangles.map(rect => ({
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height,
        confidence: rect.confidence
    }));
}

/**
 * Detect borders (lines) in the image
 */
function detectBorders(imageData, width, height) {
    const borders = [];
    const data = imageData.data;
    
    // Detect horizontal lines
    const hLines = detectHorizontalLinesSimple(data, width, height);
    // Detect vertical lines
    const vLines = detectVerticalLinesSimple(data, width, height);
    
    // Combine and return
    return {
        horizontal: hLines,
        vertical: vLines
    };
}

/**
 * Detect images in the PDF
 * Images are typically rectangular regions with complex pixel data
 */
function detectImages(imageData, width, height) {
    const images = [];
    const data = imageData.data;
    
    // Detect image-like regions (areas with high color variation)
    const regions = detectImageRegions(data, width, height);
    
    return regions.map(region => ({
        x: region.x,
        y: region.y,
        width: region.width,
        height: region.height,
        type: 'image'
    }));
}

/**
 * Detect horizontal lines (simplified)
 */
function detectHorizontalLinesSimple(data, width, height) {
    const lines = [];
    const lineThreshold = 5; // Minimum line length
    const pixelThreshold = 50; // Color difference threshold
    
    for (let y = 0; y < height; y++) {
        let lineStart = -1;
        let consecutiveDark = 0;
        
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 4;
            const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
            const isDark = gray < 200;
            
            if (isDark) {
                consecutiveDark++;
                if (lineStart === -1) {
                    lineStart = x;
                }
            } else {
                if (consecutiveDark >= lineThreshold && lineStart !== -1) {
                    lines.push({
                        y: y,
                        x1: lineStart,
                        x2: x - 1,
                        length: consecutiveDark,
                        thickness: 1
                    });
                }
                consecutiveDark = 0;
                lineStart = -1;
            }
        }
        
        // Check for line at end
        if (consecutiveDark >= lineThreshold && lineStart !== -1) {
            lines.push({
                y: y,
                x1: lineStart,
                x2: width - 1,
                length: consecutiveDark,
                thickness: 1
            });
        }
    }
    
    return lines;
}

/**
 * Detect vertical lines (simplified)
 */
function detectVerticalLinesSimple(data, width, height) {
    const lines = [];
    const lineThreshold = 5; // Minimum line length
    
    for (let x = 0; x < width; x++) {
        let lineStart = -1;
        let consecutiveDark = 0;
        
        for (let y = 0; y < height; y++) {
            const idx = (y * width + x) * 4;
            const gray = (data[idx] + data[idx + 1] + data[idx + 2]) / 3;
            const isDark = gray < 200;
            
            if (isDark) {
                consecutiveDark++;
                if (lineStart === -1) {
                    lineStart = y;
                }
            } else {
                if (consecutiveDark >= lineThreshold && lineStart !== -1) {
                    lines.push({
                        x: x,
                        y1: lineStart,
                        y2: y - 1,
                        length: consecutiveDark,
                        thickness: 1
                    });
                }
                consecutiveDark = 0;
                lineStart = -1;
            }
        }
        
        // Check for line at end
        if (consecutiveDark >= lineThreshold && lineStart !== -1) {
            lines.push({
                x: x,
                y1: lineStart,
                y2: height - 1,
                length: consecutiveDark,
                thickness: 1
            });
        }
    }
    
    return lines;
}

/**
 * Detect horizontal lines for box detection
 */
function detectHorizontalLines(edgeData, width, height) {
    const lines = [];
    const minLineLength = width * 0.1; // At least 10% of page width
    
    for (let y = 0; y < height; y++) {
        let lineLength = 0;
        let lineStart = -1;
        
        for (let x = 0; x < width; x++) {
            const idx = y * width + x;
            if (edgeData[idx] > 128) {
                if (lineStart === -1) {
                    lineStart = x;
                }
                lineLength++;
            } else {
                if (lineLength >= minLineLength) {
                    lines.push({ y: y, x1: lineStart, x2: lineStart + lineLength });
                }
                lineLength = 0;
                lineStart = -1;
            }
        }
        
        if (lineLength >= minLineLength) {
            lines.push({ y: y, x1: lineStart, x2: lineStart + lineLength });
        }
    }
    
    return lines;
}

/**
 * Detect vertical lines for box detection
 */
function detectVerticalLines(edgeData, width, height) {
    const lines = [];
    const minLineLength = height * 0.1; // At least 10% of page height
    
    for (let x = 0; x < width; x++) {
        let lineLength = 0;
        let lineStart = -1;
        
        for (let y = 0; y < height; y++) {
            const idx = y * width + x;
            if (edgeData[idx] > 128) {
                if (lineStart === -1) {
                    lineStart = y;
                }
                lineLength++;
            } else {
                if (lineLength >= minLineLength) {
                    lines.push({ x: x, y1: lineStart, y2: lineStart + lineLength });
                }
                lineLength = 0;
                lineStart = -1;
            }
        }
        
        if (lineLength >= minLineLength) {
            lines.push({ x: x, y1: lineStart, y2: lineStart + lineLength });
        }
    }
    
    return lines;
}

/**
 * Find rectangles from intersecting horizontal and vertical lines
 */
function findRectangles(hLines, vLines, width, height) {
    const rectangles = [];
    const tolerance = 5; // Pixel tolerance for intersection
    
    // Find intersections
    for (const hLine of hLines) {
        for (const vLine of vLines) {
            // Check if horizontal line intersects vertical line
            if (vLine.x >= hLine.x1 - tolerance && vLine.x <= hLine.x2 + tolerance &&
                hLine.y >= vLine.y1 - tolerance && hLine.y <= vLine.y2 + tolerance) {
                
                // Find next horizontal and vertical lines to form rectangle
                const nextHLine = hLines.find(h => h.y > hLine.y && 
                    vLine.x >= h.x1 - tolerance && vLine.x <= h.x2 + tolerance);
                const nextVLine = vLines.find(v => v.x > vLine.x &&
                    hLine.y >= v.y1 - tolerance && hLine.y <= v.y2 + tolerance);
                
                if (nextHLine && nextVLine) {
                    // Check if nextVLine also intersects nextHLine
                    if (nextVLine.x >= nextHLine.x1 - tolerance && nextVLine.x <= nextHLine.x2 + tolerance &&
                        nextHLine.y >= nextVLine.y1 - tolerance && nextHLine.y <= nextVLine.y2 + tolerance) {
                        
                        rectangles.push({
                            x: vLine.x,
                            y: hLine.y,
                            width: nextVLine.x - vLine.x,
                            height: nextHLine.y - hLine.y,
                            confidence: 0.8
                        });
                    }
                }
            }
        }
    }
    
    return rectangles;
}

/**
 * Detect image regions (areas with high color variation)
 */
function detectImageRegions(data, width, height) {
    const regions = [];
    const blockSize = 20; // Analyze in 20x20 blocks
    const variationThreshold = 30; // Color variation threshold
    
    for (let blockY = 0; blockY < height - blockSize; blockY += blockSize) {
        for (let blockX = 0; blockX < width - blockSize; blockX += blockSize) {
            let sumR = 0, sumG = 0, sumB = 0;
            let count = 0;
            
            // Calculate average color in block
            for (let y = blockY; y < blockY + blockSize && y < height; y++) {
                for (let x = blockX; x < blockX + blockSize && x < width; x++) {
                    const idx = (y * width + x) * 4;
                    sumR += data[idx];
                    sumG += data[idx + 1];
                    sumB += data[idx + 2];
                    count++;
                }
            }
            
            const avgR = sumR / count;
            const avgG = sumG / count;
            const avgB = sumB / count;
            
            // Calculate variation
            let variation = 0;
            for (let y = blockY; y < blockY + blockSize && y < height; y++) {
                for (let x = blockX; x < blockX + blockSize && x < width; x++) {
                    const idx = (y * width + x) * 4;
                    variation += Math.abs(data[idx] - avgR) +
                                Math.abs(data[idx + 1] - avgG) +
                                Math.abs(data[idx + 2] - avgB);
                }
            }
            variation = variation / count;
            
            // If variation is high, it might be an image
            if (variation > variationThreshold) {
                regions.push({
                    x: blockX,
                    y: blockY,
                    width: blockSize,
                    height: blockSize,
                    variation: variation
                });
            }
        }
    }
    
    // Merge nearby regions
    return mergeImageRegions(regions);
}

/**
 * Merge nearby image regions
 */
function mergeImageRegions(regions) {
    if (regions.length === 0) return [];
    
    const merged = [];
    const mergedFlags = new Set();
    
    for (let i = 0; i < regions.length; i++) {
        if (mergedFlags.has(i)) continue;
        
        const region = regions[i];
        const group = [region];
        mergedFlags.add(i);
        
        // Find nearby regions
        for (let j = i + 1; j < regions.length; j++) {
            if (mergedFlags.has(j)) continue;
            
            const other = regions[j];
            const distance = Math.sqrt(
                Math.pow(region.x - other.x, 2) + Math.pow(region.y - other.y, 2)
            );
            
            if (distance < 50) { // Merge if within 50 pixels
                group.push(other);
                mergedFlags.add(j);
            }
        }
        
        // Create merged region
        const minX = Math.min(...group.map(r => r.x));
        const minY = Math.min(...group.map(r => r.y));
        const maxX = Math.max(...group.map(r => r.x + r.width));
        const maxY = Math.max(...group.map(r => r.y + r.height));
        
        merged.push({
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY,
            variation: group.reduce((sum, r) => sum + r.variation, 0) / group.length
        });
    }
    
    return merged;
}

/**
 * Map visual elements to Excel cells
 * Creates a mapping of borders, boxes, and images to cell positions
 */
function mapVisualToExcel(visualElements, textObjects, columnBoundaries, rowPositions) {
    const cellMappings = new Map();
    
    if (!visualElements || !columnBoundaries || !rowPositions) {
        return cellMappings;
    }
    
    // Map borders to cells
    if (visualElements.borders) {
        // Map horizontal borders (row separators)
        if (visualElements.borders.horizontal) {
            visualElements.borders.horizontal.forEach(line => {
                // Find closest row position
                const closestRow = rowPositions.reduce((closest, rowY, idx) => {
                    const dist = Math.abs(rowY - line.y);
                    const closestDist = Math.abs(rowPositions[closest] - line.y);
                    return dist < closestDist ? idx : closest;
                }, 0);
                
                // Map to row border
                cellMappings.set(`row_${closestRow}_bottom`, {
                    type: 'border',
                    style: 'thin',
                    position: 'bottom',
                    line: line
                });
            });
        }
        
        // Map vertical borders (column separators)
        if (visualElements.borders.vertical) {
            visualElements.borders.vertical.forEach(line => {
                // Find closest column boundary
                const closestCol = columnBoundaries.reduce((closest, colX, idx) => {
                    const dist = Math.abs(colX - line.x);
                    const closestDist = Math.abs(columnBoundaries[closest] - line.x);
                    return dist < closestDist ? idx : closest;
                }, 0);
                
                // Map to column border
                cellMappings.set(`col_${closestCol}_right`, {
                    type: 'border',
                    style: 'thin',
                    position: 'right',
                    line: line
                });
            });
        }
    }
    
    // IMPROVED: Map boxes to cell ranges with better intersection detection
    if (visualElements.boxes && visualElements.boxes.length > 0) {
        visualElements.boxes.forEach((box, boxIdx) => {
            // Find cells that intersect with this box using center point and bounds
            const boxCenterX = box.x + box.width / 2;
            const boxCenterY = box.y + box.height / 2;
            
            // Find start row (row that contains or is closest to box top)
            let startRow = -1;
            let minRowDist = Infinity;
            rowPositions.forEach((rowY, idx) => {
                const dist = Math.abs(rowY - box.y);
                if (dist < minRowDist && rowY <= box.y + box.height) {
                    minRowDist = dist;
                    startRow = idx;
                }
            });
            
            // Find end row (row that contains or is closest to box bottom)
            let endRow = startRow;
            rowPositions.forEach((rowY, idx) => {
                if (rowY >= box.y && rowY <= box.y + box.height && idx >= startRow) {
                    endRow = idx;
                }
            });
            
            // Find start column (column that contains or is closest to box left)
            let startCol = -1;
            let minColDist = Infinity;
            columnBoundaries.forEach((colX, idx) => {
                const dist = Math.abs(colX - box.x);
                if (dist < minColDist && colX <= box.x + box.width) {
                    minColDist = dist;
                    startCol = idx;
                }
            });
            
            // Find end column (column that contains or is closest to box right)
            let endCol = startCol;
            columnBoundaries.forEach((colX, idx) => {
                if (colX >= box.x && colX <= box.x + box.width && idx >= startCol) {
                    endCol = idx;
                }
            });
            
            // Map box to all cells in range
            if (startRow !== -1 && startCol !== -1) {
                for (let r = startRow; r <= endRow && r < rowPositions.length; r++) {
                    for (let c = startCol; c <= endCol && c < columnBoundaries.length; c++) {
                        const key = `box_${r}_${c}`;
                        if (!cellMappings.has(key)) {
                            cellMappings.set(key, {
                                type: 'box',
                                box: box,
                                cellRange: { startRow, endRow, startCol, endCol }
                            });
                        }
                    }
                }
            }
        });
    }
    
    // IMPROVED: Map images to cells with better containment detection
    if (visualElements.images && visualElements.images.length > 0) {
        visualElements.images.forEach((image, imgIdx) => {
            // Find cell that contains the center of this image
            const imageCenterX = image.x + image.width / 2;
            const imageCenterY = image.y + image.height / 2;
            
            // Find row that contains image center
            let row = -1;
            let minRowDist = Infinity;
            rowPositions.forEach((rowY, idx) => {
                const nextRowY = idx < rowPositions.length - 1 ? rowPositions[idx + 1] : rowY + 50;
                if (imageCenterY >= rowY && imageCenterY <= nextRowY) {
                    const dist = Math.abs(imageCenterY - rowY);
                    if (dist < minRowDist) {
                        minRowDist = dist;
                        row = idx;
                    }
                }
            });
            
            // Find column that contains image center
            let col = -1;
            let minColDist = Infinity;
            columnBoundaries.forEach((colX, idx) => {
                const nextColX = idx < columnBoundaries.length - 1 ? columnBoundaries[idx + 1] : colX + 100;
                if (imageCenterX >= colX && imageCenterX <= nextColX) {
                    const dist = Math.abs(imageCenterX - colX);
                    if (dist < minColDist) {
                        minColDist = dist;
                        col = idx;
                    }
                }
            });
            
            // Map image to cell if found
            if (row !== -1 && col !== -1) {
                cellMappings.set(`cell_${row}_${col}_image`, {
                    type: 'image',
                    image: image,
                    row: row,
                    col: col,
                    width: image.width,
                    height: image.height
                });
            }
        });
    }
    
    return cellMappings;
}

/**
 * Recreate table borders based on detected visual elements
 */
function recreateTableBorders(visualElements, columnBoundaries, rowPositions) {
    const borders = {
        horizontal: [],
        vertical: []
    };
    
    if (!visualElements || !columnBoundaries || !rowPositions) {
        return borders;
    }
    
    // Recreate horizontal borders between rows
    for (let i = 0; i < rowPositions.length - 1; i++) {
        const y = rowPositions[i];
        const nextY = rowPositions[i + 1];
        const midY = (y + nextY) / 2;
        
        // Check if there's a detected border near this position
        const detectedBorder = visualElements.borders?.horizontal?.find(line => 
            Math.abs(line.y - midY) < 10
        );
        
        if (detectedBorder) {
            borders.horizontal.push({
                row: i,
                y: detectedBorder.y,
                x1: columnBoundaries[0] || 0,
                x2: columnBoundaries[columnBoundaries.length - 1] || 1000
            });
        } else {
            // Add inferred border
            borders.horizontal.push({
                row: i,
                y: midY,
                x1: columnBoundaries[0] || 0,
                x2: columnBoundaries[columnBoundaries.length - 1] || 1000,
                inferred: true
            });
        }
    }
    
    // Recreate vertical borders between columns
    for (let i = 0; i < columnBoundaries.length - 1; i++) {
        const x = columnBoundaries[i];
        const nextX = columnBoundaries[i + 1];
        const midX = (x + nextX) / 2;
        
        // Check if there's a detected border near this position
        const detectedBorder = visualElements.borders?.vertical?.find(line => 
            Math.abs(line.x - midX) < 10
        );
        
        if (detectedBorder) {
            borders.vertical.push({
                col: i,
                x: detectedBorder.x,
                y1: rowPositions[rowPositions.length - 1] || 0,
                y2: rowPositions[0] || 1000
            });
        } else {
            // Add inferred border
            borders.vertical.push({
                col: i,
                x: midX,
                y1: rowPositions[rowPositions.length - 1] || 0,
                y2: rowPositions[0] || 1000,
                inferred: true
            });
        }
    }
    
    return borders;
}

// Export
if (typeof window !== 'undefined') {
    window.PDFExcelVisualDetector = {
        detectVisualElements,
        mapVisualToExcel,
        recreateTableBorders,
        detectBoxes,
        detectBorders,
        detectImages
    };
}
