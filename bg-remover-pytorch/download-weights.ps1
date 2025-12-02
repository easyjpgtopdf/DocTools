# ============================================
# Download U2NetP Pre-trained Weights
# For Best Quality Background Removal
# ============================================

$ErrorActionPreference = "Stop"

Write-Host "=== Downloading U2NetP Pre-trained Weights ===" -ForegroundColor Green

$WEIGHTS_URL = "https://github.com/xuebinqin/U-2-Net/releases/download/v1.0/u2netp.pth"
$OUTPUT_DIR = "backend"
$OUTPUT_FILE = Join-Path $OUTPUT_DIR "u2netp.pth"

# Create backend directory if it doesn't exist
if (-not (Test-Path $OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $OUTPUT_DIR -Force | Out-Null
    Write-Host "✅ Created $OUTPUT_DIR directory" -ForegroundColor Green
}

# Check if weights already exist
if (Test-Path $OUTPUT_FILE) {
    $fileSize = (Get-Item $OUTPUT_FILE).Length / 1MB
    Write-Host "⚠️ Weights file already exists: $OUTPUT_FILE ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite? (y/N)"
    if ($overwrite -ne 'y' -and $overwrite -ne 'Y') {
        Write-Host "Skipping download." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "📥 Downloading from: $WEIGHTS_URL" -ForegroundColor Cyan
Write-Host "📁 Saving to: $OUTPUT_FILE" -ForegroundColor Cyan
Write-Host ""
Write-Host "This may take a few minutes (file size ~4.7 MB)..." -ForegroundColor Yellow

try {
    # Download using Invoke-WebRequest with progress
    $ProgressPreference = 'Continue'
    Invoke-WebRequest -Uri $WEIGHTS_URL -OutFile $OUTPUT_FILE -UseBasicParsing
    
    if (Test-Path $OUTPUT_FILE) {
        $fileSize = (Get-Item $OUTPUT_FILE).Length / 1MB
        Write-Host ""
        Write-Host "✅ Download successful!" -ForegroundColor Green
        Write-Host "   File: $OUTPUT_FILE" -ForegroundColor White
        Write-Host "   Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor White
        Write-Host ""
        Write-Host "📋 Next Steps:" -ForegroundColor Yellow
        Write-Host "   1. Rebuild Docker image: cd backend; gcloud builds submit --tag gcr.io/easyjpgtopdf-de346/bg-remover-pytorch-u2netp ." -ForegroundColor White
        Write-Host "   2. Redeploy to Cloud Run: cd ..; .\deploy.ps1" -ForegroundColor White
        Write-Host ""
        Write-Host "✅ Weights ready for deployment!" -ForegroundColor Green
    } else {
        Write-Host "❌ Download failed - file not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "❌ Download failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Manual download" -ForegroundColor Yellow
    Write-Host "   1. Visit: https://github.com/xuebinqin/U-2-Net/releases/download/v1.0/u2netp.pth" -ForegroundColor White
    Write-Host "   2. Save to: backend/u2netp.pth" -ForegroundColor White
    exit 1
}
