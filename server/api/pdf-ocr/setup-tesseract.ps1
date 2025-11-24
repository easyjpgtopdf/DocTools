# Tesseract OCR Setup and Verification Script
# This script finds and configures Tesseract OCR

Write-Host "Tesseract OCR Setup Script" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# Function to check if Tesseract is installed
function Find-Tesseract {
    $paths = @(
        "C:\Program Files\Tesseract-OCR\tesseract.exe",
        "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "$env:LOCALAPPDATA\Programs\Tesseract-OCR\tesseract.exe",
        "C:\tesseract-ocr\tesseract.exe"
    )
    
    # Check common paths
    foreach ($path in $paths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    # Check PATH
    $tesseract = Get-Command tesseract -ErrorAction SilentlyContinue
    if ($tesseract) {
        return $tesseract.Source
    }
    
    return $null
}

# Find Tesseract
Write-Host ""
Write-Host "Searching for Tesseract OCR..." -ForegroundColor Yellow
$tesseractPath = Find-Tesseract

if ($tesseractPath) {
    Write-Host ""
    Write-Host "Tesseract found at: $tesseractPath" -ForegroundColor Green
    
    # Test Tesseract
    Write-Host ""
    Write-Host "Testing Tesseract..." -ForegroundColor Yellow
    try {
        $version = & $tesseractPath --version 2>&1
        Write-Host $version -ForegroundColor Cyan
        
        # List available languages
        Write-Host ""
        Write-Host "Available languages:" -ForegroundColor Yellow
        $langs = & $tesseractPath --list-langs 2>&1 | Select-Object -Skip 1
        Write-Host $langs -ForegroundColor Cyan
        
        Write-Host ""
        Write-Host "Tesseract OCR is properly configured!" -ForegroundColor Green
        
        # Update Python script with path
        $pythonScript = Join-Path $PSScriptRoot "ocr-process.py"
        if (Test-Path $pythonScript) {
            Write-Host ""
            Write-Host "Python script will auto-detect Tesseract path." -ForegroundColor Green
        }
        
    } catch {
        Write-Host ""
        Write-Host "Error testing Tesseract: $_" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "Tesseract OCR not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Installation options:" -ForegroundColor Yellow
    Write-Host "1. Run as Administrator: .\install-tesseract.ps1" -ForegroundColor Cyan
    Write-Host "2. Manual install: See install-tesseract-manual.md" -ForegroundColor Cyan
    Write-Host "3. Download from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "Setup verification complete!" -ForegroundColor Green
