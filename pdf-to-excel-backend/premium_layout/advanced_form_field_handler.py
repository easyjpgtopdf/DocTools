"""
Advanced Form Field Handler
Handles complex form fields: checkboxes, radio buttons, multi-line fields.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AdvancedFormFieldHandler:
    """Handles advanced form field types"""
    
    def __init__(self):
        """Initialize form field handler"""
        pass
    
    def extract_advanced_fields(self, entities: List[Any], document_text: str) -> List[Dict[str, Any]]:
        """
        Extract advanced form fields with types and states.
        
        Args:
            entities: List of Document AI entities
            document_text: Full document text
            
        Returns:
            List of form field dictionaries with:
            - name: Field name
            - value: Field value
            - type: Field type (text, checkbox, radio, multiline)
            - state: Field state (checked, unchecked, selected, etc.)
            - confidence: Confidence score
        """
        advanced_fields = []
        
        for entity in entities:
            if not hasattr(entity, 'type_'):
                continue
            
            entity_type = str(entity.type_) if entity.type_ else ''
            
            # Check if it's a form field
            if 'form' not in entity_type.lower() and 'field' not in entity_type.lower():
                continue
            
            field_info = self._extract_field_info(entity, document_text)
            if field_info:
                advanced_fields.append(field_info)
        
        logger.info(f"Extracted {len(advanced_fields)} advanced form fields")
        return advanced_fields
    
    def _extract_field_info(self, entity: Any, document_text: str) -> Optional[Dict[str, Any]]:
        """Extract information from a form field entity"""
        field_info = {
            'name': '',
            'value': '',
            'type': 'text',  # Default type
            'state': None,
            'confidence': 1.0,
            'bounding_box': None
        }
        
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
                    bounding_poly = page_ref.bounding_poly
                    if hasattr(bounding_poly, 'normalized_vertices'):
                        vertices = bounding_poly.normalized_vertices
                        if vertices:
                            x_coords = [v.x for v in vertices if hasattr(v, 'x')]
                            y_coords = [v.y for v in vertices if hasattr(v, 'y')]
                            if x_coords and y_coords:
                                field_info['bounding_box'] = {
                                    'x_min': min(x_coords),
                                    'x_max': max(x_coords),
                                    'y_min': min(y_coords),
                                    'y_max': max(y_coords)
                                }
        
        # Extract name and value from properties
        if hasattr(entity, 'properties') and entity.properties:
            for prop in entity.properties:
                # Extract name
                if hasattr(prop, 'name'):
                    name_text = self._extract_text_from_property(prop.name, document_text)
                    if name_text:
                        field_info['name'] = name_text
                
                # Extract value
                if hasattr(prop, 'value'):
                    value_text = self._extract_text_from_property(prop.value, document_text)
                    if value_text:
                        field_info['value'] = value_text
                        
                        # Detect field type from value
                        field_info['type'], field_info['state'] = self._detect_field_type(value_text)
        
        # Detect field type from entity type
        entity_type = str(entity.type_) if hasattr(entity, 'type_') and entity.type_ else ''
        if 'checkbox' in entity_type.lower():
            field_info['type'] = 'checkbox'
            field_info['state'] = self._detect_checkbox_state(field_info['value'])
        elif 'radio' in entity_type.lower():
            field_info['type'] = 'radio'
            field_info['state'] = 'selected' if field_info['value'] else 'unselected'
        elif 'multiline' in entity_type.lower() or '\n' in field_info.get('value', ''):
            field_info['type'] = 'multiline'
        
        if field_info['name'] or field_info['value']:
            return field_info
        
        return None
    
    def _extract_text_from_property(self, prop: Any, document_text: str) -> str:
        """Extract text from a property"""
        if not prop:
            return ''
        
        # Try text_anchor
        if hasattr(prop, 'text_anchor') and prop.text_anchor:
            if hasattr(prop.text_anchor, 'text_segments'):
                text_parts = []
                for segment in prop.text_anchor.text_segments:
                    if hasattr(segment, 'start_index') and hasattr(segment, 'end_index'):
                        start = int(segment.start_index) if segment.start_index is not None else 0
                        end = int(segment.end_index) if segment.end_index is not None else 0
                        if start < len(document_text) and end <= len(document_text) and start < end:
                            text_parts.append(document_text[start:end])
                return ' '.join(text_parts).strip()
        
        # Try text_content
        if hasattr(prop, 'text_content'):
            return str(prop.text_content).strip()
        
        return ''
    
    def _detect_field_type(self, value: str) -> tuple:
        """Detect field type and state from value"""
        if not value:
            return ('text', None)
        
        value_lower = value.lower().strip()
        
        # Checkbox detection
        checkbox_indicators = ['✓', '☑', '×', '☐', 'checked', 'unchecked', 'yes', 'no', 'true', 'false']
        if any(indicator in value_lower for indicator in checkbox_indicators):
            state = 'checked' if value_lower in ['✓', '☑', 'checked', 'yes', 'true'] else 'unchecked'
            return ('checkbox', state)
        
        # Radio button detection
        radio_indicators = ['○', '●', 'selected', 'unselected']
        if any(indicator in value_lower for indicator in radio_indicators):
            state = 'selected' if value_lower in ['●', 'selected'] else 'unselected'
            return ('radio', state)
        
        # Multiline detection
        if '\n' in value or len(value) > 100:
            return ('multiline', None)
        
        return ('text', None)
    
    def _detect_checkbox_state(self, value: str) -> str:
        """Detect checkbox state from value"""
        if not value:
            return 'unchecked'
        
        value_lower = value.lower().strip()
        checked_indicators = ['✓', '☑', 'checked', 'yes', 'true', '1', 'x']
        
        if any(indicator in value_lower for indicator in checked_indicators):
            return 'checked'
        
        return 'unchecked'
    
    def format_field_for_excel(self, field: Dict[str, Any]) -> str:
        """Format form field for Excel display"""
        field_type = field.get('type', 'text')
        field_name = field.get('name', '')
        field_value = field.get('value', '')
        field_state = field.get('state')
        
        if field_type == 'checkbox':
            checkbox_symbol = '✓' if field_state == 'checked' else '☐'
            return f"{field_name}: {checkbox_symbol}"
        elif field_type == 'radio':
            radio_symbol = '●' if field_state == 'selected' else '○'
            return f"{field_name}: {radio_symbol} {field_value}"
        elif field_type == 'multiline':
            return f"{field_name}:\n{field_value}"
        else:
            return f"{field_name}: {field_value}"

