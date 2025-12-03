# ============================================
# PURE PYTORCH U2NET FULL MODEL BACKGROUND REMOVER
# Cloud Run Compatible (No ONNX, No rembg)
# Optimized for 8GB Memory, 2 CPU (U2Net Full requires more memory)
# With Device Tracking, Image Compression, and Enhanced Limits
# IMPROVED: Better quality with alpha matting and edge preservation
# U2Net Full Model - Better Quality than U2NetP
# ============================================

import base64
import io
import logging
import os
import gc
import datetime
import traceback
import hashlib
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageFilter
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import transforms
from scipy import ndimage
from scipy.ndimage import binary_erosion, binary_dilation, distance_transform_edt, median_filter

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CORS configuration
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": "*"}})

def add_cors_headers(response):
    """Add CORS headers to any response"""
    origin = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Authorization, X-Requested-With, X-User-ID, X-User-Type, X-Device-ID, X-Auth-Token'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Max-Age'] = '3600'
    response.headers['Access-Control-Allow-Credentials'] = 'false'
    return response

@app.after_request
def after_request(response):
    return add_cors_headers(response)

# Configuration
MAX_DIMENSION = 4096
SUPPORTED_FORMATS = ['PNG', 'JPG', 'JPEG', 'WEBP', 'BMP', 'TIFF']

# User limit configuration - Updated as per requirements
USER_LIMITS = {
    'free': {
        'images_per_month': float('inf'),
        'max_file_size': 50 * 1024 * 1024,
        'monthly_upload_limit': float('inf'),
        'monthly_download_limit': float('inf'),
        'download_compress_to': None,
        'requires_auth': False
    },
    'premium': {
        'images_per_month': float('inf'),
        'max_file_size': 50 * 1024 * 1024,
        'monthly_upload_limit': float('inf'),
        'monthly_download_limit': float('inf'),
        'download_compress_to': None,
        'requires_auth': True
    }
}

# In-memory usage tracking (key: device_id or user_id)
usage_tracker = {}

# Global model - initialized once
u2net_model = None
device = None
transform = None

# Import U2Net Full Model
from u2net_model import U2NET

def load_u2net_model():
    """Load U2Net Full model with pre-trained weights - Better Quality"""
    global u2net_model, device, transform
    
    if u2net_model is not None:
        return u2net_model
    
    try:
        logger.info("🎨 Loading PyTorch U2Net Full model (Better Quality)...")
        device = torch.device('cpu')  # Cloud Run doesn't support GPU
        logger.info(f"Using device: {device}")
        
        # Initialize U2Net Full model
        u2net_model = U2NET(in_ch=3, out_ch=1)
        u2net_model.eval()
        
        # Try to load pre-trained weights
        # In production, download from: https://github.com/xuebinqin/U-2-Net
        model_path = os.path.join(os.path.dirname(__file__), 'u2net.pth')
        
        if os.path.exists(model_path):
            logger.info(f"Loading weights from {model_path}")
            state_dict = torch.load(model_path, map_location=device)
            u2net_model.load_state_dict(state_dict, strict=False)
            logger.info("✅ Pre-trained weights loaded")
        else:
            logger.warning("⚠️ Pre-trained weights not found. Using random initialization.")
            logger.warning("⚠️ For best results, download u2net.pth from official repository")
            logger.warning("⚠️ URL: https://github.com/xuebinqin/U-2-Net/releases/download/v1.0/u2net.pth")
        
        u2net_model.to(device)
        logger.info("✅ U2Net Full model loaded successfully")
        
        # Image preprocessing transform - IMPROVED: Higher resolution, maintain aspect ratio
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        return u2net_model
        
    except Exception as e:
        logger.error(f"❌ Failed to load U2Net Full model: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def preprocess_image(image, target_size=512):
    """Preprocess PIL image for U2Net Full - FIXED: Optimal resolution for quality vs performance"""
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    original_size = image.size
    width, height = original_size
    
    # Adaptive target size - balanced for quality and detail preservation
    # U2Net Full works best at 512x512, higher can cause over-processing
    max_dim = max(width, height)
    if max_dim > 3000:
        target_size = 768  # Very large images
    elif max_dim > 1500:
        target_size = 512  # Standard - best balance
    else:
        target_size = 512  # Default - optimal for U2Net Full
    
    # U2Net requires square input - always create exact square for model compatibility
    # Resize to fit within target_size while maintaining aspect ratio
    scale = min(target_size / width, target_size / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Ensure even dimensions (required for pooling operations)
    new_width = new_width if new_width % 2 == 0 else new_width - 1
    new_height = new_height if new_height % 2 == 0 else new_height - 1
    
    # Resize with high-quality resampling (LANCZOS for best quality)
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Pad to exact target_size x target_size (square) - required by U2Net
    padded_image = Image.new('RGB', (target_size, target_size), (0, 0, 0))
    paste_x = (target_size - new_width) // 2
    paste_y = (target_size - new_height) // 2
    padded_image.paste(resized_image, (paste_x, paste_y))
    
    # Apply transform
    input_tensor = transform(padded_image).unsqueeze(0)
    return input_tensor, original_size, (new_width, new_height, paste_x, paste_y)

def postprocess_mask(mask_tensor, original_size, model_size):
    """Postprocess mask tensor to PIL Image - FIXED: Preserve all details, no over-cleaning"""
    # Convert tensor to numpy
    mask = mask_tensor.squeeze().cpu().numpy()
    
    # Remove padding - extract the actual image region
    if len(model_size) == 4:
        model_width, model_height, paste_x, paste_y = model_size
        # Extract the actual mask region (remove padding)
        mask = mask[paste_y:paste_y+model_height, paste_x:paste_x+model_width]
    else:
        # Fallback for old format
        model_width, model_height = model_size[:2]
        target_size = max(model_width, model_height, 512)
        if model_width < target_size or model_height < target_size:
            start_x = (target_size - model_width) // 2
            start_y = (target_size - model_height) // 2
            mask = mask[start_y:start_y+model_height, start_x:start_x+model_width]
    
    # Convert to uint8 - preserve original mask values from model
    # U2Net outputs probability (0-1), convert to 0-255
    mask = np.clip(mask * 255.0, 0, 255).astype(np.uint8)
    
    # MINIMAL processing - only very light smoothing to remove noise, preserve all details
    # No morphological operations - they remove fine details like hair strands
    # Very light gaussian filter only for minor noise reduction
    mask = ndimage.gaussian_filter(mask.astype(np.float32), sigma=0.3).astype(np.uint8)
    
    # Resize to original size with high-quality resampling
    mask_pil = Image.fromarray(mask, mode='L')
    mask_pil = mask_pil.resize(original_size, Image.LANCZOS)
    
    return mask_pil

def alpha_matting(image, mask, foreground_threshold=240, background_threshold=10, erode_size=10):
    """Apply alpha matting for better edge quality - FIXED: Proper mask application like rembg"""
    try:
        # Get mask array - U2Net outputs foreground probability (0-1, higher = foreground)
        mask_array = np.array(mask.convert('L')).astype(np.float32) / 255.0
        
        # Create binary mask with proper thresholding
        # U2Net mask: values > 0.5 are likely foreground
        binary_mask = (mask_array > 0.5).astype(np.uint8)
        
        # Create trimap for alpha matting (foreground, background, unknown)
        trimap = np.zeros_like(binary_mask, dtype=np.uint8)
        trimap[binary_mask == 1] = 255  # Definite foreground
        
        # Create unknown region around edges for better alpha matting
        structure = np.ones((erode_size, erode_size), dtype=np.uint8)
        eroded = binary_erosion(binary_mask, structure=structure, iterations=1)
        dilated = binary_dilation(binary_mask, structure=structure, iterations=1)
        unknown = dilated.astype(np.float32) - eroded.astype(np.float32)
        trimap[unknown > 0] = 128  # Unknown region (edges)
        
        # Calculate alpha using distance transform (like rembg)
        # Distance from foreground boundary
        dist_foreground = distance_transform_edt(1 - binary_mask)
        # Distance from background boundary  
        dist_background = distance_transform_edt(binary_mask)
        
        # Calculate alpha based on distances in unknown region
        total_dist = dist_foreground + dist_background
        alpha = np.zeros_like(total_dist, dtype=np.float32)
        mask_valid = total_dist > 0
        alpha[mask_valid] = dist_background[mask_valid] / total_dist[mask_valid]
        alpha = np.clip(alpha, 0, 1)
        
        # Preserve definite foreground and background
        alpha[binary_mask == 1] = 1.0  # Definite foreground = fully opaque
        alpha[binary_mask == 0] = 0.0  # Definite background = fully transparent
        
        # For unknown regions, use the original mask probability (preserve model confidence)
        # This ensures we don't lose fine details
        unknown_mask = (trimap == 128)
        alpha[unknown_mask] = mask_array[unknown_mask]  # Use original probability in edge regions
        
        # Enhanced edge refinement - better border cleanup
        # Apply stronger smoothing only in edge regions for cleaner borders
        edge_mask = (trimap == 128) | (trimap == 0)  # Unknown + background edges
        alpha_smooth = ndimage.gaussian_filter(alpha, sigma=0.8)
        # Blend: stronger smoothing in edge regions, preserve original in foreground
        alpha = np.where(edge_mask, alpha_smooth, alpha)
        
        # Additional edge sharpening for crisp borders
        # Use morphological operations to clean up edge artifacts
        # Apply median filter only to edge regions to remove noise
        alpha_median = median_filter(alpha, size=3)
        alpha = np.where(edge_mask, alpha_median, alpha)
        
        # Final light smoothing for natural transitions
        alpha = ndimage.gaussian_filter(alpha, sigma=0.3)
        
        # Ensure proper range
        alpha = np.clip(alpha, 0, 1)
        
        return (alpha * 255).astype(np.uint8)
    except Exception as e:
        logger.warning(f"Alpha matting failed, using simple mask: {e}")
        logger.warning(f"Traceback: {traceback.format_exc()}")
        # Fallback: use mask directly with proper thresholding
        mask_array = np.array(mask.convert('L'))
        # Ensure strong mask - threshold at 128
        mask_array = np.clip(mask_array, 0, 255)
        return mask_array.astype(np.uint8)

def remove_background_pytorch(image):
    """Remove background using PyTorch U2Net Full - IMPROVED: Higher resolution + better mask combination"""
    global u2net_model, device, transform
    
    start_time = time.time()
    
    if u2net_model is None:
        load_u2net_model()
    
    # Adaptive resolution based on image size for better quality
    original_size = image.size
    max_dim = max(original_size)
    
    # Preprocess with adaptive target size
    input_tensor, original_size, model_size = preprocess_image(image)
    input_tensor = input_tensor.to(device)
    
    # Run inference
    with torch.no_grad():
        raw_output = u2net_model(input_tensor)
        
        # U2Net Full returns a tuple of stage outputs (d0, d1..d6)
        # Use d0 (final output) - it's the best refined output from the model
        if isinstance(raw_output, (tuple, list)):
            if not raw_output:
                raise ValueError("Model returned no outputs")
            
            # Use d0 (final output) - it's already the best combination of all stages
            # Don't combine with d1 - it can cause over-cleaning
            mask_tensor = raw_output[0]
        else:
            mask_tensor = raw_output
        
        # Ensure tensor shape is valid before applying sigmoid
        if not torch.is_tensor(mask_tensor):
            raise TypeError(f"Unexpected mask output type: {type(mask_tensor)}")
        
        # Apply sigmoid to get probability mask
        mask_tensor = torch.sigmoid(mask_tensor)
    
    # Postprocess mask with better edge preservation
    mask_pil = postprocess_mask(mask_tensor, original_size, model_size)
    
    # Convert original image to RGBA
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Apply alpha matting for better edges (hair, fur, cloth)
    # Proper erode_size for good edge quality
    alpha_array = alpha_matting(image, mask_pil, foreground_threshold=240, background_threshold=10, erode_size=10)
    
    # Normalize alpha to 0-1 range
    alpha_array = alpha_array.astype(np.float32) / 255.0
    
    # Create output image with transparency - DIRECTLY set alpha channel (not multiply)
    # This ensures background is fully transparent where mask is 0
    output_array = np.array(image).astype(np.float32)
    
    # Directly set alpha channel to mask values
    # Where alpha = 0, background is transparent
    # Where alpha = 1, foreground is fully opaque
    output_array[:, :, 3] = (alpha_array * 255.0).astype(np.uint8)
    
    # Convert back to uint8
    output_array = output_array.astype(np.uint8)
    
    output_image = Image.fromarray(output_array, 'RGBA')
    
    processing_time = time.time() - start_time
    logger.info(f"✅ Background removal completed in {processing_time:.2f}s (resolution: {max(original_size)})")
    
    return output_image, processing_time

def compress_image(image, target_size_kb=150):
    """Compress RGBA image to target size in KB while keeping transparency."""
    target_size_bytes = target_size_kb * 1024
    work_image = image.convert("RGBA")

    def encode_png(img):
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer

    buf = encode_png(work_image)
    current_size = buf.tell()

    if current_size <= target_size_bytes:
        return buf.getvalue()

    # Gradually scale down until we are within target size (or hit minimum size)
    min_dimension = 256
    scale = 0.9
    width, height = work_image.size

    while current_size > target_size_bytes and (width > min_dimension or height > min_dimension):
        width = max(int(width * scale), min_dimension)
        height = max(int(height * scale), min_dimension)
        work_image = work_image.resize((width, height), Image.LANCZOS)
        buf = encode_png(work_image)
        current_size = buf.tell()
        scale = max(scale - 0.05, 0.6)

    return buf.getvalue()

def get_device_id(request):
    """Generate device ID from request headers and IP"""
    device_id_header = request.headers.get('X-Device-ID', '')
    user_agent = request.headers.get('User-Agent', '')
    ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    
    # Create device fingerprint
    fingerprint_data = f"{device_id_header}|{user_agent}|{ip_address}"
    device_id = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    return device_id

def get_tracking_id(user_id, user_type, device_id):
    """Get tracking ID - use device_id for free users, user_id for premium"""
    if user_type == 'premium':
        return user_id  # Premium users tracked by user_id
    else:
        return f"device_{device_id}"  # Free users tracked by device

def get_user_usage(tracking_id, user_type):
    """Get user usage statistics"""
    today = datetime.date.today().isoformat()
    this_month = datetime.date.today().strftime('%Y-%m')

    if tracking_id not in usage_tracker:
        usage_tracker[tracking_id] = {
            'image_count': 0,
            'upload_bytes': 0,
            'download_bytes': 0,
            'monthly_date': this_month,
            'last_reset': today
        }

    # Reset monthly if month changed
    if usage_tracker[tracking_id]['monthly_date'] != this_month:
        usage_tracker[tracking_id]['image_count'] = 0
        usage_tracker[tracking_id]['upload_bytes'] = 0
        usage_tracker[tracking_id]['download_bytes'] = 0
        usage_tracker[tracking_id]['monthly_date'] = this_month
        usage_tracker[tracking_id]['last_reset'] = today
    
    return usage_tracker[tracking_id]

def check_quota(tracking_id, user_type, file_size_bytes):
    """Unlimited quota (temporary override)"""
    limits = USER_LIMITS.get(user_type, USER_LIMITS['free'])
    if file_size_bytes > limits['max_file_size']:
        max_mb = limits['max_file_size'] / (1024 * 1024)
        return False, f"File size ({file_size_bytes / (1024*1024):.2f} MB) exceeds maximum allowed ({max_mb} MB)."
    return True, "Quota available."

def increment_usage(tracking_id, user_type, upload_bytes, download_bytes):
    """Increment user usage"""
    usage = get_user_usage(tracking_id, user_type)
    usage['image_count'] += 1
    usage['upload_bytes'] += upload_bytes
    usage['download_bytes'] += download_bytes

def verify_premium_auth(user_id, auth_token):
    """Verify premium user authentication"""
    # In production, verify with Firebase Auth or your auth system
    # For now, check if user_id is not 'anonymous' and auth_token is provided
    if user_id == 'anonymous' or not auth_token:
        return False
    # TODO: Implement actual Firebase Auth verification
    return True

def dataurl_to_image(dataurl):
    """Convert data URL to PIL Image"""
    header, b64 = dataurl.split(',', 1) if ',' in dataurl else (None, dataurl)
    data = base64.b64decode(b64)
    return Image.open(io.BytesIO(data)).convert("RGB"), len(data)

def image_to_dataurl(img, compress_to_kb=None):
    """Convert PIL Image to data URL, optionally compressed"""
    buf = io.BytesIO()
    
    if compress_to_kb:
        compressed_data = compress_image(img, compress_to_kb)
        b64 = base64.b64encode(compressed_data).decode('ascii')
        return f"data:image/png;base64,{b64}", len(compressed_data)
    else:
        # Save as PNG (high quality for premium)
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        return f"data:image/png;base64,{b64}", len(buf.getvalue())

@app.route("/", methods=["GET"])
def root():
    """Root endpoint"""
    logger.info("🩺 Root path requested.")
    model_loaded = u2net_model is not None
    return jsonify({
        "service": "Background Remover API (PyTorch U2Net Full)",
        "status": "running",
        "model": "u2net",
        "model_loaded": model_loaded,
        "device": str(device) if device else "not initialized"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    logger.info("🩺 Health check requested.")
    try:
        if u2net_model is None:
            load_u2net_model()
        logger.info("✅ Health check successful: PyTorch U2Net Full model loaded.")
        return jsonify({
            "status": "ok",
            "model": "u2net",
            "model_loaded": True,
            "device": str(device),
            "service": "Background Remover API (PyTorch U2Net Full)"
        }), 200
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": "Model initialization failed",
            "details": str(e),
            "service": "Background Remover API (PyTorch U2Net Full)"
        }), 500

@app.route('/usage', methods=['GET'])
def get_usage():
    """Get user usage statistics"""
    user_id = request.headers.get('X-User-ID', 'anonymous')
    user_type = request.headers.get('X-User-Type', 'free')
    device_id = get_device_id(request)
    tracking_id = get_tracking_id(user_id, user_type, device_id)
    
    usage = get_user_usage(tracking_id, user_type)
    limits = USER_LIMITS.get(user_type, USER_LIMITS['free'])
    
    return jsonify({
        "userId": user_id,
        "userType": user_type,
        "deviceId": device_id,
        "trackingId": tracking_id,
        "imageCount": usage['image_count'],
        "imageLimit": limits['images_per_month'] if limits['images_per_month'] != float('inf') else -1,
        "uploadBytes": usage['upload_bytes'],
        "uploadLimit": limits['monthly_upload_limit'],
        "downloadBytes": usage['download_bytes'],
        "downloadLimit": limits['monthly_download_limit'],
        "remainingUploadMB": (limits['monthly_upload_limit'] - usage['upload_bytes']) / (1024 * 1024),
        "remainingDownloadMB": (limits['monthly_download_limit'] - usage['download_bytes']) / (1024 * 1024)
    }), 200

@app.route("/remove-background", methods=["POST"])
def remove_bg():
    """Remove background from image"""
    start_time = time.time()
    user_id = request.headers.get('X-User-ID', 'anonymous')
    user_type = request.headers.get('X-User-Type', 'free')
    auth_token = request.headers.get('X-Auth-Token', '')
    device_id = get_device_id(request)
    tracking_id = get_tracking_id(user_id, user_type, device_id)
    
    # Check premium authentication
    limits = USER_LIMITS.get(user_type, USER_LIMITS['free'])
    if limits['requires_auth']:
        if not verify_premium_auth(user_id, auth_token):
            logger.warning(f"Premium user {user_id} not authenticated")
            return jsonify({
                "success": False, 
                "error": "Authentication Required", 
                "message": "Premium users must be logged in to use this service."
            }), 401

    try:
        payload = request.get_json(force=True)
        image_dataurl = payload.get("imageData")

        if not image_dataurl:
            return jsonify({"success": False, "error": "No imageData provided"}), 400

        # Decode image and get size
        img, file_size_bytes = dataurl_to_image(image_dataurl)
        
        # Check quota before processing
        quota_ok, quota_message = check_quota(tracking_id, user_type, file_size_bytes)
        if not quota_ok:
            logger.warning(f"Quota exceeded for {tracking_id} ({user_type}): {quota_message}")
            return jsonify({"success": False, "error": "Quota Exceeded", "message": quota_message}), 429
        
        if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
            logger.warning(f"Image dimensions ({img.width}x{img.height}) exceed max allowed ({MAX_DIMENSION}x{MAX_DIMENSION}).")
            return jsonify({"success": False, "error": "Image Too Large", "message": f"Image dimensions exceed {MAX_DIMENSION} pixels"}), 413

        # Load model if not loaded
        if u2net_model is None:
            load_u2net_model()
        
        logger.info(f"✨ Starting background removal with PyTorch U2Net Full for {tracking_id} ({user_type})...")
        logger.info(f"📏 Image size: {img.width}x{img.height}, File size: {file_size_bytes/(1024*1024):.2f} MB")
        
        # Process image (always high quality)
        result_img, processing_time = remove_background_pytorch(img)
        
        # Convert to data URL with compression for free users
        compress_to_kb = limits['download_compress_to']
        out_dataurl, download_size_bytes = image_to_dataurl(result_img, compress_to_kb=compress_to_kb)
        
        # Update usage
        increment_usage(tracking_id, user_type, file_size_bytes, download_size_bytes)
        total_time = time.time() - start_time
        logger.info(f"✅ Background removed successfully. Processing: {processing_time:.2f}s, Total: {total_time:.2f}s, Upload: {file_size_bytes/(1024*1024):.2f} MB, Download: {download_size_bytes/(1024*1024):.2f} MB")
        
        # Clean up memory
        gc.collect()
        if device and device.type == 'cuda':
            torch.cuda.empty_cache()

        return jsonify({
            "success": True, 
            "resultImage": out_dataurl, 
            "processedWith": "pytorch-u2net",
            "processingTime": round(processing_time, 2),
            "totalTime": round(total_time, 2),
            "uploadSizeMB": round(file_size_bytes / (1024 * 1024), 2),
            "downloadSizeMB": round(download_size_bytes / (1024 * 1024), 2),
            "compressed": compress_to_kb is not None
        }), 200

    except Exception as e:
        logger.error(f"❌ Error during image processing for {tracking_id}: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        gc.collect()
        return jsonify({"success": False, "error": "Internal Server Error", "message": str(e)}), 500

if __name__ == "__main__":
    # Initialize model on startup
    try:
        load_u2net_model()
    except Exception as e:
        logger.error(f"❌ Critical: Failed to initialize model: {str(e)}")
        logger.error("Service may not work properly")
    
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting Background Remover API (PyTorch U2Net Full) on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
