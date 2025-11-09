<#
Smart GitHub Deployer - DocTools
================================
यह स्क्रिप्ट आपको GitHub पर आसानी से डिप्लॉय करने में मदद करेगी।

मुख्य विशेषताएं:
1. नई फाइल्स को ऑटो-डिटेक्ट करना
2. बदली हुई फाइल्स को दिखाना
3. पुरानी/अनचेंज्ड फाइल्स को स्किप करना
4. हर स्टेप पर कन्फर्मेशन लेना
5. डिटेल्ड लॉगिंग

कैसे इस्तेमाल करें:
1. पहली बार: .\SmartGitDeploy.ps1 -FirstTime
2. बाद में: .\SmartGitDeploy.ps1
#>

param (
    [switch]$FirstTime = $false
)

# ============ CONFIGURATION ============
$GITHUB_USERNAME = "your-username"  # अपना GitHub यूजरनेम
$REPO_NAME = "DocTools"            # रिपॉजिटरी का नाम
$BRANCH = "main"                   # डिफॉल्ट ब्रांच
# ======================================

# कलर स्कीम
$colors = @{
    Header = 'Cyan'
    Success = 'Green'
    Warning = 'Yellow'
    Error = 'Red'
    Info = 'White'
    Highlight = 'Magenta'
}

function Show-Header {
    Clear-Host
    Write-Host "=== Smart GitHub Deployer ===" -ForegroundColor $colors.Header
    Write-Host "DocTools - Professional Deployment Tool" -ForegroundColor $colors.Highlight
    Write-Host "=====================================" -ForegroundColor $colors.Header
}

function Test-CommandExists {
    param($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    if (-not $exists) {
        Write-Host "❌ $command नहीं मिला!" -ForegroundColor $colors.Error
        if ($command -eq 'git') {
            Write-Host "कृपया Git इंस्टॉल करें: https://git-scm.com/download/win" -ForegroundColor $colors.Warning
        }
        exit 1
    }
    return $true
}

function Initialize-GitRepository {
    Write-Host "`n🔍 Git रिपॉजिटरी चेक कर रहा हूं..." -ForegroundColor $colors.Info
    
    if (-not (Test-Path ".git")) {
        Write-Host "ℹ️ Git रिपॉजिटरी इनिशियलाइज़ नहीं है" -ForegroundColor $colors.Warning
        $choice = Read-Host "क्या आप Git रिपॉजिटरी इनिशियलाइज़ करना चाहते हैं? (Y/N)"
        if ($choice -eq 'Y' -or $choice -eq 'y') {
            git init
            git add .
            git commit -m "Initial commit"
            git branch -M $BRANCH
            Write-Host "✅ Git रिपॉजिटरी सफलतापूर्वक इनिशियलाइज़ की गई" -ForegroundColor $colors.Success
        } else {
            Write-Host "❌ Git रिपॉजिटरी के बिना जारी नहीं रख सकते" -ForegroundColor $colors.Error
            exit 1
        }
    }
    
    # रिमोट रिपॉजिटरी सेटअप
    if (-not (git config --get remote.origin.url)) {
        $repoUrl = "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
        Write-Host "ℹ️ रिमोट रिपॉजिटरी सेटअप नहीं है" -ForegroundColor $colors.Warning
        $choice = Read-Host "क्या आप रिमोट रिपॉजिटरी जोड़ना चाहते हैं? [$repoUrl] (Y/N)"
        if ($choice -eq 'Y' -or $choice -eq 'y') {
            git remote add origin $repoUrl
            Write-Host "✅ रिमोट रिपॉजिटरी जोड़ी गई" -ForegroundColor $colors.Success
        } else {
            Write-Host "❌ रिमोट रिपॉजिटरी के बिना जारी नहीं रख सकते" -ForegroundColor $colors.Error
            exit 1
        }
    }
}

function Get-FileChanges {
    Write-Host "`n🔍 फाइल परिवर्तनों की जांच कर रहा हूं..." -ForegroundColor $colors.Info
    
    # स्टेज्ड और अनस्टेज्ड दोनों तरह के बदलाव देखें
    $changes = git status --porcelain
    
    if (-not $changes) {
        Write-Host "✅ कोई बदलाव नहीं मिला। सभी फाइलें अपडेटेड हैं।" -ForegroundColor $colors.Success
        exit 0
    }
    
    # बदलावों को कैटेगराइज़ करें
    $fileChanges = @{
        Added = @()
        Modified = @()
        Deleted = @()
        Renamed = @()
        Untracked = @()
    }
    
    foreach ($change in $changes) {
        $status = $change.Substring(0,2).Trim()
        $file = $change.Substring(3)
        
        switch -Wildcard ($status) {
            'A*' { $fileChanges.Added += $file }
            'M*' { $fileChanges.Modified += $file }
            'D*' { $fileChanges.Deleted += $file }
            'R*' { $fileChanges.Renamed += $file }
            '??*' { $fileChanges.Untracked += $file }
        }
    }
    
    return $fileChanges
}

function Show-ChangesSummary {
    param($changes)
    
    Write-Host "`n📊 बदलावों का सारांश:" -ForegroundColor $colors.Header
    
    if ($changes.Added.Count -gt 0) {
        Write-Host ("`n➕ {0} नई फाइलें:" -f $changes.Added.Count) -ForegroundColor $colors.Success
        $changes.Added | ForEach-Object { Write-Host "  - $_" -ForegroundColor $colors.Success }
    }
    
    if ($changes.Modified.Count -gt 0) {
        Write-Host ("`n✏️ {0} संशोधित फाइलें:" -f $changes.Modified.Count) -ForegroundColor $colors.Warning
        $changes.Modified | ForEach-Object { Write-Host "  - $_" -ForegroundColor $colors.Warning }
    }
    
    if ($changes.Deleted.Count -gt 0) {
        Write-Host ("`n🗑️ {0} हटाई गई फाइलें:" -f $changes.Deleted.Count) -ForegroundColor $colors.Error
        $changes.Deleted | ForEach-Object { Write-Host "  - $_" -ForegroundColor $colors.Error }
    }
    
    if ($changes.Renamed.Count -gt 0) {
        Write-Host ("`n🔄 {0} पुनर्नामित फाइलें:" -f $changes.Renamed.Count) -ForegroundColor $colors.Highlight
        $changes.Renamed | ForEach-Object { Write-Host "  - $_" -ForegroundColor $colors.Highlight }
    }
    
    if ($changes.Untracked.Count -gt 0) {
        Write-Host ("`n❓ {0} अनट्रैक की गई फाइलें:" -f $changes.Untracked.Count) -ForegroundColor $colors.Info
        $changes.Untracked | ForEach-Object { Write-Host "  - $_" -ForegroundColor $colors.Info }
    }
}

function Confirm-Deployment {
    param($changes)
    
    $totalChanges = $changes.Values | ForEach-Object { $_.Count } | Measure-Object -Sum | Select-Object -ExpandProperty Sum
    
    Write-Host "`n⚠️ कुल $totalChanges फाइलें बदलने के लिए तैयार हैं" -ForegroundColor $colors.Warning
    $confirmation = Read-Host "क्या आप इन बदलावों को GitHub पर डिप्लॉय करना चाहते हैं? (Y/N)"
    
    if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
        Write-Host "`n❌ डिप्लॉयमेंट रद्द किया गया" -ForegroundColor $colors.Error
        exit 0
    }
}

function Invoke-GitDeploy {
    param($changes)
    
    Write-Host "`n🚀 GitHub पर डिप्लॉय शुरू कर रहा हूं..." -ForegroundColor $colors.Header
    
    try {
        # सभी बदलावों को स्टेज करें
        git add .
        
        # कमिट मैसेज बनाएं
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $commitMessage = "Auto-deploy on $timestamp`n`n"
        $commitMessage += "Changes:`n"
        
        if ($changes.Added.Count -gt 0) {
            $commitMessage += "- Added: $($changes.Added.Count) files`n"
        }
        if ($changes.Modified.Count -gt 0) {
            $commitMessage += "- Modified: $($changes.Modified.Count) files`n"
        }
        if ($changes.Deleted.Count -gt 0) {
            $commitMessage += "- Deleted: $($changes.Deleted.Count) files`n"
        }
        
        # कमिट करें
        git commit -m $commitMessage
        
        # GitHub पर पुश करें
        Write-Host "`n📤 GitHub पर अपलोड कर रहा हूं..." -ForegroundColor $colors.Info
        git push -u origin $BRANCH --force
        
        # GitHub Pages URL
        $githubPagesUrl = "https://$GITHUB_USERNAME.github.io/$REPO_NAME"
        
        Write-Host "`n✅ सफलतापूर्वक डिप्लॉय किया गया!" -ForegroundColor $colors.Success
        Write-Host "🌐 आपकी वेबसाइट: $githubPagesUrl" -ForegroundColor $colors.Success -BackgroundColor DarkBlue
        
        # ब्राउज़र में खोलें
        Start-Process $githubPagesUrl
    }
    catch {
        Write-Host "`n❌ त्रुटि: $_" -ForegroundColor $colors.Error
        Write-Host "कृपया इंटरनेट कनेक्शन और Git क्रेडेंशियल्स चेक करें।" -ForegroundColor $colors.Warning
        exit 1
    }
}

# मुख्य प्रोग्राम
Show-Header

# आवश्यक टूल्स चेक करें
Test-CommandExists "git"

# Git रिपॉजिटरी इनिशियलाइज़ करें
Initialize-GitRepository

# बदलावों को चेक करें
$changes = Get-FileChanges

# बदलावों को दिखाएं
Show-ChangesSummary -changes $changes

# डिप्लॉयमेंट कन्फर्म करें
Confirm-Deployment -changes $changes

# डिप्लॉय प्रोसेस शुरू करें
Invoke-GitDeploy -changes $changes

Write-Host "`n✨ प्रक्रिया पूरी हुई!" -ForegroundColor $colors.Success
