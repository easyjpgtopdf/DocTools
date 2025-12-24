"""
Document Type Classifier for FREE PDF to Excel Pipeline.
Inspects Excel content to classify document type.

CPU-only, O(n) complexity, no ML/OCR.
"""

import logging
from typing import Dict, List, Optional
import io

logger = logging.getLogger(__name__)

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    logger.warning("openpyxl not available for document classification")


def classify_document_type(excel_path: str) -> str:
    """
    Classify document type by inspecting Excel content.
    
    Args:
        excel_path: Path to Excel file
        
    Returns:
        Document type: 'invoice' | 'bank_statement' | 'bill_or_receipt' | 'resume' | 'certificate' | 'id_card' | 'letter' | 'generic_form' | 'unknown'
    """
    if not HAS_OPENPYXL:
        return 'unknown'
    
    try:
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        ws = wb.active
        
        # Collect all text content (first 100 rows, first 10 columns)
        text_content = []
        for row_idx, row in enumerate(ws.iter_rows(max_row=100, max_col=10, values_only=True), start=1):
            row_text = []
            for cell_value in row:
                if cell_value is not None:
                    cell_str = str(cell_value).strip().lower()
                    if cell_str:
                        row_text.append(cell_str)
            if row_text:
                text_content.append(' '.join(row_text))
        
        # Combine all text
        full_text = ' '.join(text_content)
        
        # Classification rules (simple keyword-based, O(n))
        invoice_keywords = ['invoice', 'invoice no', 'invoice number', 'invoice date', 'billing address', 'shipping address']
        bank_statement_keywords = ['bank statement', 'account statement', 'account summary', 'statement period', 'opening balance', 'closing balance', 'bank name']
        bill_or_receipt_keywords = ['receipt', 'bill', 'payment receipt', 'transaction receipt', 'bill payment receipt', 
                                    'bill number', 'receipt number', 'paid amount', 'payment method', 'transaction id',
                                    'biller name', 'biller id', 'b-connect txn id', 'approval ref no', 'consumer number',
                                    'mobile number', 'payment mode', 'payment status', 'payment channel', 'bill date',
                                    'bill amount', 'total amount', 'platform fee', 'convenience fee', 'spice money']
        resume_keywords = ['resume', 'cv', 'curriculum vitae', 'education', 'experience', 'skills', 'objective', 'summary', 'work history', 'employment']
        certificate_keywords = ['certificate', 'certified', 'award', 'achievement', 'diploma', 'degree', 'issued', 'certification', 'awarded']
        id_card_keywords = ['id card', 'identity card', 'identification', 'photo id', 'government id', 'national id', 'driving license', 'license number']
        letter_keywords = ['dear', 'sincerely', 'yours', 'regards', 'letter', 'to whom it may concern', 'subject', 'reference']
        generic_form_keywords = ['form', 'application', 'please fill', 'signature', 'date', 'name', 'address', 'phone', 
                        'registration number', 'gst', 'website url', 'agent name', 'agent id', 'transaction date',
                        'total amount', 'biller', 'platform fee', 'convenience fee', 'bill amount', 'bill date',
                        'payment channel', 'payment status', 'details', 'field', 'fill in']
        
        # Count keyword matches
        invoice_score = sum(1 for kw in invoice_keywords if kw in full_text)
        bank_statement_score = sum(1 for kw in bank_statement_keywords if kw in full_text)
        bill_or_receipt_score = sum(1 for kw in bill_or_receipt_keywords if kw in full_text)
        resume_score = sum(1 for kw in resume_keywords if kw in full_text)
        certificate_score = sum(1 for kw in certificate_keywords if kw in full_text)
        id_card_score = sum(1 for kw in id_card_keywords if kw in full_text)
        letter_score = sum(1 for kw in letter_keywords if kw in full_text)
        generic_form_score = sum(1 for kw in generic_form_keywords if kw in full_text)
        
        # Find highest score
        scores = {
            'invoice': invoice_score,
            'bank_statement': bank_statement_score,
            'bill_or_receipt': bill_or_receipt_score,
            'resume': resume_score,
            'certificate': certificate_score,
            'id_card': id_card_score,
            'letter': letter_score,
            'generic_form': generic_form_score
        }
        
        max_score = max(scores.values())
        
        # Require at least 2 keyword matches for classification
        if max_score >= 2:
            doc_type = max(scores, key=scores.get)
            logger.info(f"Document classified as: {doc_type} (score: {max_score})")
            return doc_type
        
        logger.info("Document classified as: unknown (insufficient keyword matches)")
        return 'unknown'
        
    except Exception as e:
        logger.warning(f"Error classifying document type: {e}")
        return 'unknown'


def get_classification_rules() -> Dict[str, bool]:
    """
    Get rules for which document types should apply heuristic fixes.
    
    Returns:
        Dictionary mapping document type to whether heuristic should be applied
    """
    return {
        'invoice': True,           # Apply minimal fixes (merged rows, empty gaps, numeric alignment)
        'bank_statement': True,   # Apply minimal fixes (merged rows, empty gaps, numeric alignment)
        'bill_or_receipt': True,  # Apply label-value inference
        'resume': True,           # Apply section-to-rows conversion
        'certificate': True,      # Apply 2-column layout
        'id_card': True,          # Apply 2-column layout
        'letter': True,           # Apply paragraph-to-rows
        'generic_form': True,     # Apply form layout fixes
        'unknown': False          # Skip heuristic
    }

