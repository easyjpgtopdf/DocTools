# Production Deployment Script for PDF to Excel Backend (Windows PowerShell)
# Run this after critical Adobe API fix

$ErrorActionPreference = "Stop"

Write-Host "======================================================================"
Write-Host "🚀 DEPLOYING PDF TO EXCEL BACKEND TO PRODUCTION" -ForegroundColor Cyan
Write-Host "======================================================================"
Write-Host ""

# Configuration
$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-backend"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "📋 Pre-Deployment Checklist" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "1. ✅ Adobe API fix committed and pushed"
Write-Host "2. ✅ Adobe credentials configured in Cloud Run"
Write-Host "3. ⏳ Ready to deploy..."
Write-Host ""

# Prompt for confirmation
$response = Read-Host "Continue with deployment? (y/n)"
if ($response -ne "y" -and $response -ne "Y") {
    Write-Host "❌ Deployment cancelled" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔨 Step 1: Building Docker image..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

try {
    gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker build failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚢 Step 2: Deploying to Cloud Run..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

try {
    gcloud run deploy $SERVICE_NAME `
      --image=$IMAGE_NAME `
      --platform=managed `
      --region=$REGION `
      --project=$PROJECT_ID `
      --allow-unauthenticated `
      --memory=2Gi `
      --cpu=1 `
      --timeout=300s `
      --max-instances=10 `
      --set-env-vars="ADOBE_ENABLED=true,QA_VALIDATION_ENABLED=true,DETAILED_COST_LOGGING=true,AUDIT_TRAIL_ENABLED=true"
    
    Write-Host "✅ Deployment successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Deployment failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔍 Step 3: Verifying deployment..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME `
  --platform=managed `
  --region=$REGION `
  --project=$PROJECT_ID `
  --format='value(status.url)'

Write-Host "Service URL: $SERVICE_URL"

# Test health endpoint
Write-Host "Testing health endpoint..."
try {
    $healthResponse = Invoke-WebRequest -Uri "$SERVICE_URL/health" -UseBasicParsing -TimeoutSec 10
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✅ Health check passed" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Health check warning: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 Step 4: Checking environment variables..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Adobe credentials are set
$envVars = gcloud run services describe $SERVICE_NAME `
  --platform=managed `
  --region=$REGION `
  --project=$PROJECT_ID `
  --format='value(spec.template.spec.containers[0].env)'

if ($envVars -like "*ADOBE_CLIENT_ID*") {
    Write-Host "✅ ADOBE_CLIENT_ID is set" -ForegroundColor Green
} else {
    Write-Host "❌ ADOBE_CLIENT_ID is NOT set" -ForegroundColor Red
}

if ($envVars -like "*ADOBE_CLIENT_SECRET*") {
    Write-Host "✅ ADOBE_CLIENT_SECRET is set" -ForegroundColor Green
} else {
    Write-Host "❌ ADOBE_CLIENT_SECRET is NOT set" -ForegroundColor Red
}

if ($envVars -like "*ADOBE_ENABLED=true*") {
    Write-Host "✅ ADOBE_ENABLED=true" -ForegroundColor Green
} else {
    Write-Host "⚠️  ADOBE_ENABLED may not be true" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📝 Step 5: Checking recent logs..." -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

Write-Host "Fetching last 10 log entries..."
try {
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" `
      --limit=10 `
      --project=$PROJECT_ID `
      --format="table(timestamp,severity,textPayload)"
} catch {
    Write-Host "Could not fetch logs: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================================================"
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "======================================================================"
Write-Host ""
Write-Host "Service URL: $SERVICE_URL"
Write-Host ""
Write-Host "Next Steps:"
Write-Host "1. Test with invoice PDF: $SERVICE_URL/api/pdf-to-excel-docai"
Write-Host "2. Enable premium toggle in frontend"
Write-Host "3. Check Cloud Logging for Adobe API calls"
Write-Host "4. Monitor costs in Adobe Developer Console"
Write-Host ""
Write-Host "Emergency Disable Adobe:"
Write-Host "  gcloud run services update $SERVICE_NAME --set-env-vars='ADOBE_ENABLED=false' --region=$REGION"
Write-Host ""
Write-Host "View Logs:"
Write-Host "  gcloud logging read `"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME`" --limit=50"
Write-Host ""
Write-Host "======================================================================"

