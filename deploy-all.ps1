# Complete Deployment Script for Background Removal Service
# Deploys Frontend (Vercel) + Backend (Google Cloud Run)

param(
    [Parameter(Mandatory=$false)]
    [string]$Message = "Deploy: Background removal service update"
)

Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 Complete Deployment - Background Removal Service ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Step 1: Deploy Backend to Google Cloud Run
Write-Host "📦 Step 1: Deploying Backend to Google Cloud Run..." -ForegroundColor Yellow
Set-Location bg-removal-backend

if (Test-Path "deploy-cloudrun.sh") {
    Write-Host "   Running deploy-cloudrun.sh..." -ForegroundColor Gray
    bash deploy-cloudrun.sh
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Backend deployment failed!`n" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
} else {
    Write-Host "   ⚠️  deploy-cloudrun.sh not found, using manual deployment..." -ForegroundColor Yellow
    
    # Get project ID from environment or prompt
    $PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT
    if (-not $PROJECT_ID) {
        $PROJECT_ID = Read-Host "Enter Google Cloud Project ID"
    }
    
    $REGION = "us-central1"
    $SERVICE_NAME = "bg-removal-ai"
    
    Write-Host "   Building Docker image..." -ForegroundColor Gray
    docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME .
    
    Write-Host "   Pushing to Google Container Registry..." -ForegroundColor Gray
    docker push gcr.io/$PROJECT_ID/$SERVICE_NAME
    
    Write-Host "   Deploying to Cloud Run..." -ForegroundColor Gray
    gcloud run deploy $SERVICE_NAME `
        --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
        --platform managed `
        --region $REGION `
        --allow-unauthenticated `
        --memory 8Gi `
        --cpu 4 `
        --timeout 300 `
        --min-instances 0 `
        --max-instances 10 `
        --add-gpu type=nvidia-l4 `
        --gpu-count 1 `
        --concurrency 5
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Cloud Run deployment failed!`n" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    
    # Get service URL
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
    Write-Host "   ✅ Backend deployed: $SERVICE_URL" -ForegroundColor Green
    Write-Host "   📝 Update Vercel env: CLOUDRUN_API_URL_BG_REMOVAL=$SERVICE_URL" -ForegroundColor Yellow
}

Set-Location ..

# Step 2: Commit and push to GitHub (triggers Vercel)
Write-Host "`n📋 Step 2: Committing changes to Git..." -ForegroundColor Yellow
$status = git status --short
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "   ✅ No changes to commit`n" -ForegroundColor Green
} else {
    Write-Host "   📝 Found changes:" -ForegroundColor Cyan
    git status --short
    Write-Host ""
    
    Write-Host "   📦 Adding files..." -ForegroundColor Gray
    git add .
    
    Write-Host "   💾 Committing..." -ForegroundColor Gray
    git commit -m $Message
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Commit failed!`n" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "   📤 Pushing to GitHub..." -ForegroundColor Gray
    git push origin main
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Push failed!`n" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "   ✅ Code pushed to GitHub`n" -ForegroundColor Green
}

# Step 3: Wait for Vercel deployment
Write-Host "⏳ Step 3: Waiting for Vercel deployment..." -ForegroundColor Yellow
Write-Host "   (This takes about 30-60 seconds)`n" -ForegroundColor Gray
Start-Sleep -Seconds 45

# Step 4: Summary
Write-Host "`n╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ Deployment Complete!                          ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📊 Deployment Summary:" -ForegroundColor Cyan
Write-Host "   • Backend: Google Cloud Run (GPU-enabled)" -ForegroundColor White
Write-Host "   • Frontend: Vercel (auto-deployed from GitHub)" -ForegroundColor White
Write-Host "   • API Endpoints: /api/free-preview-bg, /api/premium-bg" -ForegroundColor White
Write-Host "`n🌐 Check deployment status:" -ForegroundColor Yellow
Write-Host "   • Vercel Dashboard: https://vercel.com/dashboard" -ForegroundColor White
Write-Host "   • Cloud Run Console: https://console.cloud.google.com/run" -ForegroundColor White
Write-Host "`n"

