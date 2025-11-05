$ErrorActionPreference = 'Stop'
$root = 'c:\Users\apnao\Downloads\NewHTML'

# Generic text replacements for mojibake
$genericMap = @{
  'Ã—' = '×'
  'â€”' = '—'
  'â€“' = '–'
  'â€¢' = '•'
  'ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢' = '•'
  'ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦' = '…'
  'Ã¢â€šÂ¬' = '€'
  'Ã‚' = ''
  'Â' = ''
}

function Apply-Replacements($path){
  $c = Get-Content -Raw -LiteralPath $path
  foreach($k in $genericMap.Keys){ $c = $c -replace [regex]::Escape($k), $genericMap[$k] }

  if($path -like '*image-resizer.html'){
    $c = $c -replace '<i>ðŸ“</i>','<i class="fas fa-cloud-upload-alt"></i>'
    $c = $c -replace '<i>ðŸ”„</i>','<i class="fas fa-sliders-h"></i>'
    $c = $c -replace '<i>â†©ï¸</i>','<i class="fas fa-undo"></i>'
    $c = $c -replace '<i>ðŸ’¾</i>','<i class="fas fa-download"></i>'
  }
  if($path -like '*split-pdf.html'){
    $c = $c -replace '<div class="upload-icon">[^<]*</div>','<div class="upload-icon"><i class="fas fa-cloud-upload-alt"></i></div>'
    $c = $c -replace '<div class="file-icon">[^<]*</div>','<div class="file-icon"><i class="fas fa-file-pdf"></i></div>'
    $c = $c -replace '0 KB\s*•?\s*.*?\s*<span id="page-count"','0 KB • <span id="page-count"'
    $c = $c -replace 'ÃƒÂ¢Ã…â€œÃ¢â‚¬Â¦\s*','<i class="fas fa-check-circle"></i> '
    $c = $c -replace 'ÃƒÂ¢Ã‚ÂÃ…â€™\s*','<i class="fas fa-times-circle"></i> '
    $c = $c -replace 'id="split-btn" disabled>[^<]*Split PDF','id="split-btn" disabled><i class="fas fa-cut"></i> Split PDF'
    $c = $c -replace 'id="clear-btn">[^<]*Clear','id="clear-btn"><i class="fas fa-undo"></i> Clear'
  }
  if($path -like '*image-resizer-result.html'){
    # generic fixes already handle title and dimension sign
  }

  Set-Content -LiteralPath $path -Value $c -Encoding UTF8
}

Get-ChildItem -Path $root -Filter *.html -File | ForEach-Object { Apply-Replacements $_.FullName; Write-Host "Fixed: $($_.Name)" }
