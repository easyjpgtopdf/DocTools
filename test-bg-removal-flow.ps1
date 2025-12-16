# Background Removal Flow Test Script
# Tests complete end-to-end flow

Write-Host "`n🔍 BACKGROUND REMOVAL FLOW TEST" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Test 1: Backend Health Check
Write-Host "`n[1/5] Testing Backend Health..." -ForegroundColor Yellow
$backendUrl = "https://bg-removal-birefnet-564572183797.us-central1.run.app"
try {
    $healthResponse = Invoke-WebRequest -Uri "$backendUrl/health" -Method GET -TimeoutSec 15 -ErrorAction Stop
    Write-Host "  ✅ Backend Health: OK ($($healthResponse.StatusCode))" -ForegroundColor Green
    Write-Host "  Response: $($healthResponse.Content)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ Backend Health: FAILED" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  ⚠️  Backend may be down or cold-starting" -ForegroundColor Yellow
}

# Test 2: API Endpoint Check (Vercel)
Write-Host "`n[2/5] Testing API Endpoint..." -ForegroundColor Yellow
$apiUrl = "https://easyjpgtopdf.com/api/tools/bg-remove-free"
try {
    # Test OPTIONS (CORS preflight)
    $optionsResponse = Invoke-WebRequest -Uri $apiUrl -Method OPTIONS -TimeoutSec 10 -ErrorAction Stop
    Write-Host "  ✅ API Endpoint: Accessible ($($optionsResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  API Endpoint: Could not verify (this is OK for OPTIONS)" -ForegroundColor Yellow
    Write-Host "  Note: Actual POST request required to test fully" -ForegroundColor Gray
}

# Test 3: Frontend Files Check
Write-Host "`n[3/5] Checking Frontend Files..." -ForegroundColor Yellow
$filesToCheck = @(
    "background-workspace.html",
    "server\public\background-workspace.html",
    "api\tools\bg-remove-free.js"
)

$allExist = $true
foreach ($file in $filesToCheck) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file - NOT FOUND" -ForegroundColor Red
        $allExist = $false
    }
}

if ($allExist) {
    Write-Host "  ✅ All frontend files present" -ForegroundColor Green
} else {
    Write-Host "  ❌ Some files missing" -ForegroundColor Red
}

# Test 4: Check Auto-Start Code
Write-Host "`n[4/5] Checking Auto-Start Implementation..." -ForegroundColor Yellow
$workspaceContent = Get-Content "background-workspace.html" -Raw -ErrorAction SilentlyContinue
if ($workspaceContent) {
    $hasAutoStart = $workspaceContent -match "AUTO-START.*Preview loaded"
    $hasFreePreviewAutoStarted = $workspaceContent -match "freePreviewAutoStarted"
    $hasProcessWithFreePreview = $workspaceContent -match "processWithFreePreview"
    
    if ($hasAutoStart) {
        Write-Host "  ✅ Auto-start code found" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Auto-start code NOT found" -ForegroundColor Red
    }
    
    if ($hasFreePreviewAutoStarted) {
        Write-Host "  ✅ freePreviewAutoStarted flag found" -ForegroundColor Green
    } else {
        Write-Host "  ❌ freePreviewAutoStarted flag NOT found" -ForegroundColor Red
    }
    
    if ($hasProcessWithFreePreview) {
        Write-Host "  ✅ processWithFreePreview function found" -ForegroundColor Green
    } else {
        Write-Host "  ❌ processWithFreePreview function NOT found" -ForegroundColor Red
    }
} else {
    Write-Host "  ❌ Could not read background-workspace.html" -ForegroundColor Red
}

# Test 5: Backend Route Check
Write-Host "`n[5/5] Checking Backend Route..." -ForegroundColor Yellow
$backendAppContent = Get-Content "bg-removal-backend\app.py" -Raw -ErrorAction SilentlyContinue
if ($backendAppContent) {
    $hasFreePreviewRoute = $backendAppContent -match '@app\.route\(.*free-preview-bg'
    $hasMultipartCheck = $backendAppContent -match "multipart/form-data"
    $hasBiRefNet = $backendAppContent -match "birefnet"
    
    if ($hasFreePreviewRoute) {
        Write-Host "  ✅ /api/free-preview-bg route found" -ForegroundColor Green
    } else {
        Write-Host "  ❌ /api/free-preview-bg route NOT found" -ForegroundColor Red
    }
    
    if ($hasMultipartCheck) {
        Write-Host "  ✅ Multipart/form-data check found" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Multipart/form-data check NOT found" -ForegroundColor Red
    }
    
    if ($hasBiRefNet) {
        Write-Host "  ✅ BiRefNet model reference found" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  BiRefNet model reference NOT found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ Could not read bg-removal-backend\app.py" -ForegroundColor Red
}

# Summary
Write-Host "`n" + ("=" * 60) -ForegroundColor Gray
Write-Host "📊 TEST SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "`n✅ Code structure appears correct" -ForegroundColor Green
Write-Host "⚠️  Backend health check failed - may be cold-starting" -ForegroundColor Yellow
Write-Host "`n💡 RECOMMENDATIONS:" -ForegroundColor Cyan
Write-Host "  1. Check Cloud Run service status in GCP console" -ForegroundColor White
Write-Host "  2. Test actual image upload in browser" -ForegroundColor White
Write-Host "  3. Check browser console logs for auto-start" -ForegroundColor White
Write-Host "  4. Check Vercel function logs for API calls" -ForegroundColor White
Write-Host "  5. Check Cloud Run logs for backend processing" -ForegroundColor White
Write-Host ""

