# Ensure Footer.css in All Pages
$rootPath = "C:\Users\apnao\Downloads\DocTools"

Write-Host "=== Adding footer.css to all pages ===" -ForegroundColor Cyan
Write-Host ""

# Get all HTML files except backups
$htmlFiles = Get-ChildItem -Path $rootPath -Filter "*.html" -File | Where-Object {
    $_.FullName -notmatch "\\backups\\" -and 
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\server\\"
}

Write-Host "Found $($htmlFiles.Count) files" -ForegroundColor Yellow
Write-Host ""

$addedCount = 0
$skippedCount = 0

foreach ($file in $htmlFiles) {
    Write-Host "Processing: $($file.Name)..." -NoNewline
    
    $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.UTF8Encoding]::new($false))
    
    # Check if footer.css already exists
    if ($content -match 'href="css/footer\.css"') {
        Write-Host " SKIP (already has footer.css)" -ForegroundColor Gray
        $skippedCount++
        continue
    }
    
    # Add footer.css link after </title> or at end of <head>
    if ($content -match '</title>') {
        $content = $content -replace '(</title>)', "`$1`n    <link rel=`"stylesheet`" href=`"css/footer.css`">"
    } elseif ($content -match '</head>') {
        $content = $content -replace '(</head>)', "    <link rel=`"stylesheet`" href=`"css/footer.css`">`n`$1"
    } else {
        Write-Host " ERROR (no </title> or </head> found)" -ForegroundColor Red
        continue
    }
    
    [System.IO.File]::WriteAllText($file.FullName, $content, [System.Text.UTF8Encoding]::new($false))
    Write-Host " ADDED" -ForegroundColor Green
    $addedCount++
}

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host "Added footer.css to: $addedCount files" -ForegroundColor Green
Write-Host "Skipped: $skippedCount files" -ForegroundColor Yellow
Write-Host ""
Write-Host "All pages now have centered footer styling!" -ForegroundColor Green
