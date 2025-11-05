# Rename visiting-card.html to ai-image-generator.html and update all references site-wide
$root = "c:\Users\apnao\Downloads\NewHTML"
$old = Join-Path $root 'visiting-card.html'
$new = Join-Path $root 'ai-image-generator.html'

if (Test-Path $old) {
  Rename-Item -Path $old -NewName 'ai-image-generator.html' -Force
  Write-Host "Renamed visiting-card.html -> ai-image-generator.html"
} elseif (-not (Test-Path $new)) {
  throw "Neither $old nor $new exists."
}

# Replace references in all HTML files
$files = Get-ChildItem -Path $root -Filter *.html -Recurse
foreach ($f in $files) {
  $path = $f.FullName
  $content = Get-Content $path -Raw
  $updated = $content -replace 'visiting-card\.html', 'ai-image-generator.html'
  if ($updated -ne $content) {
    Set-Content -Path $path -Value $updated -NoNewline
    Write-Host "Updated reference in $path"
  }
}
