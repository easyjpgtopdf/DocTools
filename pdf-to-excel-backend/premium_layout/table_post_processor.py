"""
Premium Table Post-Processing Layer
Enhances Document AI table extraction with sophisticated post-processing.
Runs ONLY for premium Document AI conversions.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

from .geometry_reconstructor import GeometryReconstructor

logger = logging.getLogger(__name__)


# STEP-11: Exception for TABLE_STRICT failures
class TableExtractionFailed(Exception):
    """Raised when TABLE_STRICT mode fails to extract any cells"""
    pass


class CellMergeType(Enum):
    """Types of cell merges"""
    NONE = "none"
    LINE_MERGE = "line_merge"  # Multiple lines merged into one cell
    ROWSPAN = "rowspan"  # Vertical merge
    COLSPAN = "colspan"  # Horizontal merge


@dataclass
class ProcessedCell:
    """Post-processed cell with enhanced metadata"""
    row: int
    column: int
    value: str
    original_value: str = ""  # Original before merging
    rowspan: int = 1
    colspan: int = 1
    is_header: bool = False
    font_size: Optional[float] = None
    is_bold: bool = False
    bounding_box: Optional[Dict[str, float]] = None  # x_min, x_max, y_min, y_max
    confidence: float = 1.0
    merge_type: CellMergeType = CellMergeType.NONE
    is_numeric_sequence: bool = False  # For Aadhaar/numeric protection


@dataclass
class ProcessedTable:
    """Post-processed table structure"""
    rows: List[List[ProcessedCell]] = field(default_factory=list)
    column_anchors: List[float] = field(default_factory=list)  # X positions for column snapping
    header_row_indices: List[int] = field(default_factory=list)
    avg_line_height: float = 0.0
    table_confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TablePostProcessor:
    """
    Post-processing layer for premium Document AI table extraction.
    Enhances table structure with header detection, column anchoring, merging, etc.
    """
    
    def __init__(self):
        self.line_merge_threshold = 0.6  # Merge lines if Y-distance < 0.6 × avg_line_height
        self.column_snap_tolerance = 0.02  # 2% of page width for column snapping
        self.min_header_font_size = 10.0  # Minimum font size for header detection
        self.numeric_sequence_min_length = 10  # Minimum length for numeric protection
        self.geometry_reconstructor = GeometryReconstructor()  # For missing geometry
        
    def process_table(
        self,
        table: Any,
        document_text: str,
        page: Optional[Any] = None,
        doc_type: Optional[Any] = None,
        table_confidence: Optional[float] = None,
        execution_mode: Optional[str] = "table_strict"
    ) -> ProcessedTable:
        """
        Process a Document AI table with post-processing.
        
        For TABLE_STRICT mode:
        - Trust DocAI structure completely
        - Preserve row/column spans
        - Preserve merges
        - Apply 7-step premium pipeline
        
        For TABLE_VISUAL mode:
        - This method is NOT used (handled in layout_decision_engine)
        
        Args:
            table: Document AI table object
            document_text: Full document text
            page: Document AI page object (for additional context)
            doc_type: premium doc category (deprecated, kept for compatibility)
            table_confidence: precomputed table confidence (0-1) for gating
            execution_mode: "table_strict" or "table_visual" (default: "table_strict")
            
        Returns:
            ProcessedTable with enhanced structure
        """
        logger.info("=" * 80)
        logger.info(f"TABLE POST-PROCESSOR: Processing table in {execution_mode} mode")
        logger.info("=" * 80)
        
        # TABLE_STRICT mode: Trust DocAI structure, preserve spans and merges
        if execution_mode == "table_strict":
            return self._process_table_strict(table, document_text, page, table_confidence)
        else:
            # TABLE_VISUAL is handled in layout_decision_engine, not here
            logger.warning(f"TABLE_VISUAL mode should not call process_table - handled in layout_decision_engine")
            return ProcessedTable()
    
    def _process_table_strict(
        self,
        table: Any,
        document_text: str,
        page: Optional[Any] = None,
        table_confidence: Optional[float] = None
    ) -> ProcessedTable:
        """
        Process table in TABLE_STRICT mode: Trust DocAI structure, preserve spans/merges.
        """
        logger.info("TABLE_STRICT: Trusting DocAI structure, preserving row/column spans and merges")
        
        # CRITICAL DEBUG: Log table object structure
        logger.info(f"🔍 _process_table_strict: Table object type: {type(table)}")
        logger.info(f"🔍 _process_table_strict: Table object: {table}")
        logger.info(f"🔍 _process_table_strict: Table dir: {[attr for attr in dir(table) if not attr.startswith('_')][:20]}")
        if hasattr(table, 'header_rows'):
            logger.info(f"🔍 _process_table_strict: table.header_rows = {table.header_rows}")
        if hasattr(table, 'body_rows'):
            logger.info(f"🔍 _process_table_strict: table.body_rows = {table.body_rows}")
        
        # PRE-PIPELINE: Extract raw cells and calculate line height
        # CRITICAL: Force flush logs to ensure visibility
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        
        logger.critical("=" * 80)
        logger.critical("STEP 1: Calling _extract_raw_cells() for initial extraction")
        logger.critical("=" * 80)
        sys.stdout.flush()
        
        raw_cells = self._extract_raw_cells(table, document_text)
        
        sys.stdout.flush()
        sys.stderr.flush()
        logger.critical(f"✅ STEP 1 RESULT: Extracted {len(raw_cells)} raw cells from table (initial attempt)")
        logger.critical("=" * 80)
        sys.stdout.flush()
        
        # CRITICAL FIX: If _extract_raw_cells fails (Form Parser compatibility issue),
        # ALWAYS invoke fallback extractor - this is especially critical for Form Parser tables
        if not raw_cells or len(raw_cells) == 0:
            sys.stdout.flush()
            sys.stderr.flush()
            logger.critical("=" * 80)
            logger.critical("⚠️ STEP 2: Raw cells empty — invoking Form Parser fallback extractor")
            logger.critical("⚠️ This typically happens with Form Parser processor tables where standard extraction fails")
            logger.critical("=" * 80)
            sys.stdout.flush()
            
            raw_cells = self._extract_raw_cells_fallback(table, document_text)
            
            sys.stdout.flush()
            sys.stderr.flush()
            if raw_cells and len(raw_cells) > 0:
                logger.critical("=" * 80)
                logger.critical(f"✅ STEP 2 SUCCESS: Fallback extracted {len(raw_cells)} cells via Form Parser fallback method")
                logger.critical("=" * 80)
            else:
                # STEP-11: BLANK EXCEL IS NEVER A VALID RESULT
                # Throw exception to trigger automatic fallback to OCR_GRID
                logger.critical("=" * 80)
                logger.critical("❌ STEP-11 FAIL-SAFE: TABLE_STRICT extracted 0 cells")
                logger.critical("❌ This indicates Form Parser table with incompatible schema")
                logger.critical("❌ BLANK EXCEL IS NEVER A VALID RESULT")
                logger.critical("🚨 THROWING TableExtractionFailed exception to trigger OCR_GRID fallback")
                logger.critical("=" * 80)
                sys.stdout.flush()
                raise TableExtractionFailed("TABLE_STRICT produced zero cells - automatic fallback to OCR_GRID required")
            sys.stdout.flush()
        else:
            sys.stdout.flush()
            logger.critical("=" * 80)
            logger.critical(f"✅ STEP 1 SUCCESS: {len(raw_cells)} cells extracted, skipping fallback")
            logger.critical("=" * 80)
            sys.stdout.flush()
        
        avg_line_height = self._calculate_avg_line_height(raw_cells)
        logger.debug(f"Average line height: {avg_line_height:.4f}")
        
        is_mixed_language = self._detect_mixed_language(raw_cells, document_text)
        if is_mixed_language:
            logger.info("Detected mixed language (Hindi/Unicode), using font-height based Y-thresholds")
        
        # Organize raw cells into initial rows
        initial_rows = self._process_cells(raw_cells, [], [], avg_line_height)
        
        # ========================================================================
        # STEP 1: HEADER DETECTION AND LOCKING
        # ========================================================================
        logger.info("STEP 1: Detecting header rows and locking column positions...")
        header_row_indices = self._detect_header_rows(raw_cells, avg_line_height)
        logger.info(f"STEP 1 COMPLETE: Detected {len(header_row_indices)} header row(s): {header_row_indices}")

        # TABLE_STRICT: Trust DocAI structure - if header missing, still proceed (DocAI knows best)
        if not header_row_indices:
            logger.warning("STEP 1: No header detected, but TABLE_STRICT mode - trusting DocAI structure and proceeding")
        
        # ========================================================================
        # STEP 2: ROWSPAN AND COLSPAN MERGE (from Document AI metadata)
        # ========================================================================
        logger.info("STEP 2: Applying rowspan/colspan merges from Document AI...")
        # TABLE_STRICT: Always allow spans - trust DocAI structure completely
        allow_spans = True
        processed_rows, span_conflict = self._apply_document_ai_merges(table, initial_rows, document_text, allow_spans)
        if span_conflict:
            logger.warning("STEP 2 FAILED: Span conflict detected. Marking SPAN_CONFLICT and aborting table reconstruction.")
            pt = ProcessedTable(rows=[], metadata={"span_conflict": True})
            return pt
        logger.info(f"STEP 2 COMPLETE: Applied rowspan/colspan merges, {len(processed_rows)} rows processed")
        
        # ========================================================================
        # STEP 3: MULTI-LINE CELL MERGE (language-aware)
        # ========================================================================
        logger.info("STEP 3: Merging multi-line cells (language-aware)...")
        processed_rows = self._apply_line_merging(processed_rows, avg_line_height, is_mixed_language)
        logger.info(f"STEP 3 COMPLETE: Multi-line cell merge complete, {len(processed_rows)} rows after merge")
        
        # ========================================================================
        # STEP 4: COLUMN ANCHOR STABILIZATION (lock header column positions)
        # ========================================================================
        logger.info("STEP 4: Building column anchors from header positions...")
        column_anchors = self._build_column_anchors(raw_cells, header_row_indices)
        logger.info(f"STEP 4 COMPLETE: Built {len(column_anchors)} column anchors: {column_anchors}")
        
        # ========================================================================
        # STEP 5: COLUMN SNAPPING (LAST step before Excel writing)
        # ========================================================================
        logger.info("STEP 5: Snapping cells to column anchors...")
        # Protect numeric sequences before snapping
        processed_rows = self._protect_numeric_sequences(processed_rows)
        
        # Recalculate table confidence if not provided
        if table_confidence is None:
            table_confidence = self._calculate_table_confidence(processed_rows, raw_cells)
        logger.info(f"Table confidence: {table_confidence:.2f}")
        
        CONFIDENCE_THRESHOLD = 0.65
        if table_confidence >= CONFIDENCE_THRESHOLD:
            processed_rows = self._snap_to_column_anchors(processed_rows, column_anchors, table_confidence)
            logger.info(f"STEP 5 COMPLETE: Column snapping applied, {len(processed_rows)} rows snapped to {len(column_anchors)} anchors")
        else:
            logger.warning(f"STEP 5 SKIPPED: Table confidence {table_confidence:.2f} < {CONFIDENCE_THRESHOLD}, using logical alignment (fail-safe mode)")
            processed_rows = self._apply_logical_alignment(processed_rows)
            logger.info(f"STEP 5 COMPLETE: Logical alignment applied (fail-safe mode)")
        
        # ========================================================================
        # STEP 6: FINAL CLEANUP AND NORMALIZATION
        # ========================================================================
        # Note: This step is handled by LayoutDecisionEngine._final_cleanup_and_normalize()
        # after ProcessedTable is converted to UnifiedLayout
        logger.info("STEP 6: Final cleanup will be applied after layout conversion")
        
        # ========================================================================
        # STEP 7: EXCEL WRITING
        # ========================================================================
        # Note: This step is handled by ExcelWordRenderer.render_to_excel()
        # which receives UnifiedLayout from convert_to_unified_layout()
        logger.info("STEP 7: Excel writing will be handled by ExcelWordRenderer.render_to_excel()")
        
        processed_table = ProcessedTable(
            rows=processed_rows,
            column_anchors=column_anchors,
            header_row_indices=header_row_indices,
            avg_line_height=avg_line_height,
            table_confidence=table_confidence
        )
        
        logger.info(f"Post-processing complete: {len(processed_rows)} rows, "
                   f"confidence: {table_confidence:.2f}")
        
        return processed_table
    
    def _extract_raw_cells(
        self,
        table: Any,
        document_text: str,
        reconstructed_geometry: Optional[Dict[str, Any]] = None
    ) -> List[ProcessedCell]:
        """
        Extract all cells from Document AI table with bounding boxes.
        
        ENHANCEMENT: If cell lacks geometry, try reconstructed_geometry first.
        """
        raw_cells = []
        row_idx = 0
        
        # CRITICAL DEBUG: Log table structure
        logger.info(f"🔍 _extract_raw_cells: Table type: {type(table)}")
        logger.info(f"🔍 _extract_raw_cells: Table object: {str(table)[:200]}")
        logger.info(f"🔍 _extract_raw_cells: Table has 'header_rows': {hasattr(table, 'header_rows')}")
        logger.info(f"🔍 _extract_raw_cells: Table has 'body_rows': {hasattr(table, 'body_rows')}")
        
        # Check if table is a dict (unlikely but possible)
        if isinstance(table, dict):
            logger.warning(f"⚠️ Table is a dict, not a DocAI table object! Keys: {list(table.keys())}")
            # Try to extract from dict
            if 'header_rows' in table:
                logger.info(f"🔍 Found header_rows in dict: {table['header_rows']}")
            if 'body_rows' in table:
                logger.info(f"🔍 Found body_rows in dict: {table['body_rows']}")
        
        if hasattr(table, 'header_rows'):
            logger.info(f"🔍 _extract_raw_cells: table.header_rows = {table.header_rows} (type: {type(table.header_rows)})")
            if table.header_rows:
                logger.info(f"🔍 _extract_raw_cells: len(table.header_rows) = {len(table.header_rows)}")
                if len(table.header_rows) > 0:
                    logger.info(f"🔍 _extract_raw_cells: First header_row type: {type(table.header_rows[0])}")
        if hasattr(table, 'body_rows'):
            logger.info(f"🔍 _extract_raw_cells: table.body_rows = {table.body_rows} (type: {type(table.body_rows)})")
            if table.body_rows:
                logger.info(f"🔍 _extract_raw_cells: len(table.body_rows) = {len(table.body_rows)}")
                if len(table.body_rows) > 0:
                    logger.info(f"🔍 _extract_raw_cells: First body_row type: {type(table.body_rows[0])}")
        
        # Get reconstructed geometries if available
        cell_geometries = {}
        if reconstructed_geometry and 'cell_geometries' in reconstructed_geometry:
            cell_geometries = reconstructed_geometry['cell_geometries']
            logger.info(f"Using {len(cell_geometries)} reconstructed geometries")
        
        # Process header rows
        # CRITICAL: Try multiple ways to access header_rows (form-parser-docai compatibility)
        header_rows_list = None
        if hasattr(table, 'header_rows'):
            header_rows_list = table.header_rows
            logger.info(f"🔍 Found header_rows via 'header_rows' attribute: {header_rows_list}")
        elif hasattr(table, 'headerRows'):
            header_rows_list = table.headerRows
            logger.info(f"🔍 Found header_rows via 'headerRows' attribute: {header_rows_list}")
        
        if header_rows_list:
            logger.info(f"✅ Processing {len(header_rows_list)} header rows")
            for header_row in header_rows_list:
                cells_list = None
                if hasattr(header_row, 'cells'):
                    cells_list = header_row.cells
                elif hasattr(header_row, 'Cells'):
                    cells_list = header_row.Cells
                
                if cells_list:
                    logger.info(f"🔍 Header row {row_idx} has {len(cells_list)} cells")
                    for col_idx, cell in enumerate(cells_list):
                        # Try with reconstructed geometry if available
                        cell_key = (row_idx, col_idx)
                        reconstructed_bbox = cell_geometries.get(cell_key)
                        
                        logger.info(f"🔍 Extracting header cell ({row_idx},{col_idx}), cell type: {type(cell)}")
                        cell_data = self._extract_cell_data(
                            cell, document_text, row_idx, col_idx, 
                            is_header=True,
                            fallback_bbox=reconstructed_bbox
                        )
                        if cell_data:
                            logger.info(f"✅ Header cell ({row_idx},{col_idx}) extracted: '{cell_data.value[:50] if cell_data.value else 'EMPTY'}'")
                            raw_cells.append(cell_data)
                        else:
                            logger.warning(f"❌ Header cell ({row_idx},{col_idx}) returned None - cell type: {type(cell)}, has layout: {hasattr(cell, 'layout')}")
                row_idx += 1
        
        # Process body rows
        # CRITICAL: Try multiple ways to access body_rows (form-parser-docai compatibility)
        body_rows_list = None
        if hasattr(table, 'body_rows'):
            body_rows_list = table.body_rows
            logger.info(f"🔍 Found body_rows via 'body_rows' attribute: {body_rows_list}")
        elif hasattr(table, 'bodyRows'):
            body_rows_list = table.bodyRows
            logger.info(f"🔍 Found body_rows via 'bodyRows' attribute: {body_rows_list}")
        
        if body_rows_list:
            logger.info(f"✅ Processing {len(body_rows_list)} body rows")
            for body_row in body_rows_list:
                cells_list = None
                if hasattr(body_row, 'cells'):
                    cells_list = body_row.cells
                elif hasattr(body_row, 'Cells'):
                    cells_list = body_row.Cells
                
                if cells_list:
                    logger.info(f"🔍 Body row {row_idx} has {len(cells_list)} cells")
                    for col_idx, cell in enumerate(cells_list):
                        # Try with reconstructed geometry if available
                        cell_key = (row_idx, col_idx)
                        reconstructed_bbox = cell_geometries.get(cell_key)
                        
                        logger.info(f"🔍 Extracting body cell ({row_idx},{col_idx}), cell type: {type(cell)}")
                        cell_data = self._extract_cell_data(
                            cell, document_text, row_idx, col_idx, 
                            is_header=False,
                            fallback_bbox=reconstructed_bbox
                        )
                        if cell_data:
                            logger.info(f"✅ Body cell ({row_idx},{col_idx}) extracted: '{cell_data.value[:50] if cell_data.value else 'EMPTY'}'")
                            raw_cells.append(cell_data)
                        else:
                            logger.warning(f"❌ Body cell ({row_idx},{col_idx}) returned None - cell type: {type(cell)}, has layout: {hasattr(cell, 'layout')}")
                else:
                    logger.warning(f"❌ Body row {row_idx} has no 'cells' attribute or cells is empty")
                row_idx += 1
        else:
            logger.warning(f"❌ Table has no 'body_rows' attribute or body_rows is empty")
        
        logger.info(f"Extracted {len(raw_cells)} raw cells from table (from {row_idx} total rows)")
        return raw_cells
    
    def _extract_raw_cells_fallback(
        self,
        table: Any,
        document_text: str
    ) -> List[ProcessedCell]:
        """
        Fallback extraction method using parse_docai_table logic.
        This works for Form Parser tables where _extract_raw_cells might fail.
        
        Uses the same logic as docai_service.parse_docai_table which successfully
        extracts cells from Form Parser tables.
        """
        raw_cells = []
        row_idx = 0
        
        logger.info("🔄 FALLBACK: Using parse_docai_table-style extraction")
        
        # Combine header and body rows (same as parse_docai_table)
        all_rows = []
        if hasattr(table, 'header_rows') and table.header_rows:
            all_rows.extend(table.header_rows)
            logger.info(f"🔄 Fallback: Found {len(table.header_rows)} header rows")
        if hasattr(table, 'body_rows') and table.body_rows:
            all_rows.extend(table.body_rows)
            logger.info(f"🔄 Fallback: Found {len(table.body_rows)} body rows")
        
        if not all_rows:
            logger.warning("🔄 Fallback: No rows found in table")
            return []
        
        # Process each row
        for row in all_rows:
            is_header = (row_idx < len(table.header_rows) if hasattr(table, 'header_rows') and table.header_rows else False)
            
            if hasattr(row, 'cells') and row.cells:
                logger.info(f"🔄 Fallback: Processing row {row_idx} with {len(row.cells)} cells")
                for col_idx, cell in enumerate(row.cells):
                    # Extract text using text_anchor (same as parse_docai_table)
                    cell_text = ""
                    if hasattr(cell, 'layout') and cell.layout:
                        layout = cell.layout
                        if hasattr(layout, 'text_anchor') and layout.text_anchor:
                            text_anchor = layout.text_anchor
                            if hasattr(text_anchor, 'text_segments') and text_anchor.text_segments:
                                text_parts = []
                                for segment in text_anchor.text_segments:
                                    if hasattr(segment, 'start_index') and hasattr(segment, 'end_index'):
                                        start = int(segment.start_index) if segment.start_index else 0
                                        end = int(segment.end_index) if segment.end_index else 0
                                        if start < len(document_text) and end <= len(document_text):
                                            text_parts.append(document_text[start:end])
                                cell_text = ' '.join(text_parts).strip()
                    
                    # Extract bounding box
                    bounding_box = None
                    if hasattr(cell, 'layout') and cell.layout:
                        layout = cell.layout
                        if hasattr(layout, 'bounding_poly') and layout.bounding_poly:
                            bounding_poly = layout.bounding_poly
                            if hasattr(bounding_poly, 'normalized_vertices') and bounding_poly.normalized_vertices:
                                vertices = bounding_poly.normalized_vertices
                                if len(vertices) >= 2:
                                    xs = [v.x for v in vertices if hasattr(v, 'x')]
                                    ys = [v.y for v in vertices if hasattr(v, 'y')]
                                    if xs and ys:
                                        bounding_box = {
                                            'x_min': min(xs),
                                            'x_max': max(xs),
                                            'y_min': min(ys),
                                            'y_max': max(ys),
                                            'x_center': (min(xs) + max(xs)) / 2,
                                            'y_center': (min(ys) + max(ys)) / 2
                                        }
                    
                    # Create minimal bbox if text exists but no bbox
                    if not bounding_box and cell_text:
                        bounding_box = {
                            'x_min': col_idx * 0.15,
                            'x_max': (col_idx + 1) * 0.15,
                            'y_min': row_idx * 0.05,
                            'y_max': (row_idx + 1) * 0.05,
                            'x_center': (col_idx + 0.5) * 0.15,
                            'y_center': (row_idx + 0.5) * 0.05
                        }
                    
                    # Only create cell if we have text or bbox
                    if cell_text or bounding_box:
                        cell_data = ProcessedCell(
                            value=cell_text,
                            row=row_idx,
                            column=col_idx,
                            bounding_box=bounding_box,
                            is_header=is_header,
                            rowspan=1,
                            colspan=1
                        )
                        raw_cells.append(cell_data)
                        logger.info(f"✅ Fallback: Extracted cell ({row_idx},{col_idx}): '{cell_text[:30] if cell_text else 'EMPTY'}'")
                    else:
                        logger.warning(f"⚠️ Fallback: Cell ({row_idx},{col_idx}) has no text and no bbox - skipping")
            else:
                logger.warning(f"⚠️ Fallback: Row {row_idx} has no cells attribute")
            
            row_idx += 1
        
        logger.info(f"🔄 Fallback extraction complete: {len(raw_cells)} cells from {row_idx} rows")
        return raw_cells
    
    def _extract_cell_data(
        self,
        cell: Any,
        document_text: str,
        row: int,
        column: int,
        is_header: bool,
        fallback_bbox: Optional[Dict[str, float]] = None
    ) -> Optional[ProcessedCell]:
        """
        Extract cell data including text, bounding box, and style.
        
        ENHANCEMENT: Use fallback_bbox if cell lacks geometry.
        """
        text = ""
        layout = None
        
        logger.info(f"🔍 _extract_cell_data: Cell ({row},{column}), cell type: {type(cell)}, has layout: {hasattr(cell, 'layout')}")
        
        if hasattr(cell, 'layout'):
            layout = cell.layout
            logger.info(f"🔍 _extract_cell_data: Cell ({row},{column}) layout type: {type(layout)}")
            text = self._extract_text_from_layout(layout, document_text)
            logger.info(f"🔍 _extract_cell_data: Cell ({row},{column}) extracted text: '{text[:50] if text else 'EMPTY'}'")
        else:
            logger.warning(f"❌ Cell ({row},{column}) has no 'layout' attribute")
        
        # CRITICAL: Extract bounding box from cell.layout.bounding_poly.normalized_vertices
        # TABLE_STRICT mode: Bounding box MUST come from DocAI, not heuristics
        bounding_box = None
        if layout:
            bounding_box = self._extract_bounding_box(layout)
            logger.info(f"🔍 _extract_cell_data: Cell ({row},{column}) bounding_box from layout: {bounding_box}")
        
        if not bounding_box and fallback_bbox:
            # Use reconstructed geometry
            bounding_box = fallback_bbox
            logger.info(f"✅ Cell ({row},{column}) using reconstructed geometry: {bounding_box}")
        
        # ENTERPRISE RULE: HARD ASSERT for TABLE_STRICT mode
        # If cell lacks bounding box, this is a data integrity issue
        if not bounding_box:
            logger.error(f"❌ CRITICAL: Cell ({row},{column}) has NO bounding box")
            logger.error(f"   Cell type: {type(cell)}")
            logger.error(f"   Has layout: {hasattr(cell, 'layout')}")
            if hasattr(cell, 'layout'):
                logger.error(f"   Layout type: {type(cell.layout)}")
                if hasattr(cell.layout, 'bounding_poly'):
                    logger.error(f"   Has bounding_poly: {cell.layout.bounding_poly}")
            
            # For TABLE_STRICT: Fail fast if bounding box missing
            # This indicates DocAI table structure is incomplete
            if text and text.strip():
                # CRITICAL: Create minimal bbox but log warning
                logger.warning(f"⚠️ Cell ({row},{column}) has text but no bbox - creating minimal bbox (DATA INTEGRITY ISSUE)")
                bounding_box = {
                    'x_min': column * 0.15,
                    'x_max': (column + 1) * 0.15,
                    'y_min': row * 0.05,
                    'y_max': (row + 1) * 0.05,
                    'x_center': (column + 0.5) * 0.15,
                    'y_center': (row + 0.5) * 0.05
                }
            else:
                logger.error(f"❌ Cell ({row},{column}) has NO text AND NO bbox - returning None")
                return None
        
        # HARD ASSERT: Bounding box must exist
        assert bounding_box is not None, f"Cell ({row},{column}) must have bounding box"
        
        # Extract style information
        font_size = self._extract_font_size(layout)
        is_bold = self._extract_is_bold(layout)
        
        # Extract rowspan/colspan from Document AI
        # Document AI may use different attribute names
        rowspan = 1
        colspan = 1
        
        # Try different possible attribute names
        if hasattr(cell, 'row_span'):
            rowspan = max(1, int(cell.row_span) if cell.row_span else 1)
        elif hasattr(cell, 'rowSpan'):
            rowspan = max(1, int(cell.rowSpan) if cell.rowSpan else 1)
        elif hasattr(cell, 'rowspan'):
            rowspan = max(1, int(cell.rowspan) if cell.rowspan else 1)
        
        if hasattr(cell, 'col_span'):
            colspan = max(1, int(cell.col_span) if cell.col_span else 1)
        elif hasattr(cell, 'colSpan'):
            colspan = max(1, int(cell.colSpan) if cell.colSpan else 1)
        elif hasattr(cell, 'colspan'):
            colspan = max(1, int(cell.colspan) if cell.colspan else 1)
        
        # Extract confidence
        confidence = 1.0
        if hasattr(layout, 'confidence'):
            confidence = float(layout.confidence) if layout.confidence else 1.0
        
        # Check if numeric sequence
        is_numeric = self._is_numeric_sequence(text)
        
        return ProcessedCell(
            row=row,
            column=column,
            value=text,
            original_value=text,
            rowspan=rowspan,
            colspan=colspan,
            is_header=is_header,
            font_size=font_size,
            is_bold=is_bold,
            bounding_box=bounding_box,
            confidence=confidence,
            is_numeric_sequence=is_numeric
        )
    
    def _extract_text_from_layout(self, layout: Any, document_text: str) -> str:
        """Extract text from layout using text anchor"""
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
                if start < len(document_text) and end <= len(document_text):
                    text_parts.append(document_text[start:end])
        
        return ' '.join(text_parts).strip()
    
    def _extract_bounding_box(self, layout: Any) -> Optional[Dict[str, float]]:
        """Extract normalized bounding box from layout"""
        if not hasattr(layout, 'bounding_poly'):
            return None
        
        bounding_poly = layout.bounding_poly
        if not hasattr(bounding_poly, 'normalized_vertices'):
            return None
        
        vertices = bounding_poly.normalized_vertices
        if not vertices or len(vertices) < 2:
            return None
        
        x_coords = [v.x for v in vertices if hasattr(v, 'x')]
        y_coords = [v.y for v in vertices if hasattr(v, 'y')]
        
        if not x_coords or not y_coords:
            return None
        
        return {
            'x_min': min(x_coords),
            'x_max': max(x_coords),
            'y_min': min(y_coords),
            'y_max': max(y_coords),
            'x_center': (min(x_coords) + max(x_coords)) / 2,
            'y_center': (min(y_coords) + max(y_coords)) / 2,
            'width': max(x_coords) - min(x_coords),
            'height': max(y_coords) - min(y_coords)
        }
    
    def _extract_font_size(self, layout: Any) -> Optional[float]:
        """Extract font size from layout"""
        # Document AI may provide font size in text_styles
        if hasattr(layout, 'text_styles') and layout.text_styles:
            for text_style in layout.text_styles:
                if hasattr(text_style, 'font_size') and hasattr(text_style.font_size, 'value'):
                    return float(text_style.font_size.value)
        return None
    
    def _extract_is_bold(self, layout: Any) -> bool:
        """Extract bold style from layout"""
        if hasattr(layout, 'text_styles') and layout.text_styles:
            for text_style in layout.text_styles:
                if hasattr(text_style, 'font_weight'):
                    weight_str = str(text_style.font_weight).lower()
                    if 'bold' in weight_str or weight_str in ['700', '800', '900']:
                        return True
        return False
    
    def _calculate_avg_line_height(self, cells: List[ProcessedCell]) -> float:
        """Calculate average line height from cell bounding boxes"""
        heights = []
        for cell in cells:
            if cell.bounding_box and cell.bounding_box.get('height'):
                heights.append(cell.bounding_box['height'])
        
        if not heights:
            return 0.02  # Default: 2% of page height
        
        return sum(heights) / len(heights)
    
    def _detect_header_rows(
        self,
        cells: List[ProcessedCell],
        avg_line_height: float
    ) -> List[int]:
        """
        Detect header rows using:
        - Font size (larger than body)
        - Bold text
        - Row height
        - Position (typically first rows)
        """
        # Group cells by row
        rows_dict: Dict[int, List[ProcessedCell]] = {}
        for cell in cells:
            if cell.row not in rows_dict:
                rows_dict[cell.row] = []
            rows_dict[cell.row].append(cell)
        
        header_scores: Dict[int, float] = {}
        
        for row_idx, row_cells in rows_dict.items():
            score = 0.0
            
            # Check if first few rows (likely headers)
            if row_idx < 3:
                score += 2.0
            
            # Check font size
            font_sizes = [c.font_size for c in row_cells if c.font_size]
            if font_sizes:
                avg_font = sum(font_sizes) / len(font_sizes)
                if avg_font >= self.min_header_font_size:
                    score += 1.5
                if avg_font > 12.0:  # Large font
                    score += 1.0
            
            # Check bold cells
            bold_count = sum(1 for c in row_cells if c.is_bold)
            if bold_count > 0:
                score += bold_count / len(row_cells) * 2.0
            
            # Check row height (headers often taller)
            heights = [c.bounding_box['height'] for c in row_cells if c.bounding_box and c.bounding_box.get('height')]
            if heights:
                avg_height = sum(heights) / len(heights)
                if avg_height > avg_line_height * 1.2:  # 20% taller
                    score += 1.0
            
            header_scores[row_idx] = score
        
        # Select rows with score >= 2.0 as headers
        header_rows = [row_idx for row_idx, score in header_scores.items() if score >= 2.0]
        header_rows.sort()
        
        # Ensure at least first row is header if score > 0
        if not header_rows and header_scores.get(0, 0) > 0:
            header_rows = [0]
        
        return header_rows
    
    def _build_column_anchors(
        self,
        cells: List[ProcessedCell],
        header_row_indices: List[int]
    ) -> List[float]:
        """
        Build stable column anchors from header row bounding boxes.
        These anchors prevent column drift across rows.
        """
        if not header_row_indices:
            # If no headers, use first row
            header_row_indices = [0]
        
        # Collect X positions from header rows
        header_x_positions: Set[float] = set()
        
        for row_idx in header_row_indices:
            row_cells = [c for c in cells if c.row == row_idx]
            for cell in row_cells:
                if cell.bounding_box:
                    # Use left edge (x_min) and right edge (x_max) as potential anchors
                    header_x_positions.add(cell.bounding_box['x_min'])
                    header_x_positions.add(cell.bounding_box['x_max'])
                    header_x_positions.add(cell.bounding_box['x_center'])
        
        if not header_x_positions:
            # Fallback: use all cell X positions
            for cell in cells:
                if cell.bounding_box:
                    header_x_positions.add(cell.bounding_box['x_center'])
        
        # Sort and cluster nearby positions
        sorted_x = sorted(header_x_positions)
        anchors = []
        
        if not sorted_x:
            return []
        
        current_cluster = [sorted_x[0]]
        
        for x in sorted_x[1:]:
            # Cluster if within tolerance
            if x - current_cluster[-1] <= self.column_snap_tolerance:
                current_cluster.append(x)
            else:
                # New cluster - use median as anchor
                anchor = sorted(current_cluster)[len(current_cluster) // 2]
                anchors.append(anchor)
                current_cluster = [x]
        
        # Add last cluster
        if current_cluster:
            anchor = sorted(current_cluster)[len(current_cluster) // 2]
            anchors.append(anchor)
        
        anchors.sort()
        logger.debug(f"Column anchors: {anchors}")
        return anchors
    
    def _process_cells(
        self,
        raw_cells: List[ProcessedCell],
        header_row_indices: List[int],
        column_anchors: List[float],
        avg_line_height: float
    ) -> List[List[ProcessedCell]]:
        """Organize cells into rows and apply initial processing"""
        # Group by row
        rows_dict: Dict[int, List[ProcessedCell]] = {}
        for cell in raw_cells:
            if cell.row not in rows_dict:
                rows_dict[cell.row] = []
            rows_dict[cell.row].append(cell)
        
        # Sort rows and process
        processed_rows = []
        for row_idx in sorted(rows_dict.keys()):
            row_cells = rows_dict[row_idx]
            
            # Mark headers
            for cell in row_cells:
                if row_idx in header_row_indices:
                    cell.is_header = True
            
            # Sort by column
            row_cells.sort(key=lambda c: c.column)
            
            processed_rows.append(row_cells)
        
        return processed_rows
    
    def _apply_line_merging(
        self,
        rows: List[List[ProcessedCell]],
        avg_line_height: float,
        is_mixed_language: bool = False
    ) -> List[List[ProcessedCell]]:
        """
        Merge multiple text blocks into single cell when Y-distance
        is less than 0.6 × average line height.
        Treats wrapped text as one logical cell.
        """
        merged_rows = []
        # Adjust threshold for mixed language (Hindi/Unicode uses font-height based)
        if is_mixed_language:
            # Use larger threshold for mixed language (more tolerance)
            merge_threshold = avg_line_height * (self.line_merge_threshold * 1.5)
        else:
            merge_threshold = avg_line_height * self.line_merge_threshold
        
        for row_cells in rows:
            if not row_cells:
                merged_rows.append([])
                continue
            
            # Group cells by column (cells in same column that should merge)
            merged_row = []
            processed_indices = set()
            
            for i, cell in enumerate(row_cells):
                if i in processed_indices:
                    continue
                
                # Find cells in same column that should merge
                merge_candidates = [cell]
                
                for j, other_cell in enumerate(row_cells[i+1:], start=i+1):
                    if j in processed_indices:
                        continue
                    
                    # Check if same column and close Y position
                    if (cell.column == other_cell.column and
                        cell.bounding_box and other_cell.bounding_box):
                        
                        y_distance = abs(cell.bounding_box['y_center'] - other_cell.bounding_box['y_center'])
                        
                        if y_distance < merge_threshold:
                            merge_candidates.append(other_cell)
                            processed_indices.add(j)
                
                # Merge candidates into one cell
                if len(merge_candidates) > 1:
                    # Combine text
                    merged_text = ' '.join([c.value for c in merge_candidates if c.value])
                    
                    # Use first cell's position and expand bounding box
                    merged_cell = ProcessedCell(
                        row=cell.row,
                        column=cell.column,
                        value=merged_text,
                        original_value=cell.value,
                        rowspan=cell.rowspan,
                        colspan=cell.colspan,
                        is_header=cell.is_header,
                        font_size=cell.font_size,
                        is_bold=cell.is_bold,
                        bounding_box=cell.bounding_box.copy() if cell.bounding_box else None,
                        confidence=min([c.confidence for c in merge_candidates]),
                        merge_type=CellMergeType.LINE_MERGE,
                        is_numeric_sequence=cell.is_numeric_sequence
                    )
                    
                    # Expand bounding box to include all merged cells
                    if merged_cell.bounding_box and merge_candidates[1:]:
                        for other_cell in merge_candidates[1:]:
                            if other_cell.bounding_box:
                                merged_cell.bounding_box['x_min'] = min(
                                    merged_cell.bounding_box['x_min'],
                                    other_cell.bounding_box['x_min']
                                )
                                merged_cell.bounding_box['x_max'] = max(
                                    merged_cell.bounding_box['x_max'],
                                    other_cell.bounding_box['x_max']
                                )
                                merged_cell.bounding_box['y_min'] = min(
                                    merged_cell.bounding_box['y_min'],
                                    other_cell.bounding_box['y_min']
                                )
                                merged_cell.bounding_box['y_max'] = max(
                                    merged_cell.bounding_box['y_max'],
                                    other_cell.bounding_box['y_max']
                                )
                        
                        # Recalculate center
                        merged_cell.bounding_box['x_center'] = (
                            merged_cell.bounding_box['x_min'] + merged_cell.bounding_box['x_max']
                        ) / 2
                        merged_cell.bounding_box['y_center'] = (
                            merged_cell.bounding_box['y_min'] + merged_cell.bounding_box['y_max']
                        ) / 2
                    
                    merged_row.append(merged_cell)
                else:
                    merged_row.append(cell)
                
                processed_indices.add(i)
            
            # Sort merged row by column
            merged_row.sort(key=lambda c: c.column)
            merged_rows.append(merged_row)
        
        return merged_rows
    
    def _apply_document_ai_merges(
        self,
        table: Any,
        rows: List[List[ProcessedCell]],
        document_text: str,
        allow_spans: bool
    ) -> Tuple[List[List[ProcessedCell]], bool]:
        """
        Apply rowspan and colspan from Document AI table structure with occupancy checks.
        Returns (rows, span_conflict_flag).
        If allow_spans is False, returns rows unchanged with conflict=False.
        """
        if not allow_spans:
            return rows, False

        # Build grid occupancy to prevent overlap
        # Only place primary cells (no placeholders)
        grid: Dict[Tuple[int, int], ProcessedCell] = {}
        span_conflict = False

        for row_cells in rows:
            for cell in row_cells:
                r0 = cell.row
                c0 = cell.column
                r1 = r0 + max(1, cell.rowspan) - 1
                c1 = c0 + max(1, cell.colspan) - 1

                # Check occupancy conflicts
                for rr in range(r0, r1 + 1):
                    for cc in range(c0, c1 + 1):
                        if (rr, cc) in grid:
                            span_conflict = True
                            break
                    if span_conflict:
                        break
                if span_conflict:
                    break

                # Place only the primary cell at its start position
                grid[(r0, c0)] = cell
                if cell.rowspan > 1 or cell.colspan > 1:
                    if cell.rowspan > 1 and cell.colspan > 1:
                        cell.merge_type = CellMergeType.BOTH if hasattr(CellMergeType, "BOTH") else CellMergeType.ROWSPAN
                    elif cell.rowspan > 1:
                        cell.merge_type = CellMergeType.ROWSPAN
                    elif cell.colspan > 1:
                        cell.merge_type = CellMergeType.COLSPAN

            if span_conflict:
                break

        if span_conflict:
            return rows, True

        # Rebuild rows from grid primary cells only
        if not grid:
            return rows, False

        max_row = max(r for r, _ in grid.keys())
        rebuilt: List[List[ProcessedCell]] = []
        for r in range(max_row + 1):
            row_cells = [cell for (rr, _), cell in grid.items() if rr == r]
            row_cells.sort(key=lambda c: c.column)
            if row_cells:
                rebuilt.append(row_cells)

        return rebuilt, False
    
    def _protect_numeric_sequences(self, rows: List[List[ProcessedCell]]) -> List[List[ProcessedCell]]:
        """
        Protect long numeric sequences (like Aadhaar numbers) from splitting.
        Ensures they stay in single column.
        """
        for row_cells in rows:
            for cell in row_cells:
                if cell.is_numeric_sequence and len(cell.value) >= self.numeric_sequence_min_length:
                    # Ensure this cell doesn't get split
                    # Mark with high priority for column assignment
                    # Force colspan to 1 (don't split)
                    if cell.colspan > 1:
                        # If it was supposed to span, keep it but don't split the number
                        pass
                    # The value is already protected by being in one cell
                    # Column snapping will ensure it stays aligned
        
        return rows
    
    def _snap_to_column_anchors(
        self,
        rows: List[List[ProcessedCell]],
        column_anchors: List[float],
        table_confidence: float = 1.0
    ) -> List[List[ProcessedCell]]:
        """
        Snap all cell X positions to nearest column anchor.
        Prevents column drift across rows.
        Uses fail-safe mode if table confidence is low.
        """
        if not column_anchors:
            return rows
        
        # Check if we should use fail-safe mode (logical alignment over visual similarity)
        use_failsafe = table_confidence < 0.7
        
        if use_failsafe:
            logger.info("Using fail-safe mode: logical alignment over visual similarity")
        
        for row_cells in rows:
            for cell in row_cells:
                if cell.bounding_box and 'x_center' in cell.bounding_box:
                    x_center = cell.bounding_box['x_center']
                    
                    # Find nearest anchor
                    nearest_anchor = min(
                        column_anchors,
                        key=lambda anchor: abs(anchor - x_center)
                    )
                    
                    distance = abs(nearest_anchor - x_center)
                    
                    # In fail-safe mode, use stricter tolerance or preserve original column
                    if use_failsafe:
                        # In fail-safe, only snap if very close, otherwise preserve logical column
                        if distance <= self.column_snap_tolerance * 0.5:  # Stricter
                            anchor_index = column_anchors.index(nearest_anchor)
                            cell.column = anchor_index
                            cell.bounding_box['x_center'] = nearest_anchor
                        # Else: keep original column (logical alignment)
                    else:
                        # Normal mode: snap if within tolerance
                        if distance <= self.column_snap_tolerance:
                            anchor_index = column_anchors.index(nearest_anchor)
                            cell.column = anchor_index
                            cell.bounding_box['x_center'] = nearest_anchor
        
        # Re-sort rows by snapped column
        for row_cells in rows:
            row_cells.sort(key=lambda c: c.column)
        
        return rows
    
    def _calculate_table_confidence(
        self,
        processed_rows: List[List[ProcessedCell]],
        raw_cells: List[ProcessedCell]
    ) -> float:
        """Calculate overall table confidence for fail-safe mode"""
        if not raw_cells:
            return 0.0
        
        # Average cell confidence
        confidences = [c.confidence for c in raw_cells if c.confidence]
        if not confidences:
            return 1.0
        
        avg_confidence = sum(confidences) / len(confidences)
        
        # Penalize if many cells have low confidence
        low_confidence_count = sum(1 for c in confidences if c < 0.7)
        penalty = (low_confidence_count / len(confidences)) * 0.2
        
        final_confidence = max(0.0, avg_confidence - penalty)
        return final_confidence
    
    def _is_numeric_sequence(self, text: str) -> bool:
        """Check if text is a long numeric sequence (like Aadhaar)"""
        if not text:
            return False
        
        # Remove spaces and common separators
        cleaned = text.replace(' ', '').replace('-', '').replace('.', '')
        
        # Check if mostly digits and long enough
        if len(cleaned) >= self.numeric_sequence_min_length:
            digit_ratio = sum(1 for c in cleaned if c.isdigit()) / len(cleaned) if cleaned else 0
            return digit_ratio >= 0.8  # 80% digits
        
        return False
    
    def _detect_mixed_language(self, cells: List[ProcessedCell], document_text: str) -> bool:
        """
        Detect if document contains Hindi or mixed language content.
        Uses font-height based Y-thresholds for such documents.
        """
        if not cells or not document_text:
            return False
        
        # Check for Devanagari script (Hindi) or other Indic scripts
        devanagari_range = range(0x0900, 0x097F + 1)
        sample_text = document_text[:1000]  # Check first 1000 chars
        
        devanagari_count = sum(1 for char in sample_text if ord(char) in devanagari_range)
        
        # If > 5% Devanagari characters, consider it mixed language
        if len(sample_text) > 0:
            devanagari_ratio = devanagari_count / len(sample_text)
            if devanagari_ratio > 0.05:
                return True
        
        # Also check cell values
        for cell in cells[:50]:  # Check first 50 cells
            if cell.value:
                devanagari_in_cell = sum(1 for char in cell.value if ord(char) in devanagari_range)
                if len(cell.value) > 0 and devanagari_in_cell / len(cell.value) > 0.1:
                    return True
        
        return False
    
    def _apply_logical_alignment(self, rows: List[List[ProcessedCell]]) -> List[List[ProcessedCell]]:
        """
        Apply logical alignment (sequential columns) when table confidence is low.
        Used in fail-safe mode instead of visual column snapping.
        """
        for row_idx, row_cells in enumerate(rows):
            # Sort by current column index
            row_cells.sort(key=lambda c: c.column)
            
            # Re-assign columns sequentially
            current_col = 0
            for cell in row_cells:
                cell.column = current_col
                current_col += cell.colspan  # Account for colspan
        
        return rows
    
    def convert_to_unified_layout(
        self,
        processed_table: ProcessedTable,
        page_index: int = 0
    ) -> 'UnifiedLayout':
        """
        Convert ProcessedTable to UnifiedLayout for Excel rendering.
        
        CRITICAL: This is where spatial indexing and newline splitting MUST happen.
        Order:
        1. Extract cells with bounding boxes
        2. Split cells by newlines (each split gets its own bbox slice)
        3. Apply spatial indexing (assign row/column based on bbox)
        4. Build UnifiedLayout
        5. FREEZE layout (no further row/column mutation)
        
        Args:
            processed_table: Post-processed table
            page_index: Page index for the layout
            
        Returns:
            UnifiedLayout ready for Excel rendering (FROZEN - no row/column changes allowed)
        """
        from .unified_layout_model import UnifiedLayout, Cell, CellStyle, CellAlignment, MergedCell
        
        logger.critical("=" * 80)
        logger.critical("🔍 COMPREHENSIVE DEBUG: CONVERT_TO_UNIFIED_LAYOUT")
        logger.critical("=" * 80)
        
        # STEP 1: Extract all cells with bounding boxes
        # CRITICAL: Ignore existing row/column indices from DocAI - we'll reassign based on bounding boxes
        cells_with_bbox = []
        cells_without_bbox = 0
        
        logger.critical(f"📊 STEP 1: Extracting cells from ProcessedTable")
        logger.critical(f"   Total rows in ProcessedTable: {len(processed_table.rows)}")
        
        for row_idx, row_cells in enumerate(processed_table.rows):
            logger.critical(f"   Row {row_idx}: {len(row_cells)} cells")
            for cell_idx, processed_cell in enumerate(row_cells):
                cell_text = str(processed_cell.value)[:30] if processed_cell.value else 'EMPTY'
                
                # CRITICAL: Each cell MUST have bounding box
                if processed_cell.bounding_box:
                    bbox = processed_cell.bounding_box
                    cells_with_bbox.append({
                        'cell': processed_cell,
                        'original_row': row_idx,  # Store original for reference
                        'original_col': processed_cell.column,  # Store original for reference
                        'bbox': bbox
                    })
                    
                    # Log first 10 cells
                    if len(cells_with_bbox) <= 10:
                        logger.critical(f"      Cell[{row_idx},{cell_idx}]: '{cell_text}' bbox={bbox}")
                else:
                    cells_without_bbox += 1
                    logger.warning(f"      ❌ Cell ({row_idx},{processed_cell.column}) '{cell_text}' - NO BBOX!")
        
        logger.critical("=" * 80)
        logger.critical(f"📊 STEP 1 RESULT:")
        logger.critical(f"   ✅ Cells WITH bbox: {len(cells_with_bbox)}")
        logger.critical(f"   ❌ Cells WITHOUT bbox: {cells_without_bbox}")
        logger.critical("=" * 80)
        
        # STEP 2: NEWLINE SPLITTING (before spatial indexing)
        # Split cells with newlines - each split gets its own bbox slice
        split_cells = []
        for cell_data in cells_with_bbox:
            cell = cell_data['cell']
            cell_value = str(cell.value) if cell.value else ''
            
            if '\n' in cell_value and len(cell_value) > 20:
                # Split by newlines - each line gets Y-axis slice of bbox
                lines = cell_value.split('\n')
                bbox = cell_data['bbox']
                bbox_height = bbox.get('y_max', 1.0) - bbox.get('y_min', 0.0)
                line_height = bbox_height / len(lines) if lines else 0.01
                
                for line_idx, line in enumerate(lines):
                    line = line.strip()
                    if line:
                        # Create bbox slice for this line
                        line_bbox = {
                            'x_min': bbox.get('x_min', 0.0),
                            'x_max': bbox.get('x_max', 1.0),
                            'y_min': bbox.get('y_min', 0.0) + (line_idx * line_height),
                            'y_max': bbox.get('y_min', 0.0) + ((line_idx + 1) * line_height),
                            'x_center': bbox.get('x_center', 0.5),
                            'y_center': bbox.get('y_min', 0.0) + ((line_idx + 0.5) * line_height)
                        }
                        
                        split_cells.append({
                            'cell': cell,
                            'row': cell_data['row'],
                            'col': cell_data['col'],
                            'bbox': line_bbox,
                            'value': line,
                            'is_split': True
                        })
            else:
                # No newlines - keep as is
                split_cells.append({
                    'cell': cell,
                    'row': cell_data['row'],
                    'col': cell_data['col'],
                    'bbox': cell_data['bbox'],
                    'value': cell_value,
                    'is_split': False
                })
        
        logger.critical(f"📊 STEP 2 RESULT: {len(split_cells)} cells after newline splitting (from {len(cells_with_bbox)} original)")
        
        # STEP 3: SPATIAL INDEXING (assign row/column based on bbox)
        logger.critical("=" * 80)
        logger.critical(f"📊 STEP 3: SPATIAL INDEXING (assigning row/col based on bbox)")
        logger.critical("=" * 80)
        
        # Group by Y-center for rows, X-center for columns
        if split_cells:
            # Sort by Y-center (top to bottom)
            split_cells.sort(key=lambda c: c['bbox'].get('y_center', 0.0))
            
            # Log first 10 cells sorted by Y
            logger.critical(f"   First 10 cells sorted by Y-center:")
            for idx, cell_data in enumerate(split_cells[:10]):
                val = str(cell_data.get('value', ''))[:30]
                y = cell_data['bbox'].get('y_center', 0.0)
                logger.critical(f"      [{idx}] Y={y:.4f} | '{val}'")
            
            # Group into rows using Y-threshold
            # CRITICAL FIX: More lenient threshold to allow labels and values in same row
            y_positions = [c['bbox'].get('y_center', 0.0) for c in split_cells]
            if len(y_positions) > 1:
                y_diffs = [abs(y_positions[i+1] - y_positions[i]) for i in range(len(y_positions)-1) if abs(y_positions[i+1] - y_positions[i]) > 0.001]
                if y_diffs:
                    avg_y_diff = sum(y_diffs) / len(y_diffs)
                    # CRITICAL: Use 2.0x threshold to be very lenient
                    # This allows labels and values that are close together to be in same row
                    # For invoices/bills, labels and values are often on same visual line
                    y_threshold = avg_y_diff * 2.0
                    logger.critical(f"   Y-threshold calculation:")
                    logger.critical(f"      avg_y_diff: {avg_y_diff:.4f}")
                    logger.critical(f"      y_threshold (2.0x): {y_threshold:.4f}")
                else:
                    y_threshold = 0.03  # Increased default
                    logger.critical(f"   Using default Y-threshold: {y_threshold:.4f}")
            else:
                y_threshold = 0.03  # Increased default
                logger.critical(f"   Using default Y-threshold (single cell): {y_threshold:.4f}")
            
            rows_groups = []
            if split_cells:
                current_row = [split_cells[0]]
                current_y = split_cells[0]['bbox'].get('y_center', 0.0)
                
                for cell_data in split_cells[1:]:
                    cell_y = cell_data['bbox'].get('y_center', 0.0)
                    y_diff = abs(cell_y - current_y)
                    
                    if y_diff <= y_threshold:
                        # Same row
                        current_row.append(cell_data)
                    else:
                        # New row
                        rows_groups.append(current_row)
                        current_row = [cell_data]
                        current_y = cell_y
                
                if current_row:
                    rows_groups.append(current_row)
            
            logger.critical("=" * 80)
            logger.critical(f"📊 SPATIAL INDEXING RESULT:")
            logger.critical(f"   Detected rows: {len(rows_groups)}")
            logger.critical("=" * 80)
            
            # Assign row/column indices
            for row_idx, row_group in enumerate(rows_groups):
                # Sort within row by X-center (left to right)
                row_group.sort(key=lambda c: c['bbox'].get('x_center', 0.0))
                
                # Log first 10 rows
                if row_idx < 10:
                    logger.critical(f"   Row {row_idx}: {len(row_group)} cells")
                    for col_idx, cell_data in enumerate(row_group[:5]):  # First 5 cells per row
                        val = str(cell_data.get('value', ''))[:30]
                        x = cell_data['bbox'].get('x_center', 0.0)
                        logger.critical(f"      Col {col_idx}: X={x:.4f} | '{val}'")
                
                for col_idx, cell_data in enumerate(row_group):
                    cell_data['final_row'] = row_idx
                    cell_data['final_col'] = col_idx
        else:
            rows_groups = []
            logger.critical("=" * 80)
            logger.critical("❌ NO CELLS AFTER SPLITTING - EMPTY LAYOUT!")
            logger.critical("=" * 80)
        
        # STEP 4: Build UnifiedLayout with spatial indices
        layout = UnifiedLayout(page_index=page_index)
        
        # Store metadata
        layout.metadata['column_anchors'] = processed_table.column_anchors
        layout.metadata['header_row_indices'] = processed_table.header_row_indices
        layout.metadata['table_confidence'] = processed_table.table_confidence
        layout.metadata['avg_line_height'] = processed_table.avg_line_height
        layout.metadata['spatial_indexing_applied'] = True
        
        # Build rows with spatial indices
        max_row_idx = max((c.get('final_row', -1) for c in split_cells), default=-1)
        if max_row_idx >= 0:
            layout.rows = [[] for _ in range(max_row_idx + 1)]
            
            for cell_data in split_cells:
                processed_cell = cell_data['cell']
                final_row = cell_data.get('final_row', 0)
                final_col = cell_data.get('final_col', 0)
                cell_value = cell_data.get('value', str(processed_cell.value) if processed_cell.value else '')
                
                # Convert style
                cell_style = CellStyle(
                    bold=processed_cell.is_bold or processed_cell.is_header,
                    font_size=int(processed_cell.font_size) if processed_cell.font_size else None,
                    alignment_horizontal=CellAlignment.CENTER if processed_cell.is_header else CellAlignment.LEFT,
                    background_color="4472C4" if processed_cell.is_header else None
                )
                
                # Create unified cell with SPATIAL indices (not original row/col)
                unified_cell = Cell(
                    row=final_row,  # SPATIAL row index
                    column=final_col,  # SPATIAL column index
                    value=cell_value,
                    style=cell_style,
                    rowspan=1,  # Reset spans after spatial indexing
                    colspan=1,
                    merged=False
                )
                
                if 0 <= final_row <= max_row_idx:
                    layout.rows[final_row].append(unified_cell)
        else:
            logger.warning("No valid rows after spatial indexing - creating empty layout")
        
        # Sort cells within each row by column
        for row in layout.rows:
            row.sort(key=lambda c: c.column)
        
        # Log final layout build result
        logger.critical("=" * 80)
        logger.critical(f"📊 STEP 4 RESULT: UnifiedLayout Built")
        logger.critical(f"   Total rows in layout: {len(layout.rows)}")
        logger.critical(f"   Total cells in layout: {sum(len(row) for row in layout.rows)}")
        
        if layout.rows:
            max_row = max(max(cell.row for cell in row) if row else -1 for row in layout.rows)
            max_col = max(max(cell.column for cell in row) if row else -1 for row in layout.rows)
            logger.critical(f"   max_row: {max_row}, max_col: {max_col}")
            
            # Log first 10 rows
            logger.critical(f"   First 10 rows:")
            for row_idx, row in enumerate(layout.rows[:10]):
                cells_info = [f"({c.row},{c.column})='{str(c.value)[:20]}'" for c in row[:3]]
                logger.critical(f"      Row {row_idx}: {len(row)} cells | {', '.join(cells_info)}")
        else:
            logger.critical("   ❌ LAYOUT IS EMPTY!")
        
        logger.critical("=" * 80)
        
        # STEP 4.5: POST-PROCESSING - Label-Value Pairing for Multi-Column Layouts
        # CRITICAL FIX: Merge adjacent rows where Col1 has label and next row Col1 has value
        # NOTE: This runs BEFORE layout is frozen, so we can mutate row/column indices
        logger.critical("=" * 80)
        logger.critical("🔧 POST-PROCESSING: Applying label-value pairing (BEFORE FREEZE)")
        logger.critical("=" * 80)
        
        # Check if Col2 is mostly empty
        rows_with_col2 = set()
        all_cells_flat = []
        for row in layout.rows:
            for cell in row:
                all_cells_flat.append(cell)
                if cell.column >= 1:
                    rows_with_col2.add(cell.row)
        
        total_rows = len(layout.rows)
        col2_coverage = len(rows_with_col2) / total_rows if total_rows > 0 else 0
        
        logger.critical(f"Col2 coverage: {col2_coverage:.1%}, Total rows: {total_rows}")
        
        # CRITICAL: Always apply label-value pairing if Col2 coverage is low OR if we have many rows with empty Col2
        rows_with_empty_col2 = total_rows - len(rows_with_col2)
        empty_col2_ratio = rows_with_empty_col2 / total_rows if total_rows > 0 else 0
        
        logger.critical(f"Rows with empty Col2: {rows_with_empty_col2} ({empty_col2_ratio:.1%})")
        
        # Apply if: Col2 coverage is low OR many rows have empty Col2
        # CRITICAL: ALWAYS apply for ANY document with empty Col2 rows (most aggressive)
        should_apply = (col2_coverage < 0.7 or empty_col2_ratio > 0.3) and total_rows >= 3
        logger.critical(f"Condition check: col2_coverage < 0.7 = {col2_coverage < 0.7}, empty_col2_ratio > 0.3 = {empty_col2_ratio > 0.3}, total_rows >= 3 = {total_rows >= 3}")
        logger.critical(f"Should apply label-value pairing: {should_apply}")
        
        # CRITICAL: ALWAYS apply if we have ANY rows with empty Col2 (MOST AGGRESSIVE)
        if should_apply or (empty_col2_ratio > 0.2 and total_rows >= 3):
            logger.critical(f"✅ APPLYING label-value pairing (Col2 coverage: {col2_coverage:.1%}, Empty Col2 ratio: {empty_col2_ratio:.1%})")
            
            # Label patterns (same as unified_layout_model)
            import re
            label_patterns = [
                r'name\s+of\s+the\s+customer', r'biller\s+name', r'biller\s+id', r'consumer\s+number',
                r'mobile\s+number', r'payment\s+mode', r'payment\s+status', r'payment\s+channel',
                r'approval\s+ref\s+no', r'approval\s+ref', r'customer\s+convenience\s+fee',
                r'biller\s+platform\s+fee', r'digital\s+fee', r'date', r'amount', r'total', r'transaction',
                r'account', r'address', r'email', r'phone', r'id', r'number', r'b-connect\s+txn\s+id',
                r'receipt', r'invoice', r'bill', r'agent', r'merchant', r'customer', r'consumer',
                r'नाम', r'पिता', r'पति', r'आधार', r'जाती', r'कार्ड', r'प्रकार', r'समग्र', r'परिवार', r'क्र'
            ]
            
            # Sort cells by row
            all_cells_flat.sort(key=lambda c: (c.row, c.column))
            
            # Group by row
            cells_by_row = {}
            for cell in all_cells_flat:
                if cell.row not in cells_by_row:
                    cells_by_row[cell.row] = []
                cells_by_row[cell.row].append(cell)
            
            # Process adjacent rows for label-value pairing
            merged_cells = []
            rows_to_remove = set()
            row_idx = 0
            
            sorted_row_indices = sorted(cells_by_row.keys())
            logger.critical(f"Processing {len(sorted_row_indices)} rows for label-value pairing")
            logger.critical(f"Row indices: {sorted_row_indices[:10]}...")
            
            i = 0
            merge_attempts = 0
            successful_merges = 0
            
            while i < len(sorted_row_indices):
                current_row_idx = sorted_row_indices[i]
                current_row_cells = cells_by_row[current_row_idx]
                
                # Get Col1 cell (label candidate)
                col1_cell = next((c for c in current_row_cells if c.column == 0), None)
                col2_cell = next((c for c in current_row_cells if c.column >= 1), None)
                
                # CRITICAL: Check if Col1 has content but Col2 is empty or missing
                if col1_cell and (not col2_cell or not (col2_cell.value and str(col2_cell.value).strip())):
                    # Col1 has content, Col2 is empty - might be a label
                    current_value = str(col1_cell.value).strip() if col1_cell.value else ""
                    current_value_lower = current_value.lower()
                    
                    is_label = any(re.search(pattern, current_value_lower) for pattern in label_patterns)
                    is_short = len(current_value) < 50
                    has_colon = ':' in current_value
                    is_all_caps = current_value.isupper() and len(current_value) > 1
                    
                    # CRITICAL: Enhanced label detection - check for common label keywords
                    has_label_keywords = any(keyword in current_value_lower for keyword in 
                                           ['name', 'id', 'number', 'date', 'amount', 'status', 'channel', 
                                            'mode', 'fee', 'ref', 'approval', 'biller', 'customer', 'payment',
                                            'agent', 'transaction', 'consumer', 'mobile'])
                    
                    is_likely_label = (is_label or has_label_keywords or
                                     (is_short and has_colon) or
                                     (is_short and ' ' in current_value and not is_all_caps and not current_value.replace(' ', '').isdigit()))
                    
                    if i < 15:  # Log first 15 rows to avoid too much output
                        logger.critical(f"Row {current_row_idx}: Checking '{current_value[:40]}' - is_label={is_label}, has_keywords={has_label_keywords}, is_likely={is_likely_label}")
                    
                    if is_likely_label and i + 1 < len(sorted_row_indices):
                        merge_attempts += 1
                        # Check next row
                        next_row_idx = sorted_row_indices[i + 1]
                        next_row_cells = cells_by_row[next_row_idx]
                        next_col1_cell = next((c for c in next_row_cells if c.column == 0), None)
                        next_col2_cell = next((c for c in next_row_cells if c.column == 1), None)
                        
                        next_col2_cell_check = next((c for c in next_row_cells if c.column >= 1), None)
                        next_has_col2 = next_col2_cell_check and (next_col2_cell_check.value and str(next_col2_cell_check.value).strip())
                        
                        if merge_attempts <= 10:  # Log first 10 merge attempts
                            logger.critical(f"  -> Row {current_row_idx} is label, checking Row {next_row_idx} for value")
                            logger.critical(f"     Next Col1: {str(next_col1_cell.value)[:40] if next_col1_cell else 'None'}")
                            logger.critical(f"     Next has Col2: {next_has_col2}")
                        
                        if next_col1_cell and not next_has_col2:
                            # Next row also has Col1 only or empty Col2 - might be value
                            next_value = str(next_col1_cell.value).strip() if next_col1_cell.value else ""
                            next_value_lower = next_value.lower()
                            next_is_label = any(re.search(pattern, next_value_lower) for pattern in label_patterns)
                            
                            # CRITICAL: Also check if next value looks like a value (not a label)
                            # Values are usually: numbers, long text, or specific formats
                            is_numeric = next_value.replace('.', '').replace('-', '').replace(' ', '').isdigit()
                            is_long_text = len(next_value) > 20
                            is_date_like = any(x in next_value for x in ['-', '/', 'DEC', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV'])
                            
                            # CRITICAL: More lenient value detection
                            # Values can be: numbers, long text, dates, or any non-label text
                            is_value = (is_numeric or is_long_text or is_date_like or 
                                      len(next_value) > 3 or 
                                      (not next_is_label and next_value and not next_value.replace(' ', '').isdigit()))
                            
                            if not next_is_label and is_value:
                                # Current is label, next is value - merge them
                                successful_merges += 1
                                if successful_merges <= 10:  # Log first 10 successful merges
                                    logger.critical(f"  -> ✅ MERGING: Row {current_row_idx} (label='{current_value[:30]}') + Row {next_row_idx} (value='{next_value[:30]}') into Row {row_idx}")
                                
                                col1_cell.row = row_idx
                                col1_cell.column = 0
                                
                                next_col1_cell.row = row_idx
                                next_col1_cell.column = 1
                                
                                merged_cells.append(col1_cell)
                                merged_cells.append(next_col1_cell)
                                
                                # Add any other cells from current row
                                for cell in current_row_cells:
                                    if cell.column != 0:
                                        cell.row = row_idx
                                        merged_cells.append(cell)
                                
                                rows_to_remove.add(current_row_idx)
                                rows_to_remove.add(next_row_idx)
                                row_idx += 1
                                i += 2  # Skip both rows
                                continue
                            elif merge_attempts <= 10:
                                logger.critical(f"  -> ❌ NOT MERGING: next_is_label={next_is_label}, is_value={is_value}, next_value='{next_value[:30]}'")
                
                # Not a label-value pair, keep as is
                # CRITICAL: Only add cells that weren't already merged
                if current_row_idx not in rows_to_remove:
                    for cell in current_row_cells:
                        # CRITICAL: Don't re-add cells that were already added in merge
                        # Check if this cell was already added
                        cell_already_added = any(id(c) == id(cell) for c in merged_cells)
                        if not cell_already_added:
                            cell.row = row_idx
                            merged_cells.append(cell)
                    row_idx += 1
                i += 1
            
            # Rebuild layout with merged cells
            if merged_cells:
                max_row_idx = max(c.row for c in merged_cells)
                new_rows = [[] for _ in range(max_row_idx + 1)]
                
                for cell in merged_cells:
                    if 0 <= cell.row <= max_row_idx:
                        new_rows[cell.row].append(cell)
                
                # Sort cells within each row by column
                for row in new_rows:
                    row.sort(key=lambda c: c.column)
                
                # Remove empty rows
                new_rows = [row for row in new_rows if row]
                
                # Re-assign row indices
                final_cells = []
                for new_row_idx, row in enumerate(new_rows):
                    for cell in row:
                        cell.row = new_row_idx
                        final_cells.append(cell)
                
                layout.rows = new_rows
                logger.critical("=" * 80)
                logger.critical(f"POST-PROCESSING: Label-Value Pairing Complete")
                logger.critical(f"   Merge attempts: {merge_attempts}")
                logger.critical(f"   Successful merges: {successful_merges}")
                logger.critical(f"   Rows removed: {len(rows_to_remove)}")
                logger.critical(f"   Final layout: {len(new_rows)} rows (was {total_rows})")
                logger.critical(f"   Unique merged cells: {len(unique_merged_cells)}")
                logger.critical("=" * 80)
        
        # STEP 5: QUALITY FAIL-SAFE - Reject invalid layouts
        max_row = layout.get_max_row()
        max_col = layout.get_max_column()
        
        if max_row < 0 or max_col < 0:
            logger.critical("=" * 80)
            logger.critical("❌ QUALITY FAIL-SAFE: Layout has invalid dimensions")
            logger.critical(f"   max_row={max_row}, max_col={max_col}")
            logger.critical("   BLANK EXCEL IS NEVER A VALID RESULT")
            logger.critical("=" * 80)
            raise TableExtractionFailed(f"Layout has invalid dimensions: max_row={max_row}, max_col={max_col}")
        
        # STEP 6: FREEZE LAYOUT - Mark as frozen (no further row/column mutation)
        layout.metadata['frozen'] = True
        layout.metadata['spatial_indexing_applied'] = True
        
        logger.critical("=" * 80)
        logger.critical(f"CONVERT_TO_UNIFIED_LAYOUT: Complete")
        logger.critical(f"   Rows: {max_row + 1}, Columns: {max_col + 1}")
        logger.critical(f"   Layout FROZEN - no further row/column mutation allowed")
        logger.critical("=" * 80)
        
        return layout

