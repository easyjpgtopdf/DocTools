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
        """Get maximum row index"""
        if not self.rows:
            return 0
        return len(self.rows)
    
    def get_max_column(self) -> int:
        """Get maximum column index"""
        if not self.rows:
            return 0
        max_col = 0
        for row in self.rows:
            if row:
                max_col = max(max_col, max(cell.column for cell in row) + 1)
        return max_col
    
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
        return not self.rows or all(not row for row in self.rows)

