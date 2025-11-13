# Excel Unlocker - Quick Start Script
# Run both servers with one command

Write-Host "🚀 Starting Excel Unlocker Services..." -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check dependencies
Write-Host ""
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
$requirements = "excel-unlocker\requirements.txt"
if (Test-Path $requirements) {
    pip install -r $requirements --quiet --disable-pip-version-check
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Requirements file not found" -ForegroundColor Red
}

# Start Flask backend in background
Write-Host ""
Write-Host "🔧 Starting Flask Backend (Port 5000)..." -ForegroundColor Yellow
$flaskJob = Start-Job -ScriptBlock {
    Set-Location "excel-unlocker"
    python app.py
}
Start-Sleep -Seconds 3

# Check if Flask started successfully
if ($flaskJob.State -eq "Running") {
    Write-Host "✅ Flask backend running on http://127.0.0.1:5000" -ForegroundColor Green
} else {
    Write-Host "❌ Flask backend failed to start" -ForegroundColor Red
    Receive-Job -Job $flaskJob
    exit 1
}

# Start HTTP server for frontend
Write-Host ""
Write-Host "🌐 Starting Frontend Server (Port 8080)..." -ForegroundColor Yellow
$httpJob = Start-Job -ScriptBlock {
    python -m http.server 8080
}
Start-Sleep -Seconds 2

# Check if HTTP server started
if ($httpJob.State -eq "Running") {
    Write-Host "✅ Frontend server running on http://127.0.0.1:8080" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend server failed to start" -ForegroundColor Red
    Stop-Job -Job $flaskJob
    Remove-Job -Job $flaskJob
    exit 1
}

# Display access information
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ✨ Excel Unlocker is Ready!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 Access your application:" -ForegroundColor Yellow
Write-Host "   Frontend: http://127.0.0.1:8080/excel-unlocker.html" -ForegroundColor White
Write-Host "   Backend:  http://127.0.0.1:5000" -ForegroundColor White
Write-Host ""
Write-Host "📊 Running Jobs:" -ForegroundColor Yellow
Write-Host "   Flask Backend  (Job ID: $($flaskJob.Id))" -ForegroundColor White
Write-Host "   HTTP Server    (Job ID: $($httpJob.Id))" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop servers:" -ForegroundColor Yellow
Write-Host "   Press CTRL+C or run: .\stop-excel-unlocker.ps1" -ForegroundColor White
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

# Monitor jobs
Write-Host ""
Write-Host "📡 Monitoring servers... (Press CTRL+C to stop)" -ForegroundColor Yellow
Write-Host ""

try {
    while ($true) {
        # Check if jobs are still running
        if ($flaskJob.State -ne "Running") {
            Write-Host "❌ Flask backend stopped unexpectedly" -ForegroundColor Red
            Receive-Job -Job $flaskJob
            break
        }
        if ($httpJob.State -ne "Running") {
            Write-Host "❌ Frontend server stopped unexpectedly" -ForegroundColor Red
            Receive-Job -Job $httpJob
            break
        }
        Start-Sleep -Seconds 5
    }
} finally {
    # Cleanup on exit
    Write-Host ""
    Write-Host "🛑 Stopping servers..." -ForegroundColor Yellow
    Stop-Job -Job $flaskJob, $httpJob
    Remove-Job -Job $flaskJob, $httpJob
    Write-Host "✅ Servers stopped successfully" -ForegroundColor Green
}
