/**
 * Enhanced FREE Converter - Maximum Usability Without AI
 * Uses PDF.js, SheetJS, and client-side enhancements
 */

/**
 * Main FREE conversion handler with enhancements
 */
async function handleFreeConversionEnhanced(pdfDoc, selectedPages, filename, pdfAnalysis = null) {
    if (!pdfDoc) {
        showToast('PDF document not loaded', true);
        return;
    }
    
    try {
        showToast('Converting to Excel (Basic)...', false);
        
        const workbook = XLSX.utils.book_new();
        const pagesToProcess = Array.from(selectedPages).sort((a, b) => a - b);
        
        let totalTablesExtracted = 0;
        let hasComplexTable = false;
        
        for (const pageNum of pagesToProcess) {
            try {
                const page = await pdfDoc.getPage(pageNum);
                const textContent = await page.getTextContent();
                
                // Use enhanced table detection if available
                let table = null;
                if (window.PDFExcelFreeEnhancer) {
                    // Enhanced alignment-based detection
                    table = window.PDFExcelFreeEnhancer.detectAlignedTable(textContent.items);
                    
                    // If enhanced detection failed, fall back to basic
                    if (!table || table.length < 2) {
                        table = detectBasicTable(textContent.items);
                    }
                } else {
                    table = detectBasicTable(textContent.items);
                }
                
                if (!table || table.length === 0) {
                    // No table found on this page, skip
                    continue;
                }
                
                // Check for complexity
                if (table.length > 50 || (table[0] && table[0].length > 10)) {
                    hasComplexTable = true;
                }
                
                // Detect and handle merged cells (for FREE, we'll split them)
                if (window.PDFExcelFreeEnhancer) {
                    const mergedCells = window.PDFExcelFreeEnhancer.detectMergedCells(table);
                    if (mergedCells.length > 0) {
                        table = window.PDFExcelFreeEnhancer.splitMergedCells(table, mergedCells);
                    }
                }
                
                // Check if this looks like an ID card
                let isIdCard = false;
                if (window.PDFExcelFreeEnhancer) {
                    isIdCard = window.PDFExcelFreeEnhancer.detectIdCardLayout(table, textContent.items);
                    
                    if (isIdCard) {
                        // Generate ID card template
                        const template = window.PDFExcelFreeEnhancer.generateIdCardTemplate(table, textContent.items);
                        table = [template.headers, ...template.rows];
                    }
                }
                
                // Handle partial export for very large/complex tables
                if (hasComplexTable && table.length > 100 && pdfAnalysis && pdfAnalysis.confidence === 'low') {
                    // Offer partial export for complex docs
                    const confirmPartial = confirm(
                        'This document is complex. Would you like to export the first 100 rows only?\n\n' +
                        'For full conversion with high accuracy, upgrade to Premium.'
                    );
                    
                    if (confirmPartial && window.PDFExcelFreeEnhancer) {
                        table = window.PDFExcelFreeEnhancer.exportPartialTable(table, 100);
                        showToast('Exporting first 100 rows. Upgrade to Premium for full export.', false);
                    }
                }
                
                // Create worksheet
                const worksheet = XLSX.utils.aoa_to_sheet(table);
                
                // Enhance worksheet if enhancer available
                if (window.PDFExcelFreeEnhancer) {
                    // Enhance with header bolding, notes, etc.
                    const tempWorkbook = XLSX.utils.book_new();
                    XLSX.utils.book_append_sheet(tempWorkbook, worksheet, `Page ${pageNum}`);
                    const enhancedWorkbook = window.PDFExcelFreeEnhancer.enhanceExcelWorkbook(
                        tempWorkbook,
                        table,
                        pageNum === pagesToProcess[0]
                    );
                    worksheet = enhancedWorkbook.Sheets[enhancedWorkbook.SheetNames[0]];
                }
                
                XLSX.utils.book_append_sheet(workbook, worksheet, `Page ${pageNum}`);
                totalTablesExtracted++;
                
            } catch (pageError) {
                console.warn(`Error processing page ${pageNum}:`, pageError);
                // Continue with other pages
            }
        }
        
        if (workbook.SheetNames.length === 0) {
            showToast('No tables found in selected pages. This PDF may be scanned. Upgrade to Premium for OCR conversion.', true);
            return;
        }
        
        // Final enhancement: Add notes sheet to first workbook
        if (window.PDFExcelFreeEnhancer && workbook.SheetNames.length > 0) {
            // Notes sheet is already added by enhanceExcelWorkbook for first sheet
            // But we can add a general notes sheet
            const generalNotes = XLSX.utils.aoa_to_sheet([
                ['Conversion Notes'],
                [''],
                ['Conversion Type: Basic (FREE)'],
                [`Pages Converted: ${totalTablesExtracted}`],
                [''],
                ['For scanned PDFs, complex tables, or better accuracy:'],
                ['→ Upgrade to Premium at easyjpgtopdf.com/pricing.html']
            ]);
            XLSX.utils.book_append_sheet(workbook, generalNotes, 'Conversion Info');
        }
        
        // Generate Excel file
        const excelBuffer = XLSX.write(workbook, { 
            bookType: 'xlsx', 
            type: 'array',
            cellStyles: true
        });
        
        const blob = new Blob([excelBuffer], { 
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        });
        
        // Download
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `${filename.replace('.pdf', '')}_basic.xlsx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
        
        showToast(`Excel file downloaded! (${totalTablesExtracted} page(s) converted)`, false);
        
        // Show upgrade suggestion for complex tables
        if (hasComplexTable) {
            setTimeout(() => {
                if (window.PDFExcelUpgradePopup) {
                    window.PDFExcelUpgradePopup.showUpgradePopup(
                        'For better accuracy with complex tables, upgrade to Premium OCR conversion.'
                    );
                }
            }, 2000);
        }
        
    } catch (error) {
        console.error('FREE conversion error:', error);
        showToast('Failed to convert PDF. This file may need Premium OCR conversion.', true);
        
        // Suggest upgrade for errors
        setTimeout(() => {
            if (window.PDFExcelUpgradePopup) {
                window.PDFExcelUpgradePopup.showUpgradePopup(
                    'Conversion failed. This PDF may be scanned or complex. Upgrade to Premium for OCR-powered conversion.'
                );
            }
        }, 1000);
    }
}

/**
 * Basic table detection (fallback)
 */
function detectBasicTable(textItems) {
    if (!textItems || textItems.length === 0) return null;
    
    const rows = {};
    let currentY = null;
    let currentRow = [];
    const yTolerance = 3;
    
    textItems.forEach(item => {
        if (!item.transform || item.transform.length < 6) return;
        
        const y = Math.round(item.transform[5] / yTolerance) * yTolerance;
        const text = (item.str || '').trim();
        
        if (!text) return;
        
        if (currentY === null) {
            currentY = y;
        }
        
        if (Math.abs(y - currentY) > yTolerance) {
            // New row
            if (currentRow.length > 0) {
                if (!rows[currentY]) rows[currentY] = [];
                rows[currentY].push(...currentRow);
            }
            currentRow = [];
            currentY = y;
        }
        
        currentRow.push(text);
    });
    
    // Add last row
    if (currentRow.length > 0 && currentY !== null) {
        if (!rows[currentY]) rows[currentY] = [];
        rows[currentY].push(...currentRow);
    }
    
    // Convert to 2D array
    const table = Object.keys(rows)
        .map(y => parseFloat(y))
        .sort((a, b) => b - a)
        .map(y => rows[y])
        .filter(row => row && row.length > 0);
    
    // Normalize column count
    const maxCols = Math.max(...table.map(row => row.length));
    return table.map(row => {
        while (row.length < maxCols) {
            row.push('');
        }
        return row;
    });
}

// Export
if (typeof window !== 'undefined') {
    window.PDFExcelFreeConverterEnhanced = {
        handleFreeConversionEnhanced,
        detectBasicTable
    };
}

