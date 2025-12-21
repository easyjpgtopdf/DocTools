"""
Credit Calculator for Premium PDF to Excel Conversion
Per-page credit deduction based on document type
"""

from typing import Optional


# Minimum credits required for premium access
MIN_PREMIUM_CREDITS = 30

# Credit costs per page based on document type
CREDIT_COSTS = {
    "clean_table": 2.0,           # Clean table OCR: 2 credits/page
    "bank_statement": 2.5,         # Bank statements: 2.5 credits/page
    "invoice_report": 3.0,         # Invoices/reports: 3 credits/page
    "heavy_scanned": 6.0,          # Heavy scanned OCR: 6 credits/page
    "default": 2.0                 # Default (fallback)
}

def detect_document_type(filename: str, is_scanned: bool = False, has_complex_tables: bool = False) -> str:
    """
    Detect document type from filename and characteristics.
    
    Args:
        filename: PDF filename (may contain hints)
        is_scanned: Whether PDF is scanned/image-based
        has_complex_tables: Whether PDF has complex tables
    
    Returns:
        Document type string ('clean_table', 'bank_statement', 'invoice_report', 'heavy_scanned')
    """
    filename_lower = filename.lower()
    
    # Bank statements
    if 'bank' in filename_lower or 'statement' in filename_lower:
        return "bank_statement"
    
    # Invoices and reports
    if any(keyword in filename_lower for keyword in ['invoice', 'bill', 'receipt', 'report', 'financial']):
        return "invoice_report"
    
    # Heavy scanned documents
    if is_scanned:
        return "heavy_scanned"
    
    # Default: clean tables
    return "clean_table"

def calculate_required_credits(pages: int, document_type: Optional[str] = None) -> float:
    """
    Calculate required credits for processing PDF pages.
    
    Args:
        pages: Number of pages to process
        document_type: Document type (if None, uses default)
    
    Returns:
        Required credits (float)
    """
    if document_type is None:
        document_type = "default"
    
    cost_per_page = CREDIT_COSTS.get(document_type, CREDIT_COSTS["default"])
    return pages * cost_per_page

def check_premium_access(current_credits: float) -> bool:
    """
    Check if user has premium access (minimum 30 credits).
    
    Args:
        current_credits: User's current credit balance
    
    Returns:
        True if user has premium access, False otherwise
    """
    return current_credits >= MIN_PREMIUM_CREDITS

def get_credit_cost_info(document_type: Optional[str] = None) -> dict:
    """
    Get credit cost information for a document type.
    
    Args:
        document_type: Document type (if None, returns all costs)
    
    Returns:
        Dictionary with credit cost information
    """
    if document_type:
        cost_per_page = CREDIT_COSTS.get(document_type, CREDIT_COSTS["default"])
        return {
            "document_type": document_type,
            "cost_per_page": cost_per_page,
            "minimum_credits": MIN_PREMIUM_CREDITS
        }
    else:
        return {
            "credit_costs": CREDIT_COSTS,
            "minimum_credits": MIN_PREMIUM_CREDITS,
            "costs": {
                "Professional tables (clean)": f"{CREDIT_COSTS['clean_table']} credits/page",
                "Bank statements": f"{CREDIT_COSTS['bank_statement']} credits/page",
                "Invoices & reports": f"{CREDIT_COSTS['invoice_report']} credits/page",
                "Heavy scanned OCR": f"{CREDIT_COSTS['heavy_scanned']} credits/page"
            }
        }

