$ErrorActionPreference = "Stop"

param(
    [string]$ServiceName = "easyjpgtopdf-backend",
    [string]$RenderToken
)

if (-not $RenderToken) {
    Write-Error "Render API token required. Pass -RenderToken or set RENDER_API_TOKEN env var."
}

if (-not $RenderToken) {
    $RenderToken = $Env:RENDER_API_TOKEN
}

if (-not $RenderToken) {
    Write-Error "Render API token missing."
}

$headers = @{ "Authorization" = "Bearer $RenderToken" }
$body = @{ serviceId = $ServiceName } | ConvertTo-Json

$response = Invoke-RestMethod -Method Post `
    -Uri "https://api.render.com/v1/services/$ServiceName/deploys" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body

Write-Host "Deployment triggered: $($response.id)"
