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


def _extract_images_with_pypdf2(pdf_bytes: bytes, page_num: int = 0, max_size_bytes: int = 200 * 1024) -> List[Dict]:
    """
    Extract images using PyPDF2 (PRIMARY METHOD).
    This is more reliable for image extraction.
    
    Returns same format as extract_small_images().
    """
    images = []
    
    try:
        from PyPDF2 import PdfReader
        
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        
        if page_num >= len(pdf_reader.pages):
            return []
        
        page = pdf_reader.pages[page_num]
        
        # Get page dimensions
        page_width = 612  # Default
        page_height = 792  # Default
        if hasattr(page, 'mediabox'):
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
        
        # Extract images from page - PyPDF2 v3.0+ uses different API
        try:
            # Method 1: Try page.images (PyPDF2 v3.0+)
            if hasattr(page, 'images') and page.images:
                for img_name, img_obj in page.images.items():
                    try:
                        # Get image data
                        image_data = None
                        if hasattr(img_obj, 'get_data'):
                            image_data = img_obj.get_data()
                        elif hasattr(img_obj, 'data'):
                            image_data = img_obj.data
                        elif hasattr(img_obj, 'get_object'):
                            # Try to get raw object
                            img_raw = img_obj.get_object()
                            if hasattr(img_raw, 'get_data'):
                                image_data = img_raw.get_data()
                            elif hasattr(img_raw, 'get_data'):
                                image_data = img_raw.get_data()
                        
                        if not image_data or len(image_data) == 0:
                            continue
                        
                        size_bytes = len(image_data)
                        
                        # Skip if too large
                        if size_bytes > max_size_bytes:
                            logger.info(f"Skipping large image: {size_bytes} bytes")
                            continue
                        
                        # Detect image format
                        image_format = None
                        if len(image_data) >= 8 and image_data[:8] == b'\x89PNG\r\n\x1a\n':
                            image_format = 'png'
                        elif len(image_data) >= 2 and image_data[:2] == b'\xff\xd8':
                            image_format = 'jpeg'
                        elif len(image_data) >= 6 and image_data[:6] in [b'GIF87a', b'GIF89a']:
                            image_format = 'gif'
                        else:
                            # Try to detect from image object name
                            if 'png' in img_name.lower() or 'image/png' in img_name.lower():
                                image_format = 'png'
                            elif 'jpeg' in img_name.lower() or 'jpg' in img_name.lower() or 'image/jpeg' in img_name.lower():
                                image_format = 'jpeg'
                            elif 'gif' in img_name.lower():
                                image_format = 'gif'
                        
                        if not image_format:
                            image_format = 'png'  # Default
                        
                        # Get image dimensions
                        width = 100  # Default
                        height = 100  # Default
                        
                        if hasattr(img_obj, 'width') and hasattr(img_obj, 'height'):
                            width = float(img_obj.width) if img_obj.width else 100
                            height = float(img_obj.height) if img_obj.height else 100
                        elif hasattr(img_obj, 'get_object'):
                            img_raw = img_obj.get_object()
                            if hasattr(img_raw, 'width') and hasattr(img_raw, 'height'):
                                width = float(img_raw.width) if img_raw.width else 100
                                height = float(img_raw.height) if img_raw.height else 100
                        
                        # Estimate position (PyPDF2 doesn't provide exact coordinates)
                        x0 = 50.0  # Default left margin
                        y0 = page_height - height - 50.0  # Default top margin
                        x1 = x0 + width
                        y1 = y0 + height
                        
                        # Check if full-page or too small
                        is_full_page = (width > page_width * 0.9 and height > page_height * 0.9)
                        is_too_small = width < 30 or height < 30
                        
                        if not is_full_page and not is_too_small:
                            images.append({
                                'x0': float(x0),
                                'y0': float(y0),
                                'x1': float(x1),
                                'y1': float(y1),
                                'width': float(width),
                                'height': float(height),
                                'size_bytes': size_bytes,
                                'image_data': image_data,
                                'image_format': image_format,
                                'page': page_num
                            })
                            logger.info(f"✅ PyPDF2 extracted image '{img_name}': {size_bytes} bytes, format: {image_format}, size: {width}x{height}")
                    
                    except Exception as img_e:
                        logger.warning(f"Error extracting image '{img_name}' with PyPDF2: {img_e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                        continue
        except Exception as e:
            logger.warning(f"PyPDF2 page.images access failed: {e}")
        
    except Exception as e:
        logger.warning(f"PyPDF2 image extraction failed: {e}")
        return []
    
    return images


def extract_small_images(pdf_bytes: bytes, page_num: int = 0, max_size_kb: int = 200) -> List[Dict]:
    """
    Extract small images (<200 KB, first page only).
    Uses PyPDF2 as PRIMARY method, pdfminer as FALLBACK.
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
        - image_data: Raw image bytes (PNG/JPEG)
        - image_format: Image format ('png', 'jpeg', etc.)
        - page: Page number
    """
    if not HAS_PDF_LIBS:
        return []
    
    images = []
    max_size_bytes = max_size_kb * 1024
    
    # METHOD 1: Try PyPDF2 first (more reliable for images)
    try:
        pypdf2_images = _extract_images_with_pypdf2(pdf_bytes, page_num, max_size_bytes)
        if pypdf2_images:
            logger.info(f"✅ PyPDF2 extracted {len(pypdf2_images)} images successfully")
            return pypdf2_images
        else:
            logger.info("PyPDF2 found no images, trying pdfminer fallback...")
    except Exception as pypdf2_e:
        logger.warning(f"PyPDF2 extraction failed, using pdfminer fallback: {pypdf2_e}")
    
    # METHOD 2: Fallback to pdfminer (original method)
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
            if pdf_reader.pages and page_idx < len(pdf_reader.pages):
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
                        
                        # Get image data and size
                        size_bytes = 0
                        image_data = None
                        image_format = None
                        
                        # Try LTImage first (direct image)
                        if isinstance(element, LTImage):
                            # Try to get image data
                            try:
                                if hasattr(element, 'stream') and hasattr(element.stream, 'get_data'):
                                    image_data = element.stream.get_data()
                                    size_bytes = len(image_data) if image_data else 0
                                    logger.info(f"Extracted LTImage (pdfminer): {size_bytes} bytes at ({x0}, {y0})")
                                    
                                    # Detect image format from stream
                                    if hasattr(element, 'name'):
                                        name_lower = element.name.lower()
                                        if 'png' in name_lower or 'image/png' in name_lower:
                                            image_format = 'png'
                                        elif 'jpeg' in name_lower or 'jpg' in name_lower or 'image/jpeg' in name_lower:
                                            image_format = 'jpeg'
                                        elif 'gif' in name_lower:
                                            image_format = 'gif'
                                    
                                    # Try to detect format from data signature
                                    if not image_format and image_data:
                                        if len(image_data) >= 8 and image_data[:8] == b'\x89PNG\r\n\x1a\n':
                                            image_format = 'png'
                                        elif len(image_data) >= 2 and image_data[:2] == b'\xff\xd8':
                                            image_format = 'jpeg'
                                        elif len(image_data) >= 6 and image_data[:6] in [b'GIF87a', b'GIF89a']:
                                            image_format = 'gif'
                                    
                                    # Default to PNG if format unknown but data exists
                                    if image_data and not image_format:
                                        image_format = 'png'
                                        
                            except (AttributeError, TypeError) as e:
                                logger.warning(f"Could not extract LTImage data: {e}")
                                size_bytes = 0
                                image_data = None
                        
                        # Try LTFigure (may contain images)
                        elif isinstance(element, LTFigure):
                            try:
                                # LTFigure might contain nested LTImage
                                if hasattr(element, 'stream') and hasattr(element.stream, 'get_data'):
                                    image_data = element.stream.get_data()
                                    size_bytes = len(image_data) if image_data else 0
                                    logger.info(f"Extracted LTFigure image (pdfminer): {size_bytes} bytes at ({x0}, {y0})")
                                    
                                    # Detect format from data
                                    if image_data:
                                        if len(image_data) >= 8 and image_data[:8] == b'\x89PNG\r\n\x1a\n':
                                            image_format = 'png'
                                        elif len(image_data) >= 2 and image_data[:2] == b'\xff\xd8':
                                            image_format = 'jpeg'
                                        elif len(image_data) >= 6 and image_data[:6] in [b'GIF87a', b'GIF89a']:
                                            image_format = 'gif'
                                        else:
                                            image_format = 'png'  # Default
                                            
                            except (AttributeError, TypeError) as e:
                                logger.warning(f"Could not extract LTFigure image data: {e}")
                                # Try to iterate through LTFigure children
                                try:
                                    if hasattr(element, '__iter__'):
                                        for child in element:
                                            if isinstance(child, LTImage):
                                                if hasattr(child, 'stream') and hasattr(child.stream, 'get_data'):
                                                    image_data = child.stream.get_data()
                                                    size_bytes = len(image_data) if image_data else 0
                                                    logger.info(f"Extracted nested LTImage from LTFigure (pdfminer): {size_bytes} bytes")
                                                    if image_data:
                                                        if len(image_data) >= 8 and image_data[:8] == b'\x89PNG\r\n\x1a\n':
                                                            image_format = 'png'
                                                        elif len(image_data) >= 2 and image_data[:2] == b'\xff\xd8':
                                                            image_format = 'jpeg'
                                                        else:
                                                            image_format = 'png'
                                                    break
                                except Exception as nested_e:
                                    logger.warning(f"Could not extract nested image from LTFigure: {nested_e}")
                                size_bytes = 0 if not image_data else size_bytes
                        
                        # Filter criteria:
                        # 1. Size must be < max_size_bytes
                        # 2. Not full-page (must be < 90% of page size)
                        # 3. Not too small (must be > 50x50 points)
                        # 4. Must have image data
                        is_full_page = (width > page_width * 0.9 and height > page_height * 0.9)
                        is_too_small = width < 50 or height < 50
                        
                        if (size_bytes == 0 or size_bytes < max_size_bytes) and not is_full_page and not is_too_small and image_data:
                            images.append({
                                'x0': float(x0),
                                'y0': float(y0),
                                'x1': float(x1),
                                'y1': float(y1),
                                'width': float(width),
                                'height': float(height),
                                'size_bytes': size_bytes,
                                'image_data': image_data,
                                'image_format': image_format or 'png',
                                'page': page_idx
                            })
                    except Exception as e:
                        logger.warning(f"Error processing image element: {e}")
                        continue
            
            break  # Only process first page
    
    except Exception as e:
        logger.error(f"Error extracting images from page {page_num}: {e}")
    
    return images

