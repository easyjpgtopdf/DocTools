# Quick Deployment Script for PDF Editor
# Run this script to deploy backend and frontend

Write-Host "🚀 PDF Editor Deployment Script" -ForegroundColor Green
Write-Host ""

# Step 1: Get Project ID
$PROJECT_ID = "easyjpgtopdf-de346"
Write-Host "Using Project ID: $PROJECT_ID" -ForegroundColor Green

$REGION = Read-Host "Enter region (default: us-central1)" 
if ([string]::IsNullOrWhiteSpace($REGION)) {
    $REGION = "us-central1"
}

$SERVICE_NAME = "pdf-editor-service"
$IMAGE_NAME = "gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

Write-Host ""
Write-Host "📋 Configuration:" -ForegroundColor Blue
Write-Host "  Project ID: $PROJECT_ID"
Write-Host "  Region: $REGION"
Write-Host "  Service: $SERVICE_NAME"
Write-Host ""

# Step 2: Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

$checks = @{
    "gcloud" = Get-Command gcloud -ErrorAction SilentlyContinue
    "docker" = Get-Command docker -ErrorAction SilentlyContinue
    "vercel" = Get-Command vercel -ErrorAction SilentlyContinue
}

foreach ($check in $checks.GetEnumerator()) {
    if ($check.Value) {
        Write-Host "  ✅ $($check.Key) installed" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($check.Key) not found" -ForegroundColor Red
        if ($check.Key -eq "gcloud") {
            Write-Host "    Install: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
        } elseif ($check.Key -eq "docker") {
            Write-Host "    Install: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        } elseif ($check.Key -eq "vercel") {
            Write-Host "    Install: npm i -g vercel" -ForegroundColor Yellow
        }
    }
}

Write-Host ""

# Step 3: Deploy Backend
$deployBackend = Read-Host "Deploy backend to Cloud Run? (Y/n)"
if ($deployBackend -ne "n" -and $deployBackend -ne "N") {
    Write-Host ""
    Write-Host "📦 Building Docker image..." -ForegroundColor Yellow
    Set-Location pdf-editor-backend
    
    docker build -t $IMAGE_NAME .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker build failed!" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    
    Write-Host "📤 Pushing to Google Container Registry..." -ForegroundColor Yellow
    docker push $IMAGE_NAME
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker push failed!" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    
    Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Yellow
    gcloud run deploy $SERVICE_NAME `
        --image $IMAGE_NAME `
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
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Cloud Run deployment failed!" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
    
    Set-Location ..
    Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green
    $BACKEND_URL = "https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app"
    Write-Host "   Backend URL: $BACKEND_URL" -ForegroundColor Cyan
} else {
    $BACKEND_URL = Read-Host "Enter existing backend URL"
}

Write-Host ""

# Step 4: Update Frontend
Write-Host "📝 Updating frontend configuration..." -ForegroundColor Yellow

# Update backend URL in API client
$apiFile = "js/pdf-editor-api.js"
if (Test-Path $apiFile) {
    $content = Get-Content $apiFile -Raw
    $content = $content -replace "https://pdf-editor-service-YOUR_PROJECT_ID.a.run.app", $BACKEND_URL
    $content = $content -replace "https://pdf-editor-service-.*\.a\.run\.app", $BACKEND_URL
    Set-Content $apiFile $content
    Write-Host "✅ Updated backend URL in $apiFile" -ForegroundColor Green
} else {
    Write-Host "⚠️  $apiFile not found, please update manually" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Deploy Frontend
$deployFrontend = Read-Host "Deploy frontend to Vercel? (Y/n)"
if ($deployFrontend -ne "n" -and $deployFrontend -ne "N") {
    Write-Host ""
    Write-Host "🌐 Setting Vercel environment variable..." -ForegroundColor Yellow
    echo $BACKEND_URL | vercel env add PDF_EDITOR_BACKEND_URL production
    
    Write-Host "🚀 Deploying to Vercel..." -ForegroundColor Yellow
    vercel --prod --yes
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Vercel deployment failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Frontend deployed successfully!" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Blue
Write-Host "  Backend URL: $BACKEND_URL" -ForegroundColor Cyan
Write-Host "  Frontend: https://easyjpgtopdf.com/pdf-editor-preview.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "🧪 Test your deployment:" -ForegroundColor Yellow
Write-Host "  1. Open: https://easyjpgtopdf.com/pdf-editor-preview.html"
Write-Host "  2. Upload a PDF"
Write-Host "  3. Test add/edit/delete text"
Write-Host "  4. Verify daily limit (5 pages)"
Write-Host "  5. Test OCR and export"
Write-Host ""
Write-Host "📊 Monitor logs:" -ForegroundColor Yellow
Write-Host "  gcloud run services logs read $SERVICE_NAME --region $REGION"
Write-Host ""

