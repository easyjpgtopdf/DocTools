# PDF to Excel Backend - Quick Deployment Script
# 1 CPU, 1Gi Memory Configuration
# Using Google Document AI

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PDF to Excel Backend Deployment" -ForegroundColor Cyan
Write-Host "Using Google Document AI" -ForegroundColor Yellow
Write-Host "Configuration: 1 CPU, 1Gi Memory" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get Document AI Processor ID
Write-Host "Step 1: Google Document AI Configuration" -ForegroundColor Yellow
Write-Host "Please provide your Document AI processor ID:" -ForegroundColor White
Write-Host "You can create one at: https://console.cloud.google.com/ai/document-ai/processors" -ForegroundColor Gray
Write-Host ""

$DOCAI_PROCESSOR_ID = Read-Host "Enter Document AI Processor ID (from UI, e.g., 19a07dc1c08ce733)"
$DOCAI_PROJECT_ID = "easyjpgtopdf-de346"
$DOCAI_LOCATION = Read-Host "Enter Document AI Location (default: us)"
if ([string]::IsNullOrWhiteSpace($DOCAI_LOCATION)) {
    $DOCAI_LOCATION = "us"
}

Write-Host ""
Write-Host "Document AI configuration:" -ForegroundColor Green
Write-Host "  Project ID: $DOCAI_PROJECT_ID" -ForegroundColor White
Write-Host "  Location: $DOCAI_LOCATION" -ForegroundColor White
Write-Host "  Processor ID: $DOCAI_PROCESSOR_ID" -ForegroundColor White

# Step 2: GCS Bucket (already created)
$GCS_BUCKET = "easyjpgtopdf-excel-exports"
Write-Host ""
Write-Host "Using GCS Bucket: $GCS_BUCKET" -ForegroundColor Green

# Step 3: Deploy to Cloud Run
Write-Host ""
Write-Host "Step 2: Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "This may take 2-3 minutes..." -ForegroundColor White
Write-Host ""

Write-Host "Deploying with configuration:" -ForegroundColor Cyan
Write-Host "  Memory: 1Gi" -ForegroundColor White
Write-Host "  CPU: 1" -ForegroundColor White
Write-Host "  Region: us-central1" -ForegroundColor White
Write-Host "  Document AI Processor: $DOCAI_PROCESSOR_ID" -ForegroundColor White
Write-Host "  GCS Bucket: $GCS_BUCKET" -ForegroundColor White
Write-Host ""

gcloud run deploy pdf-to-excel-backend `
  --image gcr.io/easyjpgtopdf-de346/pdf-to-excel-backend:latest `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10 `
  --set-env-vars DOCAI_PROCESSOR_ID=$DOCAI_PROCESSOR_ID `
  --set-env-vars DOCAI_PROJECT_ID=$DOCAI_PROJECT_ID `
  --set-env-vars DOCAI_LOCATION=$DOCAI_LOCATION `
  --set-env-vars GCS_BUCKET=$GCS_BUCKET

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Deployment failed!" -ForegroundColor Red
    Write-Host "Please check the error above and try again." -ForegroundColor Yellow
    exit 1
}

# Step 4: Get Service URL
Write-Host ""
Write-Host "Step 3: Getting Service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe pdf-to-excel-backend --region us-central1 --format "value(status.url)"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service URL: $serviceUrl" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update pdf-to-excel-convert.html (line 559)" -ForegroundColor White
Write-Host "   Replace API_BASE_URL with: $serviceUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test the API:" -ForegroundColor White
Write-Host "   curl $serviceUrl/api/health" -ForegroundColor Gray
Write-Host ""
Write-Host "3. View logs:" -ForegroundColor White
Write-Host "   gcloud run services logs read pdf-to-excel-backend --region us-central1" -ForegroundColor Gray
Write-Host ""
