#!/usr/bin/env python3
"""
PDF OCR Processing Service
High-accuracy OCR using Tesseract OCR engine
Open source implementation - no copyright restrictions
"""

import sys
import json
import base64
import io
import os
import platform
from PIL import Image
import pytesseract
import cv2
import numpy as np

# Auto-detect Tesseract path on Windows
if platform.system() == 'Windows':
    # Common Tesseract installation paths
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', '')),
        r'C:\tesseract-ocr\tesseract.exe',
    ]
    
    # Check if tesseract is in PATH first
    tesseract_found = False
    try:
        import shutil
        tesseract_cmd = shutil.which('tesseract')
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            tesseract_found = True
    except:
        pass
    
    # If not in PATH, try common installation paths
    if not tesseract_found:
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                tesseract_found = True
                break
    
    # If still not found, try to find in Program Files
    if not tesseract_found:
        try:
            import subprocess
            result = subprocess.run(['where', 'tesseract'], capture_output=True, text=True, shell=True)
            if result.returncode == 0 and result.stdout.strip():
                pytesseract.pytesseract.tesseract_cmd = result.stdout.strip().split('\n')[0]
                tesseract_found = True
        except:
            pass

def preprocess_image(image_data):
    """Preprocess image for better OCR accuracy"""
    try:
        # Decode base64 image
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array for OpenCV processing
        img_array = np.array(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Apply thresholding for better text recognition
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return processed
        
    except Exception as e:
        print(f"Error preprocessing image: {str(e)}", file=sys.stderr)
        return None

def perform_ocr(image_data, language='eng'):
    """Perform OCR on image with high accuracy settings"""
    try:
        # Preprocess image
        processed_image = preprocess_image(image_data)
        if processed_image is None:
            return None
        
        # Configure Tesseract for high accuracy
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?;:()[]{}\'"-+=*/@#$%^&*_|\\<>~` '
        
        # Perform OCR with detailed output
        ocr_data = pytesseract.image_to_data(
            processed_image,
            lang=language,
            config=custom_config,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text lines with bounding boxes
        lines = []
        current_line = None
        current_y = None
        line_height = 0
        
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i].strip()
            if text and int(ocr_data['conf'][i]) > 30:  # Confidence threshold
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                conf = int(ocr_data['conf'][i])
                
                # Group words into lines based on Y position
                if current_line is None or abs(y - current_y) > h * 0.5:
                    if current_line:
                        lines.append(current_line)
                    current_line = {
                        'text': text,
                        'bbox': {'x0': x, 'y0': y, 'x1': x + w, 'y1': y + h},
                        'confidence': conf
                    }
                    current_y = y
                    line_height = h
                else:
                    # Add to current line
                    current_line['text'] += ' ' + text
                    current_line['bbox']['x1'] = max(current_line['bbox']['x1'], x + w)
                    current_line['bbox']['y1'] = max(current_line['bbox']['y1'], y + h)
                    current_line['confidence'] = min(current_line['confidence'], conf)
        
        # Add last line
        if current_line:
            lines.append(current_line)
        
        return {
            'success': True,
            'lines': lines,
            'full_text': ' '.join([line['text'] for line in lines])
        }
        
    except Exception as e:
        print(f"Error performing OCR: {str(e)}", file=sys.stderr)
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main function to process OCR request"""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        
        image_data = input_data.get('image')
        language = input_data.get('language', 'eng')
        
        if not image_data:
            result = {
                'success': False,
                'error': 'No image data provided'
            }
        else:
            result = perform_ocr(image_data, language)
        
        # Output result as JSON
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == '__main__':
    main()

