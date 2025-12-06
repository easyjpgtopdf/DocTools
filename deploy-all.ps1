# Complete Deployment Script for PDF Editor (PowerShell)
# Deploys backend to Cloud Run and frontend to Vercel

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Complete Deployment..." -ForegroundColor Green

# Configuration
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "your-project-id" }
$SERVICE_NAME = "pdf-editor-service"
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$BACKEND_URL = "https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app"

Write-Host "Configuration:" -ForegroundColor Blue
Write-Host "  Project ID: $PROJECT_ID"
Write-Host "  Service Name: $SERVICE_NAME"
Write-Host "  Region: $REGION"
Write-Host "  Backend URL: $BACKEND_URL"
Write-Host ""

# Check if required tools are installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI not installed" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker not installed" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Vercel CLI not installed. Install with: npm i -g vercel" -ForegroundColor Red
    exit 1
}

# Step 1: Deploy Backend to Cloud Run
Write-Host "Step 1: Deploying Backend to Cloud Run..." -ForegroundColor Green
Set-Location pdf-editor-backend

# Build Docker image
Write-Host "Building Docker image..."
docker build -t "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" .

# Push to Google Container Registry
Write-Host "Pushing to Google Container Registry..."
docker push "gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME `
  --image "gcr.io/${PROJECT_ID}/${SERVICE_NAME}" `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --cpu 1 `
  --memory 2Gi `
  --min-instances 0 `
  --max-instances 10 `
  --timeout 300 `
  --concurrency 80 `
  --set-env-vars "API_BASE_URL=https://easyjpgtopdf.com"

Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green
Write-Host "Backend URL: $BACKEND_URL"
Write-Host ""

# Step 2: Update Frontend Configuration
Write-Host "Step 2: Updating Frontend Configuration..." -ForegroundColor Green
Set-Location ..

# Update backend URL in API client
if (Test-Path "js/pdf-editor-api.js") {
    # Create backup
    Copy-Item "js/pdf-editor-api.js" "js/pdf-editor-api.js.bak"
    
    # Update backend URL
    (Get-Content "js/pdf-editor-api.js") -replace "https://pdf-editor-service-YOUR_PROJECT_ID.a.run.app", $BACKEND_URL | Set-Content "js/pdf-editor-api.js"
    Write-Host "Updated backend URL in js/pdf-editor-api.js"
}

# Step 3: Deploy Frontend to Vercel
Write-Host "Step 3: Deploying Frontend to Vercel..." -ForegroundColor Green

# Set environment variable
Write-Host "Setting Vercel environment variable..."
echo $BACKEND_URL | vercel env add PDF_EDITOR_BACKEND_URL production

# Deploy
Write-Host "Deploying to Vercel..."
vercel --prod --yes

Write-Host "✅ Frontend deployed successfully!" -ForegroundColor Green
Write-Host ""

# Step 4: Health Check
Write-Host "Step 4: Verifying Deployment..." -ForegroundColor Green
Start-Sleep -Seconds 5

# Check backend health
Write-Host "Checking backend health..."
try {
    $response = Invoke-WebRequest -Uri "https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app/health" -UseBasicParsing
    if ($response.Content -match "healthy") {
        Write-Host "✅ Backend is healthy!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Backend health check failed" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Backend health check failed: $_" -ForegroundColor Yellow
}

# Step 5: Git Commit (if in git repo)
if (Test-Path ".git") {
    Write-Host "Step 5: Committing changes to Git..." -ForegroundColor Green
    git add .
    git commit -m "Deploy PDF editor with 5 pages/day limit and device tracking" 2>&1 | Out-Null
    git push origin main 2>&1 | Out-Null
}

Write-Host ""
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:"
Write-Host "1. Test the PDF editor at: https://easyjpgtopdf.com/pdf-editor-preview.html"
Write-Host "2. Verify daily limit tracking"
Write-Host "3. Test credit deduction"
Write-Host "4. Monitor Cloud Run logs: gcloud run services logs read $SERVICE_NAME --region $REGION"
Write-Host ""
Write-Host "Backend URL: $BACKEND_URL"
Write-Host "Frontend: https://easyjpgtopdf.com/pdf-editor-preview.html"
