# Automatic Deployment Script - PDF to Word Converter
$ErrorActionPreference = "Continue"

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

Write-Host "`nChecking Google Cloud SDK..." -ForegroundColor Yellow
$gcloudCheck = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloudCheck) {
    Write-Host "Error: gcloud CLI not found" -ForegroundColor Red
    exit 1
}
Write-Host "Google Cloud SDK found" -ForegroundColor Green

Write-Host "`n[1/7] Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
Write-Host "Project set" -ForegroundColor Green

Write-Host "`n[2/7] Checking GCS bucket..." -ForegroundColor Yellow
$bucketCheck = gcloud storage buckets describe gs://$BUCKET_NAME 2>&1
if ($bucketCheck -match "ERROR" -or $bucketCheck -match "not found") {
    Write-Host "Creating bucket..." -ForegroundColor Yellow
    gcloud storage buckets create gs://$BUCKET_NAME --location=$REGION --project=$PROJECT_ID
    Write-Host "Bucket created" -ForegroundColor Green
} else {
    Write-Host "Bucket exists" -ForegroundColor Green
}

Write-Host "`n[3/7] Checking Document AI API..." -ForegroundColor Yellow
$docaiCheck = gcloud services list --enabled --filter="name:documentai.googleapis.com" --format="value(name)" 2>&1
if ($docaiCheck -and $docaiCheck -notmatch "ERROR") {
    Write-Host "Document AI API enabled" -ForegroundColor Green
} else {
    Write-Host "Enabling Document AI API..." -ForegroundColor Yellow
    gcloud services enable documentai.googleapis.com --project=$PROJECT_ID
    Write-Host "Document AI API enabled" -ForegroundColor Green
}

Write-Host "`n[4/7] Building Docker image..." -ForegroundColor Yellow
$currentDir = Get-Location
if ($currentDir.Path -notlike "*backend*") {
    Set-Location backend
}
docker build -t $IMAGE_NAME .
if (-not $?) {
    Write-Host "Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "Docker image built" -ForegroundColor Green

Write-Host "`n[5/7] Pushing to Container Registry..." -ForegroundColor Yellow
docker push $IMAGE_NAME
if (-not $?) {
    Write-Host "Docker push failed" -ForegroundColor Red
    exit 1
}
Write-Host "Image pushed" -ForegroundColor Green

Write-Host "`n[6/7] Deploying to Cloud Run..." -ForegroundColor Yellow
$envVars = "PROJECT_ID=$PROJECT_ID,GCS_INPUT_BUCKET=$BUCKET_NAME,GCS_OUTPUT_BUCKET=$BUCKET_NAME,DOCAI_PROCESSOR_ID=$DOCAI_PROCESSOR_ID,DOCAI_LOCATION=$DOCAI_LOCATION,FIREBASE_PROJECT_ID=$PROJECT_ID"

gcloud run deploy $SERVICE_NAME --image $IMAGE_NAME --platform managed --region $REGION --allow-unauthenticated --memory 2Gi --cpu 2 --timeout 540 --set-env-vars $envVars --project $PROJECT_ID

if (-not $?) {
    Write-Host "Deployment failed" -ForegroundColor Red
    exit 1
}
Write-Host "Deployment successful" -ForegroundColor Green

Write-Host "`n[7/7] Getting service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)" --project $PROJECT_ID

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "=== DEPLOYMENT SUCCESSFUL ===" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URL: $serviceUrl" -ForegroundColor Cyan
Write-Host ""
