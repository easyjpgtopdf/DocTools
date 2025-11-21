# Simple Local Server for Testing
# Fixes CORS errors when opening HTML files directly

Write-Host ""
Write-Host "🚀 Starting Local Server..." -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
}

if ($pythonCmd) {
    Write-Host "✅ Python found: $pythonCmd" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Starting HTTP server on http://localhost:8000" -ForegroundColor Yellow
    Write-Host "📂 Serving files from: $PWD" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Open in browser:" -ForegroundColor Cyan
    Write-Host "   http://localhost:8000/background-remover.html" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    # Start Python HTTP server
    & $pythonCmd -m http.server 8000
} else {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Alternative: Use Node.js http-server" -ForegroundColor Yellow
    Write-Host "   npm install -g http-server" -ForegroundColor White
    Write-Host "   http-server -p 8000" -ForegroundColor White
    Write-Host ""
    Write-Host "   OR use VS Code Live Server extension" -ForegroundColor Yellow
    Write-Host ""
}

