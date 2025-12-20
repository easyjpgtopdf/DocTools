# PowerShell Deployment Script for Background Removal Service
# Usage: .\DEPLOY_NOW.ps1 -ProjectId "YOUR_PROJECT_ID" -Region "us-central1"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1"
)

$ServiceName = "bg-removal-birefnet"
$ImageName = "gcr.io/$ProjectId/$ServiceName"

Write-Host "🚀 Starting Cloud Run Deployment..." -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Service: $ServiceName" -ForegroundColor Yellow
Write-Host ""

# Set project
Write-Host "📋 Setting project to $ProjectId..." -ForegroundColor Cyan
gcloud config set project $ProjectId

# Build Docker image
Write-Host ""
Write-Host "📦 Building Docker image..." -ForegroundColor Cyan
docker build -t $ImageName .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

# Push to Google Container Registry
Write-Host ""
Write-Host "📤 Pushing image to GCR..." -ForegroundColor Cyan
docker push $ImageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run with GPU
Write-Host ""
Write-Host "🚀 Deploying to Cloud Run with High-Performance GPU..." -ForegroundColor Cyan
gcloud run deploy $ServiceName `
  --image $ImageName `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --memory 16Gi `
  --cpu 4 `
  --timeout 300 `
  --min-instances 0 `
  --max-instances 3 `
  --gpu=1 `
  --gpu-type=nvidia-l4 `
  --no-gpu-zonal-redundancy `
  --concurrency 1 `
  --port 8080

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cloud Run deployment failed!" -ForegroundColor Red
    exit 1
}

# Get service URL
Write-Host ""
Write-Host "📡 Getting service URL..." -ForegroundColor Cyan
$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format 'value(status.url)'

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Service URL: $ServiceUrl" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Copy the Service URL above" -ForegroundColor White
Write-Host "2. Go to Vercel Dashboard → Settings → Environment Variables" -ForegroundColor White
Write-Host "3. Update CLOUDRUN_API_URL_BG_REMOVAL with: $ServiceUrl" -ForegroundColor White
Write-Host "4. Redeploy Vercel frontend (if needed)" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test endpoint:" -ForegroundColor Cyan
Write-Host "curl -X POST ${ServiceUrl}/health" -ForegroundColor White
Write-Host ""

