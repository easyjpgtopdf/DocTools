# PDF Editor Deployment Script for Windows PowerShell
# Deploys both backend and frontend

Write-Host "🚀 Starting PDF Editor Deployment..." -ForegroundColor Blue

# 1. Deploy Backend to Cloud Run
Write-Host "`n📦 Deploying Backend to Cloud Run..." -ForegroundColor Cyan
Set-Location pdf-editor-backend

if (Test-Path "requirements.txt") {
    Write-Host "Installing Python dependencies..."
    pip install -r requirements.txt
}

Write-Host "Deploying to Cloud Run..."
gcloud run deploy pdf-editor-service `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --set-env-vars="PYTHONUNBUFFERED=1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Cloud Run deployment failed. Make sure you're authenticated with gcloud." -ForegroundColor Yellow
    Write-Host "You can deploy manually or skip this step."
}

Set-Location ..

# 2. Deploy Frontend to Vercel
Write-Host "`n🌐 Deploying Frontend to Vercel..." -ForegroundColor Cyan

if (Get-Command vercel -ErrorAction SilentlyContinue) {
    vercel --prod
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Vercel deployment failed. Make sure you're logged in." -ForegroundColor Yellow
        Write-Host "Run: vercel login"
    }
} else {
    Write-Host "⚠️  Vercel CLI not found. Install with: npm i -g vercel" -ForegroundColor Yellow
}

# 3. Push to GitHub
Write-Host "`n📤 Pushing to GitHub..." -ForegroundColor Cyan

if (Test-Path ".git") {
    git add .
    git commit -m "feat: Deploy dual-layer PDF editor system" 2>&1 | Out-Null
    git push origin main
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Git push failed. Make sure you have a remote configured." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Not a git repository. Initialize with: git init" -ForegroundColor Yellow
}

Write-Host "`n✅ Deployment process completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Update PDF_EDITOR_BACKEND_URL in Vercel environment variables"
Write-Host "2. Test the deployed application"
Write-Host "3. Monitor Cloud Run logs for any issues"

