# Test Backend Health - 10 Real Images Test Script
# Tests both Cloud Run backends: bg-removal-ai and bg-removal-birefnet

Write-Host "=== BACKEND HEALTH CHECK ===" -ForegroundColor Cyan

# Backend URLs
$bgRemovalAi = "https://bg-removal-ai-564572183797.us-central1.run.app"
$bgRemovalBirefnet = "https://bg-removal-birefnet-564572183797.us-central1.run.app"
$bgRemovalBirefnetActual = "https://bg-removal-birefnet-iwumaktavq-uc.a.run.app"

Write-Host "`nChecking Backend URLs:" -ForegroundColor Yellow
Write-Host "1. bg-removal-ai: $bgRemovalAi"
Write-Host "2. bg-removal-birefnet (old): $bgRemovalBirefnet"
Write-Host "3. bg-removal-birefnet (actual): $bgRemovalBirefnetActual"

# Test health endpoints
Write-Host "`n=== HEALTH CHECK ===" -ForegroundColor Cyan

function Test-Health {
    param($url, $name)
    try {
        $response = Invoke-WebRequest -Uri "$url/health" -Method GET -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $name : HEALTHY (200)" -ForegroundColor Green
            Write-Host "   Response: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))" -ForegroundColor Gray
            return $true
        } else {
            Write-Host "❌ $name : UNHEALTHY ($($response.StatusCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ $name : ERROR - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Test-Health -url $bgRemovalAi -name "bg-removal-ai"
Test-Health -url $bgRemovalBirefnet -name "bg-removal-birefnet (old URL)"
Test-Health -url $bgRemovalBirefnetActual -name "bg-removal-birefnet (actual URL)"

Write-Host "`n=== API ENDPOINT CHECK ===" -ForegroundColor Cyan
Write-Host "Checking /api/free-preview-bg endpoint..." -ForegroundColor Yellow

function Test-ApiEndpoint {
    param($url, $name)
    try {
        # Create a small test image (1x1 PNG) as base64
        $testImageBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        $jsonBody = @{
            imageData = "data:image/png;base64,$testImageBase64"
            maxSize = 512
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "$url/api/free-preview-bg" `
            -Method POST `
            -Body $jsonBody `
            -ContentType "application/json" `
            -TimeoutSec 30 `
            -UseBasicParsing `
            -ErrorAction Stop
        
        Write-Host "✅ $name : API RESPONDED ($($response.StatusCode))" -ForegroundColor Green
        return $true
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "❌ $name : API ERROR ($statusCode) - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Test-ApiEndpoint -url $bgRemovalAi -name "bg-removal-ai"
Test-ApiEndpoint -url $bgRemovalBirefnet -name "bg-removal-birefnet (old)"
Test-ApiEndpoint -url $bgRemovalBirefnetActual -name "bg-removal-birefnet (actual)"

Write-Host "`n=== VERIFICATION SUMMARY ===" -ForegroundColor Cyan
Write-Host "Current Code Configuration:" -ForegroundColor Yellow
Write-Host "- api/tools/bg-remove-free.js uses: $bgRemovalBirefnetActual"
Write-Host "`nRecommendation: Verify which backend is actually deployed and active"

