"""
Image Extractor for Document AI
Extracts images from Document AI response and prepares them for Excel insertion.
"""

import logging
import base64
import io
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ImageExtractor:
    """Extracts images from Document AI document"""
    
    def __init__(self):
        """Initialize image extractor"""
        pass
    
    def extract_images_from_document(self, document: Any) -> List[Dict[str, Any]]:
        """
        Extract all images from Document AI document.
        
        Args:
            document: Document AI Document object
            
        Returns:
            List of image dictionaries with:
            - image_bytes: bytes
            - page_index: int
            - position: (x, y) normalized coordinates
            - width: float
            - height: float
        """
        images = []
        
        if not hasattr(document, 'pages') or not document.pages:
            logger.debug("No pages found in document")
            return images
        
        for page_idx, page in enumerate(document.pages):
            page_images = self._extract_images_from_page(page, page_idx)
            images.extend(page_images)
        
        logger.info(f"Extracted {len(images)} images from document")
        return images
    
    def _extract_images_from_page(self, page: Any, page_idx: int) -> List[Dict[str, Any]]:
        """Extract images from a single page"""
        images = []
        
        # Method 1: Check for blocks with image type
        if hasattr(page, 'blocks') and page.blocks:
            for block in page.blocks:
                if hasattr(block, 'layout') and hasattr(block.layout, 'text_anchor'):
                    # This is a text block, skip
                    continue
                
                # Check if block might contain image
                if hasattr(block, 'layout'):
                    layout = block.layout
                    if hasattr(layout, 'bounding_poly'):
                        # Try to extract image data
                        image_data = self._extract_image_from_block(block)
                        if image_data:
                            position = self._get_bounding_box_position(layout.bounding_poly)
                            images.append({
                                'image_bytes': image_data,
                                'page_index': page_idx,
                                'position': position,
                                'width': position[2] if len(position) > 2 else 0.1,
                                'height': position[3] if len(position) > 3 else 0.1
                            })
        
        # Method 2: Check for entities that might be images
        if hasattr(page, 'entities') and page.entities:
            for entity in page.entities:
                if hasattr(entity, 'type') and 'image' in str(entity.type).lower():
                    image_data = self._extract_image_from_entity(entity)
                    if image_data:
                        position = (0.0, 0.0, 0.1, 0.1)  # Default position
                        if hasattr(entity, 'page_anchor') and entity.page_anchor:
                            if hasattr(entity.page_anchor, 'page_refs') and entity.page_anchor.page_refs:
                                page_ref = entity.page_anchor.page_refs[0]
                                if hasattr(page_ref, 'bounding_poly'):
                                    position = self._get_bounding_box_position(page_ref.bounding_poly)
                        
                        images.append({
                            'image_bytes': image_data,
                            'page_index': page_idx,
                            'position': position,
                            'width': position[2] if len(position) > 2 else 0.1,
                            'height': position[3] if len(position) > 3 else 0.1
                        })
        
        # Method 3: Check for visual elements (some Document AI versions)
        if hasattr(page, 'visual_elements') and page.visual_elements:
            for visual_elem in page.visual_elements:
                if hasattr(visual_elem, 'layout'):
                    image_data = self._extract_image_from_visual_element(visual_elem)
                    if image_data:
                        position = self._get_bounding_box_position(visual_elem.layout.bounding_poly)
                        images.append({
                            'image_bytes': image_data,
                            'page_index': page_idx,
                            'position': position,
                            'width': position[2] if len(position) > 2 else 0.1,
                            'height': position[3] if len(position) > 3 else 0.1
                        })
        
        return images
    
    def _extract_image_from_block(self, block: Any) -> Optional[bytes]:
        """Extract image data from a block"""
        try:
            # Document AI blocks don't directly contain image data
            # Images are usually referenced via GCS or embedded differently
            # For now, return None as we need GCS access for actual image data
            return None
        except Exception as e:
            logger.debug(f"Error extracting image from block: {e}")
            return None
    
    def _extract_image_from_entity(self, entity: Any) -> Optional[bytes]:
        """Extract image data from an entity"""
        try:
            # Check for image properties in entity
            if hasattr(entity, 'properties'):
                for prop in entity.properties:
                    if hasattr(prop, 'image_value') and prop.image_value:
                        # Try to get image bytes
                        if hasattr(prop.image_value, 'content'):
                            return prop.image_value.content
                        elif hasattr(prop.image_value, 'mime_type'):
                            # Image might be referenced, not embedded
                            return None
            return None
        except Exception as e:
            logger.debug(f"Error extracting image from entity: {e}")
            return None
    
    def _extract_image_from_visual_element(self, visual_elem: Any) -> Optional[bytes]:
        """Extract image data from visual element"""
        try:
            # Visual elements might contain image references
            # Actual image data extraction depends on Document AI version
            return None
        except Exception as e:
            logger.debug(f"Error extracting image from visual element: {e}")
            return None
    
    def _get_bounding_box_position(self, bounding_poly: Any) -> Tuple[float, float, float, float]:
        """Get normalized position from bounding polygon"""
        try:
            if not hasattr(bounding_poly, 'normalized_vertices'):
                return (0.0, 0.0, 0.1, 0.1)
            
            vertices = bounding_poly.normalized_vertices
            if not vertices or len(vertices) < 2:
                return (0.0, 0.0, 0.1, 0.1)
            
            x_coords = [v.x for v in vertices if hasattr(v, 'x')]
            y_coords = [v.y for v in vertices if hasattr(v, 'y')]
            
            if not x_coords or not y_coords:
                return (0.0, 0.0, 0.1, 0.1)
            
            x_min = min(x_coords)
            x_max = max(x_coords)
            y_min = min(y_coords)
            y_max = max(y_coords)
            
            return (x_min, y_min, x_max - x_min, y_max - y_min)
        except Exception as e:
            logger.debug(f"Error getting bounding box position: {e}")
            return (0.0, 0.0, 0.1, 0.1)
    
    def prepare_image_for_excel(self, image_bytes: bytes, max_width: int = 200, max_height: int = 200) -> Optional[bytes]:
        """
        Prepare image bytes for Excel insertion (resize if needed, convert format).
        
        Args:
            image_bytes: Original image bytes
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            
        Returns:
            Prepared image bytes (PNG format)
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not available, using image bytes as-is")
            return image_bytes
        
        try:
            # Open image
            img = PILImage.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = PILImage.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
            
            # Convert to bytes (PNG format for Excel compatibility)
            output = BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            return output.getvalue()
        
        except Exception as e:
            logger.warning(f"Error preparing image for Excel: {e}, using original bytes")
            return image_bytes

