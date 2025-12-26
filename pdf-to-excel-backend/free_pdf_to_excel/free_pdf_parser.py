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
                    
                    # IMPROVED: Handle multi-line text - split by lines if height is too large
                    # If text height is more than 2x average line height, it might be multi-line
                    # Extract individual text lines for better cell assignment
                    text_lines = []
                    if isinstance(element, LTTextContainer):
                        for text_line in element:
                            if isinstance(text_line, LTTextLine):
                                line_text = text_line.get_text().strip()
                                if line_text:
                                    try:
                                        line_bbox = text_line.bbox
                                        line_x0, line_y0, line_x1, line_y1 = line_bbox
                                        line_width = line_x1 - line_x0
                                        line_height = line_y1 - line_y0
                                        text_lines.append({
                                            'text': line_text,
                                            'x': float(line_x0),
                                            'y': float(line_y0),
                                            'width': float(line_width),
                                            'height': float(line_height)
                                        })
                                    except:
                                        # Fallback to container bbox
                                        text_lines.append({
                                            'text': line_text,
                                            'x': float(x0),
                                            'y': float(y0),
                                            'width': float(width),
                                            'height': float(height)
                                        })
                    
                    # If we extracted individual lines, use them; otherwise use container
                    if len(text_lines) > 1:
                        # Multi-line text - process each line separately
                        line_idx = 0
                        for text_line_obj in element:
                            if isinstance(text_line_obj, LTTextLine) and line_idx < len(text_lines):
                                line_data = text_lines[line_idx]
                                
                                # Extract font for this specific line
                                font_name = "Arial"
                                font_size = 10
                                is_bold = False
                                fonts_found = []
                                
                                # Get font from this line's characters
                                for char in text_line_obj:
                                    if isinstance(char, LTChar):
                                        char_font = char.fontname or "Arial"
                                        char_size = char.size or 10
                                        char_bold = 'bold' in char_font.lower() or 'Bold' in char_font
                                        fonts_found.append({
                                            'font_name': char_font,
                                            'font_size': char_size,
                                            'is_bold': char_bold
                                        })
                                
                                if fonts_found:
                                    font_counts = {}
                                    for f in fonts_found:
                                        key = (f['font_name'], f['font_size'], f['is_bold'])
                                        font_counts[key] = font_counts.get(key, 0) + 1
                                    most_common = max(font_counts.items(), key=lambda x: x[1])
                                    font_name = most_common[0][0]
                                    font_size = most_common[0][1]
                                    is_bold = most_common[0][2]
                                
                                text_objects.append({
                                    'text': line_data['text'],
                                    'x': line_data['x'],
                                    'y': line_data['y'],
                                    'width': line_data['width'],
                                    'height': line_data['height'],
                                    'font_name': font_name,
                                    'font_size': float(font_size),
                                    'is_bold': is_bold,
                                    'page': page_idx,
                                    'fonts_detail': fonts_found
                                })
                                line_idx += 1
                        continue  # Skip container-level processing for multi-line
                    
                    # Extract font information - IMPROVED: Get font from all characters
                    font_name = "Arial"
                    font_size = 10
                    is_bold = False
                    
                    # Collect fonts from all characters (not just first)
                    fonts_found = []
                    for text_line in element:
                        if isinstance(text_line, LTTextLine):
                            for char in text_line:
                                if isinstance(char, LTChar):
                                    char_font = char.fontname or "Arial"
                                    char_size = char.size or 10
                                    char_bold = 'bold' in char_font.lower() or 'Bold' in char_font
                                    fonts_found.append({
                                        'font_name': char_font,
                                        'font_size': char_size,
                                        'is_bold': char_bold
                                    })
                    
                    # Use most common font (or first if all same)
                    if fonts_found:
                        # Count font occurrences
                        font_counts = {}
                        for f in fonts_found:
                            key = (f['font_name'], f['font_size'], f['is_bold'])
                            font_counts[key] = font_counts.get(key, 0) + 1
                        
                        # Get most common font
                        most_common = max(font_counts.items(), key=lambda x: x[1])
                        font_name = most_common[0][0]
                        font_size = most_common[0][1]
                        is_bold = most_common[0][2]
                    else:
                        # Fallback to defaults
                        font_name = "Arial"
                        font_size = 10
                        is_bold = False
                    
                    text_objects.append({
                        'text': text.strip(),  # Preserve Unicode exactly
                        'x': float(x0),
                        'y': float(y0),
                        'width': float(width),
                        'height': float(height),
                        'font_name': font_name,
                        'font_size': float(font_size),
                        'is_bold': is_bold,
                        'page': page_idx,
                        'fonts_detail': fonts_found  # Store detailed font info for rich text if needed
                    })
            
            break  # Only process first page
    
    except Exception as e:
        logger.error(f"Error extracting text from page {page_num}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return text_objects


def detect_scanned_pdf(pdf_bytes: bytes) -> Tuple[bool, float, int]:
    """
    Detect if PDF is scanned/image-only.
    
    Args:
        pdf_bytes: PDF file content
        
    Returns:
        (is_scanned, text_density_ratio, text_object_count)
    """
    if not HAS_PDF_LIBS:
        return True, 0.0, 0
    
    try:
        # Extract text from first page
        text_objects = extract_text_with_coordinates(pdf_bytes, page_num=0)
        
        if not text_objects:
            return True, 0.0, 0  # No text = scanned
        
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

