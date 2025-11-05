# Standardize header across all HTML pages to match index header, but remove About/Contact from header
$root = "c:\Users\apnao\Downloads\NewHTML"
$indexPath = Join-Path $root 'index.html'
if (-not (Test-Path $indexPath)) { throw "index.html not found at $indexPath" }

# Extract header from index.html
$index = Get-Content $indexPath -Raw
$hStart = $index.IndexOf('<header')
if ($hStart -lt 0) { throw 'Header start not found in index.html' }
$hEnd = $index.IndexOf('</header>', $hStart)
if ($hEnd -lt 0) { throw 'Header end not found in index.html' }
$header = $index.Substring($hStart, ($hEnd - $hStart) + 9)

# Remove About/Contact links from header nav
# Matches anchor tags containing index.html#about or index.html#contact (case-insensitive)
$headerNoAbout = [Regex]::Replace($header, '<a[^>]+href\s*=\s*"index\.html#about"[^>]*>.*?<\/a>', '', 'IgnoreCase, Singleline')
$headerClean = [Regex]::Replace($headerNoAbout, '<a[^>]+href\s*=\s*"index\.html#contact"[^>]*>.*?<\/a>', '', 'IgnoreCase, Singleline')

# Also collapse any double spaces that might result from removal
$headerClean = $headerClean -replace '>\s+<', '><'

# Replace header in all html files
$files = Get-ChildItem -Path $root -Filter *.html -Recurse
foreach ($f in $files) {
  $path = $f.FullName
  $content = Get-Content $path -Raw
  $s = $content.IndexOf('<header')
  if ($s -lt 0) { continue }
  $e = $content.IndexOf('</header>', $s)
  if ($e -lt 0) { continue }
  $new = $content.Substring(0, $s) + $headerClean + $content.Substring($e + 9)
  Set-Content -Path $path -Value $new -NoNewline
  Write-Host "Updated header in $path"
}
