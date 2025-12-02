# Background Remover V2

High-quality AI-powered background removal service with user limits and professional processing.

## Features

- ✅ High-quality background removal using U²-Net model
- ✅ User limit system (daily/monthly limits)
- ✅ Professional alpha matting for smooth edges
- ✅ Large file support (up to 100MB)
- ✅ SEO optimized frontend
- ✅ Responsive design
- ✅ Real-time usage tracking

## Architecture

- **Backend**: Flask + Rembg (Python 3.9)
- **Frontend**: HTML5 + Vanilla JavaScript
- **Deployment**: Google Cloud Run (8GB RAM, 4 CPU)
- **Proxy**: Vercel Serverless Functions

## Directory Structure

```
bg-remover-v2/
├── backend/
│   ├── app.py              # Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile         # Docker configuration
│   └── .dockerignore      # Docker ignore file
├── frontend/
│   └── background-remover-v2.html  # Frontend page
├── deploy.ps1             # Deployment script
└── README.md              # This file
```

## Deployment

### Prerequisites

- Google Cloud SDK installed and configured
- Docker installed
- PowerShell (for Windows)

### Deploy Backend

```powershell
cd bg-remover-v2
.\deploy.ps1
```

### Deploy Frontend

Copy `frontend/background-remover-v2.html` to your web server or Vercel.

### Deploy Vercel Proxy

The proxy file is at `api/background-remove-v2.js`. It will be automatically deployed with Vercel.

## Configuration

### Backend Environment Variables

- `PORT`: Server port (default: 8080)
- `REMBG_MODEL`: Model name (default: u2net)
- `PYTHONUNBUFFERED`: Python output (default: 1)

### User Limits

Configured in `backend/app.py`:

```python
USER_LIMITS = {
    'free': {'daily': 10, 'monthly': 100},
    'premium': {'daily': 1000, 'monthly': 10000}
}
```

## API Endpoints

### Health Check
```
GET /health
```

### Remove Background
```
POST /remove-background
Content-Type: application/json
X-User-ID: <user_id>
X-User-Type: free|premium

{
  "imageData": "data:image/png;base64,..."
}
```

### Usage Statistics
```
GET /usage
X-User-ID: <user_id>
X-User-Type: free|premium
```

## Frontend Integration

The frontend page uses:
- `/api/background-remove-v2` - Main processing endpoint
- `/api/background-remove-v2/health` - Health check
- `/api/background-remove-v2/usage` - Usage statistics

## Troubleshooting

### Executable Stack Error

If you encounter `onnxruntime` executable stack errors, the Dockerfile includes a fix using `execstack -c`.

### Cold Start Issues

The service is configured with `min-instances: 1` to prevent cold starts. Warmup requests are sent every 10 minutes from the frontend.

### Memory Issues

The service is configured with 8GB memory. If you need more, update the `deploy.ps1` script.

## License

Same as main project.

