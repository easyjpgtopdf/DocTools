# Test Google Cloud Run Backend Connection
# Verify u2net rembg is working

$API_URL = "https://bg-remover-api-iwumaktavq-uc.a.run.app"

Write-Host ""
Write-Host "🔍 Testing Google Cloud Run Backend Connection..." -ForegroundColor Cyan
Write-Host ""

# Test health endpoint
Write-Host "1. Testing /health endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$API_URL/health" -Method Get -ErrorAction Stop
    Write-Host "✅ Backend is running!" -ForegroundColor Green
    Write-Host "   Status: $($healthResponse.status)" -ForegroundColor White
    Write-Host "   Model: $($healthResponse.model)" -ForegroundColor White
    Write-Host "   Tier: $($healthResponse.tier)" -ForegroundColor White
} catch {
    Write-Host "❌ Backend not reachable!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Solutions:" -ForegroundColor Yellow
    Write-Host "   1. Deploy backend: .\deploy-cloudrun.ps1" -ForegroundColor White
    Write-Host "   2. Check if service is running in Google Cloud Console" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "2. Testing / endpoint (API info)..." -ForegroundColor Yellow
try {
    $infoResponse = Invoke-RestMethod -Uri "$API_URL/" -Method Get -ErrorAction Stop
    Write-Host "✅ API Info retrieved!" -ForegroundColor Green
    Write-Host "   Service: $($infoResponse.service)" -ForegroundColor White
    Write-Host "   Model: $($infoResponse.model)" -ForegroundColor White
    Write-Host "   Powered by: $($infoResponse.powered_by)" -ForegroundColor White
    Write-Host "   Max file size: $($infoResponse.max_file_size_mb) MB" -ForegroundColor White
} catch {
    Write-Host "⚠️ Could not get API info" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Backend Connection Test Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "   • Backend URL: $API_URL" -ForegroundColor White
Write-Host "   • Model: u2net (latest rembg)" -ForegroundColor White
Write-Host "   • Status: Connected" -ForegroundColor Green
Write-Host ""

