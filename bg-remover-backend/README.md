# Background Remover Backend

**Hybrid Free + Paid Solution** for processing images of all sizes using Rembg AI.

## Architecture

### **Render (Python/Flask)** - Free for 15-50 MB
- **No Docker needed** - Direct Python deployment
- **Free tier**: 750 hours/month
- **Memory**: 512 MB
- **Best for**: Medium files (15-50 MB)

### **Google Cloud Run (Docker)** - Paid for 50+ MB
- **Docker container** - Scalable infrastructure
- **Pay per use**: ~$0.40 per 1 million requests
- **Memory**: 2 GB (configurable)
- **Best for**: Large files (50-100 MB)

---

## Deployment Instructions

### Option 1: Render (Free, Python Direct)

#### Quick Deploy
1. Push this folder to GitHub
2. Go to [render.com](https://render.com)
3. Sign up with GitHub
4. Click "New +" → "Web Service"
5. Connect repository
6. Settings:
   - **Name**: bg-remover-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan**: Free
7. Deploy!

**Your Render URL**: `https://bg-remover-api-xxxx.onrender.com`

---

### Option 2: Google Cloud Run (Paid, Docker)

#### Prerequisites
1. Google Cloud account with billing enabled
2. Install [gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. Docker installed locally (for testing)

#### Setup Steps

**1. Enable Required APIs**
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

**2. Set Project ID**
```bash
gcloud config set project YOUR-PROJECT-ID
```

**3. Build and Deploy**
```bash
# Build Docker image
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/bg-remover-api

# Deploy to Cloud Run
gcloud run deploy bg-remover-api \
  --image gcr.io/YOUR-PROJECT-ID/bg-remover-api \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --allow-unauthenticated
```

**4. Get Your Service URL**
```bash
gcloud run services describe bg-remover-api --region us-central1 --format 'value(status.url)'
```

**Your Cloud Run URL**: `https://bg-remover-api-xxxxx-uc.a.run.app`

#### Cost Optimization
- **Free tier**: First 2 million requests/month
- **After free tier**: ~$0.40 per 1M requests
- **Memory**: 2GB @ $0.0000025/GB-second
- **CPU**: 2 vCPU @ $0.00002400/vCPU-second
- **Cold start**: Free (first request may be slow)

#### Estimated Costs
- **100 requests/day**: FREE (within free tier)
- **1,000 requests/day**: ~$5/month
- **10,000 requests/day**: ~$50/month

---

## API Endpoints

### Health Check
```bash
GET /health
Response: {"status": "healthy", "service": "render" | "cloudrun"}
```

### Remove Background (Base64)
```bash
POST /remove-background
Content-Type: application/json

Body: {
  "imageData": "data:image/jpeg;base64,/9j/4AAQ..."
}

Response: {
  "success": true,
  "resultImage": "data:image/png;base64,...",
  "outputSizeMB": 2.5,
  "processedWith": "Render - Rembg AI" | "Google Cloud Run - Rembg AI"
}
```

### Remove Background (File Upload)
```bash
POST /remove-background
Content-Type: multipart/form-data

Body: image file (max 50 MB for Render, 100 MB for Cloud Run)

Response: {
  "success": true,
  "resultImage": "data:image/png;base64,...",
  "outputSizeMB": 2.5
}
```

---

## Testing Locally

### Render Setup (Python)
```bash
pip install -r requirements.txt
python app.py
# Server: http://localhost:10000
```

### Cloud Run Setup (Docker)
```bash
docker build -t bg-remover-api -f Dockerfile .
docker run -p 8080:8080 bg-remover-api
# Server: http://localhost:8080
```

---

## Performance Comparison

### Render (Free)
- **15-20 MB**: ~10-15 seconds
- **20-35 MB**: ~15-25 seconds
- **35-50 MB**: ~25-40 seconds
- **Cold start**: ~30 seconds (after 15 min sleep)

### Cloud Run (Paid)
- **50-70 MB**: ~20-35 seconds
- **70-90 MB**: ~35-50 seconds
- **90-100 MB**: ~50-70 seconds
- **Cold start**: ~10-15 seconds (optimized)

---

## Environment Variables

### Render
- `PORT`: Auto-set by Render (10000 default)
- `PYTHON_VERSION`: 3.11.0

### Cloud Run
- `PORT`: Auto-set by Cloud Run (8080)
- `PYTHONUNBUFFERED`: 1 (for better logging)

---

## Troubleshooting

### Render Issues
- **Timeout**: Increase in `Procfile` (`--timeout 120`)
- **Memory**: Upgrade to paid plan ($7/month for 1GB)
- **Sleep**: First request slow (cold start ~30s)

### Cloud Run Issues
- **Memory**: Increase in deploy command (`--memory 4Gi`)
- **Timeout**: Increase in deploy command (`--timeout 600`)
- **Billing**: Ensure billing is enabled in GCP console

---

## Recommendation

**Start with Render (Free)**
- Deploy for 15-50 MB files
- No costs, easy setup
- Upgrade to Cloud Run later when needed for 50+ MB files

**Add Cloud Run When**
- Users upload files > 50 MB frequently
- Need faster processing
- Have budget for scalability (~$5-50/month depending on usage)
