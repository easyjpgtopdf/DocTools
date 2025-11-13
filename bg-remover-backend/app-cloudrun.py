# Background Remover - Google Cloud Run (For 50+ MB files)
# Optimized for large file processing with better memory management

from flask import Flask, request, jsonify
from flask_cors import CORS
from rembg import remove
from PIL import Image
import io
import base64
import logging
import os
import gc

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Max file size for Cloud Run: 100 MB (can handle larger files)
MAX_FILE_SIZE = 100 * 1024 * 1024

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Background Remover API (Cloud Run)',
        'status': 'running',
        'version': '2.0',
        'powered_by': 'Rembg + Google Cloud Run',
        'max_file_size': '100 MB',
        'optimized_for': 'Large files (50+ MB)',
        'supported_formats': ['PNG', 'JPG', 'JPEG', 'WEBP', 'BMP', 'TIFF']
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'cloudrun'}), 200

@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        # Get image from request
        if 'image' not in request.files and 'imageData' not in request.json:
            return jsonify({'error': 'No image provided'}), 400

        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            
            # Check file size
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                return jsonify({'error': f'File too large. Max size: 100 MB'}), 400
            
            logger.info(f"Processing uploaded file: {file.filename}, Size: {file_size / (1024*1024):.2f} MB")
            input_image = Image.open(file.stream)
            
        else:
            # Handle base64 image
            data = request.get_json()
            image_data = data.get('imageData', '')
            
            if not image_data:
                return jsonify({'error': 'No image data provided'}), 400
            
            # Remove data URL prefix
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            if len(image_bytes) > MAX_FILE_SIZE:
                return jsonify({'error': f'File too large. Max size: 100 MB'}), 400
            
            logger.info(f"Processing base64 image, Size: {len(image_bytes) / (1024*1024):.2f} MB")
            input_image = Image.open(io.BytesIO(image_bytes))

        # Optimize large images for processing
        original_size = input_image.size
        max_dimension = 4096  # Max dimension for processing
        
        if max(input_image.size) > max_dimension:
            ratio = max_dimension / max(input_image.size)
            new_size = (int(input_image.size[0] * ratio), int(input_image.size[1] * ratio))
            logger.info(f"Resizing image from {original_size} to {new_size} for processing")
            input_image = input_image.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to RGB if necessary
        if input_image.mode not in ('RGB', 'RGBA'):
            input_image = input_image.convert('RGB')

        # Remove background with optimized settings for large files
        logger.info("Starting background removal with Rembg (u2net model)...")
        output_image = remove(
            input_image,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )
        logger.info("Background removal completed successfully")

        # Free memory
        del input_image
        gc.collect()

        # Optimize output
        output_buffer = io.BytesIO()
        
        # Use compression for large outputs
        if max(output_image.size) > 2048:
            output_image.save(output_buffer, format='PNG', optimize=True, compress_level=6)
        else:
            output_image.save(output_buffer, format='PNG', optimize=True, quality=95)
        
        output_buffer.seek(0)

        # Convert to base64
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        output_data_url = f'data:image/png;base64,{output_base64}'

        # Get output info
        output_size = len(output_buffer.getvalue())
        
        # Free memory
        del output_image
        gc.collect()
        
        logger.info(f"Processing complete. Output size: {output_size / (1024*1024):.2f} MB")
        
        return jsonify({
            'success': True,
            'resultImage': output_data_url,
            'outputSize': output_size,
            'outputSizeMB': round(output_size / (1024 * 1024), 2),
            'originalSize': original_size,
            'processedWith': 'Google Cloud Run - Rembg AI',
            'message': 'Background removed successfully'
        })

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        gc.collect()  # Free memory on error
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to remove background'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
