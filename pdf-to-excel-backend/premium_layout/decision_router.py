"""
Decision Router - Single Source of Truth for Premium PDF to Excel Routing

Enterprise-grade routing logic that determines ONE execution mode per document.
No silent fallbacks, no mid-pipeline downgrades.
"""

import logging
from typing import Optional, List, Any, Dict, Tuple
from enum import Enum
from .document_type_classifier import DocumentType

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Four execution modes for premium PDF to Excel conversion"""
    TABLE_STRICT = "table_strict"      # Native DocAI tables - trust structure
    TABLE_VISUAL = "table_visual"      # Visual grid reconstruction from blocks
    KEY_VALUE = "key_value"            # 2-column label:value layout
    PLAIN_TEXT = "plain_text"          # Single-column text export


class DecisionRouter:
    """
    Single source of truth for routing decisions.
    
    Determines ONE execution mode per document based on:
    1. Presence of native DocAI tables
    2. Document type (digital_pdf vs scanned)
    3. Visual alignment patterns in blocks
    4. Key-value patterns (invoices, bills)
    """
    
    def __init__(self):
        """Initialize decision router"""
        pass
    
    def _log_routing_decision(
        self,
        detected_columns: int,
        selected_mode: ExecutionMode,
        confidence: float,
        reason: str,
        key_value_blocked_reason: Optional[str] = None
    ):
        """
        Log routing decision summary.
        
        Args:
            detected_columns: Number of columns detected
            selected_mode: Selected execution mode
            confidence: Routing confidence (0.0-1.0)
            reason: Human-readable reason
            key_value_blocked_reason: Reason KEY_VALUE was blocked (if applicable)
        """
        logger.info("=" * 80)
        logger.info("ROUTING DECISION SUMMARY")
        logger.info(f"detected_columns: {detected_columns}")
        logger.info(f"selected_mode: {selected_mode.value}")
        logger.info(f"confidence: {confidence:.2f}")
        logger.info(f"reason: {reason}")
        if key_value_blocked_reason:
            logger.info(f"key_value_blocked_reason: {key_value_blocked_reason}")
        logger.info("=" * 80)
    
    def route(
        self,
        native_tables: Optional[List],
        doc_type: DocumentType,
        full_structure: Dict,
        document_text: str = ''
    ) -> Tuple[ExecutionMode, float, str]:
        """
        Route document to ONE execution mode.
        
        Args:
            native_tables: List of native DocAI table objects (if any)
            doc_type: Classified document type
            full_structure: Full OCR structure with blocks, form_fields, tables
            document_text: Extracted document text
            
        Returns:
            Tuple of (mode, confidence, reason):
            - mode: ExecutionMode enum
            - confidence: Float 0.0-1.0 indicating routing confidence
            - reason: Human-readable explanation of routing decision
        """
        # ====================================================================
        # HARD BLOCK RULE 0: MULTI-COLUMN GUARANTEE (CRITICAL)
        # ====================================================================
        # If detected_columns >= 2, FORCE TABLE_MODE and BLOCK KEY_VALUE
        # This rule MUST execute BEFORE any other routing logic
        detected_columns, column_detection_reason = self._detect_column_count(full_structure, native_tables)
        logger.info(f"Column detection: detected_columns={detected_columns}, reason={column_detection_reason}")
        
        if detected_columns >= 2:
            # FORCE TABLE_MODE - never allow KEY_VALUE for multi-column documents
            logger.warning(f"🚫 HARD BLOCK: detected_columns={detected_columns} >= 2 - FORCING TABLE_MODE, KEY_VALUE BLOCKED")
            
            # Check if we have native tables first
            if native_tables and len(native_tables) > 0:
                valid_tables = [t for t in native_tables if self._is_valid_table(t)]
                if valid_tables:
                    confidence = min(1.0, len(valid_tables) * 0.3 + 0.6)  # Higher confidence for forced table mode
                    reason = f"TABLE_MODE FORCED: {detected_columns} columns detected (native tables present) - KEY_VALUE blocked"
                    logger.info(f"DecisionRouter selected mode: TABLE_STRICT - {reason}")
                    self._log_routing_decision(detected_columns, ExecutionMode.TABLE_STRICT, confidence, reason, "detected_columns >= 2")
                    return (ExecutionMode.TABLE_STRICT, confidence, reason)
            
            # If no native tables, check for visual table patterns
            if doc_type == DocumentType.DIGITAL_PDF:
                visual_eligible, visual_confidence, visual_reason = self._check_visual_table_eligibility(full_structure)
                if visual_eligible:
                    confidence = min(1.0, visual_confidence + 0.2)  # Boost confidence for forced table mode
                    reason = f"TABLE_MODE FORCED: {detected_columns} columns detected (visual patterns) - KEY_VALUE blocked: {visual_reason}"
                    logger.info(f"DecisionRouter selected mode: TABLE_VISUAL - {reason}")
                    self._log_routing_decision(detected_columns, ExecutionMode.TABLE_VISUAL, confidence, reason, "detected_columns >= 2")
                    return (ExecutionMode.TABLE_VISUAL, confidence, reason)
            
            # Even without clear table structure, force TABLE_VISUAL for multi-column
            confidence = 0.7
            reason = f"TABLE_MODE FORCED: {detected_columns} columns detected - KEY_VALUE blocked (no clear table structure, using visual reconstruction)"
            logger.warning(f"⚠️ Multi-column document ({detected_columns} columns) but no clear table structure - forcing TABLE_VISUAL")
            self._log_routing_decision(detected_columns, ExecutionMode.TABLE_VISUAL, confidence, reason, "detected_columns >= 2")
            return (ExecutionMode.TABLE_VISUAL, confidence, reason)
        
        # ROUTING RULE 1: If native DocAI tables exist → TABLE_STRICT
        # CRITICAL FIX: Check tables FIRST, even for invoices/bills
        # Invoices often have line items tables that should use TABLE_STRICT
        if native_tables and len(native_tables) > 0:
            # Check if tables have valid structure
            valid_tables = [t for t in native_tables if self._is_valid_table(t)]
            if valid_tables:
                # For invoices/bills with tables, use TABLE_STRICT (not KEY_VALUE)
                if doc_type in [DocumentType.INVOICE, DocumentType.BILL, DocumentType.BANK_STATEMENT]:
                    confidence = min(1.0, len(valid_tables) * 0.3 + 0.5)  # Higher confidence for structured invoices
                    reason = f"Invoice/Bill with native DocAI tables detected ({len(valid_tables)} tables) - using TABLE_STRICT for line items"
                    logger.info(f"DecisionRouter selected mode: TABLE_STRICT - {reason}")
                    self._log_routing_decision(detected_columns, ExecutionMode.TABLE_STRICT, confidence, reason)
                    return (ExecutionMode.TABLE_STRICT, confidence, reason)
                else:
                    confidence = min(1.0, len(valid_tables) * 0.3 + 0.4)  # More tables = higher confidence
                    reason = f"Native DocAI tables detected ({len(valid_tables)} tables)"
                    logger.info(f"DecisionRouter selected mode: TABLE_STRICT - {reason}")
                    self._log_routing_decision(detected_columns, ExecutionMode.TABLE_STRICT, confidence, reason)
                    return (ExecutionMode.TABLE_STRICT, confidence, reason)
        
        # ROUTING RULE 2: Else if digital_pdf AND blocks show repeated X-aligned rows → TABLE_VISUAL
        # CRITICAL FIX: For invoices without native tables, check for visual table patterns
        if doc_type == DocumentType.DIGITAL_PDF:
            visual_eligible, visual_confidence, visual_reason = self._check_visual_table_eligibility(
                full_structure
            )
            if visual_eligible:
                # For invoices with visual table patterns, use TABLE_VISUAL (not KEY_VALUE)
                if doc_type in [DocumentType.INVOICE, DocumentType.BILL, DocumentType.BANK_STATEMENT]:
                    reason = f"Invoice/Bill with visual table patterns detected - using TABLE_VISUAL for line items: {visual_reason}"
                    logger.info(f"DecisionRouter selected mode: TABLE_VISUAL - {reason}")
                    self._log_routing_decision(detected_columns, ExecutionMode.TABLE_VISUAL, visual_confidence, reason)
                    return (ExecutionMode.TABLE_VISUAL, visual_confidence, reason)
                else:
                    logger.info(f"DecisionRouter selected mode: TABLE_VISUAL - {visual_reason}")
                    self._log_routing_decision(detected_columns, ExecutionMode.TABLE_VISUAL, visual_confidence, visual_reason)
                    return (ExecutionMode.TABLE_VISUAL, visual_confidence, visual_reason)
        
        # ROUTING RULE 3: Else if key:value or invoice pattern → KEY_VALUE
        # CRITICAL SAFETY: KEY_VALUE only allowed if ALL safety conditions pass
        # Safety conditions:
        # - detected_columns <= 1 (already checked by hard block rule above)
        # - table_confidence < 0.4
        # - repeated label:value pattern detected
        # - no row grid alignment
        
        # Calculate table confidence from native tables (if any)
        table_confidence = 0.0
        if native_tables and len(native_tables) > 0:
            valid_tables = [t for t in native_tables if self._is_valid_table(t)]
            if valid_tables:
                table_confidence = min(1.0, len(valid_tables) * 0.3 + 0.4)
        
        # Check for row grid alignment (if present, block KEY_VALUE)
        has_row_grid_alignment = self._has_row_grid_alignment(full_structure)
        
        key_value_eligible, kv_confidence, kv_reason, blocked_reasons = self._check_key_value_eligibility_with_safety(
            doc_type, full_structure, document_text, detected_columns, table_confidence, has_row_grid_alignment
        )
        
        if key_value_eligible:
            # For invoices without tables, use KEY_VALUE for header info only
            if doc_type in [DocumentType.INVOICE, DocumentType.BILL, DocumentType.BANK_STATEMENT]:
                reason = f"Invoice/Bill without tables detected - using KEY_VALUE for header/metadata only: {kv_reason}"
                logger.warning(f"⚠️ Invoice has no tables - line items may not be extracted. Consider Adobe fallback if premium enabled.")
            logger.info(f"DecisionRouter selected mode: KEY_VALUE - {kv_reason}")
            self._log_routing_decision(detected_columns, ExecutionMode.KEY_VALUE, kv_confidence, kv_reason)
            return (ExecutionMode.KEY_VALUE, kv_confidence, kv_reason)
        else:
            # KEY_VALUE blocked - log reasons and fall through to PLAIN_TEXT
            blocked_reason_str = ', '.join(blocked_reasons) if blocked_reasons else "Unknown"
            logger.warning(f"🚫 KEY_VALUE MODE BLOCKED: {blocked_reason_str}")
            logger.info(f"Falling back to PLAIN_TEXT mode")
        
        # ROUTING RULE 4: Else → PLAIN_TEXT
        reason = "No table patterns detected - using plain text export"
        logger.info(f"DecisionRouter selected mode: PLAIN_TEXT - {reason}")
        self._log_routing_decision(detected_columns, ExecutionMode.PLAIN_TEXT, 0.5, reason)
        return (ExecutionMode.PLAIN_TEXT, 0.5, reason)
    
    def should_enable_adobe_fallback(
        self,
        docai_confidence: float,
        full_structure: Dict,
        user_plan: str = "premium"
    ) -> Tuple[bool, str]:
        """
        Determine if Adobe PDF Extract fallback should be enabled.
        
        SELECTIVE FALLBACK RULES:
        - Document AI confidence < 0.65
        - Visual complexity is HIGH (many blocks, merged cells, charts)
        - User plan is "premium" (pay-per-use)
        
        Args:
            docai_confidence: Confidence from Document AI routing (0.0-1.0)
            full_structure: Full OCR structure with blocks
            user_plan: User subscription plan (default: "premium")
        
        Returns:
            Tuple of (enable_fallback, reason)
        """
        # Rule 1: Only for premium users (pay-per-use model)
        if user_plan != "premium":
            return (False, "Adobe fallback only available for premium plan")
        
        # Rule 2: Only if DocAI confidence is low
        if docai_confidence >= 0.65:
            return (False, f"Document AI confidence {docai_confidence:.2f} >= 0.65 - fallback not needed")
        
        # Rule 3: Check visual complexity
        complexity_score, complexity_reason = self._assess_visual_complexity(full_structure)
        
        if complexity_score < 0.6:  # LOW or MEDIUM complexity
            return (False, f"Visual complexity {complexity_reason} - fallback not needed")
        
        # All conditions met - enable Adobe fallback
        reason = f"DocAI confidence {docai_confidence:.2f} < 0.65, complexity: {complexity_reason}"
        logger.info(f"Adobe fallback ENABLED: {reason}")
        return (True, reason)
    
    def _assess_visual_complexity(self, full_structure: Dict) -> Tuple[float, str]:
        """
        Assess visual complexity of document for Adobe fallback decision.
        
        HIGH complexity indicators:
        - Many blocks (>100)
        - Mixed content (tables + text + images)
        - Potential merged cells
        - Charts or diagrams
        
        Returns:
            Tuple of (complexity_score, description)
            - complexity_score: 0.0-1.0 (0.6+ is HIGH)
            - description: Human-readable complexity level
        """
        if not full_structure:
            return (0.0, "NONE")
        
        blocks = full_structure.get('blocks', [])
        tables = full_structure.get('tables', [])
        
        # Factor 1: Block count
        block_score = min(1.0, len(blocks) / 150.0)
        
        # Factor 2: Table presence (but incomplete)
        table_score = 0.0
        if tables and len(tables) > 0:
            # Tables exist but confidence was low (otherwise we wouldn't be here)
            table_score = 0.5
        
        # Factor 3: Block diversity (varied sizes suggest complex layout)
        block_sizes = []
        for block in blocks[:100]:  # Sample first 100 blocks
            bbox = block.get('bounding_box', {})
            if bbox:
                width = bbox.get('x_max', 0) - bbox.get('x_min', 0)
                height = bbox.get('y_max', 0) - bbox.get('y_min', 0)
                block_sizes.append(width * height)
        
        diversity_score = 0.0
        if block_sizes:
            import statistics
            try:
                std_dev = statistics.stdev(block_sizes) if len(block_sizes) > 1 else 0
                mean_size = statistics.mean(block_sizes)
                if mean_size > 0:
                    diversity_score = min(1.0, (std_dev / mean_size) * 0.5)
            except:
                pass
        
        # Weighted complexity score
        complexity_score = (block_score * 0.4 + table_score * 0.3 + diversity_score * 0.3)
        
        # Classify complexity
        if complexity_score >= 0.7:
            description = "HIGH (complex tables/mixed content)"
        elif complexity_score >= 0.5:
            description = "MEDIUM (moderate structure)"
        else:
            description = "LOW (simple document)"
        
        return (complexity_score, description)
    
    def _is_valid_table(self, table: Any) -> bool:
        """
        Check if a DocAI table object has valid structure.
        
        Valid table must have:
        - header_rows or body_rows attribute
        - At least one row with cells
        """
        if not table:
            return False
        
        # Check for header_rows
        if hasattr(table, 'header_rows') and table.header_rows:
            if len(table.header_rows) > 0:
                first_header = table.header_rows[0]
                if hasattr(first_header, 'cells') and len(first_header.cells) > 0:
                    return True
        
        # Check for body_rows
        if hasattr(table, 'body_rows') and table.body_rows:
            if len(table.body_rows) > 0:
                first_body = table.body_rows[0]
                if hasattr(first_body, 'cells') and len(first_body.cells) > 0:
                    return True
        
        return False
    
    def _detect_column_count(
        self,
        full_structure: Dict,
        native_tables: Optional[List]
    ) -> Tuple[int, str]:
        """
        Detect the number of columns in the document.
        
        Priority:
        1. Native DocAI tables (count columns from table structure)
        2. Block X-position clusters (visual column detection)
        
        Returns:
            Tuple of (detected_column_count, reason)
        """
        # Method 1: Check native tables first (most reliable)
        if native_tables and len(native_tables) > 0:
            max_columns = 0
            for table in native_tables:
                if not self._is_valid_table(table):
                    continue
                
                # Count columns from header rows
                if hasattr(table, 'header_rows') and table.header_rows:
                    for header_row in table.header_rows:
                        if hasattr(header_row, 'cells'):
                            max_columns = max(max_columns, len(header_row.cells))
                
                # Count columns from body rows
                if hasattr(table, 'body_rows') and table.body_rows:
                    for body_row in table.body_rows:
                        if hasattr(body_row, 'cells'):
                            max_columns = max(max_columns, len(body_row.cells))
            
            if max_columns >= 2:
                return (max_columns, f"Native table structure: {max_columns} columns detected")
        
        # Method 2: Detect columns from block X-position clusters
        blocks = full_structure.get('blocks', []) if full_structure else []
        if not blocks or len(blocks) < 3:
            return (1, "Insufficient blocks for column detection")
        
        # Extract X-centroids from blocks
        x_centroids = []
        for block in blocks:
            bbox = block.get('bounding_box', {}) if isinstance(block, dict) else {}
            if not bbox:
                # Try to get bounding box from block object
                if hasattr(block, 'layout') and hasattr(block.layout, 'bounding_poly'):
                    vertices = block.layout.bounding_poly.normalized_vertices
                    if len(vertices) >= 4:
                        xs = [v.x for v in vertices if hasattr(v, 'x')]
                        if xs:
                            x_centroid = (min(xs) + max(xs)) / 2
                            x_centroids.append(x_centroid)
                continue
            
            x_min = bbox.get('x_min', 0)
            x_max = bbox.get('x_max', 0)
            if x_max > x_min:
                x_centroid = (x_min + x_max) / 2
                x_centroids.append(x_centroid)
        
        if len(x_centroids) < 3:
            return (1, "Insufficient X-positions for column detection")
        
        # Cluster X-positions to detect columns
        # Sort X-positions
        x_centroids_sorted = sorted(x_centroids)
        
        # Use adaptive tolerance (2% of page width)
        tolerance = 0.02
        
        # Cluster X-positions
        clusters = []
        current_cluster = [x_centroids_sorted[0]]
        
        for x in x_centroids_sorted[1:]:
            # Check if x is within tolerance of current cluster
            cluster_center = sum(current_cluster) / len(current_cluster)
            if abs(x - cluster_center) <= tolerance:
                current_cluster.append(x)
            else:
                # Start new cluster
                if len(current_cluster) >= 2:  # Require at least 2 blocks per column
                    clusters.append(current_cluster)
                current_cluster = [x]
        
        # Add last cluster
        if len(current_cluster) >= 2:
            clusters.append(current_cluster)
        
        detected_columns = len(clusters)
        
        if detected_columns >= 2:
            reason = f"Block X-clustering: {detected_columns} distinct column positions detected (tolerance={tolerance})"
        else:
            reason = f"Block X-clustering: {detected_columns} column(s) detected (single column or insufficient alignment)"
        
        return (detected_columns, reason)
    
    def _check_visual_table_eligibility(
        self,
        full_structure: Dict
    ) -> Tuple[bool, float, str]:
        """
        Check if document is eligible for TABLE_VISUAL mode.
        
        Requirements:
        - blocks >= 30
        - >= 3 rows with horizontal alignment (>= 2 blocks per row)
        - >= 2 distinct X-position clusters repeating vertically
        - Presence of numeric columns (IDs, Aadhaar, serial numbers)
        
        Returns:
            Tuple of (eligible, confidence, reason)
        """
        if not full_structure or 'blocks' not in full_structure:
            return (False, 0.0, "No blocks available")
        
        blocks = [b for b in full_structure['blocks'] if b.get('bounding_box') and b.get('text', '').strip()]
        
        # Requirement 1: blocks >= 30
        if len(blocks) < 30:
            return (False, 0.0, f"Only {len(blocks)} blocks, need >= 30")
        
        # Group blocks by Y-position (rows) - relaxed precision for visual alignment
        blocks_by_y = {}
        for block in blocks:
            bbox = block.get('bounding_box', {})
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 50) / 50  # 0.02 precision (relaxed)
            if y_key not in blocks_by_y:
                blocks_by_y[y_key] = []
            blocks_by_y[y_key].append(block)
        
        # Requirement 2: >= 3 rows with horizontal alignment
        rows_with_horizontal_alignment = 0
        x_clusters_all_rows = []
        numeric_blocks_count = 0
        
        for y_pos, row_blocks in blocks_by_y.items():
            if len(row_blocks) >= 2:  # At least 2 blocks in row (horizontal alignment)
                x_positions = []
                for block in row_blocks:
                    bbox = block.get('bounding_box', {})
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    x_positions.append(x_center)
                    
                    # Check for numeric content
                    text = block.get('text', '').strip()
                    if self._is_aadhaar_or_long_numeric(text):
                        numeric_blocks_count += 1
                    # Also check for short numeric sequences (serial numbers, IDs)
                    digits_only = ''.join(c for c in text if c.isdigit())
                    if 4 <= len(digits_only) <= 9 and len(text) <= 20:
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
        
        if rows_with_horizontal_alignment < 3:
            return (False, 0.0, f"Only {rows_with_horizontal_alignment} aligned rows, need >= 3")
        
        # Requirement 3: >= 2 distinct X-position clusters repeating vertically
        if len(x_clusters_all_rows) < 10:
            return (False, 0.0, f"Only {len(x_clusters_all_rows)} X-positions, need >= 10")
        
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
                if len(row_blocks) >= 2:
                    for block in row_blocks:
                        bbox = block.get('bounding_box', {})
                        x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                        if abs(x_center - cluster_center) <= cluster_tolerance:
                            row_count += 1
                            break
            
            if row_count >= 2:
                distinct_vertical_bands += 1
        
        if distinct_vertical_bands < 2:
            return (False, 0.0, f"Only {distinct_vertical_bands} vertical bands, need >= 2")
        
        # Requirement 4: Presence of numeric columns
        if numeric_blocks_count < 2:
            return (False, 0.0, f"Only {numeric_blocks_count} numeric blocks, need >= 2")
        
        # All requirements passed
        confidence = min(1.0, (rows_with_horizontal_alignment / 10.0) * 0.4 + 
                        (distinct_vertical_bands / 5.0) * 0.3 + 
                        (numeric_blocks_count / 10.0) * 0.3)
        reason = f"Visual table detected: {len(blocks)} blocks, {rows_with_horizontal_alignment} aligned rows, {distinct_vertical_bands} vertical bands, {numeric_blocks_count} numeric blocks"
        return (True, confidence, reason)
    
    def _has_row_grid_alignment(self, full_structure: Dict) -> bool:
        """
        Check if document has row grid alignment (indicating table structure).
        
        Returns:
            True if row grid alignment detected, False otherwise
        """
        blocks = full_structure.get('blocks', []) if full_structure else []
        if len(blocks) < 6:
            return False
        
        # Group blocks by Y-position (rows)
        blocks_by_y = {}
        for block in blocks:
            bbox = block.get('bounding_box', {}) if isinstance(block, dict) else {}
            if not bbox:
                continue
            y_center = (bbox.get('y_min', 0) + bbox.get('y_max', 0)) / 2
            y_key = round(y_center * 50) / 50  # 0.02 precision
            if y_key not in blocks_by_y:
                blocks_by_y[y_key] = []
            blocks_by_y[y_key].append(block)
        
        # Check if we have >= 3 rows with >= 2 blocks each
        aligned_rows = 0
        for y_pos, row_blocks in blocks_by_y.items():
            if len(row_blocks) >= 2:
                aligned_rows += 1
        
        return aligned_rows >= 3
    
    def _check_key_value_eligibility_with_safety(
        self,
        doc_type: DocumentType,
        full_structure: Dict,
        document_text: str,
        detected_columns: int,
        table_confidence: float,
        has_row_grid_alignment: bool
    ) -> Tuple[bool, float, str, List[str]]:
        """
        Check if document is eligible for KEY_VALUE mode WITH SAFETY CONDITIONS.
        
        Safety Conditions (ALL must pass):
        1. detected_columns <= 1
        2. table_confidence < 0.4
        3. repeated label:value pattern detected
        4. no row grid alignment
        
        Returns:
            Tuple of (eligible, confidence, reason, blocked_reasons)
        """
        blocked_reasons = []
        
        # SAFETY CONDITION 1: detected_columns <= 1
        if detected_columns > 1:
            blocked_reasons.append(f"detected_columns={detected_columns} > 1")
            return (False, 0.0, "", blocked_reasons)
        
        # SAFETY CONDITION 2: table_confidence < 0.4
        if table_confidence >= 0.4:
            blocked_reasons.append(f"table_confidence={table_confidence:.2f} >= 0.4")
            return (False, 0.0, "", blocked_reasons)
        
        # SAFETY CONDITION 3: repeated label:value pattern detected
        kv_pattern_count = 0
        if document_text:
            lines = document_text.split('\n')
            for line in lines[:50]:  # Check first 50 lines
                line = line.strip()
                if ':' in line and len(line.split(':')) == 2:
                    parts = line.split(':')
                    if len(parts[0].strip()) > 0 and len(parts[1].strip()) > 0:
                        kv_pattern_count += 1
        
        if kv_pattern_count < 3:
            blocked_reasons.append(f"insufficient key:value patterns ({kv_pattern_count} < 3)")
            return (False, 0.0, "", blocked_reasons)
        
        # SAFETY CONDITION 4: no row grid alignment
        if has_row_grid_alignment:
            blocked_reasons.append("row grid alignment detected (table structure present)")
            return (False, 0.0, "", blocked_reasons)
        
        # All safety conditions passed - check eligibility
        # Check document type
        if doc_type in [DocumentType.INVOICE, DocumentType.BILL, DocumentType.BANK_STATEMENT]:
            confidence = 0.9
            reason = f"Document type is {doc_type.value} (safety conditions passed)"
            return (True, confidence, reason, blocked_reasons)
        
        # Check for form fields
        form_fields = full_structure.get('form_fields', []) if full_structure else []
        if form_fields and len(form_fields) > 0:
            confidence = 0.8
            reason = f"Form fields detected ({len(form_fields)} fields) (safety conditions passed)"
            return (True, confidence, reason, blocked_reasons)
        
        # Key:value patterns already checked above
        if kv_pattern_count >= 3:
            confidence = 0.7
            reason = f"Key:value patterns detected ({kv_pattern_count} patterns) (safety conditions passed)"
            return (True, confidence, reason, blocked_reasons)
        
        blocked_reasons.append("No key-value eligibility criteria met")
        return (False, 0.0, "", blocked_reasons)
    
    def _check_key_value_eligibility(
        self,
        doc_type: DocumentType,
        full_structure: Dict,
        document_text: str
    ) -> Tuple[bool, float, str]:
        """
        DEPRECATED: Use _check_key_value_eligibility_with_safety instead.
        
        Check if document is eligible for KEY_VALUE mode.
        
        Requirements:
        - Document type is invoice, bill, or bank statement
        - OR form_fields present
        - OR text contains key:value patterns (colon-separated)
        """
        # Check document type
        if doc_type in [DocumentType.INVOICE, DocumentType.BILL, DocumentType.BANK_STATEMENT]:
            confidence = 0.9
            reason = f"Document type is {doc_type.value}"
            return (True, confidence, reason)
        
        # Check for form fields
        form_fields = full_structure.get('form_fields', []) if full_structure else []
        if form_fields and len(form_fields) > 0:
            confidence = 0.8
            reason = f"Form fields detected ({len(form_fields)} fields)"
            return (True, confidence, reason)
        
        # Check for key:value patterns in text
        if document_text:
            lines = document_text.split('\n')
            kv_pattern_count = 0
            for line in lines[:50]:  # Check first 50 lines
                line = line.strip()
                if ':' in line and len(line.split(':')) == 2:
                    parts = line.split(':')
                    if len(parts[0].strip()) > 0 and len(parts[1].strip()) > 0:
                        kv_pattern_count += 1
            
            if kv_pattern_count >= 3:
                confidence = 0.7
                reason = f"Key:value patterns detected ({kv_pattern_count} patterns)"
                return (True, confidence, reason)
        
        return (False, 0.0, "No key-value patterns detected")
    
    def _is_aadhaar_or_long_numeric(self, text: str) -> bool:
        """Detect long numeric sequences (10-12 digits with spaces) - Aadhaar protection"""
        digits_only = ''.join(c for c in text if c.isdigit())
        if 10 <= len(digits_only) <= 12:
            if ' ' in text:
                return True
        return False
    
    def check_structural_failures(
        self,
        docai_result: Dict,
        unified_layouts: List[Any]
    ) -> Tuple[bool, List[str]]:
        """
        STRUCTURAL FAILURE GATE: Check if document has structural issues
        requiring Adobe PDF Extract.
        
        Returns:
            Tuple of (has_failures, list_of_failure_reasons)
        """
        failures = []
        
        # Extract metrics from layouts
        detected_columns = 0
        detected_rows = 0
        merged_cell_count = 0
        
        if unified_layouts:
            for layout in unified_layouts:
                if hasattr(layout, 'rows') and layout.rows:
                    detected_rows = max(detected_rows, len(layout.rows))
                    
                    for row in layout.rows:
                        detected_columns = max(detected_columns, len(row))
                        
                        for cell in row:
                            if hasattr(cell, 'row_span') and hasattr(cell, 'col_span'):
                                if cell.row_span > 1 or cell.col_span > 1:
                                    merged_cell_count += 1
        
        # FAILURE CHECK 1: Single-column collapse (multi-row doc becomes 1 column)
        if detected_rows >= 3 and detected_columns == 1:
            failures.append(f"Single-column collapse: {detected_rows} rows but only 1 column")
        
        # FAILURE CHECK 2: No columns detected (but has content)
        if detected_columns < 2 and detected_rows > 0:
            failures.append(f"Insufficient columns: {detected_columns} (need >= 2)")
        
        # FAILURE CHECK 3: Many merged cells indicate complex table
        if merged_cell_count >= 3:
            failures.append(f"Complex merges: {merged_cell_count} merged cells")
        
        # FAILURE CHECK 4: Visual complexity from blocks
        blocks = docai_result.get('blocks', [])
        if len(blocks) > 100:
            # Check for mixed content patterns
            varied_font_sizes = set()
            for block in blocks[:50]:  # Sample first 50
                if 'font_size' in block:
                    varied_font_sizes.add(block['font_size'])
            
            if len(varied_font_sizes) >= 4:
                failures.append(f"High visual complexity: {len(blocks)} blocks with {len(varied_font_sizes)} font sizes")
        
        # FAILURE CHECK 5: Document type indicators
        doc_type = docai_result.get('document_type', '')
        if doc_type in ['bank_statement', 'govt_form', 'utility_bill']:
            failures.append(f"Complex document type: {doc_type}")
        
        has_failures = len(failures) > 0
        return (has_failures, failures)
    
    def should_enable_adobe_with_guardrails(
        self,
        user_wants_premium: bool,
        docai_confidence: float,
        full_structure: Dict,
        unified_layouts: List[Any],
        page_count: int,
        user_plan: str = "premium"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        COMPREHENSIVE ADOBE FALLBACK GATING with cost guardrails.
        
        Gates (in order):
        1. Premium Toggle Gate
        2. Confidence Gate
        3. Structural Failure Gate
        4. Page Count Guard
        5. Cost Caps
        
        Args:
            user_wants_premium: User explicitly enabled premium toggle
            docai_confidence: Document AI routing confidence
            full_structure: Full OCR structure
            unified_layouts: Processed layouts from DocAI
            page_count: Number of pages in document
            user_plan: User subscription plan
        
        Returns:
            Tuple of (enable_adobe, reason, metadata)
        """
        metadata = {
            'gates_passed': [],
            'gates_failed': [],
            'estimated_adobe_pages': 0,
            'estimated_cost_credits': 0
        }
        
        # GATE 1: Premium Toggle (User Control)
        if not user_wants_premium:
            metadata['gates_failed'].append('premium_toggle_off')
            return (False, "User did not enable premium mode - Adobe skipped", metadata)
        
        metadata['gates_passed'].append('premium_toggle_on')
        logger.info("✅ GATE 1 PASSED: User enabled premium toggle")
        
        # GATE 2: Confidence Threshold
        if docai_confidence >= 0.75:
            metadata['gates_failed'].append('high_confidence')
            return (False, f"Document AI confidence {docai_confidence:.2f} >= 0.75 - Adobe not needed", metadata)
        
        metadata['gates_passed'].append('low_confidence')
        logger.info(f"✅ GATE 2 PASSED: Low confidence ({docai_confidence:.2f} < 0.75)")
        
        # GATE 3: Structural Failure Detection
        has_failures, failure_reasons = self.check_structural_failures(full_structure, unified_layouts)
        
        if not has_failures:
            metadata['gates_failed'].append('no_structural_failures')
            return (False, "No structural failures detected - Adobe not needed", metadata)
        
        metadata['gates_passed'].append('structural_failures')
        metadata['failure_reasons'] = failure_reasons
        logger.info(f"✅ GATE 3 PASSED: Structural failures detected: {', '.join(failure_reasons)}")
        
        # GATE 4: Page Count Guard
        if page_count > 20:
            metadata['gates_failed'].append('excessive_pages')
            metadata['warning'] = f"Document has {page_count} pages (>20) - requires user confirmation"
            logger.warning(f"⚠️ GATE 4 WARNING: {page_count} pages exceed threshold - would require confirmation")
            # In production, this would prompt user
            # For now, we allow but log
        
        metadata['gates_passed'].append('page_count_ok')
        
        # GATE 5: Cost Caps
        MAX_ADOBE_PAGES_PER_DOC = 50
        MAX_ADOBE_CALLS_PER_DOC = 3
        
        if page_count > MAX_ADOBE_PAGES_PER_DOC:
            metadata['gates_failed'].append('page_limit_exceeded')
            return (False, f"Document has {page_count} pages, exceeds Adobe limit of {MAX_ADOBE_PAGES_PER_DOC}", metadata)
        
        metadata['gates_passed'].append('within_cost_caps')
        
        # Calculate estimated cost
        metadata['estimated_adobe_pages'] = page_count
        if page_count <= 10:
            metadata['estimated_cost_credits'] = page_count * 15
        else:
            metadata['estimated_cost_credits'] = (10 * 15) + ((page_count - 10) * 5)
        
        # ALL GATES PASSED
        reason = f"Adobe fallback ALLOWED: {len(metadata['gates_passed'])} gates passed"
        reason += f" | Failures: {', '.join(failure_reasons)}"
        reason += f" | Estimated cost: {metadata['estimated_cost_credits']} credits for {page_count} pages"
        
        logger.info("=" * 80)
        logger.info("🚀 ALL ADOBE GUARDRAILS PASSED")
        logger.info(f"Gates passed: {', '.join(metadata['gates_passed'])}")
        logger.info(f"Structural failures: {', '.join(failure_reasons)}")
        logger.info(f"Estimated Adobe cost: {metadata['estimated_cost_credits']} credits ({page_count} pages)")
        logger.info("=" * 80)
        
        return (True, reason, metadata)

