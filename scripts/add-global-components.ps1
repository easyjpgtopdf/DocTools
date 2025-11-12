# PowerShell Script to Add Global Header/Footer Placeholders to All HTML Pages
# This script will:
# 1. Backup all HTML files
# 2. Add global header/footer placeholders
# 3. Add CSS and JS links if missing

$ErrorActionPreference = "Continue"
$rootPath = Split-Path -Parent $PSScriptRoot

# Process both root and server/public directories
$targetPaths = @(
    $rootPath,
    (Join-Path $rootPath "server\public")
)

Write-Host "`n=== Global Header/Footer Integration Script ===" -ForegroundColor Cyan

$totalSuccess = 0
$totalSkipped = 0

foreach ($targetPath in $targetPaths) {
    if (-not (Test-Path $targetPath)) {
        Write-Host "`nSkipping: $targetPath (not found)" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "`n--- Processing: $targetPath ---" -ForegroundColor Magenta
    
    # Get all HTML files
    $htmlFiles = Get-ChildItem -Path $targetPath -Filter "*.html" -File | Where-Object { 
        $_.Name -notmatch "^(test-|result\.html)" 
    }
    
    Write-Host "Found $($htmlFiles.Count) HTML files to process" -ForegroundColor Green
    
    # Backup directory
    $backupDir = Join-Path $targetPath "backups\html-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Write-Host "Backup directory: $backupDir" -ForegroundColor Yellow
    
    $successCount = 0
    $skippedCount = 0
    
    foreach ($file in $htmlFiles) {
        Write-Host "  Processing: $($file.Name)..." -NoNewline
        
        try {
            # Backup original file
            Copy-Item -Path $file.FullName -Destination $backupDir -Force
            
            # Read file content
            $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
            
            # Check if already has placeholders
            if ($content -match 'global-header-placeholder' -and $content -match 'global-footer-placeholder') {
                Write-Host " [SKIPPED]" -ForegroundColor Yellow
                $skippedCount++
                continue
            }
            
            $modified = $false
            
            # Add CSS links if missing in <head>
            if ($content -notmatch 'css/header\.css') {
                $content = $content -replace '(</head>)', @"
    <link rel="stylesheet" href="css/header.css">
    <link rel="stylesheet" href="css/footer.css">
`$1
"@
                $modified = $true
            }
            
            # Replace existing <header> tag with placeholder
            if ($content -match '<header[\s>]') {
                # Find the closing </header> tag
                if ($content -match '(?s)<header.*?</header>') {
                    $content = $content -replace '(?s)<header.*?</header>', '<div id="global-header-placeholder"></div>'
                    $modified = $true
                }
            }
            # If no header exists, add placeholder after <body>
            elseif ($content -match '<body[^>]*>') {
                $content = $content -replace '(<body[^>]*>)', "`$1`n    <div id=`"global-header-placeholder`"></div>"
                $modified = $true
            }
            
            # Replace existing <footer> tag with placeholder
            if ($content -match '<footer[\s>]') {
                if ($content -match '(?s)<footer.*?</footer>') {
                    $content = $content -replace '(?s)<footer.*?</footer>', '<div id="global-footer-placeholder"></div>'
                    $modified = $true
                }
            }
            # If no footer exists, add placeholder before </body>
            elseif ($content -match '</body>') {
                $content = $content -replace '(</body>)', "    <div id=`"global-footer-placeholder`"></div>`n`$1"
                $modified = $true
            }
            
            # Add global-components.js before closing </body> if not present
            if ($content -notmatch 'global-components\.js') {
                $content = $content -replace '(</body>)', @"
    <script src="js/global-components.js"></script>
`$1
"@
                $modified = $true
            }
            
            if ($modified) {
                # Save modified content
                Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
                Write-Host " [SUCCESS]" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host " [NO CHANGES]" -ForegroundColor Gray
                $skippedCount++
            }
            
        } catch {
            Write-Host " [ERROR: $($_.Exception.Message)]" -ForegroundColor Red
        }
    }
    
    Write-Host "`n  Summary for $targetPath" -ForegroundColor Cyan
    Write-Host "  Successfully processed: $successCount" -ForegroundColor Green
    Write-Host "  Skipped: $skippedCount" -ForegroundColor Yellow
    
    $totalSuccess += $successCount
    $totalSkipped += $skippedCount
}

Write-Host "`n=== Overall Summary ===" -ForegroundColor Cyan
Write-Host "Total successfully processed: $totalSuccess" -ForegroundColor Green
Write-Host "Total skipped: $totalSkipped" -ForegroundColor Yellow

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Review changes in modified files" -ForegroundColor White
Write-Host "2. Test a few pages to verify header/footer display correctly" -ForegroundColor White
Write-Host "3. If everything looks good, commit changes to Git" -ForegroundColor White
Write-Host "4. To revert: Copy files from backup directory`n" -ForegroundColor White

Read-Host "Press Enter to exit"
