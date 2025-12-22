# Step 2: Deploy to Cloud Run (Run this after build completes)
# This script deploys the already-built image to Cloud Run

$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-to-word-converter"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan
Write-Host "⚠️ Note: MongoDB URI not set - database features will be disabled (this is OK for now)" -ForegroundColor Yellow
Write-Host ""

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE_NAME `
  --platform managed `
  --region $REGION `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --allow-unauthenticated `
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" `
  --port 8080

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    
    # Get service URL
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
    Write-Host "🌐 Service URL: $SERVICE_URL" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📝 Next Steps:" -ForegroundColor Yellow
    Write-Host "1. MongoDB Atlas me database create karein" -ForegroundColor White
    Write-Host "2. Cloud Run Console me jao: https://console.cloud.google.com/run?project=$PROJECT_ID" -ForegroundColor White
    Write-Host "3. Service '$SERVICE_NAME' par click karein" -ForegroundColor White
    Write-Host "4. 'EDIT & DEPLOY NEW REVISION' click karein" -ForegroundColor White
    Write-Host "5. 'Variables & Secrets' section me MONGODB_URI add karein" -ForegroundColor White
    Write-Host "6. Redeploy karein" -ForegroundColor White
    Write-Host ""
    Write-Host "✅ Server ab MongoDB ke bina bhi kaam kar raha hai (database features disabled)" -ForegroundColor Green
}

