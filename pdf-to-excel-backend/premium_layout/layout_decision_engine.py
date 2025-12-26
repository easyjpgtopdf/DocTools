"""
Layout Decision Engine
Decides whether to use native Document AI tables or heuristic inference.
"""

import logging
from typing import Optional, List, Any, Dict, Tuple
from enum import Enum

from .unified_layout_model import UnifiedLayout, Cell, CellStyle, CellAlignment
from .document_type_classifier import DocumentTypeClassifier, DocumentType
from .heuristic_table_builder import HeuristicTableBuilder
from .full_ocr_extractor import FullOCRExtractor

logger = logging.getLogger(__name__)

class PremiumDocCategory(Enum):
    TYPE_A_TRUE_TABULAR = "true_tabular"
    TYPE_B_KEY_VALUE = "key_value"
    TYPE_C_MIXED_LAYOUT = "mixed_layout"
    TYPE_D_PLAIN_TEXT = "plain_text"


class LayoutDecisionEngine:
    """Makes decisions about layout extraction strategy"""
    
    def __init__(self):
        """Initialize decision engine"""
        self.classifier = DocumentTypeClassifier()
        self.heuristic_builder = HeuristicTableBuilder()
        self.full_ocr_extractor = FullOCRExtractor(min_confidence=0.5)  # Use full OCR capabilities
        self.document_category: Optional["PremiumDocCategory"] = None  # premium-only classification
        self.table_confidence: float = 0.0  # premium-only confidence for TYPE_A tables
    
    def process_document(
        self,
        document: Any,
        document_text: str = '',
        native_tables: Optional[List] = None
    ) -> List[UnifiedLayout]:
        """
        Process document and return unified layouts (one per page).
        
        Args:
            document: Document AI Document object
            document_text: Extracted text
            native_tables: List of native tables from Document AI (if any)
            
        Returns:
            List of UnifiedLayout objects (one per page)
        """
        # Step 1: Extract full OCR structure (use Document AI's complete capabilities)
        logger.info("Extracting full OCR structure using Document AI's complete capabilities...")
        full_structure = self.full_ocr_extractor.extract_full_structure(document)
        logger.info(f"Extracted: {len(full_structure['blocks'])} blocks, "
                   f"{len(full_structure['form_fields'])} form fields, "
                   f"{len(full_structure['tables'])} tables, "
                   f"avg confidence: {full_structure['avg_confidence']:.2f}")
        
        # Step 2: Classify document type (CRITICAL: Before any table processing)
        doc_type = self.classifier.classify(document, document_text)
        logger.info(f"Document classified as: {doc_type.value}")

        # Step 2.0: Premium document category (before any table/row/col/Excel logic)
        self.document_category = self._classify_premium_category(full_structure, doc_type)
        logger.info(f"Premium document category: {self.document_category.value}")
        
        # CRITICAL: SECOND-PASS EVALUATION - TYPE_D → TYPE_A promotion for visual tables
        self.is_promoted_from_type_d = False
        if self.document_category == PremiumDocCategory.TYPE_D_PLAIN_TEXT:
            # Check if document is digital_pdf (not scanned image)
            if doc_type == DocumentType.DIGITAL_PDF:
                # Perform VISUAL TABLE CANDIDATE CHECK
                visual_table_eligible = self._check_visual_table_candidate(full_structure)
                if visual_table_eligible:
                    # Reclassify as TYPE_A (promoted from TYPE_D)
                    logger.info("CRITICAL: TYPE_D promoted to TYPE_A_CANDIDATE (visual table detected)")
                    self.document_category = PremiumDocCategory.TYPE_A_TRUE_TABULAR
                    self.is_promoted_from_type_d = True
                    logger.info("TYPE_D → TYPE_A promotion: Document will use SOFT TABLE MODE + VISUAL GRID RECONSTRUCTION without requiring native tables")
        
        # Reset table confidence per document
        self.table_confidence = 0.0
        
        # Step 2.1: Check if document type allows table processing
        # Form-style documents (key:value) should NOT force Excel table structure
        # Resume/text documents should use simple row-wise export
        allows_table_processing = self._allows_table_processing(doc_type, document, document_text)
        logger.info(f"Table processing allowed: {allows_table_processing}")
        
        # Step 3: Process per page using full structure
        page_layouts = []
        
        if not hasattr(document, 'pages') or not document.pages:
            logger.warning("No pages found in document")
            return [UnifiedLayout(page_index=0)]
        
        # Group native tables by page
        tables_by_page = {}
        if native_tables:
            # Document AI tables have page reference
            for table in native_tables:
                page_idx = 0
                if hasattr(table, 'layout') and hasattr(table.layout, 'bounding_poly'):
                    # Try to determine page from bounding box
                    # For now, we'll process all tables together and split by page later
                    pass
                tables_by_page.setdefault(page_idx, []).append(table)
        
        # Process each page using full structure
        for page_idx, page in enumerate(document.pages):
            logger.info(f"Processing page {page_idx + 1} of {len(document.pages)}")
            
            # Get page structure from full OCR extraction
            page_structure = None
            if page_idx < len(full_structure['pages']):
                page_structure = full_structure['pages'][page_idx]
            
            # Get tables for this page (from full structure or native tables)
            page_tables = []
            if page_structure and 'tables' in page_structure:
                # Use enhanced tables from full OCR extraction
                page_tables = page_structure['tables']
            elif native_tables:
                # Fallback to native tables
                if page_idx == 0:
                    page_tables = native_tables[:len(native_tables) // len(document.pages) + 1]
                else:
                    start_idx = (page_idx * len(native_tables)) // len(document.pages)
                    end_idx = ((page_idx + 1) * len(native_tables)) // len(document.pages)
                    page_tables = native_tables[start_idx:end_idx]
            
            # Check if native tables exist for this page
            has_native_tables = len(page_tables) > 0
            
            # Check for form fields (use Document AI's form parser)
            has_form_fields = False
            form_fields_list = []
            if page_structure and 'form_fields' in page_structure and page_structure['form_fields']:
                has_form_fields = True
                form_fields_list = page_structure['form_fields']
                logger.info(f"Page {page_idx + 1}: Found {len(form_fields_list)} form fields")
            
            # Check for blocks with bounding boxes
            has_blocks = False
            blocks_list = []
            if page_structure and 'blocks' in page_structure and page_structure['blocks']:
                blocks_with_bbox = [b for b in page_structure['blocks'] if b.get('bounding_box')]
                if blocks_with_bbox:
                    has_blocks = True
                    blocks_list = blocks_with_bbox
                    logger.info(f"Page {page_idx + 1}: Found {len(blocks_list)} blocks with bounding boxes")
            
            # Layout strategy decision (NEVER fallback to text-only)
            layout_strategy = "unknown"
            category = "unknown"
            page_table_confidence = 0.0

            # Pre-table decision layer (premium only)
            category_str, page_table_confidence = self._determine_layout_category(
                doc_type=doc_type,
                page_tables=page_tables,
                page_structure=page_structure,
                has_form_fields=has_form_fields,
                has_blocks=has_blocks
            )
            
            # Use document-level category (PremiumDocCategory enum) for routing
            # This ensures consistent routing across all pages based on document classification
            category = self.document_category  # This is PremiumDocCategory enum from _classify_premium_category
            
            # For TYPE_A, compute advanced table confidence
            if category == PremiumDocCategory.TYPE_A_TRUE_TABULAR and page_tables:
                page_table_confidence = self._compute_table_confidence_signals(page_tables)
            logger.info(f"Page {page_idx + 1}: Document category={category.value}, page category={category_str}, table_confidence={page_table_confidence:.2f}")
            self.table_confidence = page_table_confidence
            
            # DECISION ROUTING: Route by category FIRST (not by data availability)
            try:
                if category == PremiumDocCategory.TYPE_A_TRUE_TABULAR:
                    # TYPE_A: TRUE_TABULAR - Only proceed if table_confidence >= 0.65
                    layout_strategy = "type_a_tabular"
                    
                    # CRITICAL: If promoted from TYPE_D, allow SOFT TABLE MODE + VISUAL GRID without native tables
                    if self.is_promoted_from_type_d:
                        logger.info(f"Page {page_idx + 1}: TYPE_A (promoted from TYPE_D) - Allowing SOFT TABLE MODE + VISUAL GRID RECONSTRUCTION without native tables")
                        # Skip native table requirement, go directly to SOFT TABLE MODE check
                        has_native_tables = False  # Force SOFT TABLE MODE path
                    
                    if has_native_tables and allows_table_processing:
                        is_native_docai_table = (
                            page_tables and 
                            hasattr(page_tables[0], 'header_rows') or hasattr(page_tables[0], 'body_rows')
                        )
                        
                        if is_native_docai_table and page_table_confidence >= 0.65:
                            logger.info(f"Page {page_idx + 1}: TYPE_A - Using premium 7-step table pipeline (confidence: {page_table_confidence:.2f})")
                            page_layout = self._convert_native_tables_to_layout(
                                page_tables, 
                                document_text, 
                                page_idx,
                                page=page,
                                doc_type=doc_type,
                                table_confidence=page_table_confidence
                            )
                            page_layout.metadata['table_confidence'] = page_table_confidence
                            page_layout = self._final_cleanup_and_normalize(
                                page_layout,
                                category=category,
                                table_confidence=page_table_confidence
                            )
                        else:
                            # SOFT TABLE MODE: TYPE_A with low confidence but visible body rows >= 3
                            # NEW TRIGGER: Check body rows (NOT headers) for multi-column pattern
                            body_rows_count, distinct_x_clusters = self._check_body_rows_for_soft_mode(page_structure, document_text)
                            
                            if body_rows_count >= 3 and distinct_x_clusters >= 2:
                                # SOFT TABLE MODE: Infer columns using text alignment from BODY rows ONLY, ignore header completely
                                logger.info(f"Page {page_idx + 1}: TYPE_A - Table confidence {page_table_confidence:.2f} < 0.65, but {body_rows_count} body rows with {distinct_x_clusters} X-clusters detected. Using SOFT TABLE MODE")
                                page_layout = self._convert_to_soft_table_mode(
                                    page_tables=page_tables,
                                    document_text=document_text,
                                    page_idx=page_idx,
                                    page_structure=page_structure,
                                    page=page
                                )
                                page_layout.metadata['body_rows_count'] = body_rows_count
                                page_layout.metadata['distinct_x_clusters'] = distinct_x_clusters
                                page_layout.metadata['table_confidence_status'] = 'SOFT_TABLE_MODE'
                                page_layout.metadata['table_confidence'] = page_table_confidence
                                page_layout.metadata['user_message'] = 'Multi-column table detected with weak headers - using soft column inference from body rows'
                            elif body_rows_count >= 2 and distinct_x_clusters >= 2:
                                # RELAXED TRIGGER: Even with 2 body rows, if we have distinct X-clusters, try SOFT TABLE MODE
                                logger.info(f"Page {page_idx + 1}: TYPE_A - Table confidence {page_table_confidence:.2f} < 0.65, but {body_rows_count} body rows with {distinct_x_clusters} X-clusters detected (relaxed trigger). Using SOFT TABLE MODE")
                                page_layout = self._convert_to_soft_table_mode(
                                    page_tables=page_tables,
                                    document_text=document_text,
                                    page_idx=page_idx,
                                    page_structure=page_structure,
                                    page=page
                                )
                                page_layout.metadata['body_rows_count'] = body_rows_count
                                page_layout.metadata['distinct_x_clusters'] = distinct_x_clusters
                                page_layout.metadata['table_confidence_status'] = 'SOFT_TABLE_MODE_RELAXED'
                                page_layout.metadata['table_confidence'] = page_table_confidence
                                page_layout.metadata['user_message'] = 'Multi-column table detected with weak headers - using soft column inference from body rows (relaxed trigger)'
                            else:
                                # Log why SOFT TABLE MODE didn't trigger
                                logger.warning(f"Page {page_idx + 1}: TYPE_A - Table confidence {page_table_confidence:.2f} < 0.65, but SOFT TABLE MODE not triggered. body_rows={body_rows_count}, distinct_x_clusters={distinct_x_clusters}")
                                
                                # OPTIONAL VISUAL GRID RECONSTRUCTION MODE (fallback when all else fails)
                                # Trigger: no native tables AND stable X-position bands across >= 5 rows
                                if not has_native_tables:
                                    visual_grid_eligible, stable_rows = self._check_visual_grid_reconstruction_trigger(page_structure, document_text)
                                    if visual_grid_eligible and stable_rows >= 5:
                                        logger.info(f"Page {page_idx + 1}: TYPE_A - OPTIONAL VISUAL GRID RECONSTRUCTION MODE triggered ({stable_rows} stable rows with X-position bands)")
                                        page_layout = self._convert_to_visual_grid_reconstruction_mode(
                                            page_tables=page_tables,
                                            document_text=document_text,
                                            page_idx=page_idx,
                                            page_structure=page_structure,
                                            page=page
                                        )
                                        page_layout.metadata['table_confidence_status'] = 'VISUAL_GRID_RECONSTRUCTION'
                                        page_layout.metadata['table_confidence'] = page_table_confidence
                                        page_layout.metadata['stable_rows_count'] = stable_rows
                                        page_layout.metadata['user_message'] = 'Visual grid reconstruction mode - reconstructed from text block alignment'
                                    else:
                                        # Visual grid reconstruction not eligible, fall back to template headers
                                        logger.warning(f"Page {page_idx + 1}: TYPE_A - Visual grid reconstruction not eligible (eligible={visual_grid_eligible}, stable_rows={stable_rows})")
                                        # USER-VISIBLE BEHAVIOR: TYPE_A with low confidence = "Template/Incomplete Table"
                                        # Output minimal Excel (headers only), do NOT attempt full reconstruction
                                        logger.warning(f"Page {page_idx + 1}: TYPE_A - Table confidence {page_table_confidence:.2f} < 0.65, treating as Template/Incomplete Table (headers only)")
                                        page_layout = self._convert_to_template_headers_only(page_tables, document_text, page_idx)
                                        page_layout.metadata['table_confidence_status'] = 'TEMPLATE_INCOMPLETE_TABLE'
                                        page_layout.metadata['table_confidence'] = page_table_confidence
                                        page_layout.metadata['user_message'] = 'Template or incomplete table detected - showing headers only'
                                else:
                                    # Native tables exist, so visual grid reconstruction not applicable
                                    # USER-VISIBLE BEHAVIOR: TYPE_A with low confidence = "Template/Incomplete Table"
                                    # Output minimal Excel (headers only), do NOT attempt full reconstruction
                                    logger.warning(f"Page {page_idx + 1}: TYPE_A - Table confidence {page_table_confidence:.2f} < 0.65, treating as Template/Incomplete Table (headers only)")
                                    page_layout = self._convert_to_template_headers_only(page_tables, document_text, page_idx)
                                    page_layout.metadata['table_confidence_status'] = 'TEMPLATE_INCOMPLETE_TABLE'
                                    page_layout.metadata['table_confidence'] = page_table_confidence
                                    page_layout.metadata['user_message'] = 'Template or incomplete table detected - showing headers only'
                    else:
                        # No tables or not allowed - treat as template/blank
                        logger.warning(f"Page {page_idx + 1}: TYPE_A - No tables or table processing not allowed, treating as template/blank")
                        if page_tables:
                            page_layout = self._convert_to_template_headers_only(page_tables, document_text, page_idx)
                            page_layout.metadata['table_confidence_status'] = 'NO_TABLE_PROCESSING'
                        else:
                            # Blank document - return minimal valid Excel
                            page_layout = self._create_minimal_structured_layout(page, document_text, page_idx)
                            page_layout.metadata['document_type'] = 'blank_template'
                            page_layout.metadata['user_message'] = 'Blank or template document - minimal structure returned'
                
                elif category == PremiumDocCategory.TYPE_B_KEY_VALUE:
                    # TYPE_B: KEY_VALUE - Dedicated 2-column layout, NEVER send through table pipeline
                    layout_strategy = "type_b_key_value"
                    logger.info(f"Page {page_idx + 1}: TYPE_B - Using dedicated key-value layout (2 columns: Label | Value)")
                    
                    # Check if blank/template document
                    if self._is_blank_or_template(document_text, form_fields_list, page_structure):
                        logger.info(f"Page {page_idx + 1}: TYPE_B - Blank/template detected, returning minimal valid Excel")
                        page_layout = self._create_minimal_structured_layout(page, document_text, page_idx)
                        page_layout.metadata['document_type'] = 'blank_template'
                        page_layout.metadata['user_message'] = 'Blank or template document - minimal structure returned'
                    else:
                        page_layout = self._convert_to_key_value_layout(
                            page=page,
                            document_text=document_text,
                            page_idx=page_idx,
                            form_fields=form_fields_list,
                            page_structure=page_structure,
                            page_tables=page_tables  # Line-item tables as separate sheet
                        )
                
                elif category == PremiumDocCategory.TYPE_C_MIXED_LAYOUT:
                    # TYPE_C: MIXED_LAYOUT - Do NOT fail, export page-wise blocks or controlled output
                    layout_strategy = "type_c_mixed_layout"
                    logger.info(f"Page {page_idx + 1}: TYPE_C - Exporting page-wise text blocks (no forced table)")
                    if has_blocks:
                        page_layout = self._build_layout_from_blocks(blocks_list, doc_type.value, page_idx, force_sequential=True)
                    elif has_form_fields:
                        page_layout = self._convert_form_fields_to_layout(form_fields_list, page_idx)
                    else:
                        # Controlled output - page-wise text blocks
                        page_layout = self._build_layout_from_full_ocr(page_structure, page, document_text, doc_type.value, page_idx)
                    # Ensure it doesn't look like a failed table
                    page_layout.metadata['layout_type'] = 'mixed_layout_export'
                
                elif category == PremiumDocCategory.TYPE_D_PLAIN_TEXT:
                    # TYPE_D: PLAIN_TEXT - Single-column Excel
                    layout_strategy = "type_d_plain_text"
                    logger.info(f"Page {page_idx + 1}: TYPE_D - Using single-column plain text layout")
                    
                    # Check if blank/template document
                    if self._is_blank_or_template(document_text, form_fields_list, page_structure):
                        logger.info(f"Page {page_idx + 1}: TYPE_D - Blank/template detected, returning minimal valid Excel")
                        page_layout = self._create_minimal_structured_layout(page, document_text, page_idx)
                        page_layout.metadata['document_type'] = 'blank_template'
                        page_layout.metadata['user_message'] = 'Blank or template document - minimal structure returned'
                    else:
                        page_layout = self._convert_to_plain_text_layout(
                            page=page,
                            document_text=document_text,
                            page_idx=page_idx,
                            page_structure=page_structure
                        )
                
                else:
                    # Unknown category - fail-safe: use minimal structured layout
                    logger.warning(f"Page {page_idx + 1}: Unknown category, using fail-safe minimal layout")
                    layout_strategy = "fail_safe_minimal"
                    page_layout = self._create_minimal_structured_layout(page, document_text, page_idx)
            
            except Exception as routing_error:
                # FAIL-SAFE RULE: No document type should cause API failure
                logger.error(f"Page {page_idx + 1}: Routing error for category {category}: {routing_error}")
                logger.info(f"Page {page_idx + 1}: Applying fail-safe: minimal valid Excel")
                layout_strategy = "fail_safe_error_recovery"
                page_layout = self._create_minimal_structured_layout(page, document_text, page_idx)
                page_layout.metadata['error_recovered'] = True
                page_layout.metadata['error_message'] = str(routing_error)
            
            # FAIL-SAFE: Ensure layout is never empty (always return valid Excel)
            if page_layout.is_empty():
                logger.warning(f"Page {page_idx + 1}: Layout is empty after {layout_strategy}, applying fail-safe")
                page_layout = self._create_minimal_structured_layout(page, document_text, page_idx)
                layout_strategy = f"{layout_strategy}_fail_safe"
            
            logger.info(f"Page {page_idx + 1}: Final layout - {page_layout.get_max_row()} rows, {page_layout.get_max_column()} columns, strategy: {layout_strategy}")
            page_layouts.append(page_layout)
        
        logger.info(f"Processed {len(page_layouts)} pages")
        return page_layouts
    
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

    def _classify_premium_category(self, full_structure: Dict, doc_type: DocumentType) -> PremiumDocCategory:
        """
        Classify document into premium categories:
        TYPE_A: TRUE_TABULAR
        TYPE_B: KEY_VALUE
        TYPE_C: MIXED_LAYOUT
        TYPE_D: PLAIN_TEXT
        """
        tables = full_structure.get("tables", []) if full_structure else []
        blocks = full_structure.get("blocks", []) if full_structure else []
        form_fields = full_structure.get("form_fields", []) if full_structure else []

        # Helper to estimate columns from table object
        def table_cols(t):
            cols = 0
            if hasattr(t, "header_rows") and t.header_rows:
                cols = max(cols, len(t.header_rows[0].cells) if hasattr(t.header_rows[0], "cells") else 0)
            if hasattr(t, "body_rows") and t.body_rows:
                cols = max(cols, len(t.body_rows[0].cells) if hasattr(t.body_rows[0], "cells") else 0)
            return cols

        # Compute table confidence
        table_conf = self._compute_table_confidence_from_tables(tables)
        max_cols = max([table_cols(t) for t in tables], default=0)
        total_tables = len(tables)

        # TYPE_A TRUE_TABULAR
        if total_tables >= 1 and max_cols >= 3:
            return PremiumDocCategory.TYPE_A_TRUE_TABULAR

        # TYPE_B KEY_VALUE (bills/receipts/invoices, 2-column logical)
        if form_fields or max_cols == 2 or doc_type in [DocumentType.BILL, DocumentType.INVOICE, DocumentType.BANK_STATEMENT]:
            return PremiumDocCategory.TYPE_B_KEY_VALUE

        # TYPE_C MIXED_LAYOUT (tables + paragraphs/forms mixed)
        if total_tables >= 1 and blocks:
            return PremiumDocCategory.TYPE_C_MIXED_LAYOUT
        if blocks and form_fields:
            return PremiumDocCategory.TYPE_C_MIXED_LAYOUT

        # TYPE_D PLAIN_TEXT default
        return PremiumDocCategory.TYPE_D_PLAIN_TEXT
    
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
        from .table_post_processor import TablePostProcessor
        
        # Use premium post-processing layer
        post_processor = TablePostProcessor()
        
        # Process each table with post-processing (page isolation)
        all_processed_tables = []
        
        for table_idx, table in enumerate(native_tables):
            logger.info(f"Processing table {table_idx + 1} with premium post-processing (page {page_index + 1})...")
            
            # CRITICAL: Apply 7-step premium pipeline with document type and confidence
            # Ensure document_type and table_confidence are propagated
            logger.info(f"Calling TablePostProcessor.process_table() with:")
            logger.info(f"  - doc_type: {self.document_category.value if self.document_category else None}")
            logger.info(f"  - table_confidence: {table_confidence}")
            
            processed_table = post_processor.process_table(
                table=table,
                document_text=document_text,
                page=page,
                # CRITICAL: Pass premium category for gating decisions
                doc_type=self.document_category.value if self.document_category else None,
                # CRITICAL: Pass precomputed table confidence for threshold checks
                table_confidence=table_confidence
            )
            
            logger.info(f"TablePostProcessor.process_table() returned ProcessedTable with {len(processed_table.rows)} rows")
            
            if processed_table.rows:
                all_processed_tables.append(processed_table)
        
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
            logger.info(f"UnifiedLayout created: {table_layout.get_max_row()} rows, {table_layout.get_max_column()} columns")
            
            # Add rows with offset
            for row_cells in table_layout.rows:
                # Adjust row indices
                adjusted_cells = []
                for cell in row_cells:
                    adjusted_cell = Cell(
                        row=row_offset,
                        column=cell.column,
                        value=cell.value,
                        style=cell.style,
                        rowspan=cell.rowspan,
                        colspan=cell.colspan,
                        merged=cell.merged
                    )
                    adjusted_cells.append(adjusted_cell)
                    
                    # Adjust merged cell ranges
                    if cell.rowspan > 1 or cell.colspan > 1:
                        end_row = row_offset + cell.rowspan - 1
                        end_col = cell.column + cell.colspan - 1
                        combined_layout.add_merged_cell(
                            start_row=row_offset,
                            start_col=cell.column,
                            end_row=end_row,
                            end_col=end_col
                        )
                
                if adjusted_cells:
                    combined_layout.add_row(adjusted_cells)
                    row_offset += 1
            
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
    
    def _final_cleanup_and_normalize(
        self,
        layout: UnifiedLayout,
        category: PremiumDocCategory,
        table_confidence: float
    ) -> UnifiedLayout:
        """
        Final cleanup and normalization for premium PDF-to-Excel.
        
        Only executes if:
        - document_type == TYPE_A (TRUE_TABULAR)
        - table_confidence >= 0.65
        - HEADER_NOT_FOUND is false
        - SPAN_CONFLICT is false
        """
        # Scope protection: Only run for TYPE_A with proper conditions
        if category != PremiumDocCategory.TYPE_A_TRUE_TABULAR:
            logger.debug("Skipping final cleanup: not TYPE_A")
            return layout
        
        if table_confidence < 0.65:
            logger.debug("Skipping final cleanup: table confidence too low")
            return layout
        
        # Check for abort flags
        if layout.metadata.get('header_not_found', False):
            logger.debug("Skipping final cleanup: HEADER_NOT_FOUND flag set")
            return layout
        
        if layout.metadata.get('span_conflict', False):
            logger.debug("Skipping final cleanup: SPAN_CONFLICT flag set")
            return layout
        
        logger.info("Starting final cleanup and normalization for TYPE_A table...")
        
        try:
            # Step 1: Empty Row Cleanup
            layout = self._cleanup_empty_rows(layout)
            
            # Step 2: Empty Column Cleanup (respecting header order)
            layout = self._cleanup_empty_columns(layout)
            
            # Step 3: Font Normalization
            layout = self._normalize_fonts(layout)
            
            # Step 4: Alignment Normalization
            layout = self._normalize_alignments(layout)
            
            # Step 5: Header Finalization (already handled in Excel renderer)
            # Just ensure metadata is set
            if layout.metadata.get('header_row_count', 0) > 0:
                layout.metadata['header_frozen'] = True
            
            logger.info("Final cleanup and normalization complete")
            return layout
            
        except Exception as e:
            logger.error(f"Final cleanup detected structural inconsistency: {e}. Preserving pre-clean state.")
            # Return original layout if cleanup fails
            return layout
    
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
        TYPE_B: KEY_VALUE layout - MANDATORY: Always EXACTLY 2 columns (Label | Value)
        
        Rules:
        1. Always create exactly 2 columns: Column A = Label, Column B = Value
        2. Label-Value Detection:
           - Contains ":" OR
           - Two text blocks on same horizontal line with left/right separation
        3. Multi-line Value: Append wrapped text to previous value (no new label row)
        4. Strict Row Integrity: One label-value pair per row
        5. Safety: Non-matching lines append to previous value
        6. Output Guarantee: NEVER single-column Excel
        """
        layout = UnifiedLayout(page_index=page_idx)
        layout.metadata['layout_type'] = 'key_value'
        row_idx = 0
        last_value_cell = None  # Track last value cell for multi-line appending
        
        # Priority 1: Use form fields if available (most reliable for key-value)
        if form_fields:
            logger.info(f"Page {page_idx + 1}: TYPE_B - Using {len(form_fields)} form fields for key-value layout")
            for field in form_fields:
                field_name = field.get('name', '').strip()
                field_value = field.get('value', '').strip()
                
                if field_name or field_value:
                    label_cell = Cell(
                        row=row_idx,
                        column=0,  # Column A = Label
                        value=field_name,
                        style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                    )
                    value_cell = Cell(
                        row=row_idx,
                        column=1,  # Column B = Value
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
            
            # Process blocks line by line (sorted by Y)
            for y_pos in sorted(blocks_by_y.keys()):
                line_blocks = sorted(blocks_by_y[y_pos], key=lambda b: b.get('bounding_box', {}).get('x_min', 0))
                
                # Check if line has left/right separation (two distinct blocks)
                if len(line_blocks) >= 2:
                    # Get leftmost and rightmost blocks
                    left_block = line_blocks[0]
                    right_block = line_blocks[-1]
                    
                    left_bbox = left_block.get('bounding_box', {})
                    right_bbox = right_block.get('bounding_box', {})
                    
                    left_x_max = left_bbox.get('x_max', 0)
                    right_x_min = right_bbox.get('x_min', 1)
                    
                    # Check for clear left/right separation (gap between blocks)
                    if right_x_min > left_x_max + 0.05:  # At least 5% gap
                        left_text = left_block.get('text', '').strip()
                        right_text = right_block.get('text', '').strip()
                        
                        if left_text and right_text:
                            # Left block = Label, Right block = Value
                            label_cell = Cell(
                                row=row_idx,
                                column=0,  # Column A = Label
                                value=left_text,
                                style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                            )
                            value_cell = Cell(
                                row=row_idx,
                                column=1,  # Column B = Value
                                value=right_text,
                                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                            )
                            layout.add_row([label_cell, value_cell])
                            last_value_cell = value_cell
                            row_idx += 1
                            continue
                
                # If not left/right separation, check for colon separator in combined text
                combined_text = ' '.join([b.get('text', '').strip() for b in line_blocks if b.get('text', '').strip()])
                if combined_text:
                    if ':' in combined_text:
                        parts = combined_text.split(':', 1)
                        if len(parts) == 2:
                            label = parts[0].strip()
                            value = parts[1].strip()
                            
                            if label:  # Label is required
                                label_cell = Cell(
                                    row=row_idx,
                                    column=0,  # Column A = Label
                                    value=label,
                                    style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                                )
                                value_cell = Cell(
                                    row=row_idx,
                                    column=1,  # Column B = Value
                                    value=value,
                                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                )
                                layout.add_row([label_cell, value_cell])
                                last_value_cell = value_cell
                                row_idx += 1
                                continue
                    
                    # Safety Rule: Non-matching line - append to previous value
                    if last_value_cell is not None:
                        # Append to previous value (notes/address continuation)
                        current_value = last_value_cell.value or ''
                        last_value_cell.value = (current_value + ' ' + combined_text).strip()
                        logger.debug(f"Page {page_idx + 1}: Appended non-matching line to previous value: {combined_text[:50]}")
                    else:
                        # First line without pattern - treat as label with empty value
                        label_cell = Cell(
                            row=row_idx,
                            column=0,  # Column A = Label
                            value=combined_text,
                            style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                        )
                        value_cell = Cell(
                            row=row_idx,
                            column=1,  # Column B = Value
                            value='',
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                        )
                        layout.add_row([label_cell, value_cell])
                        last_value_cell = value_cell
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
                            label_cell = Cell(
                                row=row_idx,
                                column=0,  # Column A = Label
                                value=label,
                                style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                            )
                            value_cell = Cell(
                                row=row_idx,
                                column=1,  # Column B = Value
                                value=value,
                                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                            )
                            layout.add_row([label_cell, value_cell])
                            last_value_cell = value_cell
                            row_idx += 1
                            continue
                
                # Safety Rule: Non-matching line - append to previous value
                if last_value_cell is not None:
                    # Multi-line Value Handling: Append wrapped text to previous value
                    current_value = last_value_cell.value or ''
                    last_value_cell.value = (current_value + ' ' + line).strip()
                    logger.debug(f"Page {page_idx + 1}: Appended wrapped text to previous value: {line[:50]}")
                else:
                    # First line without pattern - treat as label with empty value
                    label_cell = Cell(
                        row=row_idx,
                        column=0,  # Column A = Label
                        value=line,
                        style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                    )
                    value_cell = Cell(
                        row=row_idx,
                        column=1,  # Column B = Value
                        value='',
                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                    )
                    layout.add_row([label_cell, value_cell])
                    last_value_cell = value_cell
                    row_idx += 1
        
        # Output Guarantee: NEVER single-column Excel - always ensure 2 columns
        if row_idx == 0:
            # Fail-safe: Create minimal 2-column key-value layout
            logger.warning(f"Page {page_idx + 1}: TYPE_B - No key-value pairs found, creating minimal 2-column layout")
            label_cell = Cell(
                row=0,
                column=0,  # Column A = Label
                value="Content",
                style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
            )
            value_cell = Cell(
                row=0,
                column=1,  # Column B = Value
                value=document_text[:100] if document_text else "No content extracted",
                style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
            )
            layout.add_row([label_cell, value_cell])
        else:
            # Verify all rows have exactly 2 columns
            for row_cells in layout.rows:
                if len(row_cells) != 2:
                    logger.warning(f"Page {page_idx + 1}: TYPE_B - Row has {len(row_cells)} columns, expected 2. Fixing...")
                    # Ensure exactly 2 columns
                    while len(row_cells) < 2:
                        # Add empty cell if missing
                        empty_cell = Cell(
                            row=row_cells[0].row if row_cells else 0,
                            column=len(row_cells),
                            value='',
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                        )
                        row_cells.append(empty_cell)
                    # Remove extra columns (keep only first 2)
                    if len(row_cells) > 2:
                        row_cells[:] = row_cells[:2]
        
        logger.info(f"Page {page_idx + 1}: TYPE_B - Created key-value layout with {row_idx} rows (EXACTLY 2 columns: Label | Value)")
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
                        row_cells[nearest_col] = Cell(
                            row=row_idx,
                            column=nearest_col,
                            value=text,
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
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
        
        # Output Guarantee: Ensure at least 2 columns
        if layout.get_max_column() < 2:
            logger.warning(f"Page {page_idx + 1}: SOFT TABLE MODE - Layout has < 2 columns, using 2-column fallback")
            return self._soft_table_fallback_2column(document_text, page_idx)
        
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
        
        # Cluster X-positions (simple k-means-like approach)
        # Group X-positions that are close together
        # RELAXED tolerance for Hindi/Devanagari tables (0.08 = 8% instead of 5%)
        x_positions = sorted(set(x_positions))
        clusters = []
        cluster_tolerance = 0.08  # 8% tolerance (more relaxed for Hindi tables)
        
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
        
        if not page_structure or 'blocks' not in page_structure:
            logger.warning(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - No blocks available, using 2-column fallback")
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        all_blocks = [b for b in page_structure['blocks'] if b.get('bounding_box') and b.get('text', '').strip()]
        if not all_blocks:
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
                    if row_cells[nearest_col] is not None:
                        # Combine with existing cell (slight overlap)
                        existing_text = row_cells[nearest_col].value or ''
                        row_cells[nearest_col].value = (existing_text + ' ' + text).strip()
                    else:
                        row_cells[nearest_col] = Cell(
                            row=row_idx,
                            column=nearest_col,
                            value=text,
                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
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
                                if row_cells[second_nearest] is not None:
                                    existing_text = row_cells[second_nearest].value or ''
                                    row_cells[second_nearest].value = (existing_text + ' ' + text).strip()
                                else:
                                    row_cells[second_nearest] = Cell(
                                        row=row_idx,
                                        column=second_nearest,
                                        value=text,
                                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                    )
                            else:
                                # Still too misaligned - append to nearest anyway (allow slight misalignment)
                                if row_cells[nearest_col] is not None:
                                    existing_text = row_cells[nearest_col].value or ''
                                    row_cells[nearest_col].value = (existing_text + ' ' + text).strip()
                                else:
                                    row_cells[nearest_col] = Cell(
                                        row=row_idx,
                                        column=nearest_col,
                                        value=text,
                                        style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
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
        
        # Output Guarantee: Ensure at least 2 columns
        if layout.get_max_column() < 2:
            logger.warning(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - Layout has < 2 columns, using 2-column fallback")
            return self._soft_table_fallback_2column(document_text, page_idx)
        
        logger.info(f"Page {page_idx + 1}: VISUAL GRID RECONSTRUCTION - Created layout with {row_idx} rows, {layout.get_max_column()} columns")
        return layout
    
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
        
        # Cluster X-positions (visual column bands)
        x_positions = sorted(set(x_positions))
        clusters = []
        cluster_tolerance = 0.08  # 8% tolerance for visual alignment
        
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
