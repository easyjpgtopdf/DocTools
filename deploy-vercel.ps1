# Vercel Manual Deployment Script
# Run this after logging in to Vercel

Write-Host "=== Vercel Deployment Script ===" -ForegroundColor Cyan
Write-Host ""

# Check if logged in
Write-Host "Checking Vercel login status..." -ForegroundColor Yellow
vercel whoami

if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in. Opening browser for login..." -ForegroundColor Red
    Write-Host "Manual login URL: https://vercel.com/oauth/device?user_code=WWHX-GJPN" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After login, run this script again." -ForegroundColor Green
    exit 1
}

Write-Host ""
Write-Host "Deploying to Vercel (Production)..." -ForegroundColor Green
vercel --prod --yes --force

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "Wait 1-2 minutes, then test:" -ForegroundColor Yellow
Write-Host "https://easyjpgtopdf.com/resume-maker.html" -ForegroundColor Green
