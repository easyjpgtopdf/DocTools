"""
Full OCR Extractor - Uses Document AI's Complete Capabilities
Extracts text using blocks, detected breaks, confidence scores, and full structure.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

try:
    from .full_style_extractor import FullStyleExtractor
    from .advanced_form_field_handler import AdvancedFormFieldHandler
    STYLE_EXTRACTOR_AVAILABLE = True
except ImportError:
    STYLE_EXTRACTOR_AVAILABLE = False

logger = logging.getLogger(__name__)


class BlockType(Enum):
    """Document AI block types"""
    UNKNOWN = 0
    TEXT = 1
    TABLE = 2
    PICTURE = 3
    RULER = 4
    BARCODE = 5
    FORM_FIELD = 6


class BreakType(Enum):
    """Document AI detected break types"""
    UNKNOWN = 0
    SPACE = 1
    WIDE_SPACE = 2
    LINE_BREAK = 3
    PARAGRAPH_BREAK = 4
    EOL_SURE_SPACE = 5
    HYPHEN = 6


class FullOCRExtractor:
    """
    Extracts text using Document AI's full capabilities:
    - Blocks with types
    - Detected breaks
    - Confidence scores
    - Proper hierarchy
    """
    
    def __init__(self, min_confidence: float = 0.5):
        """
        Initialize OCR extractor.
        
        Args:
            min_confidence: Minimum confidence score to accept text (0.0-1.0)
        """
        self.min_confidence = min_confidence
        self.style_extractor = None
        self.form_field_handler = None
        
        if STYLE_EXTRACTOR_AVAILABLE:
            try:
                self.style_extractor = FullStyleExtractor()
                self.form_field_handler = AdvancedFormFieldHandler()
            except Exception as e:
                logger.debug(f"Style extractor initialization failed: {e}")
    
    def extract_full_structure(self, document: Any) -> Dict[str, Any]:
        """
        Extract full document structure using Document AI's complete capabilities.
        
        Args:
            document: Document AI Document object
            
        Returns:
            Dictionary with:
            - pages: List of page structures
            - blocks: All blocks with types and confidence
            - form_fields: Extracted form fields
            - tables: Enhanced table structures
            - images: Image references
        """
        result = {
            'pages': [],
            'blocks': [],
            'form_fields': [],
            'tables': [],
            'images': [],
            'total_confidence': 0.0,
            'avg_confidence': 0.0
        }
        
        if not hasattr(document, 'pages') or not document.pages:
            logger.warning("No pages found in document")
            return result
        
        total_confidence = 0.0
        confidence_count = 0
        
        # Process each page
        for page_idx, page in enumerate(document.pages):
            page_structure = self._extract_page_structure(page, page_idx, document.text if hasattr(document, 'text') else '')
            result['pages'].append(page_structure)
            
            # Collect blocks
            if 'blocks' in page_structure:
                result['blocks'].extend(page_structure['blocks'])
            
            # Collect form fields
            if 'form_fields' in page_structure:
                result['form_fields'].extend(page_structure['form_fields'])
            
            # Collect tables
            if 'tables' in page_structure:
                result['tables'].extend(page_structure['tables'])
            
            # Collect images
            if 'images' in page_structure:
                result['images'].extend(page_structure['images'])
            
            # Collect confidence scores
            if 'avg_confidence' in page_structure:
                total_confidence += page_structure['avg_confidence']
                confidence_count += 1
        
        # Calculate overall confidence
        if confidence_count > 0:
            result['avg_confidence'] = total_confidence / confidence_count
            result['total_confidence'] = total_confidence
        
        logger.info(f"Extracted structure: {len(result['blocks'])} blocks, "
                   f"{len(result['form_fields'])} form fields, "
                   f"{len(result['tables'])} tables, "
                   f"avg confidence: {result['avg_confidence']:.2f}")
        
        return result
    
    def _extract_page_structure(self, page: Any, page_idx: int, document_text: str) -> Dict[str, Any]:
        """Extract structure from a single page"""
        page_structure = {
            'page_index': page_idx,
            'blocks': [],
            'form_fields': [],
            'tables': [],
            'images': [],
            'avg_confidence': 0.0
        }
        
        # Extract blocks with full information
        if hasattr(page, 'blocks') and page.blocks:
            total_confidence = 0.0
            confidence_count = 0
            
            for block in page.blocks:
                block_info = self._extract_block_info(block, document_text)
                if block_info:
                    page_structure['blocks'].append(block_info)
                    
                    # Track confidence
                    if 'confidence' in block_info:
                        total_confidence += block_info['confidence']
                        confidence_count += 1
            
            if confidence_count > 0:
                page_structure['avg_confidence'] = total_confidence / confidence_count
        
        # Extract form fields (with advanced handler if available)
        if self.form_field_handler and hasattr(page, 'entities') and page.entities:
            page_structure['form_fields'] = self.form_field_handler.extract_advanced_fields(
                page.entities, document_text
            )
        else:
            page_structure['form_fields'] = self._extract_form_fields(page, document_text)
        
        # Extract tables with enhanced info
        page_structure['tables'] = self._extract_enhanced_tables(page, document_text)
        
        # Extract images
        page_structure['images'] = self._extract_image_references(page)
        
        return page_structure
    
    def _extract_block_info(self, block: Any, document_text: str) -> Optional[Dict[str, Any]]:
        """Extract information from a block"""
        if not hasattr(block, 'layout'):
            return None
        
        layout = block.layout
        if not layout:
            return None
        
        block_info = {
            'type': 'UNKNOWN',
            'text': '',
            'confidence': 1.0,
            'bounding_box': None,
            'detected_breaks': [],
            'children': []
        }
        
        # Get block type
        if hasattr(layout, 'block_type'):
            try:
                block_type = layout.block_type
                block_info['type'] = str(block_type) if block_type else 'TEXT'
            except:
                block_info['type'] = 'TEXT'
        
        # Get confidence score
        if hasattr(layout, 'confidence'):
            try:
                confidence = float(layout.confidence) if layout.confidence is not None else 1.0
                block_info['confidence'] = confidence
            except:
                block_info['confidence'] = 1.0
        
        # Filter by confidence
        if block_info['confidence'] < self.min_confidence:
            logger.debug(f"Block filtered due to low confidence: {block_info['confidence']}")
            return None
        
        # Get bounding box
        if hasattr(layout, 'bounding_poly'):
            block_info['bounding_box'] = self._get_bounding_box(layout.bounding_poly)
        
        # Get detected breaks
        if hasattr(layout, 'detected_break'):
            break_info = self._extract_break_info(layout.detected_break)
            if break_info:
                block_info['detected_breaks'].append(break_info)
        
        # Get text
        if hasattr(layout, 'text_anchor') and layout.text_anchor:
            block_info['text'] = self._extract_text_from_anchor(layout.text_anchor, document_text)
        
        # Extract style information if available
        if self.style_extractor:
            try:
                style_info = self.style_extractor.extract_style_from_block(block)
                block_info['style'] = style_info
            except Exception as e:
                logger.debug(f"Style extraction failed: {e}")
        
        # Get child blocks (if any)
        if hasattr(block, 'blocks') and block.blocks:
            for child_block in block.blocks:
                child_info = self._extract_block_info(child_block, document_text)
                if child_info:
                    block_info['children'].append(child_info)
        
        return block_info
    
    def _extract_break_info(self, detected_break: Any) -> Optional[Dict[str, Any]]:
        """Extract break information"""
        if not detected_break:
            return None
        
        break_info = {
            'type': 'UNKNOWN'
        }
        
        if hasattr(detected_break, 'type_'):
            try:
                break_type = detected_break.type_
                break_info['type'] = str(break_type) if break_type else 'UNKNOWN'
            except:
                pass
        
        return break_info
    
    def _extract_text_from_anchor(self, text_anchor: Any, document_text: str) -> str:
        """Extract text from text anchor"""
        if not text_anchor or not hasattr(text_anchor, 'text_segments'):
            return ''
        
        text_parts = []
        for segment in text_anchor.text_segments:
            if hasattr(segment, 'start_index') and hasattr(segment, 'end_index'):
                start = int(segment.start_index) if segment.start_index is not None else 0
                end = int(segment.end_index) if segment.end_index is not None else 0
                
                if start < len(document_text) and end <= len(document_text) and start < end:
                    text_parts.append(document_text[start:end])
        
        return ' '.join(text_parts).strip()
    
    def _get_bounding_box(self, bounding_poly: Any) -> Optional[Dict[str, float]]:
        """Get bounding box from polygon"""
        if not bounding_poly or not hasattr(bounding_poly, 'normalized_vertices'):
            return None
        
        vertices = bounding_poly.normalized_vertices
        if not vertices or len(vertices) < 2:
            return None
        
        x_coords = [v.x for v in vertices if hasattr(v, 'x')]
        y_coords = [v.y for v in vertices if hasattr(v, 'y')]
        
        if not x_coords or not y_coords:
            return None
        
        return {
            'x_min': min(x_coords),
            'x_max': max(x_coords),
            'y_min': min(y_coords),
            'y_max': max(y_coords),
            'x_center': (min(x_coords) + max(x_coords)) / 2,
            'y_center': (min(y_coords) + max(y_coords)) / 2,
            'width': max(x_coords) - min(x_coords),
            'height': max(y_coords) - min(y_coords)
        }
    
    def _extract_form_fields(self, page: Any, document_text: str) -> List[Dict[str, Any]]:
        """Extract form fields from page"""
        form_fields = []
        
        # Method 1: Check entities
        if hasattr(page, 'entities') and page.entities:
            for entity in page.entities:
                if hasattr(entity, 'type_'):
                    entity_type = str(entity.type_) if entity.type_ else ''
                    if 'form' in entity_type.lower() or 'field' in entity_type.lower():
                        field_info = self._extract_entity_as_form_field(entity, document_text)
                        if field_info:
                            form_fields.append(field_info)
        
        # Method 2: Check blocks with FORM_FIELD type
        if hasattr(page, 'blocks') and page.blocks:
            for block in page.blocks:
                if hasattr(block, 'layout') and hasattr(block.layout, 'block_type'):
                    try:
                        if 'FORM' in str(block.layout.block_type) or 'FIELD' in str(block.layout.block_type):
                            field_info = self._extract_block_as_form_field(block, document_text)
                            if field_info:
                                form_fields.append(field_info)
                    except:
                        pass
        
        return form_fields
    
    def _extract_entity_as_form_field(self, entity: Any, document_text: str) -> Optional[Dict[str, Any]]:
        """Extract form field from entity"""
        field_info = {
            'name': '',
            'value': '',
            'confidence': 1.0,
            'type': 'text',
            'bounding_box': None
        }
        
        # Get field name and value from properties
        if hasattr(entity, 'properties') and entity.properties:
            for prop in entity.properties:
                if hasattr(prop, 'name') and prop.name:
                    # Try to extract name
                    if hasattr(prop.name, 'text_anchor'):
                        field_info['name'] = self._extract_text_from_anchor(prop.name.text_anchor, document_text)
                    elif hasattr(prop.name, 'text_content'):
                        field_info['name'] = str(prop.name.text_content)
                
                if hasattr(prop, 'value') and prop.value:
                    # Try to extract value
                    if hasattr(prop.value, 'text_anchor'):
                        field_info['value'] = self._extract_text_from_anchor(prop.value.text_anchor, document_text)
                    elif hasattr(prop.value, 'text_content'):
                        field_info['value'] = str(prop.value.text_content)
        
        # Get confidence
        if hasattr(entity, 'confidence'):
            try:
                field_info['confidence'] = float(entity.confidence) if entity.confidence is not None else 1.0
            except:
                pass
        
        # Get bounding box
        if hasattr(entity, 'page_anchor') and entity.page_anchor:
            if hasattr(entity.page_anchor, 'page_refs') and entity.page_anchor.page_refs:
                page_ref = entity.page_anchor.page_refs[0]
                if hasattr(page_ref, 'bounding_poly'):
                    field_info['bounding_box'] = self._get_bounding_box(page_ref.bounding_poly)
        
        if field_info['name'] or field_info['value']:
            return field_info
        
        return None
    
    def _extract_block_as_form_field(self, block: Any, document_text: str) -> Optional[Dict[str, Any]]:
        """Extract form field from block"""
        # Similar to entity extraction
        return self._extract_entity_as_form_field(block, document_text)
    
    def _extract_enhanced_tables(self, page: Any, document_text: str) -> List[Dict[str, Any]]:
        """Extract tables with enhanced information"""
        tables = []
        
        if hasattr(page, 'tables') and page.tables:
            for table_idx, table in enumerate(page.tables):
                table_info = {
                    'table_index': table_idx,
                    'header_rows': [],
                    'body_rows': [],
                    'confidence': 1.0,
                    'bounding_box': None
                }
                
                # Get table confidence
                if hasattr(table, 'confidence'):
                    try:
                        table_info['confidence'] = float(table.confidence) if table.confidence is not None else 1.0
                    except:
                        pass
                
                # Get bounding box
                if hasattr(table, 'layout') and hasattr(table.layout, 'bounding_poly'):
                    table_info['bounding_box'] = self._get_bounding_box(table.layout.bounding_poly)
                
                # Extract header rows
                if hasattr(table, 'header_rows') and table.header_rows:
                    for header_row in table.header_rows:
                        row_data = self._extract_table_row(header_row, document_text)
                        if row_data:
                            table_info['header_rows'].append(row_data)
                
                # Extract body rows
                if hasattr(table, 'body_rows') and table.body_rows:
                    for body_row in table.body_rows:
                        row_data = self._extract_table_row(body_row, document_text)
                        if row_data:
                            table_info['body_rows'].append(row_data)
                
                tables.append(table_info)
        
        return tables
    
    def _extract_table_row(self, row: Any, document_text: str) -> Optional[List[Dict[str, Any]]]:
        """Extract row data with cell information"""
        if not hasattr(row, 'cells') or not row.cells:
            return None
        
        row_data = []
        for cell in row.cells:
            cell_info = {
                'text': '',
                'confidence': 1.0,
                'bounding_box': None
            }
            
            # Get text
            if hasattr(cell, 'layout') and hasattr(cell.layout, 'text_anchor'):
                cell_info['text'] = self._extract_text_from_anchor(cell.layout.text_anchor, document_text)
            
            # Get confidence
            if hasattr(cell, 'layout') and hasattr(cell.layout, 'confidence'):
                try:
                    cell_info['confidence'] = float(cell.layout.confidence) if cell.layout.confidence is not None else 1.0
                except:
                    pass
            
            # Get bounding box
            if hasattr(cell, 'layout') and hasattr(cell.layout, 'bounding_poly'):
                cell_info['bounding_box'] = self._get_bounding_box(cell.layout.bounding_poly)
            
            row_data.append(cell_info)
        
        return row_data
    
    def _extract_image_references(self, page: Any) -> List[Dict[str, Any]]:
        """Extract image references (including GCS URIs)"""
        images = []
        
        # Check for image blocks
        if hasattr(page, 'blocks') and page.blocks:
            for block in page.blocks:
                if hasattr(block, 'layout') and hasattr(block.layout, 'block_type'):
                    try:
                        block_type = str(block.layout.block_type) if block.layout.block_type else ''
                        if 'PICTURE' in block_type or 'IMAGE' in block_type:
                            image_info = {
                                'type': 'block',
                                'bounding_box': None,
                                'gcs_uri': None,
                                'confidence': 1.0
                            }
                            
                            if hasattr(block.layout, 'bounding_poly'):
                                image_info['bounding_box'] = self._get_bounding_box(block.layout.bounding_poly)
                            
                            if hasattr(block.layout, 'confidence'):
                                try:
                                    image_info['confidence'] = float(block.layout.confidence) if block.layout.confidence is not None else 1.0
                                except:
                                    pass
                            
                            images.append(image_info)
                    except:
                        pass
        
        return images

