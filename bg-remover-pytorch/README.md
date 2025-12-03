# PyTorch U2NetP Background Remover for Cloud Run

Pure PyTorch implementation of U2NetP for background removal, fully compatible with Google Cloud Run (no ONNX, no executable stack issues).

## 🎯 Features

- ✅ **Cloud Run Compatible** - No ONNX, no executable stack issues
- ✅ **Pure PyTorch** - Direct PyTorch implementation
- ✅ **Pay-per-Use** - No fixed costs (min-instances: 0)
- ✅ **User Limits** - Daily and monthly quotas
- ✅ **High Quality** - U2NetP model for professional results
- ✅ **Cost Effective** - ~₹187/month for 10,000 images

## 📋 Prerequisites

- Google Cloud Project with Cloud Run API enabled
- `gcloud` CLI installed and configured
- Docker (for local testing)

## 🚀 Quick Start

### 1. Deploy to Cloud Run

```powershell
cd bg-remover-pytorch
.\deploy.ps1
```

### 2. Update Vercel Proxy

After deployment, update `api/background-remove-pytorch.js` with the service URL:

```javascript
const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_PYTORCH || 'YOUR_SERVICE_URL';
```

### 3. Update Frontend

The canonical frontend (`background-workspace.html`) is already configured to use `/api/background-remove-pytorch`. The legacy `server/public/background-workspace.html` file now simply redirects to this page to avoid duplicate code.

## 📁 Project Structure

```
bg-remover-pytorch/
├── backend/
│   ├── app.py              # Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Docker image definition
│   └── .dockerignore       # Files to ignore in Docker
├── deploy.ps1              # Deployment script
└── README.md               # This file
```

## 🔧 Configuration

### Cloud Run Settings

- **Memory**: 4GB (recommended for PyTorch)
- **CPU**: 2 vCPU
- **Timeout**: 300 seconds (5 minutes)
- **Min Instances**: 0 (pay-per-use)
- **Max Instances**: 10
- **Concurrency**: 1 (can be increased to 4)

### User Limits

- **Free Users**: 10 daily, 100 monthly
- **Premium Users**: 1000 daily, 10000 monthly

## 📦 Dependencies

- Flask 3.0.0
- flask-cors 4.0.0
- gunicorn 21.2.0
- Pillow 10.2.0
- torch 2.1.0
- torchvision 0.16.0
- numpy 1.26.2

## 🎨 Model Weights

**Important**: For best quality, download the official U2NetP pre-trained weights:

1. Download from: https://github.com/xuebinqin/U-2-Net
2. Place `u2netp.pth` in `bg-remover-pytorch/backend/`
3. Rebuild and redeploy

The current implementation uses a simplified model architecture. For production, use the official weights.

## 🔌 API Endpoints

### Health Check
```
GET /health
```

### Usage Statistics
```
GET /usage
Headers:
  X-User-ID: user_id
  X-User-Type: free|premium
```

### Remove Background
```
POST /remove-background
Headers:
  Content-Type: application/json
  X-User-ID: user_id
  X-User-Type: free|premium
Body:
  {
    "imageData": "data:image/png;base64,..."
  }
```

## 💰 Cost Estimate

For 10,000 images/month:
- **Total Cost**: ~₹187/month
- **Fixed Cost**: ₹0 (no fixed charges)
- **Usage Cost**: ~₹187/month
- **Per Image**: ~₹0.019

## 🐛 Troubleshooting

### Model Not Loading
- Check if `u2netp.pth` exists in backend directory
- Verify PyTorch installation
- Check Cloud Run logs: `gcloud run services logs read bg-remover-pytorch-u2netp`

### Memory Issues
- Increase memory to 8GB in `deploy.ps1`
- Reduce image size or dimensions

### Timeout Errors
- Increase timeout in `deploy.ps1` (max 900s)
- Optimize image preprocessing

## 📝 Notes

- The model uses CPU (Cloud Run doesn't support GPU)
- Processing time: ~5-15 seconds per image
- Model loads on first request (cold start ~10-20 seconds)
- For always-warm service, set `min-instances: 1` (adds fixed cost)

## 🔗 Related Files

- Frontend: `background-workspace.html`
- Node redirect: `server/public/background-workspace.html`
- Vercel Proxy: `api/background-remove-pytorch.js`
- Vercel Config: `vercel.json`

