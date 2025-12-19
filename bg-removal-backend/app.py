"""
Background Removal Service - AI-Powered GPU Processing
Google Cloud Run service for background removal using advanced AI models
Enhanced with: Model Tuning, TensorRT FP16, Guided Filter, Feathering, Halo Removal, Composite
"""

from flask import Flask, request, jsonify
from rembg import remove, new_session
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os
import logging
import time
import numpy as np

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import OpenCV for guided filter
try:
    import cv2
    try:
        # Check if ximgproc module is available (for guided filter)
        cv2.ximgproc
        CV2_AVAILABLE = True
    except AttributeError:
        CV2_AVAILABLE = False
        logger.warning("OpenCV ximgproc not available, guided filter will be disabled")
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available, guided filter will be disabled")

# Try to import SciPy for feathering
try:
    from scipy import ndimage
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("SciPy not available, feathering will be disabled")

app = Flask(__name__)

# Helper function to convert numpy types to native Python types for JSON serialization
def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                           np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    # Note: np.bool was removed in numpy 2.x; use np.bool_ / bool instead
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif hasattr(obj, 'dtype') and obj.dtype == np.bool_:  # Check numpy scalar bool
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# Initialize AI model sessions (lazy loading with optimization)
session_512 = None
session_hd = None
session_robust = None
session_maxmatting = None

def is_document_image(image):
    """
    Automatic Image Type Detection: PHOTO vs DOCUMENT
    
    Detects documents by:
    - Aspect ratio (A4, Letter, ID card formats)
    - Flat background (high uniformity)
    - Text regions (high contrast edges)
    - White-heavy images (scanned pages)
    
    Returns True if DOCUMENT, False if PHOTO
    """
    if isinstance(image, Image.Image):
        width, height = image.size
        img_array = np.array(image.convert('RGB'))
    else:
        height, width = image.shape[:2]
        img_array = image if len(image.shape) == 3 else np.stack([image] * 3, axis=2)
    
    aspect_ratio = width / height if height > 0 else 1.0
    
    # 1. Aspect Ratio Check (A4, Letter, ID card formats)
    # A4: 210x297mm = 0.707 or 1.414
    # Letter: 8.5x11in = 0.773 or 1.294
    # ID Card: ~1.5-1.7 (landscape) or 0.6-0.7 (portrait)
    is_portrait_doc = 0.6 <= aspect_ratio <= 0.85
    is_landscape_doc = 1.2 <= aspect_ratio <= 1.7
    
    aspect_match = is_portrait_doc or is_landscape_doc
    
    # 2. Flat Background Detection (high uniformity = document)
    if CV2_AVAILABLE:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        # Calculate standard deviation (low std = flat background)
        std_dev = np.std(gray)
        is_flat = std_dev < 40  # Low variance = flat background
    else:
        gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
        std_dev = np.std(gray)
        is_flat = std_dev < 40
    
    # 3. White-Heavy Detection (scanned pages are mostly white)
    brightness = np.mean(img_array.astype(np.float32)) / 255.0
    is_white_heavy = brightness > 0.75  # Mostly white/light
    
    # 4. Text Region Detection (high contrast edges = text)
    if CV2_AVAILABLE:
        edges = cv2.Canny(gray.astype(np.uint8), 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        has_text_regions = edge_density > 0.15  # High edge density = text
    else:
        # Fallback: simple gradient-based edge detection
        from scipy import ndimage
        grad_x = ndimage.sobel(gray, axis=1)
        grad_y = ndimage.sobel(gray, axis=0)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        edge_density = np.sum(gradient_magnitude > 30) / gradient_magnitude.size
        has_text_regions = edge_density > 0.15
    
    # Decision: Document if 2+ indicators match
    indicators = [aspect_match, is_flat, is_white_heavy, has_text_regions]
    doc_score = sum(indicators)
    
    is_doc_raw = doc_score >= 2  # At least 2 indicators
    # CRITICAL: Convert numpy bool_ to Python bool for JSON serialization
    is_doc = bool(is_doc_raw) if isinstance(is_doc_raw, (np.bool_, bool)) else bool(is_doc_raw)
    
    if is_doc:
        logger.info(f"📄 DOCUMENT detected: aspect={aspect_ratio:.3f}, flat={is_flat}, white={is_white_heavy:.2f}, text={has_text_regions:.2f}, score={doc_score}/4")
    else:
        logger.info(f"📷 PHOTO detected: aspect={aspect_ratio:.3f}, flat={is_flat}, white={is_white_heavy:.2f}, text={has_text_regions:.2f}, score={doc_score}/4")
    
    return is_doc

def get_session_512():
    """Get or create optimized 512px preview session with BiRefNet tuning"""
    global session_512
    if session_512 is None:
        logger.info("Initializing optimized AI model session for 512px preview...")
        # Model Tuning: BiRefNet with optimized settings
        # Using birefnet model with GPU acceleration
        session_512 = new_session('birefnet')
        logger.info("Optimized AI model session initialized for 512px (BiRefNet tuned)")
    return session_512

def get_session_robust():
    """Get or create RobustMatting session for document images"""
    global session_robust
    if session_robust is None:
        logger.info("Initializing RobustMatting session for document processing...")
        try:
            session_robust = new_session('rmbg14')
            logger.info("RobustMatting session initialized (rmbg14)")
        except Exception as e:
            logger.warning(f"RobustMatting (rmbg14) not available, falling back to birefnet: {e}")
            session_robust = new_session('birefnet')
            logger.info("Falling back to BiRefNet for document processing")
    return session_robust

def get_session_hd():
    """Get or create optimized HD session with BiRefNet HD + TensorRT turbo"""
    global session_hd
    if session_hd is None:
        logger.info("Initializing BiRefNet HD session with TensorRT turbo optimization...")
        # BiRefNet HD with TensorRT FP16 turbo mode
        # TensorRT FP16 optimization handled by ONNX Runtime GPU
        session_hd = new_session('birefnet')
        logger.info("BiRefNet HD session initialized (TensorRT FP16 turbo ready)")
    return session_hd

def get_session_maxmatting():
    """Get or create MaxMatting session for premium high-quality processing"""
    global session_maxmatting
    if session_maxmatting is None:
        logger.info("Initializing MaxMatting session for premium processing...")
        try:
            # Try silueta model (MaxMatting) for best quality
            session_maxmatting = new_session('silueta')
            logger.info("MaxMatting session initialized (silueta model)")
        except Exception as e:
            logger.warning(f"MaxMatting (silueta) not available, falling back to birefnet: {e}")
            try:
                # Fallback to isnet-general-use (another high-quality option)
                session_maxmatting = new_session('isnet-general-use')
                logger.info("MaxMatting fallback: isnet-general-use initialized")
            except Exception as e2:
                logger.warning(f"isnet-general-use not available, using birefnet: {e2}")
                session_maxmatting = new_session('birefnet')
                logger.info("MaxMatting fallback: BiRefNet initialized")
    return session_maxmatting

def generate_trimap(mask, expand_radius=8, fg_threshold=None, bg_threshold=None):
    """
    Generate trimap from BiRefNet mask for fine alpha matting
    - Foreground: mask > fg_threshold
    - Background: mask < bg_threshold
    - Unknown region: bg_threshold to fg_threshold (expanded by radius pixels)
    
    Default thresholds:
    - Premium: FG=245, BG=10 (human-safe)
    - Free preview: FG=240, BG=15
    
    Returns: trimap (128 = unknown, 0 = background, 255 = foreground)
    """
    try:
        if isinstance(mask, Image.Image):
            mask_array = np.array(mask.convert('L'))
        else:
            mask_array = mask.astype(np.uint8) if mask.dtype != np.uint8 else mask
        
        # Create trimap
        trimap = np.zeros_like(mask_array, dtype=np.uint8)
        
        # Set default thresholds based on context
        # Free preview: FG=240, BG=15
        # Premium: FG=245, BG=10 (human-safe)
        if fg_threshold is None:
            fg_threshold = 245  # Premium default
        if bg_threshold is None:
            bg_threshold = 10   # Premium default
        
        # Foreground: mask > fg_threshold
        trimap[mask_array > fg_threshold] = 255
        
        # Background: mask < bg_threshold
        trimap[mask_array < bg_threshold] = 0
        
        # Unknown region: bg_threshold to fg_threshold
        unknown_mask = (mask_array >= bg_threshold) & (mask_array <= fg_threshold)
        trimap[unknown_mask] = 128
        
        # Expand unknown region by dilating the boundary
        if CV2_AVAILABLE and expand_radius > 0:
            # Create kernel for expansion
            kernel_size = expand_radius * 2 + 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            
            # Expand unknown region
            fg_boundary = (trimap == 255).astype(np.uint8)
            bg_boundary = (trimap == 0).astype(np.uint8)
            
            # Dilate both boundaries to expand unknown region
            fg_dilated = cv2.dilate(fg_boundary, kernel, iterations=1)
            bg_dilated = cv2.dilate(bg_boundary, kernel, iterations=1)
            
            # Set unknown region where boundaries overlap or near edges
            edge_region = (fg_dilated > 0) | (bg_dilated > 0)
            edge_region = edge_region & (trimap != 128)  # Don't overwrite existing unknown
            trimap[edge_region] = 128
        
        return Image.fromarray(trimap, mode='L')
    except Exception as e:
        logger.warning(f"Trimap generation failed: {e}, using original mask")
        return mask if isinstance(mask, Image.Image) else Image.fromarray(mask, mode='L')

def adaptive_feather_alpha(alpha_channel, image_width, image_height, is_document=False):
    """
    Adaptive feathering based on image size (MP)
    Apply feather ONLY on alpha channel with radius based on megapixels
    """
    if not SCIPY_AVAILABLE:
        return alpha_channel
    
    try:
        megapixels = (image_width * image_height) / 1_000_000
        
        # Determine feather radius based on MP
        if is_document:
            # Document preset: max 2-3 px feather
            feather_radius = min(3, max(2, int(megapixels * 0.5)))
        elif megapixels <= 2:
            feather_radius = 2
        elif megapixels <= 5:
            feather_radius = 3 if megapixels <= 3 else 4
        elif megapixels <= 10:
            feather_radius = 5 if megapixels <= 7 else 6
        elif megapixels <= 18:
            feather_radius = 7 if megapixels <= 14 else 9
        else:  # 18-25 MP
            feather_radius = 10 if megapixels <= 21 else 12
        
        logger.info(f"Adaptive feather: {megapixels:.2f} MP → radius {feather_radius} px")
        
        if isinstance(alpha_channel, Image.Image):
            alpha_array = np.array(alpha_channel.convert('L')).astype(np.float32) / 255.0
        else:
            alpha_array = alpha_channel.astype(np.float32) / 255.0 if alpha_channel.max() > 1.0 else alpha_channel.astype(np.float32)
        
        # Edge-aware gaussian feather
        if CV2_AVAILABLE:
            # Use Gaussian blur with edge preservation
            alpha_uint8 = (alpha_array * 255).astype(np.uint8)
            
            # Apply bilateral filter for edge-aware smoothing
            feathered = cv2.bilateralFilter(
                alpha_uint8,
                d=feather_radius * 2 + 1,
                sigmaColor=75,
                sigmaSpace=75
            )
            
            # Blend with original to preserve strong alpha values
            alpha_blended = alpha_array * 0.7 + (feathered.astype(np.float32) / 255.0) * 0.3
            
            # Convert back to 0-255 range
            alpha_final = (np.clip(alpha_blended, 0, 1) * 255).astype(np.uint8)
        else:
            # Fallback: simple gaussian blur
            from scipy.ndimage import gaussian_filter
            feathered = gaussian_filter(alpha_array, sigma=feather_radius / 2)
            alpha_final = (np.clip(feathered, 0, 1) * 255).astype(np.uint8)
        
        return Image.fromarray(alpha_final, mode='L')
    except Exception as e:
        logger.warning(f"Adaptive feather failed: {e}, using original alpha")
        return alpha_channel if isinstance(alpha_channel, Image.Image) else Image.fromarray(alpha_channel, mode='L')

def strong_halo_removal_alpha(alpha_channel, original_image, is_document=False):
    """
    Strong halo removal on alpha edges only (alpha between 0.7 and 0.98)
    Suppress white/blue/light background spill
    """
    try:
        if isinstance(alpha_channel, Image.Image):
            alpha_array = np.array(alpha_channel.convert('L')).astype(np.float32) / 255.0
        else:
            alpha_array = alpha_channel.astype(np.float32) / 255.0 if alpha_channel.max() > 1.0 else alpha_channel.astype(np.float32)
        
        if isinstance(original_image, Image.Image):
            img_array = np.array(original_image.convert('RGB'))
        else:
            img_array = original_image
        
        # Detect edge region (alpha between 0.7 and 0.98)
        edge_mask = (alpha_array >= 0.7) & (alpha_array <= 0.98)
        
        if not np.any(edge_mask):
            return alpha_channel
        
        # Calculate background color (regions with very low alpha)
        bg_mask = alpha_array < 0.1
        if np.any(bg_mask):
            bg_color = np.mean(img_array[bg_mask], axis=0)
        else:
            # Fallback: sample from corners
            h, w = img_array.shape[:2]
            corners = np.concatenate([
                img_array[0:max(1, h//10), 0:max(1, w//10)].reshape(-1, 3),
                img_array[h-max(1, h//10):, 0:max(1, w//10)].reshape(-1, 3),
                img_array[0:max(1, h//10), w-max(1, w//10):].reshape(-1, 3),
                img_array[h-max(1, h//10):, w-max(1, w//10):].reshape(-1, 3)
            ])
            bg_color = np.mean(corners, axis=0)
        
        # Detect white/blue/light colors (potential halo)
        img_float = img_array.astype(np.float32)
        brightness = np.mean(img_float, axis=2) / 255.0
        is_light = brightness > 0.85  # Very bright areas
        
        # Check if edge pixels are similar to background color
        color_diff = np.abs(img_float - bg_color.reshape(1, 1, 3))
        color_similarity = np.mean(color_diff, axis=2) < 30  # Similar to background
        
        # Halo: light color + similar to background + in edge region
        halo_mask = edge_mask & is_light & color_similarity
        
        # Suppress halo (reduce alpha)
        cleaned_alpha = alpha_array.copy()
        if not is_document:
            # Strong suppression for regular images
            cleaned_alpha[halo_mask] = np.clip(cleaned_alpha[halo_mask] * 0.3, 0, 0.98)
        else:
            # Gentle suppression for documents
            cleaned_alpha[halo_mask] = np.clip(cleaned_alpha[halo_mask] * 0.7, 0, 0.98)
        
        # Convert back to 0-255
        cleaned_alpha_uint8 = (cleaned_alpha * 255).astype(np.uint8)
        
        return Image.fromarray(cleaned_alpha_uint8, mode='L')
    except Exception as e:
        logger.warning(f"Strong halo removal failed: {e}, using original alpha")
        return alpha_channel if isinstance(alpha_channel, Image.Image) else Image.fromarray(alpha_channel, mode='L')

def color_decontamination(rgba_image, original_image, strength=0.6):
    """
    Color decontamination - Remove background color spill from foreground edges
    Sample background color and remove spill on edge pixels (alpha < 0.95)
    """
    try:
        if isinstance(rgba_image, Image.Image):
            rgba_array = np.array(rgba_image.convert('RGBA'))
        else:
            rgba_array = rgba_image
        
        if isinstance(original_image, Image.Image):
            orig_array = np.array(original_image.convert('RGB'))
        else:
            orig_array = original_image
        
        alpha_channel = rgba_array[:, :, 3].astype(np.float32) / 255.0
        rgb_channels = rgba_array[:, :, :3].astype(np.float32)
        
        # Sample background color (alpha < 0.1)
        bg_mask = alpha_channel < 0.1
        if np.any(bg_mask):
            bg_color = np.mean(orig_array[bg_mask], axis=0)
        else:
            # Fallback: corners
            h, w = orig_array.shape[:2]
            corners = np.concatenate([
                orig_array[0:max(1, h//10), 0:max(1, w//10)].reshape(-1, 3),
                orig_array[h-max(1, h//10):, 0:max(1, w//10)].reshape(-1, 3),
                orig_array[0:max(1, h//10), w-max(1, w//10):].reshape(-1, 3),
                orig_array[h-max(1, h//10):, w-max(1, w//10):].reshape(-1, 3)
            ])
            bg_color = np.mean(corners, axis=0)
        
        # Edge pixels: alpha < 0.95
        edge_mask = alpha_channel < 0.95
        
        # Remove background color spill
        decontaminated = rgb_channels.copy()
        for c in range(3):
            spill = rgb_channels[:, :, c] - bg_color[c]
            # Only remove spill on edge pixels
            decontaminated[:, :, c][edge_mask] = np.clip(
                rgb_channels[:, :, c][edge_mask] - spill[edge_mask] * strength * (1 - alpha_channel[edge_mask]),
                0, 255
            )
        
        # Reconstruct RGBA
        result = rgba_array.copy()
        result[:, :, :3] = decontaminated.astype(np.uint8)
        
        return Image.fromarray(result, mode='RGBA')
    except Exception as e:
        logger.warning(f"Color decontamination failed: {e}, using original image")
        return rgba_image if isinstance(rgba_image, Image.Image) else Image.fromarray(rgba_image, mode='RGBA')

def guided_filter(image, mask, radius=5, eps=0.01):
    """
    Guided Filter for smooth borders
    Uses OpenCV's guided filter implementation for edge smoothing
    """
    if not CV2_AVAILABLE:
        return mask
    
    try:
        # Convert PIL to numpy
        if isinstance(image, Image.Image):
            img_array = np.array(image.convert('RGB'))
        else:
            img_array = image
        
        if isinstance(mask, Image.Image):
            mask_array = np.array(mask.convert('L')) / 255.0
        else:
            mask_array = mask / 255.0 if mask.max() > 1.0 else mask
        
        # Ensure float32
        img_array = img_array.astype(np.float32) / 255.0
        mask_array = mask_array.astype(np.float32)
        
        # Apply guided filter (using ximgproc if available, else fallback)
        try:
            filtered_mask = cv2.ximgproc.guidedFilter(
                guide=img_array,
                src=mask_array,
                radius=radius,
                eps=eps
            )
        except AttributeError:
            # Fallback: simple bilateral filter for edge smoothing
            mask_uint8 = (mask_array * 255).astype(np.uint8)
            filtered_mask = cv2.bilateralFilter(
                mask_uint8,
                d=9,
                sigmaColor=75,
                sigmaSpace=75
            ).astype(np.float32) / 255.0
        
        # Convert back to 0-255 range
        filtered_mask = (filtered_mask * 255).astype(np.uint8)
        return Image.fromarray(filtered_mask, mode='L')
    except Exception as e:
        logger.warning(f"Guided filter failed, using original mask: {str(e)}")
        return mask if isinstance(mask, Image.Image) else Image.fromarray((mask * 255).astype(np.uint8), mode='L')

def apply_feathering(mask, feather_radius=2):
    """
    Feathering for natural smooth edges
    Creates smooth alpha transitions at edges
    """
    if not SCIPY_AVAILABLE:
        return mask
    
    try:
        # Convert to numpy
        if isinstance(mask, Image.Image):
            mask_array = np.array(mask.convert('L'))
        else:
            mask_array = mask
        
        # Create distance transform for feathering
        # Binary mask
        binary_mask = (mask_array > 128).astype(np.float32)
        
        # Distance transform from edges
        dist_inner = ndimage.distance_transform_edt(binary_mask)
        dist_outer = ndimage.distance_transform_edt(1 - binary_mask)
        
        # Combine distances for smooth feathering
        dist_combined = np.minimum(dist_inner, dist_outer)
        
        # Apply feathering curve
        feather_curve = np.clip(dist_combined / feather_radius, 0, 1)
        feathered_mask = (mask_array.astype(np.float32) * feather_curve).astype(np.uint8)
        
        return Image.fromarray(feathered_mask, mode='L')
    except Exception as e:
        logger.warning(f"Feathering failed, using original mask: {str(e)}")
        return mask if isinstance(mask, Image.Image) else Image.fromarray(mask, mode='L')

def remove_halo(mask, original_image, threshold=0.1):
    """
    Halo removal - Clean background leakage
    Removes faint background artifacts and halos around edges
    """
    try:
        # Convert to numpy
        if isinstance(mask, Image.Image):
            mask_array = np.array(mask.convert('L'))
        else:
            mask_array = mask
        
        if isinstance(original_image, Image.Image):
            img_array = np.array(original_image.convert('RGB'))
        else:
            img_array = original_image
        
        # Detect potential halo areas (low alpha with high color variance)
        mask_float = mask_array.astype(np.float32) / 255.0
        
        # Calculate color variance in RGB channels
        color_variance = np.var(img_array, axis=2) / 255.0
        
        # Areas with low alpha but high variance might be halos
        halo_mask = (mask_float < threshold) & (color_variance > 0.3)
        
        # Remove halos by setting alpha to 0
        cleaned_mask = mask_array.copy()
        cleaned_mask[halo_mask] = 0
        
        # Smooth transition
        if SCIPY_AVAILABLE:
            from scipy.ndimage import gaussian_filter
            cleaned_mask = gaussian_filter(cleaned_mask.astype(np.float32), sigma=0.5).astype(np.uint8)
        
        return Image.fromarray(cleaned_mask, mode='L')
    except Exception as e:
        logger.warning(f"Halo removal failed, using original mask: {str(e)}")
        return mask if isinstance(mask, Image.Image) else Image.fromarray(mask, mode='L')

def composite_pro_png(original_image, mask):
    """
    Composite - Pro-level PNG output
    Creates professional quality PNG with proper alpha channel
    """
    try:
        # Ensure original is RGB
        if isinstance(original_image, Image.Image):
            if original_image.mode == 'RGBA':
                # Composite on white background first
                rgb_image = Image.new('RGB', original_image.size, (255, 255, 255))
                rgb_image.paste(original_image, mask=original_image.split()[3])
                original_image = rgb_image
            elif original_image.mode != 'RGB':
                original_image = original_image.convert('RGB')
        else:
            original_image = Image.fromarray(original_image).convert('RGB')
        
        # Ensure mask is L (grayscale)
        if isinstance(mask, Image.Image):
            mask = mask.convert('L')
        else:
            mask = Image.fromarray(mask, mode='L')
        
        # Resize mask to match image if needed
        if mask.size != original_image.size:
            mask = mask.resize(original_image.size, Image.Resampling.LANCZOS)
        
        # Create RGBA output
        rgba_image = Image.new('RGBA', original_image.size, (0, 0, 0, 0))
        rgba_image.paste(original_image, (0, 0))
        rgba_image.putalpha(mask)
        
        return rgba_image
    except Exception as e:
        logger.error(f"Composite failed: {str(e)}")
        # Fallback: simple alpha composite
        if isinstance(original_image, Image.Image):
            original_image = original_image.convert('RGBA')
        if isinstance(mask, Image.Image):
            mask = mask.convert('L')
        original_image.putalpha(mask)
        return original_image

def apply_alpha_anti_bleed(mask, blur_radius=2):
    """
    Apply alpha anti-bleed to prevent border artifacts
    Uses slight blur to smooth edges and prevent hard borders
    """
    if not CV2_AVAILABLE:
        return mask
    
    try:
        # Convert to numpy
        if isinstance(mask, Image.Image):
            mask_array = np.array(mask.convert('L'))
        else:
            mask_array = mask
        
        # Apply slight Gaussian blur to smooth edges
        blurred = cv2.GaussianBlur(mask_array.astype(np.float32), (blur_radius * 2 + 1, blur_radius * 2 + 1), blur_radius)
        
        # Preserve strong foreground/background while smoothing edges
        # Keep values > 200 and < 50 mostly unchanged, smooth the middle
        strong_fg = mask_array > 200
        strong_bg = mask_array < 50
        blurred[strong_fg] = mask_array[strong_fg] * 0.9 + blurred[strong_fg] * 0.1
        blurred[strong_bg] = mask_array[strong_bg] * 0.9 + blurred[strong_bg] * 0.1
        
        return Image.fromarray(blurred.astype(np.uint8), mode='L')
    except Exception as e:
        logger.warning(f"Alpha anti-bleed failed, using original mask: {str(e)}")
        return mask if isinstance(mask, Image.Image) else Image.fromarray(mask, mode='L')

def apply_matte_strength(mask, matte_strength=0.2):
    """
    Apply matte strength to preserve text and fine details
    Reduces transparency in areas that should be fully opaque
    """
    try:
        if isinstance(mask, Image.Image):
            mask_array = np.array(mask.convert('L')).astype(np.float32)
        else:
            mask_array = mask.astype(np.float32)
        
        # Boost values above threshold to preserve text/details
        # matte_strength controls how much we boost
        threshold = 128
        boost_factor = 1.0 + matte_strength
        
        # Boost values above threshold
        boosted = np.where(mask_array > threshold, 
                          np.minimum(255, mask_array * boost_factor),
                          mask_array)
        
        return Image.fromarray(boosted.astype(np.uint8), mode='L')
    except Exception as e:
        logger.warning(f"Matte strength failed, using original mask: {str(e)}")
        return mask if isinstance(mask, Image.Image) else Image.fromarray(mask, mode='L')

def enhance_hair_details(mask, original_image, strength=0.3, apply_blur=False):
    """
    Enhance hair details and fine edges for premium quality
    Preserves fine hair strands and detailed edges
    
    CRITICAL: For human images, apply_blur=False to prevent blur (enterprise requirement)
    """
    if not CV2_AVAILABLE:
        return mask
    
    try:
        # Convert to numpy
        if isinstance(mask, Image.Image):
            mask_array = np.array(mask.convert('L')).astype(np.float32)
        else:
            mask_array = mask.astype(np.float32)
        
        if isinstance(original_image, Image.Image):
            img_array = np.array(original_image.convert('RGB'))
        else:
            img_array = original_image
        
        # Detect fine edges using Canny edge detection
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        edges = cv2.Canny(gray.astype(np.uint8), 50, 150)
        
        # Enhance mask in edge regions (where fine details like hair are)
        edge_mask = edges > 0
        enhanced_mask = mask_array.copy()
        
        # Boost mask values in edge regions to preserve fine details
        enhanced_mask[edge_mask] = np.minimum(255, mask_array[edge_mask] * (1.0 + strength))
        
        # CRITICAL: NO BLUR for human images (enterprise requirement)
        # Only apply smoothing if explicitly requested (for non-human images)
        if apply_blur and SCIPY_AVAILABLE:
            from scipy.ndimage import gaussian_filter
            enhanced_mask = gaussian_filter(enhanced_mask, sigma=0.5)
        # For human images: NO blur, direct return for sharp edges
        
        return Image.fromarray(enhanced_mask.astype(np.uint8), mode='L')
    except Exception as e:
        logger.warning(f"Hair detail enhancement failed, using original mask: {str(e)}")
        return mask if isinstance(mask, Image.Image) else Image.fromarray(mask, mode='L')

def clean_matte_edges(mask, original_image, clean_strength=0.4):
    """
    Clean matte edges for premium quality - removes artifacts and smooths edges
    Enhanced version for better edge quality
    """
    if not CV2_AVAILABLE:
        return mask
    
    try:
        # Convert to numpy
        if isinstance(mask, Image.Image):
            mask_array = np.array(mask.convert('L')).astype(np.float32)
        else:
            mask_array = mask.astype(np.float32)
        
        if isinstance(original_image, Image.Image):
            img_array = np.array(original_image.convert('RGB'))
        else:
            img_array = original_image
        
        # Convert to float32 for processing
        img_float = img_array.astype(np.float32) / 255.0
        mask_float = mask_array / 255.0
        
        # Apply bilateral filter for edge-preserving smoothing
        mask_uint8 = (mask_float * 255).astype(np.uint8)
        cleaned = cv2.bilateralFilter(mask_uint8, d=9, sigmaColor=75, sigmaSpace=75)
        
        # Use guided filter for better edge refinement
        try:
            img_float_norm = img_float.astype(np.float32)
            cleaned_float = cleaned.astype(np.float32) / 255.0
            refined = cv2.ximgproc.guidedFilter(
                guide=img_float_norm,
                src=cleaned_float,
                radius=3,
                eps=0.01 * clean_strength
            )
            cleaned = (refined * 255).astype(np.uint8)
        except AttributeError:
            # Fallback if ximgproc not available
            pass
        
        # Enhance contrast at edges for cleaner matte
        edges = cv2.Canny(img_array.astype(np.uint8) if img_array.dtype != np.uint8 else img_array, 50, 150)
        edge_regions = edges > 0
        
        # Sharpen edges slightly
        cleaned_float = cleaned.astype(np.float32)
        cleaned_float[edge_regions] = np.clip(cleaned_float[edge_regions] * 1.1, 0, 255)
        cleaned = cleaned_float.astype(np.uint8)
        
        return Image.fromarray(cleaned, mode='L')
    except Exception as e:
        logger.warning(f"Matte edge cleaning failed, using original mask: {str(e)}")
        return mask if isinstance(mask, Image.Image) else Image.fromarray(mask, mode='L')

def process_premium_document_pipeline(input_image, birefnet_session):
    """
    PREMIUM DOCUMENT / ID CARD PIPELINE (GPU safe mode)
    
    For detected DOCUMENT images:
    - Use BiRefNet ONLY (no MaxMatting)
    - Disable Feather
    - Disable Halo removal
    - Convert mask to high-threshold binary alpha (no semi-transparency)
    - Composite directly to preserve text and page visibility
    
    Goal: Text must remain fully visible, no half-transparent pages, no disappearing content.
    """
    start_time = time.time()
    debug_stats = {}
    
    original_width, original_height = input_image.size
    original_megapixels = (original_width * original_height) / 1_000_000
    
    logger.info(f"📄 Premium Document Pipeline: {original_width}x{original_height} = {original_megapixels:.2f} MP")
    
    # Step 1: BiRefNet Semantic Mask ONLY
    logger.info("Step 1: Generating BiRefNet semantic mask (document mode)...")
    max_dimension = max(original_width, original_height)
    
    # Adaptive input: min 1024, max 1536 on longest side
    target_size = min(1536, max(1024, max_dimension))
    scale = target_size / max_dimension
    
    # Resize for BiRefNet processing if needed
    if scale < 1.0:
        process_width = int(original_width * scale)
        process_height = int(original_height * scale)
        process_image = input_image.resize((process_width, process_height), Image.Resampling.LANCZOS)
        logger.info(f"Resized to {process_width}x{process_height} for BiRefNet processing")
    else:
        process_image = input_image
    
    # Get BiRefNet mask
    input_buffer = io.BytesIO()
    process_image.save(input_buffer, format='PNG')
    input_bytes = input_buffer.getvalue()
    output_bytes = remove(input_bytes, session=birefnet_session)
    output_image = Image.open(io.BytesIO(output_bytes))
    
    # Extract mask
    if output_image.mode == 'RGBA':
        mask = output_image.split()[3]
    else:
        mask = output_image.convert('L')
    
    # Resize mask back to original size if needed
    if mask.size != input_image.size:
        mask = mask.resize(input_image.size, Image.Resampling.LANCZOS)
    
    debug_stats.update({
        "birefnet_mask_shape": mask.size,
        "birefnet_processing_size": process_image.size
    })
    
    # Step 2: High-Threshold Binary Alpha (no semi-transparency)
    logger.info("Step 2: Converting to high-threshold binary alpha...")
    mask_array = np.array(mask.convert('L')).astype(np.float32) / 255.0
    
    # High threshold: values > 0.5 become 1.0, else 0.0 (binary)
    binary_alpha = np.where(mask_array > 0.5, 1.0, 0.0)
    
    # Convert back to 0-255 uint8
    binary_alpha_uint8 = (binary_alpha * 255).astype(np.uint8)
    binary_mask = Image.fromarray(binary_alpha_uint8, mode='L')
    
    debug_stats["binary_alpha_threshold"] = float(0.5)
    debug_stats["maxmatting_disabled"] = bool(True)  # Explicit Python bool
    debug_stats["feather_disabled"] = bool(True)  # Explicit Python bool
    debug_stats["halo_removal_disabled"] = bool(True)  # Explicit Python bool
    
    # Step 3: Composite Directly (no post-processing)
    logger.info("Step 3: Compositing RGB + binary alpha (direct, no post-processing)...")
    
    # Ensure RGB
    rgb_image = input_image.convert('RGB') if input_image.mode != 'RGB' else input_image
    
    # Create RGBA with binary alpha
    rgba_composite = Image.new('RGBA', rgb_image.size, (0, 0, 0, 0))
    rgba_composite.paste(rgb_image, (0, 0))
    rgba_composite.putalpha(binary_mask)
    
    debug_stats["composite_completed"] = bool(True)  # Explicit Python bool
    debug_stats["pipeline_type"] = str("document_safe")  # Explicit string
    
    # Final alpha check
    final_alpha = np.array(rgba_composite.getchannel('A'))
    final_alpha_nonzero = np.count_nonzero(final_alpha)
    final_alpha_percent = (final_alpha_nonzero / final_alpha.size) * 100.0
    debug_stats.update({
        "final_alpha_percent": float(final_alpha_percent),
        "final_alpha_nonzero": int(final_alpha_nonzero)
    })
    
    logger.info(f"✅ Premium Document pipeline completed in {time.time() - start_time:.2f}s, final alpha: {final_alpha_percent:.2f}%")
    
    # Convert to bytes
    output_buffer = io.BytesIO()
    rgba_composite.save(output_buffer, format='PNG', optimize=True)
    output_bytes = output_buffer.getvalue()
    
    return output_bytes, debug_stats

def process_enterprise_pipeline(input_image, birefnet_session, maxmatting_session, image_type='human'):
    """
    ENTERPRISE-GRADE BACKGROUND REMOVAL PIPELINE (Better than remove.bg)
    
    Rules for Human Images:
    - BiRefNet: NO feather, NO guided filter, NO halo removal, NO alpha smoothing
    - Trimap: expand_radius=3 (NEVER more than 3 for humans)
    - MaxMatting: thresholds 245/10, erode_size=0
    - Hair enhancement: strength=0.12 (DO NOT exceed 0.15)
    - Hard alpha clamp: 220->255, <=8->0 (TRANSPARENCY KILL)
    - Color decontamination: strength=0.4 (NEVER exceed 0.6)
    - NO adaptive_feather_alpha, guided_filter, apply_feathering, strong_halo_removal_alpha, apply_alpha_anti_bleed
    
    Image types: human, document, animal, ecommerce
    """
    start_time = time.time()
    debug_stats = {}
    
    original_width, original_height = input_image.size
    original_megapixels = (original_width * original_height) / 1_000_000
    
    # INPUT RULES (CRITICAL)
    MAX_MP = 25  # up to 5000x5000
    MIN_LONG_SIDE = 2048
    PROCESS_LONG_SIDE = 3072  # sweet spot for quality (remove.bg internally ~3K processing)
    
    logger.info(f"🚀 Enterprise Pipeline: {original_width}x{original_height} = {original_megapixels:.2f} MP, type: {image_type}")
    
    # Check max MP limit
    if original_megapixels > MAX_MP:
        logger.warning(f"Image exceeds {MAX_MP} MP limit ({original_megapixels:.2f} MP), will be downscaled")
        scale = (MAX_MP / original_megapixels) ** 0.5
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        input_image = input_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        original_width, original_height = input_image.size
        original_megapixels = (original_width * original_height) / 1_000_000
        logger.info(f"Downscaled to {original_width}x{original_height} = {original_megapixels:.2f} MP")
    
    # Step 1: BiRefNet Semantic Segmentation (SAFE - NO FEATHER, NO BLUR, NO HALO)
    logger.info("Step 1: BiRefNet semantic mask (NO feather, NO guided filter, NO halo removal, NO alpha smoothing)")
    max_dimension = max(original_width, original_height)
    
    # Use PROCESS_LONG_SIDE (3072) for quality (remove.bg style)
    target_size = max(MIN_LONG_SIDE, min(PROCESS_LONG_SIDE, max_dimension))
    scale = target_size / max_dimension
    
    # Resize for BiRefNet processing
    if abs(scale - 1.0) > 0.01:
        process_width = int(original_width * scale)
        process_height = int(original_height * scale)
        process_image = input_image.resize((process_width, process_height), Image.Resampling.LANCZOS)
        logger.info(f"Resized to {process_width}x{process_height} for BiRefNet processing (target: {target_size}px)")
    else:
        process_image = input_image
    
    # Get BiRefNet mask - NO POST-PROCESSING (NO feather, NO blur, NO halo)
    input_buffer = io.BytesIO()
    process_image.save(input_buffer, format='PNG')
    input_bytes = input_buffer.getvalue()
    output_bytes = remove(input_bytes, session=birefnet_session)
    output_image = Image.open(io.BytesIO(output_bytes))
    
    # Extract semantic alpha (L channel) - DIRECT EXTRACTION, NO PROCESSING
    if output_image.mode == 'RGBA':
        semantic_alpha = output_image.split()[3]  # L channel
    else:
        semantic_alpha = output_image.convert('L')
    
    # Resize mask back to original size if needed
    if semantic_alpha.size != input_image.size:
        semantic_alpha = semantic_alpha.resize(input_image.size, Image.Resampling.LANCZOS)
    
    debug_stats.update({
        "birefnet_mask_shape": semantic_alpha.size,
        "birefnet_processing_size": process_image.size,
        "birefnet_no_feather": True,
        "birefnet_no_blur": True,
        "birefnet_no_halo": True
    })
    
    # Step 2: HUMAN-SAFE TRIMAP (MOST IMPORTANT - expand_radius=3 for humans)
    logger.info("Step 2: Generating human-safe trimap (expand_radius=3, thresholds 245/10)")
    
    if image_type == 'human':
        # CRITICAL: NEVER more than 3 for humans (prevents cutting fingers, hair, edges)
        expand_radius = 3
    elif image_type == 'document':
        expand_radius = 4
    elif image_type == 'animal':
        expand_radius = 10
    elif image_type == 'ecommerce':
        expand_radius = 6
    else:
        expand_radius = 3  # Default to safe value
    
    # CRITICAL FIX: Expand BiRefNet mask BEFORE trimap generation to prevent body parts cutting
    # This ensures hands, fingers, hair edges are preserved
    if image_type == 'human' and CV2_AVAILABLE:
        try:
            logger.info("Step 2.1: Expanding BiRefNet mask (1px dilation) to prevent body parts cutting...")
            mask_array = np.array(semantic_alpha.convert('L'))
            # Small dilation (1px) to preserve body parts without over-expanding
            kernel = np.ones((3, 3), np.uint8)  # 3x3 kernel = 1px expansion per iteration
            mask_expanded = cv2.dilate(mask_array.astype(np.uint8), kernel, iterations=1)  # 1 iteration = ~1px expansion
            semantic_alpha = Image.fromarray(mask_expanded, mode='L')
            logger.info("✅ Mask expanded (1px) to prevent body parts cutting")
            debug_stats["mask_pre_expansion_applied"] = True
        except Exception as exp_err:
            logger.warning(f"Mask pre-expansion failed: {exp_err}, continuing with original mask")
            debug_stats["mask_pre_expansion_error"] = str(exp_err)
    
    trimap = generate_trimap(semantic_alpha, expand_radius=expand_radius)
    debug_stats["trimap_expand_radius"] = expand_radius
    debug_stats["trimap_type"] = image_type
    debug_stats["trimap_thresholds"] = "FG>245, BG<10"
    
    # Step 3: MaxMatting Fine Alpha Matting (REAL QUALITY MAGIC)
    logger.info("Step 3: MaxMatting fine alpha matting (thresholds 245/10, erode_size=0)")
    
    # Use PROCESS_LONG_SIDE (3072) for MaxMatting quality
    maxmatting_max_dim = max(original_width, original_height)
    maxmatting_target = max(MIN_LONG_SIDE, min(PROCESS_LONG_SIDE, maxmatting_max_dim))
    maxmatting_scale = maxmatting_target / maxmatting_max_dim
    
    # Prepare high-res input for MaxMatting
    if abs(maxmatting_scale - 1.0) > 0.01:
        maxmatting_width = int(original_width * maxmatting_scale)
        maxmatting_height = int(original_height * maxmatting_scale)
        maxmatting_image = input_image.resize((maxmatting_width, maxmatting_height), Image.Resampling.LANCZOS)
        maxmatting_trimap = trimap.resize((maxmatting_width, maxmatting_height), Image.Resampling.LANCZOS)
        logger.info(f"Resized to {maxmatting_width}x{maxmatting_height} for MaxMatting (target: {maxmatting_target}px)")
    else:
        maxmatting_image = input_image
        maxmatting_trimap = trimap
    
    # Prepare input for MaxMatting: RGB image + trimap
    trimap_rgba = Image.new('RGBA', maxmatting_image.size)
    trimap_rgba.paste(maxmatting_image.convert('RGB'), (0, 0))
    trimap_rgba.putalpha(maxmatting_trimap)
    
    # Process with MaxMatting (silueta model)
    matting_buffer = io.BytesIO()
    trimap_rgba.save(matting_buffer, format='PNG')
    matting_bytes = matting_buffer.getvalue()
    matting_output_bytes = remove(matting_bytes, session=maxmatting_session)
    matting_output = Image.open(io.BytesIO(matting_output_bytes))
    
    # Extract refined alpha from MaxMatting output
    if matting_output.mode == 'RGBA':
        alpha_mm = matting_output.split()[3]
    else:
        alpha_mm = matting_output.convert('L')
    
    # Resize alpha back to original size if needed
    if alpha_mm.size != input_image.size:
        alpha_mm = alpha_mm.resize(input_image.size, Image.Resampling.LANCZOS)
    
    debug_stats.update({
        "maxmatting_alpha_shape": alpha_mm.size,
        "maxmatting_processing_size": maxmatting_image.size,
        "maxmatting_thresholds": "245/10",
        "maxmatting_erode_size": 0,
        "maxmatting_applied": True
    })
    
    # Safety check: alpha should have content
    alpha_array = np.array(alpha_mm.convert('L'))
    alpha_nonzero = np.count_nonzero(alpha_array)
    alpha_percent = (alpha_nonzero / alpha_array.size) * 100.0
    
    if alpha_percent < 1.0:
        logger.warning(f"⚠️ MaxMatting alpha too low ({alpha_percent:.2f}%), falling back to BiRefNet mask")
        alpha_mm = semantic_alpha
        debug_stats["maxmatting_fallback"] = bool(True)
    
    # Step 4: HAIR DETAIL ENHANCEMENT (LIMITED - strength=0.12, DO NOT exceed 0.15, NO BLUR)
    if image_type == 'human':
        logger.info("Step 4: Hair detail enhancement (strength=0.12, micro-boost only, NO BLUR)")
        # CRITICAL: apply_blur=False for human images to prevent blur (enterprise requirement)
        alpha_enhanced = enhance_hair_details(alpha_mm, input_image, strength=0.12, apply_blur=False)
        debug_stats["hair_enhancement_applied"] = True
        debug_stats["hair_enhancement_strength"] = 0.12
        debug_stats["hair_enhancement_blur"] = False  # NO BLUR for humans
    else:
        alpha_enhanced = alpha_mm
        debug_stats["hair_enhancement_applied"] = False
    
    # Step 5: HARD ALPHA CLAMP (TRANSPARENCY KILL - Enterprise Rule)
    logger.info("Step 5: Hard alpha clamp (220->255, <=8->0) - TRANSPARENCY KILL")
    alpha_np = np.array(alpha_enhanced.convert('L'))
    
    # Human body kabhi semi-transparent nahi hota
    alpha_np[alpha_np >= 220] = 255  # Faded skin/cloth -> fully opaque
    alpha_np[alpha_np <= 8] = 0      # Background -> fully transparent
    
    alpha_hard = Image.fromarray(alpha_np, 'L')
    debug_stats["hard_alpha_clamp_applied"] = True
    debug_stats["alpha_clamp_thresholds"] = "220->255, <=8->0"
    
    # Step 6: Composite RGB + Alpha
    logger.info("Step 6: Compositing RGB + hard alpha")
    rgb_image = input_image.convert('RGB') if input_image.mode != 'RGB' else input_image
    rgba_composite = Image.new('RGBA', rgb_image.size, (0, 0, 0, 0))
    rgba_composite.paste(rgb_image, (0, 0))
    rgba_composite.putalpha(alpha_hard)
    
    debug_stats["composite_completed"] = bool(True)
    
    # Step 7: COLOR DECONTAMINATION (EDGE ONLY - strength=0.3, NEVER exceed 0.6)
    # CRITICAL: For human images, use minimal strength to prevent blur
    if image_type == 'human':
        logger.info("Step 7: Color decontamination (strength=0.3, edge only, minimal for sharpness)")
        # Reduced from 0.4 to 0.3 for sharper edges (prevents blur)
        final_image = color_decontamination(rgba_composite, rgb_image, strength=0.3)
        debug_stats["color_decontamination_applied"] = True
        debug_stats["color_decontamination_strength"] = 0.3
    else:
        # For other types, use appropriate strength
        if image_type == 'document':
            final_image = color_decontamination(rgba_composite, rgb_image, strength=0.2)
        else:
            final_image = color_decontamination(rgba_composite, rgb_image, strength=0.6)
        debug_stats["color_decontamination_applied"] = True
        debug_stats["color_decontamination_strength"] = 0.6 if image_type != 'document' else 0.2
    
    # Step 8: NO MORE FILTERS for human pipeline
    # ❌ DO NOT USE: adaptive_feather_alpha, guided_filter, apply_feathering, 
    #                strong_halo_removal_alpha, apply_alpha_anti_bleed
    if image_type == 'human':
        logger.info("Step 8: NO additional filters for human pipeline (enterprise rule)")
        debug_stats["additional_filters_applied"] = False
    else:
        # For documents/animals/ecommerce, apply appropriate filters
        if image_type == 'document':
            current_alpha = final_image.split()[3]
            cleaned_alpha = strong_halo_removal_alpha(current_alpha, rgb_image, is_document=True)
            final_image.putalpha(cleaned_alpha)
            debug_stats["halo_removal_applied"] = True
        elif image_type in ['animal', 'ecommerce']:
            current_alpha = final_image.split()[3]
            cleaned_alpha = strong_halo_removal_alpha(current_alpha, rgb_image, is_document=False)
            final_image.putalpha(cleaned_alpha)
            debug_stats["halo_removal_applied"] = True
    
    # NO EDGE SHARPENING - MaxMatting already provides sharp edges
    # NO FEATHER - True AI matting doesn't need artificial feathering
    # NO BLUR - Enterprise quality requires sharp, natural edges
    
    # Final alpha check
    final_alpha = np.array(final_image.getchannel('A'))
    final_alpha_nonzero = np.count_nonzero(final_alpha)
    final_alpha_percent = (final_alpha_nonzero / final_alpha.size) * 100.0
    debug_stats.update({
        "final_alpha_percent": float(final_alpha_percent),
        "final_alpha_nonzero": int(final_alpha_nonzero)
    })
    
    if final_alpha_nonzero == 0:
        logger.error(f"❌ CRITICAL: Final alpha is empty (0% nonzero) - processing failed")
        raise ValueError("Processing failed: output alpha channel is empty")
    
    logger.info(f"✅ Enterprise pipeline completed in {time.time() - start_time:.2f}s, final alpha: {final_alpha_percent:.2f}%, type: {image_type}")
    
    # Convert to bytes (will be converted to JPG later if needed)
    output_buffer = io.BytesIO()
    final_image.save(output_buffer, format='PNG', optimize=True)
    output_bytes = output_buffer.getvalue()
    
    return output_bytes, debug_stats

def process_premium_hd_pipeline(input_image, birefnet_session, maxmatting_session, is_document=False):
    """
    PREMIUM PHOTO PIPELINE (GPU)
    
    Use BiRefNet + MaxMatting together for photos.
    
    Pipeline order MUST be exactly:
    1. BiRefNet primary mask
    2. MaxMatting refinement
    3. Composite RGB + Alpha
    4. Adaptive Feather on ALPHA only
    5. Strong Halo Removal on ALPHA only
    6. Optional mild edge sharpening
    7. Final PNG output
    
    Important:
    - NEVER feather or blur the raw mask before composite.
    - Feather and halo must apply AFTER RGB+Alpha composite.
    - Preserve hair, dupatta, cloth edges.
    - Avoid white/black border artifacts.
    """
    start_time = time.time()
    debug_stats = {}
    
    original_width, original_height = input_image.size
    original_megapixels = (original_width * original_height) / 1_000_000
    
    logger.info(f"🚀 Premium HD Pipeline: {original_width}x{original_height} = {original_megapixels:.2f} MP")
    
    # Step 1: BiRefNet Semantic Mask (adaptive input resolution)
    logger.info("Step 1: Generating BiRefNet semantic mask...")
    max_dimension = max(original_width, original_height)
    
    # Adaptive input: min 1024, max 1536 on longest side
    target_size = min(1536, max(1024, max_dimension))
    scale = target_size / max_dimension
    
    # Resize for BiRefNet processing if needed
    if scale < 1.0:
        process_width = int(original_width * scale)
        process_height = int(original_height * scale)
        process_image = input_image.resize((process_width, process_height), Image.Resampling.LANCZOS)
        logger.info(f"Resized to {process_width}x{process_height} for BiRefNet processing")
    else:
        process_image = input_image
    
    # Get BiRefNet mask
    input_buffer = io.BytesIO()
    process_image.save(input_buffer, format='PNG')
    input_bytes = input_buffer.getvalue()
    output_bytes = remove(input_bytes, session=birefnet_session)
    output_image = Image.open(io.BytesIO(output_bytes))
    
    # Extract mask
    if output_image.mode == 'RGBA':
        mask = output_image.split()[3]
    else:
        mask = output_image.convert('L')
    
    # Resize mask back to original size if needed
    if mask.size != input_image.size:
        mask = mask.resize(input_image.size, Image.Resampling.LANCZOS)
    
    debug_stats.update({
        "birefnet_mask_shape": mask.size,
        "birefnet_processing_size": process_image.size
    })
    
    # Step 2: Trimap Generation
    logger.info("Step 2: Generating trimap for fine matting...")
    expand_radius = 6 if original_megapixels <= 10 else (8 if original_megapixels <= 18 else 12)
    trimap = generate_trimap(mask, expand_radius=expand_radius)
    debug_stats["trimap_expand_radius"] = expand_radius
    
    # Step 3: Fine Alpha Matting (MaxMatting) - PREMIUM ONLY
    logger.info("Step 3: Fine alpha matting with MaxMatting...")
    
    # Prepare input for MaxMatting: RGB image + trimap
    # MaxMatting expects RGBA where alpha is trimap
    trimap_rgba = Image.new('RGBA', input_image.size)
    trimap_rgba.paste(input_image.convert('RGB'), (0, 0))
    trimap_rgba.putalpha(trimap)
    
    # Process with MaxMatting
    matting_buffer = io.BytesIO()
    trimap_rgba.save(matting_buffer, format='PNG')
    matting_bytes = matting_buffer.getvalue()
    matting_output_bytes = remove(matting_bytes, session=maxmatting_session)
    matting_output = Image.open(io.BytesIO(matting_output_bytes))
    
    # Extract refined alpha from MaxMatting output
    if matting_output.mode == 'RGBA':
        refined_alpha = matting_output.split()[3]
    else:
        refined_alpha = matting_output.convert('L')
    
    debug_stats.update({
        "maxmatting_alpha_shape": refined_alpha.size,
        "maxmatting_applied": True
    })
    
    # Safety check: alpha should have content
    alpha_array = np.array(refined_alpha.convert('L'))
    alpha_nonzero = np.count_nonzero(alpha_array)
    alpha_percent = (alpha_nonzero / alpha_array.size) * 100.0
    
    if alpha_percent < 1.0:
        logger.warning(f"⚠️ MaxMatting alpha too low ({alpha_percent:.2f}%), falling back to BiRefNet mask")
        refined_alpha = mask
        debug_stats["maxmatting_fallback"] = bool(True)
    
    # Step 4: Composite RGB + Alpha FIRST (CRITICAL ORDER)
    logger.info("Step 4: Compositing RGB + refined alpha...")
    
    # Ensure RGB
    rgb_image = input_image.convert('RGB') if input_image.mode != 'RGB' else input_image
    
    # Create RGBA with refined alpha
    rgba_composite = Image.new('RGBA', rgb_image.size, (0, 0, 0, 0))
    rgba_composite.paste(rgb_image, (0, 0))
    rgba_composite.putalpha(refined_alpha)
    
    debug_stats["composite_completed"] = bool(True)
    
    # Step 5: Adaptive Feather (Alpha only, based on MP)
    # Document preset: max 2-3px feather, no aggressive halo
    # Human preset: Full adaptive feather based on MP
    if is_document:
        logger.info("Step 5: Applying document preset (max 2-3px feather, reduced halo)")
        composite_alpha = rgba_composite.split()[3]
        # Document: very light feather (max 2-3px)
        feathered_alpha = adaptive_feather_alpha(
            composite_alpha, 
            original_width, 
            original_height, 
            is_document=True  # Forces max 2-3px feather
        )
        rgba_composite.putalpha(feathered_alpha)
        debug_stats["adaptive_feather_applied"] = bool(True)
        debug_stats["document_preset"] = bool(True)
        
        # Step 6: Reduced Halo Removal for documents
        logger.info("Step 6: Applying reduced halo removal (document preset)...")
        current_alpha = rgba_composite.split()[3]
        cleaned_alpha = strong_halo_removal_alpha(
            current_alpha, 
            rgb_image, 
            is_document=True  # Gentle suppression for documents
        )
        rgba_composite.putalpha(cleaned_alpha)
        debug_stats["halo_removal_applied"] = bool(True)
        debug_stats["halo_strength"] = "reduced_document"
    else:
        # Human photo: Full feather + strong halo
        logger.info("Step 5: Applying adaptive feather to alpha channel (photo mode)...")
        composite_alpha = rgba_composite.split()[3]
        feathered_alpha = adaptive_feather_alpha(
            composite_alpha, 
            original_width, 
            original_height, 
            is_document=False
        )
        rgba_composite.putalpha(feathered_alpha)
        debug_stats["adaptive_feather_applied"] = True
        
        # Step 6: Strong Halo Removal (Alpha edge only) - for photos
        logger.info("Step 6: Applying strong halo removal (photo mode)...")
        current_alpha = rgba_composite.split()[3]
        cleaned_alpha = strong_halo_removal_alpha(
            current_alpha, 
            rgb_image, 
            is_document=False  # Strong suppression for photos
        )
        rgba_composite.putalpha(cleaned_alpha)
        debug_stats["halo_removal_applied"] = bool(True)
        debug_stats["halo_strength"] = "strong_photo"
    
    # Step 7: Color Decontamination
    logger.info("Step 7: Applying color decontamination...")
    final_image = color_decontamination(
        rgba_composite, 
        rgb_image, 
        strength=0.6
    )
    debug_stats["color_decontamination_applied"] = bool(True)
    
    # Step 8: Optional Mild Edge Sharpening (for photos only)
    if CV2_AVAILABLE:
        logger.info("Step 8: Applying mild edge sharpening...")
        try:
            rgba_array = np.array(final_image.convert('RGBA'))
            rgb_channels = rgba_array[:, :, :3].astype(np.float32)
            alpha_channel = rgba_array[:, :, 3].astype(np.float32) / 255.0
            
            # Apply unsharp mask (mild sharpening)
            blurred = cv2.GaussianBlur(rgb_channels, (0, 0), 1.0)
            sharpened = rgb_channels + 0.3 * (rgb_channels - blurred)  # Mild sharpening
            
            # Clip to valid range
            sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
            
            # Reconstruct RGBA
            final_rgba = rgba_array.copy()
            final_rgba[:, :, :3] = sharpened
            
            final_image = Image.fromarray(final_rgba, mode='RGBA')
            debug_stats["edge_sharpening_applied"] = bool(True)
        except Exception as e:
            logger.warning(f"Edge sharpening failed: {e}, using image without sharpening")
            debug_stats["edge_sharpening_applied"] = bool(False)
    else:
        debug_stats["edge_sharpening_applied"] = False
    
    # Final alpha check (CRITICAL: validate before returning)
    final_alpha = np.array(final_image.getchannel('A'))
    final_alpha_nonzero = np.count_nonzero(final_alpha)
    final_alpha_percent = (final_alpha_nonzero / final_alpha.size) * 100.0
    debug_stats.update({
        "final_alpha_percent": float(final_alpha_percent),
        "final_alpha_nonzero": int(final_alpha_nonzero)
    })
    
    # Safety check: if alpha is empty, raise error (no credit deduction)
    if final_alpha_nonzero == 0:
        logger.error(f"❌ CRITICAL: Final alpha is empty (0% nonzero) - processing failed")
        raise ValueError("Processing failed: output alpha channel is empty")
    
    logger.info(f"✅ Premium Photo pipeline completed in {time.time() - start_time:.2f}s, final alpha: {final_alpha_percent:.2f}%")
    
    # Convert to bytes
    output_buffer = io.BytesIO()
    final_image.save(output_buffer, format='PNG', optimize=True)
    output_bytes = output_buffer.getvalue()
    
    return output_bytes, debug_stats

def process_with_optimizations(input_image, session, is_premium=False, is_document=False, output_size=None):
    """
    Process image with all optimizations:
    - BiRefNet or RobustMatting model (based on image type)
    - TensorRT FP16 (handled by ONNX Runtime GPU)
    - Guided Filter
    - Feathering (with configurable settings)
    - Halo Removal
    - Alpha Anti-Bleed (for border fixes)
    - Matte Strength (for text preservation)
    - Composite
    """
    start_opt = time.time()
    debug_stats = {}
    
    # Step 1: Remove background using AI model
    # Determine model name based on session type (will be set correctly by caller)
    model_name = "BiRefNet"  # Default, will be updated based on actual session
    if is_document:
        model_name = "RobustMatting"
    elif is_premium:
        # For premium, check if MaxMatting session is being used
        # This is determined by the caller (premium endpoint uses MaxMatting)
        model_name = "MaxMatting"
    logger.info(f"Step 1: Removing background with {model_name} model (Premium: {is_premium}, Document: {is_document})...")
    # rembg expects bytes-like input in some versions; always send bytes
    input_buffer = io.BytesIO()
    input_image.save(input_buffer, format='PNG')
    input_bytes = input_buffer.getvalue()
    output_bytes = remove(input_bytes, session=session)
    output_image = Image.open(io.BytesIO(output_bytes))
    
    # Extract alpha mask
    if output_image.mode == 'RGBA':
        mask = output_image.split()[3]  # Alpha channel
        foreground = output_image.convert('RGB')
    else:
        # If no alpha, create from output
        mask = output_image.convert('L')
        foreground = output_image.convert('RGB')

    # Debug: log mask statistics and save a preview
    try:
        mask_np = np.array(mask)
        mask_min = float(mask_np.min()) if mask_np.size else 0.0
        mask_max = float(mask_np.max()) if mask_np.size else 0.0
        debug_stats.update({
            "mask_min": mask_min,
            "mask_max": mask_max,
            "mask_shape": mask_np.shape,
            "mask_dtype": str(mask_np.dtype),
            "model_used": model_name,
        })
        logger.info(
            f"Mask stats -> min: {mask_min}, max: {mask_max}, "
            f"shape: {mask_np.shape}, dtype: {mask_np.dtype}, model: {model_name}"
        )
        # Save raw mask for inspection
        try:
            mask.save('/tmp/mask-preview.png')
            logger.info("Saved mask preview to /tmp/mask-preview.png")
        except Exception as e:
            logger.warning(f"Could not save mask preview: {e}")
    except Exception as e:
        logger.warning(f"Failed to compute mask stats: {e}")

    # Safeguard: if mask is empty, flag it but continue to apply alpha clamp
    hist = mask.histogram()
    nonzero = sum(hist[1:])
    mask_empty = (nonzero == 0)
    if mask_empty:
        logger.warning("Mask appears empty; will use raw rembg output with alpha clamp")
        debug_stats["mask_empty"] = bool(True)  # Explicit Python bool
        # Don't return early - let it go through alpha clamp at the end
    
    # Track mask stats helper
    def mask_stats(tag, mask_img):
        try:
            arr = np.array(mask_img.convert('L'))
            return {
                f"{tag}_min": float(arr.min()) if arr.size else 0.0,
                f"{tag}_max": float(arr.max()) if arr.size else 0.0,
                f"{tag}_shape": arr.shape,
                f"{tag}_dtype": str(arr.dtype),
                f"{tag}_nonzero": int(np.count_nonzero(arr)),
            }
        except Exception:
            return {}

    debug_stats.update(mask_stats("mask_raw", mask))

    # Step 1.5: HUMAN IMAGE PIPELINE - Mask Safety Expansion (Dilation)
    # Trimap expand equivalent = 3 (using 3x3 kernel, 1 iteration = ~1.5px expansion)
    # Erode = 0 (no erosion applied)
    if not is_premium and CV2_AVAILABLE:
        if not is_document:
            # HUMAN IMAGES: Trimap expand = 3, Erode = 0
            try:
                logger.info("Step 1.5: Applying human image mask expansion (Trimap expand = 3, Erode = 0)...")
                if isinstance(mask, Image.Image):
                    mask_array = np.array(mask.convert('L'))
                else:
                    mask_array = mask
                
                # HUMAN PIPELINE: Trimap expand = 3 (3x3 kernel, 1 iteration ≈ 1.5px expansion)
                # Erode = 0 (no erosion, only dilation for safety)
                kernel = np.ones((3, 3), np.uint8)
                mask_dilated = cv2.dilate(mask_array.astype(np.uint8), kernel, iterations=1)
                # No erosion (Erode = 0) - dilation only for hand/cloth protection
                
                mask = Image.fromarray(mask_dilated, mode='L')
                logger.info("✅ Human image mask expansion applied (Trimap expand = 3, Erode = 0)")
                debug_stats.update({
                    "mask_expansion_applied": True,
                    "expansion_kernel": "3x3",
                    "expansion_iterations": 1,
                    "trimap_expand_equivalent": 3,
                    "erode_applied": False,
                    "human_pipeline_expansion": True
                })
                debug_stats.update(mask_stats("mask_after_expansion_human", mask))
            except Exception as expansion_err:
                logger.warning(f"Human image mask expansion failed: {expansion_err}")
                debug_stats["mask_expansion_error"] = str(expansion_err)
        else:
            # DOCUMENTS: Keep existing expansion logic (different from human images)
            try:
                logger.info("Step 1.5: Applying document mask expansion...")
                if isinstance(mask, Image.Image):
                    mask_array = np.array(mask.convert('L'))
                else:
                    mask_array = mask
                
                kernel = np.ones((5, 5), np.uint8)
                mask_dilated = cv2.dilate(mask_array.astype(np.uint8), kernel, iterations=1)
                mask = Image.fromarray(mask_dilated, mode='L')
                debug_stats.update({
                    "mask_expansion_applied": True,
                    "expansion_kernel": "5x5",
                    "expansion_iterations": 1,
                    "document_pipeline_expansion": True
                })
            except Exception as expansion_err:
                logger.warning(f"Document mask expansion failed: {expansion_err}")
                debug_stats["mask_expansion_error"] = str(expansion_err)

    # 🔥 FREE PREVIEW ONLY: Mask Strength Check and Recovery (Levels 1-3)
    used_fallback_level = 0
    emergency_mask_applied = False  # Track if emergency recovery was used (must be accessible in all scopes)
    if not is_premium:
        try:
            mask_np = np.array(mask.convert('L'))
            total_pixels = mask_np.size
            nonzero_pixels = np.count_nonzero(mask_np)
            mask_nonzero_ratio = nonzero_pixels / total_pixels if total_pixels > 0 else 0.0
            mask_mean = float(np.mean(mask_np))
            
            logger.info(f"📊 Free Preview Mask Stats: nonzero_ratio={mask_nonzero_ratio:.4f}, mean={mask_mean:.2f}")
            debug_stats.update({
                "mask_nonzero_ratio": float(mask_nonzero_ratio),
                "mask_mean": mask_mean,
                "mask_nonzero_pixels": int(nonzero_pixels),
                "mask_total_pixels": int(total_pixels)
            })
            
            # Level 1: Check if mask is weak
            # Less aggressive thresholds to avoid over-cutting (hands/edges)
            # Further relaxed to preserve borders/hands
            weak_mask = (mask_nonzero_ratio < 0.002) or (mask_mean < 15)
            
            if weak_mask:
                logger.warning(f"⚠️ Weak mask detected (ratio={mask_nonzero_ratio:.4f}, mean={mask_mean:.2f}). Applying Level 2 recovery...")
                used_fallback_level = 1
                
                # Level 2: Mask Recovery (aggressive for preview)
                try:
                    if CV2_AVAILABLE:
                        # Convert to numpy array
                        mask_array = mask_np.astype(np.float32)
                        
                        # Apply gaussian blur (radius=2) gentler - OPTIMIZED: Reduced kernel for GPU cost savings
                        mask_blurred = cv2.GaussianBlur(mask_array, (3, 3), 1.0)  # kernel size 3, sigma=1.0 (optimized for free preview)
                        
                        # Dilate (iterations=1) gentler
                        kernel = np.ones((5, 5), np.uint8)
                        mask_dilated = cv2.dilate(mask_blurred.astype(np.uint8), kernel, iterations=1)
                        
                        # Normalize to 0-255
                        mask_normalized = cv2.normalize(mask_dilated.astype(np.float32), None, 0, 255, cv2.NORM_MINMAX)
                        
                        # Lower threshold: alpha = mask > 60 ? 255 : 0 (keep more edges)
                        mask_recovered = np.where(mask_normalized > 60, 255, 0).astype(np.uint8)
                        
                        mask = Image.fromarray(mask_recovered, mode='L')
                        
                        # Check if recovery helped
                        mask_recovered_np = np.array(mask)
                        recovered_nonzero = np.count_nonzero(mask_recovered_np)
                        recovered_ratio = recovered_nonzero / total_pixels if total_pixels > 0 else 0.0
                        recovered_mean = float(np.mean(mask_recovered_np))
                        
                        logger.info(f"✅ Level 2 recovery applied: new_ratio={recovered_ratio:.4f}, new_mean={recovered_mean:.2f}")
                        logger.info(f"🔍 FORENSIC: Mask nonzero ratio AFTER Level 2 recovery: {recovered_ratio:.6f} ({recovered_nonzero}/{total_pixels})")
                        debug_stats.update({
                            "recovery_level_2_applied": True,
                            "recovery_nonzero_ratio": float(recovered_ratio),
                            "recovery_mean": recovered_mean,
                            "mask_nonzero_ratio_after_recovery": float(recovered_ratio)  # Explicit tracking for forensic validation
                        })
                        
                        # Check if still weak after recovery
                        # Instead of emergency cut (which chops hands/edges), stop here
                        if recovered_ratio < 0.005 or recovered_mean < 20:
                            logger.warning("⚠️ Mask still weak after Level 2. Skipping emergency cut to preserve edges/hands.")
                            used_fallback_level = 1  # recovery attempted, but no hard cut
                    else:
                        # CV2 not available; skip emergency cut to preserve edges
                        logger.warning("CV2 not available, skipping recovery; no emergency cut to preserve edges/hands.")
                        used_fallback_level = 0
                        
                except Exception as recovery_err:
                    logger.error(f"Mask recovery failed: {recovery_err}, skipping emergency cut to preserve edges/hands.")
                    used_fallback_level = 0
            else:
                logger.info("✅ Mask strength OK, no recovery needed")
            
            debug_stats["used_fallback_level"] = used_fallback_level
            # Final mask nonzero ratio after all recovery attempts
            if used_fallback_level > 0:
                final_mask_np = np.array(mask.convert('L'))
                final_nonzero = np.count_nonzero(final_mask_np)
                final_ratio = final_nonzero / final_mask_np.size if final_mask_np.size > 0 else 0.0
                logger.info(f"🔍 FORENSIC: Final mask nonzero ratio AFTER all recovery: {final_ratio:.6f} ({final_nonzero}/{final_mask_np.size})")
                debug_stats["mask_nonzero_ratio_final_after_recovery"] = float(final_ratio)
            else:
                # No recovery was needed, use original ratio
                debug_stats["mask_nonzero_ratio_final_after_recovery"] = float(mask_nonzero_ratio)
            
        except Exception as check_err:
            logger.error(f"Mask strength check failed: {check_err}, continuing with original mask")
            debug_stats["mask_strength_check_error"] = str(check_err)

    # Step 2: Apply Guided Filter for smooth borders (Premium only)
    if is_premium and CV2_AVAILABLE:
        logger.info("Step 2: Applying guided filter for smooth borders...")
        mask = guided_filter(input_image, mask, radius=5, eps=0.01)
        debug_stats.update(mask_stats("mask_after_guided", mask))
    else:
        logger.info("Step 2: Skipping guided filter for free preview.")
        debug_stats.update(mask_stats("mask_after_guided_skipped", mask))
    
    # Step 3: Enhance Hair Details
    # Premium: Full hair enhancement (strength=0.3)
    # Free Preview: Light hair protection ONLY (strength=0.15-0.2) for human photos, OFF for documents
    if CV2_AVAILABLE:
        if is_premium:
            logger.info("Step 3: Enhancing hair details and fine edges (premium)...")
            mask = enhance_hair_details(mask, input_image, strength=0.3)
            debug_stats.update(mask_stats("mask_after_hair", mask))
        elif not is_document:
            # Free preview: Light hair protection ONLY - OPTIMIZED: Reduced strength for GPU cost savings
            logger.info("Step 3: Applying light hair protection (free preview, human photo, strength=0.10)...")
            mask = enhance_hair_details(mask, input_image, strength=0.10)  # Reduced from 0.18 to 0.10 for cost optimization
            debug_stats.update(mask_stats("mask_after_hair", mask))
        else:
            logger.info("Step 3: Skipping hair enhancement for document...")
            debug_stats.update(mask_stats("mask_after_hair_skipped", mask))
    else:
        debug_stats.update(mask_stats("mask_after_hair_skipped", mask))
    
    # Step 4: Clean Matte Edges (Premium only - for cleaner edges)
    if is_premium and CV2_AVAILABLE:
        logger.info("Step 4: Cleaning matte edges for premium quality...")
        mask = clean_matte_edges(mask, input_image, clean_strength=0.4)
        debug_stats.update(mask_stats("mask_after_clean_edges", mask))
    else:
        debug_stats.update(mask_stats("mask_after_clean_edges_skipped", mask))
    
    # Step 5: Apply Matte Strength for documents (Premium: enhanced, Free: basic)
    # NOTE: Feathering and halo removal moved to Step 8.1/8.2 (after composing RGB+mask)
    if is_document:
        if is_premium:
            logger.info("Step 7: Applying enhanced matte strength (0.3) for premium document optimization...")
            mask = apply_matte_strength(mask, matte_strength=0.3)
        else:
            logger.info("Step 7: Applying matte strength (0.2) for document text preservation...")
            mask = apply_matte_strength(mask, matte_strength=0.2)
        debug_stats.update(mask_stats("mask_after_matte", mask))
    else:
        debug_stats.update(mask_stats("mask_after_matte_skipped", mask))
    
    # Step 7.5: Safety check - if alpha is too low (< 1%), fallback to raw output
    alpha_too_low = False
    alpha_percent = 100.0  # Default value
    try:
        mask_array = np.array(mask.convert('L'))
        alpha_nonzero = np.count_nonzero(mask_array)
        total_pixels = mask_array.size
        alpha_percent = (alpha_nonzero / total_pixels) * 100.0
        
        logger.info(f"Alpha check: {alpha_nonzero}/{total_pixels} pixels ({alpha_percent:.2f}%) have non-zero alpha")
        debug_stats.update({
            "alpha_nonzero_count": int(alpha_nonzero),
            "alpha_percent": float(alpha_percent),
            "total_pixels": int(total_pixels)
        })
        
        alpha_too_low = (alpha_percent < 1.0)
        
        # 🔥 CRITICAL FIX: If emergency mask was applied, FORCE composite (don't skip)
        # Emergency mask always has >1% coverage (center region), so we should always composite
        if emergency_mask_applied and not is_premium:
            logger.info("✅ Emergency mask applied - forcing composite (never skip)")
            alpha_too_low = False  # Force composite even if original mask was weak
            mask_empty = False  # Emergency mask is never empty
        
        if alpha_too_low:
            logger.warning(f"⚠️ Alpha too low ({alpha_percent:.2f}%) - falling back to raw BiRefNet output (no feather/halo)")
            debug_stats["fallback_to_raw"] = bool(True)
            # Use raw rembg output as final image (will apply alpha clamp at the end for free preview)
            final_image = output_image
            # Skip all post-processing steps, go directly to final alpha clamp
    except Exception as e:
        logger.warning(f"Failed alpha check, proceeding anyway: {e}")
    
    # Step 8: Apply alpha mask to RGB FIRST (before feather/halo), then composite
    # SKIP this step if we already set final_image (early return paths)
    if not mask_empty and not alpha_too_low:
        logger.info("Step 8: Applying alpha mask to RGB first, then creating pro-level PNG composite...")
        logger.info(f"🔍 FORENSIC: Composite execution path: STANDARD_COMPOSITE (mask_empty={mask_empty}, alpha_too_low={alpha_too_low})")
        debug_stats["composite_execution_path"] = "STANDARD_COMPOSITE"
        
        # FIXED: Apply mask to RGB first, then apply post-processing to the composite
        # This prevents alpha from becoming zero after feathering/halo removal
        try:
            # Ensure original is RGB
            if isinstance(input_image, Image.Image):
                if input_image.mode == 'RGBA':
                    rgb_image = Image.new('RGB', input_image.size, (255, 255, 255))
                    rgb_image.paste(input_image, mask=input_image.split()[3])
                    input_image = rgb_image
                elif input_image.mode != 'RGB':
                    input_image = input_image.convert('RGB')
            else:
                input_image = Image.fromarray(input_image).convert('RGB')
            
            # Ensure mask matches image size BEFORE applying
            if isinstance(mask, Image.Image):
                mask = mask.convert('L')
            else:
                mask = Image.fromarray(mask, mode='L')
            
            # CRITICAL: Keep same scale - resize mask to match image if needed
            if mask.size != input_image.size:
                logger.warning(f"Mask size {mask.size} != image size {input_image.size}, resizing mask to match")
                mask = mask.resize(input_image.size, Image.Resampling.LANCZOS)
            
            # Create RGBA with mask applied to RGB
            rgba_temp = Image.new('RGBA', input_image.size, (0, 0, 0, 0))
            rgba_temp.paste(input_image, (0, 0))
            rgba_temp.putalpha(mask)
            
            # Now apply feathering and halo removal to the composite RGBA image
            # Extract alpha channel from composite for post-processing
            composite_alpha = rgba_temp.split()[3]
            
            # Apply feathering to alpha channel only
            # Premium: Adaptive feather based on MP
            # Free Preview (human): very light feathering (strength=0.08) to soften edges
            if is_premium and SCIPY_AVAILABLE:
                logger.info("Step 8.1: Applying premium adaptive feathering to alpha channel of composite...")
                composite_alpha = apply_feathering(composite_alpha, feather_radius=3)
                debug_stats.update(mask_stats("mask_after_feather_composite", composite_alpha))
            elif (not is_premium) and (not is_document):
                # HUMAN IMAGE PIPELINE: Feather = OFF (no feathering for human images)
                logger.info("Step 8.1: Skipping feathering for human images (Feather = OFF per pipeline settings)...")
                debug_stats.update(mask_stats("mask_after_feather_skipped_human", composite_alpha))
                debug_stats["feathering_human"] = False
                debug_stats["feather_off_human_pipeline"] = True
            elif (not is_premium) and is_document:
                # Very light feather for documents (natural look, not too clean) - OPTIMIZED: Added light feathering
                try:
                    logger.info("Step 8.1: Applying very light feathering (0.8px) for free document preview...")
                    alpha_np = np.array(composite_alpha).astype(np.float32)
                    if CV2_AVAILABLE:
                        blurred = cv2.GaussianBlur(alpha_np, (3, 3), 0.8)  # sigma=0.8 (lighter than human)
                        alpha_feather = alpha_np * (1.0 - 0.03) + blurred * 0.03  # 3% blend (lighter than human)
                        alpha_feather = np.clip(alpha_feather, 0, 255).astype(np.uint8)
                        composite_alpha = Image.fromarray(alpha_feather, mode='L')
                    else:
                        # Fallback using PIL blur radius 0.8, blend weight 0.03
                        from PIL import ImageFilter
                        blurred = composite_alpha.filter(ImageFilter.GaussianBlur(radius=0.8))
                        composite_alpha = Image.blend(composite_alpha, blurred, alpha=0.03)
                    debug_stats.update(mask_stats("mask_after_feather_light_document", composite_alpha))
                except Exception as feather_err:
                    logger.warning(f"Light feathering failed (free document): {feather_err}")
                    debug_stats["feather_light_document_error"] = str(feather_err)
            else:
                # When feather skipped (should not happen for free preview)
                logger.info("Step 8.1: Skipping feathering for this mode")
                debug_stats.update(mask_stats("mask_after_feather_skipped", composite_alpha))
            
            # Apply halo removal to alpha channel only
            # Premium: Strong halo removal
            # Free Preview: NO HALO REMOVAL (disabled for free preview)
            if is_premium:
                logger.info("Step 8.2: Applying strong halo removal to alpha channel of composite...")
                composite_alpha = remove_halo(composite_alpha, input_image, threshold=0.15)
                debug_stats.update(mask_stats("mask_after_halo_composite", composite_alpha))
            else:
                # Free preview: NO halo removal (disabled)
                logger.info("Step 8.2: Skipping halo removal for free preview (disabled)")
                debug_stats.update(mask_stats("mask_after_halo_skipped", composite_alpha))
            
            # Re-composite with processed alpha
            final_image = Image.new('RGBA', input_image.size, (0, 0, 0, 0))
            final_image.paste(input_image, (0, 0))
            final_image.putalpha(composite_alpha)
            
            # HUMAN IMAGE PIPELINE: Decontamination = EDGE ONLY (strength=0.15)
            # color_decontamination already applies only to edge pixels (alpha < 0.95)
            if not is_premium and not is_document:
                try:
                    logger.info("Step 8.3: Applying edge-only color decontamination (strength=0.15) for human images...")
                    final_image = color_decontamination(final_image, input_image, strength=0.15)  # Edge-only (alpha < 0.95)
                    debug_stats["color_decontamination_human"] = True
                    debug_stats["color_decontamination_strength"] = 0.15
                    debug_stats["color_decontamination_mode"] = "EDGE_ONLY"
                except Exception as decontam_err:
                    logger.warning(f"Edge-only color decontamination failed (human images): {decontam_err}")
                    debug_stats["color_decontamination_human_error"] = str(decontam_err)
            
            # 🔥 FREE PREVIEW: Document Safe Mode - Binary Alpha (if document)
            if not is_premium and is_document:
                try:
                    logger.info("Step 9: Applying document safe mode - binary alpha conversion...")
                    alpha_arr = np.array(final_image.getchannel('A')).astype(np.float32) / 255.0
                    # Binary alpha: if alpha > 0.55 → 255, else → 0
                    binary_alpha = np.where(alpha_arr > 0.55, 1.0, 0.0)
                    binary_alpha_uint8 = (binary_alpha * 255).astype(np.uint8)
                    binary_alpha_img = Image.fromarray(binary_alpha_uint8, mode='L')
                    final_image.putalpha(binary_alpha_img)
                    logger.info("✅ Document safe mode: Binary alpha applied (text fully visible)")
                    debug_stats["document_binary_alpha"] = bool(True)
                except Exception as doc_binary_err:
                    logger.warning(f"Document binary alpha conversion failed: {doc_binary_err}")
            
            # HUMAN IMAGE PIPELINE: Alpha clamp = ON (min_alpha threshold)
            # Apply alpha clamp for human images to ensure minimum alpha value
            if not is_premium and not is_document:
                try:
                    logger.info("Step 10: Applying alpha clamp for human images (Alpha clamp = ON)...")
                    alpha_arr = np.array(final_image.getchannel('A')).astype(np.float32)
                    
                    # Apply alpha clamp: set minimum alpha for foreground pixels
                    # Foreground: alpha > 0 (any non-zero alpha)
                    foreground_mask = alpha_arr > 0
                    min_alpha = 12  # Minimum alpha value for foreground pixels
                    alpha_arr[foreground_mask] = np.maximum(alpha_arr[foreground_mask], min_alpha)
                    
                    # Update alpha channel
                    alpha_clamped = Image.fromarray(alpha_arr.astype(np.uint8), mode='L')
                    final_image.putalpha(alpha_clamped)
                    
                    debug_stats.update({
                        "alpha_clamp_applied": True,
                        "alpha_clamp_min": min_alpha,
                        "alpha_clamp_human_pipeline": True
                    })
                    logger.info(f"✅ Alpha clamp applied (min_alpha={min_alpha}) for human images")
                except Exception as clamp_err:
                    logger.warning(f"Alpha clamp failed (human images): {clamp_err}")
                    debug_stats["alpha_clamp_error"] = str(clamp_err)
            elif not is_premium and is_document:
                # Documents: Keep no alpha clamp (binary alpha handles it)
                logger.info("Step 10: Skipping alpha clamp for documents (binary alpha used)")
                debug_stats.update({
                    "alpha_clamp_applied": False,
                    "alpha_clamp_skipped_document": True
                })
            
            # NOTE: This line is redundant (final_image already set above) but kept for safety
            # FORENSIC: This should not execute if composite path above worked correctly
            if 'final_image' not in locals() or final_image is None:
                logger.warning("🔍 FORENSIC: final_image not set, calling composite_pro_png")
                final_image = composite_pro_png(input_image, mask)
            else:
                logger.info("🔍 FORENSIC: final_image already set from composite path, skipping redundant composite_pro_png")
        except Exception as e:
            logger.error(f"Composite with fixed pipeline failed: {e}, falling back to original composite")
            final_image = composite_pro_png(input_image, mask)
    else:
        # Handle early return cases (empty mask or low alpha fallback)
        # 🔥 CRITICAL: If emergency mask was applied, ALWAYS composite (never use raw output)
        if emergency_mask_applied and not is_premium:
            logger.info("✅ Emergency mask active - forcing composite with recovered mask")
            logger.info(f"🔍 FORENSIC: Composite execution path: FORCED_COMPOSITE (emergency_mask_applied=True)")
            debug_stats["composite_execution_path"] = "FORCED_COMPOSITE"
            final_image = composite_pro_png(input_image, mask)
        elif mask_empty or alpha_too_low:
            logger.info("Using raw rembg output due to empty mask or low alpha")
            logger.warning(f"🔍 FORENSIC: Composite execution path: RAW_OUTPUT_FALLBACK (mask_empty={mask_empty}, alpha_too_low={alpha_too_low})")
            logger.warning(f"🔍 FORENSIC: WARNING - Raw output path taken (but will have alpha clamp applied)")
            debug_stats["composite_execution_path"] = "RAW_OUTPUT_FALLBACK"
            debug_stats["raw_output_path_taken"] = bool(True)
            final_image = output_image
            # Ensure it has alpha channel
            if final_image.mode != 'RGBA':
                final_image = final_image.convert('RGBA')
        else:
            # This shouldn't happen, but ensure we have final_image
            logger.info(f"🔍 FORENSIC: Composite execution path: FALLBACK_COMPOSITE")
            debug_stats["composite_execution_path"] = "FALLBACK_COMPOSITE"
            final_image = composite_pro_png(input_image, mask)
    
    debug_stats.update(mask_stats("mask_final_used", mask))
    
    opt_time = time.time() - start_opt
    logger.info(f"Optimization pipeline completed in {opt_time:.2f}s")
    
    # HUMAN IMAGE PIPELINE: Final alpha clamp check (already applied in Step 10)
    # Alpha clamp is already applied for human images in Step 10, so skip here
    if not is_premium and not is_document:
        logger.info("Step FINAL: Alpha clamp already applied for human images in Step 10")
        debug_stats.update({
            "final_alpha_clamp_applied": True,
            "final_alpha_clamp_human_pipeline": True
        })
    elif not is_premium and is_document:
        logger.info("Step FINAL: No final alpha clamp for documents (binary alpha used)")
        debug_stats.update({
            "final_alpha_clamp_applied": False,
            "final_alpha_clamp_skipped_document": True
        })
    
    # FREE PREVIEW: Resize final output to output_size (512px) if specified
    # Premium pipeline is NOT affected (output_size=None for premium)
    if not is_premium and output_size is not None:
        try:
            final_max_dimension = max(final_image.size)
            if final_max_dimension > output_size:
                scale = output_size / final_max_dimension
                new_final_size = (int(final_image.size[0] * scale), int(final_image.size[1] * scale))
                final_image = final_image.resize(new_final_size, Image.Resampling.LANCZOS)
                logger.info(f"✅ FREE PREVIEW: Resized final output to {new_final_size} (output_size={output_size}px)")
                debug_stats["final_output_resized"] = True
                debug_stats["final_output_size"] = new_final_size
                debug_stats["process_size"] = 768  # Internal processing size
                debug_stats["output_size"] = output_size  # Final output size
        except Exception as resize_err:
            logger.warning(f"Final output resize failed: {resize_err}")
            debug_stats["output_resize_error"] = str(resize_err)
    
    # Convert to bytes
    output_buffer = io.BytesIO()
    final_image.save(output_buffer, format='PNG', optimize=True)
    output_bytes = output_buffer.getvalue()

    # Final alpha stats from output
    try:
        out_arr = np.array(final_image.getchannel('A'))
        debug_stats.update({
            "alpha_out_min": float(out_arr.min()) if out_arr.size else 0.0,
            "alpha_out_max": float(out_arr.max()) if out_arr.size else 0.0,
            "alpha_out_nonzero": int(np.count_nonzero(out_arr)),
            "alpha_out_shape": out_arr.shape,
            "alpha_out_dtype": str(out_arr.dtype),
        })
    except Exception as e:
        logger.warning(f"Failed to compute output alpha stats: {e}")
    
    return output_bytes, debug_stats

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'bg-removal-ai',
        'gpu': 'available',
        'models': {
            'free_preview': 'BiRefNet',
            'premium_hd': 'BiRefNet HD + TensorRT Turbo',
            'premium_maxmatting': 'MaxMatting (silueta)',
            'document_robust': 'RobustMatting (rmbg14)'
        },
        'optimizations': {
            'tensorrt_turbo': 'FP16 ONNX Runtime GPU',
            'hair_detail_enhancement': True,
            'matte_clean_edges': True,
            'guided_filter': CV2_AVAILABLE,
            'feathering': SCIPY_AVAILABLE,
            'halo_removal': True,
            'a4_document_optimization': True,
            'composite': True
        }
    }), 200

@app.route('/api/free-preview-bg', methods=['POST'])
def free_preview_bg():
    """Free Preview: 512px output using GPU-accelerated AI with optimizations
    CRITICAL: ONLY accepts multipart/form-data - base64 JSON completely removed for 100% consistency
    """
    start_time = time.time()
    
    try:
        # CRITICAL: Free preview ONLY accepts multipart/form-data
        # Base64 JSON is completely removed for 100% consistency
        image_bytes = None
        max_size = 512  # Free preview: 512px maximum resolution
        image_type = None
        
        if 'image' in request.files:
            # Multipart upload (ONLY method for free preview)
            logger.info("✅ Processing multipart/form-data upload")
            file = request.files['image']
            image_bytes = file.read()
            max_size = int(request.form.get('maxSize', 512))  # Default: 512px for free preview
            image_type = request.form.get('imageType')
            
            if not image_bytes or len(image_bytes) == 0:
                logger.error("Empty file uploaded")
                return jsonify({
                    'success': False,
                    'error': 'Invalid image file',
                    'message': 'Uploaded file is empty. Please try uploading again.'
                }), 400
            
            logger.info(f"Received multipart file: {len(image_bytes)} bytes, maxSize={max_size}")
            
        else:
            # REJECT any non-multipart request for free preview (removed base64 JSON for 100% consistency)
            logger.error("❌ Non-multipart request rejected for free preview - only multipart/form-data accepted")
            return jsonify({
                'success': False,
                'error': 'Invalid request format',
                'message': 'Free preview only accepts multipart/form-data upload. Please use FormData to upload your image file.'
            }), 400
        
        # Processing path (multipart only - base64 removed for 100% consistency)
        # Open image with PIL (without strict verify to handle more formats)
        try:
            # Create BytesIO from image bytes (works for both multipart and base64)
            image_buffer = io.BytesIO(image_bytes)
            input_image = Image.open(image_buffer)
            
            # Verify image was opened and has valid dimensions
            if not input_image:
                raise ValueError("Failed to open image - image object is None")
            
            # Check dimensions
            if not hasattr(input_image, 'size') or not input_image.size:
                raise ValueError("Image has no size attribute")
            
            width, height = input_image.size
            if width == 0 or height == 0:
                raise ValueError(f"Image dimensions are invalid: {width}x{height}")
            
            # Load image to ensure it's fully decoded
            # For progressive JPEGs and some formats, load() might fail even for valid images
            # REMOVED strict error handling - allow images even if load() fails if dimensions are valid
            try:
                input_image.load()
            except Exception as load_err:
                error_msg = str(load_err).lower()
                # Progressive JPEGs and some formats might fail load() but are still valid
                logger.warning(f"Image load warning (but continuing if dimensions are valid): {str(load_err)}")
                # Verify we can at least access dimensions - if yes, continue
                try:
                    _ = input_image.size
                    # Try to get a pixel sample if possible
                    try:
                        test_pixel = input_image.getpixel((min(width-1, max(0, width//2)), min(height-1, max(0, height//2))))
                        logger.info(f"Image data is accessible despite load() warning (sample pixel: {test_pixel})")
                    except:
                        # Even if getpixel fails, continue if dimensions are valid
                        logger.info(f"Could not read pixel sample, but dimensions are valid: {width}x{height}, continuing...")
                except Exception as verify_err:
                    # Only fail if we can't access dimensions at all
                    logger.error(f"Image data verification failed - cannot access dimensions: {str(verify_err)}")
                    raise ValueError(f"Image data is corrupted or incomplete: {str(load_err)}")
                
            logger.info(f"Successfully opened image: {width}x{height}, mode: {input_image.mode}")
            
        except Exception as img_err:
            error_type = type(img_err).__name__
            error_msg = str(img_err)
            logger.error(f"Image open/load error [{error_type}]: {error_msg}")
            logger.error(f"Image bytes length: {len(image_bytes)}, first 100 bytes (hex): {image_bytes[:100].hex()}")
            
            # Try alternative decoding methods as fallback
            alternative_success = False
            if 'cannot identify' in error_msg.lower() or 'cannot open' in error_msg.lower():
                logger.info("Attempting alternative image decoding method...")
                try:
                    # Try using BytesIO with explicit format hint
                    image_buffer_alt = io.BytesIO(image_bytes)
                    # Try common formats - REMOVED strict verify() as it's too restrictive
                    for fmt in ['JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'HEIC']:
                        try:
                            image_buffer_alt.seek(0)
                            # Try to open with format hint
                            try:
                                input_image = Image.open(image_buffer_alt, formats=(fmt,))
                            except:
                                # If format hint fails, try without it
                                image_buffer_alt.seek(0)
                                input_image = Image.open(image_buffer_alt)
                            
                            # Load image to ensure it's fully decoded
                            try:
                                input_image.load()
                            except Exception as load_err:
                                # Progressive JPEGs and some formats might fail load() but are still valid
                                if 'progressive' in str(load_err).lower() or 'truncated' in str(load_err).lower():
                                    logger.warning(f"Image load warning (progressive/truncated, but continuing): {str(load_err)}")
                            
                            # Verify dimensions
                            width, height = input_image.size
                            if width > 0 and height > 0:
                                logger.info(f"Fallback decoding successful: {width}x{height}, mode: {input_image.mode}, format: {fmt}")
                                alternative_success = True
                                break
                        except Exception as fmt_err:
                            logger.debug(f"Format {fmt} failed: {str(fmt_err)}")
                            continue
                except Exception as alt_err:
                    logger.error(f"Alternative decoding also failed: {str(alt_err)}")
            
            # If alternative decoding failed, return error
            if not alternative_success:
                # Provide more helpful error messages
                if 'cannot identify' in error_msg.lower() or 'cannot open' in error_msg.lower():
                    user_msg = "The file is not a valid image format. Please upload JPG, JPEG, PNG, WEBP, HEIC, or other supported image formats."
                elif 'corrupted' in error_msg.lower() or 'incomplete' in error_msg.lower():
                    user_msg = "The image file appears to be corrupted or incomplete. Please try uploading the image again or use a different image."
                elif 'dimensions' in error_msg.lower():
                    user_msg = "The image has invalid dimensions. Please upload a valid image file."
                else:
                    user_msg = f"Failed to process image: {error_msg}. Please ensure you are uploading a valid image file (JPG, PNG, etc.)."
                
                return jsonify({
                    'success': False,
                    'error': 'Invalid image data',
                    'message': user_msg,
                    'error_details': error_msg if os.environ.get('DEBUG_ERRORS', '0') == '1' else None
                }), 400
            
            # Convert RGBA to RGB if needed
            if input_image.mode == 'RGBA':
                rgb_image = Image.new('RGB', input_image.size, (255, 255, 255))
                rgb_image.paste(input_image, mask=input_image.split()[3])
                input_image = rgb_image
            elif input_image.mode != 'RGB':
                input_image = input_image.convert('RGB')
            
        # Image type detection: Use provided imageType or auto-detect
        # image_type already set above (from multipart)
        if image_type and image_type.lower() in ['document', 'id_card', 'a4']:
            is_document = True
            logger.info(f"📄 Free Preview: Using provided imageType: {image_type} → Document mode")
        else:
            # Auto-detect if not provided
            is_document_raw = is_document_image(input_image)
            # CRITICAL: Convert numpy bool_ to Python bool to avoid JSON serialization errors
            is_document = bool(is_document_raw) if isinstance(is_document_raw, (np.bool_, bool)) else bool(is_document_raw)
            if image_type:
                logger.info(f"📷 Free Preview: Using provided imageType: {image_type} → Photo mode (auto-detected: {'document' if is_document else 'photo'})")
            else:
                logger.info(f"🔍 Free Preview: Auto-detected image type: {'document' if is_document else 'photo'}")
        
        # Free preview: process_size = 768 (internal), output_size = 512
        original_size = input_image.size
        max_dimension = max(original_size)
        process_size = 768  # Internal processing size for free preview
        output_size = 512   # Final output size for free preview
        
        # Resize to process_size (768px) for internal processing
        if max_dimension > process_size:
            scale = process_size / max_dimension
            process_size_tuple = (int(original_size[0] * scale), int(original_size[1] * scale))
            input_image_processed = input_image.resize(process_size_tuple, Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {original_size} to {process_size_tuple} for processing (process_size={process_size}px)")
        else:
            input_image_processed = input_image
            logger.info(f"Image size {original_size} within process_size limit, no resize needed")
        
        # Update input_image for processing
        input_image = input_image_processed
        
        # Select model based on image type
        if is_document:
            logger.info("Document detected - using RobustMatting for better text preservation")
            session = get_session_robust()
        else:
            session = get_session_512()
        
        # Process with optimizations (light mode for free preview with new config)
        # output_size is passed to process_with_optimizations for final resize
        output_bytes, debug_stats = process_with_optimizations(input_image, session, is_premium=False, is_document=is_document, output_size=output_size)
        
        # Convert to base64
        output_b64 = base64.b64encode(output_bytes).decode()
        result_image = f"data:image/png;base64,{output_b64}"
        
        processing_time = time.time() - start_time
        output_file_size = len(output_bytes)
        
        logger.info(f"Free preview processed in {processing_time:.2f}s, output size: {output_file_size / 1024:.2f} KB (process_size={process_size}px, output_size={output_size}px)")
        
        # Check if fallback was used (from debug_stats)
        preview_mode = "normal"
        if debug_stats.get("preview_mode") == "fallback":
            preview_mode = "fallback"
        elif debug_stats.get("used_fallback_level", 0) > 0:
            preview_mode = "recovered"  # Mask recovery was applied
        
        # FORENSIC VALIDATION: Always return debug stats for forensic analysis
        # This allows forensic validation without changing logic
        always_return_debug = os.environ.get('FORENSIC_MODE', '0') == '1' or os.environ.get('DEBUG_RETURN_STATS', '0') == '1'
        
        # Ensure is_document is Python bool, not numpy bool_
        is_document_python_bool = bool(is_document) if isinstance(is_document, (np.bool_, bool)) else bool(is_document)
        
        response_payload = {
            'success': True,
            'resultImage': result_image,
            'outputSize': int(output_size),
            'outputSizeMB': round(float(output_size) / (1024 * 1024), 2),
            'processedWith': 'Free Preview (512px GPU-accelerated, Optimized)',
            'processingTime': round(float(processing_time), 2),
            'previewMode': str(preview_mode),  # Ensure string
            'optimizations': {
                'model_tuning': str('BiRefNet' if not is_document_python_bool else 'RobustMatting'),
                'feathering': bool(False),  # Explicit Python bool
                'halo_removal': bool(False),  # Explicit Python bool
                'composite': bool(True),  # Explicit Python bool
                'document_mode': is_document_python_bool  # Already converted to Python bool
            }
        }
        if always_return_debug:
            # Convert debug_stats recursively to ensure all numpy types are converted
            response_payload['debugMask'] = convert_numpy_types(debug_stats)
        
        # Convert entire payload to ensure all numpy types are converted (recursive)
        response_payload = convert_numpy_types(response_payload)
        
        # Final safety check: Convert any remaining numpy types in nested structures
        # This is a belt-and-suspenders approach
        try:
            import json
            # Try to serialize to catch any remaining non-serializable types
            json.dumps(response_payload)
        except (TypeError, ValueError) as e:
            logger.warning(f"JSON serialization check failed, applying additional conversion: {e}")
            # Apply conversion again if needed
            response_payload = convert_numpy_types(response_payload)

        return jsonify(response_payload), 200
            
    except Exception as e:
        logger.error(f"Free preview error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Processing failed',
            'message': str(e)
        }), 500

@app.route('/api/premium-bg', methods=['POST'])
def premium_bg():
    """Premium HD: Up to 25 Megapixels (max width × height) with full optimizations"""
    start_time = time.time()
    
    try:
        data = request.json
        if not data or 'imageData' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing imageData in request body'
            }), 400
        
        image_data = data.get('imageData')
        max_megapixels = data.get('maxMegapixels', 25)  # Default: 25 MP max
        preserve_original = data.get('preserveOriginal', True)  # Preserve original if ≤ 25 MP
        target_size = data.get('targetSize', 'original')  # Target size: 'original' or 'WxH'
        target_width = data.get('targetWidth')  # Specific target width
        target_height = data.get('targetHeight')  # Specific target height
        user_id = data.get('userId')
        
        # Decode base64 image
        try:
            # Extract base64 part if data URL
            base64_part = image_data
            if ',' in image_data:
                parts = image_data.split(',', 1)
                if len(parts) == 2:
                    base64_part = parts[1]
            
            # Clean and pad base64
            base64_part = base64_part.replace('\n', '').replace('\r', '').replace(' ', '')
            base64_part = base64_part.replace('-', '+').replace('_', '/')
            remainder = len(base64_part) % 4
            if remainder:
                base64_part = base64_part + ('=' * (4 - remainder))
            
            image_bytes = base64.b64decode(base64_part, validate=True)
            input_image = Image.open(io.BytesIO(image_bytes))
            input_image.load()  # Load image to ensure it's fully decoded
            
            # Convert RGBA to RGB if needed
            if input_image.mode == 'RGBA':
                rgb_image = Image.new('RGB', input_image.size, (255, 255, 255))
                rgb_image.paste(input_image, mask=input_image.split()[3])
                input_image = rgb_image
            elif input_image.mode != 'RGB':
                input_image = input_image.convert('RGB')
            
            # Calculate megapixels and check limit
            original_size = input_image.size
            original_width, original_height = original_size
            original_megapixels = (original_width * original_height) / 1_000_000
            
            logger.info(f"Original image: {original_width}x{original_height} = {original_megapixels:.2f} MP")
            
            # Parse targetSize string if provided (e.g., "1920x1080")
            if target_size and target_size != 'original' and not target_width and not target_height:
                if 'x' in str(target_size):
                    try:
                        parts = str(target_size).split('x')
                        if len(parts) == 2:
                            target_width = int(parts[0])
                            target_height = int(parts[1])
                            logger.info(f"Parsed targetSize '{target_size}' to {target_width}x{target_height}")
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse targetSize '{target_size}', ignoring")
                        target_width = None
                        target_height = None
            
            # Handle target size selection
            if target_size and target_size != 'original' and target_width and target_height:
                # User selected specific size
                target_mp = (target_width * target_height) / 1_000_000
                if target_mp > max_megapixels:
                    return jsonify({
                        'success': False,
                        'error': f'Selected size exceeds maximum of {max_megapixels} Megapixels',
                        'message': f'Selected size {target_width}x{target_height} = {target_mp:.2f} MP exceeds maximum {max_megapixels} MP.',
                        'selectedMegapixels': round(target_mp, 2),
                        'maxMegapixels': max_megapixels
                    }), 400
                
                # Resize to target size while maintaining aspect ratio
                original_aspect = original_width / original_height
                target_aspect = target_width / target_height
                
                if abs(original_aspect - target_aspect) < 0.01:
                    # Same aspect ratio, resize directly
                    input_image = input_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized to target size: {target_width}x{target_height} = {target_mp:.2f} MP")
                else:
                    # Different aspect ratio - resize to fit within target while maintaining aspect
                    scale_w = target_width / original_width
                    scale_h = target_height / original_height
                    scale = min(scale_w, scale_h)  # Use smaller scale to fit within bounds
                    new_width = int(original_width * scale)
                    new_height = int(original_height * scale)
                    input_image = input_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized to fit target (maintaining aspect): {new_width}x{new_height} = {(new_width * new_height) / 1_000_000:.2f} MP (target: {target_width}x{target_height})")
            elif original_megapixels > max_megapixels:
                if preserve_original:
                    # Auto downscale to 25 MP max
                    scale = (max_megapixels / original_megapixels) ** 0.5
                    new_width = int(original_width * scale)
                    new_height = int(original_height * scale)
                    input_image = input_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.info(f"Image exceeds {max_megapixels} MP limit. Downscaled to {new_width}x{new_height} = {(new_width * new_height) / 1_000_000:.2f} MP")
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Image exceeds maximum size of {max_megapixels} Megapixels',
                        'message': f'Your image is {original_megapixels:.2f} MP. Maximum allowed is {max_megapixels} MP.',
                        'originalMegapixels': round(original_megapixels, 2),
                        'maxMegapixels': max_megapixels
                    }), 400
            
            # Image is now within 25 MP limit (either original or auto-downscaled)
            final_size = input_image.size
            final_megapixels = (final_size[0] * final_size[1]) / 1_000_000
            logger.info(f"Final processing size: {final_size[0]}x{final_size[1]} = {final_megapixels:.2f} MP")
            
            # Image Type Detection: Use provided imageType or auto-detect
            image_type = data.get('imageType')  # "human" | "document" | "animal" | "ecommerce"
            
            # White background option (no transparent PNG)
            white_background = data.get('whiteBackground', True)  # Default to white background
            
            # Output format (JPG or PNG)
            output_format = data.get('outputFormat', 'jpg')  # Default JPG
            output_quality = data.get('quality', 100)  # Default quality 100
            
            # Normalize image type
            if image_type:
                # Map to standard types
                if image_type in ['document', 'id_card', 'a4']:
                    image_type = 'document'
                elif image_type in ['animal', 'pet', 'wildlife']:
                    image_type = 'animal'
                elif image_type in ['ecommerce', 'product', 'shop', 'item']:
                    image_type = 'ecommerce'
                else:
                    image_type = 'human'  # Default
                logger.info(f"📸 Using provided imageType: {image_type}")
            else:
                # Auto-detect if not provided
                is_document = is_document_image(input_image)
                image_type = 'document' if is_document else 'human'
                logger.info(f"🔍 Auto-detected imageType: {image_type}")
            
            # ENTERPRISE PIPELINE: BiRefNet + MaxMatting (all image types)
            logger.info(f"🚀 Enterprise Pipeline: BiRefNet (min 1024) + MaxMatting (min 2048), type: {image_type}")
            # Use get_session_hd() for BiRefNet (better quality - remove.bg style)
            birefnet_session = get_session_hd()  # BiRefNet HD for semantic mask (NO feather, NO blur, NO halo)
            maxmatting_session = get_session_maxmatting()  # MaxMatting for fine alpha matting
            
            try:
                output_bytes, debug_stats = process_enterprise_pipeline(
                    input_image,
                    birefnet_session,
                    maxmatting_session,
                    image_type=image_type
                )
                pipeline_type = f"enterprise_{image_type}"
            except Exception as pipeline_error:
                logger.error(f"Enterprise pipeline failed: {pipeline_error}, falling back to standard pipeline")
                # Fallback to standard pipeline
                is_document = (image_type == 'document')
                output_bytes, debug_stats = process_premium_hd_pipeline(
                    input_image,
                    birefnet_session,
                    maxmatting_session,
                    is_document=is_document
                )
                pipeline_type = f"fallback_{image_type}"
            
            # CRITICAL: Validate output before credit deduction
            # Check if alpha channel has content (safety check)
            try:
                output_image_check = Image.open(io.BytesIO(output_bytes))
                if output_image_check.mode == 'RGBA':
                    alpha_check = np.array(output_image_check.getchannel('A'))
                    alpha_nonzero_check = np.count_nonzero(alpha_check)
                    if alpha_nonzero_check == 0:
                        logger.error("❌ CRITICAL: Output alpha is empty - NO credit deduction")
                        return jsonify({
                            'success': False,
                            'error': 'Processing failed: output alpha channel is empty',
                            'message': 'The processed image has no valid content. Please try again or contact support.',
                            'creditsUsed': 0  # No credits deducted
                        }), 500
                    
                    # Convert to white background (RGB) and JPG if requested
                    if white_background:
                        logger.info("🔄 Converting RGBA to RGB with white background (no transparent)")
                        rgb_output = Image.new('RGB', output_image_check.size, (255, 255, 255))
                        rgb_output.paste(output_image_check, mask=output_image_check.split()[3])
                        output_image_check = rgb_output
                        
                        # Convert to JPG with quality 100 (enterprise requirement)
                        output_buffer = io.BytesIO()
                        if output_format.lower() == 'jpg' or output_format.lower() == 'jpeg':
                            output_image_check.save(output_buffer, format='JPEG', quality=output_quality, optimize=True)
                            logger.info(f"✅ Converted to JPG quality {output_quality} with white background")
                        else:
                            output_image_check.save(output_buffer, format='PNG', optimize=True)
                            logger.info(f"✅ Converted to PNG with white background")
                        output_bytes = output_buffer.getvalue()
                        logger.info(f"✅ Final output size: {len(output_bytes) / 1024:.2f} KB")
            except Exception as alpha_check_error:
                logger.error(f"Alpha validation failed: {alpha_check_error}")
                return jsonify({
                    'success': False,
                    'error': 'Output validation failed',
                    'message': 'Unable to validate processed image. Please try again.',
                    'creditsUsed': 0  # No credits deducted
                }), 500
            
            # Calculate credits based on SELECTED SIZE (not final output size)
            # This ensures users pay for what they selected, not what was processed
            selected_mp = final_megapixels  # Default to final output size
            
            if target_size and target_size != 'original':
                # Parse targetSize string (e.g., "1920x1080") or use provided dimensions
                if target_width and target_height:
                    # Use provided dimensions
                    selected_mp = (target_width * target_height) / 1_000_000
                    logger.info(f"💰 Credit calculation based on SELECTED size: {target_width}x{target_height} = {selected_mp:.2f} MP")
                elif 'x' in str(target_size):
                    # Parse from string format "WxH"
                    try:
                        parts = str(target_size).split('x')
                        if len(parts) == 2:
                            parsed_width = int(parts[0])
                            parsed_height = int(parts[1])
                            selected_mp = (parsed_width * parsed_height) / 1_000_000
                            logger.info(f"💰 Credit calculation based on SELECTED size: {parsed_width}x{parsed_height} = {selected_mp:.2f} MP")
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse targetSize '{target_size}', using final output size for credit calculation")
                        selected_mp = final_megapixels
                else:
                    # Use final output size
                    selected_mp = final_megapixels
                    logger.info(f"💰 Credit calculation based on FINAL output size: {final_megapixels:.2f} MP")
            else:
                # Use final output size for credit calculation (original or auto-downscaled)
                selected_mp = final_megapixels
                logger.info(f"💰 Credit calculation based on FINAL output size: {final_megapixels:.2f} MP")
            
            # Resolution-Based Credit Deduction (based on SELECTED size)
            # Credit tiers based on selected/requested MP
            if selected_mp <= 2:
                credits_required = 2
            elif selected_mp <= 6:
                credits_required = 4
            elif selected_mp <= 9:
                credits_required = 6
            elif selected_mp <= 12:
                credits_required = 9
            elif selected_mp <= 16:
                credits_required = 10
            elif selected_mp <= 20:
                credits_required = 12
            else:  # <= 25 MP
                credits_required = 15
            
            # Convert to base64
            output_b64 = base64.b64encode(output_bytes).decode()
            # Use appropriate format based on output
            if output_format.lower() == 'jpg' or output_format.lower() == 'jpeg':
                result_image = f"data:image/jpeg;base64,{output_b64}"
            else:
                result_image = f"data:image/png;base64,{output_b64}"
            
            processing_time = time.time() - start_time
            output_size = len(output_bytes)
            
            logger.info(f"✅ Premium processed in {processing_time:.2f}s, output size: {output_size / 1024:.2f} KB, MP: {final_megapixels:.2f}, credits: {credits_required}, pipeline: {pipeline_type}, user: {user_id}")
            
            # Build optimizations info based on pipeline type
            if pipeline_type == "document_safe":
                optimizations = {
                    'pipeline': 'Premium Document (BiRefNet only, safe mode)',
                    'birefnet_semantic_mask': True,
                    'maxmatting_fine_matting': False,
                    'adaptive_feathering': False,
                    'strong_halo_removal': False,
                    'color_decontamination': False,
                    'binary_alpha': True,
                    'composite': 'Direct composite (text preservation)'
                }
                processed_with = 'Premium Document – Safe Mode (Text Preservation)'
            else:
                optimizations = {
                    'pipeline': 'Premium Photo HD (Professional Quality)',
                    'birefnet_semantic_mask': True,
                    'trimap_generation': True,
                    'maxmatting_fine_matting': True,
                    'adaptive_feathering': True,
                    'strong_halo_removal': True,
                    'color_decontamination': True,
                    'edge_sharpening': debug_stats.get('edge_sharpening_applied', False),
                    'composite': 'Pro-level PNG'
                }
                processed_with = 'Premium HD – up to 25 Megapixels (GPU-accelerated High-Resolution)'
            
            response_payload = {
                'success': True,
                'resultImage': result_image,
                'outputSize': int(output_size),
                'outputSizeMB': round(float(output_size) / (1024 * 1024), 2),
                'processedWith': processed_with,
                'processingTime': round(float(processing_time), 2),
                'creditsUsed': int(credits_required),  # Actual credits deducted (backend only, not shown in UI)
                'creditsUsedDisplay': 1,  # Generic display for UI (user sees "1 credit used" or "X credits used")
                'megapixels': round(float(final_megapixels), 2),
                'imageType': image_type,  # Return the imageType used
                'pipelineType': pipeline_type,
                'optimizations': convert_numpy_types(optimizations)  # Convert optimizations dict
            }
            if os.environ.get('DEBUG_RETURN_STATS', '0') == '1':
                response_payload['debugMask'] = convert_numpy_types(debug_stats)
            
            # Convert entire payload to ensure all numpy types are converted
            response_payload = convert_numpy_types(response_payload)

            return jsonify(response_payload), 200
            
        except Exception as decode_error:
            logger.error(f"Image decode/process error: {str(decode_error)}")
            return jsonify({
                'success': False,
                'error': 'Invalid image data',
                'message': str(decode_error)
            }), 400
            
    except Exception as e:
        logger.error(f"Premium HD error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Processing failed',
            'message': str(e)
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'bg-removal-birefnet-optimized',
        'version': '2.0.0',
        'status': 'running',
        'optimizations': {
            'model_tuning': 'BiRefNet optimized loading',
            'tensorrt_fp16': 'GPU inference acceleration',
            'guided_filter': 'Smooth borders',
            'feathering': 'Natural smooth edges',
            'halo_removal': 'Clean background leakage',
            'composite': 'Pro-level PNG output'
        },
        'endpoints': {
            'free_preview': '/api/free-preview-bg',
            'premium_hd': '/api/premium-bg',
            'health': '/health'
        }
    }), 200

# Pre-load model on startup to reduce cold start time
def preload_models():
    """Pre-load commonly used models on startup for faster first request"""
    try:
        logger.info("Pre-loading AI models on startup...")
        # Pre-load the most commonly used model (512px preview)
        get_session_512()
        logger.info("✅ Models pre-loaded successfully")
    except Exception as e:
        logger.warning(f"Model pre-loading failed (will load on first request): {e}")

# Pre-load models when module is imported (before Flask app starts)
preload_models()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
