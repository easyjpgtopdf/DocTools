# PowerShell script to add auth.js to all HTML pages
Write-Host "Adding auth.js to all HTML pages..." -ForegroundColor Cyan

$scriptTag = '    <script type="module" src="js/auth.js"></script>'
$addedCount = 0
$skippedCount = 0

# Get all HTML files in root directory
$htmlFiles = Get-ChildItem -Path "." -Filter "*.html" -File

foreach ($file in $htmlFiles) {
    # Skip test files and server files
    if ($file.Name -like "test-*" -or $file.Name -eq "result.html") {
        Write-Host "  Skipped: $($file.Name) (test/result file)" -ForegroundColor Gray
        $skippedCount++
        continue
    }

    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Check if auth.js already exists
    if ($content -match 'src="js/auth\.js"') {
        Write-Host "  Skipped: $($file.Name) (already has auth.js)" -ForegroundColor Yellow
        $skippedCount++
        continue
    }
    
    # Add auth.js before closing </body> tag
    if ($content -match '</body>') {
        $content = $content -replace '</body>', "$scriptTag`r`n</body>"
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        Write-Host "  Added: $($file.Name)" -ForegroundColor Green
        $addedCount++
    } else {
        Write-Host "  Warning: $($file.Name) has no </body> tag" -ForegroundColor Red
    }
}

Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "  Added auth.js to: $addedCount files" -ForegroundColor Green
Write-Host "  Skipped: $skippedCount files" -ForegroundColor Yellow
