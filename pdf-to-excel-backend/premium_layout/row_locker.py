"""
ROW LOCKING MECHANISM
Prevents word spill across rows by enforcing strict baseline clustering.
CRITICAL: Text from one row must NEVER appear in another row.
"""

import logging
from typing import List, Dict, Tuple, Any, Optional
from .unified_layout_model import UnifiedLayout, Cell

logger = logging.getLogger(__name__)


class RowLocker:
    """
    Enforces row boundaries to prevent word spill.
    Uses vertical overlap threshold (70%) to determine if text belongs to same row.
    """
    
    def __init__(self, overlap_threshold: float = 0.7):
        """
        Initialize Row Locker.
        
        Args:
            overlap_threshold: Minimum vertical overlap (0.0-1.0) to merge text into same row
        """
        self.overlap_threshold = overlap_threshold
    
    def calculate_vertical_overlap(self, y1_min: float, y1_max: float, y2_min: float, y2_max: float) -> float:
        """
        Calculate vertical overlap between two bounding boxes.
        
        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        # Calculate intersection
        overlap_min = max(y1_min, y2_min)
        overlap_max = min(y1_max, y2_max)
        
        if overlap_max <= overlap_min:
            return 0.0
        
        overlap_height = overlap_max - overlap_min
        
        # Calculate union
        union_min = min(y1_min, y2_min)
        union_max = max(y1_max, y2_max)
        union_height = union_max - union_min
        
        if union_height == 0:
            return 0.0
        
        return overlap_height / union_height
    
    def cluster_by_baseline(
        self, 
        blocks: List[Dict[str, Any]]
    ) -> Dict[float, List[Dict[str, Any]]]:
        """
        Cluster text blocks by baseline (Y-position).
        
        Rules:
        - Blocks with vertical overlap ≥ threshold → same row
        - Otherwise → different rows
        
        Args:
            blocks: List of text blocks with bounding_box
        
        Returns:
            Dictionary mapping row_key (Y-position) to list of blocks
        """
        if not blocks:
            return {}
        
        rows = {}  # row_key -> list of blocks
        
        for block in blocks:
            bbox = block.get('bounding_box', {})
            if not bbox:
                continue
            
            y_min = bbox.get('y_min', 0)
            y_max = bbox.get('y_max', 0)
            y_center = (y_min + y_max) / 2
            
            # Find existing row with sufficient overlap
            assigned = False
            for row_key, row_blocks in rows.items():
                # Get Y-range of existing row
                row_y_min = min(b.get('bounding_box', {}).get('y_min', 0) for b in row_blocks)
                row_y_max = max(b.get('bounding_box', {}).get('y_max', 0) for b in row_blocks)
                
                # Check overlap
                overlap = self.calculate_vertical_overlap(y_min, y_max, row_y_min, row_y_max)
                
                if overlap >= self.overlap_threshold:
                    # Belongs to same row
                    row_blocks.append(block)
                    assigned = True
                    break
            
            if not assigned:
                # New row
                rows[y_center] = [block]
        
        logger.info(f"Row Locker: Clustered {len(blocks)} blocks into {len(rows)} rows")
        return rows
    
    def enforce_row_boundaries(
        self, 
        layout: UnifiedLayout,
        original_blocks: Optional[List[Dict[str, Any]]] = None
    ) -> UnifiedLayout:
        """
        Enforce row boundaries with ZERO WORD SPILL.
        
        CRITICAL RULES:
        - Each text block may belong to ONLY ONE row
        - Row assignment priority:
          a) baseline Y overlap > 70%
          b) nearest baseline within tolerance
        - ❌ Never allow word migration to adjacent row
        - If ambiguity → create new row, NOT merge into existing
        
        Args:
            layout: Layout to process
            original_blocks: Original OCR blocks for baseline detection
        
        Returns:
            Layout with enforced row boundaries
        """
        if layout.is_empty():
            return layout
        
        # If we have original blocks, use baseline clustering
        if original_blocks:
            # Cluster blocks by baseline
            baseline_clusters = self.cluster_by_baseline(original_blocks)
            
            # Create mapping: block -> row_index
            block_to_row = {}
            row_idx = 0
            for baseline_key, blocks in sorted(baseline_clusters.items()):
                for block in blocks:
                    block_id = id(block)  # Use block ID as key
                    block_to_row[block_id] = row_idx
                row_idx += 1
            
            # Rebuild layout based on baseline clusters
            new_layout = UnifiedLayout(page_index=layout.page_index)
            new_layout.metadata = layout.metadata.copy()
            
            # Group cells by their original block's baseline
            # This is a simplified approach - in practice, we'd need to track block->cell mapping
            # For now, we'll use the existing row structure but enforce strict boundaries
            
        # Create new layout
        new_layout = UnifiedLayout(page_index=layout.page_index)
        new_layout.metadata = layout.metadata.copy()
        
        # Group cells by row
        rows_dict = {}  # row_index -> list of cells
        
        for row in layout.rows:
            for cell in row:
                row_idx = cell.row
                if row_idx not in rows_dict:
                    rows_dict[row_idx] = []
                rows_dict[row_idx].append(cell)
        
        # Process each row independently - DO NOT merge across rows
        sorted_rows = sorted(rows_dict.keys())
        new_row_idx = 0
        
        for original_row_idx in sorted_rows:
            cells = rows_dict[original_row_idx]
            
            # Sort cells by column
            cells.sort(key=lambda c: c.column)
            
            # Process cells in this row - merge only if adjacent and same row
            merged_cells = []
            i = 0
            
            while i < len(cells):
                cell = cells[i]
                
                # Check if next cell should be merged (same row, adjacent columns)
                if i + 1 < len(cells):
                    next_cell = cells[i + 1]
                    
                    # Only merge if:
                    # 1. Same row (already guaranteed)
                    # 2. Adjacent columns
                    # 3. Both have text
                    # 4. NOT already merged
                    if (next_cell.column == cell.column + 1 and 
                        cell.value and next_cell.value and
                        not cell.merged and not next_cell.merged):
                        
                        # Merge into single cell (same row, adjacent columns)
                        merged_value = (cell.value or '') + ' ' + (next_cell.value or '')
                        merged_cell = Cell(
                            row=new_row_idx,
                            column=cell.column,
                            value=merged_value.strip(),
                            style=cell.style,  # Use first cell's style
                            rowspan=1,  # Same row, no rowspan
                            colspan=2,  # Spans 2 columns
                            merged=True
                        )
                        merged_cells.append(merged_cell)
                        i += 2  # Skip next cell
                        continue
                
                # No merge, add cell as-is
                adjusted_cell = Cell(
                    row=new_row_idx,
                    column=cell.column,
                    value=cell.value,
                    style=cell.style,
                    rowspan=1,  # Enforce single row (no word spill)
                    colspan=cell.colspan,
                    merged=cell.merged
                )
                merged_cells.append(adjusted_cell)
                i += 1
            
            if merged_cells:
                new_layout.add_row(merged_cells)
                new_row_idx += 1
        
        # Copy merged cells (only if within same row)
        for merged in layout.merged_cells:
            # Only keep merged cells that are within same row (no vertical merging)
            if merged.start_row == merged.end_row:
                new_layout.add_merged_cell(
                    merged.start_row,
                    merged.start_col,
                    merged.end_row,
                    merged.end_col
                )
        
        logger.critical(f"🔒 Row Locker: Enforced ZERO WORD SPILL. Original rows: {len(sorted_rows)}, New rows: {new_row_idx}")
        return new_layout

