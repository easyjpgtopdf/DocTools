# 🚀 Google Cloud Console Deploy Guide (No CLI Needed)

## ✨ Project ID: easyjpgtopdf-de346

Tumhare liye **step-by-step Cloud Console** se deploy karne ka guide:

---

## 📋 Step 1: Google Cloud Console Kholo

1. Visit: https://console.cloud.google.com
2. Login with your Google account
3. Top bar me project selector me `easyjpgtopdf-de346` select karo

---

## 🔧 Step 2: Cloud Build & Cloud Run APIs Enable Karo

1. Visit: https://console.cloud.google.com/apis/library
2. Search aur enable karo:
   - **Cloud Build API**
   - **Cloud Run Admin API**
   - **Container Registry API**

---

## 🐳 Step 3: Cloud Shell Me Deploy Karo

### Method 1: Direct Cloud Shell (Easiest)

1. Visit: https://console.cloud.google.com
2. Top-right me **Activate Cloud Shell** button click karo (terminal icon)
3. Shell open hone ke baad ye commands run karo:

```bash
# Clone your repo
git clone https://github.com/easyjpgtopdf/DocTools.git
cd DocTools/bg-remover-backend

# Build Docker image (8-12 minutes)
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

# Copy the service URL that appears!
```

---

## 📝 Expected Output

```
Building and pushing image...
✓ DONE
Deploying container to Cloud Run service [bg-remover-api]...
✓ Deploying new service... Done.
✓ Creating Revision...
✓ Routing traffic...
Service URL: https://bg-remover-api-xxxxxxxxxx-uc.a.run.app
```

**Copy this URL! ⬆️**

---

## 🔗 Step 4: Frontend Update Karo

Open `background-workspace.html` and update:

**Line 259:**
```javascript
const CLOUDRUN_API_URL = 'https://bg-remover-api-xxxxxxxxxx-uc.a.run.app/remove-background';
```

**Line 347 (remove apiKey):**
```javascript
// Before:
body: JSON.stringify({ 
  imageData: dataURL,
  apiKey: 'YOUR_REMOVEBG_API_KEY'
}),

// After:
body: JSON.stringify({ imageData: dataURL }),
```

---

## ✅ Step 5: Test Karo

1. Open: `background-remover.html`
2. Upload your 230 KB test image
3. Should route to Cloud Run (50-100 MB tier)
4. Result: 100% professional quality! 🎨

---

## 📊 Monitor Deployment

**Real-time logs:**
```bash
# In Cloud Shell
gcloud run services logs read bg-remover-api --region us-central1 --limit 50
```

**Or visit:**
https://console.cloud.google.com/run/detail/us-central1/bg-remover-api

---

## 💰 Cost (Free Tier)

- First 2 million requests: **FREE**
- ~18,000 background removals/month: **FREE**
- After that: $0.00002/request (~₹0.0017 per image)

---

## 🎯 Quick Commands Reference

```bash
# Check service status
gcloud run services describe bg-remover-api --region us-central1

# View URL
gcloud run services describe bg-remover-api --region us-central1 --format="value(status.url)"

# Delete service (if needed)
gcloud run services delete bg-remover-api --region us-central1

# Redeploy after code changes
cd DocTools/bg-remover-backend
git pull
gcloud builds submit --tag gcr.io/easyjpgtopdf-de346/bg-remover-api .
gcloud run deploy bg-remover-api --image gcr.io/easyjpgtopdf-de346/bg-remover-api --region us-central1
```

---

## 🐛 Troubleshooting

### Build fails?
```bash
# Check logs
gcloud builds list --limit 5

# View specific build
gcloud builds log [BUILD_ID]
```

### Service not starting?
```bash
# Check logs
gcloud run services logs read bg-remover-api --region us-central1 --limit 100
```

### Permission denied?
```bash
# Set project
gcloud config set project easyjpgtopdf-de346

# Check current project
gcloud config get-value project
```

---

## 🎉 Success Indicators

✅ Build completes: "SUCCESS"  
✅ Deploy shows: "Service URL: https://..."  
✅ Health check: `curl https://your-url/health` returns `{"status":"healthy"}`  
✅ Frontend test: Image processes without over-cleaning  

---

**Total Time:** 15-20 minutes  
**Result:** 100% Professional Quality - No Over-Cleaning! 🚀

---

**Need Help?**  
Share screenshot of any error ya mujhe bolo main live guide karunga! 💬
