# 🚀 Google Cloud Run Deployment Guide
## Background Remover Backend - Step by Step

### 📋 Prerequisites

1. **Install Google Cloud SDK**
   - Download: https://cloud.google.com/sdk/docs/install
   - Install and run: `gcloud init`

2. **Authenticate**
   ```powershell
   gcloud auth login
   ```

3. **Set Project**
   ```powershell
   gcloud config set project easyjpgtopdf-de346
   ```

---

## 🎯 Method 1: Using PowerShell Script (Easiest - Windows)

### Step 1: Navigate to backend directory
```powershell
cd C:\Users\apnao\Downloads\DocTools\bg-remover-backend
```

### Step 2: Run deployment script
```powershell
.\deploy-cloudrun.ps1
```

**Script automatically:**
- ✅ Checks gcloud installation
- ✅ Verifies authentication
- ✅ Sets project
- ✅ Enables required APIs
- ✅ Builds Docker image (8-12 minutes)
- ✅ Deploys to Cloud Run
- ✅ Shows service URL

---

## 🎯 Method 2: Manual Deployment (Step by Step)

### Step 1: Navigate to backend directory
```powershell
cd C:\Users\apnao\Downloads\DocTools\bg-remover-backend
```

### Step 2: Verify gcloud is installed
```powershell
gcloud --version
```

### Step 3: Authenticate (if not already)
```powershell
gcloud auth login
```

### Step 4: Set project
```powershell
gcloud config set project easyjpgtopdf-de346
```

### Step 5: Enable required APIs
```powershell
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 6: Build Docker image
```powershell
gcloud builds submit --tag gcr.io/easyjpgtopdf-de346/bg-remover-api .
```
⏳ **Time:** 8-12 minutes (first time may take longer)

### Step 7: Deploy to Cloud Run
```powershell
gcloud run deploy bg-remover-api `
  --image gcr.io/easyjpgtopdf-de346/bg-remover-api `
  --platform managed `
  --region us-central1 `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --allow-unauthenticated
```

### Step 8: Get Service URL
```powershell
gcloud run services describe bg-remover-api --region us-central1 --format="value(status.url)"
```

---

## 🎯 Method 3: Using Google Cloud Console (Web UI)

### Step 1: Go to Cloud Run Console
- Visit: https://console.cloud.google.com/run
- Select project: `easyjpgtopdf-de346`

### Step 2: Select Service
- Click on `bg-remover-api` service

### Step 3: Edit & Deploy New Revision
- Click "EDIT & DEPLOY NEW REVISION"
- Go to "Container" tab
- Click "SELECT" next to Container image URL
- Choose the latest image from Container Registry
- Click "DEPLOY"

### Step 4: Wait for Deployment
- Deployment takes 2-5 minutes
- Service URL will be shown after deployment

---

## ✅ After Deployment

### 1. Copy Service URL
The deployment will show a URL like:
```
https://bg-remover-api-xxxxx-uc.a.run.app
```

### 2. Update Frontend Code
Update `background-workspace.html` line 570:
```javascript
const CLOUDRUN_API_URL = 'https://bg-remover-api-xxxxx-uc.a.run.app/remove-background';
```

### 3. Test
- Upload an image in background-workspace.html
- Check if background removal works
- Verify no "model_name" error

---

## 🔍 Troubleshooting

### Error: "gcloud: command not found"
**Solution:** Install Google Cloud SDK
- Download: https://cloud.google.com/sdk/docs/install

### Error: "Permission denied"
**Solution:** Authenticate
```powershell
gcloud auth login
```

### Error: "Project not found"
**Solution:** Set correct project
```powershell
gcloud config set project easyjpgtopdf-de346
```

### Error: "API not enabled"
**Solution:** Enable APIs
```powershell
gcloud services enable cloudbuild.googleapis.com run.googleapis.com
```

### Build fails
**Solution:** Check logs
```powershell
gcloud builds list --limit=1
gcloud builds log <BUILD_ID>
```

### Deployment fails
**Solution:** Check service logs
```powershell
gcloud run services logs read bg-remover-api --region us-central1
```

---

## 📊 Monitor Deployment

### View Logs
```powershell
gcloud run services logs read bg-remover-api --region us-central1 --limit=50
```

### Check Service Status
```powershell
gcloud run services describe bg-remover-api --region us-central1
```

### View in Console
https://console.cloud.google.com/run/detail/us-central1/bg-remover-api

---

## 🎉 Success Indicators

✅ Build completes without errors
✅ Deployment shows "Service deployed successfully"
✅ Service URL is accessible
✅ Health check endpoint works: `https://SERVICE_URL/health`
✅ Background removal works without "model_name" error

---

## 💡 Quick Commands Reference

```powershell
# Check authentication
gcloud auth list

# Set project
gcloud config set project easyjpgtopdf-de346

# Build and deploy (one command)
cd bg-remover-backend
.\deploy-cloudrun.ps1

# View service URL
gcloud run services describe bg-remover-api --region us-central1 --format="value(status.url)"

# View logs
gcloud run services logs read bg-remover-api --region us-central1 --limit=20
```

---

## 📝 Notes

- **First deployment:** Takes 8-12 minutes (Docker image build)
- **Subsequent deployments:** Faster (2-5 minutes) if only code changed
- **Model download:** First request takes ~30 seconds (u2net model ~180MB)
- **Free tier:** 2 million requests/month
- **Cost:** ~$0.000024 per request after free tier

---

## 🔗 Useful Links

- Cloud Run Console: https://console.cloud.google.com/run
- Container Registry: https://console.cloud.google.com/gcr
- Cloud Build: https://console.cloud.google.com/cloud-build
- Service Logs: https://console.cloud.google.com/run/detail/us-central1/bg-remover-api/logs

