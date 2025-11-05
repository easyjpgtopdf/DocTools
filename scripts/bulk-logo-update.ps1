$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetPath = Join-Path $root ".."
$files = Get-ChildItem -Path $targetPath -Filter *.html -Recurse | Where-Object { $_.FullName -notlike '*\node_modules\*' }
foreach ($file in $files) {
    $content = Get-Content -LiteralPath $file.FullName -Raw
    $updated = $content
    $updated = $updated -replace 'src="/images/logo\.png"', 'src="images/logo.png"'
    $updated = $updated -replace 'src="logo\.png"', 'src="images/logo.png"'
    $updated = $updated -replace 'alt="easyjpgtopdf logo"', 'alt="Logo"'
    if ($updated -ne $content) {
        Set-Content -LiteralPath $file.FullName -Value $updated -Encoding UTF8
    }
}
