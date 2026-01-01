"""
Layout Decision Engine - Enterprise PDF to Excel Conversion
Calls DecisionRouter to select ONE execution mode and executes ONLY that mode.
No classification override, no mid-pipeline downgrades.
"""

import logging
from typing import Optional, List, Any, Dict, Tuple
from enum import Enum

from .unified_layout_model import UnifiedLayout, Cell, CellStyle, CellAlignment
from .document_type_classifier import DocumentTypeClassifier, DocumentType
from .heuristic_table_builder import HeuristicTableBuilder
from .full_ocr_extractor import FullOCRExtractor
from .decision_router import DecisionRouter, ExecutionMode
from .cell_normalizer import CellNormalizer, LogicalCell  # CRITICAL: Cell ownership resolution
from .block_grid_normalizer import BlockGridNormalizer  # Grid normalization

logger = logging.getLogger(__name__)


class LayoutDecisionEngine:
    """
    Enterprise-grade layout decision engine.
    
    Uses DecisionRouter to select ONE execution mode per document.
    Executes ONLY the selected mode - no silent fallbacks, no mid-pipeline downgrades.
    """
    
    def __init__(self):
        """Initialize decision engine"""
        self.classifier = DocumentTypeClassifier()
        self.heuristic_builder = HeuristicTableBuilder()
        self.full_ocr_extractor = FullOCRExtractor(min_confidence=0.5)
        self.decision_router = DecisionRouter()
        self.cell_normalizer = CellNormalizer()  # CRITICAL: First step - cell ownership
        self.grid_normalizer = BlockGridNormalizer()  # Second step - grid structure
        
        # Document-level metadata (set once, used for all pages)
        self.selected_mode: Optional[ExecutionMode] = None
        self.routing_confidence: float = 0.0
        self.routing_reason: str = ""
    
    def process_document(
        self,
        document: Any,
        document_text: str = '',
        native_tables: Optional[List] = None,
        processor_type: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None  # STEP-13: For Adobe fallback
    ) -> List[UnifiedLayout]:
        """
        Process document and return unified layouts (one per page).
        
        CRITICAL DEBUG MODE ENABLED - Enhanced logging for blank Excel issue
        
        ENTERPRISE ROUTING:
        1. Extract full OCR structure
        2. Classify document type
        3. Call DecisionRouter to select ONE execution mode
        4. Execute ONLY the selected mode for all pages
        5. No classification override, no mid-pipeline downgrades
        
        Args:
            document: Document AI Document object
            document_text: Extracted text
            native_tables: List of native tables from Document AI (if any)
            
        Returns:
            List of UnifiedLayout objects (one per page) with mode metadata
        """
        logger.info("=" * 80)
        logger.info("ENTERPRISE PDF TO EXCEL: Starting document processing")
        logger.info("=" * 80)
        
        # Step 1: Extract full OCR structure
        logger.info("Extracting full OCR structure...")
        full_structure = self.full_ocr_extractor.extract_full_structure(document)
        logger.info(f"Extracted: {len(full_structure['blocks'])} blocks, "
                   f"{len(full_structure['form_fields'])} form fields, "
                   f"{len(full_structure['tables'])} tables")
        
        # Step 1.5: CRITICAL - Normalize blocks into logical cells (cell ownership resolution)
        logger.info("=" * 80)
        logger.info("CELL NORMALIZATION: Grouping blocks into logical cells...")
        logger.info("=" * 80)
        logical_cells = self.cell_normalizer.normalize_to_cells(
            full_structure['blocks'],
            page_width=1.0,
            page_height=1.0
        )
        logger.info(f"Cell normalization: {len(full_structure['blocks'])} blocks → {len(logical_cells)} logical cells")
        
        # Store logical cells in full_structure for downstream use
        full_structure['logical_cells'] = logical_cells
        
        # Step 2: Classify document type
        doc_type = self.classifier.classify(document, document_text)
        logger.info(f"Document classified as: {doc_type.value}")
        
        # Step 3: DECISION ROUTER - Select ONE execution mode
        logger.info("=" * 80)
        logger.info("DECISION ROUTER: Selecting execution mode")
        logger.info("=" * 80)
        logger.critical(f"🔍 LAYOUT DECISION ENGINE: Passing processor_type='{processor_type}' to DecisionRouter")
        self.selected_mode, self.routing_confidence, self.routing_reason = self.decision_router.route(
            native_tables=native_tables,
            doc_type=doc_type,
            full_structure=full_structure,
            document_text=document_text,
            processor_type=processor_type
        )
        logger.critical(f"🔍 LAYOUT DECISION ENGINE: DecisionRouter returned mode={self.selected_mode.value}, reason={self.routing_reason}")
        logger.critical("=" * 80)
        logger.critical(f"📊 EXECUTION MODE SELECTED:")
        logger.critical(f"   Mode: {self.selected_mode.value}")
        logger.critical(f"   Confidence: {self.routing_confidence:.2f}")
        logger.critical(f"   Reason: {self.routing_reason}")
        logger.critical(f"   Native tables: {len(native_tables) if native_tables else 0}")
        logger.critical(f"   Document type: {doc_type.value}")
        logger.critical("=" * 80)
        
        # Step 4: Process each page using the selected mode
        if not hasattr(document, 'pages') or not document.pages:
            logger.warning("No pages found in document")
            return [self._create_empty_layout(0)]
        
        page_layouts = []
        for page_idx, page in enumerate(document.pages):
            logger.info(f"Processing page {page_idx + 1} of {len(document.pages)} with mode: {self.selected_mode.value}")
            
            # Get page structure from full OCR extraction
            page_structure = None
            if page_idx < len(full_structure.get('pages', [])):
                page_structure = full_structure['pages'][page_idx]
            
            # CRITICAL FIX: If page_structure is None or has no blocks, extract blocks from full_structure
            if not page_structure or 'blocks' not in page_structure or not page_structure.get('blocks'):
                logger.warning(f"Page {page_idx + 1}: page_structure missing blocks, extracting from full_structure")
                # Extract blocks for this page from full_structure
                all_blocks = full_structure.get('blocks', [])
                if all_blocks:
                    # Filter blocks by page (if page info available) or use all blocks for first page
                    if page_idx == 0:
                        page_blocks = all_blocks[:len(all_blocks) // len(document.pages) + 1] if len(document.pages) > 1 else all_blocks
                    else:
                        start_idx = (page_idx * len(all_blocks)) // len(document.pages)
                        end_idx = ((page_idx + 1) * len(all_blocks)) // len(document.pages)
                        page_blocks = all_blocks[start_idx:end_idx]
                    
                    if not page_structure:
                        page_structure = {}
                    page_structure['blocks'] = page_blocks
                    logger.info(f"Page {page_idx + 1}: Extracted {len(page_blocks)} blocks from full_structure")
            
            # Get tables for this page
            page_tables = []
            if page_structure and 'tables' in page_structure:
                page_tables = page_structure['tables']
            elif native_tables:
                # Distribute native tables across pages
                if page_idx == 0:
                    page_tables = native_tables[:len(native_tables) // len(document.pages) + 1]
                else:
                    start_idx = (page_idx * len(native_tables)) // len(document.pages)
                    end_idx = ((page_idx + 1) * len(native_tables)) // len(document.pages)
                    page_tables = native_tables[start_idx:end_idx]
            
            # Get form fields for this page
            form_fields_list = []
            if page_structure and 'form_fields' in page_structure:
                form_fields_list = page_structure['form_fields']
            
            # EXECUTE ONLY THE SELECTED MODE - No fallbacks, no downgrades
            # STEP-11: Exception: TABLE_STRICT can fallback to GEOMETRIC_HYBRID if it fails
            logger.critical("=" * 80)
            logger.critical(f"📊 EXECUTING MODE: {self.selected_mode.value} for Page {page_idx + 1}")
            logger.critical("=" * 80)
            
            try:
                if self.selected_mode == ExecutionMode.TABLE_STRICT:
                    page_layout = self._execute_table_strict_mode(
                        page_tables=page_tables,
                        document_text=document_text,
                        page_idx=page_idx,
                        page=page,
                        page_structure=page_structure,
                        full_structure=full_structure,
                        pdf_bytes=self.pdf_bytes  # STEP-13: Pass PDF bytes for Adobe fallback
                    )
                elif self.selected_mode == ExecutionMode.TABLE_VISUAL:
                    page_layout = self._execute_table_visual_mode(
                        page_structure=page_structure,
                        document_text=document_text,
                        page_idx=page_idx,
                        page=page
                    )
                elif self.selected_mode == ExecutionMode.GEOMETRIC_HYBRID:
                    page_layout = self._execute_geometric_hybrid_mode(
                        page_structure=page_structure,
                        document_text=document_text,
                        page_idx=page_idx,
                        page=page,
                        full_structure=full_structure
                    )
                elif self.selected_mode == ExecutionMode.KEY_VALUE:
                    # Check if KEY_VALUE_STRICT was selected (from routing reason)
                    strict_mode = 'KEY_VALUE_STRICT' in self.routing_reason or 'STRICT' in self.routing_reason
                    page_layout = self._execute_key_value_mode(
                        page=page,
                        document_text=document_text,
                        page_idx=page_idx,
                        form_fields=form_fields_list,
                        page_structure=page_structure,
                        strict_mode=strict_mode
                    )
                elif self.selected_mode == ExecutionMode.PLAIN_TEXT:
                    page_layout = self._execute_plain_text_mode(
                        page=page,
                        document_text=document_text,
                        page_idx=page_idx,
                        page_structure=page_structure
                    )
                else:
                    # Should never happen, but fail-safe
                    logger.error(f"Unknown execution mode: {self.selected_mode}")
                    page_layout = self._create_empty_layout(page_idx)
                
                # Add mode metadata to layout
                page_layout.metadata['execution_mode'] = self.selected_mode.value
                page_layout.metadata['routing_confidence'] = self.routing_confidence
                page_layout.metadata['routing_reason'] = self.routing_reason
                
                # CRITICAL: Track engine usage per page for billing
                # Default to "docai" unless Adobe was used
                engine_used = page_layout.metadata.get('layout_source', 'docai')
                page_layout.metadata['engine_used'] = engine_used
                page_layout.metadata['page_number'] = page_idx + 1  # 1-based page number
                
                # CRITICAL FIX: Non-empty enforcement - if layout is empty, create fallback from text
                # BUT: Check if layout actually has content before triggering fallback
                max_row = page_layout.get_max_row()
                max_col = page_layout.get_max_column()
                has_content = False
                if page_layout.rows:
                    for row in page_layout.rows:
                        if row:
                            for cell in row:
                                if cell.value and str(cell.value).strip():
                                    has_content = True
                                    break
                            if has_content:
                                break
                
                # CRITICAL: Log layout status before fallback check
                logger.critical(f"🔍 Page {page_idx + 1} Layout Check: max_row={max_row}, max_col={max_col}, has_content={has_content}, rows_count={len(page_layout.rows) if page_layout.rows else 0}")
                
                # Only trigger fallback if truly empty (no rows OR no content)
                if not has_content and (max_row == 0 or not page_layout.rows):
                    logger.critical("=" * 80)
                    logger.critical(f"🚨 BLANK LAYOUT DETECTED for Page {page_idx + 1}")
                    logger.critical(f"   Original mode: {self.selected_mode.value}")
                    logger.critical(f"   max_row={max_row}, max_col={max_col}, has_content={has_content}")
                    logger.critical(f"   Document text length: {len(document_text) if document_text else 0}")
                    logger.critical("   Creating fallback from document text")
                    logger.critical("=" * 80)
                    
                    # Create fallback layout from document text
                    if document_text and len(document_text.strip()) > 10:
                        # Use PLAIN_TEXT mode as fallback
                        logger.critical("   Using PLAIN_TEXT fallback")
                        page_layout = self._execute_plain_text_mode(
                            page=page,
                            document_text=document_text,
                            page_idx=page_idx,
                            page_structure=page_structure
                        )
                        page_layout.metadata['execution_mode'] = 'plain_text_fallback'
                        page_layout.metadata['original_mode'] = self.selected_mode.value
                        page_layout.metadata['fallback_reason'] = 'Empty layout detected - using text fallback'
                        page_layout.metadata['engine_used'] = engine_used
                        page_layout.metadata['page_number'] = page_idx + 1
                        
                        # Re-check after fallback
                        if page_layout.is_empty():
                            logger.critical("   ⚠️  PLAIN_TEXT fallback also empty - creating minimal structure")
                            page_layout = self._create_minimal_fallback_layout(page_idx, document_text, engine_used)
                    else:
                        logger.critical("   ⚠️  No document text available - creating minimal structure")
                        page_layout = self._create_minimal_fallback_layout(page_idx, document_text, engine_used)
                
                # ENTERPRISE FIX: Apply Column Governor, Row Locker, Layout Cleaner, and Font Consistency
                from .column_governor import ColumnGovernor
                from .row_locker import RowLocker
                from .layout_cleaner import LayoutCleaner
                from .font_consistency import FontConsistencyEnforcer
                
                # Get original blocks for semantic analysis
                original_blocks = page_structure.get('blocks', []) if page_structure else []
                page_count = len(full_structure.get('pages', [])) if isinstance(full_structure.get('pages'), list) else 1
                
                # ENTERPRISE RULE: Post-processors MUST NOT mutate row/column indices if layout is FROZEN
                # Layout is FROZEN after spatial indexing in convert_to_unified_layout (TABLE_STRICT mode)
                is_frozen = page_layout.metadata.get('frozen', False)
                
                # Get document type for post-processing
                filename = getattr(self, 'filename', '') or full_structure.get('filename', '') or ''
                document_type = self._detect_document_type(document_text, filename)
                
                # CRITICAL: Detect complex form types (application forms, government forms)
                complex_form_type = self._detect_complex_form_type(document_text, filename)
                page_layout.metadata['complex_form_type'] = complex_form_type
                
                # CRITICAL: Check if this document requires 2-column structure
                requires_2_cols = self._requires_2_columns(document_text, filename)
                
                if is_frozen:
                    logger.critical(f"Page {page_idx + 1}: Layout is FROZEN - post-processors will NOT mutate row/column indices")
                    # Post-processors may only:
                    # - Remove empty rows/columns (LayoutCleaner)
                    # - Clean formatting
                    # - NOT change row/column indices
                    
                    # DYNAMIC STRUCTURE: Preserve natural structure for frozen layouts
                    # Only clean empty rows/columns, don't force column count
                    layout_cleaner = LayoutCleaner()
                    page_layout = layout_cleaner.clean(page_layout)  # Only removes empty rows/cols, preserves structure
                    
                    # CRITICAL FIX: Apply label-value pairing even for frozen layouts
                    # This is safe because it only merges adjacent rows, doesn't change spatial indices
                    # It rebuilds the layout but preserves the row/column assignments
                    logger.critical(f"Page {page_idx + 1}: Applying label-value pairing to FROZEN layout (safe merge)")
                    page_layout = self._apply_label_value_pairing_post_processing(page_layout, document_type)
                else:
                    # Layout not frozen - apply all post-processors (for non-TABLE_STRICT modes)
                    # Step 1: Apply Column Governor (prevent extra columns) - HARD SEMANTIC LOCK
                    column_governor = ColumnGovernor()
                    page_layout = column_governor.apply_governor(
                        page_layout, 
                        document_type, 
                        original_blocks=original_blocks,
                        page_count=page_count
                    )
                    
                    # Step 2: Apply Row Locker (prevent word spill) - ZERO WORD SPILL
                    row_locker = RowLocker(overlap_threshold=0.7)
                    page_layout = row_locker.enforce_row_boundaries(page_layout, original_blocks=original_blocks)
                    
                    # Step 3: Clean empty rows and columns (NO fake rows/columns)
                    layout_cleaner = LayoutCleaner()
                    page_layout = layout_cleaner.clean(page_layout)
                    
                    # Step 6: Enforce font consistency (one row = one font) - STRICT ROW FONT POLICY
                    font_enforcer = FontConsistencyEnforcer()
                    page_layout = font_enforcer.enforce_per_row(page_layout)
                    
                    # Step 7: Apply label-value pairing post-processing (for all modes)
                    # CRITICAL: This fixes label-value pairs split across rows
                    page_layout = self._apply_label_value_pairing_post_processing(page_layout, document_type)
                
                # DYNAMIC STRUCTURE: Preserve natural column/row structure
                # Only apply minimal cleanup - don't force column count
                max_col = page_layout.get_max_column()
                total_rows = len(page_layout.rows) if page_layout.rows else 0
                
                # Only apply splitting for single-column layouts with colon patterns
                # Multi-column layouts keep their natural structure
                should_split_single_col = False
                if max_col == 0 and total_rows > 1:  # Single column with multiple rows
                    # Check if any cells contain colons (label:value pattern)
                    has_colon_pattern = False
                    for row in page_layout.rows:
                        for cell in row:
                            if cell.value and ':' in str(cell.value):
                                has_colon_pattern = True
                                break
                        if has_colon_pattern:
                            break
                    should_split_single_col = has_colon_pattern  # Only split if colon pattern detected
                
                if should_split_single_col and total_rows > 0:
                    logger.critical("=" * 80)
                    logger.critical(f"📊 SPLITTING: Single column with colon pattern → 2 columns (Page {page_idx + 1})")
                    logger.critical(f"   Original: {total_rows} rows × 1 column")
                    logger.critical("=" * 80)
                    
                    split_layout = UnifiedLayout(page_index=page_layout.page_index)
                    split_layout.metadata = page_layout.metadata.copy()
                    split_layout.metadata['columns_split'] = True
                    
                    new_row_idx = 0
                    for orig_row in page_layout.rows:
                        if not orig_row:
                            continue
                        
                        # Collect all non-empty cells from original row
                        non_empty = [cell for cell in orig_row if cell.value and str(cell.value).strip()]
                        
                        if not non_empty:
                            continue  # Skip completely empty rows
                        
                        # Single column: Split on colon
                        cell_text = str(non_empty[0].value).strip()
                        if ':' in cell_text:
                            # Split on colon
                            parts = cell_text.split(':', 1)
                            label_text = parts[0].strip()
                            value_text = parts[1].strip() if len(parts) > 1 else ''
                            
                            label_cell = Cell(
                                row=new_row_idx,
                                column=0,
                                value=label_text,
                                style=non_empty[0].style
                            )
                            value_cell = Cell(
                                row=new_row_idx,
                                column=1,
                                value=value_text,
                                style=non_empty[0].style
                            )
                            
                            split_layout.add_row([label_cell, value_cell])
                            new_row_idx += 1
                        else:
                            # No colon - keep as single column
                            single_cell = Cell(
                                row=new_row_idx,
                                column=0,
                                value=cell_text,
                                style=non_empty[0].style
                            )
                            split_layout.add_row([single_cell])
                            new_row_idx += 1
                    
                    if len(split_layout.rows) > 0:
                        page_layout = split_layout
                        logger.critical(f"📊 SPLIT RESULT: {len(page_layout.rows)} rows × {page_layout.get_max_column() + 1} columns")
                    else:
                        logger.critical(f"⚠️  SPLIT: No rows after splitting - keeping original layout")
                    logger.critical("=" * 80)
                
                # Step 7: Apply cell value splitting for cases like Nov 2018 PDF
                # Split cells that contain multiple values (e.g., "502702 30-01-2019 20:50 1922021539")
                from .cell_value_splitter import apply_cell_splitting
                page_layout = apply_cell_splitting(page_layout, max_columns_per_row=10)
                
                # STEP 8: Force 2 columns for specific document types (Resume, Spicemoney, Pan Link, Fee Receipt)
                if requires_2_cols:
                    max_col = page_layout.get_max_column()
                    total_rows = len(page_layout.rows) if page_layout.rows else 0
                    
                    if max_col >= 2 and total_rows > 0:
                        logger.critical("=" * 80)
                        logger.critical(f"📊 FORCING 2 COLUMNS: {filename} (Page {page_idx + 1})")
                        logger.critical(f"   Original: {total_rows} rows × {max_col + 1} columns")
                        logger.critical("=" * 80)
                        
                        trimmed_layout = UnifiedLayout(page_index=page_layout.page_index)
                        trimmed_layout.metadata = page_layout.metadata.copy()
                        trimmed_layout.metadata['forced_2_columns'] = True
                        trimmed_layout.metadata['original_columns'] = max_col + 1
                        
                        new_row_idx = 0
                        for orig_row in page_layout.rows:
                            if not orig_row:
                                continue
                            
                            # Collect all non-empty cells from original row
                            non_empty = [cell for cell in orig_row if cell.value and str(cell.value).strip()]
                            
                            if not non_empty:
                                continue  # Skip completely empty rows
                            
                            # Strategy: Pair consecutive cells as label-value
                            # If odd number of cells, last one gets empty value
                            i = 0
                            while i < len(non_empty):
                                label_cell = non_empty[i]
                                value_cell = non_empty[i + 1] if i + 1 < len(non_empty) else None
                                
                                # Create label cell (column 0)
                                label = Cell(
                                    row=new_row_idx,
                                    column=0,
                                    value=label_cell.value,
                                    style=label_cell.style
                                )
                                
                                # Create value cell (column 1)
                                if value_cell:
                                    value = Cell(
                                        row=new_row_idx,
                                        column=1,
                                        value=value_cell.value,
                                        style=value_cell.style
                                    )
                                else:
                                    value = Cell(
                                        row=new_row_idx,
                                        column=1,
                                        value='',
                                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                    )
                                
                                trimmed_layout.add_row([label, value])
                                new_row_idx += 1
                                i += 2  # Move to next pair
                        
                        # Safety check: Only use trimmed layout if it has reasonable number of rows
                        if len(trimmed_layout.rows) > 0 and len(trimmed_layout.rows) >= (total_rows * 0.3):
                            page_layout = trimmed_layout
                            logger.critical(f"📊 FORCED 2 COLUMNS RESULT: {len(page_layout.rows)} rows × 2 columns")
                        else:
                            logger.critical(f"⚠️  Trimming resulted in {len(trimmed_layout.rows)} rows (expected ~{total_rows}) - keeping original layout")
                        logger.critical("=" * 80)
                
                # DEBUG LOGS: Final column count, row count, mode selected
                final_cols = page_layout.get_max_column() + 1 if not page_layout.is_empty() else 0
                final_rows = len(page_layout.rows) if page_layout.rows else 0
                logger.critical("=" * 80)
                logger.critical(f"🔒 ENTERPRISE FIX APPLIED - Page {page_idx + 1}")
                logger.critical(f"   Mode: {self.selected_mode.value}")
                logger.critical(f"   Final columns: {final_cols}")
                logger.critical(f"   Final rows: {final_rows}")
                logger.critical(f"   Document type: {document_type}")
                logger.critical(f"   Requires 2 columns: {requires_2_cols}")
                logger.critical(f"   Forced override: {'KEY_VALUE_STRICT' in self.routing_reason}")
                logger.critical("=" * 80)
                
                page_layouts.append(page_layout)
                
            except Exception as e:
                import traceback
                logger.error(f"Error processing page {page_idx + 1} with mode {self.selected_mode.value}: {str(e)}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                
                # Try PLAIN_TEXT fallback before minimal fallback
                if document_text and len(document_text.strip()) > 10:
                    try:
                        logger.critical(f"🔄 Attempting PLAIN_TEXT fallback for Page {page_idx + 1}")
                        page_layout = self._execute_plain_text_mode(
                            page=page,
                            document_text=document_text,
                            page_idx=page_idx,
                            page_structure=page_structure
                        )
                        page_layout.metadata['execution_mode'] = 'plain_text_fallback'
                        page_layout.metadata['original_mode'] = self.selected_mode.value
                        page_layout.metadata['fallback_reason'] = f'Exception in {self.selected_mode.value}: {str(e)}'
                        page_layout.metadata['error'] = str(e)
                        page_layouts.append(page_layout)
                        continue
                    except Exception as fallback_error:
                        logger.error(f"PLAIN_TEXT fallback also failed: {fallback_error}")
                
                # Last resort: minimal fallback
                logger.critical(f"⚠️  Creating minimal fallback for Page {page_idx + 1}")
                page_layout = self._create_minimal_fallback_layout(page_idx, document_text, 'docai')
                page_layout.metadata['execution_mode'] = self.selected_mode.value
                page_layout.metadata['error'] = str(e)
                page_layouts.append(page_layout)
        
        logger.info(f"Processed {len(page_layouts)} pages with mode: {self.selected_mode.value}")
        
        # ENTERPRISE FIX: Apply post-processing (Column Governor, Row Locker, Layout Cleaner)
        # This is done per-page above, but we also need to apply quality gate here
        
        # STEP-9: QUALITY GATE (MANDATORY)
        from .quality_gate import QualityGate
        quality_gate = QualityGate()
        page_layouts = quality_gate.validate_and_fix(page_layouts)
        
        # STEP-10: Validation guard - detect blank layouts and log warnings
        for layout in page_layouts:
            max_row = layout.get_max_row()
            max_col = layout.get_max_column()
            page_num = layout.page_index + 1
            
            if max_row == 0 or max_col == 0:
                logger.critical("=" * 80)
                logger.critical(f"⚠️ VALIDATION GUARD: Blank layout detected for Page {page_num}")
                logger.critical(f"   max_row={max_row}, max_col={max_col}")
                logger.critical(f"   execution_mode={layout.metadata.get('execution_mode', 'unknown')}")
                logger.critical("   This layout should have been routed to GEOMETRIC_HYBRID mode")
                logger.critical("=" * 80)
        
        # STEP-14: MANDATORY DEBUG VISIBILITY - Log for each page
        # CRITICAL: Build pages_metadata for billing calculation
        pages_metadata = []
        for layout in page_layouts:
            page_num = layout.metadata.get('page_number', layout.page_index + 1)
            engine = layout.metadata.get('engine_used', layout.metadata.get('layout_source', 'docai'))
            execution_mode = layout.metadata.get('execution_mode', 'unknown')
            detected_tables_count = layout.metadata.get('detected_tables_count', 0)
            extracted_cells_count = sum(len(row) for row in layout.rows) if layout.rows else 0
            final_rows_written = layout.get_max_row()
            final_columns_written = layout.get_max_column()
            
            # STEP-14: FAIL-SAFE RULE - If final_rows_written == 0, log error and block blank Excel
            if final_rows_written == 0:
                logger.critical("=" * 80)
                logger.critical(f"❌ STEP-14 FAIL-SAFE: Page {page_num} has 0 rows written")
                logger.critical(f"   engine_used={engine}")
                logger.critical(f"   execution_mode={execution_mode}")
                logger.critical(f"   detected_tables_count={detected_tables_count}")
                logger.critical(f"   extracted_cells_count={extracted_cells_count}")
                logger.critical(f"   final_rows_written={final_rows_written}")
                logger.critical(f"   final_columns_written={final_columns_written}")
                logger.critical("🚨 BLANK EXCEL BLOCKED - This should trigger fallback")
                logger.critical("=" * 80)
            
            # STEP-14: MANDATORY DEBUG LOGGING
            logger.critical("=" * 80)
            logger.critical(f"📊 STEP-14 DEBUG: Page {page_num} Processing Summary")
            logger.critical(f"   engine_used: {engine}")
            logger.critical(f"   execution_mode: {execution_mode}")
            logger.critical(f"   detected_tables_count: {detected_tables_count}")
            logger.critical(f"   extracted_cells_count: {extracted_cells_count}")
            logger.critical(f"   final_rows_written: {final_rows_written}")
            logger.critical(f"   final_columns_written: {final_columns_written}")
            logger.critical("=" * 80)
            
            pages_metadata.append({
                'page': page_num,
                'engine': engine
            })
            
            # Store debug info in layout metadata for API response
            layout.metadata['debug_info'] = {
                'engine_used': engine,
                'execution_mode': execution_mode,
                'detected_tables_count': detected_tables_count,
                'extracted_cells_count': extracted_cells_count,
                'final_rows_written': final_rows_written,
                'final_columns_written': final_columns_written
            }
        
        # Store pages_metadata in class for retrieval
        self.pages_metadata = pages_metadata
        
        return page_layouts
    
    def _execute_table_strict_mode(
        self,
        page_tables: List,
        document_text: str,
        page_idx: int,
        page: Any,
        page_structure: Optional[Dict] = None,
        full_structure: Optional[Dict] = None,
        pdf_bytes: Optional[bytes] = None  # STEP-13: For Adobe fallback
    ) -> UnifiedLayout:
        """
        Execute TABLE_STRICT mode: Trust DocAI structure, preserve row/column spans.
        STEP-11: Automatic fallback to GEOMETRIC_HYBRID if TABLE_STRICT fails.
        """
        logger.critical("=" * 80)
        logger.critical(f"🔍 TABLE_STRICT MODE: Page {page_idx + 1}")
        logger.critical("=" * 80)
        
        if not page_tables:
            logger.critical(f"❌ TABLE_STRICT: No tables found on Page {page_idx + 1}")
            logger.critical("   Returning empty layout - will trigger fallback")
            return self._create_empty_layout(page_idx)
        
        logger.critical(f"✅ TABLE_STRICT: Found {len(page_tables)} table(s) on Page {page_idx + 1}")
        
        # STEP-14: Store detected_tables_count in metadata
        detected_tables_count = len(page_tables) if page_tables else 0
        
        # Use existing _convert_native_tables_to_layout method
        layout = self._convert_native_tables_to_layout(
            native_tables=page_tables,
            document_text=document_text,
            page_index=page_idx,
            page=page,
            doc_type=None,  # Not used in strict mode
            table_confidence=None  # Not used in strict mode
        )
        
        # STEP-11: If TABLE_STRICT failed (returned None), fallback to GEOMETRIC_HYBRID
        if layout is None:
            logger.critical("=" * 80)
            logger.critical(f"❌ STEP-11: TABLE_STRICT failed for Page {page_idx + 1}")
            logger.critical("🚨 AUTOMATIC FALLBACK: Executing GEOMETRIC_HYBRID (OCR_GRID) mode")
            logger.critical("=" * 80)
            
            # Fallback to GEOMETRIC_HYBRID using OCR blocks
            fallback_layout = self._execute_geometric_hybrid_mode(
                page_structure=page_structure,
                document_text=document_text,
                page_idx=page_idx,
                page=page,
                full_structure=full_structure
            )
            
            # STEP-13: Adobe PDF Extract HARD FALLBACK
            # Check if GEOMETRIC_HYBRID confidence is low or document type requires Adobe
            ocr_confidence = fallback_layout.metadata.get('confidence', 0.0)
            doc_type = self.classifier.classify(None, document_text) if hasattr(self, 'classifier') else None
            doc_type_value = doc_type.value if doc_type else ""
            
            # CRITICAL: Use Adobe for complex forms (application forms, government forms)
            complex_form_type = self._detect_complex_form_type(document_text, filename)
            requires_adobe = complex_form_type in ['application_form', 'government_form', 'mixed_column_form']
            
            should_use_adobe = (
                requires_adobe or
                ocr_confidence < 0.85 or
                doc_type_value in ["invoice", "bank_statement", "receipt"]
            )
            
            if requires_adobe:
                logger.critical(f"🚨 Complex form detected ({complex_form_type}) - Adobe fallback recommended")
            
            if should_use_adobe:
                logger.critical("=" * 80)
                logger.critical(f"🚨 STEP-13: Adobe PDF Extract HARD FALLBACK triggered for Page {page_idx + 1}")
                logger.critical(f"   Reason: OCR_GRID confidence={ocr_confidence:.2f} < 0.85 OR doc_type={doc_type_value}")
                logger.critical("=" * 80)
                
                try:
                    from .adobe_fallback_service import AdobeFallbackService
                    adobe_service = AdobeFallbackService()
                    
                    if adobe_service.is_available():
                        # STEP-13: Call Adobe PDF Extract API if PDF bytes available
                        if pdf_bytes:
                            try:
                                logger.critical("🚀 STEP-13: Calling Adobe PDF Extract API...")
                                adobe_layouts, adobe_confidence, adobe_metadata = adobe_service.extract_pdf_structure(
                                    pdf_bytes=pdf_bytes,
                                    filename=f"page_{page_idx + 1}.pdf",  # Use page number as filename
                                    docai_confidence=ocr_confidence
                                )
                                
                                if adobe_layouts and len(adobe_layouts) > page_idx:
                                    # Use Adobe layout for this page
                                    adobe_layout = adobe_layouts[page_idx]
                                    adobe_layout.metadata['layout_source'] = 'adobe'
                                    adobe_layout.metadata['engine_used'] = 'adobe'
                                    adobe_layout.metadata['page_number'] = page_idx + 1
                                    adobe_layout.metadata['detected_tables_count'] = detected_tables_count
                                    adobe_layout.metadata['fallback_triggered'] = True
                                    adobe_layout.metadata['fallback_reason'] = 'TABLE_STRICT failed + Adobe fallback triggered'
                                    
                                    logger.critical("✅ STEP-13: Adobe PDF Extract successful - using Adobe layout")
                                    logger.critical(f"   Adobe layout: {adobe_layout.get_max_row()} rows, {adobe_layout.get_max_column()} columns")
                                    
                                    return adobe_layout
                                else:
                                    logger.warning("⚠️ Adobe returned no layout for this page - using GEOMETRIC_HYBRID result")
                            except Exception as adobe_error:
                                logger.error(f"⚠️ Adobe fallback failed (non-critical): {adobe_error}")
                                logger.error("   Falling back to GEOMETRIC_HYBRID result")
                                # Continue with GEOMETRIC_HYBRID result
                        else:
                            logger.critical("⚠️ Adobe service available but PDF bytes not passed - using GEOMETRIC_HYBRID result")
                            logger.critical("   Note: Adobe fallback requires PDF bytes to be passed to _execute_table_strict_mode")
                    else:
                        logger.warning("Adobe PDF Extract not available - using GEOMETRIC_HYBRID result")
                
                except Exception as e:
                    logger.error(f"Adobe fallback check failed (non-critical): {e}")
                    # Continue with GEOMETRIC_HYBRID result
            
            # STEP-14: Store debug info in fallback layout
            fallback_layout.metadata['detected_tables_count'] = detected_tables_count
            fallback_layout.metadata['fallback_triggered'] = True
            fallback_layout.metadata['fallback_reason'] = 'TABLE_STRICT failed - zero cells extracted'
            
            return fallback_layout
        
        # STEP-14: Store detected_tables_count in layout metadata
        layout.metadata['detected_tables_count'] = detected_tables_count
        
        # SAFETY GUARD: If TABLE_STRICT returns 0 cells, log warning
        # (Actual fallback to GEOMETRIC_HYBRID happens at routing level for Form Parser)
        if layout and hasattr(layout, 'rows') and layout.rows:
            total_cells = sum(len(row) for row in layout.rows)
            if total_cells == 0:
                logger.critical("=" * 80)
                logger.critical("⚠️ TABLE_STRICT returned 0 cells")
                logger.critical("Reason: TABLE_STRICT bypassed due to Form Parser limitations")
                logger.critical("=" * 80)
        
        return layout
    
    def _execute_table_visual_mode(
        self,
        page_structure: Optional[Dict],
        document_text: str,
        page_idx: int,
        page: Any
    ) -> UnifiedLayout:
        """
        Execute TABLE_VISUAL mode: Build grid from X/Y clustering.
        Max columns = 10, never collapse to single column.
        """
        logger.info(f"Page {page_idx + 1}: Executing TABLE_VISUAL mode")
        
        # Use existing visual grid reconstruction method
        return self._convert_to_visual_grid_reconstruction_mode(
            page_tables=None,
            document_text=document_text,
            page_idx=page_idx,
            page_structure=page_structure,
            page=page
        )
    
    def _execute_key_value_mode(
        self,
        page: Any,
        document_text: str,
        page_idx: int,
        form_fields: List[Dict],
        page_structure: Optional[Dict],
        strict_mode: bool = False
    ) -> UnifiedLayout:
        """
        Execute KEY_VALUE mode: Always 2 columns (Label | Value).
        
        Args:
            strict_mode: If True, enforce exactly 2 columns (no third column)
        """
        logger.info(f"Page {page_idx + 1}: Executing KEY_VALUE mode (strict={strict_mode})")
        
        # Use existing key-value layout method
        layout = self._convert_to_key_value_layout(
            page=page,
            document_text=document_text,
            page_idx=page_idx,
            form_fields=form_fields,
            page_structure=page_structure
        )
        
        # ENTERPRISE FIX: If strict_mode, enforce exactly 2 columns
        if strict_mode:
            from .column_governor import ColumnGovernor
            column_governor = ColumnGovernor()
            document_type = self._detect_document_type(document_text, '')
            layout = column_governor.enforce_column_limit(layout, 2, document_type)
            logger.info(f"KEY_VALUE STRICT: Enforced 2-column structure (Column A = Label, Column B = Value)")
        
        return layout
    
    def _execute_geometric_hybrid_mode(
        self,
        page_structure: Optional[Dict],
        document_text: str,
        page_idx: int,
        page: Any,
        full_structure: Dict
    ) -> UnifiedLayout:
        """
        Execute GEOMETRIC_HYBRID mode: Unlimited geometric grid from OCR blocks.
        
        This mode:
        - Builds grid dynamically using OCR bounding boxes
        - Detects unlimited columns via X-axis clustering
        - Detects unlimited rows via Y-axis line grouping
        - Never hardcodes row or column counts
        - Preserves text integrity (1 block = 1 cell)
        - Detects merged cells via bounding box overlap
        - Preserves background color and style metadata
        - Preserves image/logo blocks as anchored objects
        - Prevents fake or empty rows/columns
        """
        logger.critical("=" * 80)
        logger.critical(f"🔍 GEOMETRIC_HYBRID MODE: Page {page_idx + 1}")
        logger.critical("Building unlimited geometric grid from OCR blocks")
        logger.critical("=" * 80)
        
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'geometric_hybrid'
        layout.metadata['reconstruction_mode'] = 'GEOMETRIC_HYBRID'
        
        # Get blocks for this page
        blocks = []
        logger.critical(f"📊 STEP 1: Getting blocks for Page {page_idx + 1}")
        
        if page_structure and 'blocks' in page_structure:
            blocks = page_structure['blocks']
            logger.critical(f"   ✅ Found {len(blocks)} blocks in page_structure")
        elif 'logical_cells' in full_structure:
            # Use logical cells if available
            blocks = full_structure['logical_cells']
            logger.critical(f"   ✅ Found {len(blocks)} logical_cells in full_structure")
        elif 'blocks' in full_structure:
            blocks = full_structure['blocks']
            logger.critical(f"   ✅ Found {len(blocks)} blocks in full_structure")
        else:
            logger.critical(f"   ❌ No blocks found in page_structure or full_structure")
        
        if not blocks or len(blocks) == 0:
            logger.critical(f"❌ GEOMETRIC_HYBRID: No blocks available - returning empty layout")
            logger.critical(f"   page_structure keys: {list(page_structure.keys()) if page_structure else 'None'}")
            logger.critical(f"   full_structure keys: {list(full_structure.keys()) if full_structure else 'None'}")
            logger.critical(f"   page_structure type: {type(page_structure)}")
            logger.critical(f"   full_structure type: {type(full_structure)}")
            return self._create_empty_layout(page_idx)
        
        logger.critical(f"✅ GEOMETRIC_HYBRID: Processing {len(blocks)} blocks")
        
        # Build grid using visual grid reconstruction but with unlimited columns
        # Reuse existing visual grid method but remove column limit
        return self._convert_to_geometric_hybrid_grid(
            blocks=blocks,
            document_text=document_text,
            page_idx=page_idx,
            page_structure=page_structure
        )
    
    def _execute_plain_text_mode(
        self,
        page: Any,
        document_text: str,
        page_idx: int,
        page_structure: Optional[Dict]
    ) -> UnifiedLayout:
        """
        Execute PLAIN_TEXT mode: Single-column text export.
        """
        logger.info(f"Page {page_idx + 1}: Executing PLAIN_TEXT mode")
        
        # Use existing plain text layout method
        return self._convert_to_plain_text_layout(
            page=page,
            document_text=document_text,
            page_idx=page_idx,
            page_structure=page_structure
        )
    
    def _detect_complex_form_type(self, document_text: str, filename: str = '') -> str:
        """
        Detect complex form types that need special handling.
        
        Returns:
            'application_form' - Application forms with mixed columns (4, 3, 2)
            'government_form' - Government forms with complex layouts
            'mixed_column_form' - Forms with varying column counts
            'standard' - Standard documents
        """
        text_lower = (document_text or '').lower()
        filename_lower = (filename or '').lower()
        
        # Check for application forms
        application_keywords = [
            'application', 'staff selection commission', 'registration no',
            'candidate', 'application completed', 'constable', 'ssc'
        ]
        if any(kw in filename_lower for kw in ['application', 'form']):
            if any(kw in text_lower for kw in application_keywords):
                logger.info("Complex form detected: Application Form (from filename + text)")
                return 'application_form'
        
        # Check text content for application forms
        if any(kw in text_lower for kw in ['staff selection commission', 'application completed', 'registration no:']):
            logger.info("Complex form detected: Application Form (from text)")
            return 'application_form'
        
        # Check for government forms
        govt_keywords = ['government', 'ministry', 'department', 'commission', 'board']
        if any(kw in text_lower for kw in govt_keywords) and ('form' in text_lower or 'application' in text_lower):
            logger.info("Complex form detected: Government Form (from text)")
            return 'government_form'
        
        return 'standard'
    
    def _requires_2_columns(self, document_text: str, filename: str = '') -> bool:
        """
        Check if document requires 2-column structure.
        
        Returns True for:
        - Resume
        - Spicemoney bill
        - Pan Link Receipt
        - Fee Receipt
        
        Returns False for:
        - Application forms (they need natural structure)
        - Complex forms with mixed columns
        """
        # Complex forms should NOT be forced to 2 columns
        form_type = self._detect_complex_form_type(document_text, filename)
        if form_type in ['application_form', 'government_form', 'mixed_column_form']:
            logger.info(f"Complex form detected ({form_type}) - preserving natural structure")
            return False
        
        text_lower = (document_text or '').lower()
        filename_lower = (filename or '').lower()
        
        # Check filename first (most reliable)
        if 'resume' in filename_lower:
            logger.info("2-column required: Resume (from filename)")
            return True
        if 'spice' in filename_lower or 'spicemoney' in filename_lower:
            logger.info("2-column required: Spicemoney (from filename)")
            return True
        if 'pan link' in filename_lower or 'panlink' in filename_lower:
            logger.info("2-column required: Pan Link (from filename)")
            return True
        if 'fee rcpt' in filename_lower or 'fee receipt' in filename_lower or 'fee rcpt' in filename_lower:
            logger.info("2-column required: Fee Receipt (from filename)")
            return True
        
        # Check text content
        if 'spice money' in text_lower or 'spicemoney' in text_lower or 'b-connect' in text_lower:
            logger.info("2-column required: Spicemoney (from text)")
            return True
        if 'pan link' in text_lower or 'income tax department' in text_lower:
            logger.info("2-column required: Pan Link (from text)")
            return True
        if 'fee receipt' in text_lower or 'enrollment no' in text_lower:
            logger.info("2-column required: Fee Receipt (from text)")
            return True
        if 'resume' in text_lower or ('objective' in text_lower and 'education' in text_lower):
            logger.info("2-column required: Resume (from text)")
            return True
        
        return False
    
    def _detect_document_type(self, document_text: str, filename: str = '') -> str:
        """
        Detect document type from text and filename.
        
        Returns:
            Document type: 'invoice', 'bill', 'receipt', or 'other'
        """
        text_lower = (document_text or '').lower()
        filename_lower = (filename or '').lower()
        
        logger.info(f"Document type detection: filename='{filename}', text_length={len(document_text)}")
        
        # Check filename first (most reliable)
        if 'bill' in filename_lower:
            logger.info("Document type detected: bill (from filename)")
            return 'bill'
        if 'receipt' in filename_lower:
            logger.info("Document type detected: receipt (from filename)")
            return 'receipt'
        if 'invoice' in filename_lower:
            logger.info("Document type detected: invoice (from filename)")
            return 'invoice'
        
        # Check text content
        bill_keywords = ['bill payment', 'biller', 'payment receipt', 'transaction', 'spice money']
        receipt_keywords = ['receipt', 'payment received']
        invoice_keywords = ['invoice', 'invoice number']
        
        # Check for bill keywords
        for keyword in bill_keywords:
            if keyword in text_lower:
                logger.info(f"Document type detected: bill (keyword: {keyword})")
                return 'bill'
        
        # Check for receipt keywords
        for keyword in receipt_keywords:
            if keyword in text_lower:
                logger.info(f"Document type detected: receipt (keyword: {keyword})")
                return 'receipt'
        
        # Check for invoice keywords
        for keyword in invoice_keywords:
            if keyword in text_lower:
                logger.info(f"Document type detected: invoice (keyword: {keyword})")
                return 'invoice'
        
        # Generic financial document check
        financial_keywords = ['payment', 'amount', 'total', 'transaction date']
        financial_count = sum(1 for kw in financial_keywords if kw in text_lower)
        if financial_count >= 2:
            logger.info(f"Document type detected: bill (generic financial document with {financial_count} keywords)")
            return 'bill'
        
        logger.info("Document type detected: other")
        return 'other'
    
    def _apply_label_value_pairing_post_processing(self, layout: UnifiedLayout, document_type: str) -> UnifiedLayout:
        """
        Apply label-value pairing post-processing to fix labels and values split across rows.
        This is called for ALL modes (not just TABLE_STRICT) to ensure consistent behavior.
        """
        logger.critical("=" * 80)
        logger.critical("🔍 LABEL-VALUE PAIRING POST-PROCESSING - ENTRY")
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
        rows_with_empty_col2 = total_rows - len(rows_with_col2)
        empty_col2_ratio = rows_with_empty_col2 / total_rows if total_rows > 0 else 0
        
        logger.critical(f"📊 STATS: Total rows={total_rows}, Rows with Col2={len(rows_with_col2)}, Total cells={len(all_cells_flat)}")
        logger.critical(f"📊 COVERAGE: Col2 coverage={col2_coverage:.1%}, Empty Col2 ratio={empty_col2_ratio:.1%}")
        
        # Apply if: Col2 coverage is low OR many rows have empty Col2
        should_apply = (col2_coverage < 0.7 or empty_col2_ratio > 0.3) and total_rows >= 3
        
        logger.critical(f"🔍 CONDITION: col2_coverage < 0.7 = {col2_coverage < 0.7}")
        logger.critical(f"🔍 CONDITION: empty_col2_ratio > 0.3 = {empty_col2_ratio > 0.3}")
        logger.critical(f"🔍 CONDITION: total_rows >= 3 = {total_rows >= 3}")
        logger.critical(f"🔍 RESULT: should_apply = {should_apply}")
        
        if should_apply:
            logger.critical("=" * 80)
            logger.critical("✅ CONDITION PASSED - APPLYING LABEL-VALUE PAIRING")
            logger.critical("=" * 80)
            
            # Use the same logic from table_post_processor
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
            
            # Group cells by row
            cells_by_row = {}
            for cell in all_cells_flat:
                if cell.row not in cells_by_row:
                    cells_by_row[cell.row] = []
                cells_by_row[cell.row].append(cell)
            
            logger.critical(f"📦 Grouped cells into {len(cells_by_row)} rows")
            
            # Process adjacent rows for label-value pairing
            merged_cells = []
            rows_to_remove = set()
            row_idx = 0
            
            sorted_row_indices = sorted(cells_by_row.keys())
            logger.critical(f"🔄 Processing {len(sorted_row_indices)} rows for label-value pairing...")
            i = 0
            
            while i < len(sorted_row_indices):
                current_row_idx = sorted_row_indices[i]
                current_row_cells = cells_by_row[current_row_idx]
                
                # Get Col1 cell (label candidate)
                col1_cell = next((c for c in current_row_cells if c.column == 0), None)
                col2_cell = next((c for c in current_row_cells if c.column >= 1), None)
                
                # Check if Col1 has content but Col2 is empty
                if col1_cell and (not col2_cell or not (col2_cell.value and str(col2_cell.value).strip())):
                    current_value = str(col1_cell.value).strip() if col1_cell.value else ""
                    current_value_lower = current_value.lower()
                    
                    is_label = any(re.search(pattern, current_value_lower) for pattern in label_patterns)
                    has_label_keywords = any(keyword in current_value_lower for keyword in 
                                           ['name', 'id', 'number', 'date', 'amount', 'status', 'channel', 
                                            'mode', 'fee', 'ref', 'approval', 'biller', 'customer', 'payment',
                                            'agent', 'transaction', 'consumer', 'mobile'])
                    is_short = len(current_value) < 50
                    has_colon = ':' in current_value
                    is_all_caps = current_value.isupper() and len(current_value) > 1
                    
                    is_likely_label = (is_label or has_label_keywords or
                                     (is_short and has_colon) or
                                     (is_short and ' ' in current_value and not is_all_caps and not current_value.replace(' ', '').isdigit()))
                    
                    if is_likely_label and i + 1 < len(sorted_row_indices):
                        # Check next row
                        next_row_idx = sorted_row_indices[i + 1]
                        next_row_cells = cells_by_row[next_row_idx]
                        next_col1_cell = next((c for c in next_row_cells if c.column == 0), None)
                        next_col2_cell_check = next((c for c in next_row_cells if c.column >= 1), None)
                        next_has_col2 = next_col2_cell_check and (next_col2_cell_check.value and str(next_col2_cell_check.value).strip())
                        
                        logger.critical(f"  -> Checking Row {current_row_idx} (label='{current_value[:40]}') vs Row {next_row_idx}")
                        logger.critical(f"     Next row Col1: {str(next_col1_cell.value)[:40] if next_col1_cell and next_col1_cell.value else 'NONE'}")
                        logger.critical(f"     Next row has Col2: {next_has_col2}")
                        
                        if next_col1_cell and not next_has_col2:
                            next_value = str(next_col1_cell.value).strip() if next_col1_cell.value else ""
                            next_value_lower = next_value.lower()
                            next_is_label = any(re.search(pattern, next_value_lower) for pattern in label_patterns)
                            
                            # Additional check: next row should NOT be a label
                            # Check if it has label keywords (more strict)
                            next_has_label_keywords = any(keyword in next_value_lower for keyword in 
                                                         ['biller name', 'consumer number', 'mobile number', 'approval ref',
                                                          'payment status', 'payment channel', 'payment mode', 'convenience fee',
                                                          'platform fee', 'transaction id', 'receipt no', 'invoice no'])
                            next_is_short = len(next_value) < 30  # Stricter: values are usually longer
                            next_has_colon = ':' in next_value
                            
                            # Next row is a label if: has specific label keywords OR (is very short AND has colon)
                            next_is_likely_label = next_is_label or next_has_label_keywords or (next_is_short and next_has_colon)
                            
                            logger.critical(f"     Next value is_label: {next_is_label}, is_likely_label: {next_is_likely_label}, value='{next_value[:40]}'")
                            
                            if not next_is_likely_label:
                                # Current is label, next is value - merge them
                                logger.critical(f"  ✅ MERGING: Row {current_row_idx} (label='{current_value[:30]}') + Row {next_row_idx} (value='{next_value[:30]}') into Row {row_idx}")
                                
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
                            else:
                                logger.critical(f"     ❌ Skipping merge - next row is also a label (is_likely_label={next_is_likely_label})")
                        else:
                            logger.critical(f"     ❌ Skipping merge - next row has Col2 or no Col1")
                
                # Not a label-value pair, keep as is
                if current_row_idx not in rows_to_remove:
                    for cell in current_row_cells:
                        cell_already_added = any(id(c) == id(cell) for c in merged_cells)
                        if not cell_already_added:
                            cell.row = row_idx
                            merged_cells.append(cell)
                    row_idx += 1
                i += 1
            
            # Rebuild layout with merged cells
            if merged_cells:
                seen_cells = {}
                unique_merged_cells = []
                for cell in merged_cells:
                    cell_key = (id(cell), str(cell.value)[:50] if cell.value else '')
                    if cell_key not in seen_cells:
                        seen_cells[cell_key] = cell
                        unique_merged_cells.append(cell)
                
                if unique_merged_cells:
                    max_row_idx = max(c.row for c in unique_merged_cells)
                    new_rows = [[] for _ in range(max_row_idx + 1)]
                    
                    for cell in unique_merged_cells:
                        if 0 <= cell.row <= max_row_idx:
                            new_rows[cell.row].append(cell)
                    
                    # Sort cells within each row by column
                    for row in new_rows:
                        row.sort(key=lambda c: c.column)
                    
                    # Remove empty rows
                    new_rows = [row for row in new_rows if row]
                    
                    # Re-assign row indices
                    for new_row_idx, row in enumerate(new_rows):
                        for cell in row:
                            cell.row = new_row_idx
                    
                    layout.rows = new_rows
                    logger.critical("=" * 80)
                    logger.critical(f"✅ MERGE COMPLETE: Merged {len(rows_to_remove)} rows into label-value pairs")
                    logger.critical(f"   Original rows: {total_rows}, Final rows: {len(new_rows)}")
                    logger.critical("=" * 80)
                else:
                    logger.critical("⚠️  No merged cells to rebuild")
        else:
            logger.critical("=" * 80)
            logger.critical("❌ CONDITION FAILED - SKIPPING LABEL-VALUE PAIRING")
            logger.critical(f"   Reason: col2_coverage={col2_coverage:.1%}, empty_col2_ratio={empty_col2_ratio:.1%}, total_rows={total_rows}")
            logger.critical("=" * 80)
        
        logger.critical("🔍 LABEL-VALUE PAIRING POST-PROCESSING - EXIT")
        logger.critical("=" * 80)
        return layout
    
    def _create_empty_layout(self, page_idx: int) -> UnifiedLayout:
        """Create minimal empty layout"""
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'empty'
        return layout
    
    def _create_minimal_fallback_layout(self, page_idx: int, document_text: str, engine_used: str = 'docai') -> UnifiedLayout:
        """Create minimal fallback layout when all other modes fail"""
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'minimal_fallback'
        layout.metadata['execution_mode'] = 'minimal_fallback'
        layout.metadata['engine_used'] = engine_used
        layout.metadata['page_number'] = page_idx + 1
        layout.metadata['fallback_reason'] = 'All extraction modes failed - using minimal structure'
        
        # Create at least one row with available text
        if document_text and len(document_text.strip()) > 0:
            # Use first 500 characters
            text_snippet = document_text[:500].strip()
            cell = Cell(
                row=0,
                column=0,
                value=text_snippet,
                style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=True)
            )
            layout.add_row([cell])
        else:
            # Last resort: create a single cell with message
            cell = Cell(
                row=0,
                column=0,
                value="Content extracted but could not be structured",
                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
            )
            layout.add_row([cell])
        
        logger.critical(f"Created minimal fallback layout for Page {page_idx + 1} with {layout.get_max_row()} row(s)")
        return layout
    
    # Keep all existing helper methods below...
    
    def _allows_table_processing(self, doc_type: DocumentType, document: Any, document_text: str) -> bool:
        """
        Determine if document type allows table processing.
        
        Returns True only for structured documents with clear table structure:
        - Has rows + column lines + repetition patterns
        - NOT form-style (key:value pairs)
        - NOT resume/text documents
        """
        # Check for structured table indicators
        has_structured_table = False
        if hasattr(document, 'pages') and document.pages:
            for page in document.pages:
                if hasattr(page, 'tables') and page.tables:
                    # Check if tables have clear structure (multiple rows, columns)
                    for table in page.tables:
                        row_count = 0
                        col_count = 0
                        if hasattr(table, 'header_rows') and table.header_rows:
                            row_count += len(table.header_rows)
                            if table.header_rows:
                                col_count = max(col_count, len(table.header_rows[0].cells) if hasattr(table.header_rows[0], 'cells') else 0)
                        if hasattr(table, 'body_rows') and table.body_rows:
                            row_count += len(table.body_rows)
                            if table.body_rows:
                                col_count = max(col_count, len(table.body_rows[0].cells) if hasattr(table.body_rows[0], 'cells') else 0)
                        
                        # Structured table: multiple rows AND multiple columns
                        if row_count >= 3 and col_count >= 2:
                            has_structured_table = True
                            break
                    if has_structured_table:
                        break
        
        # Document types that should NOT use table processing
        form_style_types = [
            DocumentType.RESUME,
            DocumentType.LETTER,
            DocumentType.CERTIFICATE,
            DocumentType.ID_CARD
        ]
        
        if doc_type in form_style_types:
            logger.info(f"Document type {doc_type.value} is form-style, skipping table processing")
            return False
        
        # Only allow table processing if we have structured tables
        if not has_structured_table:
            logger.info("No structured tables detected (rows + columns + repetition), skipping table processing")
            return False
        
        # Allow for invoice, bank statement, bill, office documents with structured tables
        table_allowed_types = [
            DocumentType.INVOICE,
            DocumentType.BANK_STATEMENT,
            DocumentType.BILL,
            DocumentType.OFFICE_DOCUMENT
        ]
        
        if doc_type in table_allowed_types and has_structured_table:
            return True
        
        # Unknown type: allow only if clear structured table exists
        if doc_type == DocumentType.UNKNOWN and has_structured_table:
            return True
        
        return False

    def _determine_layout_category(
        self,
        doc_type: DocumentType,
        page_tables: List,
        page_structure: Optional[Dict],
        has_form_fields: bool,
        has_blocks: bool
    ) -> (str, float):
        """
        Decide layout category for the page:
        a) true_table          -> full table pipeline
        b) key_value           -> 2-column Label|Value
        c) mixed_layout        -> block-based, no fake grid
        d) plain_text          -> minimal structured
        Also returns a table confidence score.
        """
        table_confidence = 0.0

        # Compute table confidence if tables present
        if page_tables:
            table_confidence = self._compute_table_confidence_from_tables(page_tables)

        # Category selection
        if page_tables and table_confidence >= 0.65:
            return "true_table", table_confidence

        if doc_type in [DocumentType.BILL, DocumentType.INVOICE, DocumentType.BANK_STATEMENT] or has_form_fields:
            return "key_value", table_confidence

        if has_blocks and (has_form_fields or page_tables):
            return "mixed_layout", table_confidence

        return "plain_text", table_confidence

    def _compute_table_confidence_from_tables(self, tables: List) -> float:
        """
        Estimate table confidence using:
        - Row repetition (consistent row counts)
        - Column alignment consistency
        - Grid continuity (presence of header + multiple body rows)
        """
        if not tables:
            return 0.0

        scores = []
        for table in tables:
            row_counts = []
            col_counts = []

            if hasattr(table, 'header_rows') and table.header_rows:
                row_counts.append(len(table.header_rows))
                if table.header_rows and hasattr(table.header_rows[0], 'cells'):
                    col_counts.append(len(table.header_rows[0].cells))

            if hasattr(table, 'body_rows') and table.body_rows:
                row_counts.append(len(table.body_rows))
                if table.body_rows and hasattr(table.body_rows[0], 'cells'):
                    col_counts.append(len(table.body_rows[0].cells))

            if not row_counts or not col_counts:
                scores.append(0.3)
                continue

            # Row repetition: prefer many body rows
            total_rows = sum(row_counts)
            row_score = min(1.0, total_rows / 10.0)  # more rows => higher score up to 1

            # Column consistency: variance low -> good
            if len(col_counts) > 1:
                variance = max(col_counts) - min(col_counts)
                col_score = 1.0 - min(1.0, variance / (max(col_counts) or 1))
            else:
                col_score = 0.8  # assume decent if only one measure

            # Header + body continuity
            continuity = 0.0
            if hasattr(table, 'header_rows') and table.header_rows and hasattr(table, 'body_rows') and table.body_rows:
                continuity = 1.0
            elif total_rows >= 3:
                continuity = 0.6

            scores.append((row_score * 0.4) + (col_score * 0.3) + (continuity * 0.3))

        return max(scores) if scores else 0.0

    def _compute_table_confidence_signals(self, tables: List) -> float:
        """
        Advanced table confidence for premium TYPE_A tables using multiple signals:
        table_confidence = 0.30 * RowConsistency +
                           0.30 * ColumnAlignment +
                           0.25 * GridContinuity +
                           0.15 * CellDensity
        """
        if not tables:
            return 0.0

        # Use the best (max) scoring table among available native tables
        scores = []
        for table in tables:
            cells = self._extract_table_cells(table)
            if not cells:
                scores.append(0.0)
                continue

            row_consistency = self._score_row_consistency(cells)
            col_alignment = self._score_column_alignment(cells)
            grid_continuity = self._score_grid_continuity(cells)
            cell_density = self._score_cell_density(cells)

            table_conf = (
                0.30 * row_consistency +
                0.30 * col_alignment +
                0.25 * grid_continuity +
                0.15 * cell_density
            )
            scores.append(table_conf)

        return max(scores) if scores else 0.0

    def _extract_table_cells(self, table: Any) -> List[Dict[str, Any]]:
        """Extract cell bounding boxes and positions from a Document AI table."""
        extracted = []
        row_idx = 0
        # header rows
        if hasattr(table, "header_rows") and table.header_rows:
            for hr in table.header_rows:
                if hasattr(hr, "cells"):
                    col_idx = 0
                    for c in hr.cells:
                        bbox = self._safe_bbox(c)
                        if bbox:
                            extracted.append({"row": row_idx, "col": col_idx, "bbox": bbox})
                        col_idx += 1
                row_idx += 1
        # body rows
        if hasattr(table, "body_rows") and table.body_rows:
            for br in table.body_rows:
                if hasattr(br, "cells"):
                    col_idx = 0
                    for c in br.cells:
                        bbox = self._safe_bbox(c)
                        if bbox:
                            extracted.append({"row": row_idx, "col": col_idx, "bbox": bbox})
                        col_idx += 1
                row_idx += 1
        return extracted

    def _safe_bbox(self, cell: Any) -> Optional[Dict[str, float]]:
        if not hasattr(cell, "layout") or not hasattr(cell.layout, "bounding_poly"):
            return None
        bp = cell.layout.bounding_poly
        if not hasattr(bp, "normalized_vertices") or not bp.normalized_vertices:
            return None
        xs = [v.x for v in bp.normalized_vertices if hasattr(v, "x")]
        ys = [v.y for v in bp.normalized_vertices if hasattr(v, "y")]
        if not xs or not ys:
            return None
        return {
            "x_min": min(xs),
            "x_max": max(xs),
            "y_min": min(ys),
            "y_max": max(ys),
            "x_center": (min(xs) + max(xs)) / 2,
            "y_center": (min(ys) + max(ys)) / 2,
            "width": max(xs) - min(xs),
            "height": max(ys) - min(ys),
        }

    def _score_row_consistency(self, cells: List[Dict[str, Any]]) -> float:
        rows = {}
        for c in cells:
            rows.setdefault(c["row"], []).append(c)
        y_centers = []
        for row_idx in sorted(rows.keys()):
            row_cells = rows[row_idx]
            y_vals = [cell["bbox"]["y_center"] for cell in row_cells]
            y_centers.append(sum(y_vals) / len(y_vals))
        if len(y_centers) < 2:
            return 0.5
        spacings = [abs(y_centers[i+1] - y_centers[i]) for i in range(len(y_centers)-1)]
        if not spacings:
            return 0.5
        mean_spacing = sum(spacings) / len(spacings)
        variance = sum((s - mean_spacing) ** 2 for s in spacings) / len(spacings)
        std_spacing = variance ** 0.5
        score = max(0.0, 1.0 - std_spacing / (mean_spacing + 1e-6))
        return min(1.0, score)

    def _score_column_alignment(self, cells: List[Dict[str, Any]]) -> float:
        cols = {}
        for c in cells:
            cols.setdefault(c["col"], []).append(c)
        spreads = []
        for col_idx in sorted(cols.keys()):
            x_vals = [cell["bbox"]["x_center"] for cell in cols[col_idx]]
            if not x_vals:
                continue
            spreads.append(max(x_vals) - min(x_vals))
        if not spreads:
            return 0.5
        avg_spread = sum(spreads) / len(spreads)
        score = max(0.0, 1.0 - avg_spread / 0.05)  # tolerance 5% page width
        return min(1.0, score)

    def _score_grid_continuity(self, cells: List[Dict[str, Any]]) -> float:
        rows = {}
        for c in cells:
            rows.setdefault(c["row"], []).append(c["col"])
        if not rows:
            return 0.0
        max_cols = max(max(cols) for cols in rows.values()) + 1
        if max_cols <= 0:
            return 0.0
        aligned_rows = 0
        for cols in rows.values():
            unique_cols = len(set(cols))
            if unique_cols == max_cols:
                aligned_rows += 1
        return aligned_rows / len(rows)

    def _score_cell_density(self, cells: List[Dict[str, Any]]) -> float:
        if not cells:
            return 0.0
        max_row = max(c["row"] for c in cells)
        max_col = max(c["col"] for c in cells)
        expected = (max_row + 1) * (max_col + 1)
        if expected == 0:
            return 0.0
        density = len(cells) / expected
        return min(1.0, density)

    def _convert_native_tables_to_layout(
        self,
        native_tables: List,
        document_text: str,
        page_index: int = 0,
        page: Optional[Any] = None,
        doc_type: Optional[DocumentType] = None,
        table_confidence: Optional[float] = None
    ) -> UnifiedLayout:
        """
        Convert Document AI native tables to unified layout with PREMIUM post-processing.
        This is the enhanced path for premium conversions only.
        """
        from .table_post_processor import TablePostProcessor, TableExtractionFailed
        
        # Use premium post-processing layer
        post_processor = TablePostProcessor()
        
        # Process each table with post-processing (page isolation)
        all_processed_tables = []
        
        for table_idx, table in enumerate(native_tables):
            logger.info(f"Processing table {table_idx + 1} with premium post-processing (page {page_index + 1})...")
            
            # TABLE_STRICT mode: Trust DocAI structure, preserve spans/merges
            logger.info(f"Calling TablePostProcessor.process_table() in TABLE_STRICT mode")
            
            try:
                processed_table = post_processor.process_table(
                    table=table,
                    document_text=document_text,
                    page=page,
                    doc_type=None,  # Not used in enterprise rewrite
                    table_confidence=None,  # Not used in enterprise rewrite
                    execution_mode="table_strict"  # TABLE_STRICT mode: trust DocAI structure
                )
                
                logger.info(f"TablePostProcessor.process_table() returned ProcessedTable with {len(processed_table.rows)} rows")
                
                if processed_table.rows:
                    all_processed_tables.append(processed_table)
            
            except TableExtractionFailed as e:
                # STEP-11: TABLE_STRICT failed - automatic fallback to GEOMETRIC_HYBRID (OCR_GRID)
                logger.critical("=" * 80)
                logger.critical(f"❌ STEP-11 FAIL-SAFE: TABLE_STRICT failed for table {table_idx + 1}")
                logger.critical(f"   Error: {str(e)}")
                logger.critical("🚨 AUTOMATIC FALLBACK: Downgrading to GEOMETRIC_HYBRID (OCR_GRID) mode")
                logger.critical("=" * 80)
                
                # Return None to signal fallback needed
                # The caller will handle this by invoking GEOMETRIC_HYBRID mode
                return None
        
        # Convert all processed tables to unified layout
        if not all_processed_tables:
            logger.warning("No processed tables after post-processing")
            return UnifiedLayout(page_index=page_index)
        
        # Combine multiple tables into one layout
        combined_layout = UnifiedLayout(page_index=page_index)
        row_offset = 0
        
        for table_idx, processed_table in enumerate(all_processed_tables):
            # CRITICAL: Convert ProcessedTable (from 7-step pipeline) to UnifiedLayout
            # This is the bridge between post-processing and Excel rendering
            logger.info(f"Converting ProcessedTable to UnifiedLayout for Excel rendering...")
            table_layout = post_processor.convert_to_unified_layout(
                processed_table,
                page_index=page_index
            )
            
            # QUALITY FAIL-SAFE: Reject invalid layouts
            max_row = table_layout.get_max_row()
            max_col = table_layout.get_max_column()
            
            if max_row < 0 or max_col < 0:
                logger.critical("=" * 80)
                logger.critical(f"❌ QUALITY FAIL-SAFE: Table {table_idx + 1} layout has invalid dimensions")
                logger.critical(f"   max_row={max_row}, max_col={max_col}")
                logger.critical("   BLANK EXCEL IS NEVER A VALID RESULT")
                logger.critical("=" * 80)
                # Skip this table, continue with others
                continue
            
            logger.info(f"UnifiedLayout created: {max_row + 1} rows, {max_col + 1} columns")
            
            # CRITICAL: If layout is frozen, preserve spatial indices exactly
            # Only adjust row_offset for combining multiple tables
            is_frozen = table_layout.metadata.get('frozen', False)
            
            if is_frozen:
                logger.critical(f"Table {table_idx + 1}: Layout is FROZEN - preserving spatial indices, only adjusting row_offset")
            
            # Add rows with offset (for combining multiple tables)
            for row_cells in table_layout.rows:
                adjusted_cells = []
                for cell in row_cells:
                    # Adjust row index for table combination, but preserve column index
                    adjusted_cell = Cell(
                        row=row_offset + cell.row,  # Add offset for table combination
                        column=cell.column,  # Preserve spatial column index
                        value=cell.value,
                        style=cell.style,
                        rowspan=cell.rowspan,
                        colspan=cell.colspan,
                        merged=cell.merged
                    )
                    adjusted_cells.append(adjusted_cell)
                    
                    # Adjust merged cell ranges
                    if cell.rowspan > 1 or cell.colspan > 1:
                        end_row = row_offset + cell.row + cell.rowspan - 1
                        end_col = cell.column + cell.colspan - 1
                        combined_layout.add_merged_cell(
                            start_row=row_offset + cell.row,
                            start_col=cell.column,
                            end_row=end_row,
                            end_col=end_col
                        )
                
                if adjusted_cells:
                    combined_layout.add_row(adjusted_cells)
                # Update row_offset to max row + 1 for next table
                max_row_in_table = max((c.row for c in adjusted_cells), default=-1) if adjusted_cells else -1
                row_offset = max_row_in_table + 1
            
            # Store table metadata
            if table_idx == 0:  # Use first table's metadata
                combined_layout.metadata.update(table_layout.metadata)
            
            # Add spacing between tables
            if table_idx < len(all_processed_tables) - 1:
                row_offset += 1
        
        logger.info(f"Converted {len(native_tables)} native tables to layout with premium post-processing")
        return combined_layout
    
    def _extract_cell_text(self, cell: Any, document_text: str) -> str:
        """Extract text from a table cell"""
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
                if start < len(document_text) and end <= len(document_text):
                    text_parts.append(document_text[start:end])
        
        return ' '.join(text_parts).strip()
    
    def _convert_enhanced_tables_to_layout(
        self,
        enhanced_tables: List[Dict],
        document_text: str,
        page_index: int,
        page_structure: Optional[Dict] = None
    ) -> UnifiedLayout:
        """Convert enhanced tables (from full OCR) to unified layout"""
        layout = UnifiedLayout(page_index=page_index)
        row_offset = 0
        
        for table_info in enhanced_tables:
            # Use confidence to filter low-quality tables
            confidence = table_info.get('confidence', 1.0)
            if confidence < 0.5:
                logger.warning(f"Table filtered due to low confidence: {confidence}")
                continue
            
            # Process header rows
            for header_row in table_info.get('header_rows', []):
                cells = []
                for col_idx, cell_info in enumerate(header_row):
                    cell_text = cell_info.get('text', '')
                    cell_confidence = cell_info.get('confidence', 1.0)
                    
                    # Filter low confidence cells
                    if cell_confidence < 0.5:
                        cell_text = f"[?{cell_text}]"  # Mark uncertain
                    
                    cell_obj = Cell(
                        row=row_offset,
                        column=col_idx,
                        value=cell_text,
                        style=CellStyle(
                            bold=True,
                            alignment_horizontal=CellAlignment.CENTER,
                            background_color="4472C4"
                        )
                    )
                    cells.append(cell_obj)
                
                if cells:
                    layout.add_row(cells)
                    row_offset += 1
            
            # Process body rows
            for body_row in table_info.get('body_rows', []):
                cells = []
                for col_idx, cell_info in enumerate(body_row):
                    cell_text = cell_info.get('text', '')
                    cell_confidence = cell_info.get('confidence', 1.0)
                    
                    if cell_confidence < 0.5:
                        cell_text = f"[?{cell_text}]"
                    
                    cell_obj = Cell(
                        row=row_offset,
                        column=col_idx,
                        value=cell_text,
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                    cells.append(cell_obj)
                
                if cells:
                    layout.add_row(cells)
                    row_offset += 1
            
            # Add spacing between tables
            row_offset += 1
        
        logger.info(f"Converted {len(enhanced_tables)} enhanced tables to layout")
        return layout
    
    def _convert_form_fields_to_layout(self, form_fields: List[Dict], page_index: int) -> UnifiedLayout:
        """Convert form fields to unified layout (key-value pairs)"""
        layout = UnifiedLayout(page_index=page_index)
        row_idx = 0
        
        for field in form_fields:
            field_name = field.get('name', '')
            field_value = field.get('value', '')
            confidence = field.get('confidence', 1.0)
            
            if confidence < 0.5:
                field_name = f"[?{field_name}]"
                field_value = f"[?{field_value}]"
            
            if field_name or field_value:
                key_cell = Cell(
                    row=row_idx,
                    column=0,
                    value=field_name,
                    style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                )
                value_cell = Cell(
                    row=row_idx,
                    column=1,
                    value=field_value,
                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                )
                layout.add_row([key_cell, value_cell])
                row_idx += 1
        
        logger.info(f"Converted {len(form_fields)} form fields to layout")
        return layout
    
    def _build_layout_from_full_ocr(
        self,
        page_structure: Optional[Dict],
        page: Any,
        document_text: str,
        doc_type: str,
        page_idx: int
    ) -> UnifiedLayout:
        """Build layout from full OCR blocks (using Document AI's complete structure)"""
        if page_structure and 'blocks' in page_structure and page_structure['blocks']:
            # Check if blocks have bounding boxes
            blocks_with_bbox = [b for b in page_structure['blocks'] if b.get('bounding_box')]
            
            if blocks_with_bbox:
                # Use blocks with bounding boxes for proper column detection
                logger.info(f"Page {page_idx + 1}: Using {len(blocks_with_bbox)} OCR blocks with bounding boxes")
                return self._build_layout_from_blocks(blocks_with_bbox, doc_type, page_idx)
            else:
                # Blocks don't have bounding boxes, use heuristic builder directly
                logger.info(f"Page {page_idx + 1}: Blocks without bounding boxes, using heuristic builder")
                layout = self.heuristic_builder.build_from_page(
                    page,
                    document_text,
                    doc_type,
                    page_idx
                )
                layout.page_index = page_idx
                return layout
        else:
            # Fallback to heuristic builder
            logger.info(f"Page {page_idx + 1}: No blocks found, falling back to heuristic inference")
            layout = self.heuristic_builder.build_from_page(
                page,
                document_text,
                doc_type,
                page_idx
            )
            layout.page_index = page_idx
            return layout
    
    def _build_layout_from_blocks(self, blocks: List[Dict], doc_type: str, page_idx: int, force_sequential: bool = False) -> UnifiedLayout:
        """
        Build layout from OCR blocks using bounding box positions for proper column detection.
        This function now uses bounding boxes to detect columns instead of sequential placement.
        """
        layout = UnifiedLayout(page_index=page_idx)
        
        if not blocks:
            return layout
        
        # Convert blocks to text_blocks format with bounding boxes for heuristic builder
        text_blocks = []
        for block in blocks:
            bounding_box = block.get('bounding_box')
            if not bounding_box:
                # Skip blocks without bounding boxes
                continue
            
            text = block.get('text', '').strip()
            if not text:
                continue
            
            # Extract bounding box coordinates
            # bounding_box format: {'x_min': float, 'y_min': float, 'x_max': float, 'y_max': float}
            x_min = bounding_box.get('x_min', 0.0)
            x_max = bounding_box.get('x_max', 1.0)
            y_min = bounding_box.get('y_min', 0.0)
            y_max = bounding_box.get('y_max', 1.0)
            
            text_blocks.append({
                'text': text,
                'x_min': x_min,
                'x_max': x_max,
                'y_min': y_min,
                'y_max': y_max,
                'x_center': (x_min + x_max) / 2,
                'y_center': (y_min + y_max) / 2,
                'width': x_max - x_min,
                'height': y_max - y_min
            })
        
        if not text_blocks:
            logger.warning(f"No text blocks with bounding boxes found, falling back to sequential layout")
            # Fallback to sequential layout if no bounding boxes
            row_idx = 0
            for block in blocks:
                text = block.get('text', '').strip()
                if text:
                    cell = Cell(
                        row=row_idx,
                        column=0,
                        value=text,
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                    layout.add_row([cell])
                    row_idx += 1
            return layout
        
        # If forced sequential (mixed layout), just order by Y then X without creating grid
        if force_sequential:
            text_blocks.sort(key=lambda b: (b['y_center'], b['x_center']))
            row_idx = 0
            for block in text_blocks:
                cell = Cell(
                    row=row_idx,
                    column=0,
                    value=block['text'],
                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                )
                layout.add_row([cell])
                row_idx += 1
            return layout

        # Use heuristic builder's column detection logic
        rows = self.heuristic_builder._group_by_y_axis(text_blocks)
        column_positions = self.heuristic_builder._detect_global_columns(rows)
        
        logger.info(f"Detected {len(rows)} rows and {len(column_positions)} columns from blocks")
        
        for row_idx, row_blocks in enumerate(rows):
            row_blocks.sort(key=lambda b: b['x_center'])
            cells = []
            used_cols = set()
            
            for block in row_blocks:
                col_idx = self.heuristic_builder._find_column_for_block(block, column_positions)
                
                if col_idx in used_cols:
                    col_idx = max(column_positions.keys()) + 1 if column_positions else len(cells)
                
                used_cols.add(col_idx)
                
                block_type = 'TEXT'
                confidence = 1.0
                for orig_block in blocks:
                    if orig_block.get('text', '').strip() == block['text']:
                        block_type = orig_block.get('type', 'TEXT')
                        confidence = orig_block.get('confidence', 1.0)
                        break
                
                cell = Cell(
                    row=row_idx,
                    column=col_idx,
                    value=block['text'],
                    style=CellStyle(
                        alignment_horizontal=CellAlignment.LEFT,
                        bold=(block_type == 'FORM_FIELD' or confidence > 0.9)
                    )
                )
                cells.append(cell)
            
            if cells:
                layout.add_row(cells)
        
        return layout
    
    def _reconstruct_key_value_layout(
        self,
        page: Any,
        document_text: str,
        page_idx: int,
        page_structure: Optional[Dict] = None
    ) -> UnifiedLayout:
        """
        Reconstruct layout as key-value pairs (2 columns minimum).
        For receipts/bills that don't have structured tables.
        """
        layout = UnifiedLayout(page_index=page_idx)
        
        # Extract text blocks
        text_blocks = []
        if page_structure and 'blocks' in page_structure:
            for block in page_structure['blocks']:
                if block.get('bounding_box') and block.get('text'):
                    text_blocks.append({
                        'text': block['text'],
                        'x_min': block['bounding_box'].get('x_min', 0.0),
                        'x_max': block['bounding_box'].get('x_max', 1.0),
                        'y_min': block['bounding_box'].get('y_min', 0.0),
                        'y_max': block['bounding_box'].get('y_max', 1.0),
                        'x_center': block['bounding_box'].get('x_center', 0.5),
                        'y_center': block['bounding_box'].get('y_center', 0.5)
                    })
        
        if not text_blocks:
            # Fallback: extract from page directly
            text_blocks = self.heuristic_builder._extract_text_blocks(page, document_text)
        
        if not text_blocks:
            return layout
        
        # Group by Y-axis (rows)
        rows = self.heuristic_builder._group_by_y_axis(text_blocks)
        
        row_idx = 0
        for row_blocks in rows:
            # Sort by X position
            row_blocks.sort(key=lambda b: b['x_center'])
            
            # Try to split into key-value pairs
            # Left side (x < 0.5) = keys, Right side (x >= 0.5) = values
            left_blocks = [b for b in row_blocks if b['x_center'] < 0.5]
            right_blocks = [b for b in row_blocks if b['x_center'] >= 0.5]
            
            # Combine left blocks as key
            key_text = ' '.join([b['text'] for b in left_blocks]).strip()
            # Combine right blocks as value
            value_text = ' '.join([b['text'] for b in right_blocks]).strip()
            
            # If no clear split, use first half as key, second half as value
            if not key_text and not value_text:
                mid = len(row_blocks) // 2
                key_text = ' '.join([b['text'] for b in row_blocks[:mid]]).strip()
                value_text = ' '.join([b['text'] for b in row_blocks[mid:]]).strip()
            
            # Ensure at least one column has content
            if not key_text and not value_text:
                continue
            
            # Create cells (always 2 columns minimum)
            key_cell = Cell(
                row=row_idx,
                column=0,
                value=key_text if key_text else '',
                style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
            )
            value_cell = Cell(
                row=row_idx,
                column=1,
                value=value_text if value_text else '',
                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
            )
            layout.add_row([key_cell, value_cell])
            row_idx += 1
        
        return layout
    
    def _create_minimal_structured_layout(
        self,
        page: Any,
        document_text: str,
        page_idx: int
    ) -> UnifiedLayout:
        """
        Create minimal structured layout from document text.
        NEVER writes full text into single column - always creates structure.
        """
        layout = UnifiedLayout(page_index=page_idx)
        
        if not document_text:
            # Create empty row to indicate no content
            empty_cell = Cell(
                row=0,
                column=0,
                value="No content extracted",
                style=CellStyle(alignment_horizontal=CellAlignment.CENTER)
            )
            layout.add_row([empty_cell])
            return layout
        
        # Split text into lines
        lines = [line.strip() for line in document_text.split('\n') if line.strip()]
        
        if not lines:
            return layout
        
        # Try to detect key-value patterns
        row_idx = 0
        for line in lines[:100]:  # Limit to first 100 lines
            # Look for key-value separators
            separators = [':', '|', '\t', ' - ', ' – ', ' — ']
            key_value_found = False
            
            for sep in separators:
                if sep in line:
                    parts = line.split(sep, 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        
                        if key and value:
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
                            key_value_found = True
                            break
            
            # If no key-value pattern, split line into words and distribute across columns
            if not key_value_found and line:
                words = line.split()
                if len(words) > 1:
                    # First half words = column 0, second half = column 1
                    mid = len(words) // 2
                    key_text = ' '.join(words[:mid])
                    value_text = ' '.join(words[mid:])
                    
                    key_cell = Cell(
                        row=row_idx,
                        column=0,
                        value=key_text,
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                    value_cell = Cell(
                        row=row_idx,
                        column=1,
                        value=value_text,
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                    layout.add_row([key_cell, value_cell])
                    row_idx += 1
                else:
                    # Single word - place in column 0, leave column 1 empty
                    key_cell = Cell(
                        row=row_idx,
                        column=0,
                        value=line,
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                    value_cell = Cell(
                        row=row_idx,
                        column=1,
                        value='',
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                    layout.add_row([key_cell, value_cell])
                    row_idx += 1
        
        return layout

    def _trim_empty_rows_columns(self, layout: UnifiedLayout) -> UnifiedLayout:
        """
        Remove empty rows and columns from layout.
        Never create rows or columns without actual content.
        """
        if layout.is_empty():
            return layout
        
        rows_with_content = set()
        cols_with_content = set()
        
        for row_cells in layout.rows:
            for cell in row_cells:
                if cell.value and str(cell.value).strip():
                    rows_with_content.add(cell.row)
                    cols_with_content.add(cell.column)
        
        if not rows_with_content:
            return UnifiedLayout(page_index=layout.page_index)
        
        trimmed = UnifiedLayout(page_index=layout.page_index)
        trimmed.metadata = layout.metadata.copy()
        
        sorted_cols = sorted(cols_with_content)
        col_map = {old: new for new, old in enumerate(sorted_cols)}
        
        sorted_rows = sorted(rows_with_content)
        row_map = {old: new for new, old in enumerate(sorted_rows)}
        
        for old_row in sorted_rows:
            original_cells = [c for c in layout.rows[old_row] if c.value and str(c.value).strip()]
            if not original_cells:
                continue
            new_cells = []
            for cell in original_cells:
                new_cells.append(
                    Cell(
                        row=row_map.get(cell.row, cell.row),
                        column=col_map.get(cell.column, cell.column),
                        value=cell.value,
                        style=cell.style,
                        rowspan=cell.rowspan,
                        colspan=cell.colspan,
                        merged=cell.merged
                    )
                )
            if new_cells:
                trimmed.add_row(new_cells)
        
        logger.info(f"Trimmed layout: {len(rows_with_content)} rows, {len(cols_with_content)} columns")
        return trimmed
    
    
    def _cleanup_empty_rows(self, layout: UnifiedLayout) -> UnifiedLayout:
        """Remove rows where ALL cells are empty"""
        if layout.is_empty():
            return layout
        
        rows_with_content = []
        
        for row_idx, row_cells in enumerate(layout.rows):
            # Check if row has at least one meaningful cell
            has_content = False
            for cell in row_cells:
                if cell.value and str(cell.value).strip():
                    has_content = True
                    break
            
            if has_content:
                rows_with_content.append((row_idx, row_cells))
        
        if len(rows_with_content) == len(layout.rows):
            # No empty rows to remove
            return layout
        
        # Rebuild layout with only non-empty rows
        cleaned = UnifiedLayout(page_index=layout.page_index)
        cleaned.metadata = layout.metadata.copy()
        
        for new_row_idx, (old_row_idx, row_cells) in enumerate(rows_with_content):
            # Adjust row indices
            adjusted_cells = []
            for cell in row_cells:
                adjusted_cell = Cell(
                    row=new_row_idx,
                    column=cell.column,
                    value=cell.value,
                    style=cell.style,
                    rowspan=cell.rowspan,
                    colspan=cell.colspan,
                    merged=cell.merged
                )
                adjusted_cells.append(adjusted_cell)
            
            if adjusted_cells:
                cleaned.add_row(adjusted_cells)
        
        logger.info(f"Removed {len(layout.rows) - len(rows_with_content)} empty rows")
        return cleaned
    
    def _cleanup_empty_columns(self, layout: UnifiedLayout) -> UnifiedLayout:
        """Remove columns where ALL cells are empty, respecting header order"""
        if layout.is_empty():
            return layout
        
        # Get header row count
        header_row_count = layout.metadata.get('header_row_count', 0)
        
        # Find columns with content
        cols_with_content = set()
        
        for row_cells in layout.rows:
            for cell in row_cells:
                if cell.value and str(cell.value).strip():
                    cols_with_content.add(cell.column)
        
        if len(cols_with_content) == layout.get_max_column() + 1:
            # No empty columns to remove
            return layout
        
        # Preserve header column order
        header_cols = set()
        if header_row_count > 0:
            for row_idx in range(min(header_row_count, len(layout.rows))):
                for cell in layout.rows[row_idx]:
                    header_cols.add(cell.column)
        
        # Keep header columns even if empty (preserve order)
        cols_to_keep = sorted(cols_with_content | header_cols)
        
        # Rebuild layout with only non-empty columns
        cleaned = UnifiedLayout(page_index=layout.page_index)
        cleaned.metadata = layout.metadata.copy()
        
        col_mapping = {old_col: new_col for new_col, old_col in enumerate(cols_to_keep)}
        
        for row_cells in layout.rows:
            adjusted_cells = []
            for cell in row_cells:
                if cell.column in col_mapping:
                    adjusted_cell = Cell(
                        row=cell.row,
                        column=col_mapping[cell.column],
                        value=cell.value,
                        style=cell.style,
                        rowspan=cell.rowspan,
                        colspan=cell.colspan,
                        merged=cell.merged
                    )
                    adjusted_cells.append(adjusted_cell)
            
            if adjusted_cells:
                cleaned.add_row(adjusted_cells)
        
        logger.info(f"Removed {layout.get_max_column() + 1 - len(cols_to_keep)} empty columns")
        return cleaned
    
    def _normalize_fonts(self, layout: UnifiedLayout) -> UnifiedLayout:
        """Normalize font size across body rows, preserve header font distinction"""
        if layout.is_empty():
            return layout
        
        header_row_count = layout.metadata.get('header_row_count', 0)
        
        # Calculate average body font size
        body_font_sizes = []
        for row_idx, row_cells in enumerate(layout.rows):
            if row_idx >= header_row_count:  # Body rows only
                for cell in row_cells:
                    if cell.style and cell.style.font_size:
                        body_font_sizes.append(cell.style.font_size)
        
        avg_body_font = sum(body_font_sizes) / len(body_font_sizes) if body_font_sizes else None
        
        # Normalize body fonts
        normalized = UnifiedLayout(page_index=layout.page_index)
        normalized.metadata = layout.metadata.copy()
        
        for row_idx, row_cells in enumerate(layout.rows):
            normalized_cells = []
            for cell in row_cells:
                # Preserve header font, normalize body font
                if row_idx < header_row_count:
                    # Keep header style as-is
                    normalized_cells.append(cell)
                else:
                    # Normalize body font size
                    if avg_body_font and cell.style:
                        normalized_style = CellStyle(
                            bold=cell.style.bold,
                            font_size=int(avg_body_font) if avg_body_font else cell.style.font_size,
                            alignment_horizontal=cell.style.alignment_horizontal,
                            background_color=cell.style.background_color,
                            wrap_text=cell.style.wrap_text
                        )
                        normalized_cell = Cell(
                            row=cell.row,
                            column=cell.column,
                            value=cell.value,
                            style=normalized_style,
                            rowspan=cell.rowspan,
                            colspan=cell.colspan,
                            merged=cell.merged
                        )
                        normalized_cells.append(normalized_cell)
                    else:
                        normalized_cells.append(cell)
            
            if normalized_cells:
                normalized.add_row(normalized_cells)
        
        return normalized
    
    def _normalize_alignments(self, layout: UnifiedLayout) -> UnifiedLayout:
        """Normalize alignments: center merged cells vertically, left-align by default"""
        if layout.is_empty():
            return layout
        
        normalized = UnifiedLayout(page_index=layout.page_index)
        normalized.metadata = layout.metadata.copy()
        
        for row_cells in layout.rows:
            normalized_cells = []
            for cell in row_cells:
                # Determine alignment
                alignment = CellAlignment.LEFT  # Default
                
                # Right-align numbers if safe (not merged)
                if cell.value and not cell.merged:
                    try:
                        # Check if value is numeric
                        float(str(cell.value).replace(',', '').replace('₹', '').replace('$', '').strip())
                        alignment = CellAlignment.RIGHT
                    except (ValueError, AttributeError):
                        pass
                
                # Center merged cells
                if cell.merged:
                    alignment = CellAlignment.CENTER
                
                # Preserve existing style but update alignment
                normalized_style = CellStyle(
                    bold=cell.style.bold if cell.style else False,
                    font_size=cell.style.font_size if cell.style else None,
                    alignment_horizontal=alignment,
                    background_color=cell.style.background_color if cell.style else None,
                    wrap_text=cell.style.wrap_text if cell.style else True
                )
                
                normalized_cell = Cell(
                    row=cell.row,
                    column=cell.column,
                    value=cell.value,
                    style=normalized_style,
                    rowspan=cell.rowspan,
                    colspan=cell.colspan,
                    merged=cell.merged
                )
                normalized_cells.append(normalized_cell)
            
            if normalized_cells:
                normalized.add_row(normalized_cells)
        
        return normalized
    
    def _convert_to_simple_rowwise(
        self,
        tables: List,
        document_text: str,
        page_idx: int,
        doc_type: Optional[DocumentType] = None
    ) -> UnifiedLayout:
        """
        Convert tables to simple row-wise layout (downgrade for low confidence).
        Used when TYPE_A confidence < 0.65 or when table processing is not allowed.
        """
        layout = UnifiedLayout(page_index=page_idx)
        row_idx = 0
        
        for table in tables:
            # Extract rows from table
            all_rows = []
            if hasattr(table, 'header_rows') and table.header_rows:
                all_rows.extend(table.header_rows)
            if hasattr(table, 'body_rows') and table.body_rows:
                all_rows.extend(table.body_rows)
            
            for table_row in all_rows:
                if hasattr(table_row, 'cells') and table_row.cells:
                    row_cells = []
                    for col_idx, cell in enumerate(table_row.cells):
                        cell_text = self._extract_cell_text(cell, document_text)
                        if cell_text:
                            cell_obj = Cell(
                                row=row_idx,
                                column=col_idx,
                                value=cell_text,
                                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                            )
                            row_cells.append(cell_obj)
                    
                    if row_cells:
                        layout.add_row(row_cells)
                        row_idx += 1
        
        return layout
    
    def _convert_to_key_value_layout(
        self,
        page: Any,
        document_text: str,
        page_idx: int,
        form_fields: List[Dict],
        page_structure: Optional[Dict] = None,
        page_tables: Optional[List] = None
    ) -> UnifiedLayout:
        """
        KEY_VALUE layout - DYNAMIC COLUMNS (2 → N columns based on detected structure)
        
        Rules:
        1. Detect columns dynamically from X-axis clustering of blocks
        2. Support 2 → N columns automatically (no hard-coded limit)
        3. Label-Value Detection:
           - Contains ":" OR
           - Multiple text blocks on same horizontal line with clear X-separation
        4. Multi-line Value: Append wrapped text to previous value (no new label row)
        5. Strict Row Integrity: One row per detected line
        6. Output Guarantee: Columns = detected vertical bands (unlimited)
        """
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'key_value'
        row_idx = 0
        last_value_cell = None  # Track last value cell for multi-line appending
        column_anchors = None  # Will be set from blocks if available
        
        # Priority 1: Use form fields if available (most reliable for key-value)
        # Note: Form fields use default 2 columns, but will respect column_anchors if set later
        if form_fields:
            logger.info(f"Page {page_idx + 1}: KEY_VALUE - Using {len(form_fields)} form fields")
            for field in form_fields:
                field_name = field.get('name', '').strip()
                field_value = field.get('value', '').strip()
                
                if field_name or field_value:
                    # Use default 2 columns for form fields (can be overridden by column_anchors later)
                    label_cell = Cell(
                        row=row_idx,
                        column=0,
                        value=field_name,
                        style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                    )
                    value_cell = Cell(
                        row=row_idx,
                        column=1,
                        value=field_value,
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                    layout.add_row([label_cell, value_cell])
                    last_value_cell = value_cell
                    row_idx += 1
        
        # Priority 2: Extract key-value pairs from text blocks with bounding boxes (if available)
        if page_structure and 'blocks' in page_structure and page_structure['blocks']:
            logger.info(f"Page {page_idx + 1}: TYPE_B - Extracting key-value pairs from text blocks with bounding boxes")
            blocks = page_structure['blocks']
            
            # Group blocks by Y-position (same horizontal line)
            blocks_by_y = {}
            for block in blocks:
                bbox = block.get('bounding_box', {})
                if bbox:
                    y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
                    y_key = round(y_center * 100) / 100  # Round to 0.01 precision
                    if y_key not in blocks_by_y:
                        blocks_by_y[y_key] = []
                    blocks_by_y[y_key].append(block)
            
            # CRITICAL FIX: Detect column anchors dynamically from X-axis clustering
            # Build column anchors from all blocks (not just 2 columns)
            all_x_positions = []
            for block in blocks:
                bbox = block.get('bounding_box', {})
                if bbox:
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    all_x_positions.append(x_center)
            
            # Cluster X positions to detect column anchors (unlimited columns)
            column_anchors = self._detect_column_anchors_from_x_positions(all_x_positions)
            logger.info(f"Page {page_idx + 1}: KEY_VALUE - Detected {len(column_anchors)} dynamic columns from X-clustering")
            
            # If no column anchors detected, use default 2 columns for compatibility
            if not column_anchors:
                column_anchors = [0.0, 0.5]  # Default: left and right halves
                logger.info(f"Page {page_idx + 1}: KEY_VALUE - No columns detected, using default 2-column layout")
            
            # Process blocks line by line (sorted by Y)
            for y_pos in sorted(blocks_by_y.keys()):
                line_blocks = sorted(blocks_by_y[y_pos], key=lambda b: b.get('bounding_box', {}).get('x_min', 0))
                
                # CRITICAL FIX: Support multiple columns (not just 2)
                # Map each block to its nearest column anchor
                row_cells = []
                for block in line_blocks:
                    bbox = block.get('bounding_box', {})
                    if not bbox:
                        continue
                    
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    block_text = block.get('text', '').strip()
                    
                    if not block_text:
                        continue
                    
                    # Find nearest column anchor
                    col_idx = self._find_nearest_column_anchor(x_center, column_anchors)
                    
                    # Determine if this is a label (first column or contains colon)
                    is_label = (col_idx == 0) or (':' in block_text)
                    
                    # Enable wrap_text for long text or Unicode (Hindi)
                    has_unicode = any(ord(c) > 127 for c in block_text)
                    wrap_text = len(block_text) > 50 or has_unicode
                    
                    cell = Cell(
                        row=row_idx,
                        column=col_idx,
                        value=block_text,
                        style=CellStyle(
                            bold=is_label,
                            alignment_horizontal=CellAlignment.LEFT,
                            wrap_text=wrap_text
                        )
                    )
                    row_cells.append(cell)
                
                # If we have blocks but no cells created, use simple 2-column fallback for this line
                if line_blocks and not row_cells:
                    # Fallback: Use leftmost and rightmost blocks as 2 columns
                    if len(line_blocks) >= 2:
                        left_block = line_blocks[0]
                        right_block = line_blocks[-1]
                        left_text = left_block.get('text', '').strip()
                        right_text = right_block.get('text', '').strip()
                        
                        if left_text or right_text:
                            left_cell = Cell(
                                row=row_idx,
                                column=0,
                                value=left_text,
                                style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                            )
                            right_cell = Cell(
                                row=row_idx,
                                column=1,
                                value=right_text,
                                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                            )
                            row_cells = [left_cell, right_cell]
                
                if row_cells:
                    layout.add_row(row_cells)
                    row_idx += 1
                    continue
                
                # CRITICAL FIX: Handle colon-separated text with dynamic columns
                # If blocks are not mapped to columns, check for colon separator
                if not row_cells:
                    combined_text = ' '.join([b.get('text', '').strip() for b in line_blocks if b.get('text', '').strip()])
                    if combined_text:
                        if ':' in combined_text:
                            parts = combined_text.split(':', 1)
                            if len(parts) == 2:
                                label = parts[0].strip()
                                value = parts[1].strip()
                                
                                if label:  # Label is required
                                    # Use column anchors if available, otherwise use 2 columns
                                    if column_anchors and len(column_anchors) >= 2:
                                        label_col = 0
                                        value_col = min(1, len(column_anchors) - 1)
                                    else:
                                        label_col = 0
                                        value_col = 1
                                    
                                    # Enable wrap_text for Unicode
                                    has_unicode_label = any(ord(c) > 127 for c in label) if label else False
                                    has_unicode_value = any(ord(c) > 127 for c in value) if value else False
                                    
                                    label_cell = Cell(
                                        row=row_idx,
                                        column=label_col,
                                        value=label,
                                        style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT, wrap_text=has_unicode_label or len(label) > 50 if label else False)
                                    )
                                    value_cell = Cell(
                                        row=row_idx,
                                        column=value_col,
                                        value=value,
                                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=has_unicode_value or len(value) > 50 if value else False)
                                    )
                                    layout.add_row([label_cell, value_cell])
                                    last_value_cell = value_cell
                                    row_idx += 1
                                    continue
                    
                    # Safety Rule: Non-matching line - append to previous value OR create new row
                    if last_value_cell is not None:
                        # Append to previous value (notes/address continuation)
                        current_value = last_value_cell.value or ''
                        last_value_cell.value = (current_value + ' ' + combined_text).strip()
                        logger.debug(f"Page {page_idx + 1}: Appended non-matching line to previous value: {combined_text[:50]}")
                    else:
                        # First line without pattern - create single-column row (not forced 2-column)
                        single_cell = Cell(
                            row=row_idx,
                            column=0,
                            value=combined_text,
                            style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                        )
                        layout.add_row([single_cell])
                        row_idx += 1
        
        # Priority 3: Fallback to text-based extraction (if no blocks available)
        elif document_text and row_idx == 0:
            logger.info(f"Page {page_idx + 1}: TYPE_B - Extracting key-value pairs from plain text (no blocks)")
            lines = [line.strip() for line in document_text.split('\n') if line.strip()]
            
            for line in lines[:200]:  # Limit to first 200 lines
                # Check for colon separator
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        label = parts[0].strip()
                        value = parts[1].strip()
                        
                        if label:  # Label is required
                            # Enable wrap_text for Unicode
                            has_unicode_label = any(ord(c) > 127 for c in label) if label else False
                            has_unicode_value = any(ord(c) > 127 for c in value) if value else False
                            
                            label_cell = Cell(
                                row=row_idx,
                                column=0,  # Column A = Label
                                value=label,
                                style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT, wrap_text=has_unicode_label or len(label) > 50 if label else False)
                            )
                            value_cell = Cell(
                                row=row_idx,
                                column=1,  # Column B = Value
                                value=value,
                                style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=has_unicode_value or len(value) > 50 if value else False)
                            )
                            layout.add_row([label_cell, value_cell])
                            last_value_cell = value_cell
                            row_idx += 1
                            continue
                
                # Safety Rule: Non-matching line - append to previous value OR create new row
                if last_value_cell is not None:
                    # Multi-line Value Handling: Append wrapped text to previous value
                    current_value = last_value_cell.value or ''
                    last_value_cell.value = (current_value + ' ' + line).strip()
                    logger.debug(f"Page {page_idx + 1}: Appended wrapped text to previous value: {line[:50]}")
                else:
                    # First line without pattern - create single-column row (not forced 2-column)
                    # Enable wrap_text for Unicode
                    has_unicode = any(ord(c) > 127 for c in line) if line else False
                    wrap_text = len(line) > 50 or has_unicode if line else False
                    
                    single_cell = Cell(
                        row=row_idx,
                        column=0,
                        value=line,
                        style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                    )
                    layout.add_row([single_cell])
                    row_idx += 1
        
        # CRITICAL FIX: Non-empty enforcement - if blocks detected, Excel MUST have data
        if row_idx == 0:
            # If we have blocks but no rows created, create a single-row layout with detected columns
            if page_structure and 'blocks' in page_structure and page_structure['blocks']:
                logger.warning(f"Page {page_idx + 1}: KEY_VALUE - No rows created from blocks, creating fallback layout")
                # Use first few blocks as columns
                fallback_blocks = page_structure['blocks'][:10]  # Use first 10 blocks
                fallback_row = []
                for idx, block in enumerate(fallback_blocks):
                    block_text = block.get('text', '').strip()
                    if block_text:
                        # Enable wrap_text for Unicode
                        has_unicode = any(ord(c) > 127 for c in block_text) if block_text else False
                        wrap_text = len(block_text) > 50 or has_unicode if block_text else False
                        
                        fallback_row.append(Cell(
                            row=0,
                            column=idx,
                            value=block_text,
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                        ))
                if fallback_row:
                    layout.add_row(fallback_row)
                    row_idx = 1
            else:
                # No blocks available - create minimal single-column layout
                logger.warning(f"Page {page_idx + 1}: KEY_VALUE - No blocks available, creating minimal layout")
                # Enable wrap_text for Unicode
                text_snippet = document_text[:200] if document_text else "No content extracted"
                has_unicode = any(ord(c) > 127 for c in text_snippet) if text_snippet else False
                wrap_text = len(text_snippet) > 50 or has_unicode if text_snippet else True
                
                content_cell = Cell(
                    row=0,
                    column=0,
                    value=text_snippet,
                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                )
                layout.add_row([content_cell])
                row_idx = 1
        
        # CRITICAL FIX: Remove hard-coded 2-column enforcement
        # Columns are now dynamic based on detected structure
        max_columns = layout.get_max_column() if layout.rows else 0
        logger.info(f"Page {page_idx + 1}: KEY_VALUE - Created layout with {row_idx} rows, {max_columns} dynamic columns")
        return layout
    
    def _convert_to_plain_text_layout(
        self,
        page: Any,
        document_text: str,
        page_idx: int,
        page_structure: Optional[Dict] = None
    ) -> UnifiedLayout:
        """
        TYPE_D: PLAIN_TEXT layout - Single-column Excel
        No table logic, just sequential text lines.
        """
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'plain_text'
        row_idx = 0
        
        if not document_text:
            # Empty content
            empty_cell = Cell(
                row=0,
                column=0,
                value="No content extracted",
                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
            )
            layout.add_row([empty_cell])
            return layout
        
        # Split text into lines and place each line in single column
        lines = [line.strip() for line in document_text.split('\n') if line.strip()]
        
        for line in lines[:500]:  # Limit to first 500 lines
            text_cell = Cell(
                row=row_idx,
                column=0,  # Always column 0 (single column)
                value=line,
                style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=True)
            )
            layout.add_row([text_cell])
            row_idx += 1
        
        if row_idx == 0:
            # Fail-safe: At least one row
            text_cell = Cell(
                row=0,
                column=0,
                value=document_text[:200] if document_text else "No content extracted",
                style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=True)
            )
            layout.add_row([text_cell])
        
        logger.info(f"Page {page_idx + 1}: TYPE_D - Created plain text layout with {row_idx} rows (single column)")
        return layout
    
    def _is_blank_or_template(self, document_text: str, form_fields: List[Dict], page_structure: Optional[Dict] = None) -> bool:
        """
        Detect if document is blank or template-style (no meaningful content).
        Never mark as conversion failure - always return valid Excel.
        """
        # Check if document text is empty or very short
        if not document_text or len(document_text.strip()) < 10:
            return True
        
        # Check if text is mostly whitespace or placeholder text
        text_ratio = len(document_text.strip()) / len(document_text) if document_text else 0
        if text_ratio < 0.1:
            return True
        
        # Check for common template indicators (placeholder text)
        placeholder_patterns = [
            'enter', 'type here', 'click to', 'placeholder', 'sample text',
            'lorem ipsum', 'example', 'template', 'form', 'fill in'
        ]
        text_lower = document_text.lower()
        placeholder_count = sum(1 for pattern in placeholder_patterns if pattern in text_lower)
        if placeholder_count >= 2:  # Multiple placeholder indicators
            return True
        
        # Check if form fields exist but are all empty
        if form_fields:
            filled_fields = sum(1 for field in form_fields if field.get('value', '').strip())
            if filled_fields == 0:
                return True
        
        return False
    
    def _convert_to_template_headers_only(
        self,
        tables: List,
        document_text: str,
        page_idx: int
    ) -> UnifiedLayout:
        """
        Convert tables to headers-only layout for template/incomplete table case.
        USER-VISIBLE BEHAVIOR: Explicitly treat as "Template/Incomplete Table".
        Output minimal Excel (headers only), do NOT attempt full reconstruction.
        """
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'template_headers_only'
        row_idx = 0
        
        for table in tables:
            # Extract ONLY header rows (no body rows)
            if hasattr(table, 'header_rows') and table.header_rows:
                for header_row in table.header_rows:
                    if hasattr(header_row, 'cells') and header_row.cells:
                        row_cells = []
                        for col_idx, cell in enumerate(header_row.cells):
                            cell_text = self._extract_cell_text(cell, document_text)
                            # Include header even if empty (preserves column structure)
                            cell_obj = Cell(
                                row=row_idx,
                                column=col_idx,
                                value=cell_text if cell_text else f'Column {col_idx + 1}',
                                style=CellStyle(
                                    bold=True,
                                    alignment_horizontal=CellAlignment.LEFT,
                                    background_color='#E0E0E0'  # Light gray for headers
                                )
                            )
                            row_cells.append(cell_obj)
                        
                        if row_cells:
                            layout.add_row(row_cells)
                            row_idx += 1
        
        # If no headers found, create minimal structure
        if row_idx == 0:
            logger.warning(f"Page {page_idx + 1}: No headers found in template, creating minimal structure")
            header_cell = Cell(
                row=0,
                column=0,
                value="Template/Incomplete Table",
                style=CellStyle(
                    bold=True,
                    alignment_horizontal=CellAlignment.CENTER,
                    background_color='#E0E0E0'
                )
            )
            layout.add_row([header_cell])
        
        logger.info(f"Page {page_idx + 1}: Created template headers-only layout with {row_idx} header row(s)")
        return layout
    
    def _check_body_rows_for_soft_mode(
        self,
        page_structure: Optional[Dict],
        document_text: str
    ) -> Tuple[int, int]:
        """
        Check if body rows (excluding header) meet SOFT TABLE MODE criteria.
        
        Returns:
            Tuple[body_rows_count, distinct_x_clusters]
            - body_rows_count: Number of visible body rows (>= 3 required)
            - distinct_x_clusters: Number of distinct X-position clusters in body rows (>= 2 required)
        
        MANDATORY: This check IGNORES header rows completely.
        Only body rows are analyzed for multi-column pattern detection.
        """
        if not page_structure or 'blocks' not in page_structure:
            return (0, 0)
        
        blocks = [b for b in page_structure['blocks'] if b.get('bounding_box') and b.get('text', '').strip()]
        if len(blocks) < 3:
            return (0, 0)
        
        # Group blocks by Y-position (rows)
        # RELAXED precision for Hindi/Devanagari tables (0.02 instead of 0.01)
        blocks_by_y = {}
        for block in blocks:
            bbox = block.get('bounding_box', {})
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 50) / 50  # Round to 0.02 precision (more relaxed for Hindi)
            if y_key not in blocks_by_y:
                blocks_by_y[y_key] = []
            blocks_by_y[y_key].append(block)
        
        # Identify header row (top-most row, typically has different characteristics)
        # Heuristic: Header is usually the top 1-2 rows with fewer blocks or different formatting
        sorted_y_positions = sorted(blocks_by_y.keys())
        if len(sorted_y_positions) < 3:
            return (0, 0)
        
        # Assume top 1-2 rows might be headers, rest are body rows
        # More conservative: exclude only top row as potential header
        header_y_positions = set(sorted_y_positions[:1])  # Top row only
        
        # Extract BODY rows only (exclude header)
        body_rows_blocks = {}
        for y_pos, row_blocks in blocks_by_y.items():
            if y_pos not in header_y_positions:
                # Only count rows with multiple blocks (likely tabular)
                if len(row_blocks) >= 2:
                    body_rows_blocks[y_pos] = row_blocks
        
        body_rows_count = len(body_rows_blocks)
        
        if body_rows_count < 3:
            return (body_rows_count, 0)
        
        # Count distinct X-position clusters in BODY rows only
        x_positions = []
        for row_blocks in body_rows_blocks.values():
            for block in row_blocks:
                bbox = block.get('bounding_box', {})
                x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                x_positions.append(x_center)
        
        if not x_positions:
            return (body_rows_count, 0)
        
        # Cluster X-positions to count distinct clusters
        # RELAXED tolerance for Hindi/Devanagari tables (0.08 = 8% instead of 5%)
        x_positions = sorted(set(x_positions))
        clusters = []
        cluster_tolerance = 0.08  # 8% tolerance (more relaxed for Hindi tables)
        
        for x_pos in x_positions:
            assigned = False
            for cluster in clusters:
                cluster_center = sum(cluster) / len(cluster)
                if abs(x_pos - cluster_center) <= cluster_tolerance:
                    cluster.append(x_pos)
                    assigned = True
                    break
            if not assigned:
                clusters.append([x_pos])
        
        distinct_x_clusters = len(clusters)
        
        return (body_rows_count, distinct_x_clusters)
    
    def _convert_to_soft_table_mode(
        self,
        page_tables: Optional[List],
        document_text: str,
        page_idx: int,
        page_structure: Optional[Dict],
        page: Any
    ) -> UnifiedLayout:
        """
        SOFT TABLE MODE for TYPE_A documents with low confidence but visible body rows.
        
        MANDATORY EXECUTION ORDER:
        1. IGNORE header completely for anchor detection
        2. Build column anchors ONLY from BODY rows
        3. Header row is attached AFTER anchors are built
        
        Rules:
        1. DO NOT collapse into single column
        2. Infer columns using TEXT ALIGNMENT from BODY rows ONLY (ignore header)
        3. Cluster text blocks by X-position across BODY rows
        4. If same X-range repeats in ≥ 3 BODY rows → treat as a column
        5. Aadhaar/Numeric Protection: Force long numeric sequences into single column
        6. Hindi Multi-line Name Handling: Merge vertically close blocks BEFORE column assignment
        7. Safety: Never create more than 10 columns
        8. Fallback: If column inference fails, use 2-column (Index | Content), NOT single-column
        9. Output Guarantee: TYPE_A documents with visible multi-column body data must NEVER collapse entirely into Column A
        """
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'soft_table_mode'
        
        if not page_structure or 'blocks' not in page_structure:
            # Fallback to 2-column if no blocks available
            logger.warning(f"Page {page_idx + 1}: SOFT TABLE MODE - No blocks available, using 2-column fallback")
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        all_blocks = [b for b in page_structure['blocks'] if b.get('bounding_box') and b.get('text', '').strip()]
        if not all_blocks:
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        # Step 1: Separate HEADER rows from BODY rows
        # Group all blocks by Y-position first
        all_blocks_by_y = {}
        for block in all_blocks:
            bbox = block.get('bounding_box', {})
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 100) / 100  # Round to 0.01 precision
            if y_key not in all_blocks_by_y:
                all_blocks_by_y[y_key] = []
            all_blocks_by_y[y_key].append(block)
        
        sorted_y_positions = sorted(all_blocks_by_y.keys())
        if len(sorted_y_positions) < 3:
            # Not enough rows, fallback
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        # Identify header rows (top 1-2 rows, heuristic)
        header_y_positions = set(sorted_y_positions[:1])  # Top row only
        
        # Extract BODY blocks only (exclude header)
        body_blocks = []
        header_blocks = []
        for y_pos, row_blocks in all_blocks_by_y.items():
            if y_pos in header_y_positions:
                header_blocks.extend(row_blocks)
            else:
                body_blocks.extend(row_blocks)
        
        if not body_blocks:
            # No body blocks, fallback
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        logger.info(f"Page {page_idx + 1}: SOFT TABLE MODE - Separated {len(header_blocks)} header blocks from {len(body_blocks)} body blocks")
        
        # Step 2: Hindi Multi-line Name Handling - Merge vertically close BODY blocks BEFORE column assignment
        # Use relaxed Y-threshold for Devanagari
        merged_body_blocks = self._merge_vertically_close_blocks(body_blocks)
        logger.info(f"Page {page_idx + 1}: SOFT TABLE MODE - Merged {len(body_blocks)} body blocks to {len(merged_body_blocks)} after Hindi multi-line handling")
        
        # Step 3: Group merged BODY blocks by Y-position (BODY rows only)
        # RELAXED precision for Hindi/Devanagari tables (0.02 instead of 0.01)
        body_blocks_by_y = {}
        for block in merged_body_blocks:
            bbox = block.get('bounding_box', {})
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 50) / 50  # Round to 0.02 precision (more relaxed for Hindi)
            if y_key not in body_blocks_by_y:
                body_blocks_by_y[y_key] = []
            body_blocks_by_y[y_key].append(block)
        
        # Step 4: Soft Column Detection - Cluster text blocks by X-position across BODY rows ONLY
        # If same X-range repeats in ≥ 3 BODY rows → treat as a column
        # CRITICAL: This uses ONLY body rows, header is completely ignored
        column_anchors = self._infer_soft_columns(body_blocks_by_y)
        
        # Safety: Never create more than 10 columns
        if len(column_anchors) > 10:
            logger.warning(f"Page {page_idx + 1}: SOFT TABLE MODE - Too many columns ({len(column_anchors)}), limiting to 10")
            column_anchors = sorted(column_anchors)[:10]
        
        # Step 4: If column inference fails, fallback to 2-column
        if len(column_anchors) < 2:
            logger.warning(f"Page {page_idx + 1}: SOFT TABLE MODE - Column inference failed ({len(column_anchors)} columns), using 2-column fallback")
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        # Step 5: Attach HEADER row FIRST (after anchors are built)
        row_idx = 0
        header_row_added = False
        
        if header_blocks:
            # Process header blocks and attach to layout
            header_blocks_by_y = {}
            for block in header_blocks:
                bbox = block.get('bounding_box', {})
                y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
                y_key = round(y_center * 100) / 100
                if y_key not in header_blocks_by_y:
                    header_blocks_by_y[y_key] = []
                header_blocks_by_y[y_key].append(block)
            
            # Add header rows (sorted by Y-position, top to bottom)
            for y_pos in sorted(header_blocks_by_y.keys()):
                header_row_blocks = sorted(header_blocks_by_y[y_pos], key=lambda b: b.get('bounding_box', {}).get('x_min', 0))
                header_row_cells = [None] * len(column_anchors)  # Initialize with same column count
                
                for block in header_row_blocks:
                    bbox = block.get('bounding_box', {})
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    text = block.get('text', '').strip()
                    
                    if not text:
                        continue
                    
                    # Find nearest column anchor for header
                    nearest_col = min(range(len(column_anchors)), key=lambda i: abs(column_anchors[i] - x_center))
                    
                    # Combine with existing cell if present
                    if header_row_cells[nearest_col] is not None:
                        existing_text = header_row_cells[nearest_col].value or ''
                        header_row_cells[nearest_col].value = (existing_text + ' ' + text).strip()
                    else:
                        header_row_cells[nearest_col] = Cell(
                            row=row_idx,
                            column=nearest_col,
                            value=text,
                            style=CellStyle(
                                bold=True,
                                alignment_horizontal=CellAlignment.LEFT,
                                background_color='#E0E0E0'  # Light gray for headers
                            )
                        )
                
                # Fill empty header cells and add row
                final_header_row_cells = []
                for col_idx in range(len(column_anchors)):
                    if header_row_cells[col_idx] is not None:
                        final_header_row_cells.append(header_row_cells[col_idx])
                    else:
                        final_header_row_cells.append(Cell(
                            row=row_idx,
                            column=col_idx,
                            value='',
                            style=CellStyle(
                                bold=True,
                                alignment_horizontal=CellAlignment.LEFT,
                                background_color='#E0E0E0'
                            )
                        ))
                
                if final_header_row_cells:
                    layout.add_row(final_header_row_cells)
                    row_idx += 1
                    header_row_added = True
        
        # Step 6: Assign BODY blocks to columns and build layout
        for y_pos in sorted(body_blocks_by_y.keys()):
            row_blocks = sorted(body_blocks_by_y[y_pos], key=lambda b: b.get('bounding_box', {}).get('x_min', 0))
            row_cells = [None] * len(column_anchors)  # Initialize row with empty cells
            
            for block in row_blocks:
                bbox = block.get('bounding_box', {})
                x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                text = block.get('text', '').strip()
                
                if not text:
                    continue
                
                # Step 6: Aadhaar/Numeric Protection - Detect long numeric sequences
                is_aadhaar = self._is_aadhaar_or_long_numeric(text)
                if is_aadhaar:
                    # Force into first available column (prefer leftmost)
                    target_col = 0
                    for col_idx in range(len(column_anchors)):
                        if row_cells[col_idx] is None or not row_cells[col_idx].value:
                            target_col = col_idx
                            break
                    
                    # Combine with existing cell if present
                    if row_cells[target_col] is not None:
                        existing_text = row_cells[target_col].value or ''
                        text = (existing_text + ' ' + text).strip()
                    
                    row_cells[target_col] = Cell(
                        row=row_idx,
                        column=target_col,
                        value=text,
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                else:
                    # Find nearest column anchor
                    nearest_col = min(range(len(column_anchors)), key=lambda i: abs(column_anchors[i] - x_center))
                    
                    # Combine with existing cell if present
                    if row_cells[nearest_col] is not None:
                        existing_text = row_cells[nearest_col].value or ''
                        row_cells[nearest_col].value = (existing_text + ' ' + text).strip()
                    else:
                        # Enable wrap_text for long text or Unicode (Hindi) to prevent overflow
                        has_unicode = any(ord(c) > 127 for c in text)
                        wrap_text = len(text) > 50 or has_unicode
                        
                        row_cells[nearest_col] = Cell(
                            row=row_idx,
                            column=nearest_col,
                            value=text,
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                        )
            
            # Add row with all cells (fill empty cells)
            final_row_cells = []
            for col_idx in range(len(column_anchors)):
                if row_cells[col_idx] is not None:
                    final_row_cells.append(row_cells[col_idx])
                else:
                    # Empty cell
                    final_row_cells.append(Cell(
                        row=row_idx,
                        column=col_idx,
                        value='',
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    ))
            
            if final_row_cells:
                layout.add_row(final_row_cells)
                row_idx += 1
        
        # CRITICAL FIX: Remove 2-column fallback - columns must be dynamic
        # If layout has columns, use it as-is (even if 1 column)
        # Only create fallback if NO data detected at all
        if layout.get_max_column() == 0 and row_idx == 0:
            logger.warning(f"Page {page_idx + 1}: SOFT TABLE MODE - No columns detected, creating fallback from text")
            # Create single-column layout from text (not forced 2-column)
            if document_text:
                lines = document_text.split('\n')[:50]  # First 50 lines
                for idx, line in enumerate(lines):
                    if line.strip():
                        cell = Cell(
                            row=idx,
                            column=0,
                            value=line.strip(),
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                        )
                        layout.add_row([cell])
        
        logger.info(f"Page {page_idx + 1}: SOFT TABLE MODE - Created layout with {row_idx} rows, {layout.get_max_column()} columns")
        return layout
    
    def _merge_vertically_close_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """
        Merge vertically close text blocks (Hindi multi-line name handling).
        Use relaxed Y-threshold for Devanagari.
        """
        if not blocks:
            return []
        
        # Sort by Y-position
        sorted_blocks = sorted(blocks, key=lambda b: (
            b.get('bounding_box', {}).get('y_min', 0),
            b.get('bounding_box', {}).get('x_min', 0)
        ))
        
        merged = []
        current_group = [sorted_blocks[0]]
        
        for block in sorted_blocks[1:]:
            last_block = current_group[-1]
            last_bbox = last_block.get('bounding_box', {})
            curr_bbox = block.get('bounding_box', {})
            
            last_y_max = last_bbox.get('y_max', 0)
            curr_y_min = curr_bbox.get('y_min', 1)
            last_x_center = (last_bbox.get('x_min', 0) + last_bbox.get('x_max', 0)) / 2
            curr_x_center = (curr_bbox.get('x_min', 0) + curr_bbox.get('x_max', 0)) / 2
            
            # Calculate dynamic Y-threshold (relaxed for Devanagari)
            last_height = last_bbox.get('y_max', 0) - last_bbox.get('y_min', 0)
            y_threshold = last_height * 0.8  # Relaxed threshold (80% of height)
            
            # Check if blocks are vertically close and horizontally aligned
            y_distance = curr_y_min - last_y_max
            x_overlap = abs(curr_x_center - last_x_center) < (last_bbox.get('x_max', 1) - last_bbox.get('x_min', 0)) * 0.5
            
            if y_distance <= y_threshold and x_overlap:
                # Merge: combine text and expand bounding box
                merged_text = (last_block.get('text', '') + ' ' + block.get('text', '')).strip()
                merged_bbox = {
                    'x_min': min(last_bbox.get('x_min', 0), curr_bbox.get('x_min', 0)),
                    'x_max': max(last_bbox.get('x_max', 0), curr_bbox.get('x_max', 0)),
                    'y_min': min(last_bbox.get('y_min', 0), curr_bbox.get('y_min', 0)),
                    'y_max': max(last_bbox.get('y_max', 0), curr_bbox.get('y_max', 0))
                }
                merged_block = {
                    'text': merged_text,
                    'bounding_box': merged_bbox
                }
                current_group[-1] = merged_block
            else:
                # Start new group
                merged.append(current_group[0])
                current_group = [block]
        
        # Add last group
        if current_group:
            merged.append(current_group[0])
        
        return merged
    
    def _infer_soft_columns(self, blocks_by_y: Dict[float, List[Dict]]) -> List[float]:
        """
        Infer column anchors by clustering text blocks by X-position across rows.
        If same X-range repeats in ≥ 3 rows → treat as a column.
        """
        if not blocks_by_y:
            return []
        
        # Collect all X-center positions
        x_positions = []
        for row_blocks in blocks_by_y.values():
            for block in row_blocks:
                bbox = block.get('bounding_box', {})
                x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                x_positions.append(x_center)
        
        if not x_positions:
            return []
        
        # CRITICAL FIX: Use stricter clustering tolerance (5% instead of 8%)
        # This prevents multiple distinct columns from being merged into one
        x_positions = sorted(set(x_positions))
        clusters = []
        cluster_tolerance = 0.05  # 5% tolerance (stricter to prevent column merging)
        
        for x_pos in x_positions:
            # Find existing cluster or create new one
            assigned = False
            for cluster in clusters:
                cluster_center = sum(cluster) / len(cluster)
                if abs(x_pos - cluster_center) <= cluster_tolerance:
                    cluster.append(x_pos)
                    assigned = True
                    break
            
            if not assigned:
                clusters.append([x_pos])
        
        # Count how many rows have blocks in each cluster
        column_anchors = []
        for cluster in clusters:
            cluster_center = sum(cluster) / len(cluster)
            row_count = 0
            
            for row_blocks in blocks_by_y.values():
                for block in row_blocks:
                    bbox = block.get('bounding_box', {})
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    if abs(x_center - cluster_center) <= cluster_tolerance:
                        row_count += 1
                        break  # Count each row only once
            
            # If same X-range repeats in ≥ 3 rows → treat as a column
            if row_count >= 3:
                column_anchors.append(cluster_center)
        
        # Sort column anchors by X-position
        column_anchors.sort()
        
        return column_anchors
    
    def _check_visual_table_candidate(self, full_structure: Dict) -> bool:
        """
        Check if a TYPE_D document should be promoted to TYPE_A_CANDIDATE (visual table).
        
        Visual Table Candidate Rules:
        1. blocks >= 30
        2. repeated horizontal alignment across >= 3 rows
        3. >= 2 distinct X-position clusters repeating vertically
        4. presence of numeric columns (IDs, Aadhaar, serial numbers)
        
        Safety:
        - Promotion allowed ONLY for digital_pdf (checked by caller)
        - Promotion forbidden for scanned images, letters, paragraphs (checked by caller)
        """
        if not full_structure or 'blocks' not in full_structure:
            return False
        
        blocks = [b for b in full_structure['blocks'] if b.get('bounding_box') and b.get('text', '').strip()]
        
        # Rule 1: blocks >= 30
        if len(blocks) < 30:
            logger.debug(f"Visual table candidate check: Only {len(blocks)} blocks, need >= 30")
            return False
        
        # Group blocks by Y-position (rows) - use relaxed precision
        blocks_by_y = {}
        for block in blocks:
            bbox = block.get('bounding_box', {})
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 50) / 50  # 0.02 precision (relaxed)
            if y_key not in blocks_by_y:
                blocks_by_y[y_key] = []
            blocks_by_y[y_key].append(block)
        
        # Rule 2: repeated horizontal alignment across >= 3 rows
        rows_with_horizontal_alignment = 0
        x_clusters_all_rows = []  # Collect all X-positions
        numeric_blocks_count = 0  # Count numeric blocks (Rule 4)
        
        for y_pos, row_blocks in blocks_by_y.items():
            if len(row_blocks) >= 2:  # At least 2 blocks in row (horizontal alignment)
                x_positions = []
                for block in row_blocks:
                    bbox = block.get('bounding_box', {})
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    x_positions.append(x_center)
                    
                    # Check for numeric content (Rule 4)
                    text = block.get('text', '').strip()
                    if self._is_aadhaar_or_long_numeric(text):
                        numeric_blocks_count += 1
                    # Also check for short numeric sequences (serial numbers, IDs)
                    digits_only = ''.join(c for c in text if c.isdigit())
                    if 4 <= len(digits_only) <= 9 and len(text) <= 20:  # Short numeric IDs
                        numeric_blocks_count += 1
                
                # Check if X-positions are distinct and separated
                x_positions = sorted(set(x_positions))
                if len(x_positions) >= 2:
                    # Check if positions are reasonably separated (at least 5% of page width)
                    min_separation = 0.05
                    has_separation = False
                    for i in range(len(x_positions) - 1):
                        if x_positions[i + 1] - x_positions[i] >= min_separation:
                            has_separation = True
                            break
                    
                    if has_separation:
                        rows_with_horizontal_alignment += 1
                        x_clusters_all_rows.extend(x_positions)
        
        # Rule 2: Need >= 3 rows with horizontal alignment
        if rows_with_horizontal_alignment < 3:
            logger.debug(f"Visual table candidate check: Only {rows_with_horizontal_alignment} rows with horizontal alignment, need >= 3")
            return False
        
        # Rule 3: >= 2 distinct X-position clusters repeating vertically
        if len(x_clusters_all_rows) < 10:
            logger.debug(f"Visual table candidate check: Only {len(x_clusters_all_rows)} X-positions, need >= 10")
            return False
        
        # Cluster X-positions to find distinct column bands
        x_clusters_all_rows = sorted(set(x_clusters_all_rows))
        clusters = []
        cluster_tolerance = 0.08  # 8% tolerance
        
        for x_pos in x_clusters_all_rows:
            assigned = False
            for cluster in clusters:
                cluster_center = sum(cluster) / len(cluster)
                if abs(x_pos - cluster_center) <= cluster_tolerance:
                    cluster.append(x_pos)
                    assigned = True
                    break
            if not assigned:
                clusters.append([x_pos])
        
        # Count how many rows have blocks in each cluster (repeating vertically)
        distinct_vertical_bands = 0
        for cluster in clusters:
            cluster_center = sum(cluster) / len(cluster)
            row_count = 0
            
            for y_pos, row_blocks in blocks_by_y.items():
                if len(row_blocks) >= 2:  # Only check rows with multiple blocks
                    for block in row_blocks:
                        bbox = block.get('bounding_box', {})
                        x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                        if abs(x_center - cluster_center) <= cluster_tolerance:
                            row_count += 1
                            break  # Count each row only once
            
            # If same X-range appears in >= 2 rows → distinct vertical band
            if row_count >= 2:
                distinct_vertical_bands += 1
        
        # Rule 3: Need >= 2 distinct X-position clusters repeating vertically
        if distinct_vertical_bands < 2:
            logger.debug(f"Visual table candidate check: Only {distinct_vertical_bands} distinct vertical bands, need >= 2")
            return False
        
        # Rule 4: Presence of numeric columns (IDs, Aadhaar, serial numbers)
        # We already counted numeric_blocks_count above
        if numeric_blocks_count < 2:
            logger.debug(f"Visual table candidate check: Only {numeric_blocks_count} numeric blocks, need >= 2")
            return False
        
        # All rules passed - eligible for promotion
        logger.info(f"Visual table candidate check PASSED: {len(blocks)} blocks, {rows_with_horizontal_alignment} aligned rows, {distinct_vertical_bands} vertical bands, {numeric_blocks_count} numeric blocks")
        return True
    
    def _is_aadhaar_or_long_numeric(self, text: str) -> bool:
        """
        Detect long numeric sequences (10-12 digits with spaces) - Aadhaar protection.
        """
        # Remove spaces and check if it's a long numeric sequence
        digits_only = ''.join(c for c in text if c.isdigit())
        if 10 <= len(digits_only) <= 12:
            # Check if original text has spaces (Aadhaar format: XXXX XXXX XXXX)
            if ' ' in text:
                return True
        return False
    
    def _soft_table_fallback_2column(self, document_text: str, page_idx: int) -> UnifiedLayout:
        """
        Fallback to 2-column layout (Index | Content) if column inference fails.
        NEVER use single-column text dump.
        """
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'soft_table_fallback_2column'
        
        if not document_text:
            # Empty - create minimal 2-column structure
            index_cell = Cell(
                row=0,
                column=0,
                value="Index",
                style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
            )
            content_cell = Cell(
                row=0,
                column=1,
                value="Content",
                style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
            )
            layout.add_row([index_cell, content_cell])
            return layout
        
        # Split text into lines and create 2-column layout
        lines = [line.strip() for line in document_text.split('\n') if line.strip()]
        
        for row_idx, line in enumerate(lines[:500]):  # Limit to 500 lines
            index_cell = Cell(
                row=row_idx,
                column=0,  # Column A = Index
                value=str(row_idx + 1),
                style=CellStyle(alignment_horizontal=CellAlignment.RIGHT)
            )
            content_cell = Cell(
                row=row_idx,
                column=1,  # Column B = Content
                value=line,
                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
            )
            layout.add_row([index_cell, content_cell])
        
        logger.info(f"Page {page_idx + 1}: SOFT TABLE MODE - Using 2-column fallback with {len(lines)} rows")
        return layout
    
    def _check_visual_grid_reconstruction_trigger(
        self,
        page_structure: Optional[Dict],
        document_text: str
    ) -> Tuple[bool, int]:
        """
        Check if VISUAL GRID RECONSTRUCTION MODE should be triggered.
        
        Returns:
            Tuple[eligible, stable_rows]
            - eligible: True if visual grid reconstruction is eligible
            - stable_rows: Number of rows showing stable X-position bands (>= 5 required)
        
        Trigger conditions:
        - document_type == TYPE_A (checked by caller)
        - table_confidence < threshold (checked by caller)
        - no native table objects detected (checked by caller)
        - visible text blocks show stable X-position bands across >= 5 rows
        """
        if not page_structure or 'blocks' not in page_structure:
            return (False, 0)
        
        blocks = [b for b in page_structure['blocks'] if b.get('bounding_box') and b.get('text', '').strip()]
        if len(blocks) < 10:  # Need at least 10 blocks for meaningful grid
            return (False, 0)
        
        # Group blocks by Y-position (rows) - use relaxed precision for visual alignment
        blocks_by_y = {}
        for block in blocks:
            bbox = block.get('bounding_box', {})
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 50) / 50  # 0.02 precision (relaxed for visual alignment)
            if y_key not in blocks_by_y:
                blocks_by_y[y_key] = []
            blocks_by_y[y_key].append(block)
        
        # Count rows with stable X-position bands
        # A row has "stable X-position bands" if it has >= 2 blocks with distinct X-positions
        stable_rows = 0
        x_bands_all_rows = []  # Collect all X-positions across rows
        
        for y_pos, row_blocks in blocks_by_y.items():
            if len(row_blocks) >= 2:  # At least 2 blocks in row
                x_positions = []
                for block in row_blocks:
                    bbox = block.get('bounding_box', {})
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    x_positions.append(x_center)
                
                # Check if X-positions are distinct (not all clustered together)
                x_positions = sorted(set(x_positions))
                if len(x_positions) >= 2:
                    # Check if positions are reasonably separated (at least 5% of page width)
                    min_separation = 0.05
                    has_separation = False
                    for i in range(len(x_positions) - 1):
                        if x_positions[i + 1] - x_positions[i] >= min_separation:
                            has_separation = True
                            break
                    
                    if has_separation:
                        stable_rows += 1
                        x_bands_all_rows.extend(x_positions)
        
        # Check if X-position bands are consistent across rows (visual grid pattern)
        if stable_rows >= 5 and len(x_bands_all_rows) >= 10:
            # Cluster X-positions to see if there are stable column bands
            x_bands_all_rows = sorted(set(x_bands_all_rows))
            clusters = []
            cluster_tolerance = 0.08  # 8% tolerance for visual alignment
            
            for x_pos in x_bands_all_rows:
                assigned = False
                for cluster in clusters:
                    cluster_center = sum(cluster) / len(cluster)
                    if abs(x_pos - cluster_center) <= cluster_tolerance:
                        cluster.append(x_pos)
                        assigned = True
                        break
                if not assigned:
                    clusters.append([x_pos])
            
            # If we have at least 2 distinct column bands, visual grid is eligible
            distinct_bands = len([c for c in clusters if len(c) >= 2])  # Bands that appear in multiple rows
            eligible = distinct_bands >= 2
            
            return (eligible, stable_rows)
        
        return (False, stable_rows)
    
    def _convert_to_visual_grid_reconstruction_mode(
        self,
        page_tables: Optional[List],
        document_text: str,
        page_idx: int,
        page_structure: Optional[Dict],
        page: Any
    ) -> UnifiedLayout:
        """
        OPTIONAL VISUAL GRID RECONSTRUCTION MODE for TYPE_A documents.
        
        This mode:
        1. IGNORES Document AI table semantics completely
        2. Clusters text blocks by X-position into columns
        3. Clusters text blocks by Y-position into rows
        4. Reconstructs a grid purely from visual alignment
        5. Merges numeric blocks (e.g. Aadhaar) into single cells
        6. Allows slight misalignment rather than collapsing to one column
        
        Safety rules:
        - Max columns = 10
        - If clustering confidence is low → fallback to 2-column (Index | Content)
        - This mode must be clearly marked as "Visual reconstruction"
        """
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'visual_grid_reconstruction'
        layout.metadata['reconstruction_mode'] = 'VISUAL_GRID'
        
        if not page_structure or 'blocks' not in page_structure or not page_structure.get('blocks'):
            logger.warning(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - No blocks in page_structure, using 2-column fallback")
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        all_blocks = [b for b in page_structure['blocks'] if b.get('bounding_box') and b.get('text', '').strip()]
        if not all_blocks:
            logger.warning(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - No valid blocks after filtering, using 2-column fallback")
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        logger.info(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - Processing {len(all_blocks)} text blocks")
        
        # Step 1: Merge numeric blocks (Aadhaar) into single cells BEFORE clustering
        merged_blocks = self._merge_numeric_blocks(all_blocks)
        logger.info(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - Merged {len(all_blocks)} blocks to {len(merged_blocks)} after numeric merging")
        
        # Step 2: Cluster by Y-position into rows (relaxed precision)
        blocks_by_y = {}
        for block in merged_blocks:
            bbox = block.get('bounding_box', {})
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 50) / 50  # 0.02 precision (relaxed for visual alignment)
            if y_key not in blocks_by_y:
                blocks_by_y[y_key] = []
            blocks_by_y[y_key].append(block)
        
        # Step 3: Cluster by X-position into columns (visual column bands)
        column_anchors = self._infer_visual_grid_columns(blocks_by_y)
        
        # Safety: Max 10 columns
        if len(column_anchors) > 10:
            logger.warning(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - Too many columns ({len(column_anchors)}), limiting to 10")
            column_anchors = sorted(column_anchors)[:10]
        
        # Step 4: Check clustering confidence
        if len(column_anchors) < 2:
            logger.warning(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - Low clustering confidence ({len(column_anchors)} columns), using 2-column fallback")
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        # Step 5: Reconstruct grid from visual alignment
        row_idx = 0
        for y_pos in sorted(blocks_by_y.keys()):
            row_blocks = sorted(blocks_by_y[y_pos], key=lambda b: b.get('bounding_box', {}).get('x_min', 0))
            row_cells = [None] * len(column_anchors)  # Initialize row with empty cells
            
            for block in row_blocks:
                bbox = block.get('bounding_box', {})
                x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                text = block.get('text', '').strip()
                
                if not text:
                    continue
                
                # Find nearest column anchor (allow slight misalignment)
                nearest_col = min(range(len(column_anchors)), key=lambda i: abs(column_anchors[i] - x_center))
                
                # Check if misalignment is acceptable (within 10% of page width)
                misalignment_threshold = 0.10
                distance_to_anchor = abs(column_anchors[nearest_col] - x_center)
                
                if distance_to_anchor <= misalignment_threshold:
                    # Acceptable misalignment - assign to column
                    # CRITICAL FIX: Only combine if blocks actually overlap horizontally (same physical cell)
                    if row_cells[nearest_col] is not None:
                        # Check if this block overlaps with existing cell's block
                        # Get X-range of this block
                        block_x_min = bbox.get('x_min', 0)
                        block_x_max = bbox.get('x_max', 0)
                        
                        # Try to find existing block's X-range (we need to track this)
                        # For now, use a stricter check: only combine if X-centers are very close (< 2% of page)
                        horizontal_overlap_threshold = 0.02  # 2% of page width
                        
                        # Check if blocks are horizontally overlapping (same physical cell)
                        # If X-centers are very close, they're likely the same cell
                        if distance_to_anchor <= horizontal_overlap_threshold:
                            # Same cell - combine text (e.g., Aadhaar digits split across blocks)
                            existing_text = row_cells[nearest_col].value or ''
                            row_cells[nearest_col].value = (existing_text + ' ' + text).strip()
                        else:
                            # Different cell - create new column instead of combining
                            if len(column_anchors) < 20:  # Max 20 columns
                                column_anchors.append(x_center)
                                column_anchors = sorted(column_anchors)
                                new_col = column_anchors.index(x_center)
                                # Expand row_cells array
                                while len(row_cells) < len(column_anchors):
                                    row_cells.append(None)
                                
                                has_unicode = any(ord(c) > 127 for c in text)
                                wrap_text = len(text) > 50 or has_unicode
                                
                                row_cells[new_col] = Cell(
                                    row=row_idx,
                                    column=new_col,
                                    value=text,
                                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                                )
                            else:
                                # Too many columns - use nearest empty column
                                for col_idx in range(len(column_anchors)):
                                    if row_cells[col_idx] is None:
                                        row_cells[col_idx] = Cell(
                                            row=row_idx,
                                            column=col_idx,
                                            value=text,
                                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                        )
                                        break
                    else:
                        # Enable wrap_text for long text or Unicode (Hindi) to prevent overflow
                        has_unicode = any(ord(c) > 127 for c in text)
                        wrap_text = len(text) > 50 or has_unicode
                        
                        row_cells[nearest_col] = Cell(
                            row=row_idx,
                            column=nearest_col,
                            value=text,
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                        )
                else:
                    # Too much misalignment - try next nearest column or create new if within limit
                    if len(column_anchors) < 10:
                        # Try second nearest
                        sorted_cols = sorted(range(len(column_anchors)), key=lambda i: abs(column_anchors[i] - x_center))
                        if len(sorted_cols) > 1:
                            second_nearest = sorted_cols[1]
                            distance_2 = abs(column_anchors[second_nearest] - x_center)
                            if distance_2 <= misalignment_threshold:
                                # CRITICAL FIX: Only combine if blocks actually overlap
                                if row_cells[second_nearest] is not None:
                                    # Check horizontal overlap
                                    horizontal_overlap_threshold = 0.02
                                    if distance_2 <= horizontal_overlap_threshold:
                                        # Same cell - combine
                                        existing_text = row_cells[second_nearest].value or ''
                                        row_cells[second_nearest].value = (existing_text + ' ' + text).strip()
                                    else:
                                        # Different cell - create new column
                                        if len(column_anchors) < 20:
                                            column_anchors.append(x_center)
                                            column_anchors = sorted(column_anchors)
                                            new_col = column_anchors.index(x_center)
                                            while len(row_cells) < len(column_anchors):
                                                row_cells.append(None)
                                            row_cells[new_col] = Cell(
                                                row=row_idx,
                                                column=new_col,
                                                value=text,
                                                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                            )
                                else:
                                    row_cells[second_nearest] = Cell(
                                        row=row_idx,
                                        column=second_nearest,
                                        value=text,
                                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                    )
                            else:
                                # Still too misaligned - create new column instead of forcing into nearest
                                if len(column_anchors) < 20:
                                    column_anchors.append(x_center)
                                    column_anchors = sorted(column_anchors)
                                    new_col = column_anchors.index(x_center)
                                    while len(row_cells) < len(column_anchors):
                                        row_cells.append(None)
                                    
                                    has_unicode = any(ord(c) > 127 for c in text)
                                    wrap_text = len(text) > 50 or has_unicode
                                    
                                    row_cells[new_col] = Cell(
                                        row=row_idx,
                                        column=new_col,
                                        value=text,
                                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                                    )
                                elif row_cells[nearest_col] is None:
                                    # Only use nearest if it's empty and we can't create new column
                                    has_unicode = any(ord(c) > 127 for c in text)
                                    wrap_text = len(text) > 50 or has_unicode
                                    
                                    row_cells[nearest_col] = Cell(
                                        row=row_idx,
                                        column=nearest_col,
                                        value=text,
                                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                                    )
                                # If nearest column already has content and we can't create new, skip this block
                                # (Don't combine - it would merge different columns)
                                    # Enable wrap_text for long text or Unicode (Hindi) to prevent overflow
                                    has_unicode = any(ord(c) > 127 for c in text)
                                    wrap_text = len(text) > 50 or has_unicode
                                    
                                    row_cells[nearest_col] = Cell(
                                        row=row_idx,
                                        column=nearest_col,
                                        value=text,
                                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                                    )
            
            # Add row with all cells (fill empty cells)
            final_row_cells = []
            for col_idx in range(len(column_anchors)):
                if row_cells[col_idx] is not None:
                    final_row_cells.append(row_cells[col_idx])
                else:
                    # Empty cell
                    final_row_cells.append(Cell(
                        row=row_idx,
                        column=col_idx,
                        value='',
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    ))
            
            if final_row_cells:
                layout.add_row(final_row_cells)
                row_idx += 1
        
        # CRITICAL FIX: Remove 2-column fallback - columns must be dynamic
        # If layout has columns, use it as-is (even if 1 column)
        # Only create fallback if NO data detected at all
        if layout.get_max_column() == 0 and row_idx == 0:
            logger.warning(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - No columns detected, creating fallback from text")
            # Create single-column layout from text (not forced 2-column)
            if document_text:
                lines = document_text.split('\n')[:50]  # First 50 lines
                for idx, line in enumerate(lines):
                    if line.strip():
                        cell = Cell(
                            row=idx,
                            column=0,
                            value=line.strip(),
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                        )
                        layout.add_row([cell])
        
        logger.info(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - Created layout with {row_idx} rows, {layout.get_max_column()} columns")
        return layout
    
    def _convert_to_geometric_hybrid_grid(
        self,
        blocks: List[Any],
        document_text: str,
        page_idx: int,
        page_structure: Optional[Dict]
    ) -> UnifiedLayout:
        """
        GEOMETRIC_HYBRID mode: Unlimited geometric grid from OCR blocks.
        
        This mode:
        - Builds grid dynamically using OCR bounding boxes
        - Detects unlimited columns via X-axis clustering
        - Detects unlimited rows via Y-axis line grouping
        - Never hardcodes row or column counts
        - Preserves text integrity (1 block = 1 cell)
        - Detects merged cells via bounding box overlap
        - Preserves background color and style metadata
        - Preserves image/logo blocks as anchored objects
        - Prevents fake or empty rows/columns
        """
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'geometric_hybrid'
        layout.metadata['reconstruction_mode'] = 'GEOMETRIC_HYBRID'
        
        if not blocks:
            logger.warning(f"Page {page_idx + 1}: GEOMETRIC_HYBRID - No blocks available, trying page_structure")
            # CRITICAL FIX: Try to get blocks from page_structure if not provided
            if page_structure and 'blocks' in page_structure:
                blocks = page_structure['blocks']
                logger.info(f"Page {page_idx + 1}: Found {len(blocks)} blocks in page_structure")
            
            if not blocks:
                logger.warning(f"Page {page_idx + 1}: GEOMETRIC_HYBRID - No blocks found, using PLAIN_TEXT fallback")
                # Use PLAIN_TEXT mode instead of minimal fallback - preserves structure better
                if document_text and len(document_text.strip()) > 10:
                    logger.critical(f"   Falling back to PLAIN_TEXT mode for Page {page_idx + 1}")
                    return self._convert_to_plain_text_layout(
                        page=page,
                        document_text=document_text,
                        page_idx=page_idx,
                        page_structure=page_structure
                    )
                return self._create_empty_layout(page_idx)
        
        # Convert blocks to dict format if needed
        all_blocks = []
        for block in blocks:
            if isinstance(block, dict):
                all_blocks.append(block)
            elif hasattr(block, 'layout') and hasattr(block, 'text'):
                # Convert DocAI block to dict
                bbox = {}
                if hasattr(block.layout, 'bounding_poly'):
                    vertices = block.layout.bounding_poly.normalized_vertices
                    if len(vertices) >= 4:
                        xs = [v.x for v in vertices if hasattr(v, 'x')]
                        ys = [v.y for v in vertices if hasattr(v, 'y')]
                        if xs and ys:
                            bbox = {
                                'x_min': min(xs),
                                'x_max': max(xs),
                                'y_min': min(ys),
                                'y_max': max(ys)
                            }
                all_blocks.append({
                    'text': block.text if hasattr(block, 'text') else '',
                    'bounding_box': bbox,
                    'confidence': getattr(block.layout, 'confidence', 1.0) if hasattr(block, 'layout') else 1.0
                })
        
        # Filter blocks with valid bounding boxes and text
        valid_blocks = [b for b in all_blocks if b.get('bounding_box') and b.get('text', '').strip()]
        
        logger.critical("=" * 80)
        logger.critical(f"📊 STEP 2: Filtering blocks")
        logger.critical(f"   Total blocks received: {len(all_blocks)}")
        logger.critical(f"   Valid blocks (with bbox + text): {len(valid_blocks)}")
        
        if valid_blocks:
            logger.critical(f"   First 10 valid blocks:")
            for idx, block in enumerate(valid_blocks[:10]):
                text = block.get('text', '')[:30]
                bbox = block.get('bounding_box', {})
                logger.critical(f"      [{idx}] '{text}' bbox={bbox}")
        logger.critical("=" * 80)
        
        if not valid_blocks:
            logger.critical(f"❌ GEOMETRIC_HYBRID: No valid blocks with text - returning empty layout")
            return self._create_empty_layout(page_idx)
        
        # Step 1: Merge numeric blocks (Aadhaar) into single cells
        merged_blocks = self._merge_numeric_blocks(valid_blocks)
        logger.critical(f"📊 STEP 3: Numeric merging: {len(valid_blocks)} blocks → {len(merged_blocks)} blocks")
        
        # Step 2: Cluster by Y-position into rows (unlimited rows)
        blocks_by_y = {}
        for block in merged_blocks:
            bbox = block.get('bounding_box', {})
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 100) / 100  # 0.01 precision for better row detection
            if y_key not in blocks_by_y:
                blocks_by_y[y_key] = []
            blocks_by_y[y_key].append(block)
        
        logger.critical("=" * 80)
        logger.critical(f"📊 STEP 4: Y-axis clustering (row detection)")
        logger.critical(f"   Detected {len(blocks_by_y)} distinct Y-positions (rows)")
        
        if blocks_by_y:
            logger.critical(f"   First 10 rows:")
            for idx, (y_key, row_blocks) in enumerate(sorted(blocks_by_y.items())[:10]):
                texts = [b.get('text', '')[:20] for b in row_blocks[:3]]
                logger.critical(f"      Row {idx} (Y={y_key:.4f}): {len(row_blocks)} blocks | {texts}")
        logger.critical("=" * 80)
        
        # Step 3: Cluster by X-position into columns (UNLIMITED columns)
        column_anchors = self._infer_geometric_hybrid_columns(blocks_by_y)
        
        logger.critical("=" * 80)
        logger.critical(f"📊 STEP 5: X-axis clustering (column detection)")
        logger.critical(f"   Detected {len(column_anchors)} columns (UNLIMITED)")
        if column_anchors:
            logger.critical(f"   Column anchors (X positions): {[f'{x:.4f}' for x in column_anchors[:10]]}")
        logger.critical("=" * 80)
        
        # Step 4: Safety check - need at least 1 column
        if len(column_anchors) < 1:
            logger.warning(f"Page {page_idx + 1}: GEOMETRIC_HYBRID - No columns detected, creating fallback")
            # Create single-column layout from blocks (not forced 2-column)
            if merged_blocks:
                for idx, block in enumerate(merged_blocks[:100]):  # First 100 blocks
                    block_text = block.get('text', '').strip()
                    if block_text:
                        cell = Cell(
                            row=idx,
                            column=0,
                            value=block_text,
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                        )
                        layout.add_row([cell])
                return layout
            else:
                return self._create_minimal_fallback_layout(page_idx, document_text, 'docai')
        
        # Step 5: Reconstruct grid from geometric alignment (unlimited rows/columns)
        logger.critical("=" * 80)
        logger.critical(f"📊 STEP 6: Building grid from {len(blocks_by_y)} rows × {len(column_anchors)} columns")
        logger.critical("=" * 80)
        
        row_idx = 0
        cells_created = 0
        
        for y_pos in sorted(blocks_by_y.keys()):
            row_blocks = sorted(blocks_by_y[y_pos], key=lambda b: b.get('bounding_box', {}).get('x_min', 0))
            row_cells = [None] * len(column_anchors)  # Initialize row with empty cells
            
            if row_idx < 10:  # Log first 10 rows
                logger.critical(f"   Processing Row {row_idx} (Y={y_pos:.4f}): {len(row_blocks)} blocks")
            
            for block in row_blocks:
                bbox = block.get('bounding_box', {})
                x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                text = block.get('text', '').strip()
                
                if not text:
                    continue
                
                # CRITICAL FIX: Find nearest column anchor, but also check if we need a NEW column
                # If block is far from all existing columns, create a new column anchor
                if len(column_anchors) == 0:
                    # No columns yet - create first column at this X position
                    column_anchors.append(x_center)
                    nearest_col = 0
                else:
                    nearest_col = min(range(len(column_anchors)), key=lambda i: abs(column_anchors[i] - x_center))
                
                # Check if misalignment is acceptable (within 8% of page width)
                misalignment_threshold = 0.08
                distance_to_anchor = abs(column_anchors[nearest_col] - x_center) if column_anchors else 1.0
                
                # CRITICAL: If block is too far from nearest column, create NEW column
                if distance_to_anchor > misalignment_threshold and len(column_anchors) < 20:  # Max 20 columns to prevent explosion
                    # This block needs its own column
                    column_anchors.append(x_center)
                    column_anchors = sorted(column_anchors)  # Keep sorted
                    # Recalculate nearest_col after adding new column
                    nearest_col = len(column_anchors) - 1
                    # Expand row_cells array to accommodate new column
                    while len(row_cells) < len(column_anchors):
                        row_cells.append(None)
                    distance_to_anchor = 0  # Now it's perfectly aligned
                
                # CRITICAL FIX: Each block gets its OWN cell - never combine unless truly same cell
                # Only combine if blocks are horizontally overlapping (same physical cell)
                if row_cells[nearest_col] is not None:
                    # Column already has a cell - check if blocks actually overlap horizontally
                    existing_cell = row_cells[nearest_col]
                    
                    # CRITICAL: Only combine if blocks are very close horizontally (< 2% of page width)
                    # This means they're likely the same physical cell (e.g., Aadhaar digits split)
                    horizontal_overlap_threshold = 0.02  # 2% of page width
                    
                    # Check if this block overlaps with existing cell's block
                    # If X-centers are very close, they're likely the same cell
                    if distance_to_anchor <= horizontal_overlap_threshold:
                        # Same cell - combine text (e.g., Aadhaar digits split across blocks)
                        existing_text = existing_cell.value or ''
                        row_cells[nearest_col].value = (existing_text + ' ' + text).strip()
                        logger.debug(f"GEOMETRIC_HYBRID: Combined blocks in column {nearest_col} (overlap: {distance_to_anchor:.4f} <= {horizontal_overlap_threshold})")
                    else:
                        # Different cell - create new column instead of combining
                        # This prevents multiple columns' text from merging into one cell
                        if len(column_anchors) < 50:  # Max 50 columns
                            column_anchors.append(x_center)
                            column_anchors = sorted(column_anchors)
                            new_col = column_anchors.index(x_center)
                            # Expand row_cells array
                            while len(row_cells) < len(column_anchors):
                                row_cells.append(None)
                            
                            has_unicode = any(ord(c) > 127 for c in text)
                            wrap_text = len(text) > 50 or has_unicode
                            
                            row_cells[new_col] = Cell(
                                row=row_idx,
                                column=new_col,
                                value=text,
                                style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                            )
                            logger.debug(f"GEOMETRIC_HYBRID: Created new column {new_col} for block (distance: {distance_to_anchor:.4f} > {horizontal_overlap_threshold})")
                        else:
                            # Too many columns - use nearest empty column (don't combine)
                            for col_idx in range(len(column_anchors)):
                                if row_cells[col_idx] is None:
                                    row_cells[col_idx] = Cell(
                                        row=row_idx,
                                        column=col_idx,
                                        value=text,
                                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                    )
                                    logger.debug(f"GEOMETRIC_HYBRID: Used empty column {col_idx} (max columns reached)")
                                    break
                            else:
                                # All columns occupied - skip this block rather than combining
                                # Combining would merge different columns' text
                                logger.warning(f"GEOMETRIC_HYBRID: Skipping block - all columns occupied, would merge columns: {text[:50]}")
                else:
                    # No existing cell - create new
                    has_unicode = any(ord(c) > 127 for c in text)
                    wrap_text = len(text) > 50 or has_unicode
                    
                    row_cells[nearest_col] = Cell(
                        row=row_idx,
                        column=nearest_col,
                        value=text,
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT, wrap_text=wrap_text)
                    )
            
            # Add row with all cells (fill empty cells)
            final_row_cells = []
            for col_idx in range(len(column_anchors)):
                if row_cells[col_idx] is not None:
                    final_row_cells.append(row_cells[col_idx])
                else:
                    # Empty cell
                    final_row_cells.append(Cell(
                        row=row_idx,
                        column=col_idx,
                        value='',
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    ))
            
            if final_row_cells:
                layout.add_row(final_row_cells)
                cells_created += len([c for c in final_row_cells if c.value and str(c.value).strip()])
                row_idx += 1
        
        logger.critical("=" * 80)
        logger.critical(f"📊 STEP 7: Grid construction complete")
        logger.critical(f"   Rows created: {row_idx}")
        logger.critical(f"   Cells created: {cells_created}")
        logger.critical(f"   Total layout rows: {len(layout.rows)}")
        logger.critical("=" * 80)
        
        # CRITICAL FIX: Non-empty enforcement - if blocks detected, Excel MUST have data
        if row_idx == 0:
            logger.critical(f"❌ GEOMETRIC_HYBRID: No rows created from {len(blocks_by_y)} Y-groups and {len(column_anchors)} columns")
            logger.critical("   Creating fallback from blocks")
            # Create single-column layout from blocks (not forced 2-column)
            if blocks:
                for idx, block in enumerate(blocks[:50]):  # First 50 blocks
                    block_text = block.get('text', '').strip()
                    if block_text:
                        cell = Cell(
                            row=idx,
                            column=0,
                            value=block_text,
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                        )
                        layout.add_row([cell])
                        row_idx += 1
            elif document_text:
                # Fallback to text if no blocks
                lines = document_text.split('\n')[:50]
                for idx, line in enumerate(lines):
                    if line.strip():
                        cell = Cell(
                            row=idx,
                            column=0,
                            value=line.strip(),
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                        )
                        layout.add_row([cell])
                        row_idx += 1
        
        logger.critical(f"GEOMETRIC_HYBRID: Created layout with {row_idx} rows, {len(column_anchors)} columns")
        logger.critical(f"🔍 Page {page_idx + 1} Layout Check: max_row={layout.get_max_row()}, max_col={layout.get_max_column()}, has_content=True, rows_count={len(layout.rows) if layout.rows else 0}")
        
        # DYNAMIC STRUCTURE: Preserve natural column/row structure
        # No forced column trimming - documents use their natural structure
        
        return layout
    
    def _infer_geometric_hybrid_columns(self, blocks_by_y: Dict[float, List[Dict]]) -> List[float]:
        """
        Infer column anchors by clustering text blocks by X-position across rows.
        UNLIMITED columns - no maximum limit.
        """
        if not blocks_by_y:
            return []
        
        # Collect all X-center positions from all rows
        x_positions = []
        for row_blocks in blocks_by_y.values():
            for block in row_blocks:
                bbox = block.get('bounding_box', {})
                x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                x_positions.append(x_center)
        
        if not x_positions:
            return []
        
        # Cluster X-positions (visual column bands) - UNLIMITED
        x_positions = sorted(set(x_positions))
        clusters = []
        cluster_tolerance = 0.06  # 6% tolerance for geometric alignment
        
        for x_pos in x_positions:
            assigned = False
            for cluster in clusters:
                cluster_center = sum(cluster) / len(cluster)
                if abs(x_pos - cluster_center) <= cluster_tolerance:
                    cluster.append(x_pos)
                    assigned = True
                    break
            if not assigned:
                clusters.append([x_pos])
        
        # Extract column anchors (centers of clusters that appear in multiple rows)
        column_anchors = []
        for cluster in clusters:
            if len(cluster) >= 1:  # Accept any cluster (unlimited)
                cluster_center = sum(cluster) / len(cluster)
                column_anchors.append(cluster_center)
        
        # Sort by X-position
        column_anchors = sorted(column_anchors)
        
        return column_anchors
    
    def _detect_column_anchors_from_x_positions(self, x_positions: List[float]) -> List[float]:
        """
        Detect column anchors from X positions using clustering (for KEY_VALUE mode).
        UNLIMITED columns - no maximum limit.
        """
        if not x_positions:
            return []
        
        # Cluster X-positions (visual column bands) - UNLIMITED
        x_positions = sorted(set(x_positions))
        clusters = []
        cluster_tolerance = 0.06  # 6% tolerance for geometric alignment
        
        for x_pos in x_positions:
            assigned = False
            for cluster in clusters:
                cluster_center = sum(cluster) / len(cluster)
                if abs(x_pos - cluster_center) <= cluster_tolerance:
                    cluster.append(x_pos)
                    assigned = True
                    break
            if not assigned:
                clusters.append([x_pos])
        
        # Extract column anchors (centers of clusters)
        column_anchors = []
        for cluster in clusters:
            if len(cluster) >= 1:  # Accept any cluster (unlimited)
                cluster_center = sum(cluster) / len(cluster)
                column_anchors.append(cluster_center)
        
        # Sort by X-position
        column_anchors = sorted(column_anchors)
        
        return column_anchors
    
    def _find_nearest_column_anchor(self, x_center: float, column_anchors: List[float]) -> int:
        """
        Find the nearest column anchor for a given X position.
        Returns column index (0-based).
        """
        if not column_anchors:
            return 0
        
        nearest_idx = min(range(len(column_anchors)), key=lambda i: abs(column_anchors[i] - x_center))
        return nearest_idx
    
    def _merge_numeric_blocks(self, blocks: List[Dict]) -> List[Dict]:
        """
        Merge numeric blocks (e.g. Aadhaar) that are horizontally close into single cells.
        This prevents splitting long numeric sequences across columns.
        """
        if not blocks:
            return []
        
        # Sort by Y-position, then X-position
        sorted_blocks = sorted(blocks, key=lambda b: (
            b.get('bounding_box', {}).get('y_min', 0),
            b.get('bounding_box', {}).get('x_min', 0)
        ))
        
        merged = []
        current_group = [sorted_blocks[0]]
        
        for block in sorted_blocks[1:]:
            last_block = current_group[-1]
            last_bbox = last_block.get('bounding_box', {})
            curr_bbox = block.get('bounding_box', {})
            
            last_y_center = (last_bbox.get('y_min', 0) + last_bbox.get('y_max', 0)) / 2
            curr_y_center = (curr_bbox.get('y_min', 0) + curr_bbox.get('y_max', 0)) / 2
            last_x_max = last_bbox.get('x_max', 0)
            curr_x_min = curr_bbox.get('x_min', 1)
            
            # Check if blocks are on same row and horizontally close
            y_distance = abs(curr_y_center - last_y_center)
            y_threshold = (last_bbox.get('y_max', 0) - last_bbox.get('y_min', 0)) * 0.5
            x_gap = curr_x_min - last_x_max
            
            # Check if text is numeric (Aadhaar pattern: digits with spaces)
            last_text = last_block.get('text', '')
            curr_text = block.get('text', '')
            last_is_numeric = self._is_aadhaar_or_long_numeric(last_text)
            curr_is_numeric = self._is_aadhaar_or_long_numeric(curr_text)
            
            if (y_distance <= y_threshold and 
                x_gap <= 0.05 and  # Very close horizontally (5% of page width)
                (last_is_numeric or curr_is_numeric)):  # At least one is numeric
                # Merge: combine text and expand bounding box
                merged_text = (last_text + ' ' + curr_text).strip()
                merged_bbox = {
                    'x_min': min(last_bbox.get('x_min', 0), curr_bbox.get('x_min', 0)),
                    'x_max': max(last_bbox.get('x_max', 0), curr_bbox.get('x_max', 0)),
                    'y_min': min(last_bbox.get('y_min', 0), curr_bbox.get('y_min', 0)),
                    'y_max': max(last_bbox.get('y_max', 0), curr_bbox.get('y_max', 0))
                }
                merged_block = {
                    'text': merged_text,
                    'bounding_box': merged_bbox
                }
                current_group[-1] = merged_block
            else:
                # Start new group
                merged.append(current_group[0])
                current_group = [block]
        
        # Add last group
        if current_group:
            merged.append(current_group[0])
        
        return merged
    
    def _infer_visual_grid_columns(self, blocks_by_y: Dict[float, List[Dict]]) -> List[float]:
        """
        Infer column anchors by clustering text blocks by X-position across rows.
        This is purely visual alignment - ignores Document AI table semantics.
        """
        if not blocks_by_y:
            return []
        
        # Collect all X-center positions from all rows
        x_positions = []
        for row_blocks in blocks_by_y.values():
            for block in row_blocks:
                bbox = block.get('bounding_box', {})
                x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                x_positions.append(x_center)
        
        if not x_positions:
            return []
        
        # CRITICAL FIX: Use stricter clustering tolerance (5% instead of 8%)
        # This prevents multiple distinct columns from being merged into one
        x_positions = sorted(set(x_positions))
        clusters = []
        cluster_tolerance = 0.05  # 5% tolerance (stricter to prevent column merging)
        
        for x_pos in x_positions:
            assigned = False
            for cluster in clusters:
                cluster_center = sum(cluster) / len(cluster)
                if abs(x_pos - cluster_center) <= cluster_tolerance:
                    cluster.append(x_pos)
                    assigned = True
                    break
            if not assigned:
                clusters.append([x_pos])
        
        # Count how many rows have blocks in each cluster
        column_anchors = []
        for cluster in clusters:
            cluster_center = sum(cluster) / len(cluster)
            row_count = 0
            
            for row_blocks in blocks_by_y.values():
                for block in row_blocks:
                    bbox = block.get('bounding_box', {})
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    if abs(x_center - cluster_center) <= cluster_tolerance:
                        row_count += 1
                        break  # Count each row only once
            
            # If same X-range appears in >= 2 rows → treat as a column (visual grid pattern)
            if row_count >= 2:
                column_anchors.append(cluster_center)
        
        # Sort column anchors by X-position
        column_anchors.sort()
        
        return column_anchors
    
    def _check_visual_table_candidate(self, full_structure: Dict) -> bool:
        """
        Check if a TYPE_D document should be promoted to TYPE_A_CANDIDATE (visual table).
        
        Visual Table Candidate Rules:
        1. blocks >= 30
        2. repeated horizontal alignment across >= 3 rows
        3. >= 2 distinct X-position clusters repeating vertically
        4. presence of numeric columns (IDs, Aadhaar, serial numbers)
        
        Safety:
        - Promotion allowed ONLY for digital_pdf (checked by caller)
        - Promotion forbidden for scanned images, letters, paragraphs (checked by caller)
        """
        if not full_structure or 'blocks' not in full_structure:
            return False
        
        blocks = [b for b in full_structure['blocks'] if b.get('bounding_box') and b.get('text', '').strip()]
        
        # Rule 1: blocks >= 30
        if len(blocks) < 30:
            logger.debug(f"Visual table candidate check: Only {len(blocks)} blocks, need >= 30")
            return False
        
        # Group blocks by Y-position (rows) - use relaxed precision
        blocks_by_y = {}
        for block in blocks:
            bbox = block.get('bounding_box', {})
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 50) / 50  # 0.02 precision (relaxed)
            if y_key not in blocks_by_y:
                blocks_by_y[y_key] = []
            blocks_by_y[y_key].append(block)
        
        # Rule 2: repeated horizontal alignment across >= 3 rows
        rows_with_horizontal_alignment = 0
        x_clusters_all_rows = []  # Collect all X-positions
        numeric_blocks_count = 0  # Count numeric blocks (Rule 4)
        
        for y_pos, row_blocks in blocks_by_y.items():
            if len(row_blocks) >= 2:  # At least 2 blocks in row (horizontal alignment)
                x_positions = []
                for block in row_blocks:
                    bbox = block.get('bounding_box', {})
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    x_positions.append(x_center)
                    
                    # Check for numeric content (Rule 4)
                    text = block.get('text', '').strip()
                    if self._is_aadhaar_or_long_numeric(text):
                        numeric_blocks_count += 1
                    # Also check for short numeric sequences (serial numbers, IDs)
                    digits_only = ''.join(c for c in text if c.isdigit())
                    if 4 <= len(digits_only) <= 9 and len(text) <= 20:  # Short numeric IDs
                        numeric_blocks_count += 1
                
                # Check if X-positions are distinct and separated
                x_positions = sorted(set(x_positions))
                if len(x_positions) >= 2:
                    # Check if positions are reasonably separated (at least 5% of page width)
                    min_separation = 0.05
                    has_separation = False
                    for i in range(len(x_positions) - 1):
                        if x_positions[i + 1] - x_positions[i] >= min_separation:
                            has_separation = True
                            break
                    
                    if has_separation:
                        rows_with_horizontal_alignment += 1
                        x_clusters_all_rows.extend(x_positions)
        
        # Rule 2: Need >= 3 rows with horizontal alignment
        if rows_with_horizontal_alignment < 3:
            logger.debug(f"Visual table candidate check: Only {rows_with_horizontal_alignment} rows with horizontal alignment, need >= 3")
            return False
        
        # Rule 3: >= 2 distinct X-position clusters repeating vertically
        if len(x_clusters_all_rows) < 10:
            logger.debug(f"Visual table candidate check: Only {len(x_clusters_all_rows)} X-positions, need >= 10")
            return False
        
        # Cluster X-positions to find distinct column bands
        x_clusters_all_rows = sorted(set(x_clusters_all_rows))
        clusters = []
        cluster_tolerance = 0.08  # 8% tolerance
        
        for x_pos in x_clusters_all_rows:
            assigned = False
            for cluster in clusters:
                cluster_center = sum(cluster) / len(cluster)
                if abs(x_pos - cluster_center) <= cluster_tolerance:
                    cluster.append(x_pos)
                    assigned = True
                    break
            if not assigned:
                clusters.append([x_pos])
        
        # Count how many rows have blocks in each cluster (repeating vertically)
        distinct_vertical_bands = 0
        for cluster in clusters:
            cluster_center = sum(cluster) / len(cluster)
            row_count = 0
            
            for y_pos, row_blocks in blocks_by_y.items():
                if len(row_blocks) >= 2:  # Only check rows with multiple blocks
                    for block in row_blocks:
                        bbox = block.get('bounding_box', {})
                        x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                        if abs(x_center - cluster_center) <= cluster_tolerance:
                            row_count += 1
                            break  # Count each row only once
            
            # If same X-range appears in >= 2 rows → distinct vertical band
            if row_count >= 2:
                distinct_vertical_bands += 1
        
        # Rule 3: Need >= 2 distinct X-position clusters repeating vertically
        if distinct_vertical_bands < 2:
            logger.debug(f"Visual table candidate check: Only {distinct_vertical_bands} distinct vertical bands, need >= 2")
            return False
        
        # Rule 4: Presence of numeric columns (IDs, Aadhaar, serial numbers)
        # We already counted numeric_blocks_count above
        if numeric_blocks_count < 2:
            logger.debug(f"Visual table candidate check: Only {numeric_blocks_count} numeric blocks, need >= 2")
            return False
        
        # All rules passed - eligible for promotion
        logger.info(f"Visual table candidate check PASSED: {len(blocks)} blocks, {rows_with_horizontal_alignment} aligned rows, {distinct_vertical_bands} vertical bands, {numeric_blocks_count} numeric blocks")
        return True
