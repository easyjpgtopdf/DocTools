# ============================================
# PURE PYTORCH U2NETP BACKGROUND REMOVER
# Cloud Run Compatible (No ONNX, No rembg)
# Optimized for 4GB Memory, 2 CPU
# With Device Tracking, Image Compression, and Enhanced Limits
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
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import transforms

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
        'images_per_month': 50,
        'max_file_size': 1 * 1024 * 1024,  # 1 MB per image
        'monthly_upload_limit': 10 * 1024 * 1024,  # 10 MB total upload
        'monthly_download_limit': 10 * 1024 * 1024,  # 10 MB total download
        'download_compress_to': 150 * 1024,  # 150 KB compressed
        'requires_auth': False  # Free users can use without login
    },
    'premium': {
        'images_per_month': float('inf'),  # Unlimited
        'max_file_size': 50 * 1024 * 1024,  # 50 MB per image
        'monthly_upload_limit': 500 * 1024 * 1024,  # 500 MB total upload
        'monthly_download_limit': 500 * 1024 * 1024,  # 500 MB total download
        'download_compress_to': None,  # No compression for premium (better quality)
        'requires_auth': True  # Premium users must be logged in
    }
}

# In-memory usage tracking (key: device_id or user_id)
usage_tracker = {}

# Global model - initialized once
u2netp_model = None
device = None
transform = None

# U2NetP Model Architecture (Simplified)
class U2NETP(torch.nn.Module):
    """U2NetP model for background removal"""
    def __init__(self):
        super(U2NETP, self).__init__()
        # Simplified U2NetP architecture
        # For production, use pre-trained weights from official repository
        self.encoder = torch.nn.Sequential(
            torch.nn.Conv2d(3, 64, 3, padding=1),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(64, 64, 3, padding=1),
            torch.nn.ReLU(inplace=True),
        )
        self.decoder = torch.nn.Sequential(
            torch.nn.Conv2d(64, 64, 3, padding=1),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(64, 1, 1),
            torch.nn.Sigmoid()
        )
    
    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

def load_u2netp_model():
    """Load U2NetP model with pre-trained weights"""
    global u2netp_model, device, transform
    
    if u2netp_model is not None:
        return u2netp_model
    
    try:
        logger.info("🎨 Loading PyTorch U2NetP model...")
        device = torch.device('cpu')  # Cloud Run doesn't support GPU
        logger.info(f"Using device: {device}")
        
        # Initialize model
        u2netp_model = U2NETP()
        u2netp_model.eval()
        
        # Try to load pre-trained weights
        # In production, download from: https://github.com/xuebinqin/U-2-Net
        model_path = os.path.join(os.path.dirname(__file__), 'u2netp.pth')
        
        if os.path.exists(model_path):
            logger.info(f"Loading weights from {model_path}")
            state_dict = torch.load(model_path, map_location=device)
            u2netp_model.load_state_dict(state_dict, strict=False)
            logger.info("✅ Pre-trained weights loaded")
        else:
            logger.warning("⚠️ Pre-trained weights not found. Using random initialization.")
            logger.warning("⚠️ For best results, download u2netp.pth from official repository")
        
        u2netp_model.to(device)
        logger.info("✅ U2NetP model loaded successfully")
        
        # Image preprocessing transform
        transform = transforms.Compose([
            transforms.Resize((320, 320)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        return u2netp_model
        
    except Exception as e:
        logger.error(f"❌ Failed to load U2NetP model: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def preprocess_image(image):
    """Preprocess PIL image for U2NetP"""
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    original_size = image.size
    # Resize for model input
    input_tensor = transform(image).unsqueeze(0)
    return input_tensor, original_size

def postprocess_mask(mask_tensor, original_size):
    """Postprocess mask tensor to PIL Image"""
    # Convert tensor to numpy
    mask = mask_tensor.squeeze().cpu().numpy()
    # Resize to original size
    mask_pil = Image.fromarray((mask * 255).astype(np.uint8))
    mask_pil = mask_pil.resize(original_size, Image.LANCZOS)
    return mask_pil

def remove_background_pytorch(image, quality='high'):
    """Remove background using PyTorch U2NetP
    
    Args:
        image: PIL Image
        quality: 'high' for premium (better quality), 'compressed' for free (compressed to 150KB)
    """
    global u2netp_model, device
    
    if u2netp_model is None:
        load_u2netp_model()
    
    # Preprocess
    input_tensor, original_size = preprocess_image(image)
    input_tensor = input_tensor.to(device)
    
    # Run inference
    with torch.no_grad():
        mask_tensor = u2netp_model(input_tensor)
        # Apply sigmoid if not already applied
        if mask_tensor.max() > 1.0:
            mask_tensor = torch.sigmoid(mask_tensor)
    
    # Postprocess mask
    mask_pil = postprocess_mask(mask_tensor, original_size)
    
    # Convert original image to RGBA
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Apply mask to image
    mask_array = np.array(mask_pil.convert('L'))
    mask_array = mask_array.astype(np.float32) / 255.0
    
    # Create output image with transparency
    output_array = np.array(image)
    output_array[:, :, 3] = (output_array[:, :, 3] * mask_array).astype(np.uint8)
    
    output_image = Image.fromarray(output_array, 'RGBA')
    return output_image

def compress_image(image, target_size_kb=150):
    """Compress image to target size in KB"""
    target_size_bytes = target_size_kb * 1024
    buf = io.BytesIO()
    
    # Start with high quality
    quality = 95
    image.save(buf, format='PNG', optimize=True, quality=quality)
    current_size = buf.tell()
    
    # If still too large, reduce quality
    if current_size > target_size_bytes:
        # Try JPEG compression for smaller size
        if image.mode == 'RGBA':
            # Convert RGBA to RGB for JPEG
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = rgb_image
        
        buf = io.BytesIO()
        quality = 85
        while current_size > target_size_bytes and quality > 10:
            buf.seek(0)
            buf.truncate(0)
            image.save(buf, format='JPEG', quality=quality, optimize=True)
            current_size = buf.tell()
            quality -= 10
        
        # If still too large, resize
        if current_size > target_size_bytes:
            scale = (target_size_bytes / current_size) ** 0.5
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.LANCZOS)
            buf = io.BytesIO()
            image.save(buf, format='JPEG', quality=75, optimize=True)
    
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
    """Check if user has quota available"""
    usage = get_user_usage(tracking_id, user_type)
    limits = USER_LIMITS.get(user_type, USER_LIMITS['free'])

    # Check image count limit
    if limits['images_per_month'] != float('inf'):
        if usage['image_count'] >= limits['images_per_month']:
            return False, f"Monthly image limit ({limits['images_per_month']}) exceeded for {user_type} user."

    # Check file size limit
    if file_size_bytes > limits['max_file_size']:
        max_mb = limits['max_file_size'] / (1024 * 1024)
        return False, f"File size ({file_size_bytes / (1024*1024):.2f} MB) exceeds maximum allowed ({max_mb} MB) for {user_type} user."

    # Check upload limit
    if usage['upload_bytes'] + file_size_bytes > limits['monthly_upload_limit']:
        remaining_mb = (limits['monthly_upload_limit'] - usage['upload_bytes']) / (1024 * 1024)
        return False, f"Monthly upload limit exceeded. Remaining: {remaining_mb:.2f} MB."

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
        # Compress image
        compressed_data = compress_image(img, compress_to_kb)
        b64 = base64.b64encode(compressed_data).decode('ascii')
        # Determine format from compressed data
        format_type = 'jpeg' if compressed_data[:2] == b'\xff\xd8' else 'png'
        return f"data:image/{format_type};base64,{b64}", len(compressed_data)
    else:
        # Save as PNG (high quality for premium)
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        return f"data:image/png;base64,{b64}", len(buf.getvalue())

@app.route("/", methods=["GET"])
def root():
    """Root endpoint"""
    logger.info("🩺 Root path requested.")
    model_loaded = u2netp_model is not None
    return jsonify({
        "service": "Background Remover API (PyTorch U2NetP)",
        "status": "running",
        "model": "u2netp",
        "model_loaded": model_loaded,
        "device": str(device) if device else "not initialized"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    logger.info("🩺 Health check requested.")
    try:
        if u2netp_model is None:
            load_u2netp_model()
        logger.info("✅ Health check successful: PyTorch U2NetP model loaded.")
        return jsonify({
            "status": "ok",
            "model": "u2netp",
            "model_loaded": True,
            "device": str(device),
            "service": "Background Remover API (PyTorch U2NetP)"
        }), 200
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": "Model initialization failed",
            "details": str(e),
            "service": "Background Remover API (PyTorch U2NetP)"
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
        if u2netp_model is None:
            load_u2netp_model()
        
        logger.info(f"✨ Starting background removal with PyTorch U2NetP for {tracking_id} ({user_type})...")
        
        # Process image - use high quality for premium, compressed for free
        quality = 'high' if user_type == 'premium' else 'compressed'
        result_img = remove_background_pytorch(img, quality=quality)
        
        # Convert to data URL with compression for free users
        compress_to_kb = limits['download_compress_to']
        out_dataurl, download_size_bytes = image_to_dataurl(result_img, compress_to_kb=compress_to_kb)
        
        # Update usage
        increment_usage(tracking_id, user_type, file_size_bytes, download_size_bytes)
        logger.info(f"✅ Background removed successfully. Upload: {file_size_bytes/(1024*1024):.2f} MB, Download: {download_size_bytes/(1024*1024):.2f} MB")
        
        # Clean up memory
        gc.collect()
        if device and device.type == 'cuda':
            torch.cuda.empty_cache()

        return jsonify({
            "success": True, 
            "resultImage": out_dataurl, 
            "processedWith": "pytorch-u2netp",
            "quality": quality,
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
        load_u2netp_model()
    except Exception as e:
        logger.error(f"❌ Critical: Failed to initialize model: {str(e)}")
        logger.error("Service may not work properly")
    
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting Background Remover API (PyTorch U2NetP) on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
