$ErrorActionPreference = 'Stop'
$root = 'c:\Users\apnao\Downloads\NewHTML'
$indexPath = Join-Path $root 'index.html'
if (-not (Test-Path $indexPath)) { throw "index.html not found at $indexPath" }
$index = Get-Content -Raw -LiteralPath $indexPath

$headerMatch = [regex]::Match($index, '<header[\s\S]*?</header>')
$footerMatch = [regex]::Match($index, '<footer[\s\S]*?</footer>')
if (-not $headerMatch.Success) { throw 'Could not extract <header> from index.html' }
if (-not $footerMatch.Success) { throw 'Could not extract <footer> from index.html' }
$header = $headerMatch.Value
$footer = $footerMatch.Value

Get-ChildItem -Path $root -Filter *.html -File | Where-Object { $_.Name -ne 'index.html' } | ForEach-Object {
  $path = $_.FullName
  $html = Get-Content -Raw -LiteralPath $path

  $updated = $false
  if ($html -match '<header[\s\S]*?</header>') {
    $html = [regex]::Replace($html, '<header[\s\S]*?</header>', [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $header }, 1)
    $updated = $true
  } else {
    Write-Host "No <header> in: $($_.Name)"
  }

  if ($html -match '<footer[\s\S]*?</footer>') {
    $html = [regex]::Replace($html, '<footer[\s\S]*?</footer>', [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $footer }, 1)
    $updated = $true
  } else {
    Write-Host "No <footer> in: $($_.Name)"
  }

  if ($updated) {
    Set-Content -LiteralPath $path -Value $html -Encoding UTF8
    Write-Host "Standardized: $($_.Name)"
  }
}
