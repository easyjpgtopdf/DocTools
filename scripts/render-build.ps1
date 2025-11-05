$ErrorActionPreference = "Stop"

# Ensure Docker is available
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker CLI not found. Install Docker Desktop first."
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverPath = Join-Path $root "..\server"
Push-Location $serverPath

$tag = "easyjpgtopdf-backend:local"
Write-Host "Building Docker image $tag..."
docker build -t $tag .

Write-Host "Docker build complete."
Pop-Location
