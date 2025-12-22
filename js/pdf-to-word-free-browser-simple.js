/**
 * FREE PDF to Word Converter - Browser-Based (Zero Server Costs)
 * Simple version using PDF.js for text extraction and basic DOCX creation
 */

/**
 * Text item with position information
 */
class TextItem {
    constructor(text, x0, y0, x1, y1, fontSize, pageNum) {
        this.text = text;
        this.x0 = x0;
        this.y0 = y0;
        this.x1 = x1;
        this.y1 = y1;
        this.fontSize = fontSize || 12;
        this.pageNum = pageNum;
    }
}

/**
 * Extract text with positions from PDF using PDF.js
 */
async function extractTextWithPositions(pdfDoc) {
    const textItems = [];
    
    for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
        const page = await pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: 1.0 });
        const textContent = await page.getTextContent();
        const pageHeight = viewport.height;
        
        for (const item of textContent.items) {
            if (!item.str || !item.str.trim()) continue;
            
            const transform = item.transform || [1, 0, 0, 1, 0, 0];
            const x = transform[4] || 0;
            const y = transform[5] || 0;
            const fontSize = Math.sqrt(transform[0] * transform[0] + transform[1] * transform[1]) || 12;
            const textWidth = item.width || (item.str.length * fontSize * 0.6);
            const textHeight = fontSize * 1.2;
            
            const y0_converted = pageHeight - (y + textHeight);
            const y1_converted = pageHeight - y;
            
            textItems.push(new TextItem(
                item.str.trim(),
                x,
                y0_converted,
                x + textWidth,
                y1_converted,
                fontSize,
                pageNum
            ));
        }
    }
    
    return textItems;
}

/**
 * Detect columns by clustering X positions
 */
function detectColumns(textItems, pageNum, tolerance = 10.0) {
    const pageItems = textItems.filter(item => item.pageNum === pageNum);
    if (!pageItems.length) return [];
    
    const xPositions = [...new Set(pageItems.map(item => item.x0))].sort((a, b) => a - b);
    const columns = [];
    let currentCluster = [];
    
    for (const x of xPositions) {
        if (!currentCluster.length || Math.abs(x - currentCluster[currentCluster.length - 1]) <= tolerance) {
            currentCluster.push(x);
        } else {
            if (currentCluster.length) {
                const avgX = currentCluster.reduce((a, b) => a + b, 0) / currentCluster.length;
                columns.push({ x0: avgX, x1: x - tolerance, index: columns.length });
            }
            currentCluster = [x];
        }
    }
    
    if (currentCluster.length) {
        const avgX = currentCluster.reduce((a, b) => a + b, 0) / currentCluster.length;
        const maxX = Math.max(...pageItems.map(item => item.x1));
        columns.push({ x0: avgX, x1: maxX, index: columns.length });
    }
    
    return columns.sort((a, b) => a.x0 - b.x0).map((col, idx) => ({ ...col, index: idx }));
}

/**
 * Assign text item to a column
 */
function assignColumn(textItem, columns) {
    if (!columns.length) return null;
    
    for (const col of columns) {
        if (textItem.x0 >= col.x0 && textItem.x0 <= col.x1) {
            return col.index;
        }
        if (textItem.x0 < col.x1 && textItem.x1 > col.x0) {
            return col.index;
        }
    }
    
    const distances = columns.map(col => Math.abs(textItem.x0 - col.x0));
    return columns[distances.indexOf(Math.min(...distances))].index;
}

/**
 * Detect rows using y-distance + font-size similarity
 */
function detectRows(textItems, pageNum, fontSizeTolerance = 2.0, yToleranceFactor = 0.5) {
    const pageItems = textItems.filter(item => item.pageNum === pageNum);
    if (!pageItems.length) return [];
    
    pageItems.sort((a, b) => b.y0 - a.y0);
    
    const rows = [];
    let currentRow = null;
    
    for (const item of pageItems) {
        if (!currentRow) {
            currentRow = {
                items: [item],
                yCenter: (item.y0 + item.y1) / 2,
                fontSize: item.fontSize,
                yMin: item.y0,
                yMax: item.y1
            };
        } else {
            const itemYCenter = (item.y0 + item.y1) / 2;
            const yDistance = Math.abs(itemYCenter - currentRow.yCenter);
            const fontDiff = Math.abs(item.fontSize - currentRow.fontSize);
            const avgFontSize = (item.fontSize + currentRow.fontSize) / 2;
            const yTolerance = avgFontSize * yToleranceFactor;
            
            if (yDistance <= yTolerance && fontDiff <= fontSizeTolerance) {
                currentRow.items.push(item);
                currentRow.yCenter = (currentRow.yCenter + itemYCenter) / 2;
                currentRow.fontSize = (currentRow.fontSize + item.fontSize) / 2;
                currentRow.yMin = Math.min(currentRow.yMin, item.y0);
                currentRow.yMax = Math.max(currentRow.yMax, item.y1);
            } else {
                rows.push(currentRow);
                currentRow = {
                    items: [item],
                    yCenter: itemYCenter,
                    fontSize: item.fontSize,
                    yMin: item.y0,
                    yMax: item.y1
                };
            }
        }
    }
    
    if (currentRow) rows.push(currentRow);
    return rows;
}

/**
 * Merge multi-line cells
 */
function mergeMultilineCells(cells, yGapThreshold = 5.0) {
    const cellsByCol = {};
    
    for (const cell of cells) {
        if (!cellsByCol[cell.colIndex]) cellsByCol[cell.colIndex] = [];
        cellsByCol[cell.colIndex].push(cell);
    }
    
    const mergedCells = [];
    
    for (const colIdx in cellsByCol) {
        const colCells = cellsByCol[colIdx].sort((a, b) => a.rowIndex - b.rowIndex);
        let currentCell = null;
        
        for (const cell of colCells) {
            if (!currentCell) {
                currentCell = cell;
            } else {
                const yGap = Math.abs(cell.y0 - currentCell.y1);
                if (yGap <= yGapThreshold) {
                    currentCell.text += " " + cell.text;
                    currentCell.y1 = Math.max(currentCell.y1, cell.y1);
                    currentCell.y0 = Math.min(currentCell.y0, cell.y0);
                } else {
                    mergedCells.push(currentCell);
                    currentCell = cell;
                }
            }
        }
        if (currentCell) mergedCells.push(currentCell);
    }
    
    return mergedCells;
}

/**
 * Detect headers and footers
 */
function detectHeaderFooter(textItems, allPages) {
    if (allPages.length < 2) return { headers: [], footers: [] };
    
    const headerCounts = {};
    const footerCounts = {};
    
    for (const pageNum of allPages) {
        const pageItems = textItems.filter(item => item.pageNum === pageNum);
        if (!pageItems.length) continue;
        
        const yMax = Math.max(...pageItems.map(item => item.y1));
        const yMin = Math.min(...pageItems.map(item => item.y0));
        const pageHeight = yMax - yMin;
        const headerThreshold = yMax - (pageHeight * 0.1);
        const footerThreshold = yMin + (pageHeight * 0.1);
        
        for (const item of pageItems) {
            if (item.y1 >= headerThreshold) {
                headerCounts[item.text] = (headerCounts[item.text] || 0) + 1;
            } else if (item.y0 <= footerThreshold) {
                footerCounts[item.text] = (footerCounts[item.text] || 0) + 1;
            }
        }
    }
    
    const minOccurrences = Math.ceil(allPages.length * 0.5);
    const headers = Object.keys(headerCounts).filter(text => headerCounts[text] >= minOccurrences);
    const footers = Object.keys(footerCounts).filter(text => footerCounts[text] >= minOccurrences);
    
    return { headers, footers };
}

/**
 * Detect visual PDF
 */
async function detectVisualPDF(pdfDoc) {
    try {
        let totalTextItems = 0;
        let totalImages = 0;
        
        for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
            const page = await pdfDoc.getPage(pageNum);
            const textContent = await page.getTextContent();
            totalTextItems += textContent.items.filter(item => item.str && item.str.trim()).length;
            
            const opList = await page.getOperatorList();
            for (const op of opList.fnArray) {
                if (op === 82 || op === 83) totalImages++;
            }
        }
        
        const avgTextItemsPerPage = totalTextItems / pdfDoc.numPages;
        const avgImagesPerPage = totalImages / pdfDoc.numPages;
        
        if (avgImagesPerPage > 3) {
            return { isVisual: true, reason: 'High image density detected' };
        }
        if (avgTextItemsPerPage < 10) {
            return { isVisual: true, reason: 'Very low text content' };
        }
        
        return { isVisual: false, reason: '' };
    } catch (e) {
        console.warn('Visual PDF detection error:', e);
        return { isVisual: false, reason: '' };
    }
}

/**
 * Create simple DOCX file using docx library
 */
async function convertPdfToWordBrowser(pdfDoc, progressCallback) {
    if (!progressCallback) progressCallback = () => {};
    
    progressCallback(10, 'Extracting text from PDF...');
    const textItems = await extractTextWithPositions(pdfDoc);
    
    if (!textItems.length) {
        throw new Error('No text content found in PDF');
    }
    
    progressCallback(20, 'Detecting visual elements...');
    const visualCheck = await detectVisualPDF(pdfDoc);
    if (visualCheck.isVisual) {
        throw new Error(`This document contains complex visual layout. ${visualCheck.reason} Use Premium for accurate Excel conversion.`);
    }
    
    progressCallback(30, 'Analyzing document structure...');
    const allPages = [...new Set(textItems.map(item => item.pageNum))].sort((a, b) => a - b);
    const { headers, footers } = detectHeaderFooter(textItems, allPages);
    
    progressCallback(40, 'Loading Word library...');
    
    // Try to load docx library
    let docx;
    try {
        docx = await import('https://unpkg.com/docx@8.5.0/build/index.js');
    } catch (e) {
        throw new Error('Failed to load Word library. Please check your internet connection.');
    }
    
    progressCallback(50, 'Creating Word document...');
    
    const children = [];
    
    for (let pageIdx = 0; pageIdx < allPages.length; pageIdx++) {
        const pageNum = allPages[pageIdx];
        const progress = 50 + (pageIdx / allPages.length) * 40;
        progressCallback(progress, `Processing page ${pageNum}/${allPages.length}...`);
        
        if (pageIdx > 0) {
            children.push(new docx.Paragraph({ text: '', pageBreakBefore: true }));
        }
        
        const pageItems = textItems.filter(item => 
            item.pageNum === pageNum &&
            !headers.includes(item.text) &&
            !footers.includes(item.text)
        );
        
        if (!pageItems.length) continue;
        
        const columns = detectColumns(pageItems, pageNum);
        const rows = detectRows(pageItems, pageNum);
        
        if (columns.length && rows.length) {
            const cells = [];
            for (let rowIdx = 0; rowIdx < rows.length; rowIdx++) {
                const row = rows[rowIdx];
                for (const item of row.items) {
                    const colIdx = assignColumn(item, columns);
                    if (colIdx !== null) {
                        cells.push({
                            text: item.text,
                            colIndex: colIdx,
                            rowIndex: rowIdx
                        });
                    }
                }
            }
            
            const mergedCells = mergeMultilineCells(cells);
            
            if (mergedCells.length) {
                const maxCol = Math.max(...mergedCells.map(c => c.colIndex));
                const maxRow = Math.max(...mergedCells.map(c => c.rowIndex));
                
                const tableRows = [];
                for (let r = 0; r <= maxRow; r++) {
                    const rowCells = [];
                    for (let c = 0; c <= maxCol; c++) {
                        const cell = mergedCells.find(ce => ce.rowIndex === r && ce.colIndex === c);
                        rowCells.push(new docx.TableCell({
                            children: [new docx.Paragraph({ text: cell ? cell.text : '' })]
                        }));
                    }
                    tableRows.push(new docx.TableRow({ children: rowCells }));
                }
                
                children.push(new docx.Table({ rows: tableRows }));
            } else {
                const sorted = pageItems.sort((a, b) => b.y0 - a.y0);
                for (const item of sorted) {
                    children.push(new docx.Paragraph({ text: item.text }));
                }
            }
        } else {
            const sorted = pageItems.sort((a, b) => b.y0 - a.y0);
            for (const item of sorted) {
                children.push(new docx.Paragraph({ text: item.text }));
            }
        }
    }
    
    progressCallback(95, 'Generating Word document...');
    
    const doc = new docx.Document({
        sections: [{
            properties: {},
            children: children
        }]
    });
    
    const blob = await docx.Packer.toBlob(doc);
    
    progressCallback(100, 'Conversion complete!');
    
    return blob;
}

// Export
if (typeof window !== 'undefined') {
    window.convertPdfToWordBrowser = convertPdfToWordBrowser;
    window.detectVisualPDF = detectVisualPDF;
}

