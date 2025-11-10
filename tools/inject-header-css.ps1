param(
    [string]$Root = "C:\\Users\\apnao\\Downloads\\DocTools"
)

$headerLink = '    <link rel="stylesheet" href="css/header.css">'
$themeLink = '    <link rel="stylesheet" href="css/theme-modern.css">'
$footerLinkRegex = [regex]'([ \t]*<link rel="stylesheet" href="css/footer\.css">)'

$files = Get-ChildItem -Path $Root -Filter '*.html' -File -Recurse

foreach ($file in $files) {
    $content = Get-Content -LiteralPath $file.FullName -Raw

    # remove existing header / theme links to avoid duplicates
    $updated = [regex]::Replace($content, '<link rel="stylesheet" href="css/(header|theme-modern)\.css">', '', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)

    if ($footerLinkRegex.IsMatch($updated)) {
        $updated = $footerLinkRegex.Replace($updated, "$headerLink`r`n$themeLink`r`n$1", 1)
    }
    elseif ($updated -match '</head\s*>') {
        $updated = [regex]::Replace(
            $updated,
            '</head\s*>',
            "$headerLink`r`n$themeLink`r`n</head>",
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )
    }
    else {
        $updated = $headerLink + "`r`n" + $themeLink + "`r`n" + $updated
    }

    if ($updated -ne $content) {
        Set-Content -LiteralPath $file.FullName -Value $updated -Encoding UTF8
    }
}
