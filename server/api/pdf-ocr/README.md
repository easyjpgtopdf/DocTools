# PDF OCR Backend Service

## Overview
High-accuracy OCR processing service for PDF editing. Uses server-side Tesseract OCR engine for professional-grade text recognition.

## Technology Stack
- **Backend Language**: Python 3
- **OCR Engine**: Tesseract OCR (Open Source)
- **Image Processing**: OpenCV, PIL/Pillow
- **API Server**: Node.js (Express.js)

## Setup Instructions

### 1. Install Python Dependencies
```bash
cd server/api/pdf-ocr
pip install -r requirements.txt
```

### 2. Install Tesseract OCR
**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH
- Or use: `choco install tesseract`

**Linux:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

**macOS:**
```bash
brew install tesseract
```

### 3. Install Language Packs (Optional)
For better accuracy with specific languages:
```bash
# Linux
sudo apt-get install tesseract-ocr-hin tesseract-ocr-ben tesseract-ocr-guj

# macOS
brew install tesseract-lang
```

### 4. Start Node.js Server
```bash
cd server
npm install
npm start
```

## API Endpoint

### POST /api/pdf-ocr/process

**Request:**
```json
{
  "image": "data:image/png;base64,...",
  "language": "eng"
}
```

**Response:**
```json
{
  "success": true,
  "lines": [
    {
      "text": "Recognized text",
      "bbox": {
        "x0": 100,
        "y0": 200,
        "x1": 300,
        "y2": 220
      },
      "confidence": 95
    }
  ],
  "full_text": "Complete recognized text"
}
```

## Accuracy Features
- Image preprocessing (denoising, thresholding)
- Confidence filtering (removes low-confidence results)
- Line grouping for better text organization
- Support for multiple languages

## Performance
- Server-side processing for better accuracy
- Handles images up to 50MB
- Typical processing time: 2-5 seconds per page

## Notes
- All code is open source with no copyright restrictions
- No external paid services or proprietary software references
- Fully compatible with AdSense policies

