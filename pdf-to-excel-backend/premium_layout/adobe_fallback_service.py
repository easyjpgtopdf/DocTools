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

from .unified_layout_model import UnifiedLayout, CellData, CellStyle

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
            # Get access token
            access_token = self._get_access_token()
            if not access_token:
                logger.error("Cannot proceed without access token")
                return None, 0.0, {'error': 'Authentication failed'}
            
            # Call Adobe PDF Extract API
            start_time = time.time()
            adobe_result = self._call_adobe_api(pdf_bytes, access_token)
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
        Call Adobe PDF Extract API.
        
        Note: This is a simplified implementation. In production, you would:
        1. Upload PDF to Adobe's cloud storage
        2. Poll for job completion
        3. Download result JSON
        
        For now, returns mock structure for testing.
        """
        
        # PRODUCTION TODO: Implement full Adobe PDF Extract flow
        # https://developer.adobe.com/document-services/docs/overview/pdf-extract-api/
        
        logger.warning("Adobe API integration is a PLACEHOLDER - implement production flow")
        
        # Mock response for testing infrastructure
        mock_result = {
            "elements": [],
            "pages": [
                {
                    "page": 1,
                    "tables": []
                }
            ]
        }
        
        return mock_result
    
    def _convert_adobe_to_unified(self, adobe_data: Dict) -> Optional[List[UnifiedLayout]]:
        """
        Convert Adobe PDF Extract output to UnifiedLayout format.
        
        Adobe structure:
        {
          "elements": [...],
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
                      "Text": "Header 1"
                    }
                  ]
                }
              ]
            }
          ]
        }
        """
        
        try:
            unified_layouts = []
            
            for page_data in adobe_data.get('pages', []):
                page_num = page_data.get('page', 1)
                tables = page_data.get('tables', [])
                
                if not tables:
                    logger.info(f"Page {page_num}: No tables found by Adobe")
                    continue
                
                for table_idx, table in enumerate(tables):
                    cells = table.get('Cells', [])
                    
                    if not cells:
                        continue
                    
                    # Group cells by row
                    rows_dict = {}
                    max_row = 0
                    max_col = 0
                    
                    for cell in cells:
                        row_idx = cell.get('RowIndex', 0)
                        col_idx = cell.get('ColumnIndex', 0)
                        text = cell.get('Text', '').strip()
                        row_span = cell.get('RowSpan', 1)
                        col_span = cell.get('ColumnSpan', 1)
                        
                        max_row = max(max_row, row_idx)
                        max_col = max(max_col, col_idx)
                        
                        if row_idx not in rows_dict:
                            rows_dict[row_idx] = {}
                        
                        # Create CellData
                        cell_data = CellData(
                            text=text,
                            row_span=row_span,
                            col_span=col_span,
                            style=CellStyle(
                                bold=(row_idx == 0),  # First row is header
                                background_color='FFE0E0E0' if row_idx == 0 else None
                            ),
                            is_header=(row_idx == 0)
                        )
                        
                        rows_dict[row_idx][col_idx] = cell_data
                    
                    # Convert to list of lists
                    rows = []
                    for row_idx in sorted(rows_dict.keys()):
                        row = []
                        for col_idx in range(max_col + 1):
                            row.append(rows_dict[row_idx].get(col_idx, CellData(text="")))
                        rows.append(row)
                    
                    # Create UnifiedLayout
                    layout = UnifiedLayout(
                        rows=rows,
                        metadata={
                            'source': 'adobe',
                            'page': page_num,
                            'table_index': table_idx,
                            'total_rows': len(rows),
                            'total_columns': max_col + 1
                        }
                    )
                    
                    unified_layouts.append(layout)
                    logger.info(f"Converted Adobe table {table_idx+1}: {len(rows)} rows × {max_col+1} columns")
            
            return unified_layouts if unified_layouts else None
            
        except Exception as e:
            logger.error(f"Failed to convert Adobe data to UnifiedLayout: {e}", exc_info=True)
            return None
    
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

