# Replace All Headers & Footers with Global Components
# This script removes old <header> and <footer> tags and replaces with placeholders

$rootPath = "C:\Users\apnao\Downloads\DocTools"
$backupPath = Join-Path $rootPath "backups\header-footer-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Host "=== Global Header & Footer Replacement Tool ===" -ForegroundColor Cyan
Write-Host ""

# Create backup directory
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
Write-Host "✓ Backup directory created: $backupPath" -ForegroundColor Green

# Get all HTML files (excluding backups, node_modules, and server folders)
$htmlFiles = Get-ChildItem -Path $rootPath -Filter "*.html" -File | Where-Object {
    $_.FullName -notmatch "\\backups\\" -and 
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\server\\" -and
    $_.FullName -notmatch "\\services\\" -and
    $_.Name -ne "test-header-footer.html"
}

Write-Host "Found $($htmlFiles.Count) HTML files to process" -ForegroundColor Yellow
Write-Host ""

$processedCount = 0
$skippedCount = 0
$errorCount = 0

foreach ($file in $htmlFiles) {
    try {
        Write-Host "Processing: $($file.Name)..." -NoNewline
        
        # Backup original file
        Copy-Item $file.FullName -Destination (Join-Path $backupPath $file.Name) -Force
        
        # Read file content
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        $originalContent = $content
        
        # Check if already has placeholders
        $hasHeaderPlaceholder = $content -match '<div id="global-header-placeholder"></div>'
        $hasFooterPlaceholder = $content -match '<div id="global-footer-placeholder"></div>'
        $hasScript = $content -match '<script src="js/global-components\.js"></script>'
        
        # Step 1: Remove old <header> tag and its content (find from <header> to </header>)
        $content = $content -replace '(?s)<header>.*?</header>', '<div id="global-header-placeholder"></div>'
        
        # Step 2: Remove old <footer> tag and its content (find from <footer> to </footer>)
        $content = $content -replace '(?s)<footer>.*?</footer>', '<div id="global-footer-placeholder"></div>'
        
        # Step 3: Add script reference before closing body tag if not present
        if (-not $hasScript) {
            $bodyCloseTag = '</body>'
            if ($content -match $bodyCloseTag) {
                $scriptTag = '    <script src="js/global-components.js"></script>' + "`n"
                $content = $content -replace $bodyCloseTag, ($scriptTag + $bodyCloseTag)
            }
        }
        
        # Step 4: Ensure CSS links are present in head
        $needsHeaderCSS = $content -notmatch 'href="css/header\.css"'
        $needsFooterCSS = $content -notmatch 'href="css/footer\.css"'
        
        if ($needsHeaderCSS -or $needsFooterCSS) {
            $titleCloseTag = '</title>'
            if ($content -match $titleCloseTag) {
                $cssLinks = ""
                if ($needsHeaderCSS) {
                    $cssLinks += "`n" + '    <link rel="stylesheet" href="css/header.css">'
                }
                if ($needsFooterCSS) {
                    $cssLinks += "`n" + '    <link rel="stylesheet" href="css/footer.css">'
                }
                $content = $content -replace $titleCloseTag, ($titleCloseTag + $cssLinks)
            }
        }
        
        # Check if content changed
        if ($content -ne $originalContent) {
            # Save modified content
            $content | Out-File -FilePath $file.FullName -Encoding UTF8 -NoNewline
            Write-Host " ✓ REPLACED" -ForegroundColor Green
            $processedCount++
        } else {
            Write-Host " ⊘ SKIPPED (no changes needed)" -ForegroundColor DarkGray
            $skippedCount++
        }
        
    } catch {
        Write-Host " ✗ ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
Write-Host "=== Replacement Complete ===" -ForegroundColor Cyan
Write-Host "Successfully processed: $processedCount files" -ForegroundColor Green
Write-Host "Skipped: $skippedCount files" -ForegroundColor Yellow
Write-Host "Errors: $errorCount files" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host ""
Write-Host "Backup location: $backupPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ All pages now use centralized header/footer from js/global-components.js" -ForegroundColor Green
Write-Host "✓ Future updates to header/footer will automatically apply to all pages!" -ForegroundColor Green
