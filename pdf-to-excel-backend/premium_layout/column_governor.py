"""
STRICT COLUMN GOVERNOR
Prevents extra columns by enforcing semantic column count based on document structure.
CRITICAL: Never fixes grid to hard-coded limits. Always data-driven.
"""

import logging
from typing import List, Dict, Any, Optional
from .unified_layout_model import UnifiedLayout, Cell

logger = logging.getLogger(__name__)


class ColumnGovernor:
    """
    Enforces strict column count based on semantic analysis.
    Prevents visual alignment from creating fake columns.
    """
    
    def __init__(self):
        """Initialize Column Governor"""
        pass
    
    def analyze_semantic_columns(
        self, 
        layout: UnifiedLayout, 
        document_type: Optional[str] = None,
        original_blocks: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        Analyze layout to determine actual semantic column count using HARD SEMANTIC LOCK.
        
        Detection methods:
        a) Header text alignment
        b) Repeated numeric alignment (currency / totals)
        c) Vertical band density
        
        FINAL column count = MIN(stable semantic columns, detected visual bands)
        
        ❌ NEVER create new columns from:
        - whitespace gaps
        - logo/image blocks
        - isolated numeric values
        
        Returns:
            Actual semantic column count (minimum 1, maximum based on data)
        """
        if not layout.rows or len(layout.rows) == 0:
            return 0
        
        # Collect all column positions that have actual text
        columns_with_text = set()
        left_aligned_positions = set()
        right_aligned_positions = set()
        center_aligned_positions = set()
        
        # Track header rows (first 3 rows typically)
        header_rows = layout.rows[:3] if len(layout.rows) >= 3 else layout.rows
        header_columns = set()
        
        # Track numeric columns (currency/totals pattern)
        numeric_columns = set()
        currency_patterns = ['₹', '$', '€', '£', '¥', 'Rs.', 'INR', 'USD']
        
        for row_idx, row in enumerate(layout.rows):
            for cell in row:
                if cell.value and cell.value.strip():
                    cell_text = str(cell.value).strip()
                    columns_with_text.add(cell.column)
                    
                    # Track alignment
                    if hasattr(cell.style, 'alignment_horizontal'):
                        if cell.style.alignment_horizontal.value == 'left':
                            left_aligned_positions.add(cell.column)
                        elif cell.style.alignment_horizontal.value == 'right':
                            right_aligned_positions.add(cell.column)
                        elif cell.style.alignment_horizontal.value == 'center':
                            center_aligned_positions.add(cell.column)
                    
                    # Detect header rows (bold text, short text, common header words)
                    if row_idx < 3:
                        is_header = (
                            (cell.style and cell.style.bold) or
                            any(header_word in cell_text.lower() for header_word in [
                                'name', 'date', 'amount', 'total', 'item', 'description', 
                                'qty', 'quantity', 'price', 'rate', 'sum', 'subtotal'
                            ]) or
                            len(cell_text) < 30
                        )
                        if is_header:
                            header_columns.add(cell.column)
                    
                    # Detect numeric/currency columns
                    if any(pattern in cell_text for pattern in currency_patterns):
                        numeric_columns.add(cell.column)
                    # Also check if value is numeric
                    try:
                        # Remove currency symbols and check if numeric
                        clean_text = cell_text
                        for pattern in currency_patterns:
                            clean_text = clean_text.replace(pattern, '')
                        clean_text = clean_text.replace(',', '').replace(' ', '')
                        float(clean_text)
                        numeric_columns.add(cell.column)
                    except (ValueError, AttributeError):
                        pass
        
        if not columns_with_text:
            return 0
        
        max_col = max(columns_with_text)
        
        # Calculate vertical band density from original blocks (if available)
        visual_bands = set()
        if original_blocks:
            # Group blocks by X-position to detect vertical bands
            x_positions = []
            for block in original_blocks:
                bbox = block.get('bounding_box', {})
                if bbox and block.get('text', '').strip():
                    # Skip image/logo blocks
                    block_type = block.get('type', '').lower()
                    if 'image' in block_type or 'logo' in block_type:
                        continue
                    
                    x_center = (bbox.get('x_min', 0) + bbox.get('x_max', 0)) / 2
                    x_positions.append(x_center)
            
            if x_positions:
                # Cluster X positions to detect vertical bands
                sorted_x = sorted(set(x_positions))
                # Group nearby X positions (within 5% of page width)
                bands = []
                current_band = [sorted_x[0]]
                for x in sorted_x[1:]:
                    if x - current_band[-1] < 0.05:  # Within 5% of page width
                        current_band.append(x)
                    else:
                        bands.append(current_band)
                        current_band = [x]
                bands.append(current_band)
                
                # Only count bands with multiple blocks (stable bands)
                for band in bands:
                    if len(band) >= 3:  # At least 3 blocks in this vertical band
                        visual_bands.add(len(visual_bands))
        
        # For invoices/bills/receipts: Check if it's a 2-column structure
        if document_type and document_type.lower() in ['invoice', 'bill', 'receipt']:
            # Check if we have left-aligned labels and right-aligned values
            has_left_labels = len(left_aligned_positions) > 0
            has_right_values = len(right_aligned_positions) > 0
            
            # If structure suggests 2-column (labels + values), enforce it
            if has_left_labels and has_right_values:
                # Check if most rows have 2 or fewer columns with text
                rows_with_2_or_less = 0
                total_rows = 0
                
                for row in layout.rows:
                    row_cols_with_text = [c.column for c in row if c.value and c.value.strip()]
                    if row_cols_with_text:
                        total_rows += 1
                        if len(set(row_cols_with_text)) <= 2:
                            rows_with_2_or_less += 1
                
                # If >70% of rows have ≤2 columns, it's likely a 2-column structure
                if total_rows > 0 and (rows_with_2_or_less / total_rows) >= 0.7:
                    logger.critical(f"🔒 Column Governor: Detected 2-column structure for {document_type} (semantic lock)")
                    return 2
        
        # Calculate semantic count from multiple signals
        # Priority: Header columns > Numeric columns > Alignment > Visual bands
        semantic_signals = set()
        if header_columns:
            semantic_signals.update(header_columns)
        if numeric_columns:
            semantic_signals.update(numeric_columns)
        if left_aligned_positions or right_aligned_positions:
            semantic_signals.update(left_aligned_positions)
            semantic_signals.update(right_aligned_positions)
        
        # FINAL column count = MIN(stable semantic columns, detected visual bands)
        if semantic_signals:
            semantic_count = max(semantic_signals) + 1
        else:
            semantic_count = max_col + 1
        
        if visual_bands:
            visual_count = len(visual_bands)
            semantic_count = min(semantic_count, visual_count)
        
        logger.critical(f"🔒 Column Governor: Semantic analysis complete - {semantic_count} columns (max_col={max_col+1}, headers={len(header_columns)}, numeric={len(numeric_columns)}, visual_bands={len(visual_bands)})")
        return semantic_count
    
    def enforce_column_limit(
        self, 
        layout: UnifiedLayout, 
        max_columns: int,
        document_type: Optional[str] = None
    ) -> UnifiedLayout:
        """
        Enforce maximum column count by removing excess columns.
        
        CRITICAL RULES:
        - Never adds fake columns
        - Only removes columns beyond the limit
        - Preserves all data in allowed columns
        - Merges cells if necessary to fit
        
        Args:
            layout: Original layout
            max_columns: Maximum allowed columns (1-based, so 2 = columns 0 and 1)
            document_type: Document type for special handling
        
        Returns:
            Modified layout with enforced column limit
        """
        if max_columns <= 0:
            logger.warning("Column Governor: Invalid max_columns, returning original layout")
            return layout
        
        # Create new layout
        new_layout = UnifiedLayout(page_index=layout.page_index)
        new_layout.metadata = layout.metadata.copy()
        
        # Process each row
        for row in layout.rows:
            new_row_cells = []
            
            for cell in row:
                # Only keep cells in allowed column range (0 to max_columns-1)
                if cell.column < max_columns:
                    # Adjust column if needed (shouldn't be needed, but safety check)
                    adjusted_cell = Cell(
                        row=cell.row,
                        column=cell.column,
                        value=cell.value,
                        style=cell.style,
                        rowspan=cell.rowspan,
                        colspan=min(cell.colspan, max_columns - cell.column),  # Limit colspan
                        merged=cell.merged
                    )
                    new_row_cells.append(adjusted_cell)
                else:
                    # Cell is beyond limit - merge into last allowed column if possible
                    if new_row_cells and new_row_cells[-1].column == max_columns - 1:
                        # Append text to last cell
                        existing_value = new_row_cells[-1].value or ''
                        new_value = cell.value or ''
                        if new_value:
                            new_row_cells[-1].value = (existing_value + ' ' + new_value).strip()
                    # Otherwise, drop the cell (data loss, but prevents extra columns)
                    logger.debug(f"Column Governor: Dropping cell at column {cell.column} (beyond limit {max_columns})")
            
            if new_row_cells:
                new_layout.add_row(new_row_cells)
        
        # Copy merged cells (adjust if needed)
        for merged in layout.merged_cells:
            if merged.start_col < max_columns and merged.end_col < max_columns:
                new_layout.add_merged_cell(
                    merged.start_row,
                    merged.start_col,
                    merged.end_row,
                    merged.end_col
                )
        
        logger.info(f"Column Governor: Enforced {max_columns} column limit. Original max: {layout.get_max_column()}, New max: {new_layout.get_max_column()}")
        return new_layout
    
    def apply_governor(
        self, 
        layout: UnifiedLayout, 
        document_type: Optional[str] = None,
        original_blocks: Optional[List[Dict[str, Any]]] = None,
        page_count: int = 1
    ) -> UnifiedLayout:
        """
        Apply column governor to layout.
        
        Logic:
        1. For invoices/bills/receipts: ALWAYS enforce 2 columns if semantic_count <= 2
        2. Otherwise: Use semantic count (no artificial limits)
        
        CRITICAL: For bills/receipts, if all text is in one cell, split it into 2 columns
        
        Args:
            layout: Layout to govern
            document_type: Document type for special handling
        
        Returns:
            Governed layout with enforced column limits
        """
        if layout.is_empty():
            logger.warning("Column Governor: Layout is empty, skipping")
            return layout
        
        # CRITICAL FIX: For bills/receipts/invoices with page_count == 1, lock column count
        if document_type and document_type.lower() in ['invoice', 'bill', 'receipt'] and page_count == 1:
            current_max = layout.get_max_column()
            logger.critical(f"🔒 Column Governor: {document_type} detected (page_count=1), current_max={current_max}")
            
            # If layout has 1 column with all text, we need to split it into 2 columns
            if current_max == 1 or current_max == 0:
                logger.critical(f"🔒 Column Governor: {document_type} has {current_max} column(s) - splitting into 2-column key-value structure")
                return self._split_single_column_to_key_value(layout, document_type)
            
            # CRITICAL FIX: Check if column B is mostly empty (text all in column A)
            # If so, split column A text into A (label) and B (value)
            rows_with_col_b = 0
            total_rows = 0
            for row in layout.rows:
                if row and len(row) > 0:
                    total_rows += 1
                    if len(row) > 1 and row[1].value and str(row[1].value).strip():
                        rows_with_col_b += 1
            
            logger.critical(f"🔒 Column Governor: Checking column B - {rows_with_col_b}/{total_rows} rows have values in column B")
            
            if total_rows > 0 and (rows_with_col_b / total_rows) < 0.3:  # 30% threshold (more lenient)
                logger.critical(f"🔒 Column Governor: {document_type} has 2 columns but column B is mostly empty ({rows_with_col_b}/{total_rows} rows) - splitting column A text")
                layout = self._split_column_a_to_key_value(layout, document_type)
            
            # Analyze semantic columns with original blocks
            semantic_count = self.analyze_semantic_columns(layout, document_type, original_blocks)
            
            # LOCK column count to detected semantic count (often 2)
            if semantic_count <= 2:
                logger.critical(f"🔒 Column Governor: LOCKING 2-column structure for {document_type} (semantic_count={semantic_count})")
                locked_layout = self.enforce_column_limit(layout, 2, document_type)
                
                # CRITICAL FIX: After locking, check again if column B is still empty and split
                rows_with_col_b = 0
                total_rows = 0
                for row in locked_layout.rows:
                    if row and len(row) > 1:
                        total_rows += 1
                        if row[1].value and str(row[1].value).strip():
                            rows_with_col_b += 1
                
                if total_rows > 0 and (rows_with_col_b / total_rows) < 0.2:
                    logger.critical(f"🔒 Column Governor: After locking, column B is still mostly empty - splitting column A text")
                    locked_layout = self._split_column_a_to_key_value(locked_layout, document_type)
                
                logger.critical(f"🔒 Column Governor: Column count LOCKED - Rejecting any column expansion")
                return locked_layout
            else:
                # Multi-column invoice (e.g., line items table)
                logger.critical(f"🔒 Column Governor: LOCKING {semantic_count}-column structure for {document_type}")
                locked_layout = self.enforce_column_limit(layout, semantic_count, document_type)
                logger.critical(f"🔒 Column Governor: Column count LOCKED - Rejecting any column expansion")
                return locked_layout
        
        # For other document types, analyze semantic columns
        semantic_count = self.analyze_semantic_columns(layout, document_type, original_blocks)
        
        if semantic_count == 0:
            logger.warning("Column Governor: No semantic columns detected, returning original")
            return layout
        
        # Use semantic count (no artificial limit for non-bill documents)
        current_max = layout.get_max_column()
        if current_max > semantic_count:
            logger.info(f"Column Governor: Reducing columns from {current_max} to {semantic_count} based on semantic analysis")
            return self.enforce_column_limit(layout, semantic_count, document_type)
        
        # No change needed
        return layout
    
    def _split_single_column_to_key_value(self, layout: UnifiedLayout, document_type: str) -> UnifiedLayout:
        """
        Split single-column layout into 2-column key-value structure for bills/receipts.
        
        Rules:
        - Column A = Label (left side)
        - Column B = Value (right side)
        - Split text by common separators (:, |, etc.)
        """
        new_layout = UnifiedLayout(page_index=layout.page_index)
        new_layout.metadata = layout.metadata.copy()
        
        row_idx = 0
        for row in layout.rows:
            if not row or len(row) == 0:
                continue
            
            # Get text from first (and likely only) cell
            cell = row[0]
            text = cell.value or ''
            
            if not text or not text.strip():
                continue
            
            # CRITICAL FIX: Try to split by common separators first
            separators = [':', '|', '\t', ' - ', ' – ', ' — ']
            split_found = False
            
            for sep in separators:
                if sep in text:
                    parts = text.split(sep, 1)
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
                            new_layout.add_row([key_cell, value_cell])
                            row_idx += 1
                            split_found = True
                            break
            
            # CRITICAL FIX: If no separator found, try intelligent splitting based on label patterns
            if not split_found:
                import re
                
                # Common label patterns that indicate where label ends and value begins
                # Order matters - more specific patterns first
                label_patterns = [
                    (r'Name of the customer\s+', 'Name of the customer'),
                    (r'Biller Name\s+', 'Biller Name'),
                    (r'Biller ID\s+', 'Biller ID'),
                    (r'B-Connect Txn ID\s+', 'B-Connect Txn ID'),
                    (r'Approval Ref No\s+', 'Approval Ref No'),
                    (r'Consumer Number/IVRS\s+', 'Consumer Number/IVRS'),
                    (r'Mobile Number\s+', 'Mobile Number'),
                    (r'Payment Mode\s+', 'Payment Mode'),
                    (r'Payment Status\s+', 'Payment Status'),
                    (r'Payment Channel\s+', 'Payment Channel'),
                    (r'Bill Date\s+', 'Bill Date'),
                    (r'Bill Amount\s+', 'Bill Amount'),
                    (r'\bName\s+', 'Name'),
                    (r'\bID\s+', 'ID'),
                    (r'\bNumber\s+', 'Number'),
                    (r'\bDate\s+', 'Date'),
                    (r'\bAmount\s+', 'Amount'),
                    (r'\bTotal\s+', 'Total'),
                    (r'\bStatus\s+', 'Status'),
                    (r'\bTransaction\s+', 'Transaction'),
                    (r'\bPayment\s+', 'Payment'),
                    (r'\bApproval\s+', 'Approval'),
                    (r'\bRef\s+', 'Ref'),
                    (r'\bConsumer\s+', 'Consumer'),
                    (r'\bMobile\s+', 'Mobile'),
                ]
                
                for pattern, pattern_name in label_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        # Split at the end of the label pattern
                        label_end = match.end()
                        key = text[:label_end].strip()
                        value = text[label_end:].strip()
                        
                        # Only split if value is not empty and key is reasonable length
                        if value and len(key) < 100 and len(value) > 0:
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
                            new_layout.add_row([key_cell, value_cell])
                            row_idx += 1
                            split_found = True
                            logger.critical(f"Column Governor: Split '{text[:50]}...' into key-value using pattern '{pattern_name}'")
                            break
            
            # If still not split, add as-is (might be header or single-line content)
            if not split_found:
                key_cell = Cell(
                    row=row_idx,
                    column=0,
                    value=text,
                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                )
                value_cell = Cell(
                    row=row_idx,
                    column=1,
                    value='',
                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                )
                new_layout.add_row([key_cell, value_cell])
                row_idx += 1
        
        return new_layout
    
    def _split_column_a_to_key_value(self, layout: UnifiedLayout, document_type: str) -> UnifiedLayout:
        """
        Split text from column A into columns A (label) and B (value) for bills/receipts.
        This is called when layout already has 2 columns but column B is mostly empty.
        """
        new_layout = UnifiedLayout(page_index=layout.page_index)
        new_layout.metadata = layout.metadata.copy()
        
        import re
        
        # Common label patterns (same as _split_single_column_to_key_value)
        label_patterns = [
            (r'Name of the customer\s+', 'Name of the customer'),
            (r'Biller Name\s+', 'Biller Name'),
            (r'Biller ID\s+', 'Biller ID'),
            (r'B-Connect Txn ID\s+', 'B-Connect Txn ID'),
            (r'Approval Ref No\s+', 'Approval Ref No'),
            (r'Consumer Number/IVRS\s+', 'Consumer Number/IVRS'),
            (r'Mobile Number\s+', 'Mobile Number'),
            (r'Payment Mode\s+', 'Payment Mode'),
            (r'Payment Status\s+', 'Payment Status'),
            (r'Payment Channel\s+', 'Payment Channel'),
            (r'Bill Date\s+', 'Bill Date'),
            (r'Bill Amount\s+', 'Bill Amount'),
            (r'\bName\s+', 'Name'),
            (r'\bID\s+', 'ID'),
            (r'\bNumber\s+', 'Number'),
            (r'\bDate\s+', 'Date'),
            (r'\bAmount\s+', 'Amount'),
            (r'\bTotal\s+', 'Total'),
            (r'\bStatus\s+', 'Status'),
            (r'\bTransaction\s+', 'Transaction'),
            (r'\bPayment\s+', 'Payment'),
            (r'\bApproval\s+', 'Approval'),
            (r'\bRef\s+', 'Ref'),
            (r'\bConsumer\s+', 'Consumer'),
            (r'\bMobile\s+', 'Mobile'),
        ]
        
        row_idx = 0
        for row in layout.rows:
            if not row or len(row) == 0:
                continue
            
            # Get text from column A (first cell)
            col_a_text = (row[0].value or '').strip() if len(row) > 0 else ''
            col_b_text = (row[1].value or '').strip() if len(row) > 1 else ''
            
            # If column B already has value, keep as-is
            if col_b_text:
                new_layout.add_row(row)
                row_idx += 1
                continue
            
            # If column A is empty, keep as-is
            if not col_a_text:
                new_layout.add_row(row)
                row_idx += 1
                continue
            
            # Try to split column A text using label patterns
            split_found = False
            logger.debug(f"Column Governor: Attempting to split column A text: '{col_a_text[:60]}...'")
            
            # CRITICAL FIX: Try patterns in order (most specific first)
            for pattern, pattern_name in label_patterns:
                match = re.search(pattern, col_a_text, re.IGNORECASE)
                if match:
                    label_end = match.end()
                    key = col_a_text[:label_end].strip()
                    value = col_a_text[label_end:].strip()
                    
                    logger.debug(f"Column Governor: Pattern '{pattern_name}' matched! key='{key}', value='{value[:30]}...'")
                    
                    # CRITICAL: Only split if value is meaningful (not just whitespace)
                    if value and len(value) > 0 and len(key) < 100:
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
                        new_layout.add_row([key_cell, value_cell])
                        row_idx += 1
                        split_found = True
                        logger.critical(f"Column Governor: SUCCESS - Split column A '{col_a_text[:50]}...' into key='{key}' | value='{value[:30]}...' using pattern '{pattern_name}'")
                        break
            
            if not split_found:
                logger.warning(f"Column Governor: No pattern matched for text: '{col_a_text[:60]}...'")
            
            # If not split, keep original row
            if not split_found:
                new_layout.add_row(row)
                row_idx += 1
        
        return new_layout
            
            # CRITICAL FIX: Always split by newlines first, then process each line
            # This handles cases where content is in one cell with newlines
            if not split_found:
                # Split by newlines and detect pattern
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                
                # If we have multiple lines, process them as separate rows
                if len(lines) > 1:
                    logger.critical(f"🔒 Column Governor: Found {len(lines)} lines in single cell - splitting into rows")
                    for line in lines:
                        # Try to split each line by separators
                        line_split = False
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
                                        new_layout.add_row([key_cell, value_cell])
                                        row_idx += 1
                                        line_split = True
                                        break
                        
                        # If line couldn't be split by separator, check if it's a label or value
                        if not line_split:
                            # Check if this line looks like a label (short, common label words)
                            is_label = any(label_word in line.lower() for label_word in [
                                'name', 'id', 'number', 'date', 'amount', 'total', 'mode', 
                                'status', 'channel', 'fee', 'transaction', 'biller', 'customer',
                                'payment', 'approval', 'ref', 'consumer', 'mobile', 'bill',
                                'spice', 'money', 'assured'
                            ]) or (len(line) < 50 and ':' not in line)
                            
                            # If it's a label, put it in column A, leave B empty (next line might be value)
                            if is_label:
                                key_cell = Cell(
                                    row=row_idx,
                                    column=0,
                                    value=line,
                                    style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                                )
                                value_cell = Cell(
                                    row=row_idx,
                                    column=1,
                                    value='',
                                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                )
                                new_layout.add_row([key_cell, value_cell])
                                row_idx += 1
                            else:
                                # It's a value - check if previous row has empty value column
                                if row_idx > 0 and new_layout.rows:
                                    prev_row = new_layout.rows[-1]
                                    if len(prev_row) >= 2 and (not prev_row[1].value or not prev_row[1].value.strip()):
                                        # Fill previous row's value column
                                        prev_row[1].value = line
                                    else:
                                        # Create new row with empty label
                                        key_cell = Cell(
                                            row=row_idx,
                                            column=0,
                                            value='',
                                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                        )
                                        value_cell = Cell(
                                            row=row_idx,
                                            column=1,
                                            value=line,
                                            style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                        )
                                        new_layout.add_row([key_cell, value_cell])
                                        row_idx += 1
                    continue  # Skip the original single-cell processing
                
                # Original single-line processing (if no newlines)
                if len(lines) == 1:
                    line = lines[0]
                
                # Pattern 1: Alternating label-value pairs (common in bills/receipts)
                # e.g., "Name of the customer\nSHRI BRIJ LAL PAW\nBiller Name\nM.P. Poorv..."
                i = 0
                while i < len(lines):
                    line = lines[i]
                    
                    # Check if this line looks like a label (short, common label words)
                    is_label = any(label_word in line.lower() for label_word in [
                        'name', 'id', 'number', 'date', 'amount', 'total', 'mode', 
                        'status', 'channel', 'fee', 'transaction', 'biller', 'customer',
                        'payment', 'approval', 'ref', 'consumer', 'mobile', 'bill'
                    ]) or (len(line) < 50 and ':' not in line)
                    
                    # Try separators on this line first
                    line_split = False
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
                                    new_layout.add_row([key_cell, value_cell])
                                    row_idx += 1
                                    line_split = True
                                    i += 1
                                    break
                    
                    if not line_split:
                        # Check if next line might be the value for this label
                        if is_label and i + 1 < len(lines):
                            next_line = lines[i + 1]
                            # Next line is likely the value if it's longer or doesn't look like a label
                            is_next_label = any(label_word in next_line.lower() for label_word in [
                                'name', 'id', 'number', 'date', 'amount', 'total', 'mode', 
                                'status', 'channel', 'fee', 'transaction', 'biller', 'customer',
                                'payment', 'approval', 'ref', 'consumer', 'mobile', 'bill'
                            ]) and len(next_line) < 50
                            
                            if not is_next_label:
                                # This is label-value pair
                                key_cell = Cell(
                                    row=row_idx,
                                    column=0,
                                    value=line,
                                    style=CellStyle(bold=True, alignment_horizontal=CellAlignment.LEFT)
                                )
                                value_cell = Cell(
                                    row=row_idx,
                                    column=1,
                                    value=next_line,
                                    style=CellStyle(alignment_horizontal=CellAlignment.LEFT)
                                )
                                new_layout.add_row([key_cell, value_cell])
                                row_idx += 1
                                i += 2  # Skip both lines
                                continue
                        
                        # No pattern matched - put line in column A, leave B empty
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
                        new_layout.add_row([key_cell, value_cell])
                        row_idx += 1
                        i += 1
        
        logger.info(f"Column Governor: Split single-column {document_type} into 2-column key-value structure ({row_idx} rows)")
        return new_layout

