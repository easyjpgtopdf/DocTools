# Adobe PDF Extract API Credentials Setup Script
# Run this script to add Adobe credentials to Google Cloud Run
# 
# Usage:
#   .\add-adobe-credentials.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Adobe PDF Extract API - Credentials Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if user has credentials
Write-Host "Do you have Adobe PDF Extract API credentials?" -ForegroundColor Yellow
Write-Host "Get them from: https://developer.adobe.com/console" -ForegroundColor White
Write-Host ""

# Prompt for credentials
Write-Host "Enter your Adobe Client ID:" -ForegroundColor Green
$ADOBE_CLIENT_ID = Read-Host

Write-Host "Enter your Adobe Client Secret (will be hidden):" -ForegroundColor Green
$ADOBE_CLIENT_SECRET_SECURE = Read-Host -AsSecureString
$ADOBE_CLIENT_SECRET = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($ADOBE_CLIENT_SECRET_SECURE))

# Validate inputs
if ([string]::IsNullOrWhiteSpace($ADOBE_CLIENT_ID)) {
    Write-Host "ERROR: Adobe Client ID cannot be empty!" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrWhiteSpace($ADOBE_CLIENT_SECRET)) {
    Write-Host "ERROR: Adobe Client Secret cannot be empty!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Adding credentials to Google Cloud Run..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Cloud Run service details
$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-to-excel-backend"
$REGION = "us-central1"

# Add environment variables to Cloud Run
Write-Host "Running: gcloud run services update $SERVICE_NAME..." -ForegroundColor White

$env_vars = "ADOBE_CLIENT_ID=$ADOBE_CLIENT_ID,ADOBE_CLIENT_SECRET=$ADOBE_CLIENT_SECRET"

try {
    gcloud run services update $SERVICE_NAME `
        --project=$PROJECT_ID `
        --region=$REGION `
        --update-env-vars=$env_vars `
        --quiet

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✅ SUCCESS: Adobe credentials added to Cloud Run!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Adobe fallback is now ACTIVE and will trigger for:" -ForegroundColor White
    Write-Host "  - Documents with Document AI confidence less than 0.65" -ForegroundColor White
    Write-Host "  - Complex PDFs (merged cells, mixed content)" -ForegroundColor White
    Write-Host "  - Premium plan users" -ForegroundColor White
    Write-Host ""
    Write-Host "Monitor logs for: 'ADOBE FALLBACK: Triggered'" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "❌ ERROR: Failed to add credentials" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if you're logged in: gcloud auth list" -ForegroundColor White
    Write-Host "2. Check project: gcloud config get-value project" -ForegroundColor White
    Write-Host "3. Log in if needed: gcloud auth login" -ForegroundColor White
    Write-Host "4. Set project: gcloud config set project $PROJECT_ID" -ForegroundColor White
    exit 1
}

Write-Host "Verifying deployment..." -ForegroundColor Cyan
Write-Host ""

# Get current service configuration
gcloud run services describe $SERVICE_NAME `
    --project=$PROJECT_ID `
    --region=$REGION `
    --format="value(spec.template.spec.containers[0].env)" `
    | Select-String -Pattern "ADOBE"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test with a complex PDF at:" -ForegroundColor White
Write-Host "   https://www.easyjpgtopdf.com/pdf-to-excel-premium.html" -ForegroundColor White
Write-Host ""
Write-Host "2. Check logs for Adobe fallback:" -ForegroundColor White
Write-Host "   gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND textPayload=~\"ADOBE\"' --limit=50 --project=$PROJECT_ID" -ForegroundColor White
Write-Host ""

