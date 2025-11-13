from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, make_response
from flask_cors import CORS
import os
import sys
import logging
import secrets
from werkzeug.utils import secure_filename
import openpyxl
import msoffcrypto
from datetime import datetime
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
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
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    return response

# Configure app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
LOGS_FOLDER = os.path.join(BASE_DIR, 'logs')

# Ensure required directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)

# Configuration
app.config.update(
    UPLOAD_FOLDER=os.environ.get('UPLOAD_FOLDER', UPLOAD_FOLDER),
    MAX_CONTENT_LENGTH=500 * 1024 * 1024,  # 500MB max file size
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-change-in-production'),
    DEBUG=os.environ.get('FLASK_ENV') == 'development'
)

# Log app configuration
logger.info(f"Base directory: {BASE_DIR}")
logger.info(f"Upload folder: {UPLOAD_FOLDER}")

# Ensure upload folder exists
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    logger.info(f"Upload directory created at: {UPLOAD_FOLDER}")
except Exception as e:
    logger.error(f"Error creating upload directory: {str(e)}")

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}

def unlock_excel(input_path, password=None):
    try:
        # Create output file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"unlocked_{timestamp}_{os.path.basename(input_path)}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Try to unlock with msoffcrypto first
        with open(input_path, 'rb') as file:
            office_file = msoffcrypto.OfficeFile(file)
            if office_file.is_encrypted():
                if password:
                    office_file.load_key(password=password)
                else:
                    # Try common passwords or empty password
                    try:
                        office_file.load_key(password='')
                    except:
                        office_file.load_key()  # Try without password
                
                with open(output_path, 'wb') as decrypted_file:
                    office_file.decrypt(decrypted_file)
                input_path = output_path  # Use decrypted file for further processing
        
        # Now remove worksheet protection
        wb = openpyxl.load_workbook(input_path)
        protected = False
        
        # Remove workbook protection
        if hasattr(wb, 'security') and wb.security is not None:
            try:
                if hasattr(wb.security, 'lockStructure') and wb.security.lockStructure:
                    wb.security.lockStructure = False
                    protected = True
                if hasattr(wb.security, 'workbookPassword') and wb.security.workbookPassword:
                    wb.security.workbookPassword = None
                    protected = True
                if hasattr(wb.security, 'revisionsPassword') and wb.security.revisionsPassword:
                    wb.security.revisionsPassword = None
                    protected = True
                if hasattr(wb.security, 'lockRevision') and wb.security.lockRevision:
                    wb.security.lockRevision = False
                    protected = True
            except Exception as e:
                logger.warning(f"Could not remove workbook protection: {e}")
        
        # Remove worksheet protection
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            try:
                if ws.protection.sheet or ws.protection.password:
                    ws.protection.set_password('')
                    ws.protection.sheet = False
                    protected = True
            except Exception as e:
                logger.warning(f"Could not remove protection from sheet {sheet_name}: {e}")
        
        # Always save the file (even if no protection found, file might be decrypted)
        wb.save(output_path)
        return True, output_filename
            
    except Exception as e:
        return False, str(e)

@app.route('/test')
def test():
    try:
        return jsonify({
            'status': 'success',
            'message': 'API is working!',
            'python_version': sys.version,
            'working_directory': os.getcwd(),
            'upload_folder': app.config['UPLOAD_FOLDER']
        }), 200
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return f"Error loading page: {str(e)}", 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    password = request.form.get('password', '')
    
    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        success, result = unlock_excel(filepath, password if password else None)
        
        if success:
            return render_template('result.html', 
                                 success=True, 
                                 filename=result,
                                 original=filename)
        else:
            return render_template('result.html', 
                                 success=False, 
                                 error=result)
    
    return redirect(url_for('index'))

@app.route('/unlock', methods=['POST'])
def unlock_file():
    """API endpoint for unlocking Excel files - used by frontend"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        password = request.form.get('password', '')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Only .xls and .xlsx files are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"Processing file: {filename}")
        
        # Unlock the file
        success, result = unlock_excel(filepath, password if password else None)
        
        # Clean up original file
        try:
            os.remove(filepath)
        except:
            pass
        
        if success:
            logger.info(f"Successfully unlocked file: {filename}")
            return jsonify({
                'success': True,
                'filename': result,
                'message': 'File unlocked successfully'
            }), 200
        else:
            logger.error(f"Failed to unlock file: {result}")
            return jsonify({
                'success': False,
                'error': result
            }), 400
            
    except Exception as e:
        logger.error(f"Error in unlock endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], 
                             filename, 
                             as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
