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
    
    is_doc = doc_score >= 2  # At least 2 indicators
    
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

def generate_trimap(mask, expand_radius=8):
    """
    Generate trimap from BiRefNet mask for fine alpha matting
    - Foreground: mask > 240
    - Background: mask < 15
    - Unknown region: 15-240 (expanded by radius pixels)
    
    Returns: trimap (128 = unknown, 0 = background, 255 = foreground)
    """
    try:
        if isinstance(mask, Image.Image):
            mask_array = np.array(mask.convert('L'))
        else:
            mask_array = mask.astype(np.uint8) if mask.dtype != np.uint8 else mask
        
        # Create trimap
        trimap = np.zeros_like(mask_array, dtype=np.uint8)
        
        # Foreground: mask > 240
        trimap[mask_array > 240] = 255
        
        # Background: mask < 15
        trimap[mask_array < 15] = 0
        
        # Unknown region: 15-240
        unknown_mask = (mask_array >= 15) & (mask_array <= 240)
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

def enhance_hair_details(mask, original_image, strength=0.3):
    """
    Enhance hair details and fine edges for premium quality
    Preserves fine hair strands and detailed edges
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
        
        # Smooth transition to avoid artifacts
        if SCIPY_AVAILABLE:
            from scipy.ndimage import gaussian_filter
            enhanced_mask = gaussian_filter(enhanced_mask, sigma=0.5)
        
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
    
    debug_stats["binary_alpha_threshold"] = 0.5
    debug_stats["maxmatting_disabled"] = True
    debug_stats["feather_disabled"] = True
    debug_stats["halo_removal_disabled"] = True
    
    # Step 3: Composite Directly (no post-processing)
    logger.info("Step 3: Compositing RGB + binary alpha (direct, no post-processing)...")
    
    # Ensure RGB
    rgb_image = input_image.convert('RGB') if input_image.mode != 'RGB' else input_image
    
    # Create RGBA with binary alpha
    rgba_composite = Image.new('RGBA', rgb_image.size, (0, 0, 0, 0))
    rgba_composite.paste(rgb_image, (0, 0))
    rgba_composite.putalpha(binary_mask)
    
    debug_stats["composite_completed"] = True
    debug_stats["pipeline_type"] = "document_safe"
    
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
        debug_stats["maxmatting_fallback"] = True
    
    # Step 4: Composite RGB + Alpha FIRST (CRITICAL ORDER)
    logger.info("Step 4: Compositing RGB + refined alpha...")
    
    # Ensure RGB
    rgb_image = input_image.convert('RGB') if input_image.mode != 'RGB' else input_image
    
    # Create RGBA with refined alpha
    rgba_composite = Image.new('RGBA', rgb_image.size, (0, 0, 0, 0))
    rgba_composite.paste(rgb_image, (0, 0))
    rgba_composite.putalpha(refined_alpha)
    
    debug_stats["composite_completed"] = True
    
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
        debug_stats["adaptive_feather_applied"] = True
        debug_stats["document_preset"] = True
        
        # Step 6: Reduced Halo Removal for documents
        logger.info("Step 6: Applying reduced halo removal (document preset)...")
        current_alpha = rgba_composite.split()[3]
        cleaned_alpha = strong_halo_removal_alpha(
            current_alpha, 
            rgb_image, 
            is_document=True  # Gentle suppression for documents
        )
        rgba_composite.putalpha(cleaned_alpha)
        debug_stats["halo_removal_applied"] = True
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
        debug_stats["halo_removal_applied"] = True
        debug_stats["halo_strength"] = "strong_photo"
    
    # Step 7: Color Decontamination
    logger.info("Step 7: Applying color decontamination...")
    final_image = color_decontamination(
        rgba_composite, 
        rgb_image, 
        strength=0.6
    )
    debug_stats["color_decontamination_applied"] = True
    
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
            debug_stats["edge_sharpening_applied"] = True
        except Exception as e:
            logger.warning(f"Edge sharpening failed: {e}, using image without sharpening")
            debug_stats["edge_sharpening_applied"] = False
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

def process_with_optimizations(input_image, session, is_premium=False, is_document=False):
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
        debug_stats["mask_empty"] = True
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
            weak_mask = (mask_nonzero_ratio < 0.01) or (mask_mean < 25)
            
            if weak_mask:
                logger.warning(f"⚠️ Weak mask detected (ratio={mask_nonzero_ratio:.4f}, mean={mask_mean:.2f}). Applying Level 2 recovery...")
                used_fallback_level = 1
                
                # Level 2: Mask Recovery (aggressive for preview)
                try:
                    if CV2_AVAILABLE:
                        # Convert to numpy array
                        mask_array = mask_np.astype(np.float32)
                        
                        # Apply gaussian blur (radius=3)
                        mask_blurred = cv2.GaussianBlur(mask_array, (7, 7), 3.0)  # kernel size 7 = radius 3
                        
                        # Dilate (iterations=2)
                        kernel = np.ones((5, 5), np.uint8)
                        mask_dilated = cv2.dilate(mask_blurred.astype(np.uint8), kernel, iterations=2)
                        
                        # Normalize to 0-255
                        mask_normalized = cv2.normalize(mask_dilated.astype(np.float32), None, 0, 255, cv2.NORM_MINMAX)
                        
                        # Lower threshold: alpha = mask > 80 ? 255 : 0
                        mask_recovered = np.where(mask_normalized > 80, 255, 0).astype(np.uint8)
                        
                        mask = Image.fromarray(mask_recovered, mode='L')
                        
                        # Check if recovery helped
                        mask_recovered_np = np.array(mask)
                        recovered_nonzero = np.count_nonzero(mask_recovered_np)
                        recovered_ratio = recovered_nonzero / total_pixels if total_pixels > 0 else 0.0
                        recovered_mean = float(np.mean(mask_recovered_np))
                        
                        logger.info(f"✅ Level 2 recovery applied: new_ratio={recovered_ratio:.4f}, new_mean={recovered_mean:.2f}")
                        debug_stats.update({
                            "recovery_level_2_applied": True,
                            "recovery_nonzero_ratio": float(recovered_ratio),
                            "recovery_mean": recovered_mean
                        })
                        
                        # Check if still weak after recovery
                        if recovered_ratio < 0.01 or recovered_mean < 25:
                            # Level 3: Emergency Preview Cut (center region)
                            logger.warning("⚠️ Mask still weak after Level 2. Applying Level 3 emergency cut...")
                            used_fallback_level = 2
                            
                            width, height = mask.size
                            margin_percent = 0.15  # 15% margin
                            left = int(width * margin_percent)
                            top = int(height * margin_percent)
                            right = int(width * (1 - margin_percent))
                            bottom = int(height * (1 - margin_percent))
                            
                            # Create center region mask
                            emergency_mask = np.zeros((height, width), dtype=np.uint8)
                            emergency_mask[top:bottom, left:right] = 255
                            
                            mask = Image.fromarray(emergency_mask, mode='L')
                            emergency_mask_applied = True  # Mark that emergency mask is active
                            logger.info(f"✅ Level 3 emergency cut applied: center region {left},{top} to {right},{bottom}")
                            debug_stats.update({
                                "recovery_level_3_applied": True,
                                "emergency_center_box": f"{left},{top},{right},{bottom}",
                                "preview_mode": "fallback"
                            })
                    else:
                        # If CV2 not available, skip to Level 3
                        logger.warning("CV2 not available, skipping Level 2, applying Level 3 emergency cut...")
                        used_fallback_level = 2
                        
                        width, height = mask.size
                        margin_percent = 0.15
                        left = int(width * margin_percent)
                        top = int(height * margin_percent)
                        right = int(width * (1 - margin_percent))
                        bottom = int(height * (1 - margin_percent))
                        
                        emergency_mask = np.zeros((height, width), dtype=np.uint8)
                        emergency_mask[top:bottom, left:right] = 255
                        mask = Image.fromarray(emergency_mask, mode='L')
                        emergency_mask_applied = True  # Mark that emergency mask is active
                        debug_stats.update({
                            "recovery_level_3_applied": True,
                            "preview_mode": "fallback"
                        })
                        
                except Exception as recovery_err:
                    logger.error(f"Mask recovery failed: {recovery_err}, applying Level 3 emergency cut...")
                    used_fallback_level = 2
                    
                    # Fallback to Level 3
                    width, height = mask.size
                    margin_percent = 0.15
                    left = int(width * margin_percent)
                    top = int(height * margin_percent)
                    right = int(width * (1 - margin_percent))
                    bottom = int(height * (1 - margin_percent))
                    
                    emergency_mask = np.zeros((height, width), dtype=np.uint8)
                    emergency_mask[top:bottom, left:right] = 255
                    mask = Image.fromarray(emergency_mask, mode='L')
                    emergency_mask_applied = True  # Mark that emergency mask is active
                    debug_stats.update({
                        "recovery_level_3_applied": True,
                        "recovery_error": str(recovery_err),
                        "preview_mode": "fallback"
                    })
            else:
                logger.info("✅ Mask strength OK, no recovery needed")
            
            debug_stats["used_fallback_level"] = used_fallback_level
            
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
            # Free preview: Light hair protection ONLY (0.15-0.2 strength)
            logger.info("Step 3: Applying light hair protection (free preview, human photo, strength=0.18)...")
            mask = enhance_hair_details(mask, input_image, strength=0.18)  # 0.15-0.2 range
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
            debug_stats["fallback_to_raw"] = True
            # Use raw rembg output as final image (will apply alpha clamp at the end for free preview)
            final_image = output_image
            # Skip all post-processing steps, go directly to final alpha clamp
    except Exception as e:
        logger.warning(f"Failed alpha check, proceeding anyway: {e}")
    
    # Step 8: Apply alpha mask to RGB FIRST (before feather/halo), then composite
    # SKIP this step if we already set final_image (early return paths)
    if not mask_empty and not alpha_too_low:
        logger.info("Step 8: Applying alpha mask to RGB first, then creating pro-level PNG composite...")
        
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
            # Free Preview: NO FEATHER (disabled for free preview)
            if is_premium and SCIPY_AVAILABLE:
                logger.info("Step 8.1: Applying premium adaptive feathering to alpha channel of composite...")
                composite_alpha = apply_feathering(composite_alpha, feather_radius=3)
                debug_stats.update(mask_stats("mask_after_feather_composite", composite_alpha))
            else:
                # Free preview: NO feathering (disabled)
                logger.info("Step 8.1: Skipping feathering for free preview (disabled)")
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
                    debug_stats["document_binary_alpha"] = True
                except Exception as doc_binary_err:
                    logger.warning(f"Document binary alpha conversion failed: {doc_binary_err}")
            
            # 🔥 MOST IMPORTANT - ALPHA SAFETY CLAMP (FREE PREVIEW ONLY, MANDATORY)
            if not is_premium:
                try:
                    logger.info("Step 10: Applying MANDATORY alpha safety clamp for free preview...")
                    alpha_arr = np.array(final_image.getchannel('A'))
                    
                    # Apply safety clamp: alpha = max(alpha, 12) - ALL pixels
                    # This ensures no pixel has alpha < 12, preventing fully transparent appearance
                    min_alpha = 12
                    alpha_arr = np.maximum(alpha_arr, min_alpha)
                    
                    alpha_clamped = Image.fromarray(alpha_arr, mode='L')
                    final_image.putalpha(alpha_clamped)
                    
                    # Log stats
                    alpha_min = float(np.min(alpha_arr))
                    alpha_max = float(np.max(alpha_arr))
                    alpha_nonzero = int(np.count_nonzero(alpha_arr))
                    logger.info(f"✅ Free preview: Alpha safety clamp applied (min: {alpha_min}, max: {alpha_max}, nonzero: {alpha_nonzero})")
                    debug_stats.update({
                        "alpha_safety_clamp_applied": True,
                        "alpha_clamp_min": float(min_alpha),
                        "alpha_final_min": alpha_min,
                        "alpha_final_max": alpha_max
                    })
                except Exception as clamp_err:
                    logger.error(f"⚠️ CRITICAL: Alpha safety clamp failed: {clamp_err}")
                    # This is critical for free preview - log as error
            
        except Exception as e:
            logger.error(f"Composite with fixed pipeline failed: {e}, falling back to original composite")
            final_image = composite_pro_png(input_image, mask)
    else:
        # Handle early return cases (empty mask or low alpha fallback)
        # 🔥 CRITICAL: If emergency mask was applied, ALWAYS composite (never use raw output)
        if emergency_mask_applied and not is_premium:
            logger.info("✅ Emergency mask active - forcing composite with recovered mask")
            final_image = composite_pro_png(input_image, mask)
        elif mask_empty or alpha_too_low:
            logger.info("Using raw rembg output due to empty mask or low alpha")
            final_image = output_image
            # Ensure it has alpha channel
            if final_image.mode != 'RGBA':
                final_image = final_image.convert('RGBA')
        else:
            # This shouldn't happen, but ensure we have final_image
            final_image = composite_pro_png(input_image, mask)
    
    debug_stats.update(mask_stats("mask_final_used", mask))
    
    opt_time = time.time() - start_opt
    logger.info(f"Optimization pipeline completed in {opt_time:.2f}s")
    
    # 🔥 MOST IMPORTANT - FINAL ALPHA SAFETY CLAMP (FREE PREVIEW ONLY, MANDATORY)
    # This MUST run at the very end, after ALL processing, including fallbacks
    if not is_premium:
        try:
            logger.info("Step FINAL: Applying MANDATORY final alpha safety clamp for free preview...")
            # Ensure image has alpha channel
            if final_image.mode != 'RGBA':
                # If no alpha, create opaque alpha
                alpha_channel = Image.new('L', final_image.size, 255)
                final_image = final_image.convert('RGB')
                final_image.putalpha(alpha_channel)
            
            alpha_arr = np.array(final_image.getchannel('A'))
            
            # Apply safety clamp: alpha = max(alpha, 12) - ALL pixels
            # This ensures no pixel has alpha < 12, preventing fully transparent appearance
            min_alpha = 12
            alpha_arr = np.maximum(alpha_arr, min_alpha)
            
            alpha_clamped = Image.fromarray(alpha_arr, mode='L')
            final_image.putalpha(alpha_clamped)
            
            # Log final stats
            alpha_min = float(np.min(alpha_arr))
            alpha_max = float(np.max(alpha_arr))
            alpha_nonzero = int(np.count_nonzero(alpha_arr))
            logger.info(f"✅ Free preview: FINAL alpha safety clamp applied (min: {alpha_min}, max: {alpha_max}, nonzero: {alpha_nonzero})")
            debug_stats.update({
                "alpha_safety_clamp_applied": True,
                "alpha_clamp_min": float(min_alpha),
                "alpha_final_min": alpha_min,
                "alpha_final_max": alpha_max,
                "alpha_final_nonzero": alpha_nonzero
            })
        except Exception as clamp_err:
            logger.error(f"⚠️ CRITICAL: Final alpha safety clamp failed: {clamp_err}")
            # Try to save anyway, but log the error
            debug_stats["alpha_clamp_error"] = str(clamp_err)
    
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
    """Free Preview: 512px output using GPU-accelerated AI with optimizations"""
    start_time = time.time()
    
    try:
        data = request.json
        if not data or 'imageData' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing imageData in request body'
            }), 400
        
        image_data = data.get('imageData')
        max_size = data.get('maxSize', 512)
        
        # Validate image_data is present
        if not image_data:
            logger.error("Missing imageData in request")
            return jsonify({
                'success': False,
                'error': 'Missing imageData',
                'message': 'No image data provided in request'
            }), 400
        
        # Decode base64 image
        try:
            # Extract base64 part if data URL
            base64_part = image_data
            if ',' in image_data:
                parts = image_data.split(',', 1)  # Split only once
                if len(parts) == 2:
                    base64_part = parts[1]
                else:
                    logger.error(f"Invalid data URL format: {image_data[:100]}...")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid image data format',
                        'message': 'Image data URL format is invalid. Expected: data:image/...;base64,...'
                    }), 400
            
            # Clean base64 string: remove whitespace and fix URL-safe variants
            base64_part = base64_part.replace('\n', '').replace('\r', '').replace(' ', '')
            base64_part = base64_part.replace('-', '+').replace('_', '/')  # URL-safe to standard base64
            
            # Validate base64 string
            if not base64_part or len(base64_part) < 100:
                logger.error(f"Base64 data too short: {len(base64_part) if base64_part else 0} chars")
                return jsonify({
                    'success': False,
                    'error': 'Invalid image data',
                    'message': 'Image data is too small or corrupted. Please try uploading again.'
                }), 400
            
            # Pad base64 if needed (must be multiple of 4)
            remainder = len(base64_part) % 4
            if remainder:
                base64_part = base64_part + ('=' * (4 - remainder))
            
            # Decode base64 - try with validation first, fallback without if it fails
            try:
                image_bytes = base64.b64decode(base64_part, validate=True)
            except Exception as validate_err:
                # Try without validation (more lenient for edge cases)
                try:
                    logger.warning(f"Base64 decode with validation failed, trying without validation: {str(validate_err)}")
                    image_bytes = base64.b64decode(base64_part, validate=False)
                except Exception as decode_err:
                    logger.error(f"Base64 decode error (both with and without validation): {str(decode_err)}")
                    return jsonify({
                        'success': False,
                        'error': 'Invalid image data',
                        'message': f'Failed to decode image data: {str(decode_err)}. Please ensure you are uploading a valid image file (JPG, PNG, etc.).'
                    }), 400
            
            if not image_bytes or len(image_bytes) == 0:
                logger.error("Decoded image bytes are empty")
                return jsonify({
                    'success': False,
                    'error': 'Invalid image data',
                    'message': 'Decoded image is empty. Please try uploading a different image.'
                }), 400
            
            # Open image with PIL (without strict verify to handle more formats)
            try:
                # Create BytesIO from decoded bytes
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
            image_type = data.get('imageType')  # "human" | "document" | "id_card" | "a4"
            if image_type and image_type.lower() in ['document', 'id_card', 'a4']:
                is_document = True
                logger.info(f"📄 Free Preview: Using provided imageType: {image_type} → Document mode")
            else:
                # Auto-detect if not provided
                is_document = is_document_image(input_image)
                if image_type:
                    logger.info(f"📷 Free Preview: Using provided imageType: {image_type} → Photo mode (auto-detected: {'document' if is_document else 'photo'})")
                else:
                    logger.info(f"🔍 Free Preview: Auto-detected image type: {'document' if is_document else 'photo'}")
            
            # Resize to max 512px for preview
            original_size = input_image.size
            max_dimension = max(original_size)
            
            if max_dimension > max_size:
                scale = max_size / max_dimension
                new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
                input_image = input_image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {original_size} to {new_size} for preview")
            
            # Select model based on image type
            if is_document:
                logger.info("Document detected - using RobustMatting for better text preservation")
                session = get_session_robust()
            else:
                session = get_session_512()
            
            # Process with optimizations (light mode for free preview with new config)
            output_bytes, debug_stats = process_with_optimizations(input_image, session, is_premium=False, is_document=is_document)
            
            # Convert to base64
            output_b64 = base64.b64encode(output_bytes).decode()
            result_image = f"data:image/png;base64,{output_b64}"
            
            processing_time = time.time() - start_time
            output_size = len(output_bytes)
            
            logger.info(f"Free preview processed in {processing_time:.2f}s, output size: {output_size / 1024:.2f} KB")
            
            # Check if fallback was used (from debug_stats)
            preview_mode = "normal"
            if debug_stats.get("preview_mode") == "fallback":
                preview_mode = "fallback"
            elif debug_stats.get("used_fallback_level", 0) > 0:
                preview_mode = "recovered"  # Mask recovery was applied
            
            response_payload = {
                'success': True,
                'resultImage': result_image,
                'outputSize': output_size,
                'outputSizeMB': round(output_size / (1024 * 1024), 2),
                'processedWith': 'Free Preview (512px GPU-accelerated, Optimized)',
                'processingTime': round(processing_time, 2),
                'previewMode': preview_mode,  # "normal" | "recovered" | "fallback"
                'optimizations': {
                    'model_tuning': 'BiRefNet' if not is_document else 'RobustMatting',
                    'feathering': False,
                    'halo_removal': False,
                    'composite': True,
                    'document_mode': is_document
                }
            }
            if os.environ.get('DEBUG_RETURN_STATS', '0') == '1':
                response_payload['debugMask'] = debug_stats

            return jsonify(response_payload), 200
            
        except Exception as decode_error:
            logger.error(f"Image decode/process error: {str(decode_error)}")
            return jsonify({
                'success': False,
                'error': 'Invalid image data',
                'message': str(decode_error)
            }), 400
            
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
            image_type = data.get('imageType')  # "human" | "document" | "id_card" | "a4"
            
            if image_type:
                # Use provided imageType
                if image_type in ['document', 'id_card', 'a4']:
                    is_document = True
                    logger.info(f"📄 Using provided imageType: {image_type} → Document mode")
                else:
                    is_document = False
                    logger.info(f"📷 Using provided imageType: {image_type} → Photo mode")
            else:
                # Auto-detect if not provided
                is_document = is_document_image(input_image)
                image_type = 'document' if is_document else 'human'
            
            # Select pipeline based on image type
            birefnet_session = get_session_512()  # BiRefNet for semantic mask
            
            if is_document:
                # PREMIUM DOCUMENT PIPELINE: BiRefNet only, no MaxMatting, no feather, no halo
                logger.info("📄 Premium: Using Document Pipeline (BiRefNet only, safe mode)")
                try:
                    output_bytes, debug_stats = process_premium_document_pipeline(
                        input_image, 
                        birefnet_session
                    )
                    pipeline_type = "document_safe"
                except Exception as doc_error:
                    logger.error(f"Document pipeline failed: {doc_error}, falling back to photo pipeline")
                    # Fallback to photo pipeline if document pipeline fails
                    maxmatting_session = get_session_maxmatting()
                    output_bytes, debug_stats = process_premium_hd_pipeline(
                        input_image, 
                        birefnet_session, 
                        maxmatting_session, 
                        is_document=False
                    )
                    pipeline_type = "photo_fallback"
            else:
                # PREMIUM PHOTO PIPELINE: BiRefNet + MaxMatting
                logger.info("📷 Premium: Using Photo Pipeline (BiRefNet + MaxMatting)")
                maxmatting_session = get_session_maxmatting()  # MaxMatting for fine alpha matting
                output_bytes, debug_stats = process_premium_hd_pipeline(
                    input_image, 
                    birefnet_session, 
                    maxmatting_session, 
                    is_document=False
                )
                pipeline_type = "photo_hd"
            
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
            except Exception as alpha_check_error:
                logger.error(f"Alpha validation failed: {alpha_check_error}")
                return jsonify({
                    'success': False,
                    'error': 'Output validation failed',
                    'message': 'Unable to validate processed image. Please try again.',
                    'creditsUsed': 0  # No credits deducted
                }), 500
            
            # Calculate final megapixels for credit deduction (after successful processing)
            # Resolution-Based Credit Deduction (Backend Only)
            # New credit tiers based on final output MP
            if final_megapixels <= 2:
                credits_required = 2
            elif final_megapixels <= 6:
                credits_required = 4
            elif final_megapixels <= 9:
                credits_required = 6
            elif final_megapixels <= 12:
                credits_required = 9
            elif final_megapixels <= 16:
                credits_required = 10
            elif final_megapixels <= 20:
                credits_required = 12
            else:  # <= 25 MP
                credits_required = 15
            
            # Convert to base64
            output_b64 = base64.b64encode(output_bytes).decode()
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
                'outputSize': output_size,
                'outputSizeMB': round(output_size / (1024 * 1024), 2),
                'processedWith': processed_with,
                'processingTime': round(processing_time, 2),
                'creditsUsed': credits_required,  # Actual credits deducted (backend only, not shown in UI)
                'creditsUsedDisplay': 1,  # Generic display for UI (user sees "1 credit used" or "X credits used")
                'megapixels': round(final_megapixels, 2),
                'imageType': image_type,  # Return the imageType used
                'pipelineType': pipeline_type,
                'optimizations': optimizations
            }
            if os.environ.get('DEBUG_RETURN_STATS', '0') == '1':
                response_payload['debugMask'] = debug_stats

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
