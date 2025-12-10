# Automatic Deployment Script - PDF to Word Converter
# Project: easyjpgtopdf-de346

$ErrorActionPreference = "Stop"

$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-to-word-converter"
$REGION = "us-central1"
$BUCKET_NAME = "easyjpgtopdf-word-exports"
$DOCAI_PROCESSOR_ID = "ffaa7bcd30a9c788"
$DOCAI_LOCATION = "us"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "=== Automatic Deployment - PDF to Word Converter ===" -ForegroundColor Green
Write-Host "Project: $PROJECT_ID" -ForegroundColor Cyan
Write-Host "Service: $SERVICE_NAME" -ForegroundColor Cyan
Write-Host "Bucket: $BUCKET_NAME" -ForegroundColor Cyan

# Check if gcloud is installed
Write-Host "`nChecking Google Cloud SDK..." -ForegroundColor Yellow
$gcloudCheck = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloudCheck) {
    Write-Host "✗ Error: gcloud CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Google Cloud SDK found" -ForegroundColor Green

# Set project
Write-Host "`n[1/7] Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID 2>&1 | Out-Null
Write-Host "✓ Project set to $PROJECT_ID" -ForegroundColor Green

# Check if bucket exists, create if not
Write-Host "`n[2/7] Checking GCS bucket..." -ForegroundColor Yellow
gcloud storage buckets describe gs://$BUCKET_NAME 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating bucket: $BUCKET_NAME" -ForegroundColor Yellow
    gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION --project=$PROJECT_ID 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Bucket created: $BUCKET_NAME" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create bucket" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Bucket exists: $BUCKET_NAME" -ForegroundColor Green
}

# Check Document AI API
Write-Host "`n[3/7] Checking Document AI API..." -ForegroundColor Yellow
$docaiEnabled = gcloud services list --enabled --filter="name:documentai.googleapis.com" --format="value(name)" 2>&1
if ($docaiEnabled) {
    Write-Host "✓ Document AI API is enabled" -ForegroundColor Green
} else {
    Write-Host "Enabling Document AI API..." -ForegroundColor Yellow
    gcloud services enable documentai.googleapis.com --project=$PROJECT_ID 2>&1 | Out-Host
    Write-Host "✓ Document AI API enabled" -ForegroundColor Green
}

# Build Docker image
Write-Host "`n[4/7] Building Docker image..." -ForegroundColor Yellow
$currentDir = Get-Location
if ($currentDir.Path -like "*backend*") {
    # Already in backend directory
} else {
    Set-Location backend
}
docker build -t $IMAGE_NAME . 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker image built successfully" -ForegroundColor Green

# Push to Container Registry
Write-Host "`n[5/7] Pushing to Container Registry..." -ForegroundColor Yellow
docker push $IMAGE_NAME 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker push failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Image pushed to Container Registry" -ForegroundColor Green

# Deploy to Cloud Run
Write-Host "`n[6/7] Deploying to Cloud Run..." -ForegroundColor Yellow

$envVars = @(
    "PROJECT_ID=$PROJECT_ID",
    "GCS_OUTPUT_BUCKET=$BUCKET_NAME",
    "DOCAI_PROCESSOR_ID=$DOCAI_PROCESSOR_ID",
    "DOCAI_LOCATION=$DOCAI_LOCATION",
    "FIREBASE_PROJECT_ID=$PROJECT_ID"
)
$envVarsString = $envVars -join ","

gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 540 `
    --set-env-vars $envVarsString `
    --project $PROJECT_ID 2>&1 | Out-Host

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Deployment failed!" -ForegroundColor Red
    exit 1
}

# Get service URL
Write-Host "`n[7/7] Getting service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)" --project $PROJECT_ID 2>&1

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "=== DEPLOYMENT SUCCESSFUL! ===" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nService URL: $serviceUrl" -ForegroundColor Cyan
Write-Host "`nTest the API:" -ForegroundColor Yellow
Write-Host "curl -X POST `"$serviceUrl/api/health`"" -ForegroundColor White
Write-Host "`nConvert PDF to Word:" -ForegroundColor Yellow
Write-Host "curl -X POST `"$serviceUrl/api/convert/pdf-to-word`" -F `"file=@document.pdf`"" -ForegroundColor White
Write-Host "`n"
