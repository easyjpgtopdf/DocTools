# Background Remover Backend (Rembg + Render)
# Free Python backend for large files (15+ MB)

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from rembg import remove
from PIL import Image
import io
import base64
import logging
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Max file size: 50 MB
MAX_FILE_SIZE = 50 * 1024 * 1024

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Background Remover API',
        'status': 'running',
        'version': '1.0',
        'powered_by': 'Rembg + Render',
        'max_file_size': '50 MB',
        'supported_formats': ['PNG', 'JPG', 'JPEG', 'WEBP']
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        # Check if file is in request
        if 'image' not in request.files and 'imageData' not in request.json:
            return jsonify({'error': 'No image provided'}), 400

        # Get image from file upload or base64
        if 'image' in request.files:
            file = request.files['image']
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > MAX_FILE_SIZE:
                return jsonify({'error': f'File too large. Max size: 50 MB'}), 400
            
            logger.info(f"Processing uploaded file: {file.filename}, Size: {file_size / (1024*1024):.2f} MB")
            input_image = Image.open(file.stream)
            
        else:
            # Handle base64 image
            data = request.get_json()
            image_data = data.get('imageData', '')
            
            if not image_data:
                return jsonify({'error': 'No image data provided'}), 400
            
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            if len(image_bytes) > MAX_FILE_SIZE:
                return jsonify({'error': f'File too large. Max size: 50 MB'}), 400
            
            logger.info(f"Processing base64 image, Size: {len(image_bytes) / (1024*1024):.2f} MB")
            input_image = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA to RGB if necessary (for JPEG compatibility)
        if input_image.mode == 'RGBA':
            # Keep RGBA for PNG output
            pass
        elif input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')

        # Remove background using rembg
        logger.info("Starting background removal with rembg...")
        output_image = remove(input_image)
        logger.info("Background removal completed successfully")

        # Convert to bytes
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format='PNG', optimize=True, quality=95)
        output_buffer.seek(0)

        # Convert to base64 for JSON response
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        output_data_url = f'data:image/png;base64,{output_base64}'

        # Get output size
        output_size = len(output_buffer.getvalue())
        
        return jsonify({
            'success': True,
            'resultImage': output_data_url,
            'outputSize': output_size,
            'outputSizeMB': round(output_size / (1024 * 1024), 2),
            'message': 'Background removed successfully with Rembg'
        })

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to remove background'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
