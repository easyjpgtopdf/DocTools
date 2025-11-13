# Google Cloud Run Deployment - PowerShell Script
# For 100% Professional Quality Background Removal

# Configuration
$PROJECT_ID = "doctools-bg-remover"
$SERVICE_NAME = "bg-remover-api"
$REGION = "us-central1"

Write-Host ""
Write-Host "🚀 Starting deployment to Google Cloud Run..." -ForegroundColor Cyan
Write-Host "📦 Project: $PROJECT_ID" -ForegroundColor White
Write-Host "🎯 Service: $SERVICE_NAME" -ForegroundColor White
Write-Host "🌍 Region: $REGION" -ForegroundColor White
Write-Host ""

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "❌ gcloud CLI not found!" -ForegroundColor Red
    Write-Host "📥 Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Build Docker image
Write-Host "🏗️ Building Docker image (8-12 minutes)..." -ForegroundColor Yellow
Write-Host "⏳ Please wait... (rembg AI model downloading ~180MB)" -ForegroundColor Gray
Write-Host ""

gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Build successful!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Build failed. Check logs above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "1. Run: gcloud auth login" -ForegroundColor White
    Write-Host "2. Run: gcloud config set project $PROJECT_ID" -ForegroundColor White
    Write-Host "3. Enable APIs: gcloud services enable cloudbuild.googleapis.com run.googleapis.com" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Yellow

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME `
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
  --platform managed `
  --region $REGION `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --allow-unauthenticated `
  --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Service URL:" -ForegroundColor Cyan
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
    Write-Host $SERVICE_URL -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Next steps:" -ForegroundColor Yellow
    Write-Host "1. Copy the URL above" -ForegroundColor White
    Write-Host "2. Update CLOUDRUN_API_URL in background-workspace.html (line 259)" -ForegroundColor White
    Write-Host "3. Change line 347: Remove apiKey parameter" -ForegroundColor White
    Write-Host "4. Test with your 230 KB image" -ForegroundColor White
    Write-Host ""
    Write-Host "🎉 100% Professional quality - No over-cleaning!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Monitor:" -ForegroundColor Cyan
    Write-Host "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME" -ForegroundColor Blue
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed. Check logs above." -ForegroundColor Red
    exit 1
}
