# PDF Editor Backend Service

Native PDF editing service using PyMuPDF and PaddleOCR for real-time PDF manipulation.

## Features

- **Native PDF Editing**: Real text add/edit/delete using PyMuPDF (no HTML overlays)
- **OCR Support**: PaddleOCR for Hindi + English text extraction from scanned PDFs
- **Credit System**: Integrated with existing credit system (10 credits per page edit)
- **Free Limits**: Free users get 7 words for add/edit/delete, premium users get unlimited
- **Export Formats**: PDF, DOCX, XLSX, PPTX
- **Cloud Run Ready**: Optimized for Google Cloud Run with min instances 0

## API Endpoints

### POST /session/start
Start a new PDF editing session.
- Input: PDF file upload
- Output: `{session_id, page_count}`

### POST /page/render
Render a PDF page as PNG image.
- Input: `{session_id, page_number, zoom}`
- Output: PNG image bytes

### POST /text/search
Search for text in PDF.
- Input: `{session_id, query}`
- Output: List of matches with page_number + bbox

### POST /text/edit
Edit/replace text in PDF.
- Input: `{session_id, page_number, bbox, new_text, font_name, font_size, color, userId}`
- Output: Success message

### POST /text/add
Add new text to PDF.
- Input: `{session_id, page_number, x, y, text, font_name, font_size, color, userId}`
- Output: Success message

### POST /text/delete
Delete text from PDF.
- Input: `{session_id, page_number, bbox, userId}`
- Output: Success message

### POST /ocr/page
Run OCR on a PDF page.
- Input: `{session_id, page_number, userId}`
- Output: OCR results with text and positions

### POST /export
Export PDF to different formats.
- Input: `{session_id, format: ["pdf","docx","xlsx","pptx"], userId}`
- Output: File download

## Credit System

- **Free Users**: 7 words free for add/edit/delete operations
- **Premium Users**: Unlimited access
- **Per Page Edit**: 10 credits deducted from user balance
- **Credit Check**: Automatically checks user credits before operations

## Deployment

### Local Development
```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8080
```

### Google Cloud Run
```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Build and deploy
./deploy-cloudrun.sh
```

Or manually:
```bash
gcloud run deploy pdf-editor-service \
  --image gcr.io/YOUR_PROJECT_ID/pdf-editor-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 2Gi \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300
```

## Environment Variables

- `API_BASE_URL`: Base URL for credit API (default: https://easyjpgtopdf.com)
- `PORT`: Server port (default: 8080)

## Dependencies

- FastAPI: Web framework
- PyMuPDF (fitz): Native PDF editing
- PaddleOCR: OCR engine for Hindi + English
- python-docx: Word export
- openpyxl: Excel export
- python-pptx: PowerPoint export

## Notes

- Sessions are stored in-memory (use Redis for production)
- OCR engine initializes on first use (lazy loading)
- All PDF edits are native (no HTML overlays)
- Credit system integrates with existing Firebase/Firestore setup

