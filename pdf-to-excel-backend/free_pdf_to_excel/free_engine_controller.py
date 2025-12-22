"""
FREE PDF to Excel Engine Controller.
Main orchestrator for the FREE conversion pipeline.
Completely isolated from Premium/Document AI.
"""

import os
import io
import logging
import tempfile
from typing import Tuple, Optional

from .free_limits import check_limits, record_usage, generate_free_key
from .free_pdf_parser import (
    extract_text_with_coordinates,
    detect_scanned_pdf,
    get_page_count
)
from .free_visual_layer import extract_lines, extract_rectangles, extract_small_images
from .free_table_inference import (
    detect_table_grid,
    snap_text_to_grid,
    detect_header_rows
)
from .free_excel_writer import create_excel_workbook
from .free_response_builder import build_success_response, build_error_response

logger = logging.getLogger(__name__)


def process_pdf_to_excel_free(
    pdf_bytes: bytes,
    filename: str,
    free_key: str,
    ip_address: str
) -> Tuple[Optional[str], int, float, Optional[str]]:
    """
    Process PDF to Excel using FREE engine.
    
    Args:
        pdf_bytes: PDF file content
        filename: Original filename
        free_key: Unique identifier for abuse control
        ip_address: Client IP address
        
    Returns:
        (excel_path, pages_processed, confidence, error_message)
        - excel_path: Path to generated Excel file (None if error)
        - pages_processed: Number of pages processed (0 if error)
        - confidence: Confidence score 0.0-1.0
        - error_message: Error message (None if success)
    """
    try:
        # STEP 1: PDF INTAKE
        file_size = len(pdf_bytes)
        if file_size > 2 * 1024 * 1024:  # 2 MB limit
            return None, 0, 0.0, f"File too large. Maximum 2MB for free version."
        
        # Check limits
        allowed, message, pages_remaining = check_limits(free_key, requested_pages=1)
        if not allowed:
            return None, 0, 0.0, message
        
        # Get page count
        total_pages = get_page_count(pdf_bytes)
        if total_pages == 0:
            return None, 0, 0.0, "PDF has no pages"
        
        # FREE version: only process first page
        pages_to_process = 1
        
        # STEP 2: Detect scanned PDF
        is_scanned, text_density = detect_scanned_pdf(pdf_bytes)
        if is_scanned:
            return None, 0, 0.0, "This PDF appears to be scanned. Upgrade to Pro for OCR-powered conversion."
        
        # STEP 3: TEXT EXTRACTION
        text_objects = extract_text_with_coordinates(pdf_bytes, page_num=0)
        if not text_objects:
            return None, 0, 0.0, "No text found in PDF. This may be a scanned document. Upgrade to Pro for OCR."
        
        # Get page dimensions
        from PyPDF2 import PdfReader
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        page_width = 612  # Default
        page_height = 792  # Default
        if reader.pages:
            page = reader.pages[0]
            if hasattr(page, 'mediabox'):
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)
        
        # STEP 4: VISUAL LAYER EXTRACTION
        lines = extract_lines(pdf_bytes, page_num=0)
        rectangles = extract_rectangles(pdf_bytes, page_num=0)
        images = extract_small_images(pdf_bytes, page_num=0, max_size_kb=200)
        
        # STEP 5: TABLE GRID INFERENCE
        column_boundaries, row_boundaries, grid_confidence = detect_table_grid(
            lines, rectangles, text_objects, page_width, page_height
        )
        
        # If confidence is too low, fail gracefully
        if grid_confidence < 0.2 and not column_boundaries and not row_boundaries:
            return None, 0, 0.0, "Could not detect table structure. This PDF may be too complex. Upgrade to Pro for better accuracy."
        
        # STEP 6: SNAP TEXT TO GRID
        grid = snap_text_to_grid(text_objects, column_boundaries, row_boundaries)
        
        if not grid or not any(any(cell['text'] for cell in row) for row in grid):
            return None, 0, 0.0, "Could not extract table structure. Upgrade to Pro for better accuracy."
        
        # STEP 7: DETECT HEADER ROWS
        header_rows = detect_header_rows(grid, rectangles, row_boundaries)
        
        # STEP 8: CREATE EXCEL
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()
        
        success = create_excel_workbook(
            grid,
            header_rows,
            rectangles,
            images,
            row_boundaries,
            column_boundaries,
            temp_path
        )
        
        if not success:
            return None, 0, 0.0, "Error creating Excel file"
        
        # Record usage
        record_usage(free_key, pages_to_process, file_size)
        
        # Calculate final confidence
        final_confidence = min(grid_confidence + 0.2, 1.0) if grid_confidence > 0 else 0.5
        
        return temp_path, pages_to_process, final_confidence, None
    
    except Exception as e:
        logger.error(f"Error in FREE PDF to Excel processing: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, 0, 0.0, f"Processing error: {str(e)}"

