# 🚀 Excel Unlocker - Render Deployment Guide

Complete step-by-step guide to deploy Excel Unlocker backend on Render.com

---

## 📋 Prerequisites

✅ GitHub repository already connected to Render
✅ `excel-unlocker/` folder already pushed to GitHub
✅ All backend files ready:
- `app.py` - Flask application
- `requirements.txt` - Python dependencies
- `Procfile` - Render start command
- `render.yaml` - Render configuration

---

## 🔧 Step 1: Create New Web Service on Render

### 1.1 Login to Render Dashboard
- Go to: https://dashboard.render.com
- Sign in with GitHub account

### 1.2 Create New Web Service
1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Connect your GitHub repository: **`easyjpgtopdf/DocTools`**
4. Click **"Connect"**

---

## ⚙️ Step 2: Configure Web Service

### 2.1 Basic Settings
```
Name: excel-unlocker-backend
Region: Choose closest to users (e.g., Oregon USA)
Branch: main
Root Directory: excel-unlocker
```

### 2.2 Build & Deploy Settings
```
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn wsgi:app
```

### 2.3 Instance Type
```
Free (512MB RAM, shares CPU)
```

---

## 🔐 Step 3: Environment Variables

Add these in **Environment** section:

```bash
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-12345
PORT=10000
MAX_CONTENT_LENGTH=524288000
```

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

---

## 📦 Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes first time)
3. Check logs for errors
4. Once deployed, you'll get a URL like:
   ```
   https://excel-unlocker-backend.onrender.com
   ```

---

## ✅ Step 5: Test Backend

### Test Endpoint:
```bash
curl https://excel-unlocker-backend.onrender.com/test
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "API is working!",
  "python_version": "3.11.x",
  "working_directory": "/opt/render/project/src",
  "upload_folder": "/opt/render/project/src/uploads"
}
```

---

## 🌐 Step 6: Update Frontend

### 6.1 Get Your Render URL
Copy your deployed backend URL (e.g., `https://excel-unlocker-backend-xyz.onrender.com`)

### 6.2 Update excel-unlocker.html
Open `excel-unlocker.html` and find line ~220:

**Change this:**
```javascript
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://127.0.0.1:5000'
  : 'https://excel-unlocker-backend.onrender.com';  // ← UPDATE THIS
```

**Replace with your actual Render URL:**
```javascript
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://127.0.0.1:5000'
  : 'https://YOUR-ACTUAL-BACKEND-URL.onrender.com';  // ← YOUR URL HERE
```

### 6.3 Push to GitHub
```bash
git add excel-unlocker.html
git commit -m "Updated backend URL for Render deployment"
git push origin main
```

---

## 🎯 Step 7: Vercel Auto-Deploy

Once you push to GitHub:
1. Vercel will automatically detect changes
2. Deploy new version with updated backend URL
3. Your website will now connect to Render backend!

---

## 🧪 Final Testing

### Test Production Site:
1. Visit: `https://your-vercel-site.vercel.app/excel-unlocker.html`
2. Upload a password-protected Excel file
3. Click "Unlock Excel File"
4. File should download successfully! 🎉

---

## 🐛 Troubleshooting

### Issue 1: CORS Error in Browser Console
**Error:** `Access to fetch blocked by CORS policy`

**Fix:** Already handled! `Flask-CORS` is installed and enabled in `app.py`

### Issue 2: 500 Internal Server Error
**Check Render Logs:**
1. Go to Render Dashboard
2. Click on your service
3. View **Logs** tab
4. Look for Python errors

**Common Fixes:**
- Check `requirements.txt` has all dependencies
- Verify `PORT` environment variable is set
- Check file upload size limits

### Issue 3: Render Service Sleeping (Free Plan)
**Symptom:** First request takes 30-60 seconds

**Why:** Free tier spins down after 15 minutes of inactivity

**Solutions:**
- Upgrade to paid plan ($7/month for always-on)
- Use cron-job.org to ping `/test` endpoint every 10 minutes
- Accept the delay (free tier limitation)

### Issue 4: File Upload Fails
**Check:**
- File size < 500MB
- Valid .xls or .xlsx file
- Render logs for specific error
- Network tab in browser DevTools

---

## 💰 Cost Breakdown

### Free Tier (Render)
- ✅ 750 hours/month free
- ✅ Enough for low-traffic sites
- ❌ Spins down after 15 min inactivity
- ❌ Shared CPU

### Starter Plan ($7/month)
- ✅ Always-on (no sleep)
- ✅ Dedicated resources
- ✅ Better performance
- ✅ 100GB bandwidth

---

## 📊 Architecture Overview

```
User Browser (Vercel)
    ↓
excel-unlocker.html
    ↓ POST /unlock
Render Backend (Flask)
    ↓ processes with
openpyxl + msoffcrypto-tool
    ↓ returns
Unlocked Excel File
    ↓
Auto-download in browser
```

---

## 🔄 Deployment Checklist

Before going live:

- [ ] Backend deployed on Render
- [ ] `/test` endpoint working
- [ ] Backend URL updated in `excel-unlocker.html`
- [ ] Frontend pushed to GitHub
- [ ] Vercel auto-deployed
- [ ] CORS enabled (`Flask-CORS` installed)
- [ ] SECRET_KEY changed from default
- [ ] Test file upload works end-to-end
- [ ] Error handling tested
- [ ] Large file upload tested (>100MB)

---

## 📞 Support

**Common Questions:**

Q: Can I use Vercel for backend too?
A: No, Vercel doesn't support long-running Python processes.

Q: Why not use serverless functions?
A: Excel processing needs openpyxl/msoffcrypto which requires full Python environment.

Q: Can I deploy backend on Railway/Fly.io?
A: Yes! Similar process - just update `API_BASE_URL` with new URL.

Q: What if Render is slow?
A: Free tier spins down. Use cron job to keep alive or upgrade to Starter.

---

## ✅ Success Indicators

Your deployment is successful when:
1. ✅ Render shows "Live" status
2. ✅ `/test` endpoint returns JSON
3. ✅ Vercel site loads excel-unlocker.html
4. ✅ File upload → processing → download works
5. ✅ No CORS errors in browser console

---

**🎉 Deployment Complete! Your Excel Unlocker is now live!**
