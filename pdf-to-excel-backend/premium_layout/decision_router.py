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
        # ROUTING RULE 1: If native DocAI tables exist → TABLE_STRICT
        if native_tables and len(native_tables) > 0:
            # Check if tables have valid structure
            valid_tables = [t for t in native_tables if self._is_valid_table(t)]
            if valid_tables:
                confidence = min(1.0, len(valid_tables) * 0.3 + 0.4)  # More tables = higher confidence
                reason = f"Native DocAI tables detected ({len(valid_tables)} tables)"
                logger.info(f"DecisionRouter selected mode: TABLE_STRICT - {reason}")
                return (ExecutionMode.TABLE_STRICT, confidence, reason)
        
        # ROUTING RULE 2: Else if digital_pdf AND blocks show repeated X-aligned rows → TABLE_VISUAL
        if doc_type == DocumentType.DIGITAL_PDF:
            visual_eligible, visual_confidence, visual_reason = self._check_visual_table_eligibility(
                full_structure
            )
            if visual_eligible:
                logger.info(f"DecisionRouter selected mode: TABLE_VISUAL - {visual_reason}")
                return (ExecutionMode.TABLE_VISUAL, visual_confidence, visual_reason)
        
        # ROUTING RULE 3: Else if key:value or invoice pattern → KEY_VALUE
        key_value_eligible, kv_confidence, kv_reason = self._check_key_value_eligibility(
            doc_type, full_structure, document_text
        )
        if key_value_eligible:
            logger.info(f"DecisionRouter selected mode: KEY_VALUE - {kv_reason}")
            return (ExecutionMode.KEY_VALUE, kv_confidence, kv_reason)
        
        # ROUTING RULE 4: Else → PLAIN_TEXT
        reason = "No table patterns detected - using plain text export"
        logger.info(f"DecisionRouter selected mode: PLAIN_TEXT - {reason}")
        return (ExecutionMode.PLAIN_TEXT, 0.5, reason)
    
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
    
    def _check_key_value_eligibility(
        self,
        doc_type: DocumentType,
        full_structure: Dict,
        document_text: str
    ) -> Tuple[bool, float, str]:
        """
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

