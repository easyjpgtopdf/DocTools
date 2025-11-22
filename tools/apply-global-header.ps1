param(
    [string]$Root = "C:\\Users\\apnao\\Downloads\\DocTools"
)

$header = @"
    <header>
        <div class="container">
            <nav class="navbar">
                <a href="index.html" class="logo"><img src="images/logo.png" alt="Logo" style="height:54px;"></a>
                <div class="nav-links">
                    <div class="dropdown">
                        <a href="#">Convert to PDF <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="jpg-to-pdf.html">JPG to PDF</a>
                            <a href="word-to-pdf.html">Word to PDF</a>
                            <a href="excel-to-pdf.html">Excel to PDF</a>
                            <a href="ppt-to-pdf.html">PowerPoint to PDF</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">Convert from PDF <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="pdf-to-jpg.html">PDF to JPG</a>
                            <a href="pdf-to-word.html">PDF to Word</a>
                            <a href="pdf-to-excel.html">PDF to Excel</a>
                            <a href="pdf-to-ppt.html">PDF to PowerPoint</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">Pdf Editor <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="merge-pdf.html">Merge PDF</a>
                            <a href="split-pdf.html">Split PDF</a>
                            <a href="compress-pdf.html">Compress PDF</a>
                            <a href="edit-pdf.html">Pdf Editor</a>
                            <a href="protect-pdf.html">Protect PDF</a>
                            <a href="unlock-pdf.html">Unlock PDF</a>
                            <a href="watermark-pdf.html">Watermark PDF</a>
                            <a href="crop-pdf.html">Crop PDF</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">Image Tools <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="image-compressor.html">Image Compressor</a>
                            <a href="image-resizer.html">Image Resizer</a>
                            <a href="image-editor.html">Image Editor</a>
                            <a href="background-remover.html">Image Background Remover</a>
                            <a href="ocr-image.html">OCR Image</a>
                            <a href="image-watermark.html">Image Watermark Tool</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">Other Tools <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="resume-maker.html">Resume Maker</a>
                            <a href="biodata-maker.html">Marrige Biodata-Data Maker</a>
                            <a href="ai-image-generator.html">AI Image Generator</a>
                            <a href="marriage-card.html">Marriage Card</a>
                        </div>
                    </div>
                </div>
                <div class="auth-buttons">
                    <a href="login.html" class="auth-link">Sign In</a>
                    <a href="signup.html" class="auth-btn"><i class="fas fa-user-plus" aria-hidden="true"></i><span>Create Account</span></a>
                </div>
                <div id="user-menu" class="user-menu" data-open="false">
                    <button id="user-menu-toggle" class="user-menu-toggle" type="button" aria-haspopup="true" aria-expanded="false" aria-label="Account menu">
                        <span class="user-initial" aria-hidden="true">U</span>
                        <i class="fas fa-chevron-down" aria-hidden="true"></i>
                    </button>
                    <div class="user-dropdown" id="user-dropdown" hidden>
                        <a href="dashboard.html#dashboard-overview" data-user-nav="dashboard-overview"><i class="fas fa-user-circle"></i> Account Dashboard</a>
                        <a href="dashboard.html#dashboard-billing" data-user-nav="dashboard-billing"><i class="fas fa-file-invoice"></i> Billing Details</a>
                        <a href="dashboard.html#dashboard-payments" data-user-nav="dashboard-payments"><i class="fas fa-wallet"></i> Payment History</a>
                        <a href="dashboard.html#dashboard-orders" data-user-nav="dashboard-orders"><i class="fas fa-clipboard-list"></i> Orders &amp; Subscriptions</a>
                        <a href="accounts.html#login"><i class="fas fa-user-cog"></i> Account Center</a>
                        <button type="button" id="logout-button" class="dropdown-logout"><i class="fas fa-sign-out-alt"></i> Sign out</button>
                    </div>
                </div>
            </nav>
        </div>
    </header>
"@.Trim()

$files = Get-ChildItem -Path $Root -Filter '*.html' -File -Recurse |
    Where-Object { $_.Name -ne 'index.html' }

$headerPattern = [regex]'(?is)<header\b[\s\S]*?</header>'
$bodyPattern = [regex]'(?is)(<body[^>]*>)'

foreach ($file in $files) {
    $content = Get-Content -LiteralPath $file.FullName -Raw

    # Remove existing header blocks
    $content = $headerPattern.Replace($content, '')

    # Insert the standardized header right after <body>
    if ($bodyPattern.IsMatch($content)) {
        $content = $bodyPattern.Replace($content, { param($match) "$($match.Value)`r`n$header" }, 1)
    }
    else {
        $content = "$header`r`n$content"
    }

    Set-Content -LiteralPath $file.FullName -Value $content -Encoding UTF8
}

. "${PSScriptRoot}\inject-header-css.ps1" -Root $Root
. "${PSScriptRoot}\inject-footer-css.ps1" -Root $Root
. "${PSScriptRoot}\apply-global-footer.ps1" -Root $Root
