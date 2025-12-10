# PDF to Word Converter Backend

Production-ready PDF to Word conversion service using Python, FastAPI, LibreOffice, and Google Cloud services.

## Features

- **Dual Conversion Methods**:
  - LibreOffice headless for PDFs with extractable text
  - Google Document AI for scanned/image-based PDFs with OCR
  
- **Google Cloud Integration**:
  - Google Cloud Storage for file storage
  - Signed URLs for secure file downloads
  - Firebase Authentication support
  
- **Production Ready**:
  - Docker containerization
  - Deployable to Google Cloud Run
  - Comprehensive error handling
  - Logging and monitoring

## Tech Stack

- **Language**: Python 3.11
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Auth**: Firebase Admin SDK
- **Storage**: Google Cloud Storage
- **OCR**: Google Document AI
- **Conversion**: LibreOffice headless
- **PDF Processing**: pdfminer.six
- **Word Processing**: python-docx

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- Google Cloud Project with:
  - Document AI API enabled
  - Cloud Storage API enabled
  - Service account with appropriate permissions
- Firebase Project (optional, for authentication)
- LibreOffice (for local development)

## Setup

### 1. Clone and Navigate

```bash
cd backend
```

### 2. Install Dependencies

#### Using Python (Local Development)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Using Docker

```bash
# Build Docker image
docker build -t pdf-to-word-backend .

# Run container
docker run -p 8080:8080 --env-file .env pdf-to-word-backend
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:
- `PROJECT_ID`: Your Google Cloud Project ID (e.g., `564572183797`)
- `GCS_OUTPUT_BUCKET`: Cloud Storage bucket for converted files
- `DOCAI_PROCESSOR_ID`: Document AI processor ID (e.g., `ffaa7bcd30a9c788` for pdf-to-word-docai processor)
- `DOCAI_LOCATION`: Document AI location (usually `us`)
- `FIREBASE_PROJECT_ID`: Firebase project ID (optional)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON key

### 4. Setup Google Cloud Services

#### Create GCS Buckets

```bash
gsutil mb -p YOUR_PROJECT_ID gs://YOUR_INPUT_BUCKET
gsutil mb -p YOUR_PROJECT_ID gs://YOUR_OUTPUT_BUCKET
```

#### Create Document AI Processor

1. Go to [Document AI Console](https://console.cloud.google.com/ai/document-ai)
2. Create a new processor (use "Document OCR" or "Form Parser")
3. Note the Processor ID and Location

#### Setup Service Account

1. Create a service account in GCP Console
2. Grant roles:
   - `Storage Admin` (for GCS)
   - `Document AI API User`
   - `Firebase Admin SDK Administrator Service Agent` (if using Firebase)
3. Download JSON key file
4. Set `GOOGLE_APPLICATION_CREDENTIALS` to the key file path

### 5. Initialize Firebase (Optional)

If using Firebase Authentication:

```bash
# Install Firebase CLI (if not installed)
npm install -g firebase-tools

# Login and initialize
firebase login
firebase init
```

## Running Locally

### Without Docker

```bash
# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
export PROJECT_ID="your-project-id"
# ... set other variables

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### With Docker

```bash
docker build -t pdf-to-word-backend .
docker run -p 8080:8080 --env-file .env pdf-to-word-backend
```

The API will be available at `http://localhost:8080`

## API Endpoints

### Health Check

```bash
curl -X POST http://localhost:8080/api/health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T00:00:00"
}
```

### Convert PDF to Word

**Basic request (without authentication):**

```bash
curl -X POST "http://localhost:8080/api/convert/pdf-to-word" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**With Firebase authentication:**

```bash
curl -X POST "http://localhost:8080/api/convert/pdf-to-word" \
  -H "Authorization: Bearer YOUR_FIREBASE_ID_TOKEN" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "status": "success",
  "download_url": "https://storage.googleapis.com/your-bucket/550e8400-e29b-41d4-a716-446655440000.docx?X-Goog-Algorithm=...",
  "used_docai": false,
  "pages": 5,
  "conversion_time_ms": 1234,
  "file_size_bytes": 45678
}
```

## Frontend Integration Examples

### JavaScript/TypeScript Example

```javascript
// Example: Upload PDF and convert to Word
async function convertPdfToWord(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  // Optional: Add Firebase token if authenticated
  const token = await getFirebaseToken(); // Your Firebase auth function
  
  try {
    const response = await fetch('http://localhost:8080/api/convert/pdf-to-word', {
      method: 'POST',
      headers: {
        // Don't set Content-Type header - browser will set it with boundary
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Conversion failed');
    }
    
    const result = await response.json();
    
    if (result.status === 'success') {
      // Download the converted file
      window.location.href = result.download_url;
      
      // Or download programmatically:
      // const a = document.createElement('a');
      // a.href = result.download_url;
      // a.download = 'converted.docx';
      // a.click();
      
      console.log(`Conversion completed in ${result.conversion_time_ms}ms`);
      console.log(`Used Document AI: ${result.used_docai}`);
      console.log(`Pages: ${result.pages}`);
    }
  } catch (error) {
    console.error('Conversion error:', error);
  }
}

// Usage with file input
document.getElementById('pdf-input').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file && file.type === 'application/pdf') {
    convertPdfToWord(file);
  }
});
```

### React Example

```jsx
import { useState } from 'react';

function PdfToWordConverter() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };
  
  const handleConvert = async () => {
    if (!file) return;
    
    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      // Get Firebase token if authenticated
      const token = await getFirebaseToken();
      
      const response = await fetch('http://localhost:8080/api/convert/pdf-to-word', {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setResult(data);
        // Auto-download
        window.location.href = data.download_url;
      } else {
        setError(data.error || 'Conversion failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <input type="file" accept=".pdf" onChange={handleFileChange} />
      <button onClick={handleConvert} disabled={!file || loading}>
        {loading ? 'Converting...' : 'Convert to Word'}
      </button>
      {error && <div className="error">{error}</div>}
      {result && (
        <div className="result">
          <p>Conversion successful!</p>
          <p>Time: {result.conversion_time_ms}ms</p>
          <p>Pages: {result.pages}</p>
          <a href={result.download_url}>Download Word Document</a>
        </div>
      )}
    </div>
  );
}
```

### Python Example (Client)

```python
import requests

def convert_pdf_to_word(pdf_path, firebase_token=None):
    """Convert PDF to Word using the API."""
    url = "http://localhost:8080/api/convert/pdf-to-word"
    
    headers = {}
    if firebase_token:
        headers["Authorization"] = f"Bearer {firebase_token}"
    
    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path, f, "application/pdf")}
        response = requests.post(url, headers=headers, files=files)
    
    if response.status_code == 200:
        result = response.json()
        if result["status"] == "success":
            print(f"Conversion successful! Download URL: {result['download_url']}")
            # Download the file
            download_response = requests.get(result["download_url"])
            with open("output.docx", "wb") as out:
                out.write(download_response.content)
            return result
    else:
        print(f"Error: {response.json()}")
        return None
```

## Deployment

### Google Cloud Run

1. **Build and push Docker image**:

```bash
# Set variables
export PROJECT_ID="your-project-id"
export SERVICE_NAME="pdf-to-word-converter"
export REGION="us-central1"

# Build and tag
docker build -t gcr.io/${PROJECT_ID}/${SERVICE_NAME} .
docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}
```

2. **Deploy to Cloud Run**:

```bash
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 540 \
  --set-env-vars PROJECT_ID=${PROJECT_ID},GCS_OUTPUT_BUCKET=your-bucket,DOCAI_PROCESSOR_ID=your-processor-id
```

Or use the Cloud Run web console to deploy with environment variables.

3. **Set secrets** (if needed):

```bash
# Create secret for service account key
gcloud secrets create gcp-key --data-file=path/to/key.json

# Grant access
gcloud secrets add-iam-policy-binding gcp-key \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Using GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/setup-gcloud@v1
      - uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - run: |
          gcloud builds submit --tag gcr.io/$PROJECT_ID/pdf-to-word-converter
          gcloud run deploy pdf-to-word-converter \
            --image gcr.io/$PROJECT_ID/pdf-to-word-converter \
            --region us-central1
```

### Using Vercel (Serverless Functions)

Note: Vercel has limitations with long-running processes. For heavy PDF processing, Cloud Run is recommended.

For Vercel deployment, you may need to adapt the code to use serverless functions and external processing services.

## Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration management
│   ├── auth.py          # Firebase authentication
│   ├── storage.py       # GCS operations
│   ├── converter.py     # PDF conversion logic
│   ├── docai_client.py  # Document AI client
│   ├── models.py        # Pydantic models
│   └── utils.py         # Utility functions
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
└── README.md
```

### Testing

```bash
# Run tests (if available)
pytest

# Test API locally
python -m pytest tests/
```

### Logging

Logs are configured to output to stdout/stderr for Cloud Run compatibility.

## Troubleshooting

### LibreOffice not found

Ensure LibreOffice is installed:
- Linux: `sudo apt-get install libreoffice`
- Docker: Included in Dockerfile
- Windows/Mac: Install from [LibreOffice website](https://www.libreoffice.org/)

### Document AI errors

- Verify processor ID and location are correct
- Ensure Document AI API is enabled in your project
- Check service account has `Document AI API User` role

### GCS upload errors

- Verify bucket names and permissions
- Check service account has `Storage Admin` role
- Ensure buckets exist in the same project

### Firebase auth errors

- Verify Firebase Admin SDK is initialized
- Check `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Ensure service account has Firebase Admin permissions

## Code Examples

### Example: pdf_has_text Implementation

The `pdf_has_text` function uses pdfminer.six to check for extractable text:

```python
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

def pdf_has_text(pdf_path: str, max_pages_to_check: int = 3) -> bool:
    laparams = LAParams()
    text = extract_text(pdf_path, maxpages=max_pages_to_check, laparams=laparams)
    cleaned_text = text.strip().replace('\n', '').replace(' ', '')
    return len(cleaned_text) > 50  # At least 50 characters
```

### Example: LibreOffice Subprocess Call

```python
import subprocess

cmd = [
    "soffice",
    "--headless",
    "--convert-to", "docx",
    "--outdir", "/tmp",
    "input.pdf"
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
if result.returncode != 0:
    raise Exception(f"Conversion failed: {result.stderr}")
```

### Example: Document AI Paragraph Iteration

```python
from docx import Document

doc = Document()
for page_num, page_blocks in enumerate(parsed_doc.pages, start=1):
    if page_num > 1:
        doc.add_page_break()
    
    for block in page_blocks:
        if block.is_heading:
            doc.add_heading(block.text, level=2)
        else:
            doc.add_paragraph(block.text)

doc.save("output.docx")
```

## Document AI Processor Setup

Based on your GCP project, you may have multiple Document AI processors. Common ones include:

- **pdf-to-word-docai**: `ffaa7bcd30a9c788` (recommended for PDF to Word conversion)
- **form-parser-docai**: `9d1bf7e36946b781` (for form extraction)
- **layout-parser-docai**: `c79eead38f3ecc38` (for layout analysis)

To find your processor ID:
1. Go to [Document AI Console](https://console.cloud.google.com/ai/document-ai/processors)
2. Select your processor
3. Copy the Processor ID from the details page
4. Use it in your `.env` file as `DOCAI_PROCESSOR_ID`

## License

This project is provided as-is for production use.

## Support

For issues and questions, please check:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Document AI Documentation](https://cloud.google.com/document-ai/docs)
- [Python-docx Documentation](https://python-docx.readthedocs.io/)
