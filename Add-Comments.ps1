<#
  Insert a consistent comment box into all HTML pages before the footer, if not already present.
  - Skips index.html
  - Skips pages that already contain an element with class="comments"
#>

$root = "c:\Users\apnao\Downloads\NewHTML"

$comments = @"
    <div class="comments">
        <h2 class="section-title">User Comments</h2>
        <div class="comment-form">
            <div class="form-group">
                <label for="page-comment-name">Your Name</label>
                <input type="text" id="page-comment-name" class="form-control" placeholder="Enter your name">
            </div>
            <div class="form-group">
                <label for="page-comment-email">Email Address</label>
                <input type="email" id="page-comment-email" class="form-control" placeholder="Enter your email">
            </div>
            <div class="form-group">
                <label for="page-comment">Your Comment</label>
                <textarea id="page-comment" class="form-control" placeholder="Share your experience with this tool"></textarea>
            </div>
            <button class="btn btn-primary">Submit Comment</button>
        </div>
    </div>
"@

$files = Get-ChildItem -Path $root -Filter *.html -Recurse
foreach ($f in $files) {
  $path = $f.FullName
  if ($path -like "*index.html") { continue }

  $content = Get-Content $path -Raw
  if ($content -match 'class="comments"') { continue }

  $footerPos = $content.IndexOf('<footer')
  if ($footerPos -ge 0) {
    $new = $content.Substring(0, $footerPos) + $comments + $content.Substring($footerPos)
    Set-Content -Path $path -Value $new -NoNewline
    Write-Host "Inserted comment box in $path"
  }
}
