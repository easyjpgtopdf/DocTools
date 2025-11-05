# Inject consistent CSS styles for comment boxes into all HTML files (except index.html)
$root = "c:\Users\apnao\Downloads\NewHTML"

$marker = "/* comment styles injected */"
$css = @"
<style>
$marker
.comments { margin: 40px 0; }
.section-title { margin-bottom: 14px; color: var(--primary); }
.comment-form { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,.05); }
.comment-form .form-group { margin-bottom: 14px; }
.comment-form .form-control { padding: 10px 12px; border: 1px solid #ddd; border-radius: 8px; outline: none; }
.comment-form .form-control:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(67,97,238,0.08); }
</style>
"@

$files = Get-ChildItem -Path $root -Filter *.html -Recurse
foreach ($f in $files) {
  $path = $f.FullName
  if ($path -like "*index.html") { continue }
  $content = Get-Content $path -Raw
  if ($content -like "*${marker}*") { continue }

  $headClose = $content.IndexOf('</head>')
  if ($headClose -ge 0) {
    $new = $content.Substring(0, $headClose) + "`r`n" + $css + "`r`n" + $content.Substring($headClose)
    Set-Content -Path $path -Value $new -NoNewline
    Write-Host "Injected comment styles in $path"
  }
}
