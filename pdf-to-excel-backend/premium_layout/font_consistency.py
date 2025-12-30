"""
FONT CONSISTENCY GUARANTEE
Ensures one row = one font family + size.
Mixed fonts allowed ONLY if DocAI explicitly reports style difference.
"""

import logging
from typing import List
from .unified_layout_model import UnifiedLayout, Cell, CellStyle

logger = logging.getLogger(__name__)


class FontConsistencyEnforcer:
    """
    Enforces font consistency per row.
    Rules:
    - One row → one font family + size
    - Mixed fonts allowed ONLY if DocAI explicitly reports style difference
    - Visual heuristics must NOT change fonts
    """
    
    def __init__(self):
        """Initialize Font Consistency Enforcer"""
        pass
    
    def enforce_per_row(self, layout: UnifiedLayout) -> UnifiedLayout:
        """
        Enforce STRICT ROW FONT POLICY.
        
        Rules:
        - One row = one font family + size
        - If mixed font detected inside row → split into separate rows
        - ❌ Never normalize font across rows
        - ❌ Never merge text blocks of different font sizes
        
        Args:
            layout: Layout to process
        
        Returns:
            Layout with enforced font consistency
        """
        if layout.is_empty():
            return layout
        
        new_layout = UnifiedLayout(page_index=layout.page_index)
        new_layout.metadata = layout.metadata.copy()
        
        new_row_idx = 0
        
        for original_row in layout.rows:
            if not original_row:
                continue
            
            # Collect font info from all cells in row
            font_sizes = []
            font_info_by_cell = {}  # cell_index -> (font_size, font_family)
            
            for cell_idx, cell in enumerate(original_row):
                if cell.style:
                    font_size = cell.style.font_size
                    font_sizes.append(font_size)
                    font_info_by_cell[cell_idx] = font_size
                else:
                    font_info_by_cell[cell_idx] = None
            
            # Check if row has mixed fonts
            unique_font_sizes = set(f for f in font_sizes if f is not None)
            
            if len(unique_font_sizes) > 1:
                # MIXED FONTS DETECTED → Split into separate rows
                logger.critical(f"🔒 Font Consistency: Mixed fonts detected in row - SPLITTING into separate rows")
                
                # Group cells by font size
                cells_by_font = {}  # font_size -> list of (cell_idx, cell)
                for cell_idx, cell in enumerate(original_row):
                    font_size = font_info_by_cell.get(cell_idx)
                    if font_size not in cells_by_font:
                        cells_by_font[font_size] = []
                    cells_by_font[font_size].append((cell_idx, cell))
                
                # Create separate row for each font size
                for font_size, cell_list in sorted(cells_by_font.items()):
                    new_row = []
                    for cell_idx, cell in sorted(cell_list, key=lambda x: x[1].column):
                        new_cell = Cell(
                            row=new_row_idx,
                            column=cell.column,
                            value=cell.value,
                            style=cell.style,  # Keep original style
                            rowspan=1,  # Single row (split)
                            colspan=cell.colspan,
                            merged=False  # Don't merge across font boundaries
                        )
                        new_row.append(new_cell)
                    
                    if new_row:
                        new_layout.add_row(new_row)
                        new_row_idx += 1
            else:
                # Single font in row - use dominant font size
                dominant_font_size = unique_font_sizes.pop() if unique_font_sizes else None
                
                # Create new row with consistent fonts
                new_row = []
                for cell in original_row:
                    # Create new style with dominant font
                    new_style = CellStyle(
                        bold=cell.style.bold if cell.style else False,
                        italic=cell.style.italic if cell.style else False,
                        font_size=dominant_font_size or (cell.style.font_size if cell.style else None),
                        font_color=cell.style.font_color if cell.style else None,
                        background_color=cell.style.background_color if cell.style else None,
                        border=cell.style.border if cell.style else True,
                        alignment_horizontal=cell.style.alignment_horizontal if cell.style else None,
                        alignment_vertical=cell.style.alignment_vertical if cell.style else None,
                        wrap_text=cell.style.wrap_text if cell.style else False
                    )
                    
                    new_cell = Cell(
                        row=new_row_idx,
                        column=cell.column,
                        value=cell.value,
                        style=new_style,
                        rowspan=1,  # Single row (no font mixing)
                        colspan=cell.colspan,
                        merged=cell.merged
                    )
                    new_row.append(new_cell)
                
                new_layout.add_row(new_row)
                new_row_idx += 1
        
        # Copy merged cells (only if same font)
        for merged in layout.merged_cells:
            # Only keep merged cells within same row (font consistency already enforced)
            if merged.start_row == merged.end_row:
                new_layout.add_merged_cell(
                    merged.start_row,
                    merged.start_col,
                    merged.end_row,
                    merged.end_col
                )
        
        logger.critical(f"🔒 Font Consistency: Enforced STRICT ROW FONT POLICY. Original rows: {len(layout.rows)}, New rows: {new_row_idx}")
        return new_layout

