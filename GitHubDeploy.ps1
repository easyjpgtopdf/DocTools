<#
GitHub Auto-Deploy Script
यह स्क्रिप्ट आपके DocTools प्रोजेक्ट को GitHub पर आसानी से डिप्लॉय करने में मदद करेगी।

कैसे इस्तेमाल करें:
1. पहली बार के लिए:
   - GitHub पर नई रिपॉजिटरी बनाएं
   - नीचे दिए गए 'पहली बार सेटअप' सेक्शन को अनकमेंट करें और चलाएं
   - अपने GitHub यूजरनेम और रिपॉजिटरी नाम से बदलें

2. डिप्लॉय करने के लिए:
   - PowerShell खोलें
   - इस स्क्रिप्ट को रन करें: .\GitHubDeploy.ps1
   - Y दबाकर कन्फर्म करें

3. स्वचालित रूप से:
   - सभी नई/बदली हुई फाइल्स डिटेक्ट होंगी
   - आपको प्रीव्यू दिखेगा
   - कन्फर्म करने पर GitHub पर अपलोड हो जाएगा
#>

# ============ CONFIGURATION ============
$GITHUB_USERNAME = "your-username"  # अपना GitHub यूजरनेम लिखें
$REPO_NAME = "DocTools"            # रिपॉजिटरी का नाम
# ======================================

function Show-Header {
    Clear-Host
    Write-Host "=== GitHub Auto-Deploy Script ===" -ForegroundColor Cyan
    Write-Host "DocTools प्रोजेक्ट के लिए" -ForegroundColor Yellow
    Write-Host "================================" -ForegroundColor Cyan
}

function Initialize-Git {
    # पहली बार सेटअप (अनकमेंट करके चलाएं)
    <#
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main
    git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    #>
    
    # Git कॉन्फिगरेशन चेक करें
    if (-not (git config --get remote.origin.url)) {
        Write-Host "❌ Git रिमोट सेटअप नहीं है।" -ForegroundColor Red
        Write-Host "कृपया पहले 'Initialize-Git' फंक्शन को अनकमेंट करके सेटअप करें।" -ForegroundColor Yellow
        exit
    }
}

function Get-GitStatus {
    # Git स्टेटस चेक करें
    $status = git status --porcelain
    
    if (-not $status) {
        Write-Host "`n✅ कोई बदलाव नहीं मिला। सभी फाइलें अपडेटेड हैं।" -ForegroundColor Green
        exit
    }
    
    # बदलावों की जानकारी दिखाएं
    Write-Host "`n=== बदलावों की सूची ===" -ForegroundColor Cyan
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
            '??' { 'New File' }
            default { $statusCode }
        }
        
        Write-Host "[$statusText] $file" -ForegroundColor Cyan
    }
    
    return $status
}

function Confirm-Deploy {
    # कन्फर्मेशन लें
    Write-Host "`n=== डिप्लॉयमेंट कन्फर्मेशन ===" -ForegroundColor Yellow
    $confirmation = Read-Host "क्या आप इन बदलावों को GitHub पर डिप्लॉय करना चाहते हैं? (Y/N)"
    
    if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
        Write-Host "`n❌ डिप्लॉयमेंट रद्द किया गया।" -ForegroundColor Red
        exit
    }
}

function Invoke-GitDeploy {
    # Git कमांड्स
    Write-Host "`n=== GitHub पर अपलोड कर रहा हूं... ===" -ForegroundColor Cyan
    
    try {
        # सभी बदलाव स्टेज करें
        git add .
        
        # कमिट मैसेज बनाएं
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $commitMessage = "Auto-deploy on $timestamp"
        
        # कमिट करें
        git commit -m $commitMessage
        
        # GitHub पर पुश करें
        git push origin main
        
        # GitHub Pages URL
        $githubPagesUrl = "https://$GITHUB_USERNAME.github.io/$REPO_NAME"
        
        Write-Host "`n✅ सफलतापूर्वक डिप्लॉय किया गया!" -ForegroundColor Green
        Write-Host "🌐 आपका वेबसाइट यहां उपलब्ध है: $githubPagesUrl" -ForegroundColor Green
        
        # ब्राउज़र में खोलें
        Start-Process $githubPagesUrl
    }
    catch {
        Write-Host "`n❌ त्रुटि: $_" -ForegroundColor Red
        Write-Host "कृपया इंटरनेट कनेक्शन और Git क्रेडेंशियल्स चेक करें।" -ForegroundColor Yellow
    }
}

# मुख्य प्रोग्राम
Show-Header
Initialize-Git
$changes = Get-GitStatus
if ($changes) {
    Confirm-Deploy
    Invoke-GitDeploy
}
