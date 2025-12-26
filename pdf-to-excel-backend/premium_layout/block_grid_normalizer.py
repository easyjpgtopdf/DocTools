"""
Universal Block-Based Grid Normalization

Pre-processes LOGICAL CELLS (not raw blocks) to create normalized grid structure
BEFORE any mode-specific processing.

CRITICAL: Works with LogicalCell objects from CellNormalizer.
This runs for TABLE_STRICT, TABLE_VISUAL, and KEY_VALUE modes.
"""

import logging
from typing import List, Dict, Any, Tuple, Set, Optional
from dataclasses import dataclass

from .cell_normalizer import LogicalCell

logger = logging.getLogger(__name__)


@dataclass
class NormalizedBlock:
    """A text block with normalized position"""
    text: str
    original_bbox: Dict[str, float]
    normalized_row: int
    normalized_col: int
    row_band: float  # Y-center of the row band this belongs to
    col_band: float  # X-center of the column band this belongs to
    confidence: float
    is_numeric: bool
    font_size: float = 10.0
    is_bold: bool = False


@dataclass
class GridStructure:
    """Normalized grid structure from blocks"""
    blocks: List[NormalizedBlock]
    row_bands: List[float]  # Y-centers of detected row bands
    col_bands: List[float]  # X-centers of detected column bands
    grid: Dict[Tuple[int, int], List[NormalizedBlock]]  # (row, col) -> blocks
    metadata: Dict[str, Any]


class BlockGridNormalizer:
    """
    Universal grid normalizer for OCR blocks.
    
    Handles:
    - Column band detection (consensus-based)
    - Row band detection (body-first)
    - Position normalization
    - Cell boundary determination
    """
    
    def __init__(self):
        self.min_row_separation = 0.01  # 1% of page height minimum
        self.min_col_separation = 0.03  # 3% of page width minimum
        self.row_tolerance = 0.015      # 1.5% for Y-snapping
        self.col_tolerance = 0.04       # 4% for X-snapping
        self.consensus_threshold = 0.6  # 60% of rows must have column
        
    def normalize_cells(
        self,
        cells: List[LogicalCell],
        page_width: float = 1.0,
        page_height: float = 1.0
    ) -> GridStructure:
        """
        Main entry point: normalize logical cells into grid structure.
        
        CRITICAL: Works with LogicalCell objects, not raw blocks.
        Each cell has already been validated to have exactly one ownership.
        
        Args:
            cells: List of LogicalCell objects (from CellNormalizer)
            page_width: Page width for relative calculations
            page_height: Page height for relative calculations
            
        Returns:
            GridStructure with normalized positions
        """
        logger.info("=" * 80)
        logger.info("BLOCK GRID NORMALIZER: Starting normalization (using logical cells)")
        logger.info("=" * 80)
        
        if not cells:
            logger.warning("No cells provided")
            return GridStructure([], [], [], {}, {})
        
        logger.info(f"Processing {len(cells)} logical cells")
        
        # Step 1: Detect row bands from cells (body-first approach)
        row_bands = self._detect_row_bands_from_cells(cells)
        logger.info(f"Detected {len(row_bands)} row bands")
        
        # Step 2: Detect column bands (consensus-based)
        col_bands = self._detect_column_bands_from_cells(cells, row_bands)
        logger.info(f"Detected {len(col_bands)} column bands (consensus-based)")
        
        # Step 3: Assign cells to grid
        normalized_blocks, grid = self._assign_cells_to_grid(
            cells, row_bands, col_bands
        )
        logger.info(f"Assigned {len(cells)} cells to grid")
        
        # NOTE: No need to merge - cells are already merged by CellNormalizer
        
        metadata = {
            'row_count': len(row_bands),
            'col_count': len(col_bands),
            'total_cells': len(cells),
            'grid_cells': len(grid),
            'normalization_method': 'cell_based_consensus_body_first'
        }
        
        logger.info("=" * 80)
        logger.info(f"NORMALIZATION COMPLETE: {len(row_bands)} rows × {len(col_bands)} cols")
        logger.info("=" * 80)
        
        return GridStructure(
            blocks=normalized_blocks,
            row_bands=row_bands,
            col_bands=col_bands,
            grid=grid,
            metadata=metadata
        )
    
    def _detect_row_bands_from_cells(self, cells: List[LogicalCell]) -> List[float]:
        """
        Detect row bands using Y-position clustering from logical cells.
        BODY-FIRST: focuses on majority content, not headers.
        """
        # Extract Y-centers from cells
        y_centers = [cell.y_center for cell in cells]
        
        y_centers.sort()
        
        # Cluster Y-positions into bands
        bands = []
        current_band = [y_centers[0]]
        
        for y in y_centers[1:]:
            if y - current_band[-1] <= self.row_tolerance:
                # Same band
                current_band.append(y)
            else:
                # New band
                if len(current_band) > 0:
                    bands.append(sum(current_band) / len(current_band))
                current_band = [y]
        
        # Don't forget last band
        if current_band:
            bands.append(sum(current_band) / len(current_band))
        
        logger.debug(f"Row bands detected: {len(bands)} bands from {len(y_centers)} blocks")
        return bands
    
    def _detect_column_bands_from_cells(
        self,
        cells: List[LogicalCell],
        row_bands: List[float]
    ) -> List[float]:
        """
        Detect column bands using consensus-based approach from logical cells.
        A column must appear in >= 60% of rows to be accepted.
        """
        if not row_bands:
            return []
        
        # Assign cells to rows first
        row_cells: Dict[int, List[LogicalCell]] = {i: [] for i in range(len(row_bands))}
        
        for cell in cells:
            y_center = cell.y_center
            
            # Find nearest row
            row_idx = min(
                range(len(row_bands)),
                key=lambda i: abs(row_bands[i] - y_center)
            )
            
            if abs(row_bands[row_idx] - y_center) <= self.row_tolerance:
                row_cells[row_idx].append(cell)
        
        # Extract X-positions from each row
        all_x_positions = []
        for row_idx, row_cells_list in row_cells.items():
            if not row_cells_list:
                continue
            
            row_x = [c.x_center for c in row_cells_list]
            all_x_positions.append(sorted(set(row_x)))
        
        if not all_x_positions:
            return []
        
        # Cluster X-positions across all rows
        all_x_flat = []
        for row_x in all_x_positions:
            all_x_flat.extend(row_x)
        all_x_flat.sort()
        
        # Cluster into column bands
        col_candidates = []
        current_cluster = [all_x_flat[0]]
        
        for x in all_x_flat[1:]:
            if x - current_cluster[-1] <= self.col_tolerance:
                current_cluster.append(x)
            else:
                if current_cluster:
                    col_candidates.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [x]
        
        if current_cluster:
            col_candidates.append(sum(current_cluster) / len(current_cluster))
        
        # CONSENSUS CHECK: Keep only columns that appear in >= 60% of rows
        total_rows = len([r for r in row_cells.values() if r])
        threshold = int(total_rows * self.consensus_threshold)
        
        accepted_cols = []
        for col_x in col_candidates:
            rows_with_col = 0
            for row_cells_list in row_cells.values():
                if not row_cells_list:
                    continue
                # Check if this row has a cell near this column
                for cell in row_cells_list:
                    if abs(cell.x_center - col_x) <= self.col_tolerance:
                        rows_with_col += 1
                        break
            
            if rows_with_col >= threshold:
                accepted_cols.append(col_x)
        
        logger.debug(f"Column consensus: {len(accepted_cols)} / {len(col_candidates)} candidates passed (threshold: {threshold} rows)")
        
        # Ensure at least 1 column
        if not accepted_cols and col_candidates:
            accepted_cols = [col_candidates[0]]
        
        return sorted(accepted_cols)
    
    def _assign_cells_to_grid(
        self,
        cells: List[LogicalCell],
        row_bands: List[float],
        col_bands: List[float]
    ) -> Tuple[List[NormalizedBlock], Dict[Tuple[int, int], List[NormalizedBlock]]]:
        """
        Assign each logical cell to a grid position (row, col).
        
        CRITICAL: Each cell gets exactly ONE (row, col) coordinate.
        """
        if not row_bands or not col_bands:
            return [], {}
        
        normalized_blocks = []
        grid: Dict[Tuple[int, int], List[NormalizedBlock]] = {}
        
        for cell in cells:
            y_center = cell.y_center
            x_center = cell.x_center
            
            # Find nearest row
            row_idx = min(
                range(len(row_bands)),
                key=lambda i: abs(row_bands[i] - y_center)
            )
            
            # Find nearest column
            col_idx = min(
                range(len(col_bands)),
                key=lambda i: abs(col_bands[i] - x_center)
            )
            
            # Create normalized block from logical cell
            norm_block = NormalizedBlock(
                text=cell.merged_text,
                original_bbox=cell.bbox,
                normalized_row=row_idx,
                normalized_col=col_idx,
                row_band=row_bands[row_idx],
                col_band=col_bands[col_idx],
                confidence=cell.confidence,
                is_numeric=cell.is_numeric,
                font_size=max((b.get('font_size', 10.0) for b in cell.blocks), default=10.0),
                is_bold=any(b.get('is_bold', False) for b in cell.blocks)
            )
            
            normalized_blocks.append(norm_block)
            
            # Add to grid
            cell_key = (row_idx, col_idx)
            if cell_key not in grid:
                grid[cell_key] = []
            grid[cell_key].append(norm_block)
        
        return normalized_blocks, grid
    
    def _is_numeric(self, text: str) -> bool:
        """Check if text is primarily numeric (IDs, phone, Aadhaar, etc.)"""
        if not text:
            return False
        # Remove common separators
        cleaned = text.replace(' ', '').replace('-', '').replace('/', '')
        if not cleaned:
            return False
        digit_ratio = sum(c.isdigit() for c in cleaned) / len(cleaned)
        return digit_ratio >= 0.7

