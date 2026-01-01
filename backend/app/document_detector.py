"""
Central Document Detection Engine.
Analyzes PDFs and determines the best conversion tool and method.

This module provides the core decision logic used by all PDF conversion tools
to route documents to the appropriate converter (Word vs Excel) based on content.
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from app.converter import pdf_has_text, get_page_count
from app.docai_client import DocumentAIClient, process_pdf_to_layout
from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class DocumentAnalysis:
    """Result of document analysis."""
    page_count: int
    file_size_bytes: int
    has_text: bool
    is_scanned: bool
    has_tables: bool
    is_id_card_like: bool
    suggested_tool: str  # "word" or "excel"
    requires_premium: bool
    reason: str
    engine: str  # "libreoffice" or "docai"
    credit_cost_per_page: float
    table_count: int = 0
    confidence: Optional[float] = None


def detect_document(
    pdf_path: str,
    file_size_bytes: int,
    settings: Optional[Settings] = None,
    use_docai_for_analysis: bool = True
) -> DocumentAnalysis:
    """
    Central decision engine for PDF document analysis.
    
    Analyzes a PDF to determine:
    - Page count
    - File size
    - Text extraction capability
    - Whether it's scanned (no text)
    - Whether it contains tables
    - Whether it's ID card-like
    - Best conversion tool (Word vs Excel)
    - Required premium status
    - Recommended engine
    - Credit cost
    
    Args:
        pdf_path: Path to PDF file
        file_size_bytes: File size in bytes
        settings: Optional settings for Document AI access
        use_docai_for_analysis: Whether to use Document AI for table detection (default: True)
        
    Returns:
        DocumentAnalysis with all detected characteristics and recommendations
    """
    logger.info(f"Analyzing document: {pdf_path} ({file_size_bytes} bytes)")
    
    # Basic analysis
    page_count = get_page_count(pdf_path)
    has_text = pdf_has_text(pdf_path)
    is_scanned = not has_text
    
    # Initialize default values
    has_tables = False
    is_id_card_like = False
    table_count = 0
    confidence = None
    
    # Advanced analysis using Document AI if available
    if use_docai_for_analysis and settings:
        try:
            # Read PDF bytes
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            # Use Document AI for deep analysis
            try:
                parsed_doc = process_pdf_to_layout(
                    settings.project_id,
                    settings.docai_location,
                    settings.docai_processor_id,
                    pdf_bytes
                )
                
                # Check for tables
                table_count = len(parsed_doc.tables) if parsed_doc.tables else 0
                has_tables = table_count > 0
                
                # ID card detection heuristics
                # ID cards typically have:
                # - Small page count (1-2 pages)
                # - Structured fields (name, date, number, etc.)
                # - May have photos/images
                # - Often have table-like structures or form fields
                if page_count <= 2:
                    # Check for ID card indicators in text
                    full_text_lower = parsed_doc.full_text.lower() if parsed_doc.full_text else ""
                    id_keywords = [
                        'id card', 'identity card', 'passport', 'license', 'driver license',
                        'date of birth', 'date of issue', 'expiry date', 'valid until',
                        'identification number', 'national id', 'ssn', 'social security'
                    ]
                    has_id_keywords = any(keyword in full_text_lower for keyword in id_keywords)
                    
                    # If it has structured layout + ID keywords or small structured tables
                    if (has_id_keywords and has_tables) or (has_tables and table_count <= 3):
                        is_id_card_like = True
                        logger.info(f"Detected ID card-like structure (keywords: {has_id_keywords}, tables: {has_tables})")
                
                logger.info(f"Document AI analysis: {table_count} tables, ID card: {is_id_card_like}")
                
            except Exception as docai_error:
                logger.warning(f"Document AI analysis failed, using basic detection: {docai_error}")
                # Fallback to basic detection
                has_tables = False
                is_id_card_like = False
        
        except Exception as e:
            logger.warning(f"Document AI analysis unavailable: {e}")
            # Continue with basic analysis
    
    # DECISION ENGINE LOGIC
    
    # RULE 1: Tables or ID cards → ALWAYS Excel (Premium Pro)
    if has_tables or is_id_card_like:
        suggested_tool = "excel"
        requires_premium = True
        reason = "Document contains tables or structured data (ID card/invoice/form). Excel conversion provides better accuracy."
        engine = "docai"  # Excel conversion requires DocAI
        credit_cost_per_page = 2.0  # Premium pricing for Excel
        
        logger.info(f"Routing to Excel: has_tables={has_tables}, is_id_card={is_id_card_like}")
        return DocumentAnalysis(
            page_count=page_count,
            file_size_bytes=file_size_bytes,
            has_text=has_text,
            is_scanned=is_scanned,
            has_tables=has_tables,
            is_id_card_like=is_id_card_like,
            suggested_tool=suggested_tool,
            requires_premium=requires_premium,
            reason=reason,
            engine=engine,
            credit_cost_per_page=credit_cost_per_page,
            table_count=table_count,
            confidence=confidence
        )
    
    # RULE 2: Text PDFs → Word (Free or Premium)
    if has_text:
        suggested_tool = "word"
        requires_premium = False  # Can use free tier for text PDFs
        reason = "Text-based PDF. Word conversion recommended."
        engine = "libreoffice"
        from app.credit_manager import CREDITS_PER_PAGE_TEXT
        credit_cost_per_page = CREDITS_PER_PAGE_TEXT  # 2 credits per page for text (when premium)
        
        logger.info("Routing to Word: Text-based PDF")
        return DocumentAnalysis(
            page_count=page_count,
            file_size_bytes=file_size_bytes,
            has_text=has_text,
            is_scanned=False,
            has_tables=False,
            is_id_card_like=False,
            suggested_tool=suggested_tool,
            requires_premium=requires_premium,
            reason=reason,
            engine=engine,
            credit_cost_per_page=credit_cost_per_page,
            table_count=0,
            confidence=confidence
        )
    
    # RULE 3: Scanned PDFs (no text) → Word with OCR (Premium only)
    if is_scanned:
        suggested_tool = "word"
        requires_premium = True  # OCR requires premium
        reason = "Scanned PDF detected. OCR required (Premium feature)."
        engine = "docai"  # OCR uses Document AI
        from app.credit_manager import CREDITS_PER_PAGE_OCR
        credit_cost_per_page = CREDITS_PER_PAGE_OCR  # 5 credits per page for OCR
        
        logger.info("Routing to Word: Scanned PDF (OCR required)")
        return DocumentAnalysis(
            page_count=page_count,
            file_size_bytes=file_size_bytes,
            has_text=False,
            is_scanned=True,
            has_tables=False,
            is_id_card_like=False,
            suggested_tool=suggested_tool,
            requires_premium=requires_premium,
            reason=reason,
            engine=engine,
            credit_cost_per_page=credit_cost_per_page,
            table_count=0,
            confidence=confidence
        )
    
    # Default fallback (should not reach here)
    suggested_tool = "word"
    requires_premium = False
    reason = "Unable to determine document type. Using default Word conversion."
    engine = "libreoffice"
    credit_cost_per_page = 0.0
    
    logger.warning("Using default routing (should not reach here)")
    return DocumentAnalysis(
        page_count=page_count,
        file_size_bytes=file_size_bytes,
        has_text=has_text,
        is_scanned=is_scanned,
        has_tables=False,
        is_id_card_like=False,
        suggested_tool=suggested_tool,
        requires_premium=requires_premium,
        reason=reason,
        engine=engine,
        credit_cost_per_page=credit_cost_per_page,
        table_count=0,
        confidence=confidence
    )


def check_free_tier_eligibility(
    analysis: DocumentAnalysis,
    is_authenticated: bool
) -> Dict[str, Any]:
    """
    Check if document is eligible for free tier conversion.
    
    Free tier rules:
    - Anonymous users only (logged-in users must use credits)
    - Max 1 page per PDF
    - Max 2MB file size
    - Text/digital PDFs only (no OCR)
    - No tables/ID cards (must use Excel Pro)
    
    Args:
        analysis: DocumentAnalysis result
        is_authenticated: Whether user is logged in
        
    Returns:
        Dict with 'allowed', 'reason', and other eligibility details
    """
    if is_authenticated:
        return {
            'allowed': False,
            'reason': 'Logged-in users must use credits. Sign out to use free tier.',
            'requires_premium': True
        }
    
    # Free tier: Max 1 page
    from app.daily_usage import FREE_TIER_MAX_PAGES
    if analysis.page_count > FREE_TIER_MAX_PAGES:
        return {
            'allowed': False,
            'reason': f'Free tier limit: Maximum 1 page per PDF. Your document has {analysis.page_count} pages. Please upgrade to Premium for multi-page conversion.',
            'requires_premium': True,
            'exceeds_pages': True
        }
    
    # Free tier: Max 2MB
    from app.daily_usage import FREE_TIER_MAX_FILE_SIZE_MB
    max_size_mb = FREE_TIER_MAX_FILE_SIZE_MB
    file_size_mb = analysis.file_size_bytes / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return {
            'allowed': False,
            'reason': f'Free tier limit: Maximum {max_size_mb}MB file size. Your file is {file_size_mb:.2f}MB. Please upgrade to Premium for larger files (up to 100MB).',
            'requires_premium': True,
            'exceeds_size': True
        }
    
    # Free tier: Allow LibreOffice to try first for all PDFs
    # Don't reject based on is_scanned - let LibreOffice attempt conversion first
    # Many digital PDFs (like invoices) might have minimal extractable text but LibreOffice can still convert them
    # If LibreOffice fails, the conversion function will handle the error appropriately
    # This allows digital PDFs that pdfminer can't extract text from to still work
    # We only reject if the PDF truly requires OCR AND LibreOffice fails (handled in conversion)
    pass  # Allow all PDFs to attempt LibreOffice conversion
    
    # Free tier: No tables/ID cards (must use Excel)
    if analysis.has_tables or analysis.is_id_card_like:
        return {
            'allowed': False,
            'reason': 'This document contains tables or structured data. Please use PDF to Excel (Pro) for accurate conversion.',
            'requires_premium': True,
            'requires_excel': True,
            'suggested_tool': 'excel'
        }
    
    # Eligible for free tier
    return {
        'allowed': True,
        'reason': 'Eligible for free tier conversion.',
        'requires_premium': False
    }


# Premium tier limits
PREMIUM_MAX_PAGES = 100  # Maximum 100 pages per PDF for premium tier
PREMIUM_MAX_FILE_SIZE_MB = 100  # Maximum 100MB file size for premium tier

def check_premium_requirements(
    analysis: DocumentAnalysis,
    user_credits: float
) -> Dict[str, Any]:
    """
    Check if user meets premium requirements for conversion.
    
    Premium requirements:
    - Login required
    - Credits >= 30 (minimum threshold)
    - Sufficient credits for conversion
    - Max 100 pages per PDF
    - Max 100MB file size
    
    Args:
        analysis: DocumentAnalysis result
        user_credits: User's available credits
        
    Returns:
        Dict with 'eligible', 'reason', and requirement details
    """
    # Minimum credit threshold for premium
    MIN_CREDITS_THRESHOLD = 30.0
    
    if user_credits < MIN_CREDITS_THRESHOLD:
        return {
            'eligible': False,
            'reason': f'Premium requires minimum {MIN_CREDITS_THRESHOLD} credits. You have {user_credits:.1f} credits.',
            'required_minimum': MIN_CREDITS_THRESHOLD,
            'current_credits': user_credits
        }
    
    # Premium: Max 100 pages per PDF
    if analysis.page_count > PREMIUM_MAX_PAGES:
        return {
            'eligible': False,
            'reason': f'Premium limit: Maximum {PREMIUM_MAX_PAGES} pages per PDF. Your document has {analysis.page_count} pages.',
            'exceeds_pages': True,
            'max_pages': PREMIUM_MAX_PAGES
        }
    
    # Premium: Max 100MB file size
    file_size_mb = analysis.file_size_bytes / (1024 * 1024)
    if file_size_mb > PREMIUM_MAX_FILE_SIZE_MB:
        return {
            'eligible': False,
            'reason': f'Premium limit: Maximum {PREMIUM_MAX_FILE_SIZE_MB}MB file size. Your file is {file_size_mb:.2f}MB.',
            'exceeds_size': True,
            'max_size_mb': PREMIUM_MAX_FILE_SIZE_MB
        }
    
    # Calculate required credits for this conversion
    required_credits = analysis.page_count * analysis.credit_cost_per_page
    
    if user_credits < required_credits:
        return {
            'eligible': False,
            'reason': f'Insufficient credits. Required: {required_credits:.1f}, Available: {user_credits:.1f}',
            'required': required_credits,
            'available': user_credits
        }
    
    return {
        'eligible': True,
        'reason': 'Premium requirements met.',
        'required': required_credits,
        'available': user_credits,
        'remaining': user_credits - required_credits
    }

