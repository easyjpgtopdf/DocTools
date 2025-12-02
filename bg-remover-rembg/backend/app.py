# ============================================
# REMBG U2NET BACKGROUND REMOVER
# Cloud Run Optimized - Always Warm
# ============================================

import base64
import io
import logging
import os
import traceback
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from rembg import remove, new_session
from PIL import Image

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
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept, Authorization, X-Requested-With, X-User-ID, X-User-Type'
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

# Global session - initialized once
u2net_session = None
u2netp_session = None
current_model = None

def init_sessions():
    """Initialize rembg sessions - u2net primary, u2netp fallback"""
    global u2net_session, u2netp_session, current_model
    
    try:
        # Try u2net first (better quality)
        logger.info("🎨 Initializing u2net session...")
        u2net_session = new_session(model_name="u2net")
        current_model = "u2net"
        logger.info("✅ u2net session initialized successfully")
        
        # Also initialize u2netp as fallback
        try:
            logger.info("🎨 Initializing u2netp session (fallback)...")
            u2netp_session = new_session(model_name="u2netp")
            logger.info("✅ u2netp session initialized (fallback ready)")
        except Exception as e:
            logger.warning(f"⚠️ u2netp initialization failed (will use u2net only): {str(e)}")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize u2net: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        # Try u2netp as primary if u2net fails
        try:
            logger.info("🔄 Falling back to u2netp...")
            u2netp_session = new_session(model_name="u2netp")
            current_model = "u2netp"
            logger.info("✅ u2netp session initialized as primary")
        except Exception as e2:
            logger.error(f"❌ u2netp also failed: {str(e2)}")
            raise

# Initialize sessions on startup
try:
    init_sessions()
except Exception as e:
    logger.error(f"❌ Critical: Failed to initialize rembg sessions: {str(e)}")
    logger.error("Service may not work properly")

def dataurl_to_image(dataurl):
    """Convert data URL to PIL Image"""
    header, b64 = dataurl.split(',', 1) if ',' in dataurl else (None, dataurl)
    data = base64.b64decode(b64)
    return Image.open(io.BytesIO(data)).convert("RGBA")

def image_to_dataurl(img):
    """Convert PIL Image to data URL"""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f"data:image/png;base64,{b64}"

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
        'service': 'Background Remover API - Rembg U2Net',
        'status': 'running',
        'model': current_model or 'initializing',
        'version': '1.0.0',
        'features': ['High Quality', 'U2Net Primary', 'U2NetP Fallback', 'Always Warm']
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    model_status = current_model if current_model else 'not initialized'
    u2net_ok = u2net_session is not None
    u2netp_ok = u2netp_session is not None
    
    return jsonify({
        'status': 'ok' if (u2net_ok or u2netp_ok) else 'error',
        'model': model_status,
        'u2net_available': u2net_ok,
        'u2netp_available': u2netp_ok,
        'service': 'Background Remover API - Rembg U2Net'
    }), 200 if (u2net_ok or u2netp_ok) else 500

@app.route('/remove-background', methods=['POST'])
def remove_bg():
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
        
        payload = request.get_json(force=True)
        image_dataurl = payload.get("imageData")
        
        if not image_dataurl:
            return jsonify({
                'success': False,
                'error': 'Missing image data',
                'message': 'imageData field is required'
            }), 400
        
        # Convert data URL to image
        try:
            img = dataurl_to_image(image_dataurl)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Invalid image data',
                'message': f'Failed to decode image: {str(e)}'
            }), 400
        
        # Validate dimensions
        width, height = img.size
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            return jsonify({
                'success': False,
                'error': 'Image too large',
                'message': f'Image dimensions exceed {MAX_DIMENSION}x{MAX_DIMENSION} pixels'
            }), 400
        
        logger.info(f"Processing image: {width}x{height}, User: {user_id} ({user_type})")
        
        # Process with rembg - try u2net first, fallback to u2netp
        result_img = None
        model_used = None
        
        try:
            # Try u2net first (better quality)
            if u2net_session is not None:
                logger.info("Using u2net model...")
                result_img = remove(img, session=u2net_session)
                model_used = "u2net"
            elif u2netp_session is not None:
                logger.info("Using u2netp model (u2net not available)...")
                result_img = remove(img, session=u2netp_session)
                model_used = "u2netp"
            else:
                raise Exception("No rembg session available")
                
        except Exception as e:
            logger.error(f"❌ Error during rembg processing: {str(e)}")
            # Try fallback to u2netp if u2net failed
            if model_used != "u2netp" and u2netp_session is not None:
                try:
                    logger.info("🔄 Falling back to u2netp...")
                    result_img = remove(img, session=u2netp_session)
                    model_used = "u2netp"
                except Exception as e2:
                    logger.error(f"❌ u2netp fallback also failed: {str(e2)}")
                    raise Exception(f"Both models failed: u2net ({str(e)}), u2netp ({str(e2)})")
            else:
                raise
        
        # Convert result to data URL
        out_dataurl = image_to_dataurl(result_img)
        
        # Track usage
        track_usage(user_id)
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Processing completed in {processing_time:.2f}s using {model_used}")
        
        return jsonify({
            'success': True,
            'resultImage': out_dataurl,
            'processedWith': f'rembg-{model_used}',
            'processingTime': round(processing_time, 2),
            'model': model_used
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error during processing: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': 'Processing failed',
            'message': str(e)
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
    logger.info(f"🚀 Starting Background Remover API (Rembg U2Net) on port {port}")
    logger.info(f"📏 Max file size: {MAX_FILE_SIZE / (1024*1024):.0f} MB")
    logger.info(f"🖼️ Max dimension: {MAX_DIMENSION} pixels")
    logger.info(f"✅ Supported formats: {', '.join(SUPPORTED_FORMATS)}")
    logger.info(f"⚙️ Model: {current_model or 'initializing'}")
    
    app.run(host='0.0.0.0', port=port, debug=False)

