"""
Pricing and Credit Logic for PDF to Excel Conversion
Per-page credit consumption based on document type
"""

from typing import Optional

# Minimum credits required for premium access
MIN_PREMIUM_CREDITS = 30

# Pricing per page (in credits) by document type
CREDIT_PRICING = {
    "clean_table": 2.0,          # Clean table OCR
    "bank_statement": 2.5,        # Bank statements
    "invoice": 3.0,               # Invoices & reports
    "heavy_scanned": 6.0,         # Heavy scanned OCR
    "id_card": 6.0,               # ID cards
    "default": 2.0                # Default (fallback)
}

def get_credit_cost_for_document_type(
    document_type: Optional[str] = None,
    is_scanned: bool = False,
    is_bank_statement: bool = False,
    is_invoice: bool = False,
    is_id_card: bool = False
) -> float:
    """
    Calculate credit cost per page based on document type.
    
    Args:
        document_type: Document type hint ('bank_statement', 'invoice', 'id_card', etc.)
        is_scanned: Whether PDF is scanned/heavy OCR
        is_bank_statement: Whether document is a bank statement
        is_invoice: Whether document is an invoice/report
        is_id_card: Whether document is an ID card
    
    Returns:
        Credit cost per page (float)
    """
    # Priority order: explicit type > flags > default
    
    if document_type:
        doc_type_lower = document_type.lower()
        if 'bank' in doc_type_lower or 'statement' in doc_type_lower:
            return CREDIT_PRICING["bank_statement"]
        elif 'invoice' in doc_type_lower or 'bill' in doc_type_lower or 'report' in doc_type_lower:
            return CREDIT_PRICING["invoice"]
        elif 'id' in doc_type_lower or 'identity' in doc_type_lower or 'card' in doc_type_lower:
            return CREDIT_PRICING["id_card"]
        elif 'scanned' in doc_type_lower or 'heavy' in doc_type_lower:
            return CREDIT_PRICING["heavy_scanned"]
    
    # Check flags
    if is_id_card:
        return CREDIT_PRICING["id_card"]
    elif is_scanned:
        return CREDIT_PRICING["heavy_scanned"]
    elif is_bank_statement:
        return CREDIT_PRICING["bank_statement"]
    elif is_invoice:
        return CREDIT_PRICING["invoice"]
    
    # Default: clean table OCR
    return CREDIT_PRICING["clean_table"]

def calculate_total_credits_required(
    num_pages: int,
    credit_per_page: float
) -> float:
    """
    Calculate total credits required for conversion.
    
    Args:
        num_pages: Number of pages to process
        credit_per_page: Credit cost per page
    
    Returns:
        Total credits required (float)
    """
    return num_pages * credit_per_page

def can_access_premium(current_credits: float) -> bool:
    """
    Check if user has sufficient credits for premium access.
    
    Args:
        current_credits: User's current credit balance
    
    Returns:
        True if credits >= MIN_PREMIUM_CREDITS, False otherwise
    """
    return current_credits >= MIN_PREMIUM_CREDITS

def get_pricing_info() -> dict:
    """
    Get pricing information for UI display.
    
    Returns:
        Dictionary with pricing details
    """
    return {
        "min_premium_credits": MIN_PREMIUM_CREDITS,
        "pricing": {
            "clean_table": {
                "name": "Professional Tables",
                "credits_per_page": CREDIT_PRICING["clean_table"],
                "description": "Clean table OCR"
            },
            "bank_statement": {
                "name": "Bank Statements",
                "credits_per_page": CREDIT_PRICING["bank_statement"],
                "description": "Bank statement processing"
            },
            "invoice": {
                "name": "Invoices & Reports",
                "credits_per_page": CREDIT_PRICING["invoice"],
                "description": "Invoices and financial reports"
            },
            "heavy_scanned": {
                "name": "Heavy Scanned OCR",
                "credits_per_page": CREDIT_PRICING["heavy_scanned"],
                "description": "Heavy scanned documents with OCR"
            },
            "id_card": {
                "name": "ID Cards",
                "credits_per_page": CREDIT_PRICING["id_card"],
                "description": "ID card and identity document processing"
            }
        }
    }

