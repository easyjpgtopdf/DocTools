"""
Professional Background Remover - Production Grade
Using Rembg U²-Net AI Model (same as remove.bg uses)
100% Quality - No Over-Cleaning
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from rembg import remove
from PIL import Image
import io
import base64
import logging
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type", "Accept"]}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Professional Background Remover',
        'status': 'running',
        'version': '4.0',
        'tier': 'Render Free',
        'model': 'U²-Net (Production Grade)',
        'quality': '100% - No over-cleaning',
        'powered_by': 'Rembg AI'
    }), 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'bg-remover-professional'}), 200


@app.route('/remove-background', methods=['POST', 'OPTIONS'])
def remove_background():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        logger.info("📥 Professional background removal started")
        
        # Get image data
        if not request.is_json:
            return jsonify({'error': 'JSON with imageData required'}), 400
        
        data = request.get_json()
        image_data = data.get('imageData', '')
        
        if not image_data:
            return jsonify({'error': 'No imageData provided'}), 400
        
        # Decode base64
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]
        
        try:
            image_bytes = base64.b64decode(image_data)
        except:
            return jsonify({'error': 'Invalid base64 data'}), 400
        
        if len(image_bytes) > MAX_FILE_SIZE:
            size_mb = len(image_bytes) / (1024 * 1024)
            return jsonify({'error': f'File too large: {size_mb:.1f} MB (max 50 MB)'}), 400
        
        logger.info(f"📊 Processing {len(image_bytes)/(1024*1024):.2f} MB image")
        
        # Load image
        input_image = Image.open(io.BytesIO(image_bytes))
        logger.info(f"🖼️ Image: {input_image.size[0]}x{input_image.size[1]}, Mode: {input_image.mode}")
        
        # Convert to RGB if needed
        if input_image.mode not in ('RGB', 'RGBA'):
            input_image = input_image.convert('RGB')
        
        # Professional background removal with Rembg
        logger.info("🤖 Removing background with U²-Net AI model...")
        output_image = remove(input_image)
        logger.info("✅ Background removed with professional quality!")
        
        # Save as PNG with transparency
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format='PNG', optimize=True, compress_level=6)
        output_buffer.seek(0)
        
        # Encode to base64
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        output_data_url = f'data:image/png;base64,{output_base64}'
        
        output_size = len(output_buffer.getvalue())
        logger.info(f"🎉 Success! Output: {output_size/(1024*1024):.2f} MB")
        
        return jsonify({
            'success': True,
            'resultImage': output_data_url,
            'outputSize': output_size,
            'outputSizeMB': round(output_size / (1024 * 1024), 2),
            'processedWith': 'Rembg U²-Net (Professional)',
            'message': 'Background removed successfully with professional quality'
        }), 200
    
    except Exception as e:
        logger.error(f"💥 Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Processing failed',
            'fallback': 'browser'
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Starting Professional Background Remover on port {port}")
    logger.info(f"🎨 Model: U²-Net AI (Production Grade)")
    logger.info(f"📊 Max file size: 50 MB")
    app.run(host='0.0.0.0', port=port, debug=False)
