"""
Unified Layout Model
Standard structure for representing document layout across different document types.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class CellAlignment(Enum):
    """Cell alignment options"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


@dataclass
class CellStyle:
    """Cell styling information"""
    bold: bool = False
    italic: bool = False
    font_size: Optional[int] = None
    font_color: Optional[str] = None
    background_color: Optional[str] = None
    border: bool = True
    alignment_horizontal: CellAlignment = CellAlignment.LEFT
    alignment_vertical: CellAlignment = CellAlignment.MIDDLE
    wrap_text: bool = False


@dataclass
class Cell:
    """Represents a single cell in the layout"""
    row: int
    column: int
    value: str
    style: CellStyle = field(default_factory=CellStyle)
    rowspan: int = 1
    colspan: int = 1
    merged: bool = False


@dataclass
class MergedCell:
    """Represents a merged cell range"""
    start_row: int
    start_col: int
    end_row: int
    end_col: int


@dataclass
class UnifiedLayout:
    """
    Unified layout model for representing document structure.
    Used by both Document AI native tables and heuristic inference.
    """
    rows: List[List[Cell]] = field(default_factory=list)
    merged_cells: List[MergedCell] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_index: int = 0  # Track which page this layout belongs to
    
    def get_max_row(self) -> int:
        """Get maximum row index (0-based)"""
        if not self.rows:
            return -1  # Return -1 if no rows (will be handled as 0 rows)
        max_row = -1
        for row in self.rows:
            if row:
                # Get maximum row index from cells in this row
                max_row = max(max_row, max(cell.row for cell in row))
        return max_row  # Returns 0-based max row index
    
    def get_max_column(self) -> int:
        """Get maximum column index (0-based)"""
        if not self.rows:
            return -1  # Return -1 if no columns (will be handled as 0 columns)
        max_col = -1
        for row in self.rows:
            if row:
                max_col = max(max_col, max(cell.column for cell in row))
        return max_col  # Returns 0-based max column index
    
    def add_row(self, cells: List[Cell]):
        """Add a row of cells"""
        self.rows.append(cells)
    
    def add_merged_cell(self, start_row: int, start_col: int, end_row: int, end_col: int):
        """Add a merged cell range"""
        self.merged_cells.append(MergedCell(start_row, start_col, end_row, end_col))
    
    def get_cell(self, row: int, col: int) -> Optional[Cell]:
        """Get cell at specific position"""
        if 0 <= row < len(self.rows):
            for cell in self.rows[row]:
                if cell.column == col:
                    return cell
        return None
    
    def is_empty(self) -> bool:
        """Check if layout is empty"""
        if not self.rows:
            return True
        # Check if all rows are empty (no cells or all cells have empty values)
        for row in self.rows:
            if row:
                # Check if row has any non-empty cells
                for cell in row:
                    if cell.value and str(cell.value).strip():
                        return False
        return True
    
    def apply_spatial_indexing(self) -> bool:
        """
        CRITICAL FIX: Post-layout spatial row/column assignment.
        
        If all cells have row=0, col=0, use spatial information (y_center, x_center)
        to assign proper row/column indices.
        
        Returns:
            True if spatial indexing was applied, False if not needed
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Collect all cells
        all_cells = []
        for row_list in self.rows:
            if row_list:
                all_cells.extend(row_list)
        
        # CRITICAL: Allow single cell if it has newlines (needs splitting)
        single_cell_with_newlines = (len(all_cells) == 1 and 
                                     all_cells[0].value and 
                                     '\n' in str(all_cells[0].value))
        
        if len(all_cells) <= 1 and not single_cell_with_newlines:
            return False  # Not enough cells to index
        
        # Check if all cells have row=0, col=0 (invalid layout)
        # OR if there's only one cell with multiple lines (needs splitting)
        all_zero_indices = all(cell.row == 0 and cell.column == 0 for cell in all_cells)
        single_cell_with_newlines = (len(all_cells) == 1 and 
                                     all_cells[0].value and 
                                     '\n' in str(all_cells[0].value))
        
        if not all_zero_indices and not single_cell_with_newlines:
            # Layout already has proper indices
            return False
        
        # CRITICAL: If single cell with newlines, we MUST split it
        if single_cell_with_newlines:
            logger.critical("SPATIAL INDEXING: Single cell with newlines detected - will split into multiple rows")
        
        logger.critical("=" * 80)
        logger.critical("SPATIAL INDEXING: Detected invalid layout (all cells row=0, col=0)")
        logger.critical(f"   Total cells: {len(all_cells)}")
        logger.critical("   Applying spatial row/column assignment...")
        logger.critical("=" * 80)
        
        # CRITICAL: Use row list position AND cell content to infer spatial structure
        # Strategy: If cells contain newlines, split them into multiple rows
        # Otherwise, use row list position as row index
        cells_with_spatial = []
        
        for row_list_idx, row_list in enumerate(self.rows):
            if not row_list:
                continue
            
            for cell in row_list:
                cell_value = str(cell.value) if cell.value else ''
                
                # CRITICAL: If cell contains newlines, split it into multiple rows
                # This handles the case where all content is in one cell
                if '\n' in cell_value:
                    # Text with newlines - split into multiple rows
                    lines = cell_value.split('\n')
                    for line_idx, line in enumerate(lines):
                        line = line.strip()
                        if line:  # Only non-empty lines
                            # CRITICAL: Each line gets a distinct row index
                            # Use row_list_idx as base, but add line_idx to create separate rows
                            y_center = row_list_idx + line_idx  # Each line = different row
                            
                            # Try to detect if it's a label or value for column assignment
                            x_center = 0  # Default to column 0
                            label_patterns = ['name', 'id', 'number', 'date', 'amount', 'biller', 'customer', 'payment', 'mobile', 'consumer', 'spice', 'money', 'assured', 'bill']
                            is_label = any(pattern in line.lower() for pattern in label_patterns)
                            if not is_label and len(line) > 10 and not line[0].isupper():
                                # Might be a value - assign to column 1
                                x_center = 1
                            
                            # Create a virtual cell for this line
                            cells_with_spatial.append({
                                'cell': cell,  # Same cell object, but different logical position
                                'y_center': y_center,  # Each line gets different row
                                'x_center': x_center,
                                'value': line,
                                'row_list_idx': row_list_idx,
                                'col_list_idx': line_idx,
                                'is_split': True,
                                'line_index': line_idx
                            })
                else:
                    # Single cell - use row list position
                    # Try to detect if it's a label or value for column assignment
                    x_center = 0  # Default to column 0
                    
                    # Heuristic: If cell contains common label patterns, it's likely column 0
                    # Otherwise, it might be column 1
                    label_patterns = ['name', 'id', 'number', 'date', 'amount', 'biller', 'customer', 'payment', 'mobile', 'consumer']
                    is_label = any(pattern in cell_value.lower() for pattern in label_patterns)
                    if not is_label and len(cell_value) > 10:
                        # Might be a value - assign to column 1
                        x_center = 1
                    
                    cells_with_spatial.append({
                        'cell': cell,
                        'y_center': row_list_idx,
                        'x_center': x_center,
                        'value': cell_value,
                        'row_list_idx': row_list_idx,
                        'col_list_idx': 0,
                        'is_split': False
                    })
        
        if not cells_with_spatial:
            logger.warning("SPATIAL INDEXING: No cells with spatial information")
            return False
        
        # STEP 1: Spatial row inference
        # Sort all cells by y_center (top to bottom)
        cells_with_spatial.sort(key=lambda c: (c['y_center'], c.get('line_index', 0)))
        
        # Group cells into rows based on y_center proximity
        # Calculate threshold for row grouping
        y_positions = [c['y_center'] for c in cells_with_spatial]
        if len(y_positions) > 1:
            y_diffs = [abs(y_positions[i+1] - y_positions[i]) for i in range(len(y_positions)-1)]
            avg_y_diff = sum(y_diffs) / len(y_diffs) if y_diffs else 0.5
            threshold = max(avg_y_diff * 0.5, 0.1)  # At least 0.1 difference
        else:
            threshold = 0.5
        
        # Group into rows
        rows_groups = []
        if cells_with_spatial:
            current_row = [cells_with_spatial[0]]
            current_y = cells_with_spatial[0]['y_center']
            
            for cell_data in cells_with_spatial[1:]:
                if abs(cell_data['y_center'] - current_y) <= threshold:
                    # Same row
                    current_row.append(cell_data)
                else:
                    # New row
                    rows_groups.append(current_row)
                    current_row = [cell_data]
                    current_y = cell_data['y_center']
            
            if current_row:
                rows_groups.append(current_row)
        
        logger.critical(f"SPATIAL INDEXING: Detected {len(rows_groups)} rows using threshold {threshold:.4f}")
        
        # STEP 2: Assign row and column indices
        # CRITICAL: For split cells, create new Cell objects
        # For original cells, update their indices
        new_cells = []  # Track all cells (including split ones)
        original_cells_used = set()  # Track which original cells have been processed
        
        for row_idx, row_group in enumerate(rows_groups):
            # Sort cells within row by x_center (left to right)
            row_group.sort(key=lambda c: (c['x_center'], c.get('col_list_idx', 0)))
            
            # Assign column indices
            for col_idx, cell_data in enumerate(row_group):
                cell = cell_data['cell']
                
                if cell_data.get('is_split', False):
                    # This is a split cell - create a new cell for this line
                    new_cell = Cell(
                        row=row_idx,
                        column=col_idx,
                        value=cell_data['value'],
                        style=cell.style  # Copy style from original
                    )
                    new_cells.append(new_cell)
                    original_cells_used.add(id(cell))  # Mark original as used
                else:
                    # Original cell - update indices only if not already split
                    if id(cell) not in original_cells_used:
                        cell.row = row_idx
                        cell.column = col_idx
                        new_cells.append(cell)
                        original_cells_used.add(id(cell))
        
        # STEP 3: Rebuild rows list with proper structure
        # Group new_cells by row
        if new_cells:
            max_row_idx = max(c.row for c in new_cells)
            new_rows = [[] for _ in range(max_row_idx + 1)]
            
            for cell in new_cells:
                if 0 <= cell.row <= max_row_idx:
                    new_rows[cell.row].append(cell)
            
            # Sort cells within each row by column
            for row in new_rows:
                row.sort(key=lambda c: c.column)
            
            self.rows = new_rows
        else:
            # No cells - this shouldn't happen
            logger.warning("SPATIAL INDEXING: No cells after processing")
            self.rows = []
        
        # STEP 4: Post-processing - Detect label-value pairs and merge into 2 columns
        # CRITICAL FIX: Also work for multi-column layouts where Col2 is mostly empty
        unique_rows = set(c.row for c in new_cells)
        unique_cols = set(c.column for c in new_cells)
        
        # Check if we need label-value pairing:
        # 1. Single column layout (original case)
        # 2. Multi-column layout but Col2 is mostly empty (new case)
        needs_label_value_pairing = False
        if len(unique_cols) == 1 and len(unique_rows) >= 4:
            needs_label_value_pairing = True
            logger.critical("SPATIAL INDEXING: Detected single column with multiple rows - attempting label-value pairing")
        elif len(unique_cols) >= 2:
            # Check if Col2 is mostly empty (less than 30% of rows have Col2 content)
            rows_with_col2 = set()
            for cell in new_cells:
                if cell.column >= 1:  # Col2 or higher
                    rows_with_col2.add(cell.row)
            
            col2_coverage = len(rows_with_col2) / len(unique_rows) if unique_rows else 0
            if col2_coverage < 0.3 and len(unique_rows) >= 4:
                needs_label_value_pairing = True
                logger.critical(f"SPATIAL INDEXING: Detected multi-column layout but Col2 is mostly empty ({col2_coverage:.1%} coverage) - attempting label-value pairing")
        
        if needs_label_value_pairing:
            # Likely label-value pairs - merge adjacent rows into 2 columns
            logger.critical("SPATIAL INDEXING: Detected single column with multiple rows - attempting label-value pairing")
            
            # Sort cells by row
            sorted_cells = sorted(new_cells, key=lambda c: c.row)
            
            # Detect label patterns (case-insensitive) - Enhanced with more patterns
            label_patterns = [
                r'name\s+of\s+the\s+customer', r'biller\s+name', r'biller\s+id', r'consumer\s+number',
                r'mobile\s+number', r'payment\s+mode', r'payment\s+status', r'payment\s+channel',
                r'approval\s+ref\s+no', r'approval\s+ref', r'customer\s+convenience\s+fee',
                r'biller\s+platform\s+fee', r'digital\s+fee', r'date', r'amount', r'total', r'transaction',
                r'account', r'address', r'email', r'phone', r'id', r'number', r'b-connect\s+txn\s+id',
                r'receipt', r'invoice', r'bill', r'agent', r'merchant', r'customer', r'consumer',
                # Hindi patterns
                r'नाम', r'पिता', r'पति', r'आधार', r'जाती', r'कार्ड', r'प्रकार', r'समग्र', r'परिवार', r'क्र'
            ]
            
            import re
            merged_cells = []
            row_idx = 0
            i = 0
            
            while i < len(sorted_cells):
                current_cell = sorted_cells[i]
                current_value = str(current_cell.value).strip()
                current_value_lower = current_value.lower()
                
                # Check if current cell is a label
                is_label = any(re.search(pattern, current_value_lower) for pattern in label_patterns)
                
                # Also check if it's short text (likely label) vs long text (likely value)
                # Enhanced: Check for common label characteristics
                is_short = len(current_value) < 50  # Increased threshold
                is_all_caps = current_value.isupper() and len(current_value) > 1
                starts_with_caps = current_value and current_value[0].isupper()
                has_colon = ':' in current_value
                
                # Label characteristics: short, has spaces, not all caps, may have colon
                is_likely_label = (is_label or 
                                 (is_short and has_colon) or
                                 (is_short and ' ' in current_value and not is_all_caps and not current_value.replace(' ', '').isdigit()))
                
                if is_likely_label and i + 1 < len(sorted_cells):
                    # Current is label, next should be value
                    label_cell = current_cell
                    value_cell = sorted_cells[i + 1]
                    
                    # Check if next cell is actually a value (not another label)
                    next_value = str(value_cell.value).strip().lower()
                    next_is_label = any(re.search(pattern, next_value) for pattern in label_patterns)
                    
                    if not next_is_label:
                        # Create merged row: label in col 0, value in col 1
                        label_cell.row = row_idx
                        label_cell.column = 0
                        
                        value_cell.row = row_idx
                        value_cell.column = 1
                        
                        merged_cells.append(label_cell)
                        merged_cells.append(value_cell)
                        row_idx += 1
                        i += 2  # Skip both cells
                    else:
                        # Both are labels, keep first as single cell
                        current_cell.row = row_idx
                        current_cell.column = 0
                        merged_cells.append(current_cell)
                        row_idx += 1
                        i += 1
                else:
                    # Not a label-value pair, keep as is in column 0
                    # CRITICAL: Only add if cell has value (no empty cells)
                    if current_cell.value and str(current_cell.value).strip():
                        current_cell.row = row_idx
                        current_cell.column = 0
                        merged_cells.append(current_cell)
                        row_idx += 1
                    i += 1
            
            # Rebuild rows with merged structure
            if merged_cells:
                max_row_idx = max(c.row for c in merged_cells)
                new_rows_merged = [[] for _ in range(max_row_idx + 1)]
                
                for cell in merged_cells:
                    if 0 <= cell.row <= max_row_idx:
                        # CRITICAL: Only add cell if it has a value (no empty cells)
                        if cell.value and str(cell.value).strip():
                            new_rows_merged[cell.row].append(cell)
                
                # Sort cells within each row by column
                for row in new_rows_merged:
                    row.sort(key=lambda c: c.column)
                
                # CRITICAL: Remove empty rows
                new_rows_merged = [row for row in new_rows_merged if row]
                
                # Re-assign row indices after removing empty rows
                final_cells = []
                for new_row_idx, row in enumerate(new_rows_merged):
                    for cell in row:
                        cell.row = new_row_idx
                        final_cells.append(cell)
                
                self.rows = new_rows_merged
                new_cells = final_cells
                logger.critical(f"SPATIAL INDEXING: Merged into {len(new_rows_merged)} rows with label-value pairs (removed empty cells)")
        
        # STEP 5: Validation - use new_cells (includes split cells and merged pairs)
        unique_rows = set(c.row for c in new_cells)
        unique_cols = set(c.column for c in new_cells)
        max_row = max(unique_rows) if unique_rows else -1
        max_col = max(unique_cols) if unique_cols else -1
        
        logger.critical("=" * 80)
        logger.critical("SPATIAL INDEXING: Complete")
        logger.critical(f"   Total cells: {len(new_cells)}")
        logger.critical(f"   Unique row indices: {sorted(unique_rows)}")
        logger.critical(f"   Unique column indices: {sorted(unique_cols)}")
        logger.critical(f"   Max row: {max_row}, Max col: {max_col}")
        logger.critical(f"   First 5 cells (row, col, text):")
        for idx, cell in enumerate(new_cells[:5]):
            logger.critical(f"      ({cell.row}, {cell.column}): '{str(cell.value)[:40]}...'")
        logger.critical("=" * 80)
        
        # STEP 6: Failure handling
        if len(unique_rows) < 2 and len(unique_cols) < 2:
            error_msg = f"Spatial indexing failed: Only {len(unique_rows)} row(s) and {len(unique_cols)} column(s) detected"
            logger.critical(f"❌ {error_msg}")
            raise ValueError(f"Layout empty — conversion aborted: {error_msg}")
        
        return True

