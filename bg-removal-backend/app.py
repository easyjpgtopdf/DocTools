"""
Background Removal Service - AI-Powered GPU Processing
Google Cloud Run service for background removal using advanced AI models
"""

from flask import Flask, request, jsonify
from rembg import remove, new_session
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize AI model sessions (lazy loading)
session_512 = None
session_hd = None

def get_session_512():
    """Get or create 512px preview session"""
    global session_512
    if session_512 is None:
        logger.info("Initializing AI model session for 512px preview...")
        session_512 = new_session('birefnet')
        logger.info("AI model session initialized for 512px")
    return session_512

def get_session_hd():
    """Get or create HD session"""
    global session_hd
    if session_hd is None:
        logger.info("Initializing AI model session for HD processing...")
        session_hd = new_session('birefnet')
        logger.info("AI model session initialized for HD")
    return session_hd

# Watermark function removed - Free version now provides clear PNG without watermark

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'bg-removal-ai',
        'gpu': 'available',
        'model': 'ai-powered'
    }), 200

@app.route('/api/free-preview-bg', methods=['POST'])
def free_preview_bg():
    """Free Preview: 512px output using GPU-accelerated AI"""
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
                # Remove data URL prefix if present
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            input_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert RGBA to RGB if needed (rembg works better with RGB)
            if input_image.mode == 'RGBA':
                # Create white background
                rgb_image = Image.new('RGB', input_image.size, (255, 255, 255))
                rgb_image.paste(input_image, mask=input_image.split()[3])
                input_image = rgb_image
            elif input_image.mode != 'RGB':
                input_image = input_image.convert('RGB')
            
            # Resize to max 512px for preview (maintain aspect ratio)
            original_size = input_image.size
            max_dimension = max(original_size)
            
            if max_dimension > max_size:
                scale = max_size / max_dimension
                new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
                input_image = input_image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {original_size} to {new_size} for preview")
            
            # Remove background using AI model
            session = get_session_512()
            output_bytes = remove(input_image, session=session)
            
            # NO WATERMARK - Clear PNG output for free preview
            # Convert to base64
            output_b64 = base64.b64encode(output_bytes).decode()
            result_image = f"data:image/png;base64,{output_b64}"
            
            processing_time = time.time() - start_time
            output_size = len(output_bytes)
            
            logger.info(f"Free preview processed in {processing_time:.2f}s, output size: {output_size / 1024:.2f} KB")
            
            return jsonify({
                'success': True,
                'resultImage': result_image,
                'outputSize': output_size,
                'outputSizeMB': round(output_size / (1024 * 1024), 2),
                'processedWith': 'Free Preview (512px GPU-accelerated)',
                'processingTime': round(processing_time, 2)
            }), 200
            
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
    """Premium HD: 2000-4000px output using GPU-accelerated AI High-Resolution"""
    start_time = time.time()
    
    try:
        data = request.json
        if not data or 'imageData' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing imageData in request body'
            }), 400
        
        image_data = data.get('imageData')
        min_size = data.get('minSize', 2000)
        max_size = data.get('maxSize', 4000)
        user_id = data.get('userId')
        
        # Decode base64 image
        try:
            if ',' in image_data:
                # Remove data URL prefix if present
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            input_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert RGBA to RGB if needed
            if input_image.mode == 'RGBA':
                # Create white background
                rgb_image = Image.new('RGB', input_image.size, (255, 255, 255))
                rgb_image.paste(input_image, mask=input_image.split()[3])
                input_image = rgb_image
            elif input_image.mode != 'RGB':
                input_image = input_image.convert('RGB')
            
            # Calculate target size (2000-4000px max dimension)
            original_size = input_image.size
            max_dimension = max(original_size)
            
            if max_dimension > max_size:
                # Scale down to max_size
                scale = max_size / max_dimension
                new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
                input_image = input_image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {original_size} to {new_size} for HD processing")
            elif max_dimension < min_size:
                # Scale up to min_size (optional - can keep original if smaller)
                # For better quality, we'll scale up
                scale = min_size / max_dimension
                new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
                input_image = input_image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Upscaled image from {original_size} to {new_size} for HD processing")
            
            # Remove background using AI model HD
            session = get_session_hd()
            output_bytes = remove(input_image, session=session)
            
            # Convert to base64
            output_b64 = base64.b64encode(output_bytes).decode()
            result_image = f"data:image/png;base64,{output_b64}"
            
            processing_time = time.time() - start_time
            output_size = len(output_bytes)
            
            logger.info(f"Premium HD processed in {processing_time:.2f}s, output size: {output_size / 1024:.2f} KB, user: {user_id}")
            
            return jsonify({
                'success': True,
                'resultImage': result_image,
                'outputSize': output_size,
                'outputSizeMB': round(output_size / (1024 * 1024), 2),
                'processedWith': 'Premium HD (2000-4000px GPU-accelerated High-Resolution)',
                'processingTime': round(processing_time, 2),
                'creditsUsed': 1
            }), 200
            
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
        'service': 'bg-removal-birefnet',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'free_preview': '/api/free-preview-bg',
            'premium_hd': '/api/premium-bg',
            'health': '/health'
        }
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

