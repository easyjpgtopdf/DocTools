# Excel Unlocker - Quick Render Deployment Script
# This script helps you deploy Excel Unlocker backend to Render.com

Write-Host "🚀 Excel Unlocker - Render Deployment Helper" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify files
Write-Host "Step 1: Verifying required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "excel-unlocker\app.py",
    "excel-unlocker\requirements.txt",
    "excel-unlocker\Procfile",
    "excel-unlocker\wsgi.py"
)

$allFilesExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file (MISSING)" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host ""
    Write-Host "❌ Missing required files. Cannot proceed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All required files present!" -ForegroundColor Green
Write-Host ""

# Step 2: Check Git status
Write-Host "Step 2: Checking Git status..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "  ⚠️  You have uncommitted changes:" -ForegroundColor Yellow
    Write-Host ""
    git status --short
    Write-Host ""
    
    $commit = Read-Host "Do you want to commit and push now? (y/n)"
    if ($commit -eq 'y' -or $commit -eq 'Y') {
        $commitMsg = Read-Host "Enter commit message"
        if (-not $commitMsg) {
            $commitMsg = "Excel Unlocker deployment preparation"
        }
        
        git add -A
        git commit -m $commitMsg
        git push origin main
        
        Write-Host "  ✅ Changes pushed to GitHub" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Please commit and push manually before deploying" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✅ Git repository is clean" -ForegroundColor Green
}

Write-Host ""

# Step 3: Render deployment instructions
Write-Host "Step 3: Render.com Deployment Steps" -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  Login to Render Dashboard:" -ForegroundColor White
Write-Host "   https://dashboard.render.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "2️⃣  Create New Web Service:" -ForegroundColor White
Write-Host "   - Click 'New +' → 'Web Service'" -ForegroundColor Gray
Write-Host "   - Connect GitHub: easyjpgtopdf/DocTools" -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  Configure Service:" -ForegroundColor White
Write-Host "   Name:           excel-unlocker-backend" -ForegroundColor Gray
Write-Host "   Region:         Oregon (USA)" -ForegroundColor Gray
Write-Host "   Branch:         main" -ForegroundColor Gray
Write-Host "   Root Directory: excel-unlocker" -ForegroundColor Gray
Write-Host "   Runtime:        Python 3" -ForegroundColor Gray
Write-Host "   Build Command:  pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "   Start Command:  gunicorn wsgi:app" -ForegroundColor Gray
Write-Host ""
Write-Host "4️⃣  Environment Variables:" -ForegroundColor White
Write-Host "   FLASK_ENV=production" -ForegroundColor Gray
Write-Host "   SECRET_KEY=<generate-random-key>" -ForegroundColor Gray
Write-Host "   PORT=10000" -ForegroundColor Gray
Write-Host "   MAX_CONTENT_LENGTH=524288000" -ForegroundColor Gray
Write-Host ""

# Generate SECRET_KEY
Write-Host "5️⃣  Generate SECRET_KEY:" -ForegroundColor White
$randomKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-Host "   $randomKey" -ForegroundColor Green
Write-Host "   (Copy this and paste as SECRET_KEY environment variable)" -ForegroundColor Yellow
Write-Host ""

Write-Host "6️⃣  Deploy:" -ForegroundColor White
Write-Host "   - Click 'Create Web Service'" -ForegroundColor Gray
Write-Host "   - Wait 5-10 minutes for first deployment" -ForegroundColor Gray
Write-Host "   - Copy your backend URL (e.g., https://excel-unlocker-backend-xyz.onrender.com)" -ForegroundColor Gray
Write-Host ""

# Step 4: Update frontend
Write-Host "Step 4: After Deployment - Update Frontend" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Once Render gives you the backend URL:" -ForegroundColor White
Write-Host ""
Write-Host "1. Open: excel-unlocker.html" -ForegroundColor Gray
Write-Host "2. Find line ~220 with API_BASE_URL" -ForegroundColor Gray
Write-Host "3. Replace 'https://excel-unlocker-backend.onrender.com'" -ForegroundColor Gray
Write-Host "   with your actual Render URL" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Save and push to GitHub:" -ForegroundColor Gray
Write-Host "   git add excel-unlocker.html" -ForegroundColor Cyan
Write-Host "   git commit -m 'Updated backend URL for production'" -ForegroundColor Cyan
Write-Host "   git push origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Vercel will auto-deploy your changes" -ForegroundColor Gray
Write-Host ""

# Step 5: Testing
Write-Host "Step 5: Testing Your Deployment" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test backend health:" -ForegroundColor White
Write-Host "  curl https://YOUR-BACKEND-URL.onrender.com/test" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test frontend:" -ForegroundColor White
Write-Host "  https://your-vercel-site.vercel.app/excel-unlocker.html" -ForegroundColor Cyan
Write-Host ""

# Final notes
Write-Host "📝 Important Notes:" -ForegroundColor Yellow
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Free Render tier spins down after 15 min inactivity" -ForegroundColor White
Write-Host "✅ First request may take 30-60 seconds to wake up" -ForegroundColor White
Write-Host "✅ Subsequent requests will be fast" -ForegroundColor White
Write-Host "✅ Upgrade to Starter ($7/month) for always-on service" -ForegroundColor White
Write-Host ""
Write-Host "📚 Full Guide: RENDER_DEPLOYMENT.md" -ForegroundColor Yellow
Write-Host ""
Write-Host "🎉 Ready to deploy! Follow the steps above." -ForegroundColor Green
Write-Host ""
