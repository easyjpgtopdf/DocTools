# Ensure All Pages Have Correct CSS Links
param()

$rootPath = "C:\Users\apnao\Downloads\DocTools"

Write-Host "=== Checking & Fixing CSS Links ===" -ForegroundColor Cyan
Write-Host ""

# Get all HTML files
$htmlFiles = Get-ChildItem -Path $rootPath -Filter "*.html" -File | Where-Object {
    $_.FullName -notmatch "\\backups\\" -and 
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\server\\"
}

$fixedCount = 0
$missingCSS = @()

foreach ($file in $htmlFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $original = $content
    $fixed = $false
    
    # Check for header.css
    if ($content -notmatch 'href="css/header\.css"') {
        Write-Host "$($file.Name): Missing header.css" -ForegroundColor Yellow
        # Add after <title> tag
        if ($content -match '</title>') {
            $content = $content -replace '(</title>)', "`$1`n    <link rel=`"stylesheet`" href=`"css/header.css`">"
            $fixed = $true
        }
    }
    
    # Check for footer.css
    if ($content -notmatch 'href="css/footer\.css"') {
        Write-Host "$($file.Name): Missing footer.css" -ForegroundColor Yellow
        # Add after <title> or header.css
        if ($content -match '</title>|header\.css') {
            $content = $content -replace '(</title>|header\.css">)', "`$1`n    <link rel=`"stylesheet`" href=`"css/footer.css`">"
            $fixed = $true
        }
    }
    
    # Save if changed
    if ($fixed -and $content -ne $original) {
        [System.IO.File]::WriteAllText($file.FullName, $content, [System.Text.UTF8Encoding]::new($false))
        Write-Host "$($file.Name): FIXED" -ForegroundColor Green
        $fixedCount++
    }
}

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host "Fixed: $fixedCount files" -ForegroundColor Green
Write-Host ""
Write-Host "All pages now use consistent header & footer styles from:" -ForegroundColor Cyan
Write-Host "  - css/header.css" -ForegroundColor White
Write-Host "  - css/footer.css" -ForegroundColor White
