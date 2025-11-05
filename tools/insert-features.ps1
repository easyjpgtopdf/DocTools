$ErrorActionPreference = 'Stop'
$root = 'c:\Users\apnao\Downloads\NewHTML'
$features = @'
<div class="features" style="background-color:#fff;padding:80px 0;border-radius:20px;margin-bottom:50px;">
  <div class="container">
    <h2 class="section-title">Why Choose easyjpgtopdf?</h2>
    <div class="features-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:40px;">
      <div class="feature" style="display:flex;gap:20px;">
        <div class="feature-icon" style="width:60px;height:60px;background-color:#f8f9fa;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px;color:#4361ee;flex-shrink:0;">
          <i class="fas fa-shield-alt"></i>
        </div>
        <div class="feature-content">
          <h3 style="margin-bottom:10px;font-size:1.3rem;">Secure & Private</h3>
          <p style="color:#6c757d;">All files are processed securely and automatically deleted after 1 hour.</p>
        </div>
      </div>
      <div class="feature" style="display:flex;gap:20px;">
        <div class="feature-icon" style="width:60px;height:60px;background-color:#f8f9fa;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px;color:#4361ee;flex-shrink:0;">
          <i class="fas fa-bolt"></i>
        </div>
        <div class="feature-content">
          <h3 style="margin-bottom:10px;font-size:1.3rem;">Fast Processing</h3>
          <p style="color:#6c757d;">Our optimized algorithms process your files in seconds.</p>
        </div>
      </div>
      <div class="feature" style="display:flex;gap:20px;">
        <div class="feature-icon" style="width:60px;height:60px;background-color:#f8f9fa;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px;color:#4361ee;flex-shrink:0;">
          <i class="fas fa-desktop"></i>
        </div>
        <div class="feature-content">
          <h3 style="margin-bottom:10px;font-size:1.3rem;">Works Everywhere</h3>
          <p style="color:#6c757d;">Use easyjpgtopdf on any device with a modern web browser.</p>
        </div>
      </div>
      <div class="feature" style="display:flex;gap:20px;">
        <div class="feature-icon" style="width:60px;height:60px;background-color:#f8f9fa;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px;color:#4361ee;flex-shrink:0;">
          <i class="fas fa-euro-sign"></i>
        </div>
        <div class="feature-content">
          <h3 style="margin-bottom:10px;font-size:1.3rem;">Completely Free</h3>
          <p style="color:#6c757d;">All our basic tools are free to use with no hidden costs.</p>
        </div>
      </div>
    </div>
  </div>
</div>
'@

Get-ChildItem -Path $root -Filter *.html -File | Where-Object {
  $_.Name -ne 'index.html' -and -not (Select-String -Path $_.FullName -Pattern 'class="features"' -Quiet)
} | ForEach-Object {
  $content = Get-Content -Raw -LiteralPath $_.FullName
  if ($content -match '<footer>') {
    $new = $content -replace '<footer>', ($features + '<footer>')
    Set-Content -LiteralPath $_.FullName -Value $new -Encoding UTF8
    Write-Host "Updated: $($_.Name)"
  } else {
    Write-Host "Skipped (no <footer>): $($_.Name)"
  }
}
