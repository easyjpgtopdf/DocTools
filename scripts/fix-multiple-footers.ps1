# Fix Multiple Footers and Style Issues
param()

$rootPath = "C:\Users\apnao\Downloads\DocTools"

Write-Host "=== Fixing Multiple Footers & Styles ===" -ForegroundColor Cyan
Write-Host ""

# Files with multiple footers
$problemFiles = @(
    "resume-maker.html",
    "Indian-style-Resume-generator.html", 
    "edit-pdf.html",
    "ppt-to-pdf.html"
)

$fixedCount = 0

foreach ($fileName in $problemFiles) {
    $filePath = Join-Path $rootPath $fileName
    
    if (Test-Path $filePath) {
        Write-Host "Fixing: $fileName..." -NoNewline
        
        # Read content
        $content = Get-Content $filePath -Raw -Encoding UTF8
        $original = $content
        
        # Count footer placeholders
        $footerMatches = [regex]::Matches($content, '<div id="global-footer-placeholder"></div>')
        $footerCount = $footerMatches.Count
        
        if ($footerCount -gt 1) {
            Write-Host " Found $footerCount footers! " -NoNewline -ForegroundColor Yellow
            
            # Remove all footer placeholders
            $content = $content -replace '<div id="global-footer-placeholder"></div>', ''
            
            # Add single footer placeholder before closing body tag
            $content = $content.Replace('</body>', '<div id="global-footer-placeholder"></div>' + "`n" + '</body>')
            
            # Save
            [System.IO.File]::WriteAllText($filePath, $content, [System.Text.UTF8Encoding]::new($false))
            Write-Host "FIXED (reduced to 1 footer)" -ForegroundColor Green
            $fixedCount++
        } else {
            Write-Host " OK (already 1 footer)" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host "Fixed: $fixedCount files" -ForegroundColor Green
