# Replace 'Visiting Card' with 'AI Image Generator' only inside <footer>...</footer> across all HTML files
$root = "c:\Users\apnao\Downloads\NewHTML"

$files = Get-ChildItem -Path $root -Filter *.html -Recurse
foreach ($f in $files) {
  $path = $f.FullName
  $content = Get-Content $path -Raw
  $s = $content.IndexOf('<footer')
  if ($s -lt 0) { continue }
  $e = $content.IndexOf('</footer>', $s)
  if ($e -lt 0) { continue }
  $footerLen = ($e - $s) + 9
  $before = $content.Substring(0, $s)
  $footer = $content.Substring($s, $footerLen)
  $after = $content.Substring($e + 9)

  $newFooter = $footer -replace '>(\s*)Visiting\s+Card(\s*)<', '>AI Image Generator<'
  if ($newFooter -ne $footer) {
    $new = $before + $newFooter + $after
    Set-Content -Path $path -Value $new -NoNewline
    Write-Host "Updated footer text in $path"
  }
}
