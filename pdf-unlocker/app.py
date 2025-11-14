from flask import Flask, request, send_from_directory, jsonify, make_response
from flask_cors import CORS
import os
import sys
import logging
import secrets
from werkzeug.utils import secure_filename
import PyPDF2
import pikepdf
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data: https:;"
    return response

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logger.info(f"Base directory: {BASE_DIR}")
logger.info(f"Upload folder: {UPLOAD_FOLDER}")
logger.info(f"Upload directory created at: {UPLOAD_FOLDER}")

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def unlock_pdf(input_path, password, output_path):
    """
    Unlock a password-protected PDF file using multiple methods
    
    Args:
        input_path: Path to the encrypted PDF
        password: Password to decrypt (can be None)
        output_path: Path to save unlocked PDF
    
    Returns:
        tuple: (success: bool, method: str)
    """
    
    # Method 1: Try pikepdf first (better for owner password / restrictions)
    try:
        logger.info("Attempting pikepdf unlock (owner password bypass)...")
        with pikepdf.open(input_path, password=password if password else '', allow_overwriting_input=True) as pdf:
            pdf.save(output_path)
            logger.info("Successfully unlocked PDF using pikepdf (owner password bypass)")
            return True, "Owner password removed / Restrictions bypassed"
    except pikepdf.PasswordError:
        logger.warning("pikepdf failed - trying common passwords...")
    except Exception as e:
        logger.warning(f"pikepdf error: {str(e)}")
    
    # Method 2: Try common passwords
    common_passwords = [
        '',  # Empty password
        '123456', 'password', '12345678', 'qwerty', '123456789',
        'abc123', 'password1', '1234567', '12345', 'iloveyou',
        '111111', '123123', 'admin', 'welcome', 'monkey',
        'Password', 'PASSWORD', '1234', '000000', 'letmein',
        'qwerty123', 'password123', 'welcome123', 'abc123456',
        '123', '1234567890', 'Pass@123', 'Admin@123'
    ]
    
    # Add user-provided password to the front of the list
    if password:
        common_passwords.insert(0, password)
    
    for attempt_password in common_passwords:
        try:
            # Try with pikepdf
            with pikepdf.open(input_path, password=attempt_password, allow_overwriting_input=True) as pdf:
                pdf.save(output_path)
                if attempt_password:
                    logger.info(f"Successfully unlocked PDF with password attempt")
                else:
                    logger.info("Successfully unlocked PDF with empty password")
                return True, f"Unlocked with common password"
        except pikepdf.PasswordError:
            continue
        except Exception:
            continue
    
    # Method 3: Fallback to PyPDF2 (for some edge cases)
    try:
        logger.info("Attempting PyPDF2 unlock...")
        with open(input_path, 'rb') as input_file:
            pdf_reader = PyPDF2.PdfReader(input_file)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                # Try to decrypt with password or empty
                decrypt_password = password if password else ''
                decrypt_result = pdf_reader.decrypt(decrypt_password)
                if decrypt_result == 0:
                    logger.error("All unlock attempts failed")
                    return False, "Password required - could not unlock"
            
            # Create PDF writer
            pdf_writer = PyPDF2.PdfWriter()
            
            # Copy all pages
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                pdf_writer.add_page(page)
            
            # Write unlocked PDF
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            logger.info("Successfully unlocked PDF using PyPDF2")
            return True, "Unlocked using PyPDF2"
            
    except Exception as e:
        logger.error(f"All unlock methods failed: {str(e)}")
        return False, f"Could not unlock PDF: {str(e)}"

@app.route('/test', methods=['GET'])
def test():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'PDF Unlocker API is working!',
        'python_version': sys.version,
        'upload_folder': app.config['UPLOAD_FOLDER'],
        'working_directory': os.getcwd()
    })

@app.route('/unlock', methods=['POST'])
def unlock():
    """Unlock PDF file endpoint"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        password = request.form.get('password', '')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Only PDF files allowed'}), 400
        
        # Secure filename
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_filename = f"input_{timestamp}_{original_filename}"
        output_filename = f"unlocked_{timestamp}_{original_filename}"
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Save uploaded file
        file.save(input_path)
        logger.info(f"File saved: {input_path}")
        
        # Unlock PDF
        success, method = unlock_pdf(input_path, password, output_path)
        
        # Clean up input file
        if os.path.exists(input_path):
            os.remove(input_path)
        
        if success:
            return jsonify({
                'success': True,
                'filename': output_filename,
                'message': f'PDF unlocked successfully! ({method})'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to unlock PDF. {method}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error in unlock endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    """Download unlocked PDF file"""
    try:
        # Security: Only allow downloading files from uploads folder
        safe_filename = secure_filename(filename)
        return send_from_directory(app.config['UPLOAD_FOLDER'], 
                                  safe_filename, 
                                  as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
