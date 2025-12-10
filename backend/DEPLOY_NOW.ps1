# One-Click Deployment Script
# Run this to automatically deploy PDF to Word converter

$ErrorActionPreference = "Stop"

Write-Host "=== PDF to Word Converter - Auto Deployment ===" -ForegroundColor Green
Write-Host ""

# Change to backend directory
if (Test-Path "backend") {
    Set-Location backend
} elseif (Test-Path ".\app\main.py") {
    # Already in backend directory
} else {
    Write-Host "Error: Please run this script from project root or backend directory" -ForegroundColor Red
    exit 1
}

# Run automatic deployment
if (Test-Path "deploy-auto.ps1") {
    Write-Host "Starting automatic deployment..." -ForegroundColor Yellow
    & ".\deploy-auto.ps1"
} else {
    Write-Host "Error: deploy-auto.ps1 not found" -ForegroundColor Red
    exit 1
}

