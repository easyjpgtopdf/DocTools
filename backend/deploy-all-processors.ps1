# PowerShell script to deploy PDF to Excel backend with all Document AI processors
# This script sets all environment variables for multi-processor support

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying PDF to Excel Backend" -ForegroundColor Cyan
Write-Host "with Multi-Processor Document AI Support" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Project configuration
$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "pdf-to-excel-backend"
$REGION = "us-central1"
$IMAGE = "gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

# Document AI Configuration
$DOCAI_PROJECT_ID = "easyjpgtopdf-de346"
$DOCAI_LOCATION = "us"
$GCS_BUCKET = "easyjpgtopdf-excel-exports"

# Processor IDs
$DOCAI_PROCESSOR_ID = "19a07dc1c08ce733"  # Default PDF to Excel
$DOCAI_FORM_PARSER_ID = "9d1bf7e36946b781"
$DOCAI_LAYOUT_PARSER_ID = "c79eead38f3ecc38"
$DOCAI_BANK_ID = "6c8a0e5d0a3dddc4"
$DOCAI_EXPENSE_ID = "3ac96b4ba3725046"
$DOCAI_IDENTITY_ID = "bd5e8109cd2ff2b9"
$DOCAI_PAY_SLIP_ID = "9034bca37aa74cff"
$DOCAI_UTILITY_ID = "1c17582a99ad32d8"
$DOCAI_W2_ID = "3090005e272cc32"
$DOCAI_W9_ID = "91a5f06965a4a7a5"

# Optional: AWS S3 for Textract fallback (leave empty if not using)
$S3_BUCKET = ""
$AWS_ACCESS_KEY_ID = ""
$AWS_SECRET_ACCESS_KEY = ""
$AWS_REGION = "us-east-1"

Write-Host "Step 1: Building Docker image..." -ForegroundColor Yellow
docker build -t $IMAGE .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Step 2: Pushing image to GCR..." -ForegroundColor Yellow
docker push $IMAGE

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker push failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Step 3: Deploying to Cloud Run..." -ForegroundColor Yellow

# Build environment variables string
$envVars = @(
    "DOCAI_PROJECT_ID=$DOCAI_PROJECT_ID",
    "DOCAI_LOCATION=$DOCAI_LOCATION",
    "GCS_BUCKET=$GCS_BUCKET",
    "DOCAI_PROCESSOR_ID=$DOCAI_PROCESSOR_ID",
    "DOCAI_FORM_PARSER_ID=$DOCAI_FORM_PARSER_ID",
    "DOCAI_LAYOUT_PARSER_ID=$DOCAI_LAYOUT_PARSER_ID",
    "DOCAI_BANK_ID=$DOCAI_BANK_ID",
    "DOCAI_EXPENSE_ID=$DOCAI_EXPENSE_ID",
    "DOCAI_IDENTITY_ID=$DOCAI_IDENTITY_ID",
    "DOCAI_PAY_SLIP_ID=$DOCAI_PAY_SLIP_ID",
    "DOCAI_UTILITY_ID=$DOCAI_UTILITY_ID",
    "DOCAI_W2_ID=$DOCAI_W2_ID",
    "DOCAI_W9_ID=$DOCAI_W9_ID"
)

# Add AWS variables if provided
if ($S3_BUCKET -and $AWS_ACCESS_KEY_ID -and $AWS_SECRET_ACCESS_KEY) {
    Write-Host "Adding AWS S3 configuration for Textract fallback..." -ForegroundColor Green
    $envVars += "S3_BUCKET=$S3_BUCKET"
    $envVars += "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
    $envVars += "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
    $envVars += "AWS_REGION=$AWS_REGION"
} else {
    Write-Host "Skipping AWS S3 configuration (Textract will be disabled)" -ForegroundColor Yellow
}

# Build gcloud command
$gcloudCmd = "gcloud run deploy $SERVICE_NAME " +
    "--image $IMAGE " +
    "--platform managed " +
    "--region $REGION " +
    "--allow-unauthenticated " +
    "--memory 1Gi " +
    "--cpu 1 " +
    "--timeout 300 " +
    "--max-instances 10"

# Add environment variables
foreach ($envVar in $envVars) {
    $gcloudCmd += " --set-env-vars $envVar"
}

Write-Host "Deploying with environment variables..." -ForegroundColor Cyan
Invoke-Expression $gcloudCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ Deployment Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Service URL:" -ForegroundColor Cyan
    gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
    Write-Host ""
    Write-Host "Available Processors:" -ForegroundColor Cyan
    Write-Host "  - form-parser-docai" -ForegroundColor White
    Write-Host "  - layout-parser-docai" -ForegroundColor White
    Write-Host "  - bank-docai" -ForegroundColor White
    Write-Host "  - expense-docai" -ForegroundColor White
    Write-Host "  - identity-docai" -ForegroundColor White
    Write-Host "  - pay-slip-docai" -ForegroundColor White
    Write-Host "  - utility-docai" -ForegroundColor White
    Write-Host "  - w2-docai" -ForegroundColor White
    Write-Host "  - w9-docai" -ForegroundColor White
    Write-Host "  - pdf-to-excel-docai (default)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "Deployment failed!" -ForegroundColor Red
    exit 1
}

