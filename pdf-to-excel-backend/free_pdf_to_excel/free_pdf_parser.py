"""
PDF Parser for FREE version.
Extracts text with coordinates, preserving Unicode exactly.
NO OCR, CPU-only processing.
"""

import io
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfReader
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer, LTChar, LTTextLine
    HAS_PDF_LIBS = True
except ImportError as e:
    HAS_PDF_LIBS = False
    logger.warning(f"PDF libraries not available: {e}")


def extract_text_with_coordinates(pdf_bytes: bytes, page_num: int = 0) -> List[Dict]:
    """
    Extract text with coordinates from a specific PDF page.
    Preserves Unicode exactly (no normalization).
    
    Args:
        pdf_bytes: PDF file content
        page_num: Page index (0-based, only first page for FREE)
        
    Returns:
        List of text objects with:
        - text: Unicode text (preserved exactly)
        - x, y: Position coordinates
        - width, height: Bounding box dimensions
        - font_name: Font name
        - font_size: Font size
        - is_bold: Bold flag
        - page: Page number
    """
    if not HAS_PDF_LIBS:
        return []
    
    text_objects = []
    
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        
        for page_idx, page_layout in enumerate(extract_pages(pdf_file)):
            if page_idx != page_num:
                continue  # Only process first page for FREE
            
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    # Extract text (preserve Unicode exactly)
                    text = element.get_text()
                    if not text or not text.strip():
                        continue
                    
                    # Get bounding box (with safety check)
                    try:
                        if not hasattr(element, 'bbox'):
                            continue
                        x0, y0, x1, y1 = element.bbox
                        width = x1 - x0
                        height = y1 - y0
                    except (AttributeError, ValueError, TypeError):
                        continue
                    
                    # Extract font information
                    font_name = "Arial"
                    font_size = 10
                    is_bold = False
                    
                    # Try to get font from first character
                    for text_line in element:
                        if isinstance(text_line, LTTextLine):
                            for char in text_line:
                                if isinstance(char, LTChar):
                                    font_name = char.fontname or "Arial"
                                    font_size = char.size or 10
                                    # Check for bold
                                    if 'bold' in font_name.lower() or 'Bold' in font_name:
                                        is_bold = True
                                    break
                            if font_name != "Arial":
                                break
                    
                    text_objects.append({
                        'text': text.strip(),  # Preserve Unicode exactly
                        'x': float(x0),
                        'y': float(y0),
                        'width': float(width),
                        'height': float(height),
                        'font_name': font_name,
                        'font_size': float(font_size),
                        'is_bold': is_bold,
                        'page': page_idx
                    })
            
            break  # Only process first page
    
    except Exception as e:
        logger.error(f"Error extracting text from page {page_num}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return text_objects


def detect_scanned_pdf(pdf_bytes: bytes) -> Tuple[bool, float]:
    """
    Detect if PDF is scanned/image-only.
    
    Args:
        pdf_bytes: PDF file content
        
    Returns:
        (is_scanned, text_density_ratio)
    """
    if not HAS_PDF_LIBS:
        return True, 0.0
    
    try:
        # Extract text from first page
        text_objects = extract_text_with_coordinates(pdf_bytes, page_num=0)
        
        if not text_objects:
            return True, 0.0  # No text = scanned
        
        # Calculate text density
        total_text_length = sum(len(obj['text']) for obj in text_objects)
        
        # Get page dimensions
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        if reader.pages:
            page = reader.pages[0]
            if hasattr(page, 'mediabox'):
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)
                page_area = page_width * page_height
                
                # Text density: characters per square point
                text_density = total_text_length / max(page_area, 1)
                
                # If density is very low (< 0.01 chars/point²), likely scanned
                # But be more lenient - only mark as scanned if density is extremely low
                # Digital PDFs with sparse text should not be marked as scanned
                # Even more lenient: only mark as scanned if density is extremely low AND we have very few text objects
                is_scanned = text_density < 0.001 and len(text_objects) < 5  # Very strict: only if almost no text AND very few objects
                logger.info(f"PDF scan detection: density={text_density:.6f}, objects={len(text_objects)}, is_scanned={is_scanned}")
                return is_scanned, text_density, len(text_objects)
        
        # If we can't determine, assume not scanned if we have text
        return False, 0.1, len(text_objects) if text_objects else 0
    
    except Exception as e:
        logger.error(f"Error detecting scanned PDF: {e}")
        return False, 0.1, 0  # Assume not scanned on error


def get_page_count(pdf_bytes: bytes) -> int:
    """
    Get total page count from PDF.
    
    Args:
        pdf_bytes: PDF file content
        
    Returns:
        Number of pages
    """
    if not HAS_PDF_LIBS:
        return 0
    
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        return len(reader.pages)
    except Exception as e:
        logger.error(f"Error getting page count: {e}")
        return 0

