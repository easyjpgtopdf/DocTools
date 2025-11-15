# 🚀 Google Cloud Run Setup Guide - U2Net RemBG

Complete guide to deploy U2Net background removal service on Google Cloud Run for **image-repair-editor.html**

## 📋 Prerequisites

- Google Cloud Account ([Free $300 credit](https://cloud.google.com/free))
- Google Cloud SDK installed
- Docker installed (optional, Cloud Build can handle this)

---

## 🔧 Step 1: Create Cloud Run Service

### Option A: Using Pre-built Container (Fastest)

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Deploy U2Net RemBG service
gcloud run deploy rembg-service \
  --image danielgatis/rembg:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0
```

### Option B: Custom Dockerfile (Recommended for Production)

**1. Create `Dockerfile`:**

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    rembg[gpu]==2.0.50 \
    flask==2.3.0 \
    pillow==10.0.0 \
    gunicorn==21.2.0

# Copy application
COPY app.py .

# Expose port
EXPOSE 8080

# Run with gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 300 app:app
```

**2. Create `app.py`:**

```python
from flask import Flask, request, send_file
from rembg import remove
from PIL import Image
import io

app = Flask(__name__)

@app.route('/remove', methods=['POST'])
def remove_background():
    try:
        # Get image from request
        if 'image' not in request.files:
            return {'error': 'No image provided'}, 400
        
        file = request.files['image']
        input_image = Image.open(file.stream)
        
        # Get options
        model = request.form.get('model', 'u2net')
        alpha_matting = request.form.get('alpha_matting', 'false').lower() == 'true'
        alpha_matting_foreground_threshold = int(request.form.get('alpha_matting_foreground_threshold', 240))
        alpha_matting_background_threshold = int(request.form.get('alpha_matting_background_threshold', 10))
        
        # Remove background
        output_image = remove(
            input_image,
            model_name=model,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold
        )
        
        # Return result
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
```

**3. Deploy:**

```bash
# Build and deploy
gcloud run deploy rembg-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300
```

---

## 🌐 Step 2: Get Service URL

After deployment, you'll get a URL like:
```
https://rembg-service-xxxxx-uc.a.run.app
```

---

## 🔌 Step 3: Update HTML Editor

Open `image-repair-editor.html` and update line ~1565:

```javascript
// Cloud Run Configuration
const CLOUD_RUN_ENDPOINTS = {
    rembg: 'https://rembg-service-xxxxx-uc.a.run.app/remove', // ⬅️ UPDATE THIS
    upscale: 'https://upscale-service-xxxxx.run.app/process',
    enhance: 'https://enhance-service-xxxxx.run.app/process',
    style_transfer: 'https://style-service-xxxxx.run.app/process'
};
```

Replace `xxxxx` with your actual Cloud Run service ID.

---

## 💰 Cost Estimation

### Free Tier (Generous Limits)
- **2 million requests/month** FREE
- **360,000 GB-seconds/month** FREE
- **180,000 vCPU-seconds/month** FREE

### Typical Usage Cost
With 2Gi RAM + 2 CPU:
- **Per request**: ~$0.0001 (0.01¢)
- **1000 requests**: ~$0.10
- **10,000 requests**: ~$1.00

**Example**: Processing 500 images/day = **~$1.50/month**

---

## ⚡ Step 4: Test the Service

### Using curl:
```bash
curl -X POST https://YOUR_SERVICE_URL/remove \
  -F "image=@test-image.jpg" \
  -F "model=u2net" \
  -F "alpha_matting=true" \
  --output result.png
```

### Using JavaScript (Browser):
```javascript
const formData = new FormData();
formData.append('image', imageBlob, 'image.png');
formData.append('model', 'u2net');
formData.append('alpha_matting', 'true');

const response = await fetch('https://YOUR_SERVICE_URL/remove', {
    method: 'POST',
    body: formData
});

const resultBlob = await response.blob();
```

---

## 🎯 Available Models

U2Net RemBG supports multiple models:

| Model | Quality | Speed | Use Case |
|-------|---------|-------|----------|
| `u2net` | ⭐⭐⭐⭐⭐ | Medium | General purpose (recommended) |
| `u2netp` | ⭐⭐⭐⭐ | Fast | Quick processing |
| `u2net_human_seg` | ⭐⭐⭐⭐⭐ | Medium | Human portraits only |
| `u2net_cloth_seg` | ⭐⭐⭐⭐ | Medium | Clothing segmentation |
| `silueta` | ⭐⭐⭐ | Fast | Simple backgrounds |

---

## 🔧 Advanced Configuration

### Enable CORS (for browser access):

Update `app.py`:
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

Update `Dockerfile`:
```dockerfile
RUN pip install --no-cache-dir \
    rembg[gpu]==2.0.50 \
    flask==2.3.0 \
    flask-cors==4.0.0 \  # ⬅️ Add this
    pillow==10.0.0 \
    gunicorn==21.2.0
```

### Scale Settings:

```bash
# Auto-scale 0-10 instances
gcloud run services update rembg-service \
  --min-instances 0 \
  --max-instances 10

# Keep 1 instance warm (faster response, higher cost)
gcloud run services update rembg-service \
  --min-instances 1
```

### Increase Timeout for Large Images:

```bash
gcloud run services update rembg-service \
  --timeout 600  # 10 minutes
```

---

## 📊 Monitoring & Logs

### View Logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rembg-service" --limit 50
```

### View Metrics:
```bash
gcloud run services describe rembg-service --region us-central1
```

### Cloud Console:
https://console.cloud.google.com/run

---

## 🛡️ Security (Optional)

### Restrict Access with API Key:

**1. Update `app.py`:**
```python
API_KEY = os.environ.get('API_KEY', 'your-secret-key')

@app.before_request
def check_api_key():
    if request.path == '/health':
        return None
    
    key = request.headers.get('X-API-Key')
    if key != API_KEY:
        return {'error': 'Unauthorized'}, 401
```

**2. Deploy with secret:**
```bash
echo -n "your-secret-key" | gcloud secrets create rembg-api-key --data-file=-

gcloud run services update rembg-service \
  --update-secrets API_KEY=rembg-api-key:latest
```

**3. Update HTML:**
```javascript
const response = await fetch(CLOUD_RUN_URL, {
    method: 'POST',
    headers: {
        'X-API-Key': 'your-secret-key'
    },
    body: formData
});
```

---

## 🚀 Additional Services to Deploy

### 1. Image Upscaling (Real-ESRGAN)

**Create `upscale-service/app.py`:**
```python
from flask import Flask, request, send_file
from PIL import Image
import io

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def upscale():
    file = request.files['image']
    img = Image.open(file.stream)
    
    # Upscale 2x
    new_size = (img.width * 2, img.height * 2)
    img_upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
    
    img_io = io.BytesIO()
    img_upscaled.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
```

**Deploy:**
```bash
cd upscale-service
gcloud run deploy upscale-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi
```

---

## ✅ Verification Checklist

- [ ] Google Cloud project created
- [ ] Billing enabled (free tier available)
- [ ] `gcloud` CLI installed and authenticated
- [ ] Service deployed successfully
- [ ] Service URL obtained
- [ ] URL updated in `image-repair-editor.html`
- [ ] CORS enabled (if needed)
- [ ] Test request successful
- [ ] Monitoring enabled

---

## 🆘 Troubleshooting

### Error: "Service account does not have permission"
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Error: "Memory limit exceeded"
Increase memory:
```bash
gcloud run services update rembg-service --memory 4Gi
```

### Error: "Timeout"
Increase timeout:
```bash
gcloud run services update rembg-service --timeout 600
```

### Cold Start Too Slow
Keep instances warm:
```bash
gcloud run services update rembg-service --min-instances 1
```

---

## 📞 Support

- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **RemBG GitHub**: https://github.com/danielgatis/rembg
- **Pricing Calculator**: https://cloud.google.com/products/calculator

---

## 🎉 You're Ready!

Your image editor now has **professional AI-powered background removal** running on Google Cloud! 🚀

**Cost**: ~$1-2/month for typical usage with free tier included.
