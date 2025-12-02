# ============================================
# HIGH QUALITY AI BACKGROUND REMOVER V2
# Alternative Implementation (No onnxruntime)
# Uses PIL + scikit-image for background removal
# ============================================

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageFilter, ImageEnhance
import io
import base64
import logging
import os
import gc
import traceback
import time
from datetime import datetime, timedelta
import numpy as np
from skimage import segmentation, filters, morphology
from scipy import ndimage

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
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Max-Age'] = '3600'
    response.headers['Access-Control-Allow-Credentials'] = 'false'
    return response

@app.after_request
def after_request(response):
    return add_cors_headers(response)

# Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_DIMENSION = 4096
SUPPORTED_FORMATS = ['PNG', 'JPG', 'JPEG', 'WEBP', 'BMP', 'TIFF']

# User limit configuration
USER_LIMITS = {
    'free': {'daily': 10, 'monthly': 100},
    'premium': {'daily': 1000, 'monthly': 10000}
}

# In-memory usage tracking
usage_tracker = {}

def remove_background_pil(image):
    """
    Remove background using PIL and scikit-image
    Uses edge detection and color-based segmentation
    """
    try:
        # Convert to numpy array
        img_array = np.array(image.convert('RGB'))
        
        # Create a mask using edge detection and color analysis
        # Method 1: Use grabcut-like algorithm with scikit-image
        gray = np.array(image.convert('L'))
        
        # Edge detection
        edges = filters.sobel(gray)
        
        # Threshold to create initial mask
        threshold = filters.threshold_otsu(gray)
        mask = gray > threshold
        
        # Clean up mask with morphological operations
        mask = morphology.binary_closing(mask, morphology.disk(3))
        mask = morphology.binary_opening(mask, morphology.disk(2))
        
        # Remove small objects
        mask = morphology.remove_small_objects(mask, min_size=100)
        mask = morphology.remove_small_holes(mask, area_threshold=100)
        
        # Smooth edges
        mask = ndimage.gaussian_filter(mask.astype(float), sigma=1) > 0.5
        
        # Create RGBA image
        rgba = np.zeros((img_array.shape[0], img_array.shape[1], 4), dtype=np.uint8)
        rgba[:, :, :3] = img_array
        rgba[:, :, 3] = (mask * 255).astype(np.uint8)
        
        # Convert back to PIL Image
        result = Image.fromarray(rgba, 'RGBA')
        
        return result
        
    except Exception as e:
        logger.error(f"Error in PIL background removal: {str(e)}")
        raise

def check_user_limit(user_id, user_type='free'):
    """Check if user has exceeded limits"""
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    if user_id not in usage_tracker:
        usage_tracker[user_id] = {'daily': {}, 'monthly': {}}
    
    user_usage = usage_tracker[user_id]
    limits = USER_LIMITS.get(user_type, USER_LIMITS['free'])
    
    # Check daily limit
    daily_count = user_usage['daily'].get(str(today), 0)
    if daily_count >= limits['daily']:
        return False, f"Daily limit of {limits['daily']} images reached"
    
    # Check monthly limit
    monthly_count = sum(
        count for date_str, count in user_usage['monthly'].items()
        if datetime.fromisoformat(date_str).date() >= month_start
    )
    if monthly_count >= limits['monthly']:
        return False, f"Monthly limit of {limits['monthly']} images reached"
    
    return True, None

def track_usage(user_id):
    """Track user usage"""
    today = datetime.now().date()
    today_str = str(today)
    
    if user_id not in usage_tracker:
        usage_tracker[user_id] = {'daily': {}, 'monthly': {}}
    
    user_usage = usage_tracker[user_id]
    user_usage['daily'][today_str] = user_usage['daily'].get(today_str, 0) + 1
    user_usage['monthly'][today_str] = user_usage['monthly'].get(today_str, 0) + 1

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'Background Remover API V2 (Alternative - No onnxruntime)',
        'status': 'running',
        'method': 'PIL + scikit-image',
        'version': '2.0.0-alt',
        'features': ['High Quality', 'No onnxruntime', 'User Limits', 'Large File Support']
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Background Remover API V2 (Alternative)',
        'method': 'PIL + scikit-image',
        'onnxruntime_required': False
    }), 200

@app.route('/remove-background', methods=['POST'])
def remove_background():
    """Main background removal endpoint"""
    start_time = time.time()
    
    try:
        # Get user info
        user_id = request.headers.get('X-User-ID', 'anonymous')
        user_type = request.headers.get('X-User-Type', 'free')
        
        # Check user limits
        can_process, limit_message = check_user_limit(user_id, user_type)
        if not can_process:
            return jsonify({
                'success': False,
                'error': 'Limit exceeded',
                'message': limit_message
            }), 429
        
        # Get JSON data
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must be JSON with imageData field'
            }), 400
        
        data = request.get_json()
        image_data = data.get('imageData')
        
        if not image_data:
            return jsonify({
                'success': False,
                'error': 'Missing image data',
                'message': 'imageData field is required'
            }), 400
        
        # Extract base64 data
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Invalid image data',
                'message': 'Failed to decode base64 image data'
            }), 400
        
        # Validate file size
        if len(image_bytes) > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': 'File too large',
                'message': f'File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f} MB limit'
            }), 400
        
        # Load image
        try:
            input_image = Image.open(io.BytesIO(image_bytes))
            input_image = input_image.convert('RGB')
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Invalid image',
                'message': 'Failed to load image. Please ensure it is a valid image file.'
            }), 400
        
        # Validate dimensions
        width, height = input_image.size
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            return jsonify({
                'success': False,
                'error': 'Image too large',
                'message': f'Image dimensions exceed {MAX_DIMENSION}x{MAX_DIMENSION} pixels'
            }), 400
        
        logger.info(f"Processing image: {width}x{height}, Size: {len(image_bytes) / (1024*1024):.2f} MB")
        
        # Process image with alternative method
        logger.info("Starting background removal with PIL + scikit-image...")
        output_image = remove_background_pil(input_image)
        
        # Ensure RGBA
        if output_image.mode != 'RGBA':
            output_image = output_image.convert('RGBA')
        
        # Save to bytes
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format='PNG', optimize=True)
        output_bytes = output_buffer.getvalue()
        
        # Convert to base64
        output_base64 = base64.b64encode(output_bytes).decode('utf-8')
        output_data_url = f"data:image/png;base64,{output_base64}"
        
        # Track usage
        track_usage(user_id)
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Processing completed in {processing_time:.2f}s")
        
        return jsonify({
            'success': True,
            'resultImage': output_data_url,
            'processedWith': 'pil-scikit-image',
            'processingTime': round(processing_time, 2),
            'originalSize': {'width': width, 'height': height},
            'outputSize': len(output_bytes)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error during processing: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        gc.collect()
        
        error_message = str(e)
        if 'cold' in error_message.lower() or '503' in error_message or 'unavailable' in error_message.lower():
            error_message = 'Service is temporarily unavailable. Please wait 15-20 seconds and try again.'
        
        return jsonify({
            'success': False,
            'error': 'Processing failed',
            'message': error_message
        }), 500

@app.route('/usage', methods=['GET'])
def get_usage():
    """Get usage statistics for a user"""
    user_id = request.headers.get('X-User-ID', 'anonymous')
    user_type = request.headers.get('X-User-Type', 'free')
    
    limits = USER_LIMITS.get(user_type, USER_LIMITS['free'])
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    if user_id not in usage_tracker:
        return jsonify({
            'daily': 0,
            'monthly': 0,
            'dailyLimit': limits['daily'],
            'monthlyLimit': limits['monthly']
        }), 200
    
    user_usage = usage_tracker[user_id]
    daily_count = user_usage['daily'].get(str(today), 0)
    monthly_count = sum(
        count for date_str, count in user_usage['monthly'].items()
        if datetime.fromisoformat(date_str).date() >= month_start
    )
    
    return jsonify({
        'daily': daily_count,
        'monthly': monthly_count,
        'dailyLimit': limits['daily'],
        'monthlyLimit': limits['monthly']
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Starting Background Remover API V2 (Alternative) on port {port}")
    logger.info(f"📏 Max file size: {MAX_FILE_SIZE / (1024*1024):.0f} MB")
    logger.info(f"🖼️ Max dimension: {MAX_DIMENSION} pixels")
    logger.info(f"✅ Supported formats: {', '.join(SUPPORTED_FORMATS)}")
    logger.info(f"⚙️ Method: PIL + scikit-image (No onnxruntime)")
    
    app.run(host='0.0.0.0', port=port, debug=False)

