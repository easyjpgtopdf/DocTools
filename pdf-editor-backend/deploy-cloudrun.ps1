# PowerShell script to deploy PDF Editor Service to Google Cloud Run
# CPU only, minimum instances 0 (no monthly bill when idle)

$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-editor-service"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 Deploying PDF Editor to Cloud Run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Service: $SERVICE_NAME" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host ""

# Set the project
Write-Host "Setting GCloud project..." -ForegroundColor Green
gcloud config set project $PROJECT_ID

# Build Docker image
Write-Host "`n📦 Building Docker image..." -ForegroundColor Green
docker build -t ${IMAGE_NAME} .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

# Push to Google Container Registry
Write-Host "`n📤 Pushing to Google Container Registry..." -ForegroundColor Green
docker push ${IMAGE_NAME}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "`n🚀 Deploying to Cloud Run..." -ForegroundColor Green
gcloud run deploy ${SERVICE_NAME} `
  --image ${IMAGE_NAME} `
  --platform managed `
  --region ${REGION} `
  --allow-unauthenticated `
  --cpu 1 `
  --memory 2Gi `
  --min-instances 0 `
  --max-instances 10 `
  --timeout 300 `
  --concurrency 80 `
  --set-env-vars API_BASE_URL=https://easyjpgtopdf.com

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cloud Run deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nService URL:" -ForegroundColor Cyan
$SERVICE_URL = "https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app"
Write-Host $SERVICE_URL -ForegroundColor Yellow
Write-Host "`nHealth Check:" -ForegroundColor Cyan
try {
    $healthResponse = Invoke-WebRequest -Uri "$SERVICE_URL/health" -UseBasicParsing
    Write-Host $healthResponse.Content -ForegroundColor Green
} catch {
    Write-Host "Health check failed: $_" -ForegroundColor Yellow
}
Write-Host "`n========================================" -ForegroundColor Green

