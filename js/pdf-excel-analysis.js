/**
 * PDF Analysis Module (Browser-based, NO AI)
 * Analyzes PDF to determine if free conversion is possible
 * 
 * Rules:
 * - Text-based PDFs → HIGH confidence (free possible)
 * - Scanned/image-heavy PDFs → LOW confidence (OCR required)
 * - Complex tables → May require premium
 */

/**
 * Analyze PDF to determine conversion confidence
 * Returns: { confidence: 'high' | 'low', score: 0-100, reasons: [] }
 */
async function analyzePdf(pdfDoc) {
    if (!pdfDoc || !pdfDoc.numPages) {
        return {
            confidence: 'low',
            score: 0,
            reasons: ['Invalid PDF document']
        };
    }
    
    const analysis = {
        totalPages: pdfDoc.numPages,
        textBasedPages: 0,
        scannedPages: 0,
        pagesWithTables: 0,
        totalTextLength: 0,
        totalImageArea: 0,
        totalPageArea: 0,
        complexTables: 0,
        reasons: []
    };
    
    // Analyze each page (sample first 3 pages for performance)
    const pagesToAnalyze = Math.min(3, pdfDoc.numPages);
    
    for (let pageNum = 1; pageNum <= pagesToAnalyze; pageNum++) {
        try {
            const page = await pdfDoc.getPage(pageNum);
            const pageAnalysis = await analyzePage(page, pageNum);
            
            analysis.textBasedPages += pageAnalysis.isTextBased ? 1 : 0;
            analysis.scannedPages += pageAnalysis.isScanned ? 1 : 0;
            analysis.pagesWithTables += pageAnalysis.hasTable ? 1 : 0;
            analysis.totalTextLength += pageAnalysis.textLength;
            analysis.totalImageArea += pageAnalysis.imageArea;
            analysis.totalPageArea += pageAnalysis.pageArea;
            analysis.complexTables += pageAnalysis.hasComplexTable ? 1 : 0;
            
            if (pageAnalysis.reasons) {
                analysis.reasons.push(...pageAnalysis.reasons.map(r => `Page ${pageNum}: ${r}`));
            }
        } catch (e) {
            console.warn(`Error analyzing page ${pageNum}:`, e);
            analysis.reasons.push(`Page ${pageNum}: Analysis failed`);
        }
    }
    
    // Calculate confidence score
    const confidence = calculateConfidence(analysis);
    
    return {
        confidence: confidence.level,
        score: confidence.score,
        reasons: analysis.reasons,
        details: {
            textBasedRatio: analysis.textBasedPages / pagesToAnalyze,
            imageDominance: analysis.totalPageArea > 0 ? (analysis.totalImageArea / analysis.totalPageArea) : 0,
            tableComplexity: analysis.complexTables / pagesToAnalyze
        }
    };
}

/**
 * Analyze a single PDF page
 */
async function analyzePage(page, pageNum) {
    const result = {
        isTextBased: false,
        isScanned: false,
        hasTable: false,
        hasComplexTable: false,
        textLength: 0,
        imageArea: 0,
        pageArea: 0,
        reasons: []
    };
    
    try {
        // Get viewport to calculate page area
        const viewport = page.getViewport({ scale: 1.0 });
        result.pageArea = viewport.width * viewport.height;
        
        // Extract text content
        const textContent = await page.getTextContent();
        result.textLength = textContent.items.reduce((sum, item) => sum + (item.str || '').length, 0);
        
        // Check if text-based (has selectable text)
        if (result.textLength > 100) {
            result.isTextBased = true;
            result.reasons.push('Contains selectable text');
        } else {
            result.isScanned = true;
            result.reasons.push('Low text content, likely scanned');
        }
        
        // Check for tables (basic detection via text positioning)
        const tableIndicators = detectTableStructure(textContent);
        if (tableIndicators.hasTable) {
            result.hasTable = true;
            result.reasons.push('Table structure detected');
            
            if (tableIndicators.isComplex) {
                result.hasComplexTable = true;
                result.reasons.push('Complex table detected (merged cells, multi-line headers)');
            }
        }
        
        // Estimate image area (rough estimate based on page render)
        // This is a simplified check - in reality, would need to analyze page rendering
        if (result.textLength < 50 && result.pageArea > 0) {
            // Low text + large page = likely image-heavy
            result.imageArea = result.pageArea * 0.7; // Estimate 70% image
            result.isScanned = true;
        }
        
    } catch (e) {
        console.warn(`Error analyzing page ${pageNum}:`, e);
        result.reasons.push('Analysis error');
    }
    
    return result;
}

/**
 * Detect table structure from text content
 */
function detectTableStructure(textContent) {
    if (!textContent || !textContent.items || textContent.items.length === 0) {
        return { hasTable: false, isComplex: false };
    }
    
    // Group items by Y position (rows)
    const rows = {};
    const xPositions = new Set();
    
    textContent.items.forEach(item => {
        if (!item.transform || item.transform.length < 6) return;
        
        const y = Math.round(item.transform[5]);
        const x = Math.round(item.transform[4]);
        
        if (!rows[y]) {
            rows[y] = [];
        }
        rows[y].push({ x, text: item.str || '' });
        xPositions.add(x);
    });
    
    // Check if structure looks like a table
    const rowCount = Object.keys(rows).length;
    const columnCount = xPositions.size;
    
    // Basic table detection: multiple rows with aligned columns
    const hasTable = rowCount >= 2 && columnCount >= 2;
    
    // Complexity check: many columns or rows suggests complex table
    const isComplex = columnCount > 5 || rowCount > 20;
    
    return { hasTable, isComplex };
}

/**
 * Calculate confidence score based on analysis
 */
function calculateConfidence(analysis) {
    let score = 100;
    const pagesAnalyzed = Math.min(3, analysis.totalPages);
    
    // Deduct points for scanned pages
    const scannedRatio = analysis.scannedPages / pagesAnalyzed;
    if (scannedRatio > 0.7) {
        score -= 60; // High image dominance
    } else if (scannedRatio > 0.3) {
        score -= 30; // Moderate image dominance
    }
    
    // Deduct points for low text content
    const avgTextPerPage = analysis.totalTextLength / pagesAnalyzed;
    if (avgTextPerPage < 50) {
        score -= 40; // Very low text
    } else if (avgTextPerPage < 200) {
        score -= 20; // Low text
    }
    
    // Deduct points for complex tables
    if (analysis.complexTables > 0) {
        score -= 25; // Complex tables may need OCR
    }
    
    // Ensure score is in valid range
    score = Math.max(0, Math.min(100, score));
    
    // Determine confidence level
    let level = 'low';
    if (score >= 70) {
        level = 'high';
    } else if (score >= 40) {
        level = 'medium';
    }
    
    return { level, score };
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.PDFExcelAnalysis = {
        analyzePdf,
        analyzePage,
        detectTableStructure,
        calculateConfidence
    };
}

