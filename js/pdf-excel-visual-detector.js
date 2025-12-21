/**
 * PDF Visual Element Detector
 * Detects boxes, rectangles, borders, and images from PDF pages
 * Uses PDF.js rendering to analyze visual structure
 */

/**
 * Detect visual elements (boxes, rectangles, borders) from PDF page
 * Returns: { boxes: [], borders: [], images: [] }
 */
async function detectVisualElements(page) {
    try {
        const viewport = page.getViewport({ scale: 2.0 }); // Higher scale for better detection
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        // Render PDF page to canvas
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        
        // Get image data for analysis
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        
        // Detect visual elements
        const boxes = detectBoxes(imageData, canvas.width, canvas.height);
        const borders = detectBorders(imageData, canvas.width, canvas.height);
        const images = await detectImages(page);
        
        // Clean up canvas from DOM if it was added
        if (canvas.parentNode) {
            canvas.parentNode.removeChild(canvas);
        }
        
        return {
            boxes: boxes,
            borders: borders,
            images: images
        };
    } catch (error) {
        console.error('Error detecting visual elements:', error);
        return { boxes: [], borders: [], images: [] };
    }
}

/**
 * Detect rectangular boxes/regions in the image
 * Uses edge detection and rectangle finding
 */
function detectBoxes(imageData, width, height) {
    const boxes = [];
    const data = imageData.data;
    
    // Convert to grayscale and detect edges
    const edges = new Uint8Array(width * height);
    const threshold = 200; // Edge detection threshold
    
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            const idx = (y * width + x) * 4;
            const r = data[idx];
            const g = data[idx + 1];
            const b = data[idx + 2];
            const gray = (r + g + b) / 3;
            
            // Simple edge detection (Sobel-like)
            const rightIdx = (y * width + (x + 1)) * 4;
            const rightGray = (data[rightIdx] + data[rightIdx + 1] + data[rightIdx + 2]) / 3;
            const bottomIdx = ((y + 1) * width + x) * 4;
            const bottomGray = (data[bottomIdx] + data[bottomIdx + 1] + data[bottomIdx + 2]) / 3;
            
            const edgeX = Math.abs(gray - rightGray);
            const edgeY = Math.abs(gray - bottomGray);
            const edge = Math.sqrt(edgeX * edgeX + edgeY * edgeY);
            
            edges[y * width + x] = edge > threshold ? 255 : 0;
        }
    }
    
    // Find rectangular regions (simplified - find connected edge regions)
    const visited = new Set();
    const minBoxSize = 20; // Minimum box size in pixels
    
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const idx = y * width + x;
            if (edges[idx] > 0 && !visited.has(idx)) {
                const box = findRectangle(edges, width, height, x, y, visited);
                if (box && (box.width > minBoxSize || box.height > minBoxSize)) {
                    // Convert from canvas coordinates to PDF coordinates
                    boxes.push({
                        x: box.x / 2, // Scale back down
                        y: box.y / 2,
                        width: box.width / 2,
                        height: box.height / 2,
                        type: 'box'
                    });
                }
            }
        }
    }
    
    return boxes;
}

/**
 * Find rectangle starting from a point
 */
function findRectangle(edges, width, height, startX, startY, visited) {
    // Simple flood fill to find connected edge region
    const region = [];
    const stack = [[startX, startY]];
    let minX = startX, maxX = startX, minY = startY, maxY = startY;
    
    while (stack.length > 0) {
        const [x, y] = stack.pop();
        const idx = y * width + x;
        
        if (x < 0 || x >= width || y < 0 || y >= height) continue;
        if (visited.has(idx)) continue;
        if (edges[idx] === 0) continue;
        
        visited.add(idx);
        region.push([x, y]);
        
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
        
        // Check neighbors
        stack.push([x + 1, y]);
        stack.push([x - 1, y]);
        stack.push([x, y + 1]);
        stack.push([x, y - 1]);
    }
    
    if (region.length < 10) return null; // Too small
    
    return {
        x: minX,
        y: minY,
        width: maxX - minX,
        height: maxY - minY
    };
}

/**
 * Detect table borders (horizontal and vertical lines)
 */
function detectBorders(imageData, width, height) {
    const borders = [];
    const data = imageData.data;
    const threshold = 200; // Border detection threshold
    
    // Detect horizontal lines
    for (let y = 0; y < height; y++) {
        let lineStart = -1;
        let lineLength = 0;
        
        for (let x = 0; x < width; x++) {
            const idx = (y * width + x) * 4;
            const r = data[idx];
            const g = data[idx + 1];
            const b = data[idx + 2];
            const gray = (r + g + b) / 3;
            
            // Check if this is a dark line (border)
            if (gray < threshold) {
                if (lineStart === -1) {
                    lineStart = x;
                }
                lineLength++;
            } else {
                if (lineLength > 50) { // Minimum line length
                    borders.push({
                        type: 'horizontal',
                        x: lineStart / 2,
                        y: y / 2,
                        width: lineLength / 2,
                        height: 1
                    });
                }
                lineStart = -1;
                lineLength = 0;
            }
        }
        
        if (lineLength > 50) {
            borders.push({
                type: 'horizontal',
                x: lineStart / 2,
                y: y / 2,
                width: lineLength / 2,
                height: 1
            });
        }
    }
    
    // Detect vertical lines
    for (let x = 0; x < width; x++) {
        let lineStart = -1;
        let lineLength = 0;
        
        for (let y = 0; y < height; y++) {
            const idx = (y * width + x) * 4;
            const r = data[idx];
            const g = data[idx + 1];
            const b = data[idx + 2];
            const gray = (r + g + b) / 3;
            
            if (gray < threshold) {
                if (lineStart === -1) {
                    lineStart = y;
                }
                lineLength++;
            } else {
                if (lineLength > 50) {
                    borders.push({
                        type: 'vertical',
                        x: x / 2,
                        y: lineStart / 2,
                        width: 1,
                        height: lineLength / 2
                    });
                }
                lineStart = -1;
                lineLength = 0;
            }
        }
        
        if (lineLength > 50) {
            borders.push({
                type: 'vertical',
                x: x / 2,
                y: lineStart / 2,
                width: 1,
                height: lineLength / 2
            });
        }
    }
    
    return borders;
}

/**
 * Detect and extract images from PDF page
 */
async function detectImages(page) {
    const images = [];
    try {
        // Get page operators (drawing commands)
        const opList = await page.getOperatorList();
        
        // Check if pdfjsLib is available
        const pdfjsLib = window.pdfjsLib || window.pdfjs;
        if (!pdfjsLib || !pdfjsLib.OPS) {
            console.warn('PDF.js library not available for image detection');
            return images;
        }
        
        // Extract image objects from operators
        for (let i = 0; i < opList.fnArray.length; i++) {
            const op = opList.fnArray[i];
            const args = opList.argsArray[i];
            
            // Check for image drawing operators
            const OPS = pdfjsLib.OPS;
            if (op === OPS.paintImageXObject || 
                op === OPS.paintInlineImageXObject ||
                op === OPS.paintImageXObjectRepeat) {
                
                try {
                    // Get image data from page objects
                    if (page.objs && args && args[0]) {
                        const img = await page.objs.get(args[0]);
                        if (img && (img.data || img.src)) {
                            let imageUrl = null;
                            
                            // Handle different image formats
                            if (img.data) {
                                const blob = new Blob([img.data], { type: 'image/png' });
                                imageUrl = URL.createObjectURL(blob);
                            } else if (img.src) {
                                imageUrl = img.src;
                            } else if (typeof img === 'string') {
                                imageUrl = img; // Base64 or URL
                            }
                            
                            if (imageUrl) {
                                images.push({
                                    id: args[0],
                                    url: imageUrl,
                                    width: img.width || 100,
                                    height: img.height || 100,
                                    x: (args[1] !== undefined) ? args[1] : 0,
                                    y: (args[2] !== undefined) ? args[2] : 0
                                });
                            }
                        }
                    }
                } catch (e) {
                    console.warn('Error extracting image:', e);
                }
            }
        }
    } catch (error) {
        console.warn('Error detecting images:', error);
    }
    
    return images;
}

/**
 * Map visual elements to Excel cells
 * Creates a mapping of visual boxes/borders to cell positions
 */
function mapVisualToExcel(visualElements, textObjects, columnBoundaries, rowPositions) {
    const cellMappings = new Map();
    
    // Map borders to cell edges
    visualElements.borders.forEach(border => {
        if (border.type === 'horizontal') {
            // Find closest row
            const closestRow = rowPositions.reduce((closest, rowY, idx) => {
                return Math.abs(rowY - border.y) < Math.abs(rowPositions[closest] - border.y) ? idx : closest;
            }, 0);
            
            // Mark this row as having a border below
            const key = `row_${closestRow}_bottom`;
            cellMappings.set(key, { type: 'border', style: 'thin' });
        } else if (border.type === 'vertical') {
            // Find closest column
            const closestCol = columnBoundaries.reduce((closest, colX, idx) => {
                return Math.abs(colX - border.x) < Math.abs(columnBoundaries[closest] - border.x) ? idx : closest;
            }, 0);
            
            // Mark this column as having a border on the right
            const key = `col_${closestCol}_right`;
            cellMappings.set(key, { type: 'border', style: 'thin' });
        }
    });
    
    // Map boxes to cell regions
    visualElements.boxes.forEach(box => {
        // Find which cells this box overlaps
        const startCol = columnBoundaries.findIndex(colX => colX >= box.x);
        const endCol = columnBoundaries.findIndex(colX => colX >= box.x + box.width);
        const startRow = rowPositions.findIndex(rowY => rowY >= box.y);
        const endRow = rowPositions.findIndex(rowY => rowY >= box.y + box.height);
        
        if (startCol >= 0 && startRow >= 0) {
            for (let r = startRow; r <= (endRow >= 0 ? endRow : rowPositions.length - 1); r++) {
                for (let c = startCol; c <= (endCol >= 0 ? endCol : columnBoundaries.length - 1); c++) {
                    const key = `cell_${r}_${c}`;
                    if (!cellMappings.has(key)) {
                        cellMappings.set(key, { type: 'box', region: true });
                    }
                }
            }
        }
    });
    
    // Map images to cells
    visualElements.images.forEach((img, imgIdx) => {
        const closestCol = columnBoundaries.reduce((closest, colX, idx) => {
            return Math.abs(colX - img.x) < Math.abs(columnBoundaries[closest] - img.x) ? idx : closest;
        }, 0);
        const closestRow = rowPositions.reduce((closest, rowY, idx) => {
            return Math.abs(rowY - img.y) < Math.abs(rowPositions[closest] - img.y) ? idx : closest;
        }, 0);
        
        const key = `cell_${closestRow}_${closestCol}_image`;
        cellMappings.set(key, {
            type: 'image',
            url: img.url,
            width: img.width,
            height: img.height
        });
    });
    
    return cellMappings;
}

// Export
if (typeof window !== 'undefined') {
    window.PDFExcelVisualDetector = {
        detectVisualElements,
        detectBoxes,
        detectBorders,
        detectImages,
        mapVisualToExcel
    };
}

