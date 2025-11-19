# ============================================
# Header Synchronization Script
# Replaces all page headers with index.html header
# Sets up automatic header updates for future changes
# ============================================

Write-Host "`n╔═══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🔄 Header Synchronization Script   ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════╝`n" -ForegroundColor Cyan

# Step 1: Extract header from index.html
Write-Host "📖 Step 1: Extracting header from index.html..." -ForegroundColor Yellow

$indexPath = "index.html"
if (-not (Test-Path $indexPath)) {
    Write-Host "❌ Error: index.html not found!" -ForegroundColor Red
    exit 1
}

$indexContent = Get-Content $indexPath -Raw -Encoding UTF8

# Extract header section (from <header> to </header>)
if ($indexContent -match '(?s)(<header>.*?</header>)') {
    $headerHTML = $matches[1]
    Write-Host "✅ Header extracted successfully" -ForegroundColor Green
    Write-Host "   Header length: $($headerHTML.Length) characters" -ForegroundColor Gray
} else {
    Write-Host "❌ Error: Could not find <header> tag in index.html" -ForegroundColor Red
    exit 1
}

# Step 2: Find all HTML files (except index.html)
Write-Host "`n📁 Step 2: Finding all HTML files..." -ForegroundColor Yellow

$htmlFiles = Get-ChildItem -Path . -Filter "*.html" -File | Where-Object { 
    $_.Name -ne "index.html" -and 
    $_.Name -notlike "server\*" -and
    $_.FullName -notlike "*\node_modules\*" -and
    $_.FullName -notlike "*\excel-unlocker\*"
}

Write-Host "✅ Found $($htmlFiles.Count) HTML files to process" -ForegroundColor Green

# Step 3: Replace headers in all files
Write-Host "`n🔄 Step 3: Replacing headers in all files..." -ForegroundColor Yellow

$processedCount = 0
$skippedCount = 0
$errorCount = 0

foreach ($file in $htmlFiles) {
    try {
        Write-Host "   Processing: $($file.Name)..." -NoNewline
        
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        $originalContent = $content
        
        # Check if file has a header tag
        if ($content -match '(?s)(<header>.*?</header>)') {
            # Replace existing header with index.html header
            $content = $content -replace '(?s)(<header>.*?</header>)', $headerHTML
            
            # Save if changed
            if ($content -ne $originalContent) {
                [System.IO.File]::WriteAllText($file.FullName, $content, [System.Text.UTF8Encoding]::new($false))
                Write-Host " ✅ UPDATED" -ForegroundColor Green
                $processedCount++
            } else {
                Write-Host " ⚠️  Already matches" -ForegroundColor Yellow
                $skippedCount++
            }
        } else {
            Write-Host " ⚠️  No header found" -ForegroundColor Yellow
            $skippedCount++
        }
    } catch {
        Write-Host " ❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $errorCount++
    }
}

# Step 4: Update global-components.js with latest header
Write-Host "`n📝 Step 4: Updating global-components.js for automatic updates..." -ForegroundColor Yellow

$globalComponentsPath = "js\global-components.js"
if (Test-Path $globalComponentsPath) {
    $globalComponentsContent = Get-Content $globalComponentsPath -Raw -Encoding UTF8
    
    # Escape the header HTML for JavaScript string
    $escapedHeader = $headerHTML -replace '`', '``' -replace '\$', '`$' -replace '"', '`"'
    $escapedHeader = $escapedHeader -replace "`r`n", "`n" -replace "`n", "`n"
    
    # Replace the globalHeaderHTML constant
    if ($globalComponentsContent -match '(?s)(const globalHeaderHTML = `.*?`;)') {
        $newHeaderConstant = "const globalHeaderHTML = ``$escapedHeader``;"
        $globalComponentsContent = $globalComponentsContent -replace '(?s)(const globalHeaderHTML = `.*?`;)', $newHeaderConstant
        
        [System.IO.File]::WriteAllText($globalComponentsPath, $globalComponentsContent, [System.Text.UTF8Encoding]::new($false))
        Write-Host "✅ global-components.js updated" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Could not find globalHeaderHTML in global-components.js" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  global-components.js not found, skipping..." -ForegroundColor Yellow
}

# Summary
Write-Host "`n╔═══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ✅ Synchronization Complete!         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "📊 Summary:" -ForegroundColor White
Write-Host "   ✅ Updated: $processedCount files" -ForegroundColor Green
Write-Host "   ⚠️  Skipped: $skippedCount files" -ForegroundColor Yellow
if ($errorCount -gt 0) {
    Write-Host "   ❌ Errors: $errorCount files" -ForegroundColor Red
}

Write-Host "`n💡 Future Updates:" -ForegroundColor Cyan
Write-Host "   • Edit header in index.html" -ForegroundColor White
Write-Host "   • Run this script again to sync all pages" -ForegroundColor White
Write-Host "   • Or use js/global-components.js for automatic updates" -ForegroundColor White
Write-Host ""


