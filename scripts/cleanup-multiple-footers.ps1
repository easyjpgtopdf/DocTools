# Complete Footer & Script Cleanup
param()

$rootPath = "C:\Users\apnao\Downloads\DocTools"

Write-Host "=== Cleaning Multiple Footers & Scripts ===" -ForegroundColor Cyan
Write-Host ""

$problemFiles = @(
    "resume-maker.html",
    "edit-pdf.html",
    "ppt-to-pdf.html"
)

$fixedCount = 0

foreach ($fileName in $problemFiles) {
    $filePath = Join-Path $rootPath $fileName
    
    if (Test-Path $filePath) {
        Write-Host "Processing: $fileName..." -ForegroundColor Yellow
        
        # Read entire file
        $content = Get-Content $filePath -Raw -Encoding UTF8
        $original = $content
        
        # Count issues
        $footerMatches = [regex]::Matches($content, '<div id="global-footer-placeholder"></div>')
        $scriptMatches = [regex]::Matches($content, '<script src="js/global-components\.js"></script>')
        
        Write-Host "  - Found $($footerMatches.Count) footer placeholders" -ForegroundColor Gray
        Write-Host "  - Found $($scriptMatches.Count) script tags" -ForegroundColor Gray
        
        # Remove ALL footer placeholders and scripts
        $content = $content -replace '<div id="global-footer-placeholder"></div>\s*', ''
        $content = $content -replace '\s*<script src="js/global-components\.js"></script>\s*', ''
        
        # Add single footer placeholder and script before closing body
        if ($content -match '(.*?)</body>') {
            $beforeBody = $matches[1]
            # Ensure we add only once at the very end before </body>
            $content = $beforeBody.TrimEnd() + "`n`n    <div id=`"global-footer-placeholder`"></div>`n    <script src=`"js/global-components.js`"></script>`n</body>"
            
            # Handle closing html tag if exists
            if ($original -match '</html>') {
                $content += "`n</html>"
            }
        }
        
        # Save
        [System.IO.File]::WriteAllText($filePath, $content, [System.Text.UTF8Encoding]::new($false))
        Write-Host "  ✓ FIXED: Now has 1 footer and 1 script tag" -ForegroundColor Green
        Write-Host ""
        $fixedCount++
    }
}

Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host "Fixed: $fixedCount files" -ForegroundColor Green
