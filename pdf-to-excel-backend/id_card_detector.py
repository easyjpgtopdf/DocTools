"""
ID Card Detection Module
Detects if a PDF document is an ID card based on multiple signals
"""

import logging
from typing import Dict, Optional, List
import re
from io import BytesIO

logger = logging.getLogger(__name__)

# Keywords commonly found in ID cards
ID_CARD_KEYWORDS = [
    'name', 'dob', 'date of birth', 'id no', 'aadhaar', 'pan',
    'passport', 'license', 'uid', 'gender', 'nationality',
    'address', 'father', 'mother', 'issued', 'valid', 'expiry',
    'photo', 'signature', 'issuing authority', 'document number'
]


def detect_id_card(
    file_bytes: bytes,
    pdf_metadata: Optional[Dict] = None,
    text_blocks: Optional[List[Dict]] = None
) -> Dict:
    """
    Detect if a PDF is an ID card based on multiple signals.
    
    Detection Logic (Combination of Signals):
    A) PAGE & IMAGE SIGNAL:
       - page_count <= 2
       - image_area_ratio > 60% (estimated)
       - table_count == 0
    
    B) KEYWORD SIGNAL:
       - Check for ID-related keywords in text
       - keyword_hits >= 2
    
    C) LAYOUT SIGNAL:
       - No repeating row/column alignment (not grid-like)
       - Text blocks scattered (not table-like)
    
    FINAL DECISION:
    If (A + B) OR (A + C) true:
        document_type = "ID_CARD"
    else:
        document_type = "NORMAL_PDF"
    
    Args:
        file_bytes: PDF file bytes
        pdf_metadata: Optional dict with metadata like page_count, etc.
        text_blocks: Optional list of text blocks with coordinates
    
    Returns:
        Dict with:
        {
            "document_type": "ID_CARD" | "NORMAL_PDF",
            "confidence": 0-100,
            "signals": {
                "page_signal": bool,
                "keyword_signal": bool,
                "layout_signal": bool
            }
        }
    """
    try:
        # Initialize signals
        signals = {
            "page_signal": False,
            "keyword_signal": False,
            "layout_signal": False
        }
        
        # Get page count from metadata or estimate from file
        page_count = pdf_metadata.get('page_count', 0) if pdf_metadata else 0
        if page_count == 0:
            # Try to estimate page count from file size (rough estimate)
            # Average PDF page is ~50-100KB, but this is just a fallback
            page_count = max(1, len(file_bytes) // 70000)  # Rough estimate
        
        # Extract text for keyword analysis
        text_content = ""
        if text_blocks:
            # Extract text from text blocks
            text_content = " ".join([block.get('text', '') for block in text_blocks])
        else:
            # Try to extract text from PDF (basic extraction)
            # This is a fallback - ideally text_blocks should be provided
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                text_content = ""
                for page in pdf_reader.pages[:min(2, len(pdf_reader.pages))]:  # Check first 2 pages
                    text_content += page.extract_text() + " "
                page_count = len(pdf_reader.pages)
            except Exception as e:
                logger.warning(f"Could not extract text for ID detection: {e}")
                text_content = ""
        
        text_content_lower = text_content.lower()
        
        # SIGNAL A: Page & Image Signal
        # Check if page count <= 2 and estimate if it's image-heavy
        has_few_pages = page_count <= 2
        # If we can't get image ratio from metadata, we'll infer from text density
        # Low text density + few pages = likely image-heavy document
        text_density = len(text_content.strip()) / max(page_count, 1)
        is_image_heavy = text_density < 500  # Less than 500 chars per page suggests image-heavy
        
        # Estimate table count (if not provided in metadata)
        table_count = pdf_metadata.get('table_count', 0) if pdf_metadata else 0
        
        signals["page_signal"] = has_few_pages and is_image_heavy and table_count == 0
        
        # SIGNAL B: Keyword Signal
        keyword_hits = 0
        for keyword in ID_CARD_KEYWORDS:
            if keyword in text_content_lower:
                keyword_hits += 1
        
        signals["keyword_signal"] = keyword_hits >= 2
        
        # SIGNAL C: Layout Signal (simplified)
        # Check if text blocks are scattered (not in a table grid pattern)
        # If we have text blocks, check for grid-like alignment
        is_grid_like = False
        if text_blocks and len(text_blocks) > 5:
            # Simple check: if many text blocks have similar x or y coordinates,
            # it's likely a table/grid
            x_coords = [block.get('x', 0) for block in text_blocks if 'x' in block]
            y_coords = [block.get('y', 0) for block in text_blocks if 'y' in block]
            
            if len(x_coords) > 3 and len(y_coords) > 3:
                # Check if there are repeating x coordinates (columns)
                from collections import Counter
                x_freq = Counter([round(x, -1) for x in x_coords])  # Round to nearest 10
                y_freq = Counter([round(y, -1) for y in y_coords])  # Round to nearest 10
                
                # If many coordinates align, it's grid-like
                max_x_freq = max(x_freq.values()) if x_freq else 0
                max_y_freq = max(y_freq.values()) if y_freq else 0
                is_grid_like = max_x_freq > 3 or max_y_freq > 3
        
        # Layout signal: not grid-like + few pages + low text density
        signals["layout_signal"] = not is_grid_like and has_few_pages and text_density < 1000
        
        # FINAL DECISION
        # If (A + B) OR (A + C) true: ID_CARD
        condition_ab = signals["page_signal"] and signals["keyword_signal"]
        condition_ac = signals["page_signal"] and signals["layout_signal"]
        
        is_id_card = condition_ab or condition_ac
        
        # Calculate confidence
        confidence = 0
        if signals["page_signal"]:
            confidence += 40
        if signals["keyword_signal"]:
            confidence += 30
        if signals["layout_signal"]:
            confidence += 30
        
        # Boost confidence if multiple signals match
        if condition_ab or condition_ac:
            confidence = min(100, confidence + 10)
        
        document_type = "ID_CARD" if is_id_card else "NORMAL_PDF"
        
        logger.info(f"ID Card Detection: type={document_type}, confidence={confidence}, signals={signals}")
        
        return {
            "document_type": document_type,
            "confidence": confidence,
            "signals": signals,
            "keyword_hits": keyword_hits,
            "page_count": page_count
        }
        
    except Exception as e:
        logger.error(f"Error in ID card detection: {e}")
        # On error, default to NORMAL_PDF (safer)
        return {
            "document_type": "NORMAL_PDF",
            "confidence": 0,
            "signals": {
                "page_signal": False,
                "keyword_signal": False,
                "layout_signal": False
            },
            "error": str(e)
        }

