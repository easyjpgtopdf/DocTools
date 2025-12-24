"""
Pre-Grid Layout Inference for FREE PDF to Excel Pipeline.
Runs BEFORE detect_table_grid() to force 2-column layout for specific document types.

Operates ONLY on text_objects (x, y, text).
NO Excel access, NO LibreOffice change, CPU-only.
"""

import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Document types that should use forced 2-column layout
FORCE_TWO_COLUMN_TYPES = [
    'bill_or_receipt',
    'bill',
    'receipt',
    'generic_form',
    'form',
    'certificate',
    'id_card'
]

# Document types that should use standard table grid detection
USE_STANDARD_GRID_TYPES = [
    'invoice',
    'bank_statement',
    'table',
    'unknown'
]


def infer_document_type_from_text(text_objects: List[Dict]) -> str:
    """
    Lightweight document type inference from text_objects only.
    Used BEFORE Excel creation, so we can't use document_type_classifier.
    
    Args:
        text_objects: List of text objects with 'text', 'x', 'y' keys
        
    Returns:
        Document type string: 'bill_or_receipt' | 'generic_form' | 'certificate' | 
                              'id_card' | 'invoice' | 'bank_statement' | 'unknown'
    """
    if not text_objects:
        return 'unknown'
    
    # Collect all text content
    full_text = ' '.join([obj.get('text', '').lower() for obj in text_objects if obj.get('text')])
    
    # Simple keyword-based classification (lightweight, O(n))
    bill_receipt_keywords = [
        'receipt', 'bill', 'payment receipt', 'transaction receipt', 'bill payment receipt',
        'biller name', 'biller id', 'b-connect txn id', 'approval ref no',
        'consumer number', 'mobile number', 'payment mode', 'payment status',
        'payment channel', 'bill date', 'bill amount', 'total amount',
        'platform fee', 'convenience fee', 'spice money'
    ]
    
    form_keywords = [
        'form', 'application', 'please fill', 'signature', 'registration number',
        'gst', 'website url', 'agent name', 'agent id', 'transaction date'
    ]
    
    certificate_keywords = [
        'certificate', 'certified', 'award', 'achievement', 'diploma', 'degree',
        'issued', 'certification', 'awarded'
    ]
    
    id_card_keywords = [
        'id card', 'identity card', 'identification', 'photo id', 'government id',
        'national id', 'driving license', 'license number', 'date of birth'
    ]
    
    invoice_keywords = [
        'invoice', 'invoice no', 'invoice number', 'invoice date',
        'billing address', 'shipping address', 'subtotal', 'tax'
    ]
    
    bank_statement_keywords = [
        'bank statement', 'account statement', 'account summary', 'statement period',
        'opening balance', 'closing balance', 'bank name', 'debit', 'credit'
    ]
    
    # Count matches
    bill_receipt_score = sum(1 for kw in bill_receipt_keywords if kw in full_text)
    form_score = sum(1 for kw in form_keywords if kw in full_text)
    certificate_score = sum(1 for kw in certificate_keywords if kw in full_text)
    id_card_score = sum(1 for kw in id_card_keywords if kw in full_text)
    invoice_score = sum(1 for kw in invoice_keywords if kw in full_text)
    bank_statement_score = sum(1 for kw in bank_statement_keywords if kw in full_text)
    
    # Find highest score
    scores = {
        'bill_or_receipt': bill_receipt_score,
        'generic_form': form_score,
        'certificate': certificate_score,
        'id_card': id_card_score,
        'invoice': invoice_score,
        'bank_statement': bank_statement_score
    }
    
    max_score = max(scores.values())
    
    # Require at least 2 keyword matches for classification
    if max_score >= 2:
        doc_type = max(scores, key=scores.get)
        logger.info(f"Pre-grid: Document type inferred as: {doc_type} (score: {max_score})")
        return doc_type
    
    logger.info("Pre-grid: Document type inferred as: unknown (insufficient keyword matches)")
    return 'unknown'


def infer_pre_grid_from_text(
    text_objects: List[Dict],
    page_width: float,
    page_height: float
) -> Tuple[List[float], List[float]]:
    """
    Infer 2-column grid layout from text_objects for form-like documents.
    
    Strategy:
    1. Cluster X positions into LEFT and RIGHT groups using median
    2. Force exactly 2 virtual column boundaries
    3. Row boundaries from Y positions
    
    Args:
        text_objects: List of text objects with 'x', 'y', 'text' keys
        page_width: Page width in points
        page_height: Page height in points
        
    Returns:
        (column_boundaries, row_boundaries)
        - column_boundaries: [min_x - padding, median_x, max_x + padding]
        - row_boundaries: Sorted Y positions (top to bottom, reverse order)
    """
    if not text_objects:
        # Fallback: return default boundaries
        return [0.0, page_width], [0.0, page_height]
    
    # Extract X positions
    x_positions = [obj.get('x', 0) for obj in text_objects if obj.get('x') is not None]
    
    if not x_positions:
        return [0.0, page_width], [0.0, page_height]
    
    # Calculate median X position to split into LEFT and RIGHT
    sorted_x = sorted(x_positions)
    median_x = sorted_x[len(sorted_x) // 2]
    
    # Separate into LEFT and RIGHT groups
    left_group = [x for x in sorted_x if x < median_x]
    right_group = [x for x in sorted_x if x >= median_x]
    
    # Calculate boundaries for each group
    min_x = min(x_positions) if x_positions else 0.0
    max_x = max(x_positions) if x_positions else page_width
    
    # Padding: 5% of page width or 20 points, whichever is smaller
    padding = min(page_width * 0.05, 20.0)
    
    # Force 2-column layout:
    # Column 0: Left edge to median (with padding)
    # Column 1: Median to right edge (with padding)
    column_boundaries = [
        max(0.0, min_x - padding),  # Left boundary
        median_x,                   # Middle boundary (split point)
        min(page_width, max_x + padding)  # Right boundary
    ]
    
    # Extract Y positions for row boundaries
    y_positions = sorted(set([obj.get('y', 0) for obj in text_objects if obj.get('y') is not None]), reverse=True)
    
    if not y_positions:
        row_boundaries = [0.0, page_height]
    else:
        # Add page edges
        row_boundaries = [max(y_positions[0], page_height)] + y_positions + [min(y_positions[-1], 0.0)]
        # Remove duplicates and sort (top to bottom, reverse order)
        row_boundaries = sorted(set(row_boundaries), reverse=True)
    
    logger.info(f"Pre-grid: Forced 2-column layout - boundaries: {column_boundaries}, rows: {len(row_boundaries)}")
    
    return column_boundaries, row_boundaries


def should_apply_pre_grid_heuristic(doc_type: str) -> bool:
    """
    Check if pre-grid heuristic should be applied for this document type.
    
    Args:
        doc_type: Document type string
        
    Returns:
        True if pre-grid should be applied, False otherwise
    """
    return doc_type in FORCE_TWO_COLUMN_TYPES

