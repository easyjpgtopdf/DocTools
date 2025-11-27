# PDF Editor Backend

Backend server for PDF editor with OCR, editing, and cloud integration.

## Project Structure

```
server/
├── config/
│   └── google-cloud.js          # Google Cloud configuration
├── controllers/
│   ├── pdfController.js         # PDF operations controller
│   └── pagesController.js       # Page management controller
├── middleware/
│   └── upload.js                # File upload middleware
├── routes/
│   ├── pdf.js                   # PDF API routes
│   └── pages.js                 # Page management routes
├── api/
│   ├── pdf-edit/                # PDF editing modules
│   └── pdf-ocr/                 # OCR modules
├── uploads/                     # Uploaded files directory
├── server.js                    # Main server file
├── package.json                 # Dependencies
└── .env.example                 # Environment variables example
```

## Installation

```bash
npm install
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Set up Google Cloud credentials:
   - Add `GOOGLE_CLOUD_SERVICE_ACCOUNT` or `FIREBASE_SERVICE_ACCOUNT` to `.env`
   - Or set `GOOGLE_APPLICATION_CREDENTIALS` to point to a JSON file

## Running the Server

### Development
```bash
npm run dev
```

### Production
```bash
npm start
```

## API Endpoints

### PDF Operations

- `POST /api/pdf/upload` - Upload PDF file
- `POST /api/pdf/edit` - Edit PDF (text, images)
- `POST /api/pdf/ocr` - Perform OCR on PDF page
- `POST /api/pdf/ocr/batch` - Batch OCR on multiple pages
- `POST /api/pdf/download` - Download edited PDF
- `GET /api/pdf/status` - Check server status
- `GET /api/pdf/ocr/status` - Check OCR service status

### Page Management

- `POST /api/pdf/pages/rotate` - Rotate pages
- `POST /api/pdf/pages/delete` - Delete pages
- `POST /api/pdf/pages/reorder` - Reorder pages
- `POST /api/pdf/pages/extract` - Extract pages
- `POST /api/pdf/pages/add` - Add new page

## Dependencies

- **express** - Web framework
- **cors** - Cross-origin resource sharing
- **multer** - File upload handling
- **pdf-lib** - PDF manipulation
- **pdfjs-dist** - PDF rendering
- **canvas** - Image conversion
- **@google-cloud/vision** - Google Cloud Vision API
- **firebase-admin** - Firebase Admin SDK
- **dotenv** - Environment variables

## Environment Variables

See `.env.example` for all available configuration options.

## Error Handling

All endpoints return JSON responses with `success` and `error` fields:

```json
{
  "success": false,
  "error": "Error message here"
}
```

## Rate Limiting

OCR endpoints include rate limiting (100 requests per minute per client).

## License

MIT
