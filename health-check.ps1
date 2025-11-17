# System Health Check - EasyJpgToPDF.com
# Verifies Local + Git + Vercel + Domain setup

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   SYSTEM HEALTH CHECK - EASYJPGTOPDF.COM" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

$errors = 0
$warnings = 0

# Test 1: Git Configuration
Write-Host "[1] LOCAL GIT CONFIGURATION" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor White
try {
    $gitUser = git config user.name
    $gitEmail = git config user.email
    
    if ($gitUser -and $gitEmail) {
        Write-Host "   [OK] Git configured: $gitUser" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Git not configured" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] Git not installed" -ForegroundColor Red
    $errors++
}

# Test 2: GitHub Connection
Write-Host "`n[2] GITHUB REMOTE CONNECTION" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor White
try {
    $remote = git remote get-url origin
    if ($remote -match "easyjpgtopdf/DocTools") {
        Write-Host "   [OK] GitHub remote connected" -ForegroundColor Green
        
        git ls-remote origin HEAD > $null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] GitHub access verified" -ForegroundColor Green
        } else {
            Write-Host "   [WARNING] Cannot access GitHub" -ForegroundColor Yellow
            $warnings++
        }
    } else {
        Write-Host "   [ERROR] Invalid GitHub remote" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] No GitHub remote configured" -ForegroundColor Red
    $errors++
}

# Test 3: Vercel CLI
Write-Host "`n[3] VERCEL CLI STATUS" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor White
try {
    $vercelUser = vercel whoami 2>&1 | Out-String
    if ($vercelUser -match "easyjpgtopdf") {
        Write-Host "   [OK] Vercel CLI logged in" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Vercel CLI not logged in" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "   [ERROR] Vercel CLI not installed" -ForegroundColor Red
    $errors++
}

# Test 4: Domain Connection
Write-Host "`n[4] DOMAIN CONNECTION" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor White
try {
    $response = Invoke-WebRequest -Uri "https://easyjpgtopdf.com" -Method Head -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "   [OK] Domain accessible" -ForegroundColor Green
        Write-Host "   [OK] SSL/HTTPS working" -ForegroundColor Green
        
        $lastModified = $response.Headers['Last-Modified']
        Write-Host "   [INFO] Last deploy: $lastModified" -ForegroundColor Cyan
    } else {
        Write-Host "   [WARNING] Domain status: $($response.StatusCode)" -ForegroundColor Yellow
        $warnings++
    }
} catch {
    Write-Host "   [ERROR] Cannot reach domain" -ForegroundColor Red
    $errors++
}

# Test 5: Required Files
Write-Host "`n[5] REQUIRED FILES" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor White

$requiredFiles = @("vercel.json", "package.json", ".gitignore", "deploy-vercel.ps1", "index.html")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "   [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Missing: $file" -ForegroundColor Red
        $errors++
    }
}

# Test 6: Git Status
Write-Host "`n[6] REPOSITORY STATUS" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor White

$gitStatus = git status --short
if ([string]::IsNullOrWhiteSpace($gitStatus)) {
    Write-Host "   [OK] Working tree clean" -ForegroundColor Green
} else {
    Write-Host "   [WARNING] Uncommitted changes found" -ForegroundColor Yellow
    $warnings++
}

# Final Report
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "              HEALTH CHECK RESULTS" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host "   STATUS: ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    Write-Host "   Errors: 0" -ForegroundColor Green
    Write-Host "   Warnings: 0`n" -ForegroundColor Green
    Write-Host "   Auto-deployment setup is PERFECT!" -ForegroundColor Cyan
    Write-Host "   Edit -> Commit -> Push -> Auto Deploy`n" -ForegroundColor White
} elseif ($errors -eq 0) {
    Write-Host "   STATUS: OPERATIONAL (with warnings)" -ForegroundColor Yellow
    Write-Host "   Errors: 0" -ForegroundColor Green
    Write-Host "   Warnings: $warnings`n" -ForegroundColor Yellow
} else {
    Write-Host "   STATUS: NEEDS ATTENTION" -ForegroundColor Red
    Write-Host "   Errors: $errors" -ForegroundColor Red
    Write-Host "   Warnings: $warnings`n" -ForegroundColor Yellow
}

Write-Host "================================================`n" -ForegroundColor White
