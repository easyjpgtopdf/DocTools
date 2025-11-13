# Stop Excel Unlocker Services
# Safely stops all running servers

Write-Host "🛑 Stopping Excel Unlocker Services..." -ForegroundColor Yellow
Write-Host ""

# Find and kill Python processes on port 5000 (Flask)
Write-Host "🔍 Searching for Flask backend (Port 5000)..." -ForegroundColor Cyan
$flaskProcess = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty OwningProcess -First 1

if ($flaskProcess) {
    Stop-Process -Id $flaskProcess -Force
    Write-Host "✅ Flask backend stopped (PID: $flaskProcess)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Flask backend not running on port 5000" -ForegroundColor Yellow
}

# Find and kill Python processes on port 8080 (HTTP Server)
Write-Host ""
Write-Host "🔍 Searching for Frontend server (Port 8080)..." -ForegroundColor Cyan
$httpProcess = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | 
               Select-Object -ExpandProperty OwningProcess -First 1

if ($httpProcess) {
    Stop-Process -Id $httpProcess -Force
    Write-Host "✅ Frontend server stopped (PID: $httpProcess)" -ForegroundColor Green
} else {
    Write-Host "⚠️  Frontend server not running on port 8080" -ForegroundColor Yellow
}

# Stop any background jobs
Write-Host ""
Write-Host "🔍 Checking for background jobs..." -ForegroundColor Cyan
$jobs = Get-Job | Where-Object { $_.State -eq "Running" }
if ($jobs) {
    $jobs | Stop-Job
    $jobs | Remove-Job
    Write-Host "✅ Stopped $($jobs.Count) background job(s)" -ForegroundColor Green
} else {
    Write-Host "⚠️  No running background jobs found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ✅ All services stopped successfully!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
