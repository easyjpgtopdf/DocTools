# PDF Unlocker - Render Deployment Guide

## 🚀 Quick Deploy to Render

### Step 1: Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `easyjpgtopdf/DocTools`
4. Configure service:

**Service Details:**
- **Name:** `pdf-unlocker-backend`
- **Region:** `Oregon (US West)` or closest to you
- **Branch:** `main`
- **Root Directory:** `pdf-unlocker`
- **Runtime:** `Python 3`

**Build & Deploy:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app`

**Instance Type:**
- Select **Free** tier

### Step 2: Environment Variables (Optional)

- `FLASK_ENV` = `production`
- `SECRET_KEY` = (auto-generated, optional)

### Step 3: Deploy

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for build to complete
3. Your service will be live at: `https://pdf-unlocker-backend.onrender.com`

### Step 4: Test Backend

```bash
# Test health endpoint
curl https://pdf-unlocker-backend.onrender.com/test
```

Expected response:
```json
{
  "status": "success",
  "message": "PDF Unlocker API is working!",
  "python_version": "3.11.9",
  ...
}
```

### Step 5: Update Frontend

Once deployed, the frontend (`unlock-pdf.html`) is already configured with:
```javascript
const API_BASE_URL = 'https://pdf-unlocker-backend.onrender.com';
```

## 🎯 Features

✅ Remove PDF password protection  
✅ Support encrypted PDFs  
✅ Max 500MB file size  
✅ Auto-delete files after download  
✅ CORS enabled  
✅ HTTPS encryption  

## 📡 API Endpoints

- `GET /test` - Health check
- `POST /unlock` - Upload and unlock PDF
  - Form data: `file` (PDF), `password` (optional)
- `GET /download/<filename>` - Download unlocked PDF

## 💰 Cost

**Free Tier:** 750 hours/month (enough for moderate traffic)  
**Paid:** $7/month for unlimited uptime

## 🔧 Local Testing

```powershell
cd pdf-unlocker
pip install -r requirements.txt
python app.py
```

Access: http://localhost:5001

## 📊 Performance

- First request: 30-60 seconds (wake-up)
- Subsequent: 2-5 seconds
- Auto-sleep after 15 min inactivity (free tier)

---

**Status:** Ready for deployment 🚀
