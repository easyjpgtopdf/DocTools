# Quick API Test Script for PDF Editor Backend
# Usage: .\TEST_API.ps1 <BACKEND_URL>

param(
    [string]$BackendUrl = "https://pdf-editor-service-564572183797.us-central1.run.app"
)

Write-Host " Testing PDF Editor Backend API" -ForegroundColor Green
Write-Host "Backend URL: $BackendUrl`n" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "1 Testing /health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BackendUrl/health" -Method GET
    Write-Host "    Health check passed" -ForegroundColor Green
    Write-Host "   Response: $($response | ConvertTo-Json)" -ForegroundColor Gray
} catch {
    Write-Host "    Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Device IP
Write-Host "`n2 Testing /device/ip endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BackendUrl/device/ip" -Method GET
    Write-Host "    Device IP endpoint works" -ForegroundColor Green
    Write-Host "   IP: $($response.ip)" -ForegroundColor Gray
} catch {
    Write-Host "    Device IP endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: CORS (check if OPTIONS works)
Write-Host "`n3 Testing CORS..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/health" -Method OPTIONS -Headers @{"Origin"="https://easyjpgtopdf.com"}
    Write-Host "    CORS headers present" -ForegroundColor Green
    Write-Host "   Access-Control-Allow-Origin: $($response.Headers['Access-Control-Allow-Origin'])" -ForegroundColor Gray
} catch {
    Write-Host "     CORS test inconclusive: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n API Testing Complete!" -ForegroundColor Green
Write-Host "`n To test with a real PDF:" -ForegroundColor Yellow
Write-Host "   Use Postman or curl to POST a PDF to: $BackendUrl/session/start" -ForegroundColor White
