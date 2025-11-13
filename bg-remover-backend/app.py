"""
Professional Background Remover - Remove.bg API Integration
100% Quality - No Over-Cleaning
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
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
        'version': '5.0',
        'tier': 'Remove.bg API',
        'quality': '100% Professional - No over-cleaning',
        'powered_by': 'Remove.bg'
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
        
        # Get image data and API key
        if not request.is_json:
            return jsonify({'error': 'JSON with imageData required'}), 400
        
        data = request.get_json()
        image_data = data.get('imageData', '')
        api_key = data.get('apiKey', os.environ.get('REMOVEBG_API_KEY', ''))
        
        if not image_data:
            return jsonify({'error': 'No imageData provided'}), 400
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide Remove.bg API key',
                'fallback': 'browser'
            }), 400
        
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
        
        # Call Remove.bg API
        logger.info("🤖 Calling Remove.bg professional API...")
        response = requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': image_bytes},
            data={'size': 'auto'},
            headers={'X-Api-Key': api_key},
            timeout=60
        )
        
        if response.status_code == 200:
            output_bytes = response.content
            output_base64 = base64.b64encode(output_bytes).decode('utf-8')
            output_data_url = f'data:image/png;base64,{output_base64}'
            
            output_size = len(output_bytes)
            logger.info(f"🎉 Success! Output: {output_size/(1024*1024):.2f} MB")
            
            return jsonify({
                'success': True,
                'resultImage': output_data_url,
                'outputSize': output_size,
                'outputSizeMB': round(output_size / (1024 * 1024), 2),
                'processedWith': 'Remove.bg (Professional)',
                'message': 'Background removed successfully with professional quality'
            }), 200
        else:
            error_msg = response.json().get('errors', [{}])[0].get('title', 'API error')
            logger.error(f"💥 Remove.bg error: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'message': 'API processing failed',
                'fallback': 'browser'
            }), 500
    
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
    logger.info(f"🎨 Using Remove.bg API (Professional Quality)")
    logger.info(f"📊 Max file size: 50 MB")
    app.run(host='0.0.0.0', port=port, debug=False)
