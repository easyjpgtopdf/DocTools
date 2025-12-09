# PDF to Excel Backend - Cloud Run Deployment Script
# Windows PowerShell Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PDF to Excel Backend Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if gcloud is installed
Write-Host "Step 1: Checking Google Cloud SDK..." -ForegroundColor Yellow
try {
    $gcloudVersion = gcloud --version 2>&1 | Select-Object -First 1
    Write-Host "✓ Google Cloud SDK found: $gcloudVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Google Cloud SDK not found. Please install it first." -ForegroundColor Red
    Write-Host "Download from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Step 2: Set project
Write-Host ""
Write-Host "Step 2: Setting GCP project..." -ForegroundColor Yellow
gcloud config set project easyjpgtopdf-de346
Write-Host "✓ Project set to: easyjpgtopdf-de346" -ForegroundColor Green

# Step 3: Get environment variables from user
Write-Host ""
Write-Host "Step 3: Environment Variables Setup" -ForegroundColor Yellow
Write-Host "Please provide the following information:" -ForegroundColor White
Write-Host ""

$AWS_ACCESS_KEY_ID = Read-Host "Enter AWS Access Key ID"
$AWS_SECRET_ACCESS_KEY = Read-Host "Enter AWS Secret Access Key" -AsSecureString
$AWS_SECRET_ACCESS_KEY_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($AWS_SECRET_ACCESS_KEY))

$AWS_REGION = Read-Host "Enter AWS Region (default: us-east-1)"
if ([string]::IsNullOrWhiteSpace($AWS_REGION)) {
    $AWS_REGION = "us-east-1"
}

$S3_BUCKET = Read-Host "Enter S3 Bucket Name (e.g., easyjpgtopdf-pdf-uploads)"
$GCS_BUCKET = Read-Host "Enter GCS Bucket Name (e.g., easyjpgtopdf-excel-exports)"

Write-Host ""
Write-Host "✓ Environment variables collected" -ForegroundColor Green

# Step 4: Enable APIs
Write-Host ""
Write-Host "Step 4: Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com --quiet
gcloud services enable storage-component.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
Write-Host "✓ APIs enabled" -ForegroundColor Green

# Step 5: Build Docker image
Write-Host ""
Write-Host "Step 5: Building Docker image..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor White
docker build -t gcr.io/easyjpgtopdf-de346/pdf-to-excel-backend:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker image built successfully" -ForegroundColor Green

# Step 6: Push to GCR
Write-Host ""
Write-Host "Step 6: Pushing image to Google Container Registry..." -ForegroundColor Yellow
docker push gcr.io/easyjpgtopdf-de346/pdf-to-excel-backend:latest
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker push failed!" -ForegroundColor Red
    Write-Host "Try running: gcloud auth configure-docker" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Image pushed successfully" -ForegroundColor Green

# Step 7: Deploy to Cloud Run
Write-Host ""
Write-Host "Step 7: Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "This may take 2-3 minutes..." -ForegroundColor White

$deployCommand = @"
gcloud run deploy pdf-to-excel-backend `
  --image gcr.io/easyjpgtopdf-de346/pdf-to-excel-backend:latest `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --set-env-vars AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID `
  --set-env-vars AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY_PLAIN `
  --set-env-vars AWS_REGION=$AWS_REGION `
  --set-env-vars S3_BUCKET=$S3_BUCKET `
  --set-env-vars GCS_BUCKET=$GCS_BUCKET `
  --set-env-vars GCP_PROJECT_ID=easyjpgtopdf-de346
"@

Invoke-Expression $deployCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Deployment failed!" -ForegroundColor Red
    exit 1
}

# Step 8: Get service URL
Write-Host ""
Write-Host "Step 8: Getting service URL..." -ForegroundColor Yellow
$serviceUrl = gcloud run services describe pdf-to-excel-backend --region us-central1 --format 'value(status.url)'
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Deployment Successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service URL: $serviceUrl" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Update pdf-to-excel-convert.html (line ~559)" -ForegroundColor White
Write-Host "   Replace API_BASE_URL with: $serviceUrl" -ForegroundColor White
Write-Host ""
Write-Host "2. Test the API:" -ForegroundColor White
Write-Host "   curl $serviceUrl/api/health" -ForegroundColor Gray
Write-Host ""
Write-Host "3. View logs:" -ForegroundColor White
Write-Host "   gcloud run services logs read pdf-to-excel-backend --region us-central1" -ForegroundColor Gray
Write-Host ""

