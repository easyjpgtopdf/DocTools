# Remove Header/Footer from All Pages Except Index
$rootPath = "C:\Users\apnao\Downloads\DocTools"

Write-Host "=== Removing Headers & Footers from All Pages (Except index.html) ===" -ForegroundColor Cyan
Write-Host ""

# Get all HTML files except index.html
$htmlFiles = Get-ChildItem -Path $rootPath -Filter "*.html" -File | Where-Object {
    $_.FullName -notmatch "\\backups\\" -and 
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\server\\" -and
    $_.FullName -notmatch "\\services\\" -and
    $_.Name -ne "index.html"
}

Write-Host "Found $($htmlFiles.Count) files to process" -ForegroundColor Yellow
Write-Host ""

$processedCount = 0

foreach ($file in $htmlFiles) {
    Write-Host "Processing: $($file.Name)..." -NoNewline
    
    $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.UTF8Encoding]::new($false))
    $original = $content
    
    # Remove all header placeholders
    $content = $content -replace '<div id="global-header-placeholder"></div>\s*', ''
    
    # Remove all footer placeholders
    $content = $content -replace '<div id="global-footer-placeholder"></div>\s*', ''
    
    # Remove global-components.js script references
    $content = $content -replace '\s*<script src="js/global-components\.js"></script>\s*', ''
    
    # Remove header.css link
    $content = $content -replace '\s*<link rel="stylesheet" href="css/header\.css">\s*', ''
    
    # Remove footer.css link
    $content = $content -replace '\s*<link rel="stylesheet" href="css/footer\.css">\s*', ''
    
    # Save if changed
    if ($content -ne $original) {
        [System.IO.File]::WriteAllText($file.FullName, $content, [System.Text.UTF8Encoding]::new($false))
        Write-Host " REMOVED" -ForegroundColor Green
        $processedCount++
    } else {
        Write-Host " NO CHANGE" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host "Processed: $processedCount files" -ForegroundColor Green
Write-Host ""
Write-Host "Headers & Footers removed from all pages except index.html" -ForegroundColor Green
