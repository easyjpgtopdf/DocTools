# Clean Multiple Footers
$rootPath = "C:\Users\apnao\Downloads\DocTools"

Write-Host "Fixing multiple footers..." -ForegroundColor Cyan

$files = @("resume-maker.html", "edit-pdf.html", "ppt-to-pdf.html")

foreach ($file in $files) {
    $path = Join-Path $rootPath $file
    Write-Host "Processing $file..." -NoNewline
    
    $content = [System.IO.File]::ReadAllText($path, [System.Text.UTF8Encoding]::new($false))
    
    # Remove all footer placeholders
    $content = $content -replace '<div id="global-footer-placeholder"></div>', ''
    
    # Remove all script references
    $content = $content -replace '<script src="js/global-components\.js"></script>', ''
    
    # Add single footer and script before closing body
    $content = $content.Replace('</body>', '<div id="global-footer-placeholder"></div>' + "`n" + '<script src="js/global-components.js"></script>' + "`n" + '</body>')
    
    [System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))
    Write-Host " DONE" -ForegroundColor Green
}

Write-Host "Complete!" -ForegroundColor Green
