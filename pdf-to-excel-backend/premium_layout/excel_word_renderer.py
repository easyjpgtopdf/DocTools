"""
Excel/Word Renderer
Converts unified layout model to Excel and Word formats.
"""

import logging
import io
from typing import Optional, List, Dict

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available, Word export disabled")

from .unified_layout_model import UnifiedLayout, Cell, CellStyle, CellAlignment

try:
    from openpyxl.drawing.image import Image as ExcelImage
    IMAGE_SUPPORT = True
except ImportError:
    IMAGE_SUPPORT = False
    logger.warning("openpyxl image support not available")


class ExcelWordRenderer:
    """Renders unified layout to Excel and Word formats"""
    
    def __init__(self):
        """Initialize renderer"""
        pass
    
    def render_to_excel(self, layouts: List[UnifiedLayout], images: Optional[List[Dict]] = None) -> bytes:
        """
        Render unified layouts to Excel format (one sheet per page).
        
        Args:
            layouts: List of UnifiedLayout objects (one per page)
            images: Optional list of images to insert (from ImageExtractor)
            
        Returns:
            Excel file as bytes
        """
        workbook = Workbook()
        workbook.remove(workbook.active)
        
        # Group images by page
        images_by_page = {}
        if images:
            for img in images:
                page_idx = img.get('page_index', 0)
                if page_idx not in images_by_page:
                    images_by_page[page_idx] = []
                images_by_page[page_idx].append(img)
        
        # Create one sheet per page (Page-to-Sheet Mapping)
        for layout in layouts:
            page_num = layout.page_index + 1
            # Sheet naming: Page_1, Page_2, Page_3... (with underscore)
            sheet_name = f"Page_{page_num}" if len(layouts) > 1 else "Document"
            # Excel sheet names max 31 characters
            if len(sheet_name) > 31:
                sheet_name = sheet_name[:31]
            
            sheet = workbook.create_sheet(title=sheet_name)
            
            # SINGLE SOURCE OF MERGE TRUTH: Build set of merged cell positions from layout.merged_cells only
            merged_cell_positions = set()  # Track all positions that are part of merges (excluding top-left)
            merge_ranges = []  # Store merge ranges for application
            
            # Build merge ranges from layout.merged_cells (SINGLE SOURCE OF TRUTH)
            for merged in layout.merged_cells:
                start_row = merged.start_row + 1  # Convert to 1-based
                start_col = merged.start_col + 1
                # CORRECT MERGE RANGE: Fix off-by-one error
                end_row = merged.end_row + 1  # end_row is already inclusive in UnifiedLayout
                end_col = merged.end_col + 1  # end_col is already inclusive in UnifiedLayout
                
                # Store merge range
                merge_ranges.append((start_row, start_col, end_row, end_col))
                
                # Mark all slave cells (non-top-left) as merged positions
                for r in range(start_row, end_row + 1):
                    for c in range(start_col, end_col + 1):
                        if not (r == start_row and c == start_col):
                            merged_cell_positions.add((r, c))
            
            # Also handle cells with rowspan/colspan that might not be in merged_cells
            # (defensive: ensure we don't write to spanned cells)
            for row in layout.rows:
                for cell in row:
                    if cell.rowspan > 1 or cell.colspan > 1:
                        row_num = cell.row + 1
                        col_num = cell.column + 1
                        # CORRECT MERGE RANGE: end = start + span - 1
                        end_row = row_num + cell.rowspan - 1
                        end_col = col_num + cell.colspan - 1
                        
                        # Mark slave cells
                        for r in range(row_num, end_row + 1):
                            for c in range(col_num, end_col + 1):
                                if not (r == row_num and c == col_num):
                                    merged_cell_positions.add((r, c))
                        
                        # Add to merge ranges if not already present
                        merge_key = (row_num, col_num, end_row, end_col)
                        if merge_key not in merge_ranges:
                            merge_ranges.append(merge_key)
            
            # Track styles for cells (only top-left of merges get values)
            cell_styles_map = {}  # Track styles for each cell position
            
            # First pass: Write ONLY top-left cells (skip merged slave cells)
            # CLEAN RENDER GUARANTEE: Dumb mirror - write exactly what UnifiedLayout provides
            for row in layout.rows:
                for cell in row:
                    row_num = cell.row + 1
                    col_num = cell.column + 1
                    
                    # MERGED CELL WRITE RULE: Skip writing if this is a slave cell
                    if (row_num, col_num) in merged_cell_positions:
                        # This is a slave cell - skip writing value completely
                        # Only store style for potential border/formatting
                        cell_styles_map[(row_num, col_num)] = cell.style
                        continue
                    
                    # This is either top-left of merge or regular cell - write value
                    excel_cell = sheet.cell(row=row_num, column=col_num, value=cell.value)
                    cell_styles_map[(row_num, col_num)] = cell.style
            
            # Apply merges from SINGLE SOURCE (layout.merged_cells is primary, cell rowspan/colspan is fallback)
            # SINGLE SOURCE OF MERGE TRUTH: Never merge the same range twice
            applied_merges = set()  # Track applied merges to prevent duplicates
            
            for start_row, start_col, end_row, end_col in merge_ranges:
                merge_key = (start_row, start_col, end_row, end_col)
                
                # Prevent duplicate merges
                if merge_key in applied_merges:
                    logger.debug(f"Skipping duplicate merge: ({start_row},{start_col}) to ({end_row},{end_col})")
                    continue
                
                applied_merges.add(merge_key)
                
                # Validate merge range (end must be >= start)
                if end_row < start_row or end_col < start_col:
                    logger.warning(f"Invalid merge range: ({start_row},{start_col}) to ({end_row},{end_col}), skipping")
                    continue
                
                try:
                    sheet.merge_cells(
                        start_row=start_row,
                        start_column=start_col,
                        end_row=end_row,
                        end_column=end_col
                    )
                    logger.debug(f"Merged cells: ({start_row},{start_col}) to ({end_row},{end_col})")
                except Exception as e:
                    logger.warning(f"Failed to merge cells {start_row},{start_col} to {end_row},{end_col}: {e}")
            
            # Second pass: Apply styles to ALL cells (after merge)
            for (row_num, col_num), style in cell_styles_map.items():
                excel_cell = sheet.cell(row=row_num, column=col_num)
                self._apply_cell_style(excel_cell, style)
            
            # Auto-adjust column widths
            self._auto_adjust_columns(sheet, layout)
            
            # Freeze header rows (PREMIUM feature)
            header_row_indices = layout.metadata.get('header_row_indices', [])
            if header_row_indices:
                # Freeze at the row after the last header row
                freeze_row = max(header_row_indices) + 2  # +1 for 1-based, +1 for next row
                if freeze_row <= sheet.max_row:
                    sheet.freeze_panes = f"A{freeze_row}"
                    logger.info(f"Froze header rows at row {freeze_row}")
            
            # Insert images for this page
            page_images = images_by_page.get(layout.page_index, [])
            if page_images and IMAGE_SUPPORT:
                self._insert_images_to_sheet(sheet, page_images, layout)
        
        # Save to bytes
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        return output.getvalue()
    
    def _insert_images_to_sheet(self, sheet, images: List[Dict], layout: UnifiedLayout):
        """Insert images into Excel sheet at appropriate positions"""
        if not IMAGE_SUPPORT:
            return
        
        try:
            from .image_extractor import ImageExtractor
            extractor = ImageExtractor()
            
            max_col = layout.get_max_column()
            image_col = max_col + 2  # Place images after data columns
            
            for img_idx, img_info in enumerate(images[:5]):  # Limit to 5 images per sheet
                try:
                    image_bytes = img_info.get('image_bytes')
                    if not image_bytes:
                        continue
                    
                    # Prepare image for Excel
                    prepared_bytes = extractor.prepare_image_for_excel(image_bytes, max_width=150, max_height=150)
                    if not prepared_bytes:
                        continue
                    
                    # Create Excel image
                    img = ExcelImage(io.BytesIO(prepared_bytes))
                    
                    # Calculate position (use normalized coordinates to determine cell)
                    position = img_info.get('position', (0.0, 0.0, 0.1, 0.1))
                    x_norm, y_norm = position[0], position[1]
                    
                    # Convert normalized position to row/column
                    # Assuming page height = 1.0, width = 1.0
                    max_row = layout.get_max_row()
                    if max_row > 0:
                        row_num = max(1, int(y_norm * max_row) + 1)
                    else:
                        row_num = img_idx * 20 + 1
                    
                    # Anchor image to cell
                    from openpyxl.utils import get_column_letter
                    anchor_col = get_column_letter(image_col)
                    anchor_cell = f"{anchor_col}{row_num}"
                    
                    # Add image to sheet
                    sheet.add_image(img, anchor_cell)
                    logger.debug(f"Inserted image {img_idx + 1} at {anchor_cell}")
                    
                except Exception as img_error:
                    logger.warning(f"Failed to insert image {img_idx + 1}: {img_error}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error inserting images to sheet: {e}")
    
    def render_to_word(self, layout: UnifiedLayout) -> bytes:
        """
        Render unified layout to Word format.
        
        Args:
            layout: UnifiedLayout object
            
        Returns:
            Word file as bytes
        """
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx is required for Word export")
        
        doc = Document()
        
        # Create table if we have structured data
        if layout.get_max_row() > 0 and layout.get_max_column() > 1:
            table = doc.add_table(rows=layout.get_max_row(), cols=layout.get_max_column())
            table.style = 'Light Grid Accent 1'
            
            # Fill table cells
            for row in layout.rows:
                for cell in row:
                    if cell.row < len(table.rows) and cell.column < len(table.rows[cell.row].cells):
                        table_cell = table.rows[cell.row].cells[cell.column]
                        paragraph = table_cell.paragraphs[0]
                        run = paragraph.add_run(cell.value)
                        
                        # Apply styles
                        if cell.style.bold:
                            run.bold = True
                        if cell.style.italic:
                            run.italic = True
                        if cell.style.font_size:
                            run.font.size = Pt(cell.style.font_size)
                        
                        # Alignment
                        if cell.style.alignment_horizontal == CellAlignment.CENTER:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        elif cell.style.alignment_horizontal == CellAlignment.RIGHT:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            # Simple paragraph format for unstructured content
            for row in layout.rows:
                for cell in row:
                    paragraph = doc.add_paragraph(cell.value)
                    if cell.style.bold:
                        for run in paragraph.runs:
                            run.bold = True
        
        # Save to bytes
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output.getvalue()
    
    def _apply_cell_style(self, excel_cell, style: CellStyle):
        """Apply cell style to Excel cell"""
        # Font
        font_kwargs = {}
        if style.bold:
            font_kwargs['bold'] = True
        if style.italic:
            font_kwargs['italic'] = True
        if style.font_size:
            font_kwargs['size'] = style.font_size
        if style.font_color:
            font_kwargs['color'] = style.font_color
        
        if font_kwargs:
            excel_cell.font = Font(**font_kwargs)
        
        # Alignment
        alignment_kwargs = {}
        if style.alignment_horizontal == CellAlignment.CENTER:
            alignment_kwargs['horizontal'] = 'center'
        elif style.alignment_horizontal == CellAlignment.RIGHT:
            alignment_kwargs['horizontal'] = 'right'
        else:
            alignment_kwargs['horizontal'] = 'left'
        
        if style.alignment_vertical == CellAlignment.TOP:
            alignment_kwargs['vertical'] = 'top'
        elif style.alignment_vertical == CellAlignment.BOTTOM:
            alignment_kwargs['vertical'] = 'bottom'
        else:
            alignment_kwargs['vertical'] = 'center'
        
        if style.wrap_text:
            alignment_kwargs['wrap_text'] = True
        
        excel_cell.alignment = Alignment(**alignment_kwargs)
        
        # Border
        if style.border:
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            excel_cell.border = thin_border
        
        # Background color
        if style.background_color:
            fill = PatternFill(
                start_color=style.background_color,
                end_color=style.background_color,
                fill_type='solid'
            )
            excel_cell.fill = fill
    
    def _auto_adjust_columns(self, sheet, layout: UnifiedLayout):
        """
        Auto-adjust column widths based on content.
        COLUMN STABILITY: Only adjusts width, does NOT infer new columns.
        Column indices from UnifiedLayout are final.
        """
        max_col = layout.get_max_column()
        
        # COLUMN STABILITY: Only process columns that exist in UnifiedLayout
        # Do NOT create or infer new columns
        for col_idx in range(max_col):
            column_letter = get_column_letter(col_idx + 1)
            max_length = 0
            
            # Find max length in this column (only from actual cells in layout)
            for row in layout.rows:
                for cell in row:
                    # Only consider cells in this exact column (no inference)
                    if cell.column == col_idx:
                        if cell.value:
                            # Estimate length (Unicode-aware)
                            length = sum(2 if ord(c) > 127 else 1 for c in str(cell.value))
                            max_length = max(max_length, length)
            
            # Set column width (conservative adjustment - doesn't break alignment)
            # Minimum width 10, maximum 50, with small padding
            if max_length > 0:
                adjusted_width = min(max(max_length + 2, 10), 50)
                sheet.column_dimensions[column_letter].width = adjusted_width
            else:
                # Empty column - set minimal width
                sheet.column_dimensions[column_letter].width = 10

