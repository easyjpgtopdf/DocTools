# Replace All Headers & Footers with Global Components
param()

$rootPath = "C:\Users\apnao\Downloads\DocTools"
$backupPath = Join-Path $rootPath "backups\header-footer-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Host "=== Global Header & Footer Replacement Tool ===" -ForegroundColor Cyan
Write-Host ""

# Create backup
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
Write-Host "Backup created: $backupPath" -ForegroundColor Green
Write-Host ""

# Get HTML files
$htmlFiles = Get-ChildItem -Path $rootPath -Filter "*.html" -File | Where-Object {
    $_.FullName -notmatch "\\backups\\" -and 
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\server\\" -and
    $_.FullName -notmatch "\\services\\"
}

Write-Host "Found $($htmlFiles.Count) files" -ForegroundColor Yellow
Write-Host ""

$processedCount = 0
$skippedCount = 0

foreach ($file in $htmlFiles) {
    Write-Host "Processing: $($file.Name)..." -NoNewline
    
    # Backup
    Copy-Item $file.FullName -Destination (Join-Path $backupPath $file.Name) -Force
    
    # Read content
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $original = $content
    
    # Replace header tags with placeholder
    $content = $content -replace '(?s)<header>.*?</header>', '<div id="global-header-placeholder"></div>'
    
    # Replace footer tags with placeholder  
    $content = $content -replace '(?s)<footer>.*?</footer>', '<div id="global-footer-placeholder"></div>'
    
    # Add script if missing
    $hasScript = $content -match 'src="js/global-components\.js"'
    if (-not $hasScript) {
        $scriptLine = '    <script src="js/global-components.js"></script>'
        $content = $content.Replace('</body>', "$scriptLine`n</body>")
    }
    
    # Save if changed
    if ($content -ne $original) {
        [System.IO.File]::WriteAllText($file.FullName, $content, [System.Text.UTF8Encoding]::new($false))
        Write-Host " DONE" -ForegroundColor Green
        $processedCount++
    } else {
        Write-Host " SKIP" -ForegroundColor Gray
        $skippedCount++
    }
}

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host "Processed: $processedCount" -ForegroundColor Green
Write-Host "Skipped: $skippedCount" -ForegroundColor Yellow
Write-Host ""
Write-Host "All pages now use js/global-components.js" -ForegroundColor Green
Write-Host "Future header/footer changes will auto-update everywhere!" -ForegroundColor Green
