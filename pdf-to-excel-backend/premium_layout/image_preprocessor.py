"""
Image Pre-Processor
Enhances images for better OCR accuracy (sharpening, contrast, noise reduction).
"""

import logging
from typing import Optional
from io import BytesIO

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available for image preprocessing")

logger = logging.getLogger(__name__)


class ImagePreProcessor:
    """Pre-processes images to improve OCR accuracy"""
    
    def __init__(self):
        """Initialize image preprocessor"""
        self.enhance_sharpness = True
        self.enhance_contrast = True
        self.reduce_noise = True
        self.auto_orient = True
    
    def preprocess_image(self, image_bytes: bytes, enhance_for_ocr: bool = True) -> Optional[bytes]:
        """
        Pre-process image to improve quality for OCR.
        
        Args:
            image_bytes: Original image bytes
            enhance_for_ocr: Whether to apply OCR-specific enhancements
            
        Returns:
            Pre-processed image bytes or None if processing fails
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL not available, returning original image")
            return image_bytes
        
        try:
            # Open image
            img = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode not in ('RGB', 'L'):
                if img.mode == 'RGBA':
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = img.convert('RGB')
            
            # Auto-orient based on EXIF
            if self.auto_orient and hasattr(img, '_getexif'):
                try:
                    from PIL.ExifTags import ORIENTATION
                    exif = img._getexif()
                    if exif:
                        orientation = exif.get(ORIENTATION)
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
                except:
                    pass
            
            if enhance_for_ocr:
                # Enhance contrast
                if self.enhance_contrast:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(1.2)  # Increase contrast by 20%
                
                # Enhance sharpness
                if self.enhance_sharpness:
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.3)  # Increase sharpness by 30%
                
                # Reduce noise (light denoising)
                if self.reduce_noise:
                    # Light smoothing to reduce noise without losing detail
                    img = img.filter(ImageFilter.SMOOTH_MORE)
            
            # Convert back to bytes
            output = BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            return output.getvalue()
        
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original")
            return image_bytes
    
    def enhance_for_ocr(self, image_bytes: bytes) -> Optional[bytes]:
        """Alias for preprocess_image with OCR enhancements"""
        return self.preprocess_image(image_bytes, enhance_for_ocr=True)
    
    def detect_image_quality(self, image_bytes: bytes) -> Dict[str, float]:
        """
        Detect image quality metrics.
        
        Returns:
            Dictionary with quality metrics:
            - sharpness: float (0-1)
            - contrast: float (0-1)
            - brightness: float (0-1)
            - needs_enhancement: bool
        """
        if not PIL_AVAILABLE:
            return {
                'sharpness': 0.5,
                'contrast': 0.5,
                'brightness': 0.5,
                'needs_enhancement': False
            }
        
        try:
            img = Image.open(BytesIO(image_bytes))
            img = img.convert('RGB')
            
            # Simple quality metrics
            # Sharpness: variance of Laplacian (simplified)
            # Contrast: standard deviation of pixel values
            # Brightness: mean pixel value
            
            import numpy as np
            img_array = np.array(img)
            
            # Brightness (mean)
            brightness = np.mean(img_array) / 255.0
            
            # Contrast (standard deviation)
            contrast = np.std(img_array) / 255.0
            
            # Sharpness (simplified - edge detection)
            from PIL import ImageFilter
            edges = img.filter(ImageFilter.FIND_EDGES)
            edge_array = np.array(edges)
            sharpness = np.std(edge_array) / 255.0
            
            needs_enhancement = (
                sharpness < 0.3 or  # Low sharpness
                contrast < 0.2 or   # Low contrast
                brightness < 0.2 or brightness > 0.8  # Too dark or too bright
            )
            
            return {
                'sharpness': float(sharpness),
                'contrast': float(contrast),
                'brightness': float(brightness),
                'needs_enhancement': needs_enhancement
            }
        
        except Exception as e:
            logger.debug(f"Quality detection failed: {e}")
            return {
                'sharpness': 0.5,
                'contrast': 0.5,
                'brightness': 0.5,
                'needs_enhancement': False
            }

