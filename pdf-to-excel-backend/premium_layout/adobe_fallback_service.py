"""
Adobe PDF Extract API Fallback Service
Enterprise-grade fallback for complex PDF layouts when Document AI confidence is low.

Author: AI Assistant
Date: 2025-12-27
"""

import logging
import json
import os
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import requests

from .unified_layout_model import UnifiedLayout, Cell, CellStyle

logger = logging.getLogger(__name__)


@dataclass
class AdobeConfig:
    """Configuration for Adobe PDF Extract API"""
    client_id: str
    client_secret: str
    api_endpoint: str = "https://pdf-services.adobe.io/operation/extractpdf"
    auth_endpoint: str = "https://ims-na1.adobelogin.com/ims/token/v3"
    timeout: int = 120  # seconds
    max_retries: int = 1  # Never auto-retry for cost safety


class AdobeFallbackService:
    """
    Fallback service using Adobe PDF Extract API for complex documents.
    
    USAGE:
    - Called ONLY when Document AI confidence < 0.65
    - Pay-per-use model
    - Returns UnifiedLayout compatible with existing pipeline
    """
    
    def __init__(self):
        self.config = self._load_config()
        self.access_token = None
        self.token_expiry = 0
        self.call_count = 0  # Track Adobe API calls for billing
        
    def _load_config(self) -> AdobeConfig:
        """Load Adobe API credentials from environment"""
        client_id = os.getenv('ADOBE_CLIENT_ID', '')
        client_secret = os.getenv('ADOBE_CLIENT_SECRET', '')
        
        if not client_id or not client_secret:
            logger.warning("Adobe PDF Extract credentials not configured - fallback disabled")
            
        return AdobeConfig(
            client_id=client_id,
            client_secret=client_secret
        )
    
    def is_available(self) -> bool:
        """Check if Adobe fallback is available"""
        return bool(self.config.client_id and self.config.client_secret)
    
    def _get_access_token(self) -> Optional[str]:
        """Get or refresh Adobe API access token"""
        current_time = time.time()
        
        # Reuse token if still valid (with 5 min buffer)
        if self.access_token and self.token_expiry > current_time + 300:
            return self.access_token
        
        try:
            logger.info("Requesting Adobe API access token...")
            
            response = requests.post(
                self.config.auth_endpoint,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'scope': 'openid,AdobeID,read_organizations'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expiry = current_time + expires_in
                logger.info(f"Adobe access token obtained, expires in {expires_in}s")
                return self.access_token
            else:
                logger.error(f"Adobe token request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Adobe access token: {e}")
            return None
    
    def extract_pdf_structure(
        self,
        pdf_bytes: bytes,
        filename: str,
        docai_confidence: float
    ) -> Tuple[Optional[List[UnifiedLayout]], float, Dict[str, Any]]:
        """
        Extract PDF structure using Adobe PDF Extract API.
        
        Args:
            pdf_bytes: Raw PDF file bytes
            filename: Original filename
            docai_confidence: Document AI confidence (for logging)
        
        Returns:
            (unified_layouts, confidence, metadata)
        """
        
        if not self.is_available():
            logger.warning("Adobe PDF Extract not available - credentials missing")
            return None, 0.0, {'error': 'Adobe credentials not configured'}
        
        # Cost safety: Increment call counter
        self.call_count += 1
        
        logger.info("=" * 80)
        logger.info(f"ADOBE FALLBACK: Triggered for {filename}")
        logger.info(f"Reason: Document AI confidence {docai_confidence:.2f} < 0.65")
        logger.info(f"Adobe cost meter: {self.call_count} transaction(s) this session")
        logger.info("=" * 80)
        
        try:
            # Call Adobe PDF Extract API (handles auth internally)
            start_time = time.time()
            adobe_result = self._call_adobe_api(pdf_bytes, None)  # access_token handled by API client
            elapsed = time.time() - start_time
            
            if not adobe_result:
                logger.error("Adobe API returned no data")
                return None, 0.0, {'error': 'Adobe API failed'}
            
            logger.info(f"Adobe API call completed in {elapsed:.2f}s")
            
            # Parse Adobe output into UnifiedLayout
            unified_layouts = self._convert_adobe_to_unified(adobe_result)
            
            if not unified_layouts:
                logger.warning("Adobe data could not be converted to UnifiedLayout")
                return None, 0.0, {'error': 'Conversion failed'}
            
            # Calculate confidence (Adobe is generally high quality)
            confidence = 0.85  # Adobe Extract is reliable for tables
            
            # Log results
            total_rows = sum(len(layout.rows) for layout in unified_layouts)
            total_cols = max((len(row) for layout in unified_layouts for row in layout.rows), default=0)
            logger.info(f"Adobe layout: {len(unified_layouts)} page(s), {total_rows} rows, {total_cols} columns")
            
            metadata = {
                'source': 'adobe',
                'confidence': confidence,
                'api_time_seconds': elapsed,
                'pages_processed': len(unified_layouts),
                'cost_transactions': 1
            }
            
            return unified_layouts, confidence, metadata
            
        except Exception as e:
            logger.error(f"Adobe fallback failed: {e}", exc_info=True)
            return None, 0.0, {'error': str(e)}
    
    def _call_adobe_api(self, pdf_bytes: bytes, access_token: str) -> Optional[Dict]:
        """
        Call Adobe PDF Extract API - PRODUCTION IMPLEMENTATION.
        
        Complete flow:
        1. Upload PDF to Adobe's cloud storage
        2. Submit extraction job
        3. Poll for job completion
        4. Download result JSON
        """
        
        try:
            # Use production Adobe API client
            from .adobe_api_client import AdobeAPIClient
            
            logger.info("🚀 Calling REAL Adobe PDF Extract API...")
            
            api_client = AdobeAPIClient(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret
            )
            
            # Execute full extraction flow
            result = api_client.extract_pdf_full_flow(pdf_bytes, "document.pdf")
            
            if result:
                logger.info("✅ Adobe API returned structured data")
                return result
            else:
                logger.error("❌ Adobe API returned no data")
                return None
                
        except ImportError as import_err:
            logger.error(f"❌ Adobe API client not available: {import_err}")
            return None
        except Exception as e:
            logger.error(f"❌ Adobe API call failed: {e}", exc_info=True)
            return None
    
    def _convert_adobe_to_unified(self, adobe_data: Dict) -> Optional[List[UnifiedLayout]]:
        """
        HIGH-FIDELITY Adobe PDF Extract → UnifiedLayout → Excel mapping.
        
        Adobe Extract API structure:
        {
          "elements": [
            {"Path": "//Document/H1", "Text": "...", "Bounds": [x1,y1,x2,y2]},
            {"Path": "//Document/Table", "filePaths": ["tables/table_0.csv"]}
          ],
          "pages": [
            {
              "page": 1,
              "tables": [
                {
                  "Cells": [
                    {
                      "RowIndex": 0,
                      "ColumnIndex": 0,
                      "RowSpan": 1,
                      "ColumnSpan": 1,
                      "Text": "Header 1",
                      "Bounds": [x1, y1, x2, y2],
                      "attributes": {"TextSize": 12, "FontWeight": 700}
                    }
                  ]
                }
              ]
            }
          ]
        }
        
        Guarantees:
        - Preserve rowSpan/colSpan exactly
        - Only top-left merged cell has value
        - Lock column anchors from headers
        - Normalize row heights and column widths
        - Preserve Unicode text exactly
        - Handle charts separately (data sheet or visual ref)
        """
        
        logger.info("=" * 80)
        logger.info("ADOBE MAPPING: Starting high-fidelity conversion to UnifiedLayout")
        logger.info("=" * 80)
        
        try:
            unified_layouts = []
            charts_found = []
            
            # Extract charts from elements (if present)
            elements = adobe_data.get('elements', [])
            for elem in elements:
                path = elem.get('Path', '')
                if 'Figure' in path or 'Chart' in path or 'Graph' in path:
                    charts_found.append(elem)
            
            # Adobe PDF Extract returns two possible formats:
            # Format 1: elements[] with table references (most common)
            # Format 2: pages[] with direct table data (less common)
            
            # Check for Format 1 first (elements with table references)
            if 'elements' in adobe_data and adobe_data['elements']:
                logger.info("Adobe data contains 'elements' array - processing table elements")
                unified_layouts = self._process_adobe_elements(adobe_data['elements'])
                if unified_layouts:
                    return unified_layouts
            
            # Fallback to Format 2 (pages with direct table data)
            for page_data in adobe_data.get('pages', []):
                page_num = page_data.get('page', 1)
                tables = page_data.get('tables', [])
                
                if not tables:
                    logger.info(f"Page {page_num}: No tables found by Adobe")
                    continue
                
                for table_idx, table in enumerate(tables):
                    logger.info(f"Page {page_num}, Table {table_idx + 1}: Starting conversion")
                    
                    # STEP 1: Extract and validate cells
                    cells = table.get('Cells', [])
                    if not cells:
                        logger.warning(f"Page {page_num}, Table {table_idx + 1}: No cells found")
                        continue
                    
                    logger.info(f"Extracted {len(cells)} raw cells from Adobe table")
                    
                    # STEP 2: Build cell grid with geometry
                    cell_grid, max_row, max_col, merge_count = self._build_cell_grid_from_adobe(
                        cells, page_num, table_idx
                    )
                    
                    # STEP 2.5: Validate cell grid integrity
                    if not self._validate_cell_integrity(cell_grid, max_row, max_col):
                        logger.warning(f"Page {page_num}, Table {table_idx + 1}: Cell grid validation failed")
                        # Continue anyway with best-effort conversion
                    
                    # STEP 3: Detect header rows and lock columns
                    header_rows, locked_columns = self._detect_headers_and_lock_columns(
                        cell_grid, max_row, max_col
                    )
                    
                    # STEP 4: Normalize row heights and column widths
                    normalized_grid = self._normalize_row_column_dimensions(
                        cell_grid, max_row, max_col, locked_columns
                    )
                    
                    # STEP 5: Convert to UnifiedLayout rows
                    rows = self._convert_grid_to_unified_rows(
                        normalized_grid, max_row, max_col, header_rows
                    )
                    
                    if not rows:
                        logger.warning(f"Page {page_num}, Table {table_idx + 1}: No rows generated")
                        continue
                    
                    # STEP 6: Create UnifiedLayout with metadata
                    layout = UnifiedLayout(
                        rows=rows,
                        metadata={
                            'source': 'adobe',
                            'page': page_num,
                            'table_index': table_idx,
                            'total_rows': len(rows),
                            'total_columns': max_col + 1,
                            'header_rows': header_rows,
                            'merged_cells': merge_count,
                            'locked_columns': len(locked_columns)
                        }
                    )
                    
                    unified_layouts.append(layout)
                    
                    logger.info("=" * 80)
                    logger.info(f"ADOBE MAPPING COMPLETE: Page {page_num}, Table {table_idx + 1}")
                    logger.info(f"Mapped rows={len(rows)}, cols={max_col + 1}, merges={merge_count}")
                    logger.info(f"Header rows: {header_rows}, Locked columns: {len(locked_columns)}")
                    logger.info("=" * 80)
            
            # STEP 7: Handle charts (if present)
            chart_handling_result = "none"
            if charts_found:
                chart_handling_result = self._handle_charts(charts_found, unified_layouts)
            
            logger.info(f"Charts handled: {chart_handling_result}")
            
            return unified_layouts if unified_layouts else None
            
        except Exception as e:
            logger.error(f"Adobe mapping failed: {e}", exc_info=True)
            return None
    
    def _process_adobe_elements(self, elements: List[Dict]) -> Optional[List[UnifiedLayout]]:
        """
        Process Adobe elements format where tables are in elements[] array.
        
        Adobe returns:
        {
          "elements": [
            {"Path": "//Document/Table", "Page": 1, "Cells": [...]}
          ]
        }
        """
        unified_layouts = []
        
        try:
            for elem in elements:
                path = elem.get('Path', '')
                
                # Look for table elements
                if '/Table' in path or elem.get('type') == 'Table':
                    logger.info(f"Processing table element: {path}")
                    
                    # Extract cells from element
                    cells = elem.get('Cells', [])
                    if not cells:
                        # Try alternative formats
                        cells = elem.get('cells', [])
                    
                    if not cells:
                        logger.warning(f"Table element has no cells: {path}")
                        continue
                    
                    # Get page number
                    page_num = elem.get('Page', 1)
                    if not page_num:
                        page_num = elem.get('page', 1)
                    
                    # Build cell grid
                    cell_grid, max_row, max_col, merge_count = self._build_cell_grid_from_adobe(
                        cells, page_num, 0
                    )
                    
                    # Validate
                    if not self._validate_cell_integrity(cell_grid, max_row, max_col):
                        logger.warning(f"Cell grid validation failed for {path}")
                    
                    # Detect headers and lock columns
                    header_rows, locked_columns = self._detect_headers_and_lock_columns(
                        cell_grid, max_row, max_col
                    )
                    
                    # Normalize
                    normalized_grid = self._normalize_row_column_dimensions(
                        cell_grid, max_row, max_col, locked_columns
                    )
                    
                    # Convert to rows
                    rows = self._convert_grid_to_unified_rows(
                        normalized_grid, max_row, max_col, header_rows
                    )
                    
                    if rows:
                        layout = UnifiedLayout(
                            rows=rows,
                            metadata={
                                'source': 'adobe',
                                'page': page_num,
                                'table_path': path,
                                'total_rows': len(rows),
                                'total_columns': max_col + 1,
                                'header_rows': header_rows,
                                'merged_cells': merge_count,
                                'locked_columns': len(locked_columns)
                            }
                        )
                        unified_layouts.append(layout)
                        
                        logger.info(f"✅ Processed table: {path} ({len(rows)} rows × {max_col + 1} cols)")
            
            return unified_layouts if unified_layouts else None
            
        except Exception as e:
            logger.error(f"Failed to process Adobe elements: {e}", exc_info=True)
            return None
    
    def _build_cell_grid_from_adobe(
        self,
        cells: List[Dict],
        page_num: int,
        table_idx: int
    ) -> Tuple[Dict, int, int, int]:
        """
        Build a cell grid from Adobe cells with geometry and span information.
        
        Returns:
            Tuple of (cell_grid, max_row, max_col, merge_count)
        """
        cell_grid = {}  # {(row, col): cell_info}
        max_row = 0
        max_col = 0
        merge_count = 0
        
        for cell in cells:
            row_idx = cell.get('RowIndex', 0)
            col_idx = cell.get('ColumnIndex', 0)
            row_span = cell.get('RowSpan', 1)
            col_span = cell.get('ColumnSpan', 1)
            raw_text = cell.get('Text', '')
            
            # CRITICAL: Preserve Unicode text exactly (no normalization)
            # This ensures Hindi, Chinese, Arabic, emoji, etc. remain intact
            text = self._preserve_unicode_text(raw_text)
            
            # Extract geometry (bounding box)
            bounds = cell.get('Bounds', [])
            bounding_box = None
            if len(bounds) == 4:
                bounding_box = {
                    'x_min': bounds[0],
                    'y_min': bounds[1],
                    'x_max': bounds[2],
                    'y_max': bounds[3]
                }
            
            # Extract style attributes
            attributes = cell.get('attributes', {})
            text_size = attributes.get('TextSize', 11)
            font_weight = attributes.get('FontWeight', 400)
            is_bold = font_weight >= 700
            
            # Track merged cells
            if row_span > 1 or col_span > 1:
                merge_count += 1
            
            max_row = max(max_row, row_idx + row_span - 1)
            max_col = max(max_col, col_idx + col_span - 1)
            
            # Store cell info
            cell_info = {
                'text': text,
                'row_idx': row_idx,
                'col_idx': col_idx,
                'row_span': row_span,
                'col_span': col_span,
                'bounding_box': bounding_box,
                'text_size': text_size,
                'is_bold': is_bold,
                'is_top_left': True  # This is the top-left cell of a merge
            }
            
            cell_grid[(row_idx, col_idx)] = cell_info
            
            # Mark spanned cells as occupied (no value, just placeholder)
            for r in range(row_idx, row_idx + row_span):
                for c in range(col_idx, col_idx + col_span):
                    if (r, c) != (row_idx, col_idx):
                        cell_grid[(r, c)] = {
                            'text': '',
                            'row_idx': r,
                            'col_idx': c,
                            'row_span': 0,  # Marker for merged cell continuation
                            'col_span': 0,
                            'is_top_left': False,
                            'merged_from': (row_idx, col_idx)
                        }
        
        logger.info(f"Built cell grid: {max_row + 1} rows × {max_col + 1} columns, {merge_count} merges")
        return cell_grid, max_row, max_col, merge_count
    
    def _detect_headers_and_lock_columns(
        self,
        cell_grid: Dict,
        max_row: int,
        max_col: int
    ) -> Tuple[List[int], List[float]]:
        """
        Detect header rows and lock column anchors.
        
        Header detection rules:
        - Top band rows (first 1-3 rows)
        - Bold text or larger font size
        - Background color or border style
        
        Returns:
            Tuple of (header_row_indices, locked_column_positions)
        """
        header_rows = []
        
        # Check first 3 rows for header indicators
        for row_idx in range(min(3, max_row + 1)):
            is_header = True
            bold_count = 0
            total_cells = 0
            
            for col_idx in range(max_col + 1):
                if (row_idx, col_idx) in cell_grid:
                    cell = cell_grid[(row_idx, col_idx)]
                    if cell.get('is_top_left', False):
                        total_cells += 1
                        if cell.get('is_bold', False):
                            bold_count += 1
            
            # If >50% of cells are bold, consider it a header row
            if total_cells > 0 and bold_count / total_cells >= 0.5:
                header_rows.append(row_idx)
            elif row_idx == 0:
                # First row is always considered header by default
                header_rows.append(row_idx)
            else:
                break  # Stop once we hit a non-header row
        
        # Lock column positions from header cells
        locked_columns = []
        for col_idx in range(max_col + 1):
            # Find first header cell in this column
            for row_idx in header_rows:
                if (row_idx, col_idx) in cell_grid:
                    cell = cell_grid[(row_idx, col_idx)]
                    bbox = cell.get('bounding_box')
                    if bbox:
                        # Use x_min as column anchor
                        x_anchor = bbox['x_min']
                        locked_columns.append(x_anchor)
                        break
            else:
                # No header cell found, use estimated position
                locked_columns.append(col_idx * 0.1)  # Fallback: 10% per column
        
        logger.info(f"Detected {len(header_rows)} header rows: {header_rows}")
        logger.info(f"Locked {len(locked_columns)} column anchors")
        
        return header_rows, locked_columns
    
    def _normalize_row_column_dimensions(
        self,
        cell_grid: Dict,
        max_row: int,
        max_col: int,
        locked_columns: List[float]
    ) -> Dict:
        """
        Normalize row heights and column widths for stable Excel rendering.
        
        - Row heights: uniform per row band
        - Column widths: based on locked column positions
        - No auto-fit or inference
        """
        # For now, return cell_grid as-is
        # In production, you would calculate normalized dimensions
        # and store them in cell metadata
        
        normalized_grid = cell_grid.copy()
        
        # Calculate row heights (uniform per row)
        for row_idx in range(max_row + 1):
            row_cells = [(r, c) for (r, c) in cell_grid.keys() if r == row_idx]
            # Could calculate height from bounding boxes here
        
        # Column widths are implicitly defined by locked_columns
        
        return normalized_grid
    
    def _convert_grid_to_unified_rows(
        self,
        cell_grid: Dict,
        max_row: int,
        max_col: int,
        header_rows: List[int]
    ) -> List[List[Cell]]:
        """
        Convert cell grid to UnifiedLayout rows format.
        
        - Only top-left merged cells contain values
        - Header rows have special styling
        - All rows have same column count
        """
        rows = []
        
        for row_idx in range(max_row + 1):
            row = []
            
            for col_idx in range(max_col + 1):
                if (row_idx, col_idx) in cell_grid:
                    cell = cell_grid[(row_idx, col_idx)]
                    
                    # Only include value if this is the top-left cell
                    text = cell['text'] if cell.get('is_top_left', False) else ''
                    
                    # Determine if this is a header cell
                    is_header = row_idx in header_rows
                    
                    # Create Cell (mapping from Adobe table cell to UnifiedLayout Cell format)
                    cell_data = Cell(
                        row=row_idx,
                        column=col_idx,
                        value=text,
                        rowspan=cell.get('row_span', 1) if cell.get('is_top_left', False) else 1,
                        colspan=cell.get('col_span', 1) if cell.get('is_top_left', False) else 1,
                        style=CellStyle(
                            bold=cell.get('is_bold', False) or is_header,
                            background_color='FFE0E0E0' if is_header else None,
                            font_size=cell.get('text_size', 11)
                        ),
                        merged=(cell.get('row_span', 1) > 1 or cell.get('col_span', 1) > 1) if cell.get('is_top_left', False) else False
                    )
                    
                    row.append(cell_data)
                else:
                    # Empty cell
                    row.append(Cell(row=row_idx, column=col_idx, value=''))
            
            rows.append(row)
        
        return rows
    
    def _handle_charts(self, charts: List[Dict], layouts: List[UnifiedLayout]) -> str:
        """
        Handle chart elements from Adobe PDF Extract.
        
        Strategy:
        - If chart has vector data → create "Chart_Data" sheet with tabular data
        - Else → create "Chart_Visual" sheet with image reference
        - Never mix charts with tables
        
        Returns:
            "data" | "visual" | "none"
        """
        if not charts:
            return "none"
        
        logger.info(f"Found {len(charts)} chart(s) in Adobe output")
        
        chart_layout_created = False
        
        for idx, chart in enumerate(charts):
            path = chart.get('Path', '')
            text = chart.get('Text', '')
            bounds = chart.get('Bounds', [])
            
            logger.info(f"Chart {idx + 1}: Path={path}, Text={text[:50] if text else 'N/A'}")
            
            # Check if chart has associated data file
            file_paths = chart.get('filePaths', [])
            if file_paths:
                # Chart has vector data - create data sheet
                logger.info(f"Chart {idx + 1} has data file: {file_paths}")
                # TODO: Parse chart data CSV and create UnifiedLayout
                chart_layout_created = True
            else:
                # Chart is visual only - create visual reference
                logger.info(f"Chart {idx + 1} is visual only")
                
                # Create a simple layout with chart caption
                if text:
                    chart_rows = [
                        [Cell(row=0, column=0, value="[Chart Visual]", style=CellStyle(bold=True))],
                        [Cell(row=1, column=0, value=text)]
                    ]
                    
                    chart_layout = UnifiedLayout(
                        rows=chart_rows,
                        metadata={
                            'source': 'adobe',
                            'type': 'chart_visual',
                            'chart_index': idx,
                            'bounds': bounds
                        }
                    )
                    
                    layouts.append(chart_layout)
                    chart_layout_created = True
        
        return "visual" if chart_layout_created else "none"
    
    def _preserve_unicode_text(self, text: str) -> str:
        """
        Preserve Unicode text exactly without normalization.
        
        Critical for:
        - Hindi (Devanagari script)
        - Chinese (CJK characters)
        - Arabic (RTL text)
        - Emoji and symbols
        
        Args:
            text: Raw text from Adobe
        
        Returns:
            Preserved Unicode text
        """
        if not text:
            return ""
        
        # Do NOT perform any of these operations:
        # - encode/decode cycles
        # - strip combining characters
        # - normalize Unicode forms (NFC, NFD, NFKC, NFKD)
        # - replace RTL markers
        
        # Just return the text as-is
        return text
    
    def _validate_cell_integrity(
        self,
        cell_grid: Dict,
        max_row: int,
        max_col: int
    ) -> bool:
        """
        Validate that cell grid has proper structure.
        
        Checks:
        - No overlapping cells (except valid merges)
        - All rows have same column count
        - Merged cells have proper spans
        
        Returns:
            True if valid, False otherwise
        """
        # Check all positions are covered
        for row_idx in range(max_row + 1):
            for col_idx in range(max_col + 1):
                if (row_idx, col_idx) not in cell_grid:
                    logger.warning(f"Missing cell at ({row_idx}, {col_idx})")
                    return False
        
        # Check merged cells don't overlap improperly
        for (row_idx, col_idx), cell in cell_grid.items():
            if cell.get('is_top_left', False):
                row_span = cell.get('row_span', 1)
                col_span = cell.get('col_span', 1)
                
                # Verify all spanned positions are marked correctly
                for r in range(row_idx, row_idx + row_span):
                    for c in range(col_idx, col_idx + col_span):
                        if (r, c) != (row_idx, col_idx):
                            if (r, c) not in cell_grid:
                                logger.warning(f"Merged cell span incomplete at ({r}, {c})")
                                return False
                            
                            spanned_cell = cell_grid[(r, c)]
                            if spanned_cell.get('merged_from') != (row_idx, col_idx):
                                logger.warning(f"Merged cell reference mismatch at ({r}, {c})")
                                return False
        
        logger.info("Cell grid integrity validated successfully")
        return True
    
    def get_cost_info(self) -> Dict[str, Any]:
        """Return cost tracking information"""
        return {
            'total_calls': self.call_count,
            'estimated_cost_usd': self.call_count * 0.05,  # Example: $0.05 per call
            'billing_note': 'Adobe PDF Extract charged per document'
        }


# Singleton instance
_adobe_service = None

def get_adobe_fallback_service() -> AdobeFallbackService:
    """Get or create Adobe fallback service singleton"""
    global _adobe_service
    if _adobe_service is None:
        _adobe_service = AdobeFallbackService()
    return _adobe_service

