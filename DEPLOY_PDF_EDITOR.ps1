# Complete PDF Editor Deployment Script
# Deploys backend to Cloud Run and frontend to Vercel

Write-Host "🚀 PDF Editor Complete Deployment" -ForegroundColor Green
Write-Host ""

$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-editor-service"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Step 1: Check Docker
Write-Host "🔍 Step 1: Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "  ✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker Desktop is not running!" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop and run this script again." -ForegroundColor Yellow
    exit 1
}

# Step 2: Verify backend files
Write-Host "`n🔍 Step 2: Verifying backend structure..." -ForegroundColor Yellow
$backendFiles = @(
    "pdf-editor-backend/app/main.py",
    "pdf-editor-backend/app/models.py",
    "pdf-editor-backend/app/pdf_engine.py",
    "pdf-editor-backend/app/ocr_engine.py",
    "pdf-editor-backend/app/storage.py",
    "pdf-editor-backend/Dockerfile",
    "pdf-editor-backend/requirements.txt"
)

$allPresent = $true
foreach ($file in $backendFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file MISSING" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host "`n❌ Backend files are missing. Please check the structure." -ForegroundColor Red
    exit 1
}

# Step 3: Build Docker image
Write-Host "`n📦 Step 3: Building Docker image..." -ForegroundColor Yellow
Set-Location pdf-editor-backend

docker build -t $IMAGE_NAME:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Docker build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Write-Host "  ✅ Docker image built successfully" -ForegroundColor Green

# Step 4: Push to GCR
Write-Host "`n📤 Step 4: Pushing to Google Container Registry..." -ForegroundColor Yellow
docker push $IMAGE_NAME:latest
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Docker push failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Write-Host "  ✅ Image pushed successfully" -ForegroundColor Green

# Step 5: Deploy to Cloud Run
Write-Host "`n🚀 Step 5: Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME:latest `
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
    Write-Host "  ❌ Cloud Run deployment failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Get the service URL
$BACKEND_URL = "https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app"
Write-Host "  ✅ Backend deployed successfully!" -ForegroundColor Green
Write-Host "  📍 Backend URL: $BACKEND_URL" -ForegroundColor Cyan

Set-Location ..

# Step 6: Test backend health
Write-Host "`n🧪 Step 6: Testing backend health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BACKEND_URL/health" -Method GET -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ Backend is healthy!" -ForegroundColor Green
        Write-Host "  Response: $($response.Content)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠️  Health check failed (service may still be starting)" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
}

# Step 7: Update frontend with backend URL
Write-Host "`n📝 Step 7: Updating frontend configuration..." -ForegroundColor Yellow
$apiFile = "js/pdf-editor-api.js"
if (Test-Path $apiFile) {
    $content = Get-Content $apiFile -Raw
    # Update the default backend URL
    $content = $content -replace "https://pdf-editor-service-\d+\.us-central1\.run\.app", $BACKEND_URL
    $content = $content -replace "https://pdf-editor-service-.*\.a\.run\.app", $BACKEND_URL
    Set-Content $apiFile $content -NoNewline
    Write-Host "  ✅ Updated backend URL in $apiFile" -ForegroundColor Green
    Write-Host "  New URL: $BACKEND_URL" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠️  $apiFile not found" -ForegroundColor Yellow
}

# Step 8: Deploy to GitHub (if git is available)
Write-Host "`n📦 Step 8: Preparing for GitHub deployment..." -ForegroundColor Yellow
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitStatus = git status --porcelain 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Git repository detected" -ForegroundColor Green
        Write-Host "  💡 To deploy to GitHub, run:" -ForegroundColor Yellow
        Write-Host "     git add ." -ForegroundColor White
        Write-Host "     git commit -m 'Deploy PDF Editor backend and frontend'" -ForegroundColor White
        Write-Host "     git push origin main" -ForegroundColor White
    } else {
        Write-Host "  ⚠️  Not a git repository" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  Git not found" -ForegroundColor Yellow
}

# Step 9: Deploy to Vercel
Write-Host "`n🌐 Step 9: Deploying frontend to Vercel..." -ForegroundColor Yellow
if (Get-Command vercel -ErrorAction SilentlyContinue) {
    Write-Host "  Setting environment variable..." -ForegroundColor Gray
    echo $BACKEND_URL | vercel env add PDF_EDITOR_BACKEND_URL production 2>&1 | Out-Null
    
    Write-Host "  Deploying to Vercel..." -ForegroundColor Gray
    vercel --prod --yes 2>&1 | Tee-Object -Variable vercelOutput
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Frontend deployed to Vercel!" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Vercel deployment may have issues" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠️  Vercel CLI not found. Install with: npm i -g vercel" -ForegroundColor Yellow
    Write-Host "  💡 Or deploy manually at: https://vercel.com" -ForegroundColor Yellow
}

# Summary
Write-Host "`n🎉 DEPLOYMENT SUMMARY" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "✅ Backend: $BACKEND_URL" -ForegroundColor Cyan
Write-Host "✅ Frontend: https://easyjpgtopdf.com/pdf-editor-preview.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "🧪 Test Your Deployment:" -ForegroundColor Yellow
Write-Host "  1. Health Check: $BACKEND_URL/health" -ForegroundColor White
Write-Host "  2. Open: https://easyjpgtopdf.com/pdf-editor-preview.html" -ForegroundColor White
Write-Host "  3. Upload a PDF and test editing" -ForegroundColor White
Write-Host ""
Write-Host "📊 Monitor Backend:" -ForegroundColor Yellow
Write-Host "  gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50" -ForegroundColor White
Write-Host ""
Write-Host "🔧 API Endpoints:" -ForegroundColor Yellow
Write-Host "  POST $BACKEND_URL/session/start" -ForegroundColor White
Write-Host "  POST $BACKEND_URL/page/render" -ForegroundColor White
Write-Host "  POST $BACKEND_URL/text/add" -ForegroundColor White
Write-Host "  POST $BACKEND_URL/text/edit" -ForegroundColor White
Write-Host "  POST $BACKEND_URL/text/delete" -ForegroundColor White
Write-Host "  POST $BACKEND_URL/ocr/page" -ForegroundColor White
Write-Host "  POST $BACKEND_URL/export" -ForegroundColor White
Write-Host ""

