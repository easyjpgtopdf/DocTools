# PDF to Excel Converter Backend

Production-ready backend for converting PDF files to Excel using Google Document AI.

## Features

- PDF processing with Google Document AI
- Table extraction from PDF documents
- Excel generation using openpyxl
- Google Cloud Storage for output files
- Credit system (5 free pages for new users)
- CORS enabled for browser access

## Environment Variables

Set these environment variables before running:

```bash
# Google Document AI
DOCAI_PROJECT_ID=easyjpgtopdf-de346
DOCAI_LOCATION=us-central1
DOCAI_PROCESSOR_ID=your-processor-id  # Get from Document AI UI

# Storage
GCS_BUCKET=your-gcs-bucket-name
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables

3. Run the server:
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## Docker Build

```bash
docker build -t pdf-to-excel-backend .
docker run -p 8080:8080 --env-file .env pdf-to-excel-backend
```

## Google Cloud Run Deployment

See `DEPLOYMENT.md` for detailed instructions.

## API Endpoints

### POST /api/pdf-to-excel
Convert PDF to Excel.

**Request:**
- Form data with `file` field containing PDF

**Response:**
```json
{
  "success": true,
  "downloadUrl": "https://...",
  "pagesConverted": 5,
  "creditsLeft": 0,
  "tablesFound": 3,
  "filename": "document.xlsx"
}
```

### GET /api/credits
Get current credit balance.

**Response:**
```json
{
  "success": true,
  "credits": 5,
  "created_at": "2024-01-01T00:00:00"
}
```

### POST /api/buy-credits
Add credits (dummy implementation).

**Response:**
```json
{
  "success": true,
  "message": "Added 10 credits",
  "credits": 15
}
```

## Error Responses

### Insufficient Credits (402)
```json
{
  "insufficient_credits": true,
  "message": "Insufficient credits. Need 5 credits, have 2",
  "required": 5,
  "available": 2
}
```

## Credit System

- New users get 5 free pages
- 1 credit = 1 page
- Credits deducted only after successful conversion
- In-memory storage (can be replaced with database)

## Google Document AI Setup

1. Go to [Google Cloud Console - Document AI](https://console.cloud.google.com/ai/document-ai/processors)
2. Create a new processor (Form Parser or Document OCR)
3. Copy the Processor ID from the UI
4. Set `DOCAI_PROCESSOR_ID` environment variable with the Processor ID
