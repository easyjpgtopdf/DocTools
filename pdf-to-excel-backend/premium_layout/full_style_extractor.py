"""
Full Style Extractor
Extracts complete style information (font, size, color) from Document AI.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FullStyleExtractor:
    """Extracts complete style information from Document AI blocks and tokens"""
    
    def __init__(self):
        """Initialize style extractor"""
        pass
    
    def extract_style_from_block(self, block: Any) -> Dict[str, Any]:
        """
        Extract style information from a Document AI block.
        
        Args:
            block: Document AI block object
            
        Returns:
            Dictionary with style information:
            - font_family: str or None
            - font_size: int or None
            - font_color: str (hex) or None
            - background_color: str (hex) or None
            - bold: bool
            - italic: bool
            - underline: bool
        """
        style_info = {
            'font_family': None,
            'font_size': None,
            'font_color': None,
            'background_color': None,
            'bold': False,
            'italic': False,
            'underline': False
        }
        
        if not block or not hasattr(block, 'layout'):
            return style_info
        
        layout = block.layout
        
        # Try to extract from tokens (more detailed style info)
        if hasattr(block, 'tokens') and block.tokens:
            style_info = self._extract_from_tokens(block.tokens, style_info)
        
        # Try to extract from layout properties
        if hasattr(layout, 'properties'):
            style_info = self._extract_from_properties(layout.properties, style_info)
        
        # Try to extract from detected languages (can indicate font)
        if hasattr(layout, 'detected_languages') and layout.detected_languages:
            # Some languages use specific fonts
            detected_lang = layout.detected_languages[0]
            if hasattr(detected_lang, 'language_code'):
                lang_code = detected_lang.language_code
                # Map language to likely font
                if lang_code in ['zh', 'ja', 'ko']:
                    style_info['font_family'] = 'Arial Unicode MS'  # Better for CJK
        
        return style_info
    
    def _extract_from_tokens(self, tokens: Any, style_info: Dict) -> Dict[str, Any]:
        """Extract style from tokens (more detailed)"""
        if not tokens:
            return style_info
        
        # Analyze tokens for style patterns
        font_sizes = []
        bold_count = 0
        italic_count = 0
        
        for token in tokens[:10]:  # Sample first 10 tokens
            if not hasattr(token, 'layout'):
                continue
            
            token_layout = token.layout
            
            # Try to get font size from bounding box height
            if hasattr(token_layout, 'bounding_poly'):
                bounding_poly = token_layout.bounding_poly
                if hasattr(bounding_poly, 'normalized_vertices'):
                    vertices = bounding_poly.normalized_vertices
                    if vertices and len(vertices) >= 2:
                        y_coords = [v.y for v in vertices if hasattr(v, 'y')]
                        if y_coords:
                            height = max(y_coords) - min(y_coords)
                            # Convert normalized height to approximate font size
                            # Assuming page height = 1.0, typical font = 0.01-0.02
                            if height > 0:
                                estimated_size = int(height * 1000)  # Rough estimate
                                if 8 <= estimated_size <= 72:  # Valid font size range
                                    font_sizes.append(estimated_size)
            
            # Check for style indicators in text anchor
            if hasattr(token_layout, 'text_anchor'):
                # Document AI doesn't directly provide bold/italic, but we can infer
                # from text patterns or use heuristics
                pass
        
        # Calculate average font size
        if font_sizes:
            avg_size = sum(font_sizes) / len(font_sizes)
            style_info['font_size'] = int(round(avg_size))
        
        # Heuristic: If most tokens are larger, might be bold
        if font_sizes and sum(font_sizes) / len(font_sizes) > 14:
            style_info['bold'] = True
        
        return style_info
    
    def _extract_from_properties(self, properties: Any, style_info: Dict) -> Dict[str, Any]:
        """Extract style from layout properties"""
        if not properties:
            return style_info
        
        # Document AI properties might contain style information
        # This depends on the processor type
        try:
            for prop in properties:
                if hasattr(prop, 'name') and hasattr(prop, 'value'):
                    prop_name = str(prop.name).lower() if prop.name else ''
                    prop_value = str(prop.value) if prop.value else ''
                    
                    # Look for font-related properties
                    if 'font' in prop_name:
                        if 'size' in prop_name or 'height' in prop_name:
                            try:
                                style_info['font_size'] = int(float(prop_value))
                            except:
                                pass
                        elif 'family' in prop_name or 'name' in prop_name:
                            style_info['font_family'] = prop_value
                    
                    # Look for color properties
                    elif 'color' in prop_name:
                        if 'text' in prop_name or 'foreground' in prop_name:
                            style_info['font_color'] = self._parse_color(prop_value)
                        elif 'background' in prop_name or 'fill' in prop_name:
                            style_info['background_color'] = self._parse_color(prop_value)
                    
                    # Look for style properties
                    elif 'bold' in prop_name:
                        style_info['bold'] = prop_value.lower() in ['true', '1', 'yes']
                    elif 'italic' in prop_name:
                        style_info['italic'] = prop_value.lower() in ['true', '1', 'yes']
                    elif 'underline' in prop_name:
                        style_info['underline'] = prop_value.lower() in ['true', '1', 'yes']
        except Exception as e:
            logger.debug(f"Error extracting from properties: {e}")
        
        return style_info
    
    def _parse_color(self, color_value: str) -> Optional[str]:
        """Parse color value to hex format"""
        if not color_value:
            return None
        
        color_str = str(color_value).strip().upper()
        
        # Already hex format
        if color_str.startswith('#'):
            if len(color_str) == 7:  # #RRGGBB
                return color_str
            elif len(color_str) == 4:  # #RGB
                return f"#{color_str[1]}{color_str[1]}{color_str[2]}{color_str[2]}{color_str[3]}{color_str[3]}"
        
        # RGB format: "rgb(255, 0, 0)"
        if color_str.startswith('RGB('):
            try:
                rgb_values = color_str[4:-1].split(',')
                if len(rgb_values) == 3:
                    r = int(rgb_values[0].strip())
                    g = int(rgb_values[1].strip())
                    b = int(rgb_values[2].strip())
                    return f"#{r:02X}{g:02X}{b:02X}"
            except:
                pass
        
        # Named colors (basic)
        color_map = {
            'BLACK': '#000000',
            'WHITE': '#FFFFFF',
            'RED': '#FF0000',
            'GREEN': '#00FF00',
            'BLUE': '#0000FF',
            'YELLOW': '#FFFF00',
            'CYAN': '#00FFFF',
            'MAGENTA': '#FF00FF'
        }
        
        if color_str in color_map:
            return color_map[color_str]
        
        return None
    
    def apply_style_to_cell(self, style_info: Dict, cell_style: Any) -> Any:
        """
        Apply extracted style information to a CellStyle object.
        
        Args:
            style_info: Style information dictionary
            cell_style: CellStyle object to update
            
        Returns:
            Updated CellStyle object
        """
        from .unified_layout_model import CellStyle
        
        if isinstance(cell_style, CellStyle):
            if style_info.get('font_size'):
                cell_style.font_size = style_info['font_size']
            if style_info.get('font_color'):
                cell_style.font_color = style_info['font_color']
            if style_info.get('background_color'):
                cell_style.background_color = style_info['background_color']
            if style_info.get('bold'):
                cell_style.bold = True
            if style_info.get('italic'):
                cell_style.italic = True
        
        return cell_style

