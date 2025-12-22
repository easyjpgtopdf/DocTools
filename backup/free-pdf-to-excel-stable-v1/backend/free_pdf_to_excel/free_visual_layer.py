"""
Visual Layer Extraction for FREE version.
Extracts lines, rectangles, and small images from PDF.
CPU-only, NO OCR.
"""

import io
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTLine, LTRect, LTFigure, LTImage
    HAS_PDF_LIBS = True
except ImportError as e:
    HAS_PDF_LIBS = False
    logger.warning(f"PDF libraries not available: {e}")


def extract_lines(pdf_bytes: bytes, page_num: int = 0) -> List[Dict]:
    """
    Extract straight horizontal and vertical lines.
    
    Args:
        pdf_bytes: PDF file content
        page_num: Page index (0-based, only first page for FREE)
        
    Returns:
        List of line objects with:
        - x0, y0, x1, y1: Line coordinates
        - is_horizontal: True if horizontal line
        - is_vertical: True if vertical line
        - page: Page number
    """
    if not HAS_PDF_LIBS:
        return []
    
    lines = []
    
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        
        for page_idx, page_layout in enumerate(extract_pages(pdf_file)):
            if page_idx != page_num:
                continue
            
            for element in page_layout:
                if isinstance(element, LTLine):
                    try:
                        if not hasattr(element, 'bbox'):
                            continue
                        x0, y0, x1, y1 = element.bbox
                        
                        # Determine if horizontal or vertical
                        width = abs(x1 - x0)
                        height = abs(y1 - y0)
                        is_horizontal = height < width * 0.1  # Height is much smaller than width
                        is_vertical = width < height * 0.1    # Width is much smaller than height
                        
                        # Only include straight lines (horizontal or vertical)
                        if is_horizontal or is_vertical:
                            lines.append({
                                'x0': float(x0),
                                'y0': float(y0),
                                'x1': float(x1),
                                'y1': float(y1),
                                'is_horizontal': is_horizontal,
                                'is_vertical': is_vertical,
                                'page': page_idx
                            })
                    except (AttributeError, ValueError, TypeError):
                        continue
            
            break  # Only process first page
    
    except Exception as e:
        logger.error(f"Error extracting lines from page {page_num}: {e}")
    
    return lines


def extract_rectangles(pdf_bytes: bytes, page_num: int = 0) -> List[Dict]:
    """
    Extract filled rectangles (solid fills only).
    Ignores gradients and decorative shapes.
    
    Args:
        pdf_bytes: PDF file content
        page_num: Page index (0-based, only first page for FREE)
        
    Returns:
        List of rectangle objects with:
        - x0, y0, x1, y1: Rectangle coordinates
        - width, height: Dimensions
        - page: Page number
    """
    if not HAS_PDF_LIBS:
        return []
    
    rectangles = []
    
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        
        for page_idx, page_layout in enumerate(extract_pages(pdf_file)):
            if page_idx != page_num:
                continue
            
            for element in page_layout:
                if isinstance(element, LTRect):
                    try:
                        if not hasattr(element, 'bbox'):
                            continue
                        x0, y0, x1, y1 = element.bbox
                        width = abs(x1 - x0)
                        height = abs(y1 - y0)
                        
                        # Only include substantial rectangles (not tiny decorative elements)
                        if width > 10 and height > 10:
                            rectangles.append({
                                'x0': float(x0),
                                'y0': float(y0),
                                'x1': float(x1),
                                'y1': float(y1),
                                'width': float(width),
                                'height': float(height),
                                'page': page_idx
                            })
                    except (AttributeError, ValueError, TypeError):
                        continue
            
            break  # Only process first page
    
    except Exception as e:
        logger.error(f"Error extracting rectangles from page {page_num}: {e}")
    
    return rectangles


def extract_small_images(pdf_bytes: bytes, page_num: int = 0, max_size_kb: int = 200) -> List[Dict]:
    """
    Extract small images (<200 KB, first page only).
    Ignores background and full-page images.
    
    Args:
        pdf_bytes: PDF file content
        page_num: Page index (0-based, only first page for FREE)
        max_size_kb: Maximum image size in KB
        
    Returns:
        List of image objects with:
        - x0, y0, x1, y1: Image coordinates
        - width, height: Dimensions
        - size_bytes: Image size in bytes
        - page: Page number
    """
    if not HAS_PDF_LIBS:
        return []
    
    images = []
    max_size_bytes = max_size_kb * 1024
    
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        
        for page_idx, page_layout in enumerate(extract_pages(pdf_file)):
            if page_idx != page_num:
                continue
            
            # Get page dimensions to detect full-page images
            from PyPDF2 import PdfReader
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            page_width = 612  # Default
            page_height = 792  # Default
            if pdf_reader.pages:
                page_obj = pdf_reader.pages[page_idx]
                if hasattr(page_obj, 'mediabox'):
                    page_width = float(page_obj.mediabox.width)
                    page_height = float(page_obj.mediabox.height)
            
            for element in page_layout:
                if isinstance(element, (LTImage, LTFigure)):
                    try:
                        if not hasattr(element, 'bbox'):
                            continue
                        x0, y0, x1, y1 = element.bbox
                        width = abs(x1 - x0)
                        height = abs(y1 - y0)
                        
                        # Get image size
                        size_bytes = 0
                        if isinstance(element, LTImage):
                            # Try to get image data size
                            try:
                                if hasattr(element, 'stream') and hasattr(element.stream, 'get_data'):
                                    size_bytes = len(element.stream.get_data())
                            except (AttributeError, TypeError):
                                size_bytes = 0
                        
                        # Filter criteria:
                        # 1. Size must be < max_size_bytes
                        # 2. Not full-page (must be < 90% of page size)
                        # 3. Not too small (must be > 50x50 points)
                        is_full_page = (width > page_width * 0.9 and height > page_height * 0.9)
                        is_too_small = width < 50 or height < 50
                        
                        if (size_bytes == 0 or size_bytes < max_size_bytes) and not is_full_page and not is_too_small:
                            images.append({
                                'x0': float(x0),
                                'y0': float(y0),
                                'x1': float(x1),
                                'y1': float(y1),
                                'width': float(width),
                                'height': float(height),
                                'size_bytes': size_bytes,
                                'page': page_idx
                            })
                    except Exception as e:
                        logger.warning(f"Error processing image element: {e}")
                        continue
            
            break  # Only process first page
    
    except Exception as e:
        logger.error(f"Error extracting images from page {page_num}: {e}")
    
    return images

