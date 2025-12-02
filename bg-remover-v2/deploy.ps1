# Deployment Script for Background Remover V2
# Deploys to Google Cloud Run with 8GB memory and 4 CPU

Write-Host "=== Background Remover V2 Deployment ===" -ForegroundColor Cyan

# Configuration
$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "bg-remover-api-v2"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
$MEMORY = "8Gi"
$CPU = "4"
$TIMEOUT = "300"
$MAX_INSTANCES = "10"
$MIN_INSTANCES = "1"

Write-Host "`nConfiguration:" -ForegroundColor Yellow
Write-Host "  Project: $PROJECT_ID" -ForegroundColor White
Write-Host "  Service: $SERVICE_NAME" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White
Write-Host "  Memory: $MEMORY" -ForegroundColor White
Write-Host "  CPU: $CPU" -ForegroundColor White
Write-Host "  Image: $IMAGE_NAME" -ForegroundColor White

# Step 1: Build Docker image
Write-Host "`n=== Step 1: Building Docker Image ===" -ForegroundColor Cyan
Set-Location backend
gcloud builds submit --tag $IMAGE_NAME .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Build successful" -ForegroundColor Green
Set-Location ..

# Step 2: Deploy to Cloud Run
Write-Host "`n=== Step 2: Deploying to Cloud Run ===" -ForegroundColor Cyan
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --memory $MEMORY `
    --cpu $CPU `
    --timeout $TIMEOUT `
    --max-instances $MAX_INSTANCES `
    --min-instances $MIN_INSTANCES `
    --allow-unauthenticated

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Deployment successful" -ForegroundColor Green

# Step 3: Get service URL
Write-Host "`n=== Step 3: Getting Service URL ===" -ForegroundColor Cyan
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green

# Step 4: Test service
Write-Host "`n=== Step 4: Testing Service ===" -ForegroundColor Cyan
Start-Sleep -Seconds 15
try {
    $response = Invoke-WebRequest -Uri "$SERVICE_URL/" -Method GET -Headers @{"Accept"="application/json"} -TimeoutSec 20
    Write-Host "✅ Service is working! Status: $($response.StatusCode)" -ForegroundColor Green
    $json = $response.Content | ConvertFrom-Json
    Write-Host "Service: $($json.service)" -ForegroundColor White
    Write-Host "Status: $($json.status)" -ForegroundColor White
    Write-Host "Model: $($json.model)" -ForegroundColor White
} catch {
    Write-Host "❌ Service test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Update Vercel proxy with new URL: $SERVICE_URL" -ForegroundColor White
Write-Host "2. Test the frontend page" -ForegroundColor White
Write-Host "3. Update sitemap.xml if needed" -ForegroundColor White

