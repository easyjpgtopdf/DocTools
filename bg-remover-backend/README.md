# Background Remover Backend - Google Cloud Run

Professional AI background removal using Rembg U²-Net (latest version) with Google Cloud Run.

## Features

- ✅ Latest Rembg U²-Net model (auto-downloads on first run)
- ✅ Alpha matting for smooth edges
- ✅ Optimized to prevent over-cleaning
- ✅ Handles files up to 100 MB
- ✅ Free tier: 2M requests/month
- ✅ Fast processing with memory optimization

## Quick Deploy

### Prerequisites

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Authenticate: `gcloud auth login`
3. Set project: `gcloud config set project easyjpgtopdf-de346`

### Deploy

**Windows (PowerShell):**
```powershell
cd bg-remover-backend
.\deploy-cloudrun.ps1
```

**Linux/Mac:**
```bash
cd bg-remover-backend
chmod +x deploy-cloudrun.sh
./deploy-cloudrun.sh
```

## Manual Deployment

```bash
# Build Docker image
gcloud builds submit --tag gcr.io/easyjpgtopdf-de346/bg-remover-api .

# Deploy to Cloud Run
gcloud run deploy bg-remover-api \
  --image gcr.io/easyjpgtopdf-de346/bg-remover-api \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --allow-unauthenticated
```

## API Usage

### Endpoint
```
POST /remove-background
```

### Request (JSON)
```json
{
  "imageData": "data:image/png;base64,iVBORw0KGgo..."
}
```

### Response
```json
{
  "success": true,
  "resultImage": "data:image/png;base64,iVBORw0KGgo...",
  "outputSize": 123456,
  "outputSizeMB": 0.12,
  "processedWith": "Rembg U²-Net Latest + Alpha Matting",
  "model": "u2net"
}
```

## Configuration

- **Model**: u2net (latest, auto-downloads)
- **Max File Size**: 100 MB
- **Max Dimension**: 4096 pixels
- **Memory**: 2 GB
- **CPU**: 2 cores
- **Timeout**: 300 seconds

## Cost

- **Free Tier**: 2 million requests/month
- **After Free Tier**: ~$0.000024 per request
- **Storage**: Included in free tier

## Troubleshooting

### Build fails
- Check gcloud authentication: `gcloud auth list`
- Enable APIs: `gcloud services enable cloudbuild.googleapis.com run.googleapis.com`

### Slow first request
- Normal! Model downloads on first request (~180MB, ~30 seconds)
- Subsequent requests are fast

### Memory errors
- Increase memory in deployment: `--memory 4Gi`

## Model Information

- **Model**: u2net (latest version)
- **Auto-download**: Yes (on first request)
- **Size**: ~180 MB
- **Quality**: Professional, no over-cleaning
- **Speed**: Fast after initial download
