# Deployment Script for PDF to Word Backend
# Deploys to Google Cloud Run

$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-to-word-converter"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🚀 Deploying PDF to Word Backend" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Step 1: Building Docker image..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_NAME --project $PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nStep 2: Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 10 `
    --set-env-vars DOCAI_PROJECT_ID=$PROJECT_ID `
    --set-env-vars DOCAI_LOCATION=us `
    --set-env-vars GCS_BUCKET=easyjpgtopdf-word-exports `
    --set-env-vars DOCAI_PROCESSOR_ID=ffaa7bcd30a9c788 `
    --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Deployment successful!" -ForegroundColor Green
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID
    Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

