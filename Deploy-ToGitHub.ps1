# Deploy-ToGitHub.ps1
# यह स्क्रिप्ट केवल बदली हुई फाइल्स को GitHub पर डिप्लॉय करेगी

# 1. Git स्टेटस चेक करें
Write-Host "`n=== Git स्टेटस चेक कर रहा हूं... ===" -ForegroundColor Cyan
$status = git status --porcelain

if (-not $status) {
    Write-Host "`n❌ कोई बदलाव नहीं मिला। सभी फाइलें अपडेटेड हैं।" -ForegroundColor Yellow
    exit
}

# 2. बदली हुई फाइल्स दिखाएं
Write-Host "`n=== निम्नलिखित फाइल्स में बदलाव किए गए हैं: ===" -ForegroundColor Green
$status | ForEach-Object {
    $file = $_.Substring(3)
    $statusCode = $_.Substring(0,2).Trim()
    $statusText = switch ($statusCode) {
        'M' { 'Modified' }
        'A' { 'Added' }
        'D' { 'Deleted' }
        'R' { 'Renamed' }
        'C' { 'Copied' }
        'U' { 'Unmerged' }
        '?' { 'Untracked' }
        '!' { 'Ignored' }
        default { $statusCode }
    }
    Write-Host "[$statusText] $file" -ForegroundColor Cyan
}

# 3. क्या आगे बढ़ना है?
$confirmation = Read-Host "`nक्या आप इन बदलावों को GitHub पर डिप्लॉय करना चाहते हैं? (Y/N)"
if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
    Write-Host "`n❌ डिप्लॉयमेंट रद्द किया गया।" -ForegroundColor Red
    exit
}

# 4. Git कमांड्स
Write-Host "`n=== GitHub पर अपलोड कर रहा हूं... ===" -ForegroundColor Cyan

# 5. सभी बदलाव स्टेज करें
git add .

# 6. कमिट मैसेज बनाएं
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$commitMessage = "Auto-deploy on $timestamp"

# 7. कमिट करें
git commit -m $commitMessage

# 8. GitHub पर पुश करें
git push origin main

# 9. GitHub Pages URL
$repoUrl = git config --get remote.origin.url
$userRepo = $repoUrl -replace '^.*[:/]([^/]+/[^/]+?)(\.git)?$', '$1'
$githubPagesUrl = "https://${userRepo}.github.io"

Write-Host "`n✅ सफलतापूर्वक डिप्लॉय किया गया!" -ForegroundColor Green
Write-Host "🌐 आपका वेबसाइट यहां उपलब्ध है: $githubPagesUrl" -ForegroundColor Green
