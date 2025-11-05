# Extract footer from index.html and apply it to all .html files in this folder and subfolders
$indexPath = "c:\Users\apnao\Downloads\NewHTML\index.html"
if (-not (Test-Path $indexPath)) { throw "index.html not found at $indexPath" }
$index = Get-Content $indexPath -Raw
$start = $index.IndexOf('<footer')
if ($start -lt 0) { throw 'Footer start not found in index.html' }
$end = $index.IndexOf('</footer>', $start)
if ($end -lt 0) { throw 'Footer end not found in index.html' }
$footer = $index.Substring($start, ($end - $start) + 9)

Get-ChildItem -Path "c:\Users\apnao\Downloads\NewHTML" -Filter *.html -Recurse |
  ForEach-Object {
    $path = $_.FullName
    $content = Get-Content $path -Raw
    $s = $content.IndexOf('<footer')
    $e = -1
    if ($s -ge 0) { $e = $content.IndexOf('</footer>', $s) }
    if ($s -ge 0 -and $e -ge 0) {
      $new = $content.Substring(0, $s) + $footer + $content.Substring($e + 9)
      Set-Content -Path $path -Value $new -NoNewline
      Write-Host "Updated footer in $path"
    }
  }
