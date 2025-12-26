"""
Heuristic Table Builder
Builds table structure from text and bounding boxes when native tables are not available.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from .unified_layout_model import UnifiedLayout, Cell, CellStyle, CellAlignment

logger = logging.getLogger(__name__)


class HeuristicTableBuilder:
    """Builds tables using heuristic methods based on text layout"""
    
    def __init__(self):
        """Initialize table builder"""
        # Tolerance values for normalized coordinates (0-1 range)
        # For normalized: 0.01 = 1% of page width/height
        # Increased tolerance for better column detection
        self.y_tolerance = 0.015  # Normalized tolerance for grouping by Y-axis (1.5% of page height)
        self.x_tolerance = 0.02  # Normalized tolerance for grouping by X-axis (2% of page width)
        self.column_detection_enabled = True  # Enable advanced column detection
        self.alignment_clustering_enabled = True  # Enable alignment-based clustering
    
    def build_from_document(
        self,
        document: Any,
        document_text: str = '',
        doc_type: str = 'unknown'
    ) -> UnifiedLayout:
        """
        Build unified layout from Document AI document.
        
        Args:
            document: Document AI Document object
            document_text: Extracted text
            doc_type: Document type (for specialized handling)
            
        Returns:
            UnifiedLayout object
        """
        layout = UnifiedLayout()
        
        if not hasattr(document, 'pages') or not document.pages:
            logger.warning("No pages found in document")
            return layout
        
        # Process each page
        for page_idx, page in enumerate(document.pages):
            page_layout = self._build_from_page(page, document_text, doc_type, page_idx)
            
            # Merge page layouts
            row_offset = layout.get_max_row()
            for row in page_layout.rows:
                adjusted_row = []
                for cell in row:
                    adjusted_cell = Cell(
                        row=cell.row + row_offset,
                        column=cell.column,
                        value=cell.value,
                        style=cell.style,
                        rowspan=cell.rowspan,
                        colspan=cell.colspan,
                        merged=cell.merged
                    )
                    adjusted_row.append(adjusted_cell)
                layout.add_row(adjusted_row)
            
            # Adjust merged cells
            for merged in page_layout.merged_cells:
                layout.add_merged_cell(
                    merged.start_row + row_offset,
                    merged.start_col,
                    merged.end_row + row_offset,
                    merged.end_col
                )
        
        logger.info(f"Built layout with {layout.get_max_row()} rows and {layout.get_max_column()} columns")
        return layout
    
    def _build_from_page(
        self,
        page: Any,
        document_text: str,
        doc_type: str,
        page_idx: int,
        text_blocks: Optional[List[Dict]] = None,
        form_fields: Optional[List[Dict]] = None
    ) -> UnifiedLayout:
        """Build layout from a single page"""
        layout = UnifiedLayout(page_index=page_idx)
        
        # Extract text blocks with bounding boxes if not provided
        if text_blocks is None:
            text_blocks = self._extract_text_blocks(page, document_text)
        
        if not text_blocks:
            logger.warning(f"No text blocks found on page {page_idx + 1}")
            return layout
        
        # Group by document type
        if doc_type == 'resume':
            layout = self._build_resume_layout(text_blocks)
        elif doc_type == 'certificate':
            layout = self._build_certificate_layout(text_blocks)
        elif doc_type == 'id_card':
            layout = self._build_id_card_layout(text_blocks)
        elif doc_type == 'letter':
            layout = self._build_letter_layout(text_blocks)
        elif doc_type in ['invoice', 'bank', 'bill', 'statement']:
            layout = self._build_statement_layout(text_blocks)
        else:
            # Generic layout - use this for table-like documents
            layout = self._build_generic_layout(text_blocks)
        
        # Ensure page_index is set
        layout.page_index = page_idx
        return layout
    
    def _extract_text_blocks(self, page: Any, document_text: str) -> List[Dict[str, Any]]:
        """Extract text blocks with bounding box information"""
        text_blocks = []
        
        # Method 1: Try paragraphs with layouts (preferred)
        if hasattr(page, 'paragraphs') and page.paragraphs:
            for para in page.paragraphs:
                if not hasattr(para, 'layout'):
                    continue
                
                layout = para.layout
                if not hasattr(layout, 'bounding_poly'):
                    continue
                
                # Get bounding box
                bounding_poly = layout.bounding_poly
                if not hasattr(bounding_poly, 'normalized_vertices'):
                    continue
                
                vertices = bounding_poly.normalized_vertices
                if len(vertices) < 2:
                    continue
                
                # Calculate bounding box (using normalized coordinates 0-1)
                x_coords = [v.x for v in vertices]
                y_coords = [v.y for v in vertices]
                
                x_min = min(x_coords)
                x_max = max(x_coords)
                y_min = min(y_coords)
                y_max = max(y_coords)
                
                # Get text content
                text = self._get_text_from_layout(layout, document_text)
                
                if text and text.strip():
                    text_blocks.append({
                        'text': text.strip(),
                        'x_min': x_min,
                        'x_max': x_max,
                        'y_min': y_min,
                        'y_max': y_max,
                        'x_center': (x_min + x_max) / 2,
                        'y_center': (y_min + y_max) / 2,
                        'width': x_max - x_min,
                        'height': y_max - y_min
                    })
        
        # Method 2: Try tokens (fallback if paragraphs don't work)
        if not text_blocks and hasattr(page, 'tokens') and page.tokens:
            logger.debug("Using tokens as fallback for text extraction")
            for token in page.tokens:
                if not hasattr(token, 'layout'):
                    continue
                
                layout = token.layout
                if not hasattr(layout, 'bounding_poly'):
                    continue
                
                bounding_poly = layout.bounding_poly
                if not hasattr(bounding_poly, 'normalized_vertices'):
                    continue
                
                vertices = bounding_poly.normalized_vertices
                if len(vertices) < 2:
                    continue
                
                x_coords = [v.x for v in vertices]
                y_coords = [v.y for v in vertices]
                
                x_min = min(x_coords)
                x_max = max(x_coords)
                y_min = min(y_coords)
                y_max = max(y_coords)
                
                text = self._get_text_from_layout(layout, document_text)
                
                if text and text.strip():
                    text_blocks.append({
                        'text': text.strip(),
                        'x_min': x_min,
                        'x_max': x_max,
                        'y_min': y_min,
                        'y_max': y_max,
                        'x_center': (x_min + x_max) / 2,
                        'y_center': (y_min + y_max) / 2,
                        'width': x_max - x_min,
                        'height': y_max - y_min
                    })
        
        # Method 3: Fallback to line-based extraction from document text
        if not text_blocks and document_text:
            logger.debug("Using line-based fallback extraction from document text")
            lines = document_text.split('\n')
            y_pos = 0.0
            for line in lines:
                line = line.strip()
                if line:
                    # Assign approximate positions (will be grouped by Y-axis later)
                    text_blocks.append({
                        'text': line,
                        'x_min': 0.0,
                        'x_max': 1.0,
                        'y_min': y_pos,
                        'y_max': y_pos + 0.01,
                        'x_center': 0.5,
                        'y_center': y_pos + 0.005,
                        'width': 1.0,
                        'height': 0.01
                    })
                    y_pos += 0.02  # Increment Y position for each line
        
        # Sort by Y then X
        text_blocks.sort(key=lambda b: (b['y_center'], b['x_center']))
        
        logger.debug(f"Extracted {len(text_blocks)} text blocks from page")
        return text_blocks
    
    def _get_text_from_layout(self, layout: Any, document_text: str) -> str:
        """Extract text from layout using text anchors"""
        if not layout:
            return ''
        
        if not hasattr(layout, 'text_anchor'):
            return ''
        
        text_anchor = layout.text_anchor
        if not text_anchor:
            return ''
        
        if not hasattr(text_anchor, 'text_segments'):
            return ''
        
        if not text_anchor.text_segments:
            return ''
        
        text_parts = []
        for segment in text_anchor.text_segments:
            if not segment:
                continue
            
            if hasattr(segment, 'start_index') and hasattr(segment, 'end_index'):
                start = int(segment.start_index) if segment.start_index is not None else 0
                end = int(segment.end_index) if segment.end_index is not None else 0
                
                # Validate indices
                if start < 0:
                    start = 0
                if end > len(document_text):
                    end = len(document_text)
                if start < len(document_text) and end <= len(document_text) and start < end:
                    text_parts.append(document_text[start:end])
        
        result = ' '.join(text_parts).strip()
        # Preserve Unicode characters
        return result
    
    def _build_resume_layout(self, text_blocks: List[Dict]) -> UnifiedLayout:
        """Build layout for resume (key-value pairs) with enhanced detection"""
        layout = UnifiedLayout()
        row_idx = 0
        
        for block in text_blocks:
            text = block['text']
            
            # Enhanced key-value pattern detection
            # Patterns: "Key: Value", "Key - Value", "Key – Value", "Key — Value"
            key_value_patterns = [
                (':', 1),  # Colon
                (' - ', 3),  # Space-dash-space
                (' – ', 3),  # En dash
                (' — ', 3),  # Em dash
                ('\t', 1),  # Tab
            ]
            
            found_pattern = False
            for pattern, split_count in key_value_patterns:
                if pattern in text:
                    parts = text.split(pattern, split_count)
                    if len(parts) >= 2:
                        key = parts[0].strip()
                        value = pattern.join(parts[1:]).strip() if len(parts) > 2 else parts[1].strip()
                        
                        # Validate key-value (key should be short, value can be longer)
                        if key and len(key) < 50 and (value or len(key) < 20):
                            key_cell = Cell(
                                row=row_idx,
                                column=0,
                                value=key,
                                style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                            )
                            value_cell = Cell(
                                row=row_idx,
                                column=1,
                                value=value,
                                style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=True)
                            )
                            layout.add_row([key_cell, value_cell])
                            row_idx += 1
                            found_pattern = True
                            break
            
            if not found_pattern:
                # Regular text block - check if it's a heading (bold, centered, or larger)
                is_heading = (
                    len(text) < 50 and  # Short text
                    text.isupper() or  # All caps
                    (text and text[0].isupper() and not ' ' in text[:10])  # Title case, single word
                )
                
                cell = Cell(
                    row=row_idx,
                    column=0,
                    value=text,
                    style=CellStyle(
                        bold=is_heading,
                        alignment_horizontal=CellAlignment.LEFT,
                        font_size=14 if is_heading else None
                    ),
                    colspan=2
                )
                layout.add_row([cell])
                row_idx += 1
        
        return layout
    
    def _build_certificate_layout(self, text_blocks: List[Dict]) -> UnifiedLayout:
        """Build layout for certificate (centered, structured)"""
        layout = UnifiedLayout()
        row_idx = 0
        
        for block in text_blocks:
            text = block['text']
            
            # Check for key-value pattern
            if ':' in text or '—' in text or '–' in text:
                parts = re.split(r'[:—–]', text, 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    key_cell = Cell(
                        row=row_idx,
                        column=0,
                        value=key,
                        style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                    )
                    value_cell = Cell(
                        row=row_idx,
                        column=1,
                        value=value,
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                    layout.add_row([key_cell, value_cell])
                    row_idx += 1
                    continue
            
            # Centered text (likely title or heading)
            cell = Cell(
                row=row_idx,
                column=0,
                value=text,
                style=CellStyle(
                    bold=True,
                    alignment_horizontal=CellAlignment.CENTER,
                    font_size=14
                ),
                colspan=2
            )
            layout.add_row([cell])
            row_idx += 1
        
        return layout
    
    def _build_id_card_layout(self, text_blocks: List[Dict]) -> UnifiedLayout:
        """Build layout for ID card (compact key-value)"""
        return self._build_resume_layout(text_blocks)  # Similar structure
    
    def _build_letter_layout(self, text_blocks: List[Dict]) -> UnifiedLayout:
        """Build layout for letter (paragraph-based)"""
        layout = UnifiedLayout()
        row_idx = 0
        
        for block in text_blocks:
            text = block['text']
            
            # Single column for paragraphs
            cell = Cell(
                row=row_idx,
                column=0,
                value=text,
                style=CellStyle(
                    alignment_horizontal=CellAlignment.LEFT,
                    wrap_text=True
                ),
                colspan=1
            )
            layout.add_row([cell])
            row_idx += 1
        
        return layout
    
    def _build_statement_layout(self, text_blocks: List[Dict]) -> UnifiedLayout:
        """Build layout for invoices/bank statements (table-like)"""
        layout = UnifiedLayout()
        
        # Group blocks by Y-axis (rows)
        rows = self._group_by_y_axis(text_blocks)
        
        # Detect merged cells
        merged_cells_info = self._detect_merged_cells(rows)
        merged_map = {(m['row'], m['col']): m for m in merged_cells_info}
        
        row_idx = 0
        for row_blocks in rows:
            # Sort blocks in row by X-axis
            row_blocks.sort(key=lambda b: b['x_center'])
            
            # Create cells for this row
            cells = []
            col_idx = 0
            for block in row_blocks:
                # Check if this cell should be merged
                merge_info = merged_map.get((row_idx, col_idx))
                rowspan = merge_info['rowspan'] if merge_info else 1
                colspan = merge_info['colspan'] if merge_info else 1
                
                # Check if text contains multiple values (e.g., "Item | Price | Qty")
                if '|' in block['text'] or '\t' in block['text']:
                    parts = re.split(r'[|\t]', block['text'])
                    for part in parts:
                        part = part.strip()
                        if part:
                            cell = Cell(
                                row=row_idx,
                                column=col_idx,
                                value=part,
                                style=CellStyle(alignment_horizontal=CellAlignment.LEFT),
                                rowspan=rowspan,
                                colspan=colspan,
                                merged=(rowspan > 1 or colspan > 1)
                            )
                            cells.append(cell)
                            col_idx += 1
                else:
                    cell = Cell(
                        row=row_idx,
                        column=col_idx,
                        value=block['text'],
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT),
                        rowspan=rowspan,
                        colspan=colspan,
                        merged=(rowspan > 1 or colspan > 1)
                    )
                    cells.append(cell)
                    col_idx += 1
            
            if cells:
                layout.add_row(cells)
                row_idx += 1
        
        return layout
    
    def _build_generic_layout(self, text_blocks: List[Dict]) -> UnifiedLayout:
        """Build generic layout (fallback) with enhanced column detection"""
        layout = UnifiedLayout()
        row_idx = 0
        
        # Group by Y-axis proximity
        rows = self._group_by_y_axis(text_blocks)
        
        # Detect column boundaries across all rows for better alignment
        column_positions = self._detect_global_columns(rows)
        
        for row_blocks in rows:
            row_blocks.sort(key=lambda b: b['x_center'])
            
            # Map blocks to detected columns
            cells = []
            used_cols = set()
            
            for block in row_blocks:
                # Find which column this block belongs to
                col_idx = self._find_column_for_block(block, column_positions)
                
                # Avoid duplicate column assignment
                if col_idx in used_cols:
                    # Find next available column
                    col_idx = max(column_positions.keys()) + 1 if column_positions else len(cells)
                
                used_cols.add(col_idx)
                
                cell = Cell(
                    row=row_idx,
                    column=col_idx,
                    value=block['text'],
                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                )
                cells.append(cell)
            
            if cells:
                layout.add_row(cells)
                row_idx += 1
        
        return layout
    
    def _detect_global_columns(self, rows: List[List[Dict]]) -> Dict[int, float]:
        """
        Detect column positions globally across all rows.
        Returns dict mapping column index to X position.
        """
        if not rows:
            return {}
        
        # Collect all X positions
        all_x_positions = []
        for row_blocks in rows:
            for block in row_blocks:
                all_x_positions.append(block['x_center'])
        
        if not all_x_positions:
            return {}
        
        # Cluster X positions to find column boundaries
        sorted_x = sorted(set(all_x_positions))
        
        # Group nearby X positions (same column)
        clusters = []
        current_cluster = [sorted_x[0]]
        
        for x in sorted_x[1:]:
            # If X is close to current cluster, add to it
            # Use normalized tolerance directly (no division by 1000)
            if x - current_cluster[-1] <= self.x_tolerance:
                current_cluster.append(x)
            else:
                # New cluster
                clusters.append(current_cluster)
                current_cluster = [x]
        
        if current_cluster:
            clusters.append(current_cluster)
        
        # Map cluster centers to column indices
        column_positions = {}
        for col_idx, cluster in enumerate(clusters):
            # Use median of cluster as column position
            cluster_center = sorted(cluster)[len(cluster) // 2]
            column_positions[col_idx] = cluster_center
        
        logger.debug(f"Detected {len(column_positions)} global columns")
        return column_positions
    
    def _find_column_for_block(self, block: Dict, column_positions: Dict[int, float]) -> int:
        """Find which column a block belongs to based on its X position"""
        if not column_positions:
            return 0
        
        block_x = block['x_center']
        
        # Find closest column
        min_distance = float('inf')
        closest_col = 0
        
        for col_idx, col_x in column_positions.items():
            distance = abs(block_x - col_x)
            if distance < min_distance:
                min_distance = distance
                closest_col = col_idx
        
        # Check if within tolerance (normalized coordinates)
        if min_distance <= self.x_tolerance:
            return closest_col
        
        # If not close to any column, create new column
        return max(column_positions.keys()) + 1
    
    def _group_by_y_axis(self, text_blocks: List[Dict]) -> List[List[Dict]]:
        """Group text blocks by Y-axis proximity (same row)"""
        if not text_blocks:
            return []
        
        rows = []
        current_row = [text_blocks[0]]
        
        for block in text_blocks[1:]:
            # Check if block is on same row (within tolerance)
            # Use normalized tolerance directly (no division by 1000)
            last_y = current_row[-1]['y_center']
            if abs(block['y_center'] - last_y) <= self.y_tolerance:
                current_row.append(block)
            else:
                rows.append(current_row)
                current_row = [block]
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def _detect_merged_cells(self, rows: List[List[Dict]]) -> List[Dict]:
        """
        Detect merged cells by analyzing bounding box overlaps and gaps.
        Returns list of merged cell info: (row, col, rowspan, colspan)
        """
        merged_cells = []
        
        # Build a grid of cells with their positions
        cell_grid = {}  # (row_idx, col_idx) -> block info
        
        for row_idx, row_blocks in enumerate(rows):
            row_blocks.sort(key=lambda b: b['x_center'])
            
            # Detect columns by X-axis alignment
            columns = self._detect_columns(row_blocks)
            
            for col_idx, block in enumerate(row_blocks):
                cell_grid[(row_idx, col_idx)] = {
                    'block': block,
                    'x_min': block['x_min'],
                    'x_max': block['x_max'],
                    'y_min': block['y_min'],
                    'y_max': block['y_max'],
                    'width': block['width'],
                    'height': block['height']
                }
        
        # Analyze for merged cells
        # A cell is merged if:
        # 1. It spans multiple columns (wide cell)
        # 2. It spans multiple rows (tall cell)
        # 3. Adjacent cells are missing (gap detection)
        
        for (row_idx, col_idx), cell_info in cell_grid.items():
            block = cell_info['block']
            
            # Check if this cell is wider than average (potential colspan > 1)
            avg_width = sum(c['width'] for c in cell_grid.values()) / max(len(cell_grid), 1)
            if cell_info['width'] > avg_width * 1.5:
                # Check how many columns it spans
                colspan = self._calculate_colspan(row_idx, col_idx, cell_info, cell_grid, rows)
                if colspan > 1:
                    merged_cells.append({
                        'row': row_idx,
                        'col': col_idx,
                        'rowspan': 1,
                        'colspan': colspan
                    })
            
            # Check if this cell is taller than average (potential rowspan > 1)
            avg_height = sum(c['height'] for c in cell_grid.values()) / max(len(cell_grid), 1)
            if cell_info['height'] > avg_height * 1.5:
                # Check how many rows it spans
                rowspan = self._calculate_rowspan(row_idx, col_idx, cell_info, cell_grid, rows)
                if rowspan > 1:
                    merged_cells.append({
                        'row': row_idx,
                        'col': col_idx,
                        'rowspan': rowspan,
                        'colspan': 1
                    })
        
        return merged_cells
    
    def _detect_columns(self, row_blocks: List[Dict]) -> List[int]:
        """Detect column boundaries from X-axis positions"""
        if not row_blocks:
            return []
        
        # Sort by X position
        sorted_blocks = sorted(row_blocks, key=lambda b: b['x_center'])
        
        # Group blocks that are close on X-axis (same column)
        columns = []
        current_col = [sorted_blocks[0]]
        
        for block in sorted_blocks[1:]:
            # Check if block is in same column (X-axis proximity)
            # Use normalized tolerance directly (no division by 1000)
            last_x = current_col[-1]['x_center']
            if abs(block['x_center'] - last_x) <= self.x_tolerance:
                current_col.append(block)
            else:
                columns.append(len(columns))
                current_col = [block]
        
        if current_col:
            columns.append(len(columns))
        
        return columns
    
    def _calculate_colspan(self, row_idx: int, col_idx: int, cell_info: Dict, cell_grid: Dict, rows: List[List[Dict]]) -> int:
        """Calculate how many columns a cell spans"""
        if row_idx >= len(rows):
            return 1
        
        row_blocks = rows[row_idx]
        if not row_blocks:
            return 1
        
        # Find average column width in this row
        widths = [b['width'] for b in row_blocks]
        avg_width = sum(widths) / max(len(widths), 1) if widths else cell_info['width']
        
        # Calculate colspan based on cell width vs average
        if avg_width > 0:
            colspan = max(1, int(round(cell_info['width'] / avg_width)))
            return min(colspan, 10)  # Cap at 10 columns
        
        return 1
    
    def _calculate_rowspan(self, row_idx: int, col_idx: int, cell_info: Dict, cell_grid: Dict, rows: List[List[Dict]]) -> int:
        """Calculate how many rows a cell spans"""
        if not rows:
            return 1
        
        # Find average row height
        heights = []
        for row in rows:
            for block in row:
                heights.append(block['height'])
        
        avg_height = sum(heights) / max(len(heights), 1) if heights else cell_info['height']
        
        # Calculate rowspan based on cell height vs average
        if avg_height > 0:
            rowspan = max(1, int(round(cell_info['height'] / avg_height)))
            return min(rowspan, 20)  # Cap at 20 rows
        
        return 1

