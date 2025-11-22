# Apply Exact Header & Footer from Index to All Pages
$rootPath = "C:\Users\apnao\Downloads\DocTools"

Write-Host "=== Applying Index Page Header & Footer to All Pages ===" -ForegroundColor Cyan
Write-Host ""

# Exact header HTML from index page (via global-components.js)
$headerHTML = @'
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
                        <a href="add-page-numbers.html">Add Page Numbers</a>
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
                <div class="dropdown">
                    <a href="#">Other Tools <i class="fas fa-chevron-down"></i></a>
                    <div class="dropdown-content">
                        <a href="excel-unlocker/" target="_blank">Excel Unlocker</a>
                        <a href="protect-excel.html">Protect Excel Sheet</a>
                    </div>
                </div>
            </div>
            <div class="auth-buttons">
                <a href="login.html" class="auth-link">Sign In</a>
                <a href="signup.html" class="auth-btn"><i class="fas fa-user-plus" aria-hidden="true"></i><span>Signup</span></a>
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
                    <a href="dashboard.html#dashboard-orders" data-user-nav="dashboard-orders"><i class="fas fa-clipboard-list"></i> Orders & Subscriptions</a>
                    <a href="accounts.html#login"><i class="fas fa-user-cog"></i> Account Center</a>
                    <button type="button" id="logout-button" class="dropdown-logout"><i class="fas fa-sign-out-alt"></i> Sign out</button>
                </div>
            </div>
        </nav>
    </div>
</header>
'@

# Exact footer HTML from index page (via global-components.js)
$footerHTML = @'
<footer>
    <div class="container footer-inner">
        <div class="footer-company-links">
            <span>Company</span>
            <a href="index.html#about">About Us</a>
            <a href="index.html#contact">Contact</a>
            <a href="privacy-policy.html">Privacy Policy</a>
            <a href="terms-of-service.html">Terms of Service</a>
        </div>
        <p class="footer-brand-line">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone.</p>
        <p class="footer-credits">
            Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
            <a href="attributions.html">See full acknowledgements</a>.
        </p>
    </div>
</footer>
'@

# Get all HTML files except index.html
$htmlFiles = Get-ChildItem -Path $rootPath -Filter "*.html" -File | Where-Object {
    $_.Name -ne "index.html" -and
    $_.FullName -notmatch "\\backups\\" -and 
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\server\\"
}

Write-Host "Found $($htmlFiles.Count) files to update" -ForegroundColor Yellow
Write-Host ""

$processedCount = 0

foreach ($file in $htmlFiles) {
    Write-Host "Processing: $($file.Name)..." -NoNewline
    
    $content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.UTF8Encoding]::new($false))
    
    # Add header after <body> tag
    if ($content -match '<body[^>]*>') {
        $content = $content -replace '(<body[^>]*>)', "`$1`n$headerHTML`n"
    }
    
    # Add footer before </body> tag
    if ($content -match '</body>') {
        $content = $content -replace '(</body>)', "`n$footerHTML`n`$1"
    }
    
    # Ensure CSS links are present
    if ($content -notmatch 'href="css/header\.css"') {
        $content = $content -replace '(</title>)', "`$1`n    <link rel=`"stylesheet`" href=`"css/header.css`">"
    }
    if ($content -notmatch 'href="css/footer\.css"') {
        $content = $content -replace '(</title>)', "`$1`n    <link rel=`"stylesheet`" href=`"css/footer.css`">"
    }
    
    # Add auth.js script if not present (for user menu functionality)
    if ($content -notmatch 'src="js/auth\.js"' -and $content -match '</body>') {
        $content = $content -replace '(</body>)', "    <script src=`"js/auth.js`"></script>`n`$1"
    }
    
    [System.IO.File]::WriteAllText($file.FullName, $content, [System.Text.UTF8Encoding]::new($false))
    Write-Host " DONE" -ForegroundColor Green
    $processedCount++
}

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host "Processed: $processedCount files" -ForegroundColor Green
Write-Host ""
Write-Host "All pages now have:" -ForegroundColor Green
Write-Host "  - Exact same header as index.html" -ForegroundColor White
Write-Host "  - Exact same footer as index.html" -ForegroundColor White
Write-Host "  - Same fonts, spacing, alignment" -ForegroundColor White
Write-Host "  - header.css & footer.css linked" -ForegroundColor White
Write-Host "  - auth.js for user menu functionality" -ForegroundColor White
