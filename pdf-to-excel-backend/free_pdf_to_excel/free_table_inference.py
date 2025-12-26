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
    
    # If still no boundaries, infer from text positions (IMPROVED)
    if not column_xs and text_objects:
        # IMPROVED: Use text bounding boxes for better column detection
        # Collect all X positions (start and end of text)
        all_x_positions = []
        for obj in text_objects:
            x_start = obj.get('x', 0)
            x_end = x_start + obj.get('width', 0)
            all_x_positions.append(x_start)
            all_x_positions.append(x_end)
        
        # Sort and cluster X positions
        x_positions = sorted(set(all_x_positions))
        column_xs = set()
        
        # Use adaptive threshold based on page width
        threshold = max(20, page_width * 0.02)  # 2% of page width or 20 points, whichever is larger
        
        for x in x_positions:
            # Only add if not too close to existing column
            if not column_xs or min(abs(x - cx) for cx in column_xs) > threshold:
                column_xs.add(x)
        
        # Also add page edges if needed
        if column_xs:
            # Ensure we have left and right boundaries
            min_x = min(column_xs)
            max_x = max(column_xs)
            if min_x > 50:  # If no column near left edge
                column_xs.add(0)
            if max_x < page_width - 50:  # If no column near right edge
                column_xs.add(page_width)
    
    if not row_ys and text_objects:
        # IMPROVED: Use text bounding boxes for better row detection
        # Collect all Y positions (top and bottom of text)
        all_y_positions = []
        for obj in text_objects:
            y_top = obj.get('y', 0)
            y_bottom = y_top + obj.get('height', 0)
            all_y_positions.append(y_top)
            all_y_positions.append(y_bottom)
        
        # Sort Y positions (top to bottom - reverse order)
        y_positions = sorted(set(all_y_positions), reverse=True)
        row_ys = set()
        
        # Use adaptive threshold based on text height
        avg_text_height = sum(obj.get('height', 10) for obj in text_objects) / max(len(text_objects), 1)
        threshold = max(5, avg_text_height * 0.3)  # 30% of average text height or 5 points
        
        for y in y_positions:
            if not row_ys or min(abs(y - ry) for ry in row_ys) > threshold:
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
            # Find nearest column (with safety check)
            if column_boundaries and row_boundaries:
                try:
                    nearest_col = min(column_boundaries, key=lambda cx: abs(cx - obj['x']))
                    nearest_row = min(row_boundaries, key=lambda ry: abs(ry - obj['y']))
                    
                    if abs(nearest_col - obj['x']) < 50 and abs(nearest_row - obj['y']) < 20:
                        aligned_count += 1
                except (ValueError, KeyError):
                    # Skip if boundaries are invalid
                    continue
        
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
    if not column_boundaries or not row_boundaries or len(column_boundaries) == 0 or len(row_boundaries) == 0:
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
    
    # IMPROVED: Snap each text object to nearest cell using bounding box
    for obj in text_objects:
        # Get text bounding box
        text_x = obj.get('x', 0)
        text_y = obj.get('y', 0)
        text_width = obj.get('width', 0)
        text_height = obj.get('height', 0)
        
        # Use center of text bounding box for better alignment
        text_center_x = text_x + (text_width / 2)
        text_center_y = text_y + (text_height / 2)
        
        # Find closest column - use text start position (left edge)
        col_idx = 0
        min_col_dist = float('inf')
        for i, col_x in enumerate(column_boundaries):
            # Check distance from text start to column boundary
            dist = abs(text_x - col_x)
            if dist < min_col_dist:
                min_col_dist = dist
                col_idx = i
        
        # If text spans multiple columns, check if center is closer to next column
        if col_idx + 1 < len(column_boundaries):
            next_col_x = column_boundaries[col_idx + 1]
            current_col_x = column_boundaries[col_idx]
            
            # If text center is closer to next column, use next column
            if abs(text_center_x - next_col_x) < abs(text_center_x - current_col_x):
                # But only if text doesn't start before current column
                if text_x >= current_col_x:
                    col_idx = col_idx + 1
        
        # Find closest row - use text top position (top edge)
        row_idx = 0
        min_row_dist = float('inf')
        for i, row_y in enumerate(row_boundaries):
            # Check distance from text top to row boundary
            dist = abs(text_y - row_y)
            if dist < min_row_dist:
                min_row_dist = dist
                row_idx = i
        
        # If text spans multiple rows, check if center is closer to next row
        if row_idx + 1 < len(row_boundaries):
            next_row_y = row_boundaries[row_idx + 1]
            current_row_y = row_boundaries[row_idx]
            
            # If text center is closer to next row, use next row
            # But only if text doesn't start above current row
            if abs(text_center_y - next_row_y) < abs(text_center_y - current_row_y):
                if text_y <= current_row_y:  # Y decreases downward in PDF coordinates
                    row_idx = row_idx + 1
        
        # Assign to cell - IMPROVED: Better column separation for Unicode
        if row_idx < len(grid) and col_idx < len(grid[row_idx]):
            cell = grid[row_idx][col_idx]
            obj_text = obj.get('text', '').strip()
            
            if not obj_text:
                continue
            
            # Check if text should go to a different column (better X-axis separation)
            # If text is far from current column center, check if it belongs to adjacent column
            if column_boundaries and len(column_boundaries) > col_idx + 1:
                col_center = column_boundaries[col_idx]
                next_col_center = column_boundaries[col_idx + 1]
                mid_point = (col_center + next_col_center) / 2
                
                # If text X position is closer to next column, use next column
                if obj['x'] > mid_point and col_idx + 1 < len(grid[row_idx]):
                    # Check if next column is empty or has less text
                    next_cell = grid[row_idx][col_idx + 1]
                    if not next_cell['text'] or len(next_cell['text']) < len(obj_text):
                        cell = next_cell
                        col_idx = col_idx + 1
            
            # IMPROVED: Assign text to cell with better conflict resolution
            if cell['text']:
                # Check if this text belongs to the same logical cell
                cell_x = column_boundaries[col_idx] if column_boundaries and col_idx < len(column_boundaries) else 0
                cell_y = row_boundaries[row_idx] if row_boundaries and row_idx < len(row_boundaries) else 0
                
                # Calculate distance from text to cell
                text_x = obj.get('x', 0)
                text_y = obj.get('y', 0)
                dist_x = abs(text_x - cell_x)
                dist_y = abs(text_y - cell_y)
                
                # Thresholds for same cell detection
                same_col_threshold = 30  # Points
                same_row_threshold = 15  # Points
                
                # If text is close to cell (same column and row), merge
                if dist_x < same_col_threshold and dist_y < same_row_threshold:
                    # Same cell - append text
                    if cell['text'].strip() and obj_text.strip():
                        cell['text'] += ' ' + obj_text
                    elif obj_text.strip():
                        cell['text'] = obj_text
                else:
                    # Different cell - find the correct cell
                    # Recalculate best column and row
                    best_col = col_idx
                    best_row = row_idx
                    min_total_dist = dist_x + dist_y
                    
                    # Check all columns
                    for i, col_x in enumerate(column_boundaries):
                        col_dist = abs(text_x - col_x)
                        if col_dist < min_total_dist:
                            # Check if this column is better
                            for j, row_y in enumerate(row_boundaries):
                                row_dist = abs(text_y - row_y)
                                total_dist = col_dist + row_dist
                                if total_dist < min_total_dist:
                                    min_total_dist = total_dist
                                    best_col = i
                                    best_row = j
                    
                    # Assign to best cell
                    if best_row < len(grid) and best_col < len(grid[best_row]):
                        best_cell = grid[best_row][best_col]
                        if best_cell['text']:
                            if best_cell['text'].strip() and obj_text.strip():
                                best_cell['text'] += ' ' + obj_text
                            elif obj_text.strip():
                                best_cell['text'] = obj_text
                        else:
                            best_cell['text'] = obj_text
                            best_cell['font_name'] = obj.get('font_name', 'Arial')
                            best_cell['font_size'] = obj.get('font_size', 10)
                            best_cell['is_bold'] = obj.get('is_bold', False)
            else:
                # Empty cell - assign text
                cell['text'] = obj_text
                cell['font_name'] = obj.get('font_name', 'Arial')
                cell['font_size'] = obj.get('font_size', 10)
                cell['is_bold'] = obj.get('is_bold', False)
    
    # Detect merged cells (horizontal and vertical)
    # This is a light cleanup pass
    for row_idx, row in enumerate(grid):
        for col_idx, cell in enumerate(row):
            if not cell['text']:
                continue
            
            # Check if this cell should be merged with left neighbor (horizontal merge)
            if col_idx > 0:
                left_cell = row[col_idx - 1]
                if left_cell['text'] == cell['text'] and left_cell['text']:
                    # Horizontal merge: keep text in left cell, mark right as merged
                    left_cell['merged'] = True
                    left_cell['merge_right'] = True  # Mark for horizontal merge
                    cell['text'] = ''
                    cell['merged'] = True
                    cell['merge_left'] = True
            
            # Check if this cell should be merged with top neighbor (vertical merge)
            if row_idx > 0 and col_idx < len(grid[row_idx - 1]):
                top_cell = grid[row_idx - 1][col_idx]
                if top_cell['text'] == cell['text'] and top_cell['text']:
                    # Vertical merge: keep text in top cell, mark bottom as merged
                    top_cell['merged'] = True
                    top_cell['merge_down'] = True  # Mark for vertical merge
                    cell['text'] = ''
                    cell['merged'] = True
                    cell['merge_up'] = True
    
    # IMPROVED: Clean up empty rows and columns
    # Remove completely empty rows
    non_empty_rows = []
    for row in grid:
        if any(cell.get('text', '').strip() for cell in row):
            non_empty_rows.append(row)
    
    if not non_empty_rows:
        return grid  # Return original if all empty
    
    # Remove completely empty columns
    if non_empty_rows:
        # Find columns that have at least one non-empty cell
        non_empty_col_indices = set()
        for row in non_empty_rows:
            for col_idx, cell in enumerate(row):
                if cell.get('text', '').strip():
                    non_empty_col_indices.add(col_idx)
        
        # Rebuild grid with only non-empty columns
        if non_empty_col_indices:
            cleaned_grid = []
            for row in non_empty_rows:
                cleaned_row = []
                for col_idx in sorted(non_empty_col_indices):
                    if col_idx < len(row):
                        cleaned_row.append(row[col_idx])
                if cleaned_row:
                    cleaned_grid.append(cleaned_row)
            
            # Update column boundaries to match cleaned grid
            if cleaned_grid and column_boundaries:
                cleaned_column_boundaries = []
                for col_idx in sorted(non_empty_col_indices):
                    if col_idx < len(column_boundaries):
                        cleaned_column_boundaries.append(column_boundaries[col_idx])
                # Update column boundaries (will be used by caller if needed)
                # Note: This is a side effect, but necessary for proper grid structure
            
            if cleaned_grid:
                logger.info(f"Cleaned grid: {len(cleaned_grid)} rows, {len(cleaned_grid[0]) if cleaned_grid else 0} columns (removed empty rows/columns)")
                return cleaned_grid
    
    return non_empty_rows if non_empty_rows else grid


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

