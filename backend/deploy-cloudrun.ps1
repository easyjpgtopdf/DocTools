# PowerShell Deployment Script for Cloud Run
# Project: easyjpgtopdf-de346

$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-to-word-converter"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "=== Deploying PDF to Word Converter to Cloud Run ===" -ForegroundColor Green
Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Cyan
Write-Host "Service Name: $SERVICE_NAME" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan

# Check if gcloud is installed
try {
    gcloud --version | Out-Null
} catch {
    Write-Host "Error: gcloud CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
    exit 1
}

# Set project
Write-Host "`nSetting GCP project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Build Docker image
Write-Host "`nBuilding Docker image..." -ForegroundColor Yellow
Set-Location ..
docker build -t $IMAGE_NAME ./backend
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    exit 1
}

# Push to Container Registry
Write-Host "`nPushing to Container Registry..." -ForegroundColor Yellow
docker push $IMAGE_NAME
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker push failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "`nDeploying to Cloud Run..." -ForegroundColor Yellow

# Check if environment variables are set
$envVars = @(
    "PROJECT_ID=$PROJECT_ID"
)

# Prompt for environment variables if not set
if (-not $env:GCS_OUTPUT_BUCKET) {
    $bucket = Read-Host "Enter GCS Output Bucket name"
    $envVars += "GCS_OUTPUT_BUCKET=$bucket"
} else {
    $envVars += "GCS_OUTPUT_BUCKET=$env:GCS_OUTPUT_BUCKET"
}

if (-not $env:DOCAI_PROCESSOR_ID) {
    $processorId = Read-Host "Enter Document AI Processor ID (default: ffaa7bcd30a9c788)"
    if ([string]::IsNullOrWhiteSpace($processorId)) {
        $processorId = "ffaa7bcd30a9c788"
    }
    $envVars += "DOCAI_PROCESSOR_ID=$processorId"
} else {
    $envVars += "DOCAI_PROCESSOR_ID=$env:DOCAI_PROCESSOR_ID"
}

if (-not $env:DOCAI_LOCATION) {
    $envVars += "DOCAI_LOCATION=us"
} else {
    $envVars += "DOCAI_LOCATION=$env:DOCAI_LOCATION"
}

if (-not $env:FIREBASE_PROJECT_ID) {
    $firebaseId = Read-Host "Enter Firebase Project ID (or press Enter to skip)"
    if (-not [string]::IsNullOrWhiteSpace($firebaseId)) {
        $envVars += "FIREBASE_PROJECT_ID=$firebaseId"
    }
} else {
    $envVars += "FIREBASE_PROJECT_ID=$env:FIREBASE_PROJECT_ID"
}

$envVarsString = $envVars -join ","

Write-Host "`nDeploying with environment variables..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 540 `
    --set-env-vars $envVarsString

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Deployment Successful! ===" -ForegroundColor Green
    
    # Get service URL
    $serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
    Write-Host "`nService URL: $serviceUrl" -ForegroundColor Cyan
    Write-Host "`nTest the API:" -ForegroundColor Yellow
    Write-Host "curl -X POST `"$serviceUrl/api/health`"" -ForegroundColor White
} else {
    Write-Host "`nDeployment failed!" -ForegroundColor Red
    exit 1
}

Set-Location backend

