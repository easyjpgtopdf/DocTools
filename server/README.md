# easyjpgtopdf Backend (Render setup)

This folder contains the Node.js backend for heavy conversions (PDF → Word/PowerPoint, background remover, etc.).

## Prerequisites

- Node.js 18+
- Docker Desktop (for local container tests)
- LibreOffice binaries (already installed inside the Docker image)
- Python 3 (bundled in Docker image for `rembg`)
- Google Cloud / Render CLI (depending on deployment target)

## Local development

```powershell
# install dependencies
npm install

# run dev server
npm run dev
```

The server listens on `http://localhost:10000` (Render default) unless `PORT` is overridden.

### Testing LibreOffice conversion locally

```powershell
# convert sample.pdf to DOCX using the API
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:10000/api/convert/pdf-to-word" `
  -InFile ".\samples\sample.pdf" `
  -ContentType "application/pdf" `
  -OutFile ".\output\sample.docx"
```

## Docker build (Render-compatible)

```powershell
# build image
docker build -t easyjpgtopdf-backend:latest .

# run container locally
docker run --rm -p 10000:10000 easyjpgtopdf-backend:latest
```

## Deploying to Render (Docker Web Service)

1. Ensure `render.yaml` exists in repo root (see below).
2. Commit & push changes to GitHub.
3. In Render dashboard, choose **New Web Service** → **Use Existing Repository**.
4. Select the repo, pick branch, and Render will use `render.yaml` for configuration.

### render.yaml template

```yaml
services:
  - type: web
    name: easyjpgtopdf-backend
    env: docker
    plan: starter
    autoDeploy: true
    healthCheckPath: /health
    disk:
      name: tmp-storage
      sizeGB: 2
```

## PowerShell helpers

- `../scripts/render-build.ps1` – builds and pushes Docker image to Render registry.
- `../scripts/render-deploy.ps1` – triggers deployment via Render API.

(See `scripts/` directory for actual commands.)

## Environment variables

| Variable | Purpose |
|----------|---------|
| `PORT` | HTTP port (Render defaults to 10000) |
| `MAX_UPLOAD_MB` | Limit user upload size |
| `LIBREOFFICE_PATH` | Override libreoffice binary if needed |

All secrets should be configured in Render dashboard (or `.env` for local). Never commit secrets to Git.
