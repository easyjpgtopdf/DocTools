"""
Cell Normalization Layer

CRITICAL PRE-PROCESSING STEP:
Groups OCR text blocks into logical cells BEFORE any row/column detection.

Ensures:
- Each text block belongs to exactly ONE logical cell
- Multi-line text is merged correctly
- Numeric sequences stay in one cell
- Cell structure is stable and believable
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LogicalCell:
    """A logical cell composed of one or more text blocks"""
    blocks: List[Dict[str, Any]]  # OCR blocks that form this cell
    merged_text: str
    bbox: Dict[str, float]  # Combined bounding box
    is_numeric: bool
    is_header: bool
    confidence: float
    cell_id: int  # Unique identifier
    
    @property
    def x_center(self) -> float:
        return (self.bbox['x_min'] + self.bbox['x_max']) / 2
    
    @property
    def y_center(self) -> float:
        return (self.bbox['y_min'] + self.bbox['y_max']) / 2
    
    @property
    def x_range(self) -> Tuple[float, float]:
        return (self.bbox['x_min'], self.bbox['x_max'])
    
    @property
    def y_range(self) -> Tuple[float, float]:
        return (self.bbox['y_min'], self.bbox['y_max'])


class CellNormalizer:
    """
    Cell Normalization Layer
    
    Converts raw OCR blocks into logical cells with strict ownership rules.
    This is the FIRST step before any row/column detection.
    """
    
    def __init__(self):
        self.x_overlap_threshold = 0.70  # 70% X-overlap = same cell
        self.line_height_multiplier = 1.5  # Y-distance ≤ 1.5× line height = same cell
        self.numeric_threshold = 0.6  # 60% digits = numeric sequence
        
    def normalize_to_cells(
        self,
        blocks: List[Dict[str, Any]],
        page_width: float = 1.0,
        page_height: float = 1.0
    ) -> List[LogicalCell]:
        """
        Main entry point: Convert OCR blocks to logical cells.
        
        Args:
            blocks: List of OCR blocks with text and bounding_box
            page_width: Page width for relative calculations
            page_height: Page height for relative calculations
            
        Returns:
            List of LogicalCell objects with strict ownership
        """
        logger.info("=" * 80)
        logger.info("CELL NORMALIZER: Grouping blocks into logical cells")
        logger.info("=" * 80)
        
        if not blocks:
            logger.warning("No blocks to normalize")
            return []
        
        # Step 1: Filter and validate blocks
        valid_blocks = self._filter_valid_blocks(blocks)
        logger.info(f"Valid blocks: {len(valid_blocks)} / {len(blocks)}")
        
        if not valid_blocks:
            logger.warning("No valid blocks after filtering")
            return []
        
        # Step 2: Calculate average line height for merging threshold
        avg_line_height = self._calculate_avg_line_height(valid_blocks)
        logger.info(f"Average line height: {avg_line_height:.4f}")
        
        # Step 3: Group blocks into logical cells using strict rules
        logical_cells = self._group_blocks_into_cells(valid_blocks, avg_line_height)
        logger.info(f"Grouped into {len(logical_cells)} logical cells")
        
        # Step 4: Validate cell integrity
        validation_passed = self._validate_cell_integrity(logical_cells, valid_blocks)
        
        if not validation_passed:
            logger.error("Cell integrity validation FAILED!")
            # Fallback: treat each block as its own cell
            logger.warning("Fallback: treating each block as separate cell")
            logical_cells = self._fallback_one_block_per_cell(valid_blocks)
        
        logger.info("=" * 80)
        logger.info(f"CELL NORMALIZATION COMPLETE: {len(logical_cells)} cells created")
        logger.info("=" * 80)
        
        return logical_cells
    
    def _filter_valid_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter blocks that have required fields"""
        valid = []
        for block in blocks:
            # Must have text
            if not block.get('text', '').strip():
                continue
            
            # Must have bounding box
            bbox = block.get('bounding_box')
            if not bbox:
                continue
            
            # Must have all bbox coordinates
            required_keys = ['x_min', 'x_max', 'y_min', 'y_max']
            if not all(k in bbox for k in required_keys):
                continue
            
            # Valid bbox (not degenerate)
            if bbox['x_max'] <= bbox['x_min'] or bbox['y_max'] <= bbox['y_min']:
                continue
            
            valid.append(block)
        
        return valid
    
    def _calculate_avg_line_height(self, blocks: List[Dict[str, Any]]) -> float:
        """Calculate average line height from blocks"""
        heights = []
        for block in blocks:
            bbox = block['bounding_box']
            height = bbox['y_max'] - bbox['y_min']
            if height > 0:
                heights.append(height)
        
        if not heights:
            return 0.02  # Default 2% of page height
        
        return sum(heights) / len(heights)
    
    def _group_blocks_into_cells(
        self,
        blocks: List[Dict[str, Any]],
        avg_line_height: float
    ) -> List[LogicalCell]:
        """
        Group blocks into logical cells using strict ownership rules.
        
        Rules:
        1. Blocks are in same cell if X-overlap >= 70% AND Y-distance <= threshold
        2. Each block belongs to exactly ONE cell
        3. Numeric sequences are forced to merge
        4. Hindi multi-line text is merged
        """
        # Sort blocks by position (top-to-bottom, left-to-right)
        sorted_blocks = sorted(
            blocks,
            key=lambda b: (b['bounding_box']['y_min'], b['bounding_box']['x_min'])
        )
        
        # Union-Find data structure for grouping
        block_to_cell_id = {}  # block index -> cell ID
        cell_groups = []  # List of lists of block indices
        next_cell_id = 0
        
        for i, block in enumerate(sorted_blocks):
            if i in block_to_cell_id:
                continue  # Already assigned
            
            # Start new cell with this block
            current_cell = [i]
            block_to_cell_id[i] = next_cell_id
            
            # Try to merge with subsequent blocks
            for j in range(i + 1, len(sorted_blocks)):
                if j in block_to_cell_id:
                    continue  # Already assigned to another cell
                
                # Check if block j should merge with current cell
                if self._should_merge_into_cell(
                    sorted_blocks, current_cell, j, avg_line_height
                ):
                    current_cell.append(j)
                    block_to_cell_id[j] = next_cell_id
            
            cell_groups.append(current_cell)
            next_cell_id += 1
        
        # Build LogicalCell objects
        logical_cells = []
        for cell_id, block_indices in enumerate(cell_groups):
            cell_blocks = [sorted_blocks[i] for i in block_indices]
            logical_cell = self._create_logical_cell(cell_blocks, cell_id)
            logical_cells.append(logical_cell)
        
        return logical_cells
    
    def _should_merge_into_cell(
        self,
        all_blocks: List[Dict[str, Any]],
        current_cell_indices: List[int],
        candidate_idx: int,
        avg_line_height: float
    ) -> bool:
        """
        Determine if candidate block should merge into current cell.
        
        Checks against ALL blocks in current cell for consistency.
        """
        candidate = all_blocks[candidate_idx]
        candidate_bbox = candidate['bounding_box']
        candidate_text = candidate['text'].strip()
        
        # Check against each block in current cell
        for cell_idx in current_cell_indices:
            cell_block = all_blocks[cell_idx]
            cell_bbox = cell_block['bounding_box']
            cell_text = cell_block['text'].strip()
            
            # Rule 1: X-overlap check (must overlap >= 70%)
            x_overlap = self._calculate_x_overlap(candidate_bbox, cell_bbox)
            if x_overlap < self.x_overlap_threshold:
                continue  # Not enough X-overlap with this cell block
            
            # Rule 2: Y-distance check (must be within threshold)
            y_distance = abs(
                (candidate_bbox['y_min'] + candidate_bbox['y_max']) / 2 -
                (cell_bbox['y_min'] + cell_bbox['y_max']) / 2
            )
            threshold = avg_line_height * self.line_height_multiplier
            
            if y_distance <= threshold:
                # Additional rule: If both are numeric, force merge
                if self._is_numeric(candidate_text) and self._is_numeric(cell_text):
                    logger.debug(f"Merging numeric blocks: '{cell_text[:20]}' + '{candidate_text[:20]}'")
                    return True
                
                # Additional rule: If same language script, likely multi-line
                if self._same_script(candidate_text, cell_text):
                    return True
        
        return False
    
    def _calculate_x_overlap(
        self,
        bbox1: Dict[str, float],
        bbox2: Dict[str, float]
    ) -> float:
        """Calculate X-axis overlap ratio (0.0 to 1.0)"""
        x1_min, x1_max = bbox1['x_min'], bbox1['x_max']
        x2_min, x2_max = bbox2['x_min'], bbox2['x_max']
        
        # Calculate overlap
        overlap_min = max(x1_min, x2_min)
        overlap_max = min(x1_max, x2_max)
        
        if overlap_max <= overlap_min:
            return 0.0  # No overlap
        
        overlap_width = overlap_max - overlap_min
        
        # Calculate overlap ratio relative to smaller box
        width1 = x1_max - x1_min
        width2 = x2_max - x2_min
        min_width = min(width1, width2)
        
        if min_width == 0:
            return 0.0
        
        return overlap_width / min_width
    
    def _is_numeric(self, text: str) -> bool:
        """Check if text is primarily numeric (IDs, Aadhaar, phone numbers)"""
        if not text:
            return False
        
        # Remove common separators
        cleaned = text.replace(' ', '').replace('-', '').replace('/', '').replace('.', '')
        if not cleaned:
            return False
        
        digit_count = sum(c.isdigit() for c in cleaned)
        digit_ratio = digit_count / len(cleaned)
        
        return digit_ratio >= self.numeric_threshold
    
    def _same_script(self, text1: str, text2: str) -> bool:
        """Check if two texts use the same script (Devanagari, Latin, etc.)"""
        if not text1 or not text2:
            return False
        
        def get_script(text: str) -> str:
            """Detect primary script"""
            # Devanagari range
            devanagari_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
            # Latin
            latin_count = sum(1 for c in text if ('a' <= c.lower() <= 'z'))
            # Digit
            digit_count = sum(1 for c in text if c.isdigit())
            
            total = len(text)
            if total == 0:
                return 'unknown'
            
            if devanagari_count / total > 0.3:
                return 'devanagari'
            if latin_count / total > 0.3:
                return 'latin'
            if digit_count / total > 0.5:
                return 'numeric'
            
            return 'mixed'
        
        script1 = get_script(text1)
        script2 = get_script(text2)
        
        return script1 == script2 and script1 != 'unknown'
    
    def _create_logical_cell(
        self,
        blocks: List[Dict[str, Any]],
        cell_id: int
    ) -> LogicalCell:
        """Create a LogicalCell from a group of blocks"""
        # Sort blocks top-to-bottom, left-to-right for reading order
        sorted_blocks = sorted(
            blocks,
            key=lambda b: (b['bounding_box']['y_min'], b['bounding_box']['x_min'])
        )
        
        # Merge text with space separator
        merged_text = ' '.join(b['text'].strip() for b in sorted_blocks if b['text'].strip())
        
        # Calculate combined bounding box
        all_x_mins = [b['bounding_box']['x_min'] for b in sorted_blocks]
        all_x_maxs = [b['bounding_box']['x_max'] for b in sorted_blocks]
        all_y_mins = [b['bounding_box']['y_min'] for b in sorted_blocks]
        all_y_maxs = [b['bounding_box']['y_max'] for b in sorted_blocks]
        
        combined_bbox = {
            'x_min': min(all_x_mins),
            'x_max': max(all_x_maxs),
            'y_min': min(all_y_mins),
            'y_max': max(all_y_maxs)
        }
        
        # Determine if header (heuristic: larger font or bold)
        is_header = any(
            b.get('font_size', 0) > 12 or b.get('is_bold', False)
            for b in sorted_blocks
        )
        
        # Average confidence
        avg_confidence = sum(b.get('confidence', 1.0) for b in sorted_blocks) / len(sorted_blocks)
        
        # Check if numeric
        is_numeric = self._is_numeric(merged_text)
        
        return LogicalCell(
            blocks=sorted_blocks,
            merged_text=merged_text,
            bbox=combined_bbox,
            is_numeric=is_numeric,
            is_header=is_header,
            confidence=avg_confidence,
            cell_id=cell_id
        )
    
    def _validate_cell_integrity(
        self,
        cells: List[LogicalCell],
        original_blocks: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate that cell normalization was successful.
        
        Checks:
        1. Every block is in exactly one cell
        2. No cell is empty
        3. Total blocks match
        """
        # Count blocks in cells
        total_blocks_in_cells = sum(len(cell.blocks) for cell in cells)
        
        if total_blocks_in_cells != len(original_blocks):
            logger.error(f"Block count mismatch: {total_blocks_in_cells} in cells vs {len(original_blocks)} original")
            return False
        
        # Check for empty cells
        empty_cells = [cell for cell in cells if not cell.merged_text.strip()]
        if empty_cells:
            logger.warning(f"Found {len(empty_cells)} empty cells (may be whitespace-only)")
        
        # Check for duplicate blocks (same block in multiple cells)
        block_ids_seen = set()
        for cell in cells:
            for block in cell.blocks:
                block_id = id(block)  # Use object identity
                if block_id in block_ids_seen:
                    logger.error(f"Duplicate block found in multiple cells!")
                    return False
                block_ids_seen.add(block_id)
        
        logger.info("✓ Cell integrity validation PASSED")
        return True
    
    def _fallback_one_block_per_cell(
        self,
        blocks: List[Dict[str, Any]]
    ) -> List[LogicalCell]:
        """
        Fallback: treat each block as its own cell.
        Used when grouping fails validation.
        """
        logger.warning("Using fallback: one block = one cell")
        
        cells = []
        for i, block in enumerate(blocks):
            cell = LogicalCell(
                blocks=[block],
                merged_text=block['text'].strip(),
                bbox=block['bounding_box'].copy(),
                is_numeric=self._is_numeric(block['text']),
                is_header=block.get('font_size', 0) > 12 or block.get('is_bold', False),
                confidence=block.get('confidence', 1.0),
                cell_id=i
            )
            cells.append(cell)
        
        return cells

