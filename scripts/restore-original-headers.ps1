# Restore Original Headers & Footers from 4 Hours Ago
$rootPath = "C:\Users\apnao\Downloads\DocTools"
$backupPath = Join-Path $rootPath "backups\html-backup-20251112-234241"

Write-Host "=== Restoring Original Headers & Footers ===" -ForegroundColor Cyan
Write-Host "Backup: html-backup-20251112-234241 (from 4+ hours ago)" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path $backupPath)) {
    Write-Host "ERROR: Backup directory not found!" -ForegroundColor Red
    exit 1
}

# Get all HTML files from backup
$backupFiles = Get-ChildItem -Path $backupPath -Filter "*.html" -File

Write-Host "Found $($backupFiles.Count) backup files" -ForegroundColor Yellow
Write-Host ""

$restoredCount = 0

foreach ($backupFile in $backupFiles) {
    $targetPath = Join-Path $rootPath $backupFile.Name
    
    if (Test-Path $targetPath) {
        Write-Host "Restoring: $($backupFile.Name)..." -NoNewline
        
        # Copy backup file to main directory
        Copy-Item $backupFile.FullName -Destination $targetPath -Force
        
        Write-Host " DONE" -ForegroundColor Green
        $restoredCount++
    } else {
        Write-Host "Skipping: $($backupFile.Name) (not in main directory)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== Restore Complete ===" -ForegroundColor Cyan
Write-Host "Restored: $restoredCount files" -ForegroundColor Green
Write-Host ""
Write-Host "All header/footer changes from last 4 hours have been reverted!" -ForegroundColor Green
