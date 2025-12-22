# PowerShell Deployment Script for Google Cloud Run
# Deploys server to Cloud Run without MongoDB (will work with warning)

$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-to-word-converter"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "🚀 Starting deployment to Google Cloud Run..." -ForegroundColor Cyan
Write-Host "📦 Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "🎯 Service: $SERVICE_NAME" -ForegroundColor Yellow
Write-Host "🌍 Region: $REGION" -ForegroundColor Yellow
Write-Host ""

# Check if gcloud is installed
$gcloudCheck = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloudCheck) {
    Write-Host "❌ gcloud CLI not found!" -ForegroundColor Red
    Write-Host "📥 Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Check authentication
Write-Host "🔐 Checking authentication..." -ForegroundColor Cyan
$authStatus = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
if ([string]::IsNullOrWhiteSpace($authStatus)) {
    Write-Host "⚠️ Not authenticated. Running gcloud auth login..." -ForegroundColor Yellow
    gcloud auth login
}

# Set project
Write-Host "📋 Setting project to $PROJECT_ID..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host "🔧 Enabling required APIs..." -ForegroundColor Cyan
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com vision.googleapis.com language.googleapis.com storage-component.googleapis.com datastore.googleapis.com --quiet

# Build Docker image
Write-Host ""
Write-Host "🏗️ Building Docker image..." -ForegroundColor Cyan
gcloud builds submit --tag $IMAGE_NAME . --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed. Check logs above." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build successful!" -ForegroundColor Green

Write-Host ""
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan
Write-Host "⚠️ Note: MongoDB URI not set - database features will be disabled (this is OK for now)" -ForegroundColor Yellow
Write-Host ""

# Deploy to Cloud Run
# Note: MongoDB URI will be added later via Cloud Console
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE_NAME `
  --platform managed `
  --region $REGION `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --allow-unauthenticated `
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" `
  --port 8080 `
  --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed. Check logs above." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Deployment successful!" -ForegroundColor Green
Write-Host ""

# Get service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
Write-Host "🌐 Service URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "1. MongoDB Atlas me database create karein" -ForegroundColor White
Write-Host "2. Cloud Run Console me jao: https://console.cloud.google.com/run?project=$PROJECT_ID" -ForegroundColor White
Write-Host "3. Service '$SERVICE_NAME' par click karein" -ForegroundColor White
Write-Host "4. 'EDIT & DEPLOY NEW REVISION' click karein" -ForegroundColor White
Write-Host "5. 'Variables & Secrets' section me MONGODB_URI add karein" -ForegroundColor White
Write-Host "6. Redeploy karein" -ForegroundColor White
Write-Host ""
Write-Host "✅ Server ab MongoDB ke bina bhi kaam kar raha hai (database features disabled)" -ForegroundColor Green
