# Delete PyTorch Background Removal Service from Google Cloud Run
# This script removes the unused PyTorch backend service

$ErrorActionPreference = "Stop"

Write-Host "=== Deleting PyTorch Background Removal Service from Cloud Run ===" -ForegroundColor Yellow

# --- Configuration ---
$PROJECT_ID = "easyjpgtopdf-de346"
$SERVICE_NAME = "bg-remover-pytorch-u2net"
$REGION = "us-central1"

Write-Host "`nConfiguration:" -ForegroundColor Cyan
Write-Host "  Project: $PROJECT_ID" -ForegroundColor White
Write-Host "  Service: $SERVICE_NAME" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White

# Confirm deletion
Write-Host "`n⚠️  WARNING: This will permanently delete the service!" -ForegroundColor Red
$confirm = Read-Host "Are you sure you want to delete the service? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "`n❌ Deletion cancelled." -ForegroundColor Yellow
    exit 0
}

# Set project
Write-Host "`n=== Setting Google Cloud Project ===" -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# Check if service exists
Write-Host "`n=== Checking if service exists ===" -ForegroundColor Cyan
$serviceExists = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(metadata.name)" 2>$null

if (-not $serviceExists) {
    Write-Host "✅ Service '$SERVICE_NAME' does not exist. Nothing to delete." -ForegroundColor Green
    exit 0
}

# Delete service
Write-Host "`n=== Deleting Cloud Run Service ===" -ForegroundColor Cyan
Write-Host "Deleting service: $SERVICE_NAME" -ForegroundColor White

try {
    gcloud run services delete $SERVICE_NAME `
        --region $REGION `
        --quiet
    
    Write-Host "`n✅ Service '$SERVICE_NAME' deleted successfully!" -ForegroundColor Green
} catch {
    Write-Host "`n❌ Error deleting service: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Optional: Delete container image from GCR
Write-Host "`n=== Checking for container images ===" -ForegroundColor Cyan
$imageName = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
Write-Host "Image name: $imageName" -ForegroundColor White

$deleteImage = Read-Host "Do you also want to delete the container image from GCR? (yes/no)"
if ($deleteImage -eq "yes") {
    try {
        Write-Host "Deleting image: $imageName" -ForegroundColor White
        gcloud container images delete $imageName --quiet --force-delete-tags
        Write-Host "✅ Image deleted successfully!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Could not delete image (may not exist): $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`n=== ✅ Cleanup Complete ===" -ForegroundColor Green
Write-Host "`nNote: The code in 'bg-remover-pytorch' folder is not deleted." -ForegroundColor Cyan
Write-Host "      Only the Cloud Run service has been removed." -ForegroundColor Cyan

