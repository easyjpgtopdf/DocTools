"""
Cell Value Splitter
Splits text in a single cell that contains multiple values into separate columns.
Used for cases like "502702 30-01-2019 20:50 1922021539 '1111" which should be in separate columns.
"""

import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class CellValueSplitter:
    """
    Intelligently splits cell values that contain multiple distinct values.
    Detects patterns like:
    - Numbers separated by spaces
    - Dates
    - IDs
    - Mixed alphanumeric values
    """
    
    def __init__(self):
        # Patterns to detect distinct values
        self.value_patterns = [
            r'\d{4,}',  # 4+ digit numbers (years, IDs)
            r'\d{2}-\d{2}-\d{4}',  # Dates (DD-MM-YYYY)
            r'\d{2}:\d{2}',  # Time (HH:MM)
            r"'[^']*'",  # Quoted strings
            r'[A-Z]{2}\d{2}[A-Z]{2}\d{4}',  # Vehicle numbers (e.g., MP09GG6879)
            r'\d+\.\d+',  # Decimal numbers
        ]
    
    def should_split(self, text: str) -> bool:
        """
        Determine if a cell value should be split into multiple columns.
        
        Criteria:
        - Contains multiple distinct patterns (numbers, dates, IDs)
        - Has multiple space-separated values that look like different data types
        - Length > 30 characters (likely contains multiple values)
        """
        if not text or len(text.strip()) < 30:
            return False
        
        # Count distinct value patterns
        pattern_count = 0
        for pattern in self.value_patterns:
            matches = re.findall(pattern, text)
            if matches:
                pattern_count += len(matches)
        
        # If we have 3+ distinct patterns, likely multiple values
        if pattern_count >= 3:
            return True
        
        # Check for multiple space-separated tokens that look like different data types
        tokens = text.split()
        if len(tokens) >= 4:
            # Check if tokens have different patterns (numbers, dates, text)
            has_numbers = any(re.match(r'^\d+', t) for t in tokens)
            has_dates = any(re.match(r'\d{2}-\d{2}-\d{4}', t) for t in tokens)
            has_text = any(not re.match(r'^\d', t) and not re.match(r'\d{2}-\d{2}-\d{4}', t) for t in tokens)
            
            if (has_numbers and has_dates) or (has_numbers and has_text and len(tokens) >= 5):
                return True
        
        return False
    
    def split_value(self, text: str, max_columns: int = 10) -> List[str]:
        """
        Split a cell value into multiple values based on patterns.
        
        Returns:
            List of split values (will be placed in separate columns)
        """
        if not self.should_split(text):
            return [text]
        
        # Strategy: Split by detecting boundaries between different value types
        # 1. Split by quoted strings first (they're usually complete values)
        parts = []
        current_pos = 0
        
        # Find quoted strings
        quoted_matches = list(re.finditer(r"'[^']*'", text))
        
        if quoted_matches:
            for match in quoted_matches:
                # Add text before quote
                before = text[current_pos:match.start()].strip()
                if before:
                    parts.append(before)
                # Add quoted string
                parts.append(match.group())
                current_pos = match.end()
            
            # Add remaining text
            remaining = text[current_pos:].strip()
            if remaining:
                parts.append(remaining)
        else:
            # No quoted strings - split by detecting value boundaries
            # Look for transitions: number->date, date->number, number->text, etc.
            tokens = text.split()
            parts = []
            current_group = []
            
            for i, token in enumerate(tokens):
                current_group.append(token)
                
                # Check if next token is a different type (boundary)
                if i < len(tokens) - 1:
                    next_token = tokens[i + 1]
                    current_type = self._get_token_type(token)
                    next_type = self._get_token_type(next_token)
                    
                    # If type changes significantly, end current group
                    if current_type != next_type and current_type != 'mixed' and next_type != 'mixed':
                        parts.append(' '.join(current_group))
                        current_group = []
            
            # Add last group
            if current_group:
                parts.append(' '.join(current_group))
        
        # Limit to max_columns
        if len(parts) > max_columns:
            # Merge excess parts into last column
            merged = parts[:max_columns - 1]
            merged.append(' '.join(parts[max_columns - 1:]))
            parts = merged
        
        logger.debug(f"CellValueSplitter: Split '{text[:50]}...' into {len(parts)} parts: {[p[:30] for p in parts]}")
        return parts
    
    def _get_token_type(self, token: str) -> str:
        """Classify token type: number, date, time, text, mixed"""
        if re.match(r'^\d{2}-\d{2}-\d{4}$', token):
            return 'date'
        elif re.match(r'^\d{2}:\d{2}$', token):
            return 'time'
        elif re.match(r'^\d+$', token):
            return 'number'
        elif re.match(r'^\d+\.\d+$', token):
            return 'decimal'
        elif re.match(r"'[^']*'", token):
            return 'quoted'
        elif re.match(r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$', token):
            return 'vehicle'
        elif re.match(r'^\d', token):
            return 'mixed'
        else:
            return 'text'


def apply_cell_splitting(layout, max_columns_per_row: int = 10):
    """
    Apply cell value splitting to a layout.
    Splits cells that contain multiple values into separate columns.
    
    Args:
        layout: UnifiedLayout to process
        max_columns_per_row: Maximum columns to create per row
    
    Returns:
        Modified layout with split cells
    """
    from .unified_layout_model import UnifiedLayout, Cell, CellStyle, CellAlignment
    
    splitter = CellValueSplitter()
    new_layout = UnifiedLayout(page_index=layout.page_index)
    new_layout.metadata = layout.metadata.copy()
    
    max_cols_needed = 0
    
    # First pass: identify rows that need splitting
    rows_to_split = []
    for row_idx, row in enumerate(layout.rows):
        if not row:
            continue
        
        row_needs_splitting = False
        split_parts_per_cell = []
        
        for cell in row:
            text = str(cell.value or '').strip()
            if text and splitter.should_split(text):
                parts = splitter.split_value(text, max_columns_per_row)
                split_parts_per_cell.append(parts)
                row_needs_splitting = True
                max_cols_needed = max(max_cols_needed, len(parts))
            else:
                split_parts_per_cell.append([text])
        
        rows_to_split.append((row_idx, row, row_needs_splitting, split_parts_per_cell))
    
    if max_cols_needed == 0:
        # No splitting needed
        return layout
    
    logger.critical(f"CellValueSplitter: Splitting {sum(1 for _, _, needs, _ in rows_to_split if needs)} rows, max columns needed: {max_cols_needed}")
    
    # Second pass: create new rows with split cells
    for row_idx, original_row, needs_splitting, split_parts in rows_to_split:
        if not needs_splitting:
            # Keep original row
            new_layout.add_row(original_row)
            continue
        
        # Create new row with split cells
        new_cells = []
        max_parts = max(len(parts) for parts in split_parts)
        
        # Ensure all cells have same number of parts (pad with empty)
        for parts in split_parts:
            while len(parts) < max_parts:
                parts.append('')
        
        # Create cells column by column
        for col_idx in range(max_parts):
            # Find which original cell this part came from
            cell_value = ''
            cell_style = None
            
            for cell_idx, parts in enumerate(split_parts):
                if col_idx < len(parts):
                    if parts[col_idx]:
                        cell_value = parts[col_idx]
                        # Use style from original cell if available
                        if cell_idx < len(original_row):
                            cell_style = original_row[cell_idx].style
                        break
            
            if not cell_style:
                cell_style = CellStyle(alignment_horizontal=CellAlignment.LEFT)
            
            new_cell = Cell(
                row=row_idx,
                column=col_idx,
                value=cell_value,
                style=cell_style
            )
            new_cells.append(new_cell)
        
        new_layout.add_row(new_cells)
    
    logger.critical(f"CellValueSplitter: Layout modified - original max_col={layout.get_max_column()}, new max_col={new_layout.get_max_column()}")
    return new_layout

