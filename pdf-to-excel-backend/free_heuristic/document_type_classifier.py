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
        Document type: 'invoice' | 'bank' | 'resume' | 'certificate' | 'form' | 'letter' | 'unknown'
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
        invoice_keywords = ['invoice', 'bill', 'amount due', 'total', 'subtotal', 'tax', 'invoice no', 'invoice number']
        bank_keywords = ['account', 'balance', 'transaction', 'debit', 'credit', 'statement', 'bank', 'account number']
        resume_keywords = ['resume', 'cv', 'curriculum vitae', 'education', 'experience', 'skills', 'objective', 'summary']
        certificate_keywords = ['certificate', 'certified', 'award', 'achievement', 'diploma', 'degree', 'issued']
        form_keywords = ['form', 'application', 'please fill', 'signature', 'date', 'name', 'address', 'phone']
        letter_keywords = ['dear', 'sincerely', 'yours', 'regards', 'letter', 'to whom it may concern']
        
        # Count keyword matches
        invoice_score = sum(1 for kw in invoice_keywords if kw in full_text)
        bank_score = sum(1 for kw in bank_keywords if kw in full_text)
        resume_score = sum(1 for kw in resume_keywords if kw in full_text)
        certificate_score = sum(1 for kw in certificate_keywords if kw in full_text)
        form_score = sum(1 for kw in form_keywords if kw in full_text)
        letter_score = sum(1 for kw in letter_keywords if kw in full_text)
        
        # Find highest score
        scores = {
            'invoice': invoice_score,
            'bank': bank_score,
            'resume': resume_score,
            'certificate': certificate_score,
            'form': form_score,
            'letter': letter_score
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
        'invoice': False,      # Do nothing - LibreOffice output trusted
        'bank': False,          # Do nothing - LibreOffice output trusted
        'resume': True,         # Apply heuristic
        'certificate': True,    # Apply heuristic
        'form': True,           # Apply heuristic
        'letter': True,         # Apply heuristic
        'unknown': False        # Skip heuristic
    }

