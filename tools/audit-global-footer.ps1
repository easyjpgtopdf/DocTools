param(
    [string]$Root = "C:\\Users\\apnao\\Downloads\\DocTools"
)

$footer = @"
    <footer>
        <div class=\"container footer-inner\">
            <div class=\"footer-company-links\">
                <span>Company</span>
                <a href=\"index.html#about\">About Us</a>
                <a href=\"index.html#contact\">Contact</a>
                <a href=\"privacy-policy.html\">Privacy Policy</a>
                <a href=\"terms-of-service.html\">Terms of Service</a>
            </div>
            <p class=\"footer-brand-line\">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone.</p>
            <p class=\"footer-credits\">
                Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
                <a href=\"attributions.html\">See full acknowledgements</a>.
            </p>
        </div>
    </footer>
"@.Trim()

$files = Get-ChildItem -Path $Root -Filter '*.html' -File -Recurse |
    Where-Object { $_.Name -notin 'index.html','accounts.html' }

$result = foreach ($file in $files) {
    $content = Get-Content -LiteralPath $file.FullName -Raw
    $matches = [regex]::Matches($content, '<footer[\s\S]*?</footer>', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $matchesCount = $matches.Count
    $status = if ($matchesCount -eq 1 -and $matches[0].Value.Trim() -eq $footer) { 'OK' }
              elseif ($matchesCount -eq 0) { 'Missing footer' }
              elseif ($matchesCount -gt 1) { "Multiple footers ($matchesCount)" }
              elseif ($matches[0].Value.Trim() -ne $footer) { 'Footer mismatch' }
              else { 'Unknown' }

    [pscustomobject]@{
        File = $file.FullName
        Status = $status
    }
}

$result | Format-Table -AutoSize
