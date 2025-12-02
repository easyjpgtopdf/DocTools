$ErrorActionPreference = "Stop"

Write-Host "=== Testing Different onnxruntime Versions ===" -ForegroundColor Green

# Configuration
$PROJECT_ID = "easyjpgtopdf-de346"
$REGION = "us-central1"
$MEMORY = "4Gi"
$CPU = "2"
$TIMEOUT = "300"
$MAX_INSTANCES = "10"
$MIN_INSTANCES = "1"
$CONCURRENCY = "1"

# Versions to test
$versions = @(
    @{name="v1.15.1"; file="requirements-v1.15.1.txt"; dockerfile="Dockerfile.v1.15.1"},
    @{name="v1.14.1"; file="requirements-v1.14.1.txt"; dockerfile="Dockerfile"},
    @{name="v1.13.1"; file="requirements-v1.13.1.txt"; dockerfile="Dockerfile"}
)

Set-Location backend

foreach ($version in $versions) {
    Write-Host "`n=== Testing onnxruntime $($version.name) ===" -ForegroundColor Cyan
    
    $SERVICE_NAME = "bg-remover-rembg-$($version.name)"
    $IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
    
    # Update Dockerfile to use correct requirements file
    if ($version.dockerfile -ne "Dockerfile") {
        Copy-Item $version.dockerfile -Destination Dockerfile -Force
    } else {
        # Update Dockerfile to use correct requirements
        (Get-Content Dockerfile) -replace "requirements.txt", $version.file | Set-Content Dockerfile
    }
    
    # Build Docker Image
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    gcloud builds submit --tag $IMAGE_NAME .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Build failed for $($version.name)" -ForegroundColor Red
        continue
    }
    
    # Deploy to Cloud Run
    Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
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
        --allow-unauthenticated `
        --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Deployment failed for $($version.name)" -ForegroundColor Red
        continue
    }
    
    # Get Service URL
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)"
    Write-Host "✅ Service URL: $SERVICE_URL" -ForegroundColor Green
    
    # Wait for service to start
    Write-Host "Waiting 30 seconds for service to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    # Test Health Endpoint
    Write-Host "Testing health endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$SERVICE_URL/health" -Method GET -Headers @{"Accept"="application/json"} -TimeoutSec 30
        $json = $response.Content | ConvertFrom-Json
        
        if ($json.status -eq "ok") {
            Write-Host "✅ SUCCESS! onnxruntime $($version.name) works!" -ForegroundColor Green
            Write-Host "   Model: $($json.model)" -ForegroundColor White
            Write-Host "   U2Net Available: $($json.u2net_available)" -ForegroundColor White
            Write-Host "   U2NetP Available: $($json.u2netp_available)" -ForegroundColor White
            Write-Host "`n🎉 This version works! Use this for production." -ForegroundColor Green
            break
        } else {
            Write-Host "⚠️ Service responded but status is not 'ok'" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Checking logs..." -ForegroundColor Yellow
        gcloud run services logs read $SERVICE_NAME --region $REGION --limit 10 | Select-String -Pattern "ERROR|CRITICAL|onnxruntime" | Select-Object -Last 5
    }
    
    Write-Host "`n---" -ForegroundColor Gray
}

Set-Location ..

Write-Host "`n=== Testing Complete ===" -ForegroundColor Green
Write-Host "Check the results above to see which version works." -ForegroundColor Yellow

