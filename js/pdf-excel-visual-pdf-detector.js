/**
 * Visual PDF Detector (FREE Version)
 * Detects visual-heavy/design-based PDFs that should use Premium conversion
 * NO AI, NO OCR - Pure browser-based detection using text and layout analysis
 */

/**
 * Detect if PDF is visual-heavy/design-based
 * Returns: { isVisualPDF: boolean, confidence: number, reasons: string[] }
 */
async function detectVisualPDF(page) {
    try {
        const viewport = page.getViewport({ scale: 1.0 });
        const textContent = await page.getTextContent();
        
        if (!textContent || !textContent.items) {
            return { isVisualPDF: false, confidence: 0, reasons: [] };
        }
        
        const reasons = [];
        let score = 0;
        
        // 1. Check image density (using canvas rendering - lightweight)
        const imageDensity = await checkImageDensity(page, viewport);
        if (imageDensity > 0.4) { // >40% of page is images
            score += 30;
            reasons.push(`High image density (${Math.round(imageDensity * 100)}%)`);
        }
        
        // 2. Check text density (low text = likely visual)
        const textDensity = calculateTextDensity(textContent, viewport);
        if (textDensity < 0.15) { // <15% text coverage
            score += 25;
            reasons.push(`Low text density (${Math.round(textDensity * 100)}%)`);
        }
        
        // 3. Check for rectangular layout (boxes/design elements)
        const rectangularLayout = await detectRectangularLayout(page, viewport);
        if (rectangularLayout) {
            score += 20;
            reasons.push('Rectangular layout detected (design elements)');
        }
        
        // 4. Check for text inside boxes (design pattern)
        const textInBoxes = detectTextInBoxes(textContent, viewport);
        if (textInBoxes) {
            score += 15;
            reasons.push('Text inside boxes/containers detected');
        }
        
        // 5. Check for logo-like elements (large text near top, centered)
        const logoDetected = detectLogoPattern(textContent, viewport);
        if (logoDetected) {
            score += 10;
            reasons.push('Logo/header pattern detected');
        }
        
        // Decision: If score >= 50, likely visual PDF
        const isVisualPDF = score >= 50;
        const confidence = Math.min(score / 100, 1.0);
        
        return {
            isVisualPDF: isVisualPDF,
            confidence: confidence,
            reasons: reasons,
            score: score
        };
        
    } catch (error) {
        console.error('Error detecting visual PDF:', error);
        // On error, allow free conversion (fail-safe)
        return { isVisualPDF: false, confidence: 0, reasons: [] };
    }
}

/**
 * Check image density using lightweight canvas analysis
 * Returns: ratio of image area to total page area (0-1)
 */
async function checkImageDensity(page, viewport) {
    try {
        // Render to canvas at low resolution for performance
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const scale = 0.5; // Lower scale for faster processing
        const scaledViewport = page.getViewport({ scale: scale });
        canvas.width = scaledViewport.width;
        canvas.height = scaledViewport.height;
        
        await page.render({
            canvasContext: ctx,
            viewport: scaledViewport
        }).promise;
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        // Count non-white pixels (images/content areas)
        let nonWhitePixels = 0;
        let totalPixels = canvas.width * canvas.height;
        
        // Sample every 4th pixel for performance
        for (let i = 0; i < data.length; i += 16) { // RGBA = 4 bytes, sample every 4th pixel
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Check if pixel is not white/background
            // White = RGB(255,255,255) or very light colors
            const isNotWhite = r < 240 || g < 240 || b < 240;
            if (isNotWhite) {
                nonWhitePixels++;
            }
        }
        
        // Calculate ratio (accounting for sampling)
        const sampledRatio = nonWhitePixels / (totalPixels / 4);
        
        // Adjust for text area (subtract estimated text area)
        // Assume text takes ~20% of non-white area in text-based PDFs
        const adjustedRatio = Math.max(0, sampledRatio - 0.2);
        
        return Math.min(adjustedRatio, 1.0);
        
    } catch (error) {
        console.warn('Image density check failed:', error);
        return 0; // Fail-safe: assume not visual
    }
}

/**
 * Calculate text density (coverage of page by text)
 * Returns: ratio of text area to page area (0-1)
 */
function calculateTextDensity(textContent, viewport) {
    if (!textContent.items || textContent.items.length === 0) {
        return 0;
    }
    
    const pageArea = viewport.width * viewport.height;
    let textArea = 0;
    
    textContent.items.forEach(item => {
        if (!item.transform || item.transform.length < 6) return;
        
        // Estimate text bounding box
        const fontSize = Math.sqrt(
            Math.pow(item.transform[0] || 1, 2) + 
            Math.pow(item.transform[1] || 0, 2)
        );
        const textWidth = item.width || (item.str ? item.str.length * fontSize * 0.6 : 0);
        const textHeight = fontSize * 1.2;
        
        textArea += textWidth * textHeight;
    });
    
    return Math.min(textArea / pageArea, 1.0);
}

/**
 * Detect rectangular layout (design-based layouts often have boxes/containers)
 * Returns: boolean
 */
async function detectRectangularLayout(page, viewport) {
    try {
        // Use lightweight canvas rendering
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const scale = 0.3; // Very low resolution for fast processing
        const scaledViewport = page.getViewport({ scale: scale });
        canvas.width = scaledViewport.width;
        canvas.height = scaledViewport.height;
        
        await page.render({
            canvasContext: ctx,
            viewport: scaledViewport
        }).promise;
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;
        
        // Look for rectangular patterns (vertical and horizontal lines)
        // Simplified: Check for strong horizontal/vertical edges
        let horizontalEdges = 0;
        let verticalEdges = 0;
        
        for (let y = 1; y < canvas.height - 1; y++) {
            for (let x = 1; x < canvas.width - 1; x++) {
                const idx = (y * canvas.width + x) * 4;
                const prevIdx = (y * canvas.width + (x - 1)) * 4;
                const nextIdx = (y * canvas.width + (x + 1)) * 4;
                const topIdx = ((y - 1) * canvas.width + x) * 4;
                const bottomIdx = ((y + 1) * canvas.width + x) * 4;
                
                // Check horizontal edge (vertical line)
                const hDiff = Math.abs(data[idx] - data[prevIdx]) + 
                             Math.abs(data[idx + 1] - data[prevIdx + 1]) + 
                             Math.abs(data[idx + 2] - data[prevIdx + 2]);
                if (hDiff > 100) { // Strong edge
                    verticalEdges++;
                }
                
                // Check vertical edge (horizontal line)
                const vDiff = Math.abs(data[idx] - data[topIdx]) + 
                             Math.abs(data[idx + 1] - data[topIdx + 1]) + 
                             Math.abs(data[idx + 2] - data[topIdx + 2]);
                if (vDiff > 100) { // Strong edge
                    horizontalEdges++;
                }
            }
        }
        
        // If many edges detected, likely rectangular layout
        const totalPixels = canvas.width * canvas.height;
        const edgeRatio = (horizontalEdges + verticalEdges) / totalPixels;
        
        return edgeRatio > 0.05; // >5% edge pixels
        
    } catch (error) {
        console.warn('Rectangular layout detection failed:', error);
        return false;
    }
}

/**
 * Detect if text is inside boxes (common in design PDFs)
 * Returns: boolean
 */
function detectTextInBoxes(textContent, viewport) {
    if (!textContent.items || textContent.items.length < 3) {
        return false;
    }
    
    // Check if text items form box-like patterns
    // Look for text items that form rectangular boundaries
    
    const items = textContent.items.filter(item => 
        item.transform && item.transform.length >= 6 && item.str && item.str.trim()
    );
    
    if (items.length < 4) {
        return false;
    }
    
    // Group items by approximate Y position (rows)
    const yGroups = new Map();
    items.forEach(item => {
        const y = Math.round(item.transform[5] / 10) * 10; // Round to 10px groups
        if (!yGroups.has(y)) {
            yGroups.set(y, []);
        }
        yGroups.get(y).push(item);
    });
    
    // Check if items align in box-like pattern (4 corners or aligned boundaries)
    if (yGroups.size < 2) {
        return false;
    }
    
    const sortedYs = Array.from(yGroups.keys()).sort((a, b) => b - a);
    const topRow = yGroups.get(sortedYs[0]);
    const bottomRow = yGroups.get(sortedYs[sortedYs.length - 1]);
    
    // Check if top and bottom rows have items at similar X positions (box alignment)
    if (topRow && bottomRow && topRow.length >= 2 && bottomRow.length >= 2) {
        const topXs = topRow.map(item => Math.round(item.transform[4] / 20) * 20);
        const bottomXs = bottomRow.map(item => Math.round(item.transform[4] / 20) * 20);
        
        // Check for alignment (items at similar X positions in both rows)
        const alignedCount = topXs.filter(topX => 
            bottomXs.some(bottomX => Math.abs(topX - bottomX) < 30)
        ).length;
        
        // If >= 50% alignment, likely box layout
        return alignedCount >= Math.min(topXs.length, bottomXs.length) * 0.5;
    }
    
    return false;
}

/**
 * Detect logo pattern (large text near top, often centered)
 * Returns: boolean
 */
function detectLogoPattern(textContent, viewport) {
    if (!textContent.items || textContent.items.length === 0) {
        return false;
    }
    
    const topThreshold = viewport.height * 0.2; // Top 20% of page
    
    // Find items in top region
    const topItems = textContent.items.filter(item => {
        if (!item.transform || item.transform.length < 6) return false;
        const y = viewport.height - item.transform[5]; // Convert to top-left origin
        return y < topThreshold;
    });
    
    if (topItems.length === 0) {
        return false;
    }
    
    // Check for large text (likely logo/header)
    const largeTextItems = topItems.filter(item => {
        const fontSize = Math.sqrt(
            Math.pow(item.transform[0] || 1, 2) + 
            Math.pow(item.transform[1] || 0, 2)
        );
        return fontSize > 20; // Large font size
    });
    
    // Check if centered (common for logos)
    if (largeTextItems.length > 0) {
        const centerX = viewport.width / 2;
        const centeredItems = largeTextItems.filter(item => {
            const x = item.transform[4];
            return Math.abs(x - centerX) < viewport.width * 0.3; // Within 30% of center
        });
        
        return centeredItems.length > 0;
    }
    
    return false;
}

/**
 * Detect visual PDF for entire document
 * Checks first page (most design PDFs show pattern on first page)
 */
async function detectVisualPDFDocument(pdfDoc) {
    try {
        if (!pdfDoc || pdfDoc.numPages === 0) {
            return { isVisualPDF: false, confidence: 0, reasons: [] };
        }
        
        // Check first page (most important for detection)
        const firstPage = await pdfDoc.getPage(1);
        const firstPageResult = await detectVisualPDF(firstPage);
        
        // If first page is clearly visual, return immediately
        if (firstPageResult.isVisualPDF && firstPageResult.confidence > 0.7) {
            return firstPageResult;
        }
        
        // If document has multiple pages, check a few more
        if (pdfDoc.numPages > 1) {
            const pagesToCheck = Math.min(3, pdfDoc.numPages);
            let totalScore = firstPageResult.score || 0;
            let allReasons = [...firstPageResult.reasons];
            
            for (let i = 2; i <= pagesToCheck; i++) {
                const page = await pdfDoc.getPage(i);
                const result = await detectVisualPDF(page);
                totalScore += result.score || 0;
                allReasons = allReasons.concat(result.reasons);
            }
            
            const avgScore = totalScore / pagesToCheck;
            const isVisualPDF = avgScore >= 50;
            
            return {
                isVisualPDF: isVisualPDF,
                confidence: Math.min(avgScore / 100, 1.0),
                reasons: [...new Set(allReasons)], // Remove duplicates
                score: avgScore
            };
        }
        
        return firstPageResult;
        
    } catch (error) {
        console.error('Error detecting visual PDF document:', error);
        return { isVisualPDF: false, confidence: 0, reasons: [] };
    }
}

// Export
if (typeof window !== 'undefined') {
    window.PDFExcelVisualPDFDetector = {
        detectVisualPDF,
        detectVisualPDFDocument,
        checkImageDensity,
        calculateTextDensity,
        detectRectangularLayout,
        detectTextInBoxes,
        detectLogoPattern
    };
}

