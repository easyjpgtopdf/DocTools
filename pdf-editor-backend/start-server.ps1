# PDF Editor Backend Server Startup Script
# Windows PowerShell script to start the FastAPI backend server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PDF Editor Backend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if we're in the correct directory
if (-not (Test-Path "app\main.py")) {
    Write-Host "ERROR: Please run this script from pdf-editor-backend directory" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install/update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Set environment variables
$env:PORT = "8080"
$env:API_BASE_URL = "https://easyjpgtopdf.com"

Write-Host ""
Write-Host "Starting server on http://localhost:8080" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

