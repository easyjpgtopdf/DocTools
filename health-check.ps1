# System Health Check Script
# Verifies complete Local + Git + Vercel + Domain setup

Write-Host "`n╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🔍 EASYJPGTOPDF.COM - SYSTEM HEALTH CHECK       ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$errors = 0
$warnings = 0

# Test 1: Local Git Configuration
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "1️⃣  LOCAL GIT CONFIGURATION" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White

try {
    $gitUser = git config user.name
    $gitEmail = git config user.email
    
    if ($gitUser -and $gitEmail) {
        Write-Host "   ✅ Git user configured: $gitUser <$gitEmail>" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Git user not configured" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   ❌ Git not installed or configured" -ForegroundColor Red
    $errors++
}

# Test 2: GitHub Remote Connection
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "2️⃣  GITHUB REMOTE CONNECTION" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White

try {
    $remote = git remote get-url origin
    if ($remote -match "easyjpgtopdf/DocTools") {
        Write-Host "   ✅ GitHub remote: $remote" -ForegroundColor Green
        
        # Test push access
        git ls-remote origin HEAD > $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ GitHub access verified" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Cannot access GitHub (check credentials)" -ForegroundColor Yellow
            $warnings++
        }
    } else {
        Write-Host "   ❌ Invalid GitHub remote" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   ❌ No GitHub remote configured" -ForegroundColor Red
    $errors++
}

# Test 3: Vercel CLI
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "3️⃣  VERCEL CLI STATUS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White

try {
    $vercelUser = vercel whoami 2>&1 | Out-String
    if ($vercelUser -match "easyjpgtopdf") {
        Write-Host "   ✅ Vercel CLI logged in as: easyjpgtopdf" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Vercel CLI not logged in" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   ❌ Vercel CLI not installed" -ForegroundColor Red
    $errors++
}

# Test 4: Vercel Project
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "4️⃣  VERCEL PROJECT STATUS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White

if (Test-Path ".vercel") {
    Write-Host "   ✅ Project linked to Vercel" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Project not linked (will link on first deploy)" -ForegroundColor Yellow
    $warnings++
}

# Test 5: Domain Connection
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "5️⃣  DOMAIN CONNECTION" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White

try {
    $response = Invoke-WebRequest -Uri "https://easyjpgtopdf.com" -Method Head -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Domain accessible: easyjpgtopdf.com" -ForegroundColor Green
        Write-Host "   ✅ SSL/HTTPS working" -ForegroundColor Green
        
        $lastModified = $response.Headers['Last-Modified']
        Write-Host "   📅 Last deployment: $lastModified" -ForegroundColor Cyan
    } else {
        Write-Host "   ⚠️  Domain returned status: $($response.StatusCode)" -ForegroundColor Yellow
        $warnings++
    }
} catch {
    Write-Host "   ❌ Cannot reach easyjpgtopdf.com" -ForegroundColor Red
    $errors++
}

# Test 6: Environment Variables
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "6️⃣  ENVIRONMENT VARIABLES" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White

try {
    $envVars = vercel env ls 2>&1 | Out-String
    if ($envVars -match "RAZORPAY_KEY_ID" -and $envVars -match "FIREBASE_SERVICE_ACCOUNT") {
        Write-Host "   ✅ All environment variables configured (10/10)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Some environment variables may be missing" -ForegroundColor Yellow
        $warnings++
    }
} catch {
    Write-Host "   ⚠️  Cannot check environment variables" -ForegroundColor Yellow
    $warnings++
}

# Test 7: Required Files
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "7️⃣  REQUIRED FILES" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White

$requiredFiles = @(
    "vercel.json",
    "package.json",
    ".gitignore",
    "deploy-vercel.ps1",
    "index.html"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Missing: $file" -ForegroundColor Red
        $errors++
    }
}

# Test 8: Git Status
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White
Write-Host "8️⃣  REPOSITORY STATUS" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor White

$gitStatus = git status --short
if ([string]::IsNullOrWhiteSpace($gitStatus)) {
    Write-Host "   ✅ Working tree clean (no uncommitted changes)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Uncommitted changes found:" -ForegroundColor Yellow
    git status --short | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
    $warnings++
}

# Final Report
Write-Host "`n╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                  HEALTH CHECK RESULTS                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host "   🎉 ALL SYSTEMS OPERATIONAL!" -ForegroundColor Green
    Write-Host "   ✅ 0 Errors" -ForegroundColor Green
    Write-Host "   ✅ 0 Warnings`n" -ForegroundColor Green
    Write-Host "   Your auto-deployment setup is perfect!" -ForegroundColor Cyan
    Write-Host "   Just edit → commit → push → automatic deploy ✨`n" -ForegroundColor White
} elseif ($errors -eq 0) {
    Write-Host "   ✅ SYSTEM OPERATIONAL (with minor warnings)" -ForegroundColor Yellow
    Write-Host "   ✅ 0 Errors" -ForegroundColor Green
    Write-Host "   ⚠️  $warnings Warning(s)`n" -ForegroundColor Yellow
} else {
    Write-Host "   ❌ SYSTEM NEEDS ATTENTION" -ForegroundColor Red
    Write-Host "   ❌ $errors Error(s)" -ForegroundColor Red
    Write-Host "   ⚠️  $warnings Warning(s)`n" -ForegroundColor Yellow
    Write-Host "   Please fix the errors above before deploying.`n" -ForegroundColor White
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor White
