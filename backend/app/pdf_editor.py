"""
PDF editing and annotation module.
Burns annotations into PDF using PyMuPDF (fitz).
"""
import logging
from typing import List, Dict
import os

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

logger = logging.getLogger(__name__)


def _normalize_color(color: str) -> tuple:
    """
    Convert hex color to RGB tuple (0-1 range for fitz).
    
    Args:
        color: Hex color string (e.g., "#ff0000" or "ff0000")
        
    Returns:
        RGB tuple (r, g, b) with values 0-1
    """
    color = color.lstrip('#')
    if len(color) == 6:
        r = int(color[0:2], 16) / 255.0
        g = int(color[2:4], 16) / 255.0
        b = int(color[4:6], 16) / 255.0
        return (r, g, b)
    return (0, 0, 0)  # Default to black


def apply_annotations_to_pdf(
    pdf_path: str,
    annotations: List[Dict],
    output_path: str,
    canvas_width: float = 800.0,
    canvas_height: float = 600.0
) -> str:
    """
    Apply annotations to PDF and save as new PDF.
    
    Annotations are expected to have coordinates normalized to canvas dimensions.
    This function maps canvas coordinates to PDF page coordinates.
    
    Coordinate System:
    - Frontend canvas: (0,0) at top-left, coordinates in pixels
    - PDF page: (0,0) at bottom-left, coordinates in points (72 points = 1 inch)
    - We assume frontend rendered PDF at a specific scale
    
    Args:
        pdf_path: Path to input PDF file
        annotations: List of annotation dicts with structure:
            {
                "type": "text" | "highlight" | "rect",
                "page": int (1-indexed),
                "x": float (canvas x coordinate),
                "y": float (canvas y coordinate),
                "width": float (for rect/highlight),
                "height": float (for rect/highlight),
                "text": str (for text type),
                "font_size": float (for text),
                "color": str (hex color, e.g., "#ff0000"),
                "border_color": str (for rect)
            }
        output_path: Path to save edited PDF
        canvas_width: Width of canvas used in frontend (for coordinate mapping)
        canvas_height: Height of canvas used in frontend (for coordinate mapping)
        
    Returns:
        Path to saved PDF
        
    Raises:
        ImportError: If PyMuPDF is not installed
        Exception: If annotation application fails
    """
    if not HAS_PYMUPDF:
        raise ImportError("PyMuPDF (fitz) is required for PDF editing. Install with: pip install PyMuPDF")
    
    try:
        logger.info(f"Applying {len(annotations)} annotations to PDF: {pdf_path}")
        
        # Open PDF
        doc = fitz.open(pdf_path)
        
        for annotation in annotations:
            ann_type = annotation.get("type")
            page_num = annotation.get("page", 1) - 1  # Convert to 0-indexed
            
            if page_num < 0 or page_num >= len(doc):
                logger.warning(f"Invalid page number: {page_num + 1}, skipping annotation")
                continue
            
            page = doc[page_num]
            page_rect = page.rect
            
            # Get actual PDF page dimensions
            pdf_width = page_rect.width
            pdf_height = page_rect.height
            
            # Calculate scale factors
            # Frontend canvas might be scaled, we map coordinates proportionally
            scale_x = pdf_width / canvas_width
            scale_y = pdf_height / canvas_height
            
            if ann_type == "text":
                # Text annotation
                x = annotation.get("x", 0) * scale_x
                y = annotation.get("y", 0) * scale_y
                
                # Convert y coordinate (canvas: top-left, PDF: bottom-left)
                y_pdf = pdf_height - y
                
                text = annotation.get("text", "")
                font_size = annotation.get("font_size", 12)
                color_hex = annotation.get("color", "#000000")
                color = _normalize_color(color_hex)
                
                # Insert text
                point = fitz.Point(x, y_pdf)
                page.insert_text(
                    point,
                    text,
                    fontsize=font_size,
                    color=color
                )
                
                logger.debug(f"Added text annotation on page {page_num + 1}: {text[:20]}")
                
            elif ann_type == "highlight":
                # Highlight annotation (semi-transparent rectangle)
                x = annotation.get("x", 0) * scale_x
                y = annotation.get("y", 0) * scale_y
                width = annotation.get("width", 0) * scale_x
                height = annotation.get("height", 0) * scale_y
                
                # Convert y coordinate
                y_pdf = pdf_height - y
                
                # Create rectangle
                rect = fitz.Rect(x, y_pdf - height, x + width, y_pdf)
                
                color_hex = annotation.get("color", "#ffff00")
                color = _normalize_color(color_hex)
                
                # Add highlight annotation
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors(stroke=color)
                highlight.update()
                
                logger.debug(f"Added highlight annotation on page {page_num + 1}")
                
            elif ann_type == "rect":
                # Rectangle annotation (outline)
                x = annotation.get("x", 0) * scale_x
                y = annotation.get("y", 0) * scale_y
                width = annotation.get("width", 0) * scale_x
                height = annotation.get("height", 0) * scale_y
                
                # Convert y coordinate
                y_pdf = pdf_height - y
                
                # Create rectangle
                rect = fitz.Rect(x, y_pdf - height, x + width, y_pdf)
                
                border_color_hex = annotation.get("border_color", "#000000")
                border_color = _normalize_color(border_color_hex)
                
                # Draw rectangle
                page.draw_rect(rect, color=border_color, width=1)
                
                logger.debug(f"Added rectangle annotation on page {page_num + 1}")
            
            else:
                logger.warning(f"Unknown annotation type: {ann_type}, skipping")
        
        # Save edited PDF
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        doc.save(output_path)
        doc.close()
        
        logger.info(f"Annotations applied, saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error applying annotations: {e}")
        raise

