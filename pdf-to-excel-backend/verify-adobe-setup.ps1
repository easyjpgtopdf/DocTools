# Verify Adobe PDF Extract API Setup
# This script checks if Adobe credentials are properly configured in Cloud Run
# WITHOUT exposing the actual secret values

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Adobe PDF Extract API - Setup Verification" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-to-excel-backend"
$REGION = "us-central1"

Write-Host "Checking Cloud Run service: $SERVICE_NAME" -ForegroundColor White
Write-Host ""

# Get environment variables from Cloud Run
$env_vars = gcloud run services describe $SERVICE_NAME `
    --project=$PROJECT_ID `
    --region=$REGION `
    --format="value(spec.template.spec.containers[0].env)" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Could not connect to Cloud Run service" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check if you're logged in: gcloud auth list" -ForegroundColor White
    Write-Host "2. Log in if needed: gcloud auth login" -ForegroundColor White
    Write-Host "3. Set project: gcloud config set project $PROJECT_ID" -ForegroundColor White
    exit 1
}

# Check for Adobe credentials
$has_client_id = $env_vars -match "ADOBE_CLIENT_ID"
$has_client_secret = $env_vars -match "ADOBE_CLIENT_SECRET"

Write-Host "Environment Variables Check:" -ForegroundColor Yellow
Write-Host ""

if ($has_client_id) {
    # Extract client ID (safe to show - it's public)
    $client_id_line = $env_vars | Select-String "ADOBE_CLIENT_ID" | Select-Object -First 1
    if ($client_id_line -match "value='([^']+)'") {
        $client_id = $matches[1]
        Write-Host "✅ ADOBE_CLIENT_ID: $client_id" -ForegroundColor Green
    } else {
        Write-Host "✅ ADOBE_CLIENT_ID: Set (value hidden)" -ForegroundColor Green
    }
} else {
    Write-Host "❌ ADOBE_CLIENT_ID: NOT SET" -ForegroundColor Red
}

if ($has_client_secret) {
    # Never show the actual secret value
    Write-Host "✅ ADOBE_CLIENT_SECRET: Set (value hidden for security)" -ForegroundColor Green
} else {
    Write-Host "❌ ADOBE_CLIENT_SECRET: NOT SET" -ForegroundColor Red
}

Write-Host ""

if ($has_client_id -and $has_client_secret) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✅ Adobe PDF Extract API is CONFIGURED and ACTIVE!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Adobe fallback will trigger for:" -ForegroundColor White
    Write-Host "  ✓ Documents with Document AI confidence < 0.65" -ForegroundColor White
    Write-Host "  ✓ Complex PDFs (merged cells, mixed content)" -ForegroundColor White
    Write-Host "  ✓ Premium plan users" -ForegroundColor White
    Write-Host ""
    Write-Host "Test URL:" -ForegroundColor Yellow
    Write-Host "  https://www.easyjpgtopdf.com/pdf-to-excel-premium.html" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Monitor Adobe fallback in logs:" -ForegroundColor Yellow
    Write-Host "  gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND textPayload=~`"ADOBE`"' --limit=10 --project=$PROJECT_ID" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "❌ Adobe PDF Extract API is NOT CONFIGURED" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "System will continue to work using Document AI only." -ForegroundColor Yellow
    Write-Host "Adobe fallback will be skipped for all documents." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To add Adobe credentials, run:" -ForegroundColor White
    Write-Host "  .\add-adobe-credentials.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or manually:" -ForegroundColor White
    Write-Host "  gcloud run services update $SERVICE_NAME ``" -ForegroundColor Cyan
    Write-Host "    --update-env-vars=ADOBE_CLIENT_ID=xxx,ADOBE_CLIENT_SECRET=yyy ``" -ForegroundColor Cyan
    Write-Host "    --region=$REGION --project=$PROJECT_ID" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Verification Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

