/**
 * PDF to Excel Pricing Information
 * Displays pricing and credit costs for different document types
 */

const PDF_EXCEL_PRICING = {
    minPremiumCredits: 30,
    pricing: {
        clean_table: {
            name: "Professional Tables",
            creditsPerPage: 2.0,
            description: "Clean table OCR - Standard tables"
        },
        bank_statement: {
            name: "Bank Statements",
            creditsPerPage: 2.5,
            description: "Bank statement processing"
        },
        invoice: {
            name: "Invoices & Reports",
            creditsPerPage: 3.0,
            description: "Invoices and financial reports"
        },
        heavy_scanned: {
            name: "Heavy Scanned OCR",
            creditsPerPage: 6.0,
            description: "Heavy scanned documents with OCR"
        },
        id_card: {
            name: "ID Cards",
            creditsPerPage: 6.0,
            description: "ID card and identity document processing"
        }
    }
};

/**
 * Get credit cost for a document type
 */
function getCreditCost(documentType, isScanned = false, isBankStatement = false, isInvoice = false, isIdCard = false) {
    if (isIdCard) return PDF_EXCEL_PRICING.pricing.id_card.creditsPerPage;
    if (isScanned) return PDF_EXCEL_PRICING.pricing.heavy_scanned.creditsPerPage;
    if (isBankStatement) return PDF_EXCEL_PRICING.pricing.bank_statement.creditsPerPage;
    if (isInvoice) return PDF_EXCEL_PRICING.pricing.invoice.creditsPerPage;
    
    // Default: clean table
    return PDF_EXCEL_PRICING.pricing.clean_table.creditsPerPage;
}

/**
 * Calculate total credits required for pages
 */
function calculateTotalCredits(numPages, creditPerPage) {
    return numPages * creditPerPage;
}

/**
 * Get pricing info for UI display
 */
function getPricingInfo() {
    return PDF_EXCEL_PRICING;
}

// Export
if (typeof window !== 'undefined') {
    window.PDFExcelPricing = {
        getCreditCost,
        calculateTotalCredits,
        getPricingInfo,
        MIN_PREMIUM_CREDITS: PDF_EXCEL_PRICING.minPremiumCredits
    };
}

