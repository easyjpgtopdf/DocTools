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
try:
    # Try absolute import first
    try:
        from free_heuristic.pre_grid_layout_inference import (
            infer_document_type_from_text,
            infer_pre_grid_from_text,
            should_apply_pre_grid_heuristic
        )
    except ImportError:
        # Fallback: try relative import if absolute fails
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from free_heuristic.pre_grid_layout_inference import (
            infer_document_type_from_text,
            infer_pre_grid_from_text,
            should_apply_pre_grid_heuristic
        )
    PRE_GRID_AVAILABLE = True
except ImportError:
    PRE_GRID_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Pre-grid heuristic module not available - will use standard grid detection")
from .free_excel_writer import create_excel_workbook, create_excel_workbook_multi_page
from .free_response_builder import build_success_response, build_error_response
from .free_libreoffice_converter import convert_with_libreoffice, is_libreoffice_available, LIBREOFFICE_ENABLED

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
        
        # Check limits (5 PDFs per day)
        allowed, message, pdfs_remaining = check_limits(free_key, requested_pdfs=1)
        if not allowed:
            return None, 0, 0.0, message
        
        # Get page count
        total_pages = get_page_count(pdf_bytes)
        if total_pages == 0:
            return None, 0, 0.0, "PDF has no pages"
        
        # STEP 2: Detect scanned PDF (very lenient - only block if absolutely no text)
        is_scanned, text_density, text_object_count = detect_scanned_pdf(pdf_bytes)
        logger.info(f"Scanned PDF detection: is_scanned={is_scanned}, text_density={text_density}, text_objects={text_object_count}")
        if is_scanned:
            # Block scanned PDFs - show upgrade popup instead of blank output
            return None, 0, 0.0, "This file appears to be scanned. Free version does not support OCR. Upgrade to convert this file."
        
        # Get page dimensions helper
        from PyPDF2 import PdfReader
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        
        # STEP 3-8: PROCESS ALL PAGES
        # Collect data for all pages
        all_pages_data = []
        pages_to_process = 0
        
        for page_num in range(total_pages):
            try:
                # Get page dimensions
                page_width = 612  # Default
                page_height = 792  # Default
                if page_num < len(reader.pages):
                    page = reader.pages[page_num]
                    if hasattr(page, 'mediabox'):
                        page_width = float(page.mediabox.width)
                        page_height = float(page.mediabox.height)
                
                # TEXT EXTRACTION
                text_objects = extract_text_with_coordinates(pdf_bytes, page_num=page_num)
                if not text_objects:
                    logger.warning(f"No text found on page {page_num + 1}, skipping...")
                    continue  # Skip pages with no text
                
                # VISUAL LAYER EXTRACTION
                lines = extract_lines(pdf_bytes, page_num=page_num)
                rectangles = extract_rectangles(pdf_bytes, page_num=page_num)
                images = extract_small_images(pdf_bytes, page_num=page_num, max_size_kb=200)
                logger.info(f"Page {page_num + 1}: Extracted {len(images)} images, {len(lines)} lines, {len(rectangles)} rectangles")
                
                # PRE-GRID HEURISTIC LAYER (NEW - runs BEFORE detect_table_grid)
                # Infer document type from text_objects only (lightweight, before Excel creation)
                if PRE_GRID_AVAILABLE:
                    try:
                        doc_type = infer_document_type_from_text(text_objects)
                        
                        # Apply pre-grid heuristic for specific document types
                        if should_apply_pre_grid_heuristic(doc_type):
                            logger.info(f"Page {page_num + 1}: Applying pre-grid heuristic for {doc_type}")
                            try:
                                column_boundaries, row_boundaries = infer_pre_grid_from_text(
                                    text_objects, page_width, page_height
                                )
                                grid_confidence = 0.45  # Moderate confidence for pre-grid
                                
                                # FAILSAFE: Verify grid produces reasonable results
                                # If grid is invalid, fallback to standard detection
                                if not column_boundaries or len(column_boundaries) < 2:
                                    logger.warning(f"Pre-grid produced invalid boundaries, falling back to standard detection")
                                    raise ValueError("Invalid pre-grid boundaries")
                                
                            except Exception as pre_grid_error:
                                logger.warning(f"Pre-grid heuristic failed: {pre_grid_error}, falling back to standard detection")
                                # Fallback to standard table grid detection
                                column_boundaries, row_boundaries, grid_confidence = detect_table_grid(
                                    lines, rectangles, text_objects, page_width, page_height
                                )
                        else:
                            # For invoices, bank statements, tables: Use standard table grid detection
                            logger.info(f"Page {page_num + 1}: Using standard table grid detection for {doc_type}")
                            column_boundaries, row_boundaries, grid_confidence = detect_table_grid(
                                lines, rectangles, text_objects, page_width, page_height
                            )
                    except Exception as pre_grid_import_error:
                        logger.warning(f"Pre-grid import/execution error: {pre_grid_import_error}, using standard detection")
                        # Fallback to standard table grid detection
                        column_boundaries, row_boundaries, grid_confidence = detect_table_grid(
                            lines, rectangles, text_objects, page_width, page_height
                        )
                else:
                    # Pre-grid not available - use standard detection
                    column_boundaries, row_boundaries, grid_confidence = detect_table_grid(
                        lines, rectangles, text_objects, page_width, page_height
                    )
                    
                    # If confidence is too low, still try to create grid from text positions
                    if grid_confidence < 0.2 and not column_boundaries and not row_boundaries:
                        logger.warning(f"Low confidence on page {page_num + 1}, using text-based grid")
                        if text_objects:
                            x_positions = sorted(set([obj['x'] for obj in text_objects]))
                            y_positions = sorted(set([obj['y'] for obj in text_objects]), reverse=True)
                            column_boundaries = x_positions if x_positions else [0, page_width]
                            row_boundaries = y_positions if y_positions else [0, page_height]
                            grid_confidence = 0.3  # Low but acceptable
                
                # SNAP TEXT TO GRID
                grid = snap_text_to_grid(text_objects, column_boundaries, row_boundaries)
                
                if not grid or not any(any(cell.get('text', '').strip() for cell in row) for row in grid):
                    logger.warning(f"Could not create grid for page {page_num + 1}, skipping...")
                    continue
                
                # IMPROVED: Clean grid - remove empty rows/columns and update boundaries
                if grid:
                    # Find rows with content
                    rows_with_content = []
                    for row_idx, row in enumerate(grid):
                        if any(cell.get('text', '').strip() for cell in row):
                            rows_with_content.append(row_idx)
                    
                    # Find columns with content
                    cols_with_content = set()
                    for row in grid:
                        for col_idx, cell in enumerate(row):
                            if cell.get('text', '').strip():
                                cols_with_content.add(col_idx)
                    
                    # Rebuild grid with only content rows/columns
                    if rows_with_content and cols_with_content:
                        cleaned_grid = []
                        cleaned_row_boundaries = []
                        sorted_cols = sorted(cols_with_content)
                        cleaned_column_boundaries = []
                        
                        # Build cleaned column boundaries
                        for col_idx in sorted_cols:
                            if col_idx < len(column_boundaries):
                                cleaned_column_boundaries.append(column_boundaries[col_idx])
                        
                        # Build cleaned grid and row boundaries
                        for row_idx in rows_with_content:
                            if row_idx < len(row_boundaries):
                                cleaned_row_boundaries.append(row_boundaries[row_idx])
                            cleaned_row = []
                            for col_idx in sorted_cols:
                                if col_idx < len(grid[row_idx]):
                                    cleaned_row.append(grid[row_idx][col_idx])
                            if cleaned_row:
                                cleaned_grid.append(cleaned_row)
                        
                        if cleaned_grid and cleaned_column_boundaries:
                            grid = cleaned_grid
                            row_boundaries = cleaned_row_boundaries
                            column_boundaries = cleaned_column_boundaries
                            logger.info(f"Page {page_num + 1}: Cleaned grid - {len(grid)} rows x {len(grid[0]) if grid else 0} columns (removed empty rows/columns)")
                
                # DETECT HEADER ROWS
                header_rows = detect_header_rows(grid, rectangles, row_boundaries)
                
                # Store page data
                all_pages_data.append({
                    'page_num': page_num,
                    'grid': grid,
                    'header_rows': header_rows,
                    'rectangles': rectangles,
                    'images': images,
                    'row_boundaries': row_boundaries,
                    'column_boundaries': column_boundaries,
                    'grid_confidence': grid_confidence
                })
                pages_to_process += 1
                
            except Exception as page_error:
                logger.error(f"Error processing page {page_num + 1}: {page_error}")
                continue  # Continue with other pages
        
        if not all_pages_data:
            return None, 0, 0.0, "No pages could be processed. This PDF may be too complex. Upgrade to Pro for better accuracy."
        
        # CREATE EXCEL WITH ALL PAGES
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()
        
        # Try LibreOffice conversion first (if enabled and available)
        use_libreoffice = False
        if LIBREOFFICE_ENABLED and is_libreoffice_available():
            logger.info("Attempting LibreOffice conversion...")
            libreoffice_success, libreoffice_error = convert_with_libreoffice(pdf_bytes, temp_path)
            if libreoffice_success:
                use_libreoffice = True
                logger.info("✅ LibreOffice conversion successful, applying heuristic fixes...")
            else:
                logger.warning(f"LibreOffice conversion failed: {libreoffice_error}, falling back to Python method")
        
        # Fallback to Python-based conversion
        if not use_libreoffice:
            success = create_excel_workbook_multi_page(
                all_pages_data,
                temp_path
            )
            
            if not success:
                return None, 0, 0.0, "Error creating Excel file"
        
        # HEURISTIC LAYER HOOK (FULLY REVERSIBLE)
        # Apply heuristic table-fix and document-type classification if enabled
        try:
            from free_heuristic.free_layout_guard import apply_heuristic_layer_if_enabled
            heuristic_applied, heuristic_error = apply_heuristic_layer_if_enabled(temp_path)
            if heuristic_applied:
                logger.info("Heuristic layer applied successfully")
            elif heuristic_error:
                logger.warning(f"Heuristic layer warning: {heuristic_error}")
                # Continue with original Excel - heuristic failure is non-fatal
        except ImportError:
            # Heuristic module not available - continue normally
            logger.debug("Heuristic module not available - skipping")
        except Exception as heuristic_e:
            # Heuristic error is non-fatal - continue with original Excel
            logger.warning(f"Heuristic layer error (non-fatal): {heuristic_e}")
        
        # Record usage (1 PDF converted)
        record_usage(free_key, pdfs_used=1, file_size=file_size)
        
        # Calculate final confidence (average of all pages)
        if all_pages_data:
            avg_confidence = sum(page_data.get('grid_confidence', 0.5) for page_data in all_pages_data) / len(all_pages_data)
            final_confidence = min(avg_confidence + 0.2, 1.0) if avg_confidence > 0 else 0.5
        else:
            final_confidence = 0.5
        
        return temp_path, pages_to_process, final_confidence, None
    
    except Exception as e:
        logger.error(f"Error in FREE PDF to Excel processing: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None, 0, 0.0, f"Processing error: {str(e)}"

