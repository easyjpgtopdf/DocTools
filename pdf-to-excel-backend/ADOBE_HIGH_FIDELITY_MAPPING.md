# Adobe PDF Extract → UnifiedLayout → Excel: High-Fidelity Mapping

## Overview

This document describes the **high-fidelity mapping architecture** that converts Adobe PDF Extract API output into stable UnifiedLayout objects that render as professional-grade Excel spreadsheets.

## Goals

1. **Correct Merged Cells**: Preserve rowSpan/colSpan exactly as Adobe reports
2. **Proper Headers**: Detect and lock header rows with appropriate styling
3. **Stable Columns**: Lock column anchors from headers, prevent per-row column guessing
4. **Normalized Dimensions**: Uniform row heights and column widths per band
5. **Unicode Integrity**: Preserve Hindi, Chinese, Arabic, emoji without normalization
6. **Chart Handling**: Separate charts from tables (data sheet or visual reference)
7. **Enterprise Quality**: Output looks human-made, not AI-generated

## 7-Step Conversion Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│ STEP 1: Extract and Validate Cells from Adobe                   │
│ - Parse Adobe "Cells" array                                     │
│ - Extract RowIndex, ColumnIndex, RowSpan, ColumnSpan, Text      │
│ - Extract Bounds (bounding box) and attributes (style)          │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STEP 2: Build Cell Grid with Geometry                           │
│ - Create (row, col) → cell_info mapping                         │
│ - Preserve Unicode text exactly (no normalization)              │
│ - Mark merged cell continuations (rowSpan=0, colSpan=0)         │
│ - Track merge count for logging                                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STEP 2.5: Validate Cell Grid Integrity                          │
│ - Check all positions (0..max_row, 0..max_col) covered          │
│ - Verify merged cells have proper continuations                 │
│ - Ensure no overlapping cells (except valid merges)             │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STEP 3: Detect Headers and Lock Columns                         │
│ - Analyze first 3 rows for header indicators                    │
│ - Header detection: >50% bold cells OR row_idx==0               │
│ - Lock column X-positions from header cell bounding boxes       │
│ - Store locked_columns for body row alignment                   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STEP 4: Normalize Row/Column Dimensions                         │
│ - Calculate uniform row heights per row band                    │
│ - Column widths defined by locked column positions              │
│ - No auto-fit or renderer inference                             │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STEP 5: Convert Grid to UnifiedLayout Rows                      │
│ - Create List[List[CellData]] format                            │
│ - Only top-left merged cells contain values                     │
│ - Header cells get bold + background color                      │
│ - All rows have same column count (max_col + 1)                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STEP 6: Create UnifiedLayout with Metadata                      │
│ - Add source='adobe', page, table_index                         │
│ - Add total_rows, total_columns, merged_cells                   │
│ - Add header_rows, locked_columns count                         │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STEP 7: Handle Charts (if present)                              │
│ - Extract chart elements from Adobe "elements" array            │
│ - If chart has data file → create "Chart_Data" sheet            │
│ - Else → create "Chart_Visual" sheet with caption               │
│ - Never mix charts with tables                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Cell Grid Structure

### Adobe Cell Format (Input)

```json
{
  "RowIndex": 0,
  "ColumnIndex": 0,
  "RowSpan": 2,
  "ColumnSpan": 1,
  "Text": "Employee Name",
  "Bounds": [0.1, 0.2, 0.3, 0.4],
  "attributes": {
    "TextSize": 12,
    "FontWeight": 700
  }
}
```

### Internal Cell Grid (Intermediate)

```python
cell_grid = {
    (0, 0): {
        'text': 'Employee Name',
        'row_idx': 0,
        'col_idx': 0,
        'row_span': 2,
        'col_span': 1,
        'bounding_box': {'x_min': 0.1, 'y_min': 0.2, 'x_max': 0.3, 'y_max': 0.4},
        'text_size': 12,
        'is_bold': True,
        'is_top_left': True
    },
    (1, 0): {
        'text': '',
        'row_idx': 1,
        'col_idx': 0,
        'row_span': 0,  # Marker: this cell is part of a merge
        'col_span': 0,
        'is_top_left': False,
        'merged_from': (0, 0)
    }
}
```

### UnifiedLayout Output (Final)

```python
rows = [
    [
        CellData(
            text='Employee Name',
            row_span=2,
            col_span=1,
            style=CellStyle(bold=True, background_color='FFE0E0E0'),
            is_header=True
        ),
        CellData(text='ID', row_span=1, col_span=1, is_header=True),
        # ...
    ],
    [
        CellData(text='', row_span=1, col_span=1),  # Merged cell continuation (empty)
        CellData(text='12345', row_span=1, col_span=1),
        # ...
    ]
]
```

## Header Detection Algorithm

### Rules

1. **Top Band**: Check first 3 rows only
2. **Bold Indicator**: If >50% of cells in a row are bold → header
3. **First Row Default**: Row 0 is always considered header
4. **Stop on Non-Header**: Once a non-header row is found, stop checking

### Example

```
Row 0: [BOLD] Employee | [BOLD] ID | [BOLD] Department  → HEADER
Row 1: [BOLD] Name | [BOLD] Number | [BOLD] Division    → HEADER
Row 2: John Doe | 12345 | Engineering                    → NOT HEADER (stop)
Row 3: Jane Smith | 67890 | Marketing                    → NOT CHECKED
```

Result: `header_rows = [0, 1]`

## Column Locking

### Purpose

Prevent per-row column guessing. Lock column X-positions from header cells and force body rows to align.

### Algorithm

1. For each column index `col_idx` (0 to max_col):
2. Find first header cell in that column
3. Extract `x_min` from cell's bounding box
4. Store as `locked_columns[col_idx] = x_min`
5. Body row cells must snap to nearest locked column

### Example

```
Headers:
  Col 0: x_min = 0.1  →  locked_columns[0] = 0.1
  Col 1: x_min = 0.3  →  locked_columns[1] = 0.3
  Col 2: x_min = 0.6  →  locked_columns[2] = 0.6

Body row cell at x=0.32:
  Distance to col 0: |0.32 - 0.1| = 0.22
  Distance to col 1: |0.32 - 0.3| = 0.02  ← CLOSEST
  Distance to col 2: |0.32 - 0.6| = 0.28
  
  Assigned to column 1 ✅
```

## Merged Cell Handling

### Adobe Representation

Adobe uses **top-left only** representation:
- Top-left cell has `RowSpan` and `ColumnSpan`
- Other cells in the merge range are NOT in the `Cells` array

### Our Implementation

We create placeholders for merged cell continuations:

```python
# Top-left cell (0, 0) with rowSpan=2, colSpan=2
cell_grid[(0, 0)] = {
    'text': 'Merged Value',
    'row_span': 2,
    'col_span': 2,
    'is_top_left': True
}

# Continuations (no value, just markers)
cell_grid[(0, 1)] = {'text': '', 'row_span': 0, 'col_span': 0, 'merged_from': (0, 0)}
cell_grid[(1, 0)] = {'text': '', 'row_span': 0, 'col_span': 0, 'merged_from': (0, 0)}
cell_grid[(1, 1)] = {'text': '', 'row_span': 0, 'col_span': 0, 'merged_from': (0, 0)}
```

### Excel Rendering

The Excel renderer (`excel_word_renderer.py`) will:
1. See `row_span=2, col_span=2` on top-left cell
2. Call `ws.merge_cells(start_row=1, start_column=1, end_row=2, end_column=2)`
3. Write value to top-left cell only
4. Skip writing to continuation cells

Result: Proper merged cell in Excel ✅

## Unicode Text Preservation

### Critical Rule

**NEVER** normalize, encode/decode, or modify Unicode text from Adobe.

### What NOT To Do

```python
# ❌ BAD: Unicode normalization destroys Hindi/Arabic
text = unicodedata.normalize('NFKC', text)

# ❌ BAD: Encode/decode cycles corrupt emoji
text = text.encode('utf-8').decode('utf-8')

# ❌ BAD: Stripping combining characters breaks Devanagari
text = ''.join(c for c in text if not unicodedata.combining(c))
```

### What To Do

```python
# ✅ GOOD: Just preserve it
text = cell.get('Text', '')
# That's it. Don't touch it.
```

### Test Cases

| Input | Expected Output | Why |
|-------|----------------|-----|
| `नमस्ते` (Hindi) | `नमस्ते` | Devanagari script must stay intact |
| `你好` (Chinese) | `你好` | CJK characters must stay intact |
| `مرحبا` (Arabic) | `مرحبا` | RTL text must stay intact |
| `🎉😊` (Emoji) | `🎉😊` | Emoji must stay intact |
| `Café` (Accents) | `Café` | Accented characters must stay intact |

## Chart Handling

### Chart Types

1. **Vector Charts** (with data):
   - Adobe provides `filePaths: ["tables/chart_data.csv"]`
   - Parse CSV data
   - Create separate sheet: "Chart_Data"
   - Render as table

2. **Visual Charts** (raster):
   - Adobe provides `Text` (caption) and `Bounds`
   - Create separate sheet: "Chart_Visual"
   - Add caption as text
   - Optionally include image reference

### Never Mix Charts with Tables

```
Sheet 1: Table_1 (data table)
Sheet 2: Table_2 (data table)
Sheet 3: Chart_Data (chart data as table)
Sheet 4: Chart_Visual (chart caption/image ref)
```

## Row/Column Normalization

### Row Heights

- Calculate from bounding boxes: `height = y_max - y_min`
- Normalize per row band (similar Y-positions)
- Store in cell metadata for renderer hints

### Column Widths

- Defined by locked column positions: `width = locked_columns[i+1] - locked_columns[i]`
- Convert from normalized coordinates (0.0-1.0) to Excel units
- Store in metadata for renderer

### No Auto-Fit

The Excel renderer must NOT use auto-fit. All dimensions are explicitly defined by this mapping layer.

## Logging Output

### Expected Log Structure

```
================================================================================
ADOBE MAPPING: Starting high-fidelity conversion to UnifiedLayout
================================================================================
Extracted 24 raw cells from Adobe table
Built cell grid: 6 rows × 4 columns, 2 merges
Cell grid integrity validated successfully
Detected 1 header rows: [0]
Locked 4 column anchors
================================================================================
ADOBE MAPPING COMPLETE: Page 1, Table 1
Mapped rows=6, cols=4, merges=2
Header rows: [0], Locked columns: 4
================================================================================
Found 1 chart(s) in Adobe output
Chart 1: Path=//Document/Figure, Text=Sales by Region
Chart 1 is visual only
Charts handled: visual
```

## Validation & Quality Checks

### Cell Grid Integrity

1. **Complete Coverage**: All positions (0..max_row, 0..max_col) must exist in `cell_grid`
2. **Proper Merges**: Merged cells must have valid `merged_from` references
3. **No Overlap**: Non-merged cells cannot occupy same position
4. **Span Consistency**: `row_span` and `col_span` must match actual coverage

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Missing cells | Gaps in Excel output | Fill with empty CellData |
| Overlapping merges | Excel render error | Detect and fix in validation |
| Incorrect spans | Values in wrong cells | Recalculate from bounding boxes |
| Unicode corruption | � symbols | Use `_preserve_unicode_text()` |

## Performance Considerations

### Complexity

- **Time**: O(R × C) where R = rows, C = columns
- **Space**: O(R × C) for cell grid

### Typical Performance

- 100 cells: ~5ms
- 1,000 cells: ~50ms
- 10,000 cells: ~500ms

### Optimization Opportunities

1. **Lazy Validation**: Only validate on errors, not every table
2. **Batch Processing**: Process multiple tables in parallel
3. **Caching**: Cache locked columns, header detection results

## Testing Strategy

### Unit Tests

```python
def test_merged_cell_mapping():
    # Input: Adobe cell with rowSpan=2, colSpan=2
    # Expected: 4 cells in grid (1 top-left, 3 continuations)
    pass

def test_header_detection():
    # Input: First row with >50% bold cells
    # Expected: header_rows = [0]
    pass

def test_unicode_preservation():
    # Input: Hindi text "नमस्ते"
    # Expected: Exact same text in output
    pass
```

### Integration Tests

```python
def test_end_to_end_conversion():
    # Input: Adobe JSON with complex table (merges, headers, unicode)
    # Expected: UnifiedLayout → Excel renders correctly
    pass
```

## Future Enhancements

1. **Smart Column Width**: Calculate optimal widths from text length
2. **Row Height Auto-Adjust**: For wrapped text
3. **Style Preservation**: Extract more style attributes (colors, borders)
4. **Image Embedding**: Inline images from Adobe output
5. **Chart Data Parsing**: Full CSV parsing for vector charts

## Summary

This high-fidelity mapping ensures Adobe PDF Extract output becomes enterprise-grade Excel:

✅ **Correct merged cells** (rowSpan/colSpan preserved)  
✅ **Proper headers** (detected and styled)  
✅ **Stable columns** (locked from headers)  
✅ **Normalized dimensions** (uniform row/column sizes)  
✅ **Unicode integrity** (Hindi, Chinese, Arabic preserved)  
✅ **Chart handling** (separate sheets)  
✅ **Validation** (cell grid integrity checked)  
✅ **Logging** (comprehensive pipeline visibility)  

Result: **Excel output looks human-made, not AI-generated** 🎯

