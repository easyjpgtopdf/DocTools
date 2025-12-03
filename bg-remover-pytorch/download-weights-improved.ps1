# ============================================
# Download U2Net Full Pre-trained Weights
# Improved version with retry logic
# ============================================

$ErrorActionPreference = "Stop"

Write-Host "=== Downloading U2Net Full Pre-trained Weights ===" -ForegroundColor Green
Write-Host "U2Net Full provides better quality than U2NetP" -ForegroundColor Yellow

$WEIGHTS_URL = "https://github.com/xuebinqin/U-2-Net/releases/download/v1.0/u2net.pth"
$OUTPUT_DIR = "backend"
$OUTPUT_FILE = Join-Path $OUTPUT_DIR "u2net.pth"

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
Write-Host "This may take 2-5 minutes (file size ~173 MB)..." -ForegroundColor Yellow
Write-Host "If download fails, you can download manually from the URL above" -ForegroundColor Yellow
Write-Host ""

$maxRetries = 3
$retryCount = 0
$success = $false

while ($retryCount -lt $maxRetries -and -not $success) {
    try {
        if ($retryCount -gt 0) {
            Write-Host "Retry attempt $retryCount/$maxRetries..." -ForegroundColor Yellow
        }
        
        # Use BITS (Background Intelligent Transfer Service) for better reliability
        $ProgressPreference = 'SilentlyContinue'
        
        # Try with Invoke-WebRequest first
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($WEIGHTS_URL, $OUTPUT_FILE)
        $webClient.Dispose()
        
        if (Test-Path $OUTPUT_FILE) {
            $fileSize = (Get-Item $OUTPUT_FILE).Length / 1MB
            if ($fileSize -gt 100) {  # Should be ~173 MB
                Write-Host ""
                Write-Host "✅ Download successful!" -ForegroundColor Green
                Write-Host "   File: $OUTPUT_FILE" -ForegroundColor White
                Write-Host "   Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor White
                Write-Host ""
                Write-Host "📋 Next Steps:" -ForegroundColor Yellow
                Write-Host "   1. Rebuild Docker image: cd backend; gcloud builds submit --tag gcr.io/easyjpgtopdf-de346/bg-remover-pytorch-u2net ." -ForegroundColor White
                Write-Host "   2. Redeploy to Cloud Run: cd ..; .\deploy.ps1" -ForegroundColor White
                Write-Host ""
                Write-Host "✅ Weights ready for deployment!" -ForegroundColor Green
                $success = $true
            } else {
                $sizeRounded = [math]::Round($fileSize, 2)
                Write-Host "❌ Downloaded file too small ($sizeRounded MB). Expected ~173 MB." -ForegroundColor Red
                Remove-Item $OUTPUT_FILE -Force
                $retryCount++
            }
        } else {
            Write-Host "❌ Download failed - file not found" -ForegroundColor Red
            $retryCount++
        }
    } catch {
        Write-Host "❌ Download attempt $($retryCount + 1) failed: $($_.Exception.Message)" -ForegroundColor Red
        if (Test-Path $OUTPUT_FILE) {
            Remove-Item $OUTPUT_FILE -Force
        }
        $retryCount++
        
        if ($retryCount -lt $maxRetries) {
            Write-Host "Waiting 10 seconds before retry..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
    }
}

if (-not $success) {
    Write-Host ""
    Write-Host "❌ All download attempts failed." -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Manual download" -ForegroundColor Yellow
    Write-Host "   1. Visit: $WEIGHTS_URL" -ForegroundColor White
    Write-Host "   2. Save to: $OUTPUT_FILE" -ForegroundColor White
    Write-Host "   3. Then redeploy: cd bg-remover-pytorch; .\deploy.ps1" -ForegroundColor White
    exit 1
}

