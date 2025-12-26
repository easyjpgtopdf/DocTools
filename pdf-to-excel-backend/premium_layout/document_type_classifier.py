"""
Document Type Classifier
Analyzes Document AI output to classify document type.
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types"""
    INVOICE = "invoice"
    BANK_STATEMENT = "bank"
    RESUME = "resume"
    CERTIFICATE = "certificate"
    ID_CARD = "id_card"
    LETTER = "letter"
    OFFICE_DOCUMENT = "office_document"
    BILL = "bill"
    DIGITAL_PDF = "digital_pdf"
    OCR_IMAGE = "ocr_image"
    UNKNOWN = "unknown"


class DocumentTypeClassifier:
    """Classifies document type based on Document AI output"""
    
    # Keywords for different document types
    INVOICE_KEYWORDS = [
        'invoice', 'bill', 'tax', 'total', 'amount due', 'subtotal',
        'invoice number', 'invoice date', 'due date', 'payment terms',
        'item', 'quantity', 'price', 'tax', 'gst', 'vat'
    ]
    
    BANK_KEYWORDS = [
        'account', 'balance', 'transaction', 'debit', 'credit',
        'statement', 'bank', 'deposit', 'withdrawal', 'balance',
        'date', 'description', 'amount', 'available balance'
    ]
    
    RESUME_KEYWORDS = [
        'resume', 'cv', 'curriculum vitae', 'education', 'experience',
        'skills', 'objective', 'summary', 'qualification', 'employment',
        'work history', 'professional', 'contact', 'phone', 'email'
    ]
    
    CERTIFICATE_KEYWORDS = [
        'certificate', 'certified', 'this is to certify', 'awarded',
        'completion', 'achievement', 'issued', 'date of issue',
        'certificate number', 'valid', 'authorized'
    ]
    
    ID_CARD_KEYWORDS = [
        'id card', 'identity', 'identification', 'card number',
        'date of birth', 'dob', 'address', 'photo', 'signature',
        'valid until', 'issued by', 'government'
    ]
    
    LETTER_KEYWORDS = [
        'dear', 'sir', 'madam', 'yours sincerely', 'yours faithfully',
        'regards', 'subject', 'reference', 'date', 'to', 'from',
        'letter', 'correspondence'
    ]
    
    OFFICE_KEYWORDS = [
        'memo', 'memorandum', 'report', 'agenda', 'minutes',
        'meeting', 'department', 'organization', 'company'
    ]
    
    BILL_KEYWORDS = [
        'bill', 'receipt', 'payment', 'charges', 'fees',
        'service charge', 'tax', 'total amount'
    ]
    
    def __init__(self):
        """Initialize classifier"""
        pass
    
    def classify(self, document: Any, document_text: str = '') -> DocumentType:
        """
        Classify document type based on Document AI output.
        
        Args:
            document: Document AI Document object
            document_text: Extracted text from document
            
        Returns:
            DocumentType enum value
        """
        if not document_text:
            # Try to get text from document if not provided
            if hasattr(document, 'text') and document.text:
                document_text = document.text
            else:
                logger.warning("No text available for classification")
                return DocumentType.UNKNOWN
        
        # Normalize text for keyword matching
        text_lower = document_text.lower()
        
        # Check for native tables first (indicates structured document)
        has_tables = False
        if hasattr(document, 'pages') and document.pages:
            for page in document.pages:
                if hasattr(page, 'tables') and page.tables:
                    has_tables = True
                    break
        
        # Score each document type
        scores = {
            DocumentType.INVOICE: self._score_keywords(text_lower, self.INVOICE_KEYWORDS),
            DocumentType.BANK_STATEMENT: self._score_keywords(text_lower, self.BANK_KEYWORDS),
            DocumentType.RESUME: self._score_keywords(text_lower, self.RESUME_KEYWORDS),
            DocumentType.CERTIFICATE: self._score_keywords(text_lower, self.CERTIFICATE_KEYWORDS),
            DocumentType.ID_CARD: self._score_keywords(text_lower, self.ID_CARD_KEYWORDS),
            DocumentType.LETTER: self._score_keywords(text_lower, self.LETTER_KEYWORDS),
            DocumentType.OFFICE_DOCUMENT: self._score_keywords(text_lower, self.OFFICE_KEYWORDS),
            DocumentType.BILL: self._score_keywords(text_lower, self.BILL_KEYWORDS),
        }
        
        # Boost score if tables are present (more likely to be structured documents)
        if has_tables:
            scores[DocumentType.INVOICE] += 2
            scores[DocumentType.BANK_STATEMENT] += 2
            scores[DocumentType.OFFICE_DOCUMENT] += 1
        
        # Get highest scoring type
        max_score = max(scores.values())
        if max_score == 0:
            # Check if it's a digital PDF (has text but no clear structure)
            if len(document_text) > 100 and not has_tables:
                return DocumentType.DIGITAL_PDF
            return DocumentType.UNKNOWN
        
        # Return type with highest score
        for doc_type, score in scores.items():
            if score == max_score:
                logger.info(f"Classified document as: {doc_type.value} (score: {score})")
                return doc_type
        
        return DocumentType.UNKNOWN
    
    def _score_keywords(self, text: str, keywords: List[str]) -> int:
        """Score text based on keyword matches"""
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        return score
    
    def get_classification_metadata(self, doc_type: DocumentType) -> Dict[str, Any]:
        """Get metadata for a document type"""
        return {
            'type': doc_type.value,
            'has_structured_layout': doc_type in [
                DocumentType.INVOICE,
                DocumentType.BANK_STATEMENT,
                DocumentType.RESUME,
                DocumentType.CERTIFICATE,
                DocumentType.ID_CARD,
                DocumentType.OFFICE_DOCUMENT
            ],
            'requires_heuristic': doc_type not in [
                DocumentType.UNKNOWN,
                DocumentType.DIGITAL_PDF
            ]
        }

