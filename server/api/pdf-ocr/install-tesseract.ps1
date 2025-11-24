# Tesseract OCR Installation Script for Windows
# Run this script as Administrator

Write-Host "Tesseract OCR Installation Script" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`nERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Write-Host "`nAlternative: Install manually from:" -ForegroundColor Yellow
    Write-Host "https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
    exit 1
}

Write-Host "`nChecking for Chocolatey..." -ForegroundColor Yellow
$chocoInstalled = Get-Command choco -ErrorAction SilentlyContinue

if ($chocoInstalled) {
    Write-Host "Chocolatey found. Installing Tesseract OCR..." -ForegroundColor Green
    choco install tesseract -y
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nTesseract OCR installed successfully!" -ForegroundColor Green
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        # Verify installation
        $tesseractPath = Get-Command tesseract -ErrorAction SilentlyContinue
        if ($tesseractPath) {
            Write-Host "`nVerification:" -ForegroundColor Green
            tesseract --version
            Write-Host "`nSetup complete! Tesseract OCR is ready to use." -ForegroundColor Green
        } else {
            Write-Host "`nWarning: Tesseract installed but not found in PATH." -ForegroundColor Yellow
            Write-Host "Please restart your terminal or add Tesseract to PATH manually." -ForegroundColor Yellow
        }
    } else {
        Write-Host "`nInstallation failed. Trying manual download..." -ForegroundColor Yellow
        Write-Host "Please download and install from:" -ForegroundColor Cyan
        Write-Host "https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
    }
} else {
    Write-Host "Chocolatey not found. Please install manually:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
    Write-Host "2. Install to: C:\Program Files\Tesseract-OCR" -ForegroundColor Cyan
    Write-Host "3. Add to PATH: C:\Program Files\Tesseract-OCR" -ForegroundColor Cyan
}

Write-Host "`nInstallation script completed." -ForegroundColor Green

