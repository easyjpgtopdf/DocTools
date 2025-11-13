# 🚀 Google Cloud Run Deployment - Step by Step (Hindi)

## ✨ Kya Milega?
- **100% Professional Quality** - Rembg U²-Net AI (Photopea jaisa)
- **No Over-Cleaning** - Alpha matting se perfect edges
- **Fast Processing** - 2GB RAM + 2 CPU
- **Free Tier** - 2 million requests/month FREE
- **Up to 100MB** files support

---

## 📋 Prerequisites (Pehle ye karo)

### 1. Google Cloud Account Banao
- Visit: https://cloud.google.com/free
- Sign up with Gmail
- Free $300 credit milega (3 months)
- Credit card add karna padega (but charge nahi hoga free tier me)

### 2. Google Cloud SDK Install Karo
**Windows:**
```powershell
# Download installer
Invoke-WebRequest -Uri https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe -OutFile gcloud-installer.exe

# Run installer
.\gcloud-installer.exe
```

**Ya Direct Download:**
https://cloud.google.com/sdk/docs/install

### 3. gcloud CLI Setup
```powershell
# Login karo
gcloud auth login

# Project banao (ya existing project ka ID use karo)
gcloud projects create doctools-bg-remover --name="DocTools Background Remover"

# Project set karo
gcloud config set project doctools-bg-remover

# Billing enable karo (free tier ke liye bhi zaruri hai)
# Visit: https://console.cloud.google.com/billing
# Link your project to billing account

# APIs enable karo
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

---

## 🚀 Deployment Steps

### Step 1: Code Ready Hai
```powershell
cd C:\Users\apnao\Downloads\DocTools\bg-remover-backend

# Check files
ls
# Dekhna chahiye:
# - Dockerfile ✅
# - app-cloudrun.py ✅
# - requirements-cloudrun.txt ✅
```

### Step 2: Docker Image Build Karo
```powershell
# PROJECT_ID replace karo apne project ID se
$PROJECT_ID = "doctools-bg-remover"
$SERVICE_NAME = "bg-remover-api"
$REGION = "us-central1"

# Build image (5-10 minutes lagega)
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .
```

**Build Process:**
- Python 3.11 install hoga
- System packages install honge (libgl1, libglib, libgomp1)
- Rembg + dependencies install honge (~180MB AI model download)
- Total build time: 8-12 minutes
- Build khatam hone par image Container Registry me save hoga

### Step 3: Cloud Run Par Deploy Karo
```powershell
# Deploy (auto-scaling with 2GB RAM)
gcloud run deploy $SERVICE_NAME `
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
  --platform managed `
  --region $REGION `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --allow-unauthenticated
```

**Deployment Settings:**
- **Memory:** 2GB (rembg ke liye)
- **CPU:** 2 cores (fast processing)
- **Timeout:** 300 seconds (5 minutes)
- **Max Instances:** 10 (auto-scaling)
- **Authentication:** Public access (no login required)

### Step 4: URL Copy Karo
Deploy ke baad milega:
```
Service [bg-remover-api] revision [bg-remover-api-00001-abc] has been deployed and is serving 100 percent of traffic.
Service URL: https://bg-remover-api-xxxxxxxxxx-uc.a.run.app
```

**Is URL ko copy karo!**

---

## 🔗 Frontend Connect Karo

### Update background-workspace.html
```powershell
# Open file
notepad C:\Users\apnao\Downloads\DocTools\background-workspace.html
```

**Line 259 par CLOUDRUN_API_URL update karo:**
```javascript
const CLOUDRUN_API_URL = 'https://bg-remover-api-xxxxxxxxxx-uc.a.run.app/remove-background';
```

**Line 347 se Remove.bg API code hatao (ab zarurat nahi):**
```javascript
// Old (delete this):
body: JSON.stringify({ 
  imageData: dataURL,
  apiKey: 'YOUR_REMOVEBG_API_KEY'
}),

// New (keep this):
body: JSON.stringify({ imageData: dataURL }),
```

---

## ✅ Testing

### 1. Health Check
```powershell
# Replace with your URL
$URL = "https://bg-remover-api-xxxxxxxxxx-uc.a.run.app"
Invoke-RestMethod -Uri "$URL/health"
```

**Expected Output:**
```json
{
  "status": "healthy",
  "tier": "cloudrun",
  "service": "background-remover-premium"
}
```

### 2. Frontend Test
1. Open: `background-remover.html`
2. Upload your 230 KB test image
3. Should see: "Processing with Cloud Run (50-100 MB tier)"
4. Result: Professional quality, no over-cleaning! ✨

---

## 💰 Cost Analysis

### Free Tier (Monthly):
- **Requests:** 2 million FREE
- **CPU Time:** 180,000 vCPU-seconds FREE
- **Memory:** 360,000 GiB-seconds FREE
- **Network:** 1 GB egress FREE

### For DocTools:
- **Per Request:** ~10 seconds processing
- **Free Requests:** ~18,000 images/month (FREE)
- **After Free Tier:** $0.00002/request (~₹0.0017 per image)

**Matlab:** Pehle 18,000 images bilkul FREE! 🎉

---

## 📊 Monitoring

### View Logs:
```powershell
gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50
```

### View Metrics:
Visit: https://console.cloud.google.com/run

---

## 🛠️ Common Issues

### Issue 1: Build fails with "permission denied"
**Solution:**
```powershell
gcloud auth login
gcloud config set project doctools-bg-remover
```

### Issue 2: "Billing not enabled"
**Solution:**
- Visit: https://console.cloud.google.com/billing
- Enable billing (free tier ke liye bhi zaruri)

### Issue 3: Service unhealthy
**Solution:**
```powershell
# Check logs
gcloud run services logs read $SERVICE_NAME --region $REGION --limit 100

# Redeploy
gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/$SERVICE_NAME --region $REGION
```

---

## 🎨 Quality Settings

**app-cloudrun.py me already configured:**
- ✅ Alpha Matting enabled (best quality edges)
- ✅ Memory optimization (100MB files support)
- ✅ Auto image resizing (performance)
- ✅ PNG optimization (smaller output)

**No changes needed - already 100% quality! 🚀**

---

## 📝 Quick Deploy Script

Save as `deploy.ps1`:
```powershell
# Quick Deploy Script
$PROJECT_ID = "doctools-bg-remover"
$SERVICE_NAME = "bg-remover-api"
$REGION = "us-central1"

Write-Host "🚀 Building image..." -ForegroundColor Green
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .

Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Green
gcloud run deploy $SERVICE_NAME `
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
  --platform managed `
  --region $REGION `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --allow-unauthenticated

Write-Host "✅ Deployment complete!" -ForegroundColor Green
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
```

**Run karo:**
```powershell
cd C:\Users\apnao\Downloads\DocTools\bg-remover-backend
.\deploy.ps1
```

---

## 🎯 Final Steps

1. ✅ Google Cloud account bana lo
2. ✅ gcloud CLI install karo
3. ✅ Project banao aur billing enable karo
4. ✅ `.\deploy.ps1` run karo
5. ✅ URL copy karke frontend me paste karo
6. ✅ Test karo apni 230 KB image se

**Result:** 100% Professional quality - No over-cleaning! 🎨✨

---

## 💡 Pro Tips

1. **Cold Start:** Pehli request slow ho sakti hai (10-15 sec) - model load hota hai
2. **Warm Instances:** Regular traffic se fast rahega (~5 sec)
3. **Scaling:** 10 concurrent users tak auto-scale karega
4. **Logs:** Console se real-time logs dekh sakte ho
5. **Updates:** Code change karke `.\deploy.ps1` dobara run karo

---

**Questions? Check logs:**
```powershell
gcloud run services logs read bg-remover-api --region us-central1 --limit 100
```

**Happy Deploying! 🚀**
