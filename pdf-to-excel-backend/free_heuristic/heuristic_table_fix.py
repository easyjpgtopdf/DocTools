"""
Heuristic Table Fix for FREE PDF to Excel Pipeline.
Fixes collapsed rows, misaligned label-value pairs, missing row breaks.

Works ONLY on Excel cell content (no PDF parsing).
CPU-only, O(n log n) complexity.
"""

import logging
from typing import List, Dict, Tuple, Optional
import copy

logger = logging.getLogger(__name__)

try:
    import openpyxl
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    logger.warning("openpyxl not available for heuristic table fix")


def fix_table_layout(excel_path: str) -> bool:
    """
    Apply heuristic fixes to Excel table layout.
    
    Args:
        excel_path: Path to Excel file (modified in-place)
        
    Returns:
        True if fixes were applied, False otherwise
    """
    if not HAS_OPENPYXL:
        return False
    
    try:
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
        
        # Read all cell values into memory (O(n))
        rows_data = []
        max_row = ws.max_row
        max_col = ws.max_column
        
        for row_idx in range(1, max_row + 1):
            row_data = []
            for col_idx in range(1, max_col + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                value = cell.value
                row_data.append({
                    'value': str(value) if value is not None else '',
                    'row': row_idx,
                    'col': col_idx,
                    'cell': cell
                })
            rows_data.append(row_data)
        
        # Apply heuristic fixes
        fixed_rows = apply_heuristic_fixes(rows_data)
        
        if fixed_rows == rows_data:
            # No changes made
            return False
        
        # Write fixed data back to Excel
        # Clear existing content
        for row_idx in range(1, max_row + 1):
            for col_idx in range(1, max_col + 1):
                ws.cell(row=row_idx, column=col_idx).value = None
        
        # Write fixed content
        for row_data in fixed_rows:
            for cell_data in row_data:
                if cell_data['value']:
                    ws.cell(row=cell_data['row'], column=cell_data['col']).value = cell_data['value']
        
        wb.save(excel_path)
        logger.info("Heuristic table fixes applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error applying heuristic table fixes: {e}")
        return False


def apply_heuristic_fixes(rows_data: List[List[Dict]]) -> List[List[Dict]]:
    """
    Apply heuristic fixes to row data.
    
    Args:
        rows_data: List of rows, each row is a list of cell dictionaries
        
    Returns:
        Fixed rows data (new list, original unchanged)
    """
    if not rows_data:
        return rows_data
    
    # Create a copy to avoid modifying original
    fixed_rows = copy.deepcopy(rows_data)
    
    # Fix 1: Detect and split collapsed rows (rows with too much content in one cell)
    fixed_rows = fix_collapsed_rows(fixed_rows)
    
    # Fix 2: Detect and align label-value pairs (patterns like "Label: Value")
    fixed_rows = fix_label_value_pairs(fixed_rows)
    
    # Fix 3: Add missing row breaks (detect multi-line content that should be separate rows)
    fixed_rows = fix_missing_row_breaks(fixed_rows)
    
    return fixed_rows


def fix_collapsed_rows(rows_data: List[List[Dict]]) -> List[List[Dict]]:
    """
    Fix collapsed rows where multiple logical rows are in one physical row.
    
    Strategy: If a cell has multiple sentences or line breaks, split it.
    """
    fixed_rows = []
    
    for row_data in rows_data:
        # Check if any cell has multiple sentences (indicated by periods or line breaks)
        needs_split = False
        for cell_data in row_data:
            value = cell_data['value']
            if value and (value.count('.') > 2 or '\n' in value or '  ' in value):
                needs_split = True
                break
        
        if needs_split:
            # Try to split the row
            split_rows = split_row_by_content(row_data)
            fixed_rows.extend(split_rows)
        else:
            fixed_rows.append(row_data)
    
    return fixed_rows


def split_row_by_content(row_data: List[Dict]) -> List[List[Dict]]:
    """
    Split a row into multiple rows based on content patterns.
    
    Returns:
        List of row data (each is a list of cell dictionaries)
    """
    if not row_data:
        return [row_data]
    
    # Find the cell with the most content
    max_len = 0
    max_idx = 0
    for idx, cell_data in enumerate(row_data):
        if len(cell_data['value']) > max_len:
            max_len = len(cell_data['value'])
            max_idx = idx
    
    # If the max cell has line breaks, split by line breaks
    max_cell = row_data[max_idx]
    value = max_cell['value']
    
    if '\n' in value:
        lines = value.split('\n')
        split_rows = []
        for line_idx, line in enumerate(lines):
            if line.strip():
                new_row = copy.deepcopy(row_data)
                new_row[max_idx]['value'] = line.strip()
                # Clear other cells in this row (keep only the split content)
                for cell_idx, cell_data in enumerate(new_row):
                    if cell_idx != max_idx:
                        cell_data['value'] = ''
                split_rows.append(new_row)
        return split_rows if split_rows else [row_data]
    
    # If the max cell has multiple sentences, try to split by periods
    if value.count('.') > 2:
        sentences = [s.strip() + '.' for s in value.split('.') if s.strip()]
        if len(sentences) > 1:
            split_rows = []
            for sent in sentences:
                new_row = copy.deepcopy(row_data)
                new_row[max_idx]['value'] = sent
                for cell_idx, cell_data in enumerate(new_row):
                    if cell_idx != max_idx:
                        cell_data['value'] = ''
                split_rows.append(new_row)
            return split_rows if split_rows else [row_data]
    
    return [row_data]


def fix_label_value_pairs(rows_data: List[List[Dict]]) -> List[List[Dict]]:
    """
    Fix misaligned label-value pairs.
    
    Strategy: Detect "Label: Value" patterns and ensure they're in separate columns.
    """
    fixed_rows = []
    
    for row_data in rows_data:
        # Check if any cell contains ":" pattern (label: value)
        has_colon_pattern = False
        colon_cell_idx = -1
        
        for idx, cell_data in enumerate(row_data):
            value = cell_data['value']
            if ':' in value and len(value.split(':')) == 2:
                parts = value.split(':')
                if len(parts[0].strip()) > 0 and len(parts[1].strip()) > 0:
                    has_colon_pattern = True
                    colon_cell_idx = idx
                    break
        
        if has_colon_pattern and colon_cell_idx >= 0:
            # Split label and value into separate columns
            cell_data = row_data[colon_cell_idx]
            value = cell_data['value']
            label, value_part = value.split(':', 1)
            label = label.strip()
            value_part = value_part.strip()
            
            # Create new row with label and value in adjacent columns
            new_row = copy.deepcopy(row_data)
            new_row[colon_cell_idx]['value'] = label
            
            # Put value in next column if available
            if colon_cell_idx + 1 < len(new_row):
                new_row[colon_cell_idx + 1]['value'] = value_part
            else:
                # Add a new column (extend row)
                new_cell = {
                    'value': value_part,
                    'row': cell_data['row'],
                    'col': cell_data['col'] + 1,
                    'cell': None  # Will be created when writing back
                }
                new_row.append(new_cell)
            
            fixed_rows.append(new_row)
        else:
            fixed_rows.append(row_data)
    
    return fixed_rows


def fix_missing_row_breaks(rows_data: List[List[Dict]]) -> List[List[Dict]]:
    """
    Fix missing row breaks where content should be on separate rows.
    
    Strategy: Detect cells with multiple distinct pieces of information.
    """
    fixed_rows = []
    
    for row_data in rows_data:
        # Check for cells with multiple distinct values (separated by common delimiters)
        needs_break = False
        
        for cell_data in row_data:
            value = cell_data['value']
            if not value:
                continue
            
            # Check for multiple distinct pieces (separated by |, ;, or multiple spaces)
            if '|' in value:
                parts = [p.strip() for p in value.split('|') if p.strip()]
                if len(parts) > 1:
                    needs_break = True
                    break
            elif ';' in value:
                parts = [p.strip() for p in value.split(';') if p.strip()]
                if len(parts) > 1:
                    needs_break = True
                    break
        
        if needs_break:
            # Split into multiple rows
            split_rows = split_row_by_delimiters(row_data)
            fixed_rows.extend(split_rows)
        else:
            fixed_rows.append(row_data)
    
    return fixed_rows


def split_row_by_delimiters(row_data: List[List[Dict]]) -> List[List[Dict]]:
    """
    Split a row by delimiter-separated values.
    """
    if not row_data:
        return [row_data]
    
    # Find cell with delimiter
    delimiter = None
    delimiter_idx = -1
    
    for idx, cell_data in enumerate(row_data):
        value = cell_data['value']
        if '|' in value:
            delimiter = '|'
            delimiter_idx = idx
            break
        elif ';' in value:
            delimiter = ';'
            delimiter_idx = idx
            break
    
    if delimiter_idx < 0:
        return [row_data]
    
    # Split the cell value
    cell_data = row_data[delimiter_idx]
    value = cell_data['value']
    parts = [p.strip() for p in value.split(delimiter) if p.strip()]
    
    if len(parts) <= 1:
        return [row_data]
    
    # Create separate rows for each part
    split_rows = []
    for part in parts:
        new_row = copy.deepcopy(row_data)
        new_row[delimiter_idx]['value'] = part
        # Clear other cells
        for cell_idx, cell_data in enumerate(new_row):
            if cell_idx != delimiter_idx:
                cell_data['value'] = ''
        split_rows.append(new_row)
    
    return split_rows if split_rows else [row_data]

