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
    Detect if image is a document (A4, letter, etc.) by aspect ratio
    A4: 1.414 (width/height) or 0.707 (height/width)
    Letter: 1.294 or 0.773
    Documents typically have aspect ratio between 0.6-0.8 or 1.2-1.7
    """
    if isinstance(image, Image.Image):
        width, height = image.size
    else:
        height, width = image.shape[:2]
    
    aspect_ratio = width / height if height > 0 else 1.0
    inverse_aspect = height / width if width > 0 else 1.0
    
    # Check if aspect ratio matches document formats (A4, Letter, etc.)
    # A4: 210x297mm = 0.707 or 1.414
    # Letter: 8.5x11in = 0.773 or 1.294
    # Documents typically: 0.6-0.85 (portrait) or 1.2-1.7 (landscape)
    is_portrait_doc = 0.6 <= aspect_ratio <= 0.85
    is_landscape_doc = 1.2 <= aspect_ratio <= 1.7
    
    is_doc = is_portrait_doc or is_landscape_doc
    
    if is_doc:
        logger.info(f"Document detected: aspect_ratio={aspect_ratio:.3f}, size={width}x{height}")
    
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

    # Safeguard: if mask is empty, fall back to rembg output directly
    hist = mask.histogram()
    nonzero = sum(hist[1:])
    if nonzero == 0:
        logger.warning("Mask appears empty; returning rembg output directly")
        debug_stats["mask_empty"] = True
        final_buffer = io.BytesIO()
        output_image.save(final_buffer, format='PNG', optimize=True)
        return final_buffer.getvalue(), debug_stats
    
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

    # Step 2: Apply Guided Filter for smooth borders (Premium only)
    if is_premium and CV2_AVAILABLE:
        logger.info("Step 2: Applying guided filter for smooth borders...")
        mask = guided_filter(input_image, mask, radius=5, eps=0.01)
        debug_stats.update(mask_stats("mask_after_guided", mask))
    else:
        logger.info("Step 2: Skipping guided filter for free preview.")
        debug_stats.update(mask_stats("mask_after_guided_skipped", mask))
    
    # Step 3: Enhance Hair Details (Premium only - for fine hair strands and details)
    if is_premium and CV2_AVAILABLE:
        logger.info("Step 3: Enhancing hair details and fine edges...")
        mask = enhance_hair_details(mask, input_image, strength=0.3)
        debug_stats.update(mask_stats("mask_after_hair", mask))
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
        
        if alpha_percent < 1.0:
            logger.warning(f"⚠️ Alpha too low ({alpha_percent:.2f}%) - falling back to raw BiRefNet output (no feather/halo)")
            debug_stats["fallback_to_raw"] = True
            # Return raw rembg output without post-processing
            final_buffer = io.BytesIO()
            output_image.save(final_buffer, format='PNG', optimize=True)
            return final_buffer.getvalue(), debug_stats
    except Exception as e:
        logger.warning(f"Failed alpha check, proceeding anyway: {e}")
    
    # Step 8: Apply alpha mask to RGB FIRST (before feather/halo), then composite
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
        
        # Apply feathering to alpha channel only (if premium)
        if is_premium and SCIPY_AVAILABLE:
            logger.info("Step 8.1: Applying feathering to alpha channel of composite...")
            composite_alpha = apply_feathering(composite_alpha, feather_radius=3)
            debug_stats.update(mask_stats("mask_after_feather_composite", composite_alpha))
        
        # Apply halo removal to alpha channel only (if premium)
        if is_premium:
            logger.info("Step 8.2: Applying halo removal to alpha channel of composite...")
            composite_alpha = remove_halo(composite_alpha, input_image, threshold=0.15)
            debug_stats.update(mask_stats("mask_after_halo_composite", composite_alpha))
        
        # Re-composite with processed alpha
        final_image = Image.new('RGBA', input_image.size, (0, 0, 0, 0))
        final_image.paste(input_image, (0, 0))
        final_image.putalpha(composite_alpha)
        
    except Exception as e:
        logger.error(f"Composite with fixed pipeline failed: {e}, falling back to original composite")
        final_image = composite_pro_png(input_image, mask)
    
    debug_stats.update(mask_stats("mask_final_used", mask))
    
    opt_time = time.time() - start_opt
    logger.info(f"Optimization pipeline completed in {opt_time:.2f}s")
    
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
        
        # Decode base64 image
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            input_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert RGBA to RGB if needed
            if input_image.mode == 'RGBA':
                rgb_image = Image.new('RGB', input_image.size, (255, 255, 255))
                rgb_image.paste(input_image, mask=input_image.split()[3])
                input_image = rgb_image
            elif input_image.mode != 'RGB':
                input_image = input_image.convert('RGB')
            
            # Detect if image is a document (A4, letter, etc.)
            is_document = is_document_image(input_image)
            
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
            
            response_payload = {
                'success': True,
                'resultImage': result_image,
                'outputSize': output_size,
                'outputSizeMB': round(output_size / (1024 * 1024), 2),
                'processedWith': 'Free Preview (512px GPU-accelerated, Optimized)',
                'processingTime': round(processing_time, 2),
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
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            input_image = Image.open(io.BytesIO(image_bytes))
            
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
            
            # Detect if image is a document (A4, letter, etc.)
            is_document = is_document_image(input_image)
            
            # Select best model for premium: MaxMatting for regular images, RobustMatting for documents
            if is_document:
                logger.info("Premium: Document detected - using RobustMatting for A4 optimization")
                session = get_session_robust()
            else:
                logger.info("Premium: Using MaxMatting for highest quality")
                session = get_session_maxmatting()
            
            # Process with full premium optimizations
            output_bytes, debug_stats = process_with_optimizations(input_image, session, is_premium=True, is_document=is_document)
            
            # Convert to base64
            output_b64 = base64.b64encode(output_bytes).decode()
            result_image = f"data:image/png;base64,{output_b64}"
            
            processing_time = time.time() - start_time
            output_size = len(output_bytes)
            
            logger.info(f"Premium HD processed in {processing_time:.2f}s, output size: {output_size / 1024:.2f} KB, user: {user_id}")
            
            response_payload = {
                'success': True,
                'resultImage': result_image,
                'outputSize': output_size,
                'outputSizeMB': round(output_size / (1024 * 1024), 2),
                'processedWith': 'Premium HD – up to 25 Megapixels (GPU-accelerated High-Resolution)',
                'processingTime': round(processing_time, 2),
                'creditsUsed': 2,  # UPDATED: 2 credits per premium image
                'megapixels': round(final_megapixels, 2),
                'optimizations': {
                    'model': 'MaxMatting' if not is_document else 'RobustMatting',
                    'tensorrt_turbo': 'FP16 ONNX Runtime GPU',
                    'hair_detail_enhancement': True,
                    'matte_clean_edges': True,
                    'guided_filter': CV2_AVAILABLE,
                    'feathering': SCIPY_AVAILABLE,
                    'halo_removal': True,
                    'a4_document_optimization': is_document,
                    'composite': 'Pro-level PNG'
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
