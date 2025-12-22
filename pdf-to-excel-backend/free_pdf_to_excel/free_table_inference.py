"""
Table Grid Inference for FREE version.
Builds grid from line intersections and snaps text to cells.
CPU-only, controlled inference (no aggressive guessing).
"""

import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


def detect_table_grid(
    lines: List[Dict],
    rectangles: List[Dict],
    text_objects: List[Dict],
    page_width: float,
    page_height: float
) -> Tuple[List[float], List[float], float]:
    """
    Detect table grid from lines and rectangles.
    One-pass + light cleanup.
    
    Args:
        lines: List of line objects
        rectangles: List of rectangle objects
        text_objects: List of text objects
        page_width: Page width in points
        page_height: Page height in points
        
    Returns:
        (column_boundaries, row_boundaries, confidence)
        confidence: 0.0 to 1.0
    """
    # Extract horizontal and vertical lines
    horizontal_lines = [l for l in lines if l.get('is_horizontal', False)]
    vertical_lines = [l for l in lines if l.get('is_vertical', False)]
    
    # Find column boundaries from vertical lines
    column_xs = set()
    for line in vertical_lines:
        # Use midpoint or start/end points
        x0, x1 = line['x0'], line['x1']
        column_xs.add((x0 + x1) / 2)
        column_xs.add(x0)
        column_xs.add(x1)
    
    # Find row boundaries from horizontal lines
    row_ys = set()
    for line in horizontal_lines:
        y0, y1 = line['y0'], line['y1']
        row_ys.add((y0 + y1) / 2)
        row_ys.add(y0)
        row_ys.add(y1)
    
    # If no lines, try rectangles
    if not column_xs and rectangles:
        for rect in rectangles:
            column_xs.add(rect['x0'])
            column_xs.add(rect['x1'])
            row_ys.add(rect['y0'])
            row_ys.add(rect['y1'])
    
    # If still no boundaries, infer from text positions
    if not column_xs and text_objects:
        # Cluster X positions
        x_positions = sorted(set([obj['x'] for obj in text_objects]))
        column_xs = set()
        for x in x_positions:
            # Only add if not too close to existing
            if not column_xs or min(abs(x - cx) for cx in column_xs) > 30:
                column_xs.add(x)
    
    if not row_ys and text_objects:
        # Cluster Y positions
        y_positions = sorted(set([obj['y'] for obj in text_objects]), reverse=True)
        row_ys = set()
        for y in y_positions:
            if not row_ys or min(abs(y - ry) for ry in row_ys) > 10:
                row_ys.add(y)
    
    # Sort boundaries
    column_boundaries = sorted(column_xs) if column_xs else []
    row_boundaries = sorted(row_ys, reverse=True) if row_ys else []  # Top to bottom
    
    # Calculate confidence based on line count and text alignment
    line_count = len(horizontal_lines) + len(vertical_lines)
    text_alignment_score = 0.0
    
    if text_objects and column_boundaries and row_boundaries:
        # Check how many text objects align with grid
        aligned_count = 0
        for obj in text_objects:
            # Find nearest column
            nearest_col = min(column_boundaries, key=lambda cx: abs(cx - obj['x']))
            nearest_row = min(row_boundaries, key=lambda ry: abs(ry - obj['y']))
            
            if abs(nearest_col - obj['x']) < 50 and abs(nearest_row - obj['y']) < 20:
                aligned_count += 1
        
        text_alignment_score = aligned_count / len(text_objects) if text_objects else 0.0
    
    # Combined confidence
    line_confidence = min(line_count / 10.0, 1.0) if line_count > 0 else 0.0
    confidence = (line_confidence * 0.6 + text_alignment_score * 0.4)
    
    return column_boundaries, row_boundaries, confidence


def snap_text_to_grid(
    text_objects: List[Dict],
    column_boundaries: List[float],
    row_boundaries: List[float]
) -> List[List[Dict]]:
    """
    Snap text objects to grid cells.
    Allows simple merged cells.
    
    Args:
        text_objects: List of text objects
        column_boundaries: List of X coordinates for columns
        row_boundaries: List of Y coordinates for rows
        
    Returns:
        2D grid: grid[row][col] = cell content
    """
    if not column_boundaries or not row_boundaries:
        return []
    
    # Initialize grid
    grid = []
    for _ in row_boundaries:
        row = []
        for _ in column_boundaries:
            row.append({
                'text': '',
                'font_name': 'Arial',
                'font_size': 10,
                'is_bold': False,
                'merged': False
            })
        grid.append(row)
    
    # Snap each text object to nearest cell
    for obj in text_objects:
        # Find closest column
        col_idx = 0
        min_col_dist = float('inf')
        for i, col_x in enumerate(column_boundaries):
            dist = abs(obj['x'] - col_x)
            if dist < min_col_dist:
                min_col_dist = dist
                col_idx = i
        
        # Find closest row
        row_idx = 0
        min_row_dist = float('inf')
        for i, row_y in enumerate(row_boundaries):
            dist = abs(obj['y'] - row_y)
            if dist < min_row_dist:
                min_row_dist = dist
                row_idx = i
        
        # Assign to cell (merge if already has text)
        if row_idx < len(grid) and col_idx < len(grid[row_idx]):
            cell = grid[row_idx][col_idx]
            if cell['text']:
                cell['text'] += ' ' + obj['text']
            else:
                cell['text'] = obj['text']
                cell['font_name'] = obj.get('font_name', 'Arial')
                cell['font_size'] = obj.get('font_size', 10)
                cell['is_bold'] = obj.get('is_bold', False)
    
    # Detect simple merged cells (adjacent cells with same content)
    # This is a light cleanup pass
    for row_idx, row in enumerate(grid):
        for col_idx, cell in enumerate(row):
            if not cell['text']:
                continue
            
            # Check if this cell should be merged with left neighbor
            if col_idx > 0:
                left_cell = row[col_idx - 1]
                if left_cell['text'] == cell['text']:
                    # Merge: keep text in left cell, mark right as merged
                    left_cell['merged'] = True
                    cell['text'] = ''
                    cell['merged'] = True
    
    return grid


def detect_header_rows(
    grid: List[List[Dict]],
    rectangles: List[Dict],
    row_boundaries: List[float]
) -> List[int]:
    """
    Detect header rows (usually first row, or rows with background rectangles).
    
    Args:
        grid: 2D grid of cells
        rectangles: List of rectangle objects
        row_boundaries: List of Y coordinates for rows
        
    Returns:
        List of row indices that are headers
    """
    header_rows = []
    
    if not grid:
        return header_rows
    
    # First row is often header
    header_rows.append(0)
    
    # Check if rectangles align with first row
    if rectangles and row_boundaries:
        first_row_y = row_boundaries[0] if row_boundaries else 0
        for rect in rectangles:
            # Check if rectangle aligns with first row (within 20 points)
            if abs(rect['y0'] - first_row_y) < 20 or abs(rect['y1'] - first_row_y) < 20:
                if 0 not in header_rows:
                    header_rows.append(0)
                break
    
    return header_rows

