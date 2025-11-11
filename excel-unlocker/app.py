from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, make_response
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

app.config.update(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=106 * 1024 * 1024,  # 106MB max file size
    SECRET_KEY='EasyJpgtoPdf',
    DEBUG=True
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
        if hasattr(wb, 'security') and (wb.security.lockStructure or wb.security.workbookPassword):
            wb.security.lockStructure = False
            wb.security.workbookPassword = None
            wb.security.revisionsPassword = None
            wb.security.lockRevision = False
            protected = True
        
        # Remove worksheet protection
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            if ws.protection.sheet or ws.protection.password:
                ws.protection.set_password('')
                ws.protection.sheet = False
                protected = True
        
        if protected:
            wb.save(output_path)
            return True, output_filename
        else:
            return False, "No protection found on the file."
            
    except Exception as e:
        return False, str(e)

@app.route('/test')
def test():
    try:
        return jsonify({
            'status': 'success',
            'message': 'API is working!',
            'python_version': sys.version,
            'flask_version': Flask.__version__,
            'working_directory': os.getcwd(),
            'files_in_dir': os.listdir('.')
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

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], 
                             filename, 
                             as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
