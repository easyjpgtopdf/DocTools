"""
Geometry Reconstructor for Document AI Tables

When Document AI provides tables but cells lack layout/bounding boxes,
this module reconstructs missing geometry using:
- Neighboring cells
- Grid inference
- Block-based fallback
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class GeometryReconstructor:
    """
    Reconstructs missing bounding boxes for Document AI table cells.
    
    Handles cases where:
    - cell.layout is missing
    - cell.layout exists but bounding_poly is missing
    - Bounding boxes are partial/malformed
    """
    
    def __init__(self):
        self.min_cell_width = 0.05  # 5% of page width
        self.min_cell_height = 0.02  # 2% of page height
        
    def reconstruct_table_geometry(
        self,
        table: Any,
        blocks: List[Dict[str, Any]],
        document_text: str
    ) -> Dict[str, Any]:
        """
        Main entry point: reconstruct geometry for table cells.
        
        Args:
            table: Document AI table object
            blocks: OCR blocks with bounding boxes
            document_text: Full document text
            
        Returns:
            Dictionary with enhanced cell geometries
        """
        logger.info("GEOMETRY RECONSTRUCTOR: Starting reconstruction")
        
        # Extract table structure
        structure = self._analyze_table_structure(table)
        logger.info(f"Table structure: {structure['rows']} rows × {structure['cols']} columns")
        
        # Build cell map with text matching
        cell_map = self._build_cell_text_map(table, document_text)
        logger.info(f"Built cell map with {len(cell_map)} cells")
        
        # Match cells to blocks
        matched_geometries = self._match_cells_to_blocks(cell_map, blocks)
        logger.info(f"Matched {len(matched_geometries)} cells to blocks")
        
        # Fill gaps using grid inference
        complete_geometries = self._fill_geometry_gaps(
            matched_geometries,
            structure
        )
        logger.info(f"Filled gaps, total cells: {len(complete_geometries)}")
        
        return {
            'cell_geometries': complete_geometries,
            'structure': structure,
            'matched_count': len(matched_geometries),
            'total_count': len(complete_geometries)
        }
    
    def _analyze_table_structure(self, table: Any) -> Dict[str, Any]:
        """Analyze table to get row/column counts"""
        rows = 0
        cols = 0
        has_header = False
        
        if hasattr(table, 'header_rows') and table.header_rows:
            has_header = True
            for header_row in table.header_rows:
                rows += 1
                if hasattr(header_row, 'cells') and header_row.cells:
                    cols = max(cols, len(header_row.cells))
        
        if hasattr(table, 'body_rows') and table.body_rows:
            for body_row in table.body_rows:
                rows += 1
                if hasattr(body_row, 'cells') and body_row.cells:
                    cols = max(cols, len(body_row.cells))
        
        return {
            'rows': rows,
            'cols': cols,
            'has_header': has_header
        }
    
    def _build_cell_text_map(
        self,
        table: Any,
        document_text: str
    ) -> Dict[Tuple[int, int], Dict[str, Any]]:
        """
        Build map of (row, col) -> cell data including text.
        """
        cell_map = {}
        row_idx = 0
        
        # Process header rows
        if hasattr(table, 'header_rows') and table.header_rows:
            for header_row in table.header_rows:
                if hasattr(header_row, 'cells') and header_row.cells:
                    for col_idx, cell in enumerate(header_row.cells):
                        text = self._extract_cell_text(cell, document_text)
                        bbox = self._extract_cell_bbox(cell)
                        
                        cell_map[(row_idx, col_idx)] = {
                            'text': text,
                            'bbox': bbox,
                            'is_header': True,
                            'has_geometry': bbox is not None
                        }
                row_idx += 1
        
        # Process body rows
        if hasattr(table, 'body_rows') and table.body_rows:
            for body_row in table.body_rows:
                if hasattr(body_row, 'cells') and body_row.cells:
                    for col_idx, cell in enumerate(body_row.cells):
                        text = self._extract_cell_text(cell, document_text)
                        bbox = self._extract_cell_bbox(cell)
                        
                        cell_map[(row_idx, col_idx)] = {
                            'text': text,
                            'bbox': bbox,
                            'is_header': False,
                            'has_geometry': bbox is not None
                        }
                row_idx += 1
        
        return cell_map
    
    def _extract_cell_text(self, cell: Any, document_text: str) -> str:
        """Extract text from cell using text_anchor"""
        if not hasattr(cell, 'layout'):
            return ''
        
        layout = cell.layout
        if not hasattr(layout, 'text_anchor'):
            return ''
        
        text_anchor = layout.text_anchor
        if not hasattr(text_anchor, 'text_segments'):
            return ''
        
        text_parts = []
        for segment in text_anchor.text_segments:
            if hasattr(segment, 'start_index') and hasattr(segment, 'end_index'):
                start = int(segment.start_index) if segment.start_index else 0
                end = int(segment.end_index) if segment.end_index else 0
                if 0 <= start < len(document_text) and start < end <= len(document_text):
                    text_parts.append(document_text[start:end])
        
        return ' '.join(text_parts).strip()
    
    def _extract_cell_bbox(self, cell: Any) -> Optional[Dict[str, float]]:
        """Extract bounding box from cell if available"""
        if not hasattr(cell, 'layout'):
            return None
        
        layout = cell.layout
        if not hasattr(layout, 'bounding_poly'):
            return None
        
        bounding_poly = layout.bounding_poly
        if not hasattr(bounding_poly, 'normalized_vertices'):
            return None
        
        vertices = bounding_poly.normalized_vertices
        if not vertices or len(vertices) < 2:
            return None
        
        # Extract min/max coordinates
        x_coords = [v.x for v in vertices if hasattr(v, 'x')]
        y_coords = [v.y for v in vertices if hasattr(v, 'y')]
        
        if not x_coords or not y_coords:
            return None
        
        return {
            'x_min': min(x_coords),
            'x_max': max(x_coords),
            'y_min': min(y_coords),
            'y_max': max(y_coords),
            'x_center': sum(x_coords) / len(x_coords),
            'y_center': sum(y_coords) / len(y_coords)
        }
    
    def _match_cells_to_blocks(
        self,
        cell_map: Dict[Tuple[int, int], Dict[str, Any]],
        blocks: List[Dict[str, Any]]
    ) -> Dict[Tuple[int, int], Dict[str, float]]:
        """
        Match cells without geometry to OCR blocks by text similarity.
        """
        matched = {}
        
        for cell_key, cell_data in cell_map.items():
            if cell_data['has_geometry'] and cell_data['bbox']:
                # Already has geometry
                matched[cell_key] = cell_data['bbox']
                continue
            
            # Try to find matching block by text
            cell_text = cell_data['text'].strip()
            if not cell_text:
                continue
            
            best_match = None
            best_score = 0.0
            
            for block in blocks:
                block_text = block.get('text', '').strip()
                if not block_text:
                    continue
                
                # Simple text similarity
                score = self._text_similarity(cell_text, block_text)
                if score > best_score and score > 0.7:  # 70% threshold
                    best_score = score
                    best_match = block.get('bounding_box')
            
            if best_match:
                matched[cell_key] = best_match
                logger.debug(f"Matched cell {cell_key} to block (score: {best_score:.2f})")
        
        return matched
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity measure"""
        if not text1 or not text2:
            return 0.0
        
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        if text1 in text2 or text2 in text1:
            return 0.8
        
        # Word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1 & words2)
        total = len(words1 | words2)
        
        return overlap / total if total > 0 else 0.0
    
    def _fill_geometry_gaps(
        self,
        matched: Dict[Tuple[int, int], Dict[str, float]],
        structure: Dict[str, Any]
    ) -> Dict[Tuple[int, int], Dict[str, float]]:
        """
        Fill missing geometries using grid inference from neighboring cells.
        """
        rows = structure['rows']
        cols = structure['cols']
        
        if not matched:
            logger.warning("No matched cells to infer from")
            return {}
        
        # Calculate average cell dimensions
        widths = []
        heights = []
        for bbox in matched.values():
            widths.append(bbox['x_max'] - bbox['x_min'])
            heights.append(bbox['y_max'] - bbox['y_min'])
        
        avg_width = sum(widths) / len(widths) if widths else self.min_cell_width
        avg_height = sum(heights) / len(heights) if heights else self.min_cell_height
        
        logger.debug(f"Average cell size: {avg_width:.4f} × {avg_height:.4f}")
        
        # Build complete grid
        complete = dict(matched)  # Start with matched cells
        
        for r in range(rows):
            for c in range(cols):
                if (r, c) in complete:
                    continue  # Already has geometry
                
                # Try to infer from neighbors
                inferred_bbox = self._infer_bbox_from_neighbors(
                    r, c, complete, avg_width, avg_height, rows, cols
                )
                
                if inferred_bbox:
                    complete[(r, c)] = inferred_bbox
                    logger.debug(f"Inferred geometry for cell ({r},{c})")
        
        return complete
    
    def _infer_bbox_from_neighbors(
        self,
        row: int,
        col: int,
        grid: Dict[Tuple[int, int], Dict[str, float]],
        avg_width: float,
        avg_height: float,
        max_rows: int,
        max_cols: int
    ) -> Optional[Dict[str, float]]:
        """
        Infer bounding box for a cell from its neighbors.
        """
        # Try left neighbor
        if col > 0 and (row, col - 1) in grid:
            left_bbox = grid[(row, col - 1)]
            return {
                'x_min': left_bbox['x_max'],
                'x_max': left_bbox['x_max'] + avg_width,
                'y_min': left_bbox['y_min'],
                'y_max': left_bbox['y_max'],
                'x_center': left_bbox['x_max'] + avg_width / 2,
                'y_center': (left_bbox['y_min'] + left_bbox['y_max']) / 2
            }
        
        # Try above neighbor
        if row > 0 and (row - 1, col) in grid:
            above_bbox = grid[(row - 1, col)]
            return {
                'x_min': above_bbox['x_min'],
                'x_max': above_bbox['x_max'],
                'y_min': above_bbox['y_max'],
                'y_max': above_bbox['y_max'] + avg_height,
                'x_center': (above_bbox['x_min'] + above_bbox['x_max']) / 2,
                'y_center': above_bbox['y_max'] + avg_height / 2
            }
        
        # Try diagonal (top-left)
        if row > 0 and col > 0 and (row - 1, col - 1) in grid:
            diag_bbox = grid[(row - 1, col - 1)]
            return {
                'x_min': diag_bbox['x_max'],
                'x_max': diag_bbox['x_max'] + avg_width,
                'y_min': diag_bbox['y_max'],
                'y_max': diag_bbox['y_max'] + avg_height,
                'x_center': diag_bbox['x_max'] + avg_width / 2,
                'y_center': diag_bbox['y_max'] + avg_height / 2
            }
        
        # No neighbors available
        return None

