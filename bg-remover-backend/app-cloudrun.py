# ============================================
# HIGH QUALITY AI BACKGROUND REMOVER
# Google Cloud Run Backend (Premium Tier)
# ============================================
# Tier 3: Handles 50-100 MB files
# Free Tier: 2M requests/month (~ 6,000 large images)
# Model: U²-Net with Alpha Matting (highest quality)
# Output: PNG with transparency, optimized for large files
# Memory: 2 GB RAM, optimized garbage collection
# ============================================

from flask import Flask, request, jsonify
from flask_cors import CORS
from rembg import remove, new_session
from PIL import Image
import io
import base64
import logging
import os
import gc
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
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB for Cloud Run (premium)
MAX_DIMENSION = 4096  # Max pixels for processing (to manage memory)
SUPPORTED_FORMATS = ['PNG', 'JPG', 'JPEG', 'WEBP', 'BMP', 'TIFF']

MODEL_NAME = os.environ.get('REMBG_MODEL', 'u2net')
_rembg_session = None


def get_rembg_session():
    """Lazy-load and reuse a single rembg session to avoid duplicate model args."""
    global _rembg_session
    if _rembg_session is not None:
        return _rembg_session
    logger.info("🔄 Initializing rembg session with model %s", MODEL_NAME)
    try:
        _rembg_session = new_session(model_name=MODEL_NAME)
    except Exception as exc:
        logger.error("❌ Failed to initialize rembg session: %s", exc)
        raise
    return _rembg_session

@app.route('/', methods=['GET'])
def home():
    """API info endpoint"""
    return jsonify({
        'service': 'Background Remover API (Premium)',
        'status': 'running',
        'version': '2.0',
        'tier': 'Google Cloud Run',
        'powered_by': 'Rembg U²-Net + Alpha Matting',
        'model': MODEL_NAME,
        'model_auto_download': True,
        'max_file_size_mb': 100,
        'max_dimension': MAX_DIMENSION,
        'supported_formats': SUPPORTED_FORMATS,
        'features': [
            'U²-Net model (explicitly configured)',
            'Alpha matting for high quality edges',
            'Large file optimization (50-100 MB)',
            'Memory-optimized processing',
            'Auto image resizing for performance',
            'Anti over-cleaning thresholds optimized'
        ],
        'endpoints': {
            'POST /remove-background': 'Remove background from large images',
            'GET /health': 'Health check'
        }
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'tier': 'cloudrun',
        'service': 'background-remover-premium'
    }), 200

@app.route('/remove-background', methods=['POST', 'OPTIONS'])
def remove_background():
    """Main endpoint: Remove background with premium quality (alpha matting)"""
    
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        logger.info("📥 Received premium background removal request (Cloud Run)")
        
        # Clean up memory before processing
        gc.collect()
        
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
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                logger.warning(f"⚠️ File too large: {size_mb:.2f} MB")
                return jsonify({'error': f'File too large ({size_mb:.1f} MB). Maximum: 100 MB'}), 400
            
            logger.info(f"📁 Processing uploaded file: {file.filename}, Size: {file_size / (1024*1024):.2f} MB")
            
            # Read image
            try:
                input_image = Image.open(file.stream)
            except Exception as e:
                logger.error(f"❌ Invalid image file: {str(e)}")
                return jsonify({'error': 'Invalid image file. Please upload valid image format'}), 400
            
        # === OPTION 2: Handle JSON base64 imageData ===
        else:
            data = request.get_json()
            image_data = data.get('imageData', '')
            
            if not image_data:
                return jsonify({'error': 'No imageData provided in JSON'}), 400
            
            # Remove data URL prefix if present
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
                return jsonify({'error': f'Image too large ({size_mb:.1f} MB). Maximum: 100 MB'}), 400
            
            logger.info(f"📊 Processing base64 image, Size: {len(image_bytes) / (1024*1024):.2f} MB")
            
            # Create PIL Image from bytes
            try:
                input_image = Image.open(io.BytesIO(image_bytes))
            except Exception as e:
                logger.error(f"❌ Invalid image data: {str(e)}")
                return jsonify({'error': 'Invalid image data. Cannot parse as image'}), 400

        # === IMAGE OPTIMIZATION FOR LARGE FILES ===
        original_size = input_image.size
        original_mode = input_image.mode
        logger.info(f"🖼️ Original: {original_size[0]}x{original_size[1]}, Mode: {original_mode}")
        
        # Resize if too large (to manage memory)
        if max(input_image.size) > MAX_DIMENSION:
            ratio = MAX_DIMENSION / max(input_image.size)
            new_size = (int(input_image.size[0] * ratio), int(input_image.size[1] * ratio))
            logger.info(f"📐 Resizing from {original_size} to {new_size} for memory optimization")
            input_image = input_image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB/RGBA for processing
        if input_image.mode not in ('RGB', 'RGBA'):
            logger.info(f"🔄 Converting from {input_image.mode} to RGB")
            input_image = input_image.convert('RGB')

        # === PREMIUM BACKGROUND REMOVAL WITH U²-NET + ALPHA MATTING ===
        logger.info("🎨 Starting PREMIUM background removal with U²-Net + Alpha Matting (Maximum Quality)...")
        try:
            output_image = remove(
                input_image,
                session=get_rembg_session(),
                alpha_matting=True,              # Enable alpha matting for smooth edges
                alpha_matting_foreground_threshold=120,  # Optimized - keeps maximum foreground
                alpha_matting_background_threshold=10,   # Optimized - best foreground preservation
                alpha_matting_erode_size=3      # Minimal refinement (prevents over-cleaning)
            )
            logger.info("✅ Premium background removal completed!")
        except Exception as e:
            logger.error(f"❌ Rembg processing failed: {str(e)}")
            logger.error(traceback.format_exc())
            gc.collect()  # Clean memory on error
            return jsonify({'error': f'AI processing failed: {str(e)}'}), 500

        # Free input image memory
        del input_image
        gc.collect()

        # === OUTPUT OPTIMIZATION (FAST COMPRESSION + SPEED) ===
        logger.info("💾 Optimizing PNG output with fast compression...")
        output_buffer = io.BytesIO()
        
        output_image.save(
            output_buffer, 
            format='PNG', 
            optimize=False,
            compress_level=1
        )
        
        output_buffer.seek(0)

        # Get output size info
        output_size = len(output_buffer.getvalue())
        output_size_mb = output_size / (1024 * 1024)
        logger.info(f"📦 Output size: {output_size_mb:.2f} MB")

        # Convert to base64 for JSON response
        output_bytes = output_buffer.getvalue()
        output_base64 = base64.b64encode(output_bytes).decode('utf-8')
        output_data_url = f'data:image/png;base64,{output_base64}'

        # Free memory
        del output_image
        del output_bytes
        del output_buffer
        gc.collect()
        
        # === SUCCESS RESPONSE ===
        logger.info("🎉 Returning premium quality result")
        return jsonify({
            'success': True,
            'resultImage': output_data_url,
            'outputSize': output_size,
            'outputSizeMB': round(output_size_mb, 2),
            'originalSize': list(original_size),
            'processedWith': 'Rembg U²-Net + Alpha Matting (Google Cloud Run)',
            'model': MODEL_NAME,
            'message': 'Background removed with premium quality'
        }), 200

    except Exception as e:
        # Catch-all error handler
        logger.error(f"💥 Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        gc.collect()  # Clean memory on error
        return jsonify({
            'success': False,
            'error': f'Processing error: {str(e)}',
            'message': 'An unexpected error occurred during premium processing'
        }), 500


# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🚀 Starting Premium Background Remover API (Cloud Run) on port {port}")
    logger.info(f"📊 Max file size: {MAX_FILE_SIZE / (1024*1024):.0f} MB")
    logger.info(f"📐 Max dimension: {MAX_DIMENSION} pixels")
    logger.info(f"🎨 Supported formats: {', '.join(SUPPORTED_FORMATS)}")
    logger.info(f"✨ Features: Alpha Matting, Memory Optimization, Large File Support")
    app.run(host='0.0.0.0', port=port, debug=False)
