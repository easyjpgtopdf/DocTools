# Adobe PDF Extract API - Complete Setup Guide
# Adobe API को Securely Configure करने का पूरा Guide

## 🎯 Overview (सारांश)

Adobe PDF Extract API को **backend (Cloud Run) में ही** configure करना है।
**Frontend (Vercel) को कुछ नहीं चाहिए** - security के लिए।

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (Vercel)                                           │
│ - NO Adobe credentials needed                              │
│ - Only calls backend API                                   │
│ - Credentials NEVER exposed to browser                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTPS API calls
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend (Cloud Run)                                         │
│ ✅ ADOBE_CLIENT_ID (environment variable)                   │
│ ✅ ADOBE_CLIENT_SECRET (environment variable)               │
│ - Handles Adobe API calls internally                       │
│ - Never exposes credentials                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Step-by-Step Setup (क्रमशः Setup)

### **STEP 1: Adobe Developer Console से Credentials लेना**

#### 1.1 Adobe Developer Console पर जाएं
```
https://developer.adobe.com/console
```

#### 1.2 Login करें
- Adobe ID से login करें (या new account बनाएं - FREE)

#### 1.3 New Project बनाएं
1. Click "Create new project"
2. Project name दें: "PDF to Excel Service" (कोई भी)
3. Click "Save"

#### 1.4 PDF Services API Add करें
1. Project में, click "Add API"
2. Select "**PDF Services API**" (Adobe Document Services में से)
3. Authentication type: "**OAuth Server-to-Server**"
4. Click "Save configured API"

#### 1.5 Credentials Copy करें
आपको ये मिलेंगे:
```json
{
  "client_id": "abc123def456ghi789...",
  "client_secret": "p-xyz789abc123def456..."
}
```

**Important**: 
- ✅ `client_id`: Public identifier (log में show हो सकता है)
- ❌ `client_secret`: **TOP SECRET** - कभी भी share या commit नहीं करना!

---

### **STEP 2: Cloud Run में Credentials Add करना**

#### Option A: Automated Script (Recommended)

**Windows (PowerShell):**
```powershell
cd pdf-to-excel-backend
.\add-adobe-credentials.ps1
```

**Linux/Mac (Bash):**
```bash
cd pdf-to-excel-backend
chmod +x add-adobe-credentials.sh
./add-adobe-credentials.sh
```

Script automatically:
- ✅ Prompts for credentials securely
- ✅ Validates inputs
- ✅ Adds to Cloud Run
- ✅ Verifies deployment

#### Option B: Manual Command

```bash
gcloud run services update pdf-to-excel-backend \
  --project=easyjpgtopdf-de346 \
  --region=us-central1 \
  --update-env-vars="ADOBE_CLIENT_ID=your_client_id_here,ADOBE_CLIENT_SECRET=your_secret_here" \
  --quiet
```

**Replace**:
- `your_client_id_here` → Your actual Adobe Client ID
- `your_secret_here` → Your actual Adobe Client Secret

---

### **STEP 3: Verify Setup (Setup Check करना)**

```powershell
cd pdf-to-excel-backend
.\verify-adobe-setup.ps1
```

**Expected Output**:
```
✅ ADOBE_CLIENT_ID: abc123def456...
✅ ADOBE_CLIENT_SECRET: Set (value hidden for security)

✅ Adobe PDF Extract API is CONFIGURED and ACTIVE!
```

---

### **STEP 4: Test with Real PDF (Test करना)**

1. **Upload a complex PDF at**:
   ```
   https://www.easyjpgtopdf.com/pdf-to-excel-premium.html
   ```

2. **Check logs for Adobe fallback trigger**:
   ```bash
   gcloud logging read \
     'resource.type=cloud_run_revision AND resource.labels.service_name=pdf-to-excel-backend AND textPayload=~"ADOBE"' \
     --limit=20 --project=easyjpgtopdf-de346
   ```

3. **Expected log entries**:
   ```
   ADOBE FALLBACK: Triggered for complex_invoice.pdf
   Reason: Document AI confidence 0.55 < 0.65
   Adobe cost meter: 1 transaction(s) this session
   
   Adobe fallback SUCCESS: Replacing 1 DocAI layouts with 1 Adobe layouts
   Adobe layout: 1 page(s), 25 rows, 5 columns
   ```

---

## 🔒 Security Checklist (Security जाँच)

### ✅ SAFE (सुरक्षित)
- [x] Credentials stored in Cloud Run environment variables
- [x] `.gitignore` configured to exclude `.env` files
- [x] No credentials in source code files
- [x] No credentials sent to frontend/browser
- [x] `client_secret` never logged
- [x] Only backend has access to credentials

### ❌ NEVER DO (कभी नहीं करना)
- [ ] Commit `.env` to GitHub
- [ ] Hard-code credentials in `.py` files
- [ ] Send credentials to frontend
- [ ] Share credentials in public chat/docs
- [ ] Log `client_secret` value
- [ ] Store credentials in Vercel (frontend doesn't need them)

---

## 🌐 Vercel (Frontend) - NO CHANGES NEEDED

**Important**: Frontend को कुछ करने की जरूरत नहीं है!

```
Frontend (pdf-to-excel-premium.html):
  - Calls backend API: /api/pdf-to-excel-docai
  - Backend internally handles Adobe API
  - Response includes layout_source: "adobe" or "docai"
  - No credentials needed in Vercel environment variables
```

---

## 📊 How It Works (कैसे काम करता है)

### 1️⃣ User uploads PDF
```javascript
// Frontend (pdf-to-excel-premium.html)
fetch('https://pdf-to-excel-backend.../api/pdf-to-excel-docai', {
  method: 'POST',
  body: formData
})
```

### 2️⃣ Backend processes
```python
# Backend (docai_service.py)
1. Document AI processes PDF
2. DecisionRouter checks confidence
3. If confidence < 0.65 AND complexity HIGH:
   → Adobe fallback triggered
4. Adobe API called with credentials from env vars
5. Result converted to UnifiedLayout
6. Excel rendered
```

### 3️⃣ Response to frontend
```json
{
  "status": "success",
  "downloadUrl": "https://...",
  "mode": "table_strict",
  "confidence": 0.85,
  "layout_source": "adobe"  ← Indicates Adobe was used
}
```

---

## 🔍 Troubleshooting (समस्या समाधान)

### Problem 1: "Adobe credentials not configured"

**Symptom**: Log shows `Adobe PDF Extract credentials not configured - fallback disabled`

**Solution**:
```bash
# Verify credentials are set
.\verify-adobe-setup.ps1

# If not set, add them
.\add-adobe-credentials.ps1
```

### Problem 2: "Adobe fallback NOT triggered"

**Symptom**: Adobe never triggers, even for complex PDFs

**Reasons**:
1. Document AI confidence ≥ 0.65 (fallback not needed)
2. Visual complexity is LOW/MEDIUM (fallback not needed)
3. Credentials missing (check with `verify-adobe-setup.ps1`)

**Expected**: Adobe triggers for ~5-10% of documents only

### Problem 3: "Authentication failed"

**Symptom**: `Adobe token request failed: 401`

**Solution**:
1. Verify credentials are correct
2. Check Adobe Developer Console for API status
3. Regenerate credentials if needed
4. Re-run `add-adobe-credentials.ps1`

### Problem 4: Credentials visible in GitHub

**Solution**:
1. **NEVER commit actual credentials to GitHub**
2. Remove committed credentials:
   ```bash
   git rm --cached .env
   git commit -m "Remove sensitive credentials"
   git push origin main
   ```
3. Regenerate credentials in Adobe Developer Console
4. Add new credentials to Cloud Run only

---

## 📈 Cost Tracking (खर्च की जानकारी)

### Adobe Pricing (Estimated)
- **Pay-per-document**: ~$0.05 per extraction
- **Expected usage**: 5-10% of total documents
- **Monthly estimate** (for 1000 docs/month): ~$2.50-$5.00

### When Adobe is Called
```
✅ Triggers:
  - DocAI confidence < 0.65
  - Visual complexity HIGH
  - Premium users only

❌ Not Triggered:
  - Simple PDFs
  - High DocAI confidence
  - Low/Medium complexity
```

### Monitoring Costs
Check session call count in logs:
```
Adobe cost meter: 3 transaction(s) this session
```

---

## 🎯 Quick Reference Commands

### Add Credentials
```powershell
.\add-adobe-credentials.ps1
```

### Verify Setup
```powershell
.\verify-adobe-setup.ps1
```

### Check Logs
```bash
gcloud logging read \
  'resource.type=cloud_run_revision AND textPayload=~"ADOBE"' \
  --limit=20 --project=easyjpgtopdf-de346
```

### Remove Credentials (if needed)
```bash
gcloud run services update pdf-to-excel-backend \
  --remove-env-vars="ADOBE_CLIENT_ID,ADOBE_CLIENT_SECRET" \
  --region=us-central1 --project=easyjpgtopdf-de346
```

---

## ✅ Final Checklist

- [ ] Adobe Developer Console account created
- [ ] PDF Services API added to project
- [ ] Client ID and Secret obtained
- [ ] Credentials added to Cloud Run (not Vercel!)
- [ ] Setup verified with `verify-adobe-setup.ps1`
- [ ] Test PDF uploaded successfully
- [ ] Logs show Adobe fallback trigger
- [ ] Frontend response includes `layout_source: "adobe"`
- [ ] No credentials committed to GitHub
- [ ] No credentials in Vercel environment variables

---

## 📞 Support

**Adobe Developer Console**:
https://developer.adobe.com/console

**Adobe PDF Services Documentation**:
https://developer.adobe.com/document-services/docs/overview/pdf-extract-api/

**Cloud Run Environment Variables**:
https://cloud.google.com/run/docs/configuring/environment-variables

---

## Summary (सारांश)

1. **Adobe credentials**: Cloud Run में environment variables के रूप में
2. **Frontend (Vercel)**: कोई credentials नहीं चाहिए
3. **Security**: Credentials कभी भी code, GitHub, या frontend में नहीं
4. **Testing**: `verify-adobe-setup.ps1` से check करें
5. **Cost**: Pay-per-use, ~5-10% documents के लिए trigger

**Setup is complete when**:
- ✅ `verify-adobe-setup.ps1` shows "CONFIGURED and ACTIVE"
- ✅ Test PDF triggers Adobe fallback
- ✅ Logs show "ADOBE FALLBACK: Triggered"
- ✅ Response includes `layout_source: "adobe"`

