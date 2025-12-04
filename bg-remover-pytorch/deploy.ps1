$ErrorActionPreference = "Stop"

Write-Host "=== Starting Deployment for PyTorch U2Net Full Background Remover ===" -ForegroundColor Green

# --- Configuration ---
$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "bg-remover-pytorch-u2net"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
$MEMORY = "1Gi"  # Free tier: 1GB (within 360,000 GB-seconds/month limit)
$CPU = "1"  # Free tier: 1 vCPU (within 180,000 vCPU-seconds/month limit)
$TIMEOUT = "300"  # 5 minutes
$MAX_INSTANCES = "10"
$MIN_INSTANCES = "0"  # Free tier: 0 instances when idle (no always-on cost)
$CONCURRENCY = "1"  # 1 for stability

# --- Build Docker Image ---
Write-Host "`n=== Building Docker Image ===" -ForegroundColor Cyan
Set-Location backend
gcloud builds submit --tag $IMAGE_NAME .

# --- Deploy to Cloud Run ---
Write-Host "`n=== Deploying to Cloud Run ===" -ForegroundColor Cyan
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Memory: $MEMORY" -ForegroundColor White
Write-Host "  CPU: $CPU" -ForegroundColor White
Write-Host "  Timeout: $TIMEOUT seconds" -ForegroundColor White
Write-Host "  Min Instances: $MIN_INSTANCES (Free tier - scales to zero)" -ForegroundColor White
Write-Host "  Concurrency: $CONCURRENCY" -ForegroundColor White

gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --memory $MEMORY `
    --cpu $CPU `
    --timeout $TIMEOUT `
    --max-instances $MAX_INSTANCES `
    --min-instances $MIN_INSTANCES `
    --concurrency $CONCURRENCY `
    --allow-unauthenticated

# --- Get Service URL ---
Write-Host "`n=== Getting Service URL ===" -ForegroundColor Cyan
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)"
Write-Host "✅ Service URL: $SERVICE_URL" -ForegroundColor Green

# --- Test Service ---
Write-Host "`n=== Testing Service Health Endpoint ===" -ForegroundColor Cyan
Start-Sleep -Seconds 20
try {
    $response = Invoke-WebRequest -Uri "$SERVICE_URL/health" -Method GET -Headers @{"Accept"="application/json"} -TimeoutSec 30
    Write-Host "✅ Health check passed! Status: $($response.StatusCode)" -ForegroundColor Green
    $json = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($json.status)" -ForegroundColor White
    Write-Host "Model: $($json.model)" -ForegroundColor White
    Write-Host "Model Loaded: $($json.model_loaded)" -ForegroundColor White
    Write-Host "Device: $($json.device)" -ForegroundColor White
} catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nChecking logs for more details..." -ForegroundColor Yellow
    gcloud run services logs read $SERVICE_NAME --region $REGION --limit 10 --format="value(timestamp,severity,textPayload)" | Select-String -Pattern "ERROR|CRITICAL|WARNING" | Select-Object -Last 10
    exit 1
}

Set-Location ..

Write-Host "`n=== ✅ Deployment Complete ===" -ForegroundColor Green
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "1. Update CLOUDRUN_API_URL in api/background-remove-pytorch.js to: $SERVICE_URL" -ForegroundColor Yellow
Write-Host "2. Update frontend to use /api/background-remove-pytorch endpoint" -ForegroundColor Yellow
Write-Host "3. Update vercel.json with new routes" -ForegroundColor Yellow
Write-Host "`nNote: For best quality, download u2net.pth from official repository" -ForegroundColor Cyan
Write-Host "      https://github.com/xuebinqin/U-2-Net/releases/download/v1.0/u2net.pth" -ForegroundColor Cyan
Write-Host "      U2Net Full (~173 MB) provides better quality than U2NetP (~4.7 MB)" -ForegroundColor Yellow

