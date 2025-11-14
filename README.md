# DocTools (easyjpgtopdf.com)

Unified workspace for **easyjpgtopdf.com** — frontend, backend, heavy compute services, and automation.

```
DocTools/
├─ frontend/            # Vercel site (HTML/JS today, Next.js later)
├─ server/              # Render Node.js backend (LibreOffice + rembg)
├─ excel-unlocker/      # Flask backend for Excel password removal
├─ bg-remover-backend/  # Google Cloud Run - AI background removal (rembg)
├─ services/
│  ├─ cloud-run/        # Google Cloud Run microservices
│  └─ firebase/         # Firebase Functions project
├─ scripts/             # PowerShell automation helpers
├─ *.html, css/, js/, images/  # existing static assets (to migrate into frontend/)
└─ README.md            # this document
```

---

## 🆕 Excel Unlocker (Python Flask)
**Status:** ✅ Live in Production

Professional Excel password & protection removal tool with cloud backend.

### 🌐 Live URLs:
- **Frontend:** https://easyjpgtopdf.com/excel-unlocker.html
- **Backend API:** https://excel-unlocker-backend.onrender.com
- **Test Endpoint:** https://excel-unlocker-backend.onrender.com/test

### 🔧 Tech Stack:
- **Backend:** Flask 3.1.2, Python 3.13
- **Libraries:** openpyxl 3.1.5, msoffcrypto-tool 5.4.2
- **Server:** Gunicorn 23.0.0 on Render.com
- **CORS:** Enabled for cross-origin requests

### ✨ Features:
- ✅ Remove file encryption (password-protected Excel)
- ✅ Remove workbook protection
- ✅ Remove worksheet protection
- ✅ Support .xls and .xlsx formats
- ✅ Max 500MB file size
- ✅ Auto-delete files after download
- ✅ HTTPS encryption for all transfers
- ✅ Input validation (only Excel files)

### 🔒 Security & Privacy:
- **CORS Enabled** - Only allowed domains can access
- **File Size Limits** - Maximum 500MB for optimal performance
- **Secure File Handling** - Auto-delete after download
- **HTTPS Encryption** - All data transmitted securely
- **No Storage** - Files are processed temporarily only
- **Input Validation** - Only .xls and .xlsx files accepted

### 📡 API Endpoints:
- `POST /unlock` - Upload and unlock Excel file
  - Form data: `file` (required), `password` (optional)
  - Returns: `{"success": true, "filename": "unlocked_file.xlsx"}`
- `GET /download/<filename>` - Download unlocked file
- `GET /test` - Health check endpoint

### 🚀 Deployment:

#### Production (Render):
```bash
# Backend auto-deploys from GitHub
# Repository: https://github.com/easyjpgtopdf/DocTools
# Service: excel-unlocker-backend
# Build Command: pip install -r excel-unlocker/requirements.txt
# Start Command: gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app
# Working Directory: excel-unlocker/
```

#### Local Development:
```powershell
# Option 1: Auto-start both servers
.\start-excel-unlocker.ps1

# Option 2: Manual start
cd excel-unlocker
python app.py  # Backend on port 5000

# In new terminal
python -m http.server 8080  # Frontend on port 8080
```

**Local Access:** http://127.0.0.1:8080/excel-unlocker.html

### ⚡ Performance:
- **First Request:** 30-60 seconds (backend wake-up from sleep)
- **Subsequent Requests:** 2-5 seconds
- **Large Files (100MB+):** 10-20 seconds
- **Free Tier Limit:** 750 hours/month (auto-sleep after 15 min inactivity)

### 💰 Cost:
- **Current:** FREE (Render Free Tier)
- **Future (if needed):** $7/month for unlimited uptime

📖 **Complete Guide:** See `EXCEL_UNLOCKER_GUIDE.md`

---

## 🎨 AI Background Remover (Google Cloud Run)
**Status:** ⏳ Ready for deployment (awaiting Cloud verification)

High-quality background removal (100% like Photopea/remove.bg):
- **Server:** Google Cloud Run with rembg U²-Net
- **Browser:** IMG.LY @imgly/background-removal v1.7.0
- **Project:** easyjpgtopdf-de346
- **Quality:** 
  - Cloud Run: 100% (U²-Net + Alpha Matting)
  - Browser: 95-98% (medium model, featherRadius: 5)

### Deployment:
```bash
# Wait for Google Cloud verification (2-3 days)
# Then follow steps in CLOUDRUN_URL_SETUP.md
gcloud run deploy bg-remover --source . --region us-central1
```

📖 **Complete Guide:** See `CLOUDRUN_URL_SETUP.md`

---

## Frontend (Vercel)
- Static HTML currently lives at repo root; plan to migrate into `frontend/` (Next.js or Vite) for routing + shared env vars.
- Deployment: connect GitHub repo to Vercel → auto-build on `main`.
- When APIs are ready, set env vars such as `NEXT_PUBLIC_API_BASE` in Vercel dashboard.

## Render Backend (`/server`)
- Express server orchestrating conversions and delegating to Cloud Run workers.
- `Dockerfile` installs Node 18, LibreOffice 7.6.5, fonts, Python + rembg.
- Scripts: `npm run dev`, `npm run start`, `npm run render-build`, `npm run render-start`.
- Deploy via Render Docker Web Service or using scripts in `/scripts`.

## Cloud Run Services (`/services/cloud-run`)
Planned microservices (folders to be scaffolded):
1. `pdf-word/` — Node worker invoking LibreOffice CLI for PDF→DOCX.
2. `background-remover/` — Python rembg inference API.
3. `ocr/` — Node wrapper around Google Vision.

Each service should carry its own Dockerfile, package manifest, and README with `gcloud run deploy` commands.

## Firebase Functions (`/services/firebase`)
- Hosts authentication hooks, billing webhooks, usage tracking.
- Initialize with `firebase init functions` (Node 20 runtime).
- Deploy through GitHub Actions using `firebase deploy --only functions` when ready.

## Automation Scripts (`/scripts`)
- `render-build.ps1` — local Docker build for Render.
- `render-deploy.ps1` — trigger Render deployment via API.
- Future: `cloudrun-deploy.ps1`, `firebase-deploy.ps1`.

---

## Next Steps
1. Move static frontend into `frontend/` and configure Vercel build pipeline.
2. Flesh out `/server` routes (upload/background removal/pdf→word) calling Cloud Run services.
3. Scaffold Cloud Run service directories with starter code + Dockerfiles.
4. Initialize Firebase Functions project for auth/payment flows.
5. Add CI/CD pipelines covering Vercel, Render, Cloud Run, Firebase deployments.
6. Implement regression tests (LibreOffice conversions, rembg) and integrate into CI.

---

## 1. Frontend (Vercel)

- Source: `/frontend` (or root HTML files until migration finishes).
- Deploy by connecting GitHub repo to Vercel → auto-build on `main`.
- Environment variables: `NEXT_PUBLIC_API_BASE`, etc. (if needed).

> **TODO**: move remaining loose HTML files into `/frontend` and create a Vite/Next wrapper if client-only features required.

---

## 2. Render Backend (Node.js)

Location: `/server`

Key files:

- `Dockerfile` – installs Node 18, LibreOffice 7.6.5, rembg.
- `package.json` – Express API for conversions, `render-build`/`render-start` scripts.
- `README.md` – instructions for local dev & Render deployment.

Run locally:

```powershell
cd server
npm install
npm run dev
```

Docker test:

```powershell
cd server
docker build -t easyjpgtopdf-backend:local .
docker run --rm -p 10000:10000 easyjpgtopdf-backend:local
```

Render deploy: use `scripts\render-build.ps1` and `scripts\render-deploy.ps1`.

---

## 3. Google Cloud Run Services

Location: `/services/cloud-run`

Expected microservices:

1. `pdf-word/` – Node worker using LibreOffice CLI for PDF → DOCX.
2. `background-remover/` – Python rembg API (fast inference).
3. `ocr/` – Node wrapper around Google Vision API.

Each service should include:

- `Dockerfile`
- `package.json` or `requirements.txt`
- `README.md` with `gcloud run deploy` commands

> **Next**: scaffold directories and add sample handler code.

---

## 4. Firebase Functions

Location: `/services/firebase`

- Provides auth hooks, payment webhooks, usage quota tracking.
- Will include `firebase.json`, `firestore.rules`, and `functions/` (Node 20).
- Deployment via `firebase deploy --only functions` (GitHub Actions later).

> **Next**: initialize Firebase project, add `package.json`, sample `index.ts`.

---

## 5. Scripts

PowerShell helpers located in `/scripts`:

- `render-build.ps1`
- `render-deploy.ps1`
- future: `cloudrun-deploy.ps1`, `firebase-deploy.ps1`

Ensure PowerShell execution policy allows running local scripts:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

## Deployment Flow

1. **Frontend**: Git push → Vercel auto-deploy.
2. **Render backend**: Git push → Render auto-deploy (render.yaml or GitHub Actions).
3. **Cloud Run services**: GitHub Actions builds Docker, deploys with `gcloud run deploy` using Workload Identity.
4. **Firebase functions**: GitHub Actions uses `firebase-tools` for deploy.

Monitoring & logs via Render dashboard, Cloud Logging, Firebase console.

---

## Roadmap

- [ ] Move HTML files into `/frontend` structure (Next.js/Vite).
- [ ] Implement REST endpoints in `/server` for conversions, hooking to Cloud Run/Firebase.
- [ ] Scaffold Cloud Run microservices + CI.
- [ ] Add automated regression tests (rembg, LibreOffice conversions).
- [ ] Documentation for API contracts and environment setup.
