# ============================================
# Google Cloud Run Deployment - PowerShell Script
# Background Remover with Rembg U²-Net Latest
# ============================================

# Configuration
$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "bg-remover-api"
$REGION = "us-central1"

Write-Host ""
Write-Host "🚀 Starting deployment to Google Cloud Run..." -ForegroundColor Cyan
Write-Host "📦 Project: $PROJECT_ID" -ForegroundColor White
Write-Host "🎯 Service: $SERVICE_NAME" -ForegroundColor White
Write-Host "🌍 Region: $REGION" -ForegroundColor White
Write-Host "🤖 Model: u2net (latest, auto-downloads)" -ForegroundColor White
Write-Host ""

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
    Write-Host "✅ gcloud CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ gcloud CLI not found!" -ForegroundColor Red
    Write-Host "📥 Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Write-Host "   After installation, run: gcloud init" -ForegroundColor Yellow
    exit 1
}

# Check if authenticated
Write-Host "🔐 Checking authentication..." -ForegroundColor Yellow
$authCheck = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
if (-not $authCheck) {
    Write-Host "⚠️ Not authenticated. Running gcloud auth login..." -ForegroundColor Yellow
    gcloud auth login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Authentication failed" -ForegroundColor Red
        exit 1
    }
}

# Set project
Write-Host "📋 Setting project to $PROJECT_ID..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set project" -ForegroundColor Red
    exit 1
}

# Enable required APIs
Write-Host "🔧 Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com 2>&1 | Out-Null

# Build Docker image
Write-Host ""
Write-Host "🏗️ Building Docker image (8-12 minutes)..." -ForegroundColor Yellow
Write-Host "⏳ Please wait... (rembg u2net model will download ~180MB on first run)" -ForegroundColor Gray
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
    Write-Host "2. Update CLOUDRUN_API_URL in background-workspace.html" -ForegroundColor White
    Write-Host "3. Test with an image above 2 MB" -ForegroundColor White
    Write-Host ""
    Write-Host "🎉 100% Professional quality - No over-cleaning!" -ForegroundColor Green
    Write-Host "🤖 Using latest u2net model" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Monitor:" -ForegroundColor Cyan
    Write-Host "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME" -ForegroundColor Blue
    Write-Host ""
    Write-Host "💡 Note: First request will take longer (~30s) as model downloads" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed. Check logs above." -ForegroundColor Red
    exit 1
}
