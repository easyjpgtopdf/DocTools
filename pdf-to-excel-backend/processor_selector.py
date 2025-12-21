"""
Smart Processor Selector for PREMIUM Pipeline
Automatically selects the best Document AI processor based on document characteristics
"""

import os
from typing import Optional, Dict

# Processor mappings
PROCESSOR_MAP: Dict[str, str] = {
    "layout-parser-docai": os.environ.get('DOCAI_LAYOUT_PARSER_ID', 'c79eead38f3ecc38'),
    "pdf-to-excel-docai": os.environ.get('DOCAI_PROCESSOR_ID', '19a07dc1c08ce733'),
    "form-parser-docai": os.environ.get('DOCAI_FORM_PARSER_ID', '9d1bf7e36946b781'),
    "bank-docai": os.environ.get('DOCAI_BANK_ID', '6c8a0e5d0a3dddc4'),
    "identity-docai": os.environ.get('DOCAI_IDENTITY_ID', 'bd5e8109cd2ff2b9'),
    "pay-slip-docai": os.environ.get('DOCAI_PAY_SLIP_ID', '9034bca37aa74cff'),
}

def select_processor_for_document(
    filename: str,
    file_size: int,
    document_type_hint: Optional[str] = None,
    is_scanned: bool = False,
    has_complex_tables: bool = False
) -> str:
    """
    Select the best Document AI processor based on document characteristics.
    
    Args:
        filename: PDF filename (may contain hints like 'invoice', 'bank', etc.)
        file_size: File size in bytes
        document_type_hint: Optional hint from frontend ('invoice', 'bank', 'id', etc.)
        is_scanned: Whether PDF is scanned/image-based
        has_complex_tables: Whether PDF has complex tables
    
    Returns:
        Processor type string (e.g., 'layout-parser-docai')
    """
    filename_lower = filename.lower()
    
    # Domain-specific detection
    if document_type_hint:
        hint_lower = document_type_hint.lower()
        if 'bank' in hint_lower or 'statement' in hint_lower:
            return "bank-docai"
        elif 'invoice' in hint_lower or 'bill' in hint_lower:
            return "form-parser-docai"
        elif 'id' in hint_lower or 'identity' in hint_lower or 'card' in hint_lower:
            return "identity-docai"
        elif 'pay' in hint_lower or 'salary' in hint_lower or 'payslip' in hint_lower:
            return "pay-slip-docai"
    
    # Filename-based detection
    if 'bank' in filename_lower or 'statement' in filename_lower:
        return "bank-docai"
    elif 'invoice' in filename_lower or 'bill' in filename_lower:
        return "form-parser-docai"
    elif 'id' in filename_lower or 'identity' in filename_lower or 'card' in filename_lower:
        return "identity-docai"
    elif 'pay' in filename_lower or 'salary' in filename_lower or 'payslip' in filename_lower:
        return "pay-slip-docai"
    
    # Content-based selection
    if is_scanned:
        # Scanned PDFs: use layout parser (best for image-heavy documents)
        return "layout-parser-docai"
    elif has_complex_tables:
        # Complex tables: use pdf-to-excel processor (specialized for tables)
        return "pdf-to-excel-docai"
    else:
        # Default: form parser (good general-purpose processor)
        return "form-parser-docai"

def get_processor_for_domain(domain: str) -> Optional[str]:
    """
    Get processor for a specific domain/preset.
    
    Args:
        domain: Domain name ('bank', 'invoice', 'financial_report', 'office_report', 'id_card')
    
    Returns:
        Processor type or None if domain not recognized
    """
    domain_map = {
        'bank': 'bank-docai',
        'bank_statement': 'bank-docai',
        'invoice': 'form-parser-docai',
        'financial_report': 'pdf-to-excel-docai',
        'office_report': 'pdf-to-excel-docai',
        'id_card': 'identity-docai',
        'identity': 'identity-docai',
        'payslip': 'pay-slip-docai',
        'pay_slip': 'pay-slip-docai'
    }
    
    return domain_map.get(domain.lower())

