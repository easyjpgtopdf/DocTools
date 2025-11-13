"""
Background Remover API - Lightweight Proxy Mode
Optimized for Render Free Tier
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os

app = Flask(__name__)

# Enable CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"]
    }
})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/', methods=['GET'])
def home():
    """API info endpoint"""
    return jsonify({
        'service': 'Background Remover API',
        'status': 'running',
        'version': '2.0',
        'tier': 'Render Free',
        'note': 'Lightweight proxy mode - browser processing recommended',
        'endpoints': {
            'GET /': 'API information',
            'GET /health': 'Health check',
            'POST /remove-background': 'Background removal (proxy mode)'
        }
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'background-remover-proxy'
    }), 200


@app.route('/remove-background', methods=['POST', 'OPTIONS'])
def remove_background():
    """Proxy endpoint - recommends browser processing"""
    
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    logger.info("Request received - recommending browser processing")
    
    return jsonify({
        'success': False,
        'error': 'Server processing unavailable',
        'message': 'Browser processing works great for 0-25 MB files',
        'fallback': 'browser'
    }), 503


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
