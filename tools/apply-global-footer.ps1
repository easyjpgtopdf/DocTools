param(
    [string]$Root = "C:\\Users\\apnao\\Downloads\\DocTools"
)

$footer = @"
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
"@.Trim()

$files = Get-ChildItem -Path $Root -Filter '*.html' -File -Recurse |
    Where-Object { $_.Name -notin 'index.html','accounts.html' }

foreach ($file in $files) {
    $content = Get-Content -LiteralPath $file.FullName -Raw
    $content = [regex]::Replace($content, '<footer[\s\S]*?</footer>', '', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if ($content -match '</body\s*>') {
        $content = [regex]::Replace($content, '</body\s*>', "$footer`r`n</body>", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    }
    else {
        $content = $content.TrimEnd() + "`r`n$footer`r`n"
    }
    Set-Content -LiteralPath $file.FullName -Value $content -Encoding UTF8
}
