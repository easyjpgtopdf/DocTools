param(
    [string]$Root = "C:\\Users\\apnao\\Downloads\\DocTools"
)

$linkTag = '    <link rel="stylesheet" href="css/footer.css">'

$files = Get-ChildItem -Path $Root -Filter '*.html' -File -Recurse

foreach ($file in $files) {
    $content = Get-Content -LiteralPath $file.FullName -Raw

    if ($content -notmatch [regex]::Escape($linkTag)) {
        $updated = $content
        if ($content -match '</head\s*>') {
            $updated = [regex]::Replace(
                $content,
                '</head\s*>',
                "$linkTag`r`n</head>",
                [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
            )
        }
        else {
            $updated = $linkTag + "`r`n" + $content
        }

        if ($updated -ne $content) {
            Set-Content -LiteralPath $file.FullName -Value $updated -Encoding UTF8
        }
    }
}
