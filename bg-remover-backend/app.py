# ============================================
# HIGH QUALITY AI BACKGROUND REMOVER
# Render Backend (Python + Simple Proxy)
# ============================================
# NOTE: Due to Render free tier limitations with rembg compilation,
# this backend serves as a placeholder/proxy.
# Main processing happens via browser (IMG.LY) which works great!
# ============================================

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import base64
import logging
import os
import traceback

app = Flask(__name__)

# Enable CORS for all routes and origins
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"]
    }
})

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit
SUPPORTED_FORMATS = ['PNG', 'JPG', 'JPEG', 'WEBP', 'BMP']

@app.route('/', methods=['GET'])
def home():
    """API info endpoint"""
    return jsonify({
        'service': 'Background Remover API',
        'status': 'running',
        'version': '1.2',
        'tier': 'Render Free (Proxy Mode)',
        'note': 'Processing happens via browser (IMG.LY) due to Render free tier compilation limits',
        'max_file_size_mb': 50,
        'supported_formats': SUPPORTED_FORMATS,
        'recommendation': 'Use browser processing (0-25 MB works great!)',
        'endpoints': {
            'POST /remove-background': 'Placeholder - redirects to browser processing',
            'GET /health': 'Health check'
        }
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'tier': 'render-proxy',
        'service': 'background-remover'
    }), 200

@app.route('/remove-background', methods=['POST', 'OPTIONS'])
def remove_background():
    """Main endpoint: Remove background from image"""
    
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        logger.info("📥 Received background removal request")
        
        # Check if image data provided
        if 'image' not in request.files and not request.is_json:
            logger.error("❌ No image provided in request")
            return jsonify({'error': 'No image provided. Send file or JSON with imageData'}), 400

        # === OPTION 1: Handle multipart file upload ===
        if 'image' in request.files:
            file = request.files['image']
            
            # Validate file
            if not file or file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                logger.warning(f"⚠️ File too large: {size_mb:.2f} MB")
                return jsonify({'error': f'File too large ({size_mb:.1f} MB). Maximum: 50 MB'}), 400
            
            logger.info(f"📁 Processing uploaded file: {file.filename}, Size: {file_size / (1024*1024):.2f} MB")
            
            # Read image
            try:
                input_image = Image.open(file.stream)
            except Exception as e:
                logger.error(f"❌ Invalid image file: {str(e)}")
                return jsonify({'error': 'Invalid image file. Please upload PNG, JPG, or WEBP'}), 400
            
        # === OPTION 2: Handle JSON base64 imageData ===
        else:
            data = request.get_json()
            image_data = data.get('imageData', '')
            
            if not image_data:
                return jsonify({'error': 'No imageData provided in JSON'}), 400
            
            # Remove data URL prefix if present (data:image/png;base64,...)
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            
            # Decode base64
            try:
                image_bytes = base64.b64decode(image_data)
            except Exception as e:
                logger.error(f"❌ Base64 decode failed: {str(e)}")
                return jsonify({'error': 'Invalid base64 image data'}), 400
            
            # Check size
            if len(image_bytes) > MAX_FILE_SIZE:
                size_mb = len(image_bytes) / (1024 * 1024)
                logger.warning(f"⚠️ Image data too large: {size_mb:.2f} MB")
                return jsonify({'error': f'Image too large ({size_mb:.1f} MB). Maximum: 50 MB'}), 400
            
            logger.info(f"📊 Processing base64 image, Size: {len(image_bytes) / (1024*1024):.2f} MB")
            
            # Create PIL Image from bytes
            try:
                input_image = Image.open(io.BytesIO(image_bytes))
            except Exception as e:
                logger.error(f"❌ Invalid image data: {str(e)}")
                return jsonify({'error': 'Invalid image data. Cannot parse as image'}), 400

        # === IMAGE PREPROCESSING ===
        original_size = input_image.size
        original_mode = input_image.mode
        logger.info(f"🖼️ Image info: {original_size[0]}x{original_size[1]}, Mode: {original_mode}")
        
        # Convert to RGB/RGBA for processing
        if input_image.mode not in ('RGB', 'RGBA'):
            logger.info(f"🔄 Converting from {input_image.mode} to RGB")
            input_image = input_image.convert('RGB')

@app.route('/remove-background', methods=['POST', 'OPTIONS'])
def remove_background():
    """Placeholder endpoint - recommends browser processing"""
    
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        logger.info("📥 Received background removal request")
        
        # Return recommendation to use browser processing
        return jsonify({
            'success': False,
            'error': 'Server processing temporarily unavailable',
            'message': 'Please use browser processing (works great for files up to 25 MB!)',
            'recommendation': 'Your browser can process this image instantly with high quality',
            'fallback': 'browser',
            'tier': 'render-proxy'
        }), 503  # Service Unavailable - triggers frontend fallback

    except Exception as e:
        logger.error(f"💥 Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'fallback': 'browser'
        }), 500


# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Starting Background Remover API (Proxy Mode) on port {port}")
    logger.info(f"📊 Recommendation: Use browser processing for best results")
    logger.info(f"🎨 Browser can handle 0-25 MB files with IMG.LY")
    app.run(host='0.0.0.0', port=port, debug=False)
