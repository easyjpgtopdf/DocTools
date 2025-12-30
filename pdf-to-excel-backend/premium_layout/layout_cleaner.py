"""
LAYOUT CLEANER
Removes empty rows and columns before Excel rendering.
CRITICAL: NO fake rows or columns allowed.
"""

import logging
from typing import List
from .unified_layout_model import UnifiedLayout, Cell

logger = logging.getLogger(__name__)


class LayoutCleaner:
    """
    Cleans layout by removing empty rows and columns.
    CRITICAL RULES:
    - DROP any column with no text
    - DROP any row with no text
    - NO placeholder rows/columns
    """
    
    def __init__(self):
        """Initialize Layout Cleaner"""
        pass
    
    def has_text(self, cell: Cell) -> bool:
        """Check if cell has actual text content"""
        return bool(cell.value and str(cell.value).strip())
    
    def clean_empty_rows(self, layout: UnifiedLayout) -> UnifiedLayout:
        """
        Remove rows that have no text in any cell.
        
        Returns:
            Layout with empty rows removed
        """
        if layout.is_empty():
            return layout
        
        new_layout = UnifiedLayout(page_index=layout.page_index)
        new_layout.metadata = layout.metadata.copy()
        
        new_row_idx = 0
        
        for row in layout.rows:
            # Check if row has any text
            has_content = any(self.has_text(cell) for cell in row)
            
            if has_content:
                # Adjust row indices
                adjusted_row = []
                for cell in row:
                    adjusted_cell = Cell(
                        row=new_row_idx,
                        column=cell.column,
                        value=cell.value,
                        style=cell.style,
                        rowspan=cell.rowspan,
                        colspan=cell.colspan,
                        merged=cell.merged
                    )
                    adjusted_row.append(adjusted_cell)
                
                new_layout.add_row(adjusted_row)
                new_row_idx += 1
            else:
                logger.debug(f"Layout Cleaner: Dropping empty row {row[0].row if row else 'unknown'}")
        
        logger.info(f"Layout Cleaner: Cleaned empty rows. Original: {len(layout.rows)}, New: {len(new_layout.rows)}")
        return new_layout
    
    def clean_empty_columns(self, layout: UnifiedLayout) -> UnifiedLayout:
        """
        Remove columns that have no text or <2 non-empty cells.
        
        CRITICAL RULES:
        - DROP any column with no text
        - DROP any column with <2 non-empty cells
        - ❌ Do NOT pad table to rectangle shape
        - ❌ Do NOT auto-fill missing cells
        
        Returns:
            Layout with empty columns removed
        """
        if layout.is_empty():
            return layout
        
        # Count non-empty cells per column
        column_cell_count = {}  # column -> count of non-empty cells
        for row in layout.rows:
            for cell in row:
                if self.has_text(cell):
                    col = cell.column
                    column_cell_count[col] = column_cell_count.get(col, 0) + 1
        
        if not column_cell_count:
            logger.warning("Layout Cleaner: No columns with text found")
            return layout
        
        # Keep only columns with >= 2 non-empty cells
        valid_columns = {col for col, count in column_cell_count.items() if count >= 2}
        
        if not valid_columns:
            # If no column has >= 2 cells, keep columns with at least 1 cell
            valid_columns = set(column_cell_count.keys())
            logger.warning(f"Layout Cleaner: No column has >= 2 cells, keeping columns with at least 1 cell: {valid_columns}")
        
        # Create mapping: old_column -> new_column
        sorted_columns = sorted(valid_columns)
        column_mapping = {old_col: new_col for new_col, old_col in enumerate(sorted_columns)}
        
        # Create new layout with remapped columns
        new_layout = UnifiedLayout(page_index=layout.page_index)
        new_layout.metadata = layout.metadata.copy()
        
        for row in layout.rows:
            new_row = []
            for cell in row:
                if cell.column in column_mapping:
                    new_col = column_mapping[cell.column]
                    adjusted_cell = Cell(
                        row=cell.row,
                        column=new_col,
                        value=cell.value,
                        style=cell.style,
                        rowspan=cell.rowspan,
                        colspan=1,  # Reset colspan (simplified)
                        merged=cell.merged
                    )
                    new_row.append(adjusted_cell)
            
            if new_row:
                new_layout.add_row(new_row)
        
        dropped_columns = len(column_cell_count) - len(valid_columns)
        logger.critical(f"🔒 Layout Cleaner: Cleaned columns. Original: {len(column_cell_count)}, Valid (>=2 cells): {len(valid_columns)}, Dropped: {dropped_columns}")
        return new_layout
    
    def clean(self, layout: UnifiedLayout) -> UnifiedLayout:
        """
        Clean layout by removing empty rows and columns.
        
        Order:
        1. Remove empty rows
        2. Remove empty columns
        
        Returns:
            Cleaned layout
        """
        if layout.is_empty():
            return layout
        
        # Step 1: Remove empty rows
        cleaned = self.clean_empty_rows(layout)
        
        # Step 2: Remove empty columns
        cleaned = self.clean_empty_columns(cleaned)
        
        return cleaned

