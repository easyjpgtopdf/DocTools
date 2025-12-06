# Background Removal Service - BiRefNet GPU

Google Cloud Run service for AI-powered background removal using BiRefNet model.

## Features

- **Free Preview**: 512px output using BiRefNet GPU
- **Premium HD**: 2000-4000px output using BiRefNet GPU High-Resolution
- **GPU Accelerated**: Uses NVIDIA L4 GPU for fast processing
- **Scalable**: Auto-scales from 0 to 5 instances based on demand

## API Endpoints

### Health Check
```
GET /health
```

### Free Preview (512px)
```
POST /api/free-preview-bg
Content-Type: application/json

{
  "imageData": "data:image/jpeg;base64,...",
  "maxSize": 512
}
```

### Premium HD (2000-4000px)
```
POST /api/premium-bg
Content-Type: application/json

{
  "imageData": "data:image/jpeg;base64,...",
  "minSize": 2000,
  "maxSize": 4000,
  "userId": "user123"
}
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Or with gunicorn
gunicorn --bind 0.0.0.0:8080 app:app
```

## Deployment to Google Cloud Run

### Prerequisites
- Google Cloud SDK installed
- Docker installed
- Project with billing enabled
- GPU quota enabled

### Deploy

```bash
# Make script executable
chmod +x deploy-cloudrun.sh

# Deploy
./deploy-cloudrun.sh YOUR_PROJECT_ID us-central1
```

### Manual Deployment

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and push
docker build -t gcr.io/YOUR_PROJECT_ID/bg-removal-birefnet .
docker push gcr.io/YOUR_PROJECT_ID/bg-removal-birefnet

# Deploy
gcloud run deploy bg-removal-birefnet \
  --image gcr.io/YOUR_PROJECT_ID/bg-removal-birefnet \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 8Gi \
  --cpu 2 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 5 \
  --add-gpu type=nvidia-l4 \
  --gpu-count 1 \
  --concurrency 1
```

## Configuration

### Environment Variables
- `PORT`: Server port (default: 8080)

### GPU Requirements
- NVIDIA L4 GPU
- 8GB RAM minimum
- 2 vCPU minimum

## Cost

- **GPU**: $0.35/hour (on-demand, only when processing)
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GB-second

See `BACKGROUND_REMOVAL_SETUP_COST.md` for detailed cost analysis.

## Monitoring

Check logs:
```bash
gcloud run services logs read bg-removal-birefnet --region us-central1
```

## Troubleshooting

### Model Download Issues
The BiRefNet model is downloaded automatically on first use. If download fails:
1. Check internet connectivity
2. Verify GPU availability
3. Check Cloud Run logs

### GPU Not Available
Ensure:
1. GPU quota is enabled in your project
2. Region supports L4 GPUs (us-central1, us-east1, etc.)
3. Billing is enabled

## License

See main project license.

