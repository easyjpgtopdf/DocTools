# Deployment Script for PDF to Excel Backend
# Deploys to Google Cloud Run

$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-to-excel-backend"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🚀 Deploying PDF to Excel Backend" -ForegroundColor Cyan
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
    --set-env-vars GCS_BUCKET=easyjpgtopdf-excel-exports `
    --set-env-vars DOCAI_PROCESSOR_ID=19a07dc1c08ce733 `
    --set-env-vars DOCAI_FORM_PARSER_ID=9d1bf7e36946b781 `
    --set-env-vars DOCAI_LAYOUT_PARSER_ID=c79eead38f3ecc38 `
    --set-env-vars DOCAI_BANK_ID=6c8a0e5d0a3dddc4 `
    --set-env-vars DOCAI_EXPENSE_ID=3ac96b4ba3725046 `
    --set-env-vars DOCAI_IDENTITY_ID=bd5e8109cd2ff2b9 `
    --set-env-vars DOCAI_PAY_SLIP_ID=9034bca37aa74cff `
    --set-env-vars DOCAI_UTILITY_ID=1c17582a99ad32d8 `
    --set-env-vars DOCAI_W2_ID=3090005e272cc32 `
    --set-env-vars DOCAI_W9_ID=91a5f06965a4a7a5 `
    --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Deployment successful!" -ForegroundColor Green
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID
    Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

