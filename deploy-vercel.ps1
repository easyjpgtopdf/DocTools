# Quick Deployment Script for EasyJpgToPDF.com
# This script automates the Local → Git → Vercel workflow

param(
    [Parameter(Mandatory=$false)]
    [string]$Message = "Update: Quick deployment"
)

Write-Host "`n╔═══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 EasyJpgToPDF Deployment Script   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════╝`n" -ForegroundColor Cyan

# Step 1: Check for uncommitted changes
Write-Host "📋 Step 1: Checking for changes..." -ForegroundColor Yellow
$status = git status --short
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "✅ No changes to commit`n" -ForegroundColor Green
    exit 0
}

Write-Host "📝 Found changes:" -ForegroundColor Cyan
git status --short
Write-Host ""

# Step 2: Add all changes
Write-Host "📦 Step 2: Adding files to Git..." -ForegroundColor Yellow
git add .
Write-Host "✅ Files staged`n" -ForegroundColor Green

# Step 3: Commit
Write-Host "💾 Step 3: Committing changes..." -ForegroundColor Yellow
git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Commit failed!`n" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Committed successfully`n" -ForegroundColor Green

# Step 4: Push to GitHub
Write-Host "📤 Step 4: Pushing to GitHub..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Push failed!`n" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Pushed to GitHub`n" -ForegroundColor Green

# Step 5: Wait for Vercel deployment
Write-Host "⏳ Step 5: Waiting for Vercel deployment..." -ForegroundColor Yellow
Write-Host "   (This takes about 30-60 seconds)`n" -ForegroundColor Gray

Start-Sleep -Seconds 45

# Step 6: Check deployment
Write-Host "🔍 Step 6: Checking deployment status..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "https://easyjpgtopdf.com/?v=$(Get-Date -Format 'yyyyMMddHHmmss')" -Method Head -UseBasicParsing
Write-Host "✅ Site is live!" -ForegroundColor Green
Write-Host "   Last-Modified: $($response.Headers['Last-Modified'])`n" -ForegroundColor Cyan

# Final message
Write-Host "╔═══════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     🎉 DEPLOYMENT SUCCESSFUL!         ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "🌐 Your site: https://easyjpgtopdf.com" -ForegroundColor Cyan
Write-Host "⏱️  Changes will be visible in 1-2 minutes" -ForegroundColor Yellow
Write-Host "🧹 Clear browser cache (Ctrl+Shift+Delete) to see changes`n" -ForegroundColor White

# Usage examples
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "Usage Examples:" -ForegroundColor Yellow
Write-Host "  .\deploy-vercel.ps1" -ForegroundColor White
Write-Host "  .\deploy-vercel.ps1 -Message 'Fix: Resume preview bug'" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
