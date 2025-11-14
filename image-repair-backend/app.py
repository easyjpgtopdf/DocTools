from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import cv2
import numpy as np
from rembg import remove
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import io
import base64
from datetime import datetime
import tempfile

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Maximum file size: 15MB
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024

@app.route('/test', methods=['GET'])
def test():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Image Repair API is working!',
        'backend': 'Google Cloud + rembg',
        'tools': '100+',
        'supported_formats': ['jpg', 'jpeg', 'png', 'webp', 'bmp']
    })

@app.route('/upload', methods=['POST'])
def upload_image():
    """Upload and store image"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Save uploaded file
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'Image uploaded successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_image():
    """Process image with AI tools"""
    try:
        data = request.json
        filename = data.get('filename')
        tool = data.get('tool')
        params = data.get('params', {})
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Load image
        img = Image.open(filepath)
        
        # Apply tool
        processed_img = apply_tool(img, tool, params)
        
        # Save processed image
        output_filename = f"processed_{filename}"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        processed_img.save(output_path)
        
        # Convert to base64 for preview
        buffered = io.BytesIO()
        processed_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'preview': f"data:image/png;base64,{img_str}"
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remove-background', methods=['POST'])
def remove_background():
    """Remove background using rembg"""
    try:
        data = request.json
        filename = data.get('filename')
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Load image
        with open(filepath, 'rb') as f:
            input_img = f.read()
        
        # Remove background
        output_img = remove(input_img)
        
        # Save processed image
        output_filename = f"nobg_{filename}"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        with open(output_path, 'wb') as f:
            f.write(output_img)
        
        # Convert to base64
        img_str = base64.b64encode(output_img).decode()
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'preview': f"data:image/png;base64,{img_str}"
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/face-enhance', methods=['POST'])
def face_enhance():
    """AI Face Enhancement"""
    try:
        data = request.json
        filename = data.get('filename')
        enhancement_type = data.get('type', 'smooth')
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        img = cv2.imread(filepath)
        
        # Face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Enhance faces
        for (x, y, w, h) in faces:
            face_roi = img[y:y+h, x:x+w]
            
            if enhancement_type == 'smooth':
                # Bilateral filter for skin smoothing
                face_roi = cv2.bilateralFilter(face_roi, 9, 75, 75)
            elif enhancement_type == 'sharpen':
                # Sharpen face
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                face_roi = cv2.filter2D(face_roi, -1, kernel)
            
            img[y:y+h, x:x+w] = face_roi
        
        # Save result
        output_filename = f"face_{filename}"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        cv2.imwrite(output_path, img)
        
        # Convert to base64
        _, buffer = cv2.imencode('.png', img)
        img_str = base64.b64encode(buffer).decode()
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'preview': f"data:image/png;base64,{img_str}",
            'faces_detected': len(faces)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download processed image"""
    try:
        format_type = request.args.get('format', 'png')
        filepath = os.path.join(PROCESSED_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Convert to requested format
        img = Image.open(filepath)
        output = io.BytesIO()
        
        if format_type == 'jpg' or format_type == 'jpeg':
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(output, format='JPEG', quality=95)
            mimetype = 'image/jpeg'
        elif format_type == 'webp':
            img.save(output, format='WEBP', quality=95)
            mimetype = 'image/webp'
        else:  # png
            img.save(output, format='PNG')
            mimetype = 'image/png'
        
        output.seek(0)
        return send_file(output, mimetype=mimetype, as_attachment=True, 
                        download_name=f"repaired_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}")
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def apply_tool(img, tool, params):
    """Apply various image processing tools"""
    
    if tool == 'auto-fix':
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.3)
    
    elif tool == 'deblur':
        img = img.filter(ImageFilter.SHARPEN)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
    
    elif tool == 'denoise':
        img = img.filter(ImageFilter.MedianFilter(size=3))
    
    elif tool == 'enhance':
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)
    
    elif tool == 'brightness':
        value = params.get('value', 0) / 100
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1 + value)
    
    elif tool == 'contrast':
        value = params.get('value', 0) / 100
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1 + value)
    
    elif tool == 'saturation':
        value = params.get('value', 0) / 100
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1 + value)
    
    elif tool == 'grayscale':
        img = img.convert('L').convert('RGB')
    
    elif tool == 'sepia':
        img = img.convert('RGB')
        pixels = img.load()
        for i in range(img.width):
            for j in range(img.height):
                r, g, b = pixels[i, j]
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                pixels[i, j] = (min(tr, 255), min(tg, 255), min(tb, 255))
    
    elif tool == 'invert':
        img = Image.eval(img, lambda x: 255 - x)
    
    elif tool == 'blur-bg':
        img = img.filter(ImageFilter.GaussianBlur(radius=10))
    
    elif tool == 'sharpen':
        img = img.filter(ImageFilter.SHARPEN)
    
    return img

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
