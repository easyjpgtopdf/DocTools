# PowerShell Script to Add Environment Variables to Vercel from JSON File
# This script reads the Firebase service account JSON and adds it to Vercel

$jsonFilePath = "D:\Software\easyjpgtopdf-de346-firebase-adminsdk-fbsvc-9680417763.json"

Write-Host "🚀 Adding Environment Variables to Vercel..." -ForegroundColor Green
Write-Host ""

# Check if file exists
if (-not (Test-Path $jsonFilePath)) {
    Write-Host "❌ JSON file not found at: $jsonFilePath" -ForegroundColor Red
    exit 1
}

# Read JSON file
Write-Host "📖 Reading JSON file..." -ForegroundColor Yellow
$jsonContent = Get-Content $jsonFilePath -Raw

# Validate JSON
try {
    $json = $jsonContent | ConvertFrom-Json
    Write-Host "✅ JSON is valid!" -ForegroundColor Green
    Write-Host "   Project ID: $($json.project_id)" -ForegroundColor Cyan
    Write-Host "   Client Email: $($json.client_email)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Invalid JSON format!" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""
Write-Host "📋 Adding GOOGLE_CLOUD_PROJECT..." -ForegroundColor Yellow

# Add GOOGLE_CLOUD_PROJECT
$projectId = $json.project_id
Write-Host "   Value: $projectId" -ForegroundColor Cyan

# Note: Vercel CLI doesn't support interactive input for multiline JSON easily
# So we'll provide instructions instead
Write-Host ""
Write-Host "⚠️  Vercel CLI में multiline JSON add करना tricky है" -ForegroundColor Yellow
Write-Host "   इसलिए Dashboard से manually add करना better है" -ForegroundColor Yellow
Write-Host ""
Write-Host "📝 Manual Steps:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Go to: https://vercel.com/apnaonlineservics-projects/doc-tools/settings/environment-variables" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Add GOOGLE_CLOUD_PROJECT:" -ForegroundColor Yellow
Write-Host "   Key: GOOGLE_CLOUD_PROJECT" -ForegroundColor White
Write-Host "   Value: $projectId" -ForegroundColor White
Write-Host "   Environments: Production, Preview, Development" -ForegroundColor White
Write-Host ""
Write-Host "3. Add GOOGLE_CLOUD_SERVICE_ACCOUNT:" -ForegroundColor Yellow
Write-Host "   Key: GOOGLE_CLOUD_SERVICE_ACCOUNT" -ForegroundColor White
Write-Host "   Value: (Paste complete JSON from file below)" -ForegroundColor White
Write-Host "   Environments: Production, Preview, Development" -ForegroundColor White
Write-Host ""
Write-Host "4. JSON Content (copy this):" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host $jsonContent -ForegroundColor White
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""
Write-Host "5. After adding, run: vercel --prod" -ForegroundColor Cyan
Write-Host ""

# Save JSON to a temp file for easy copy
$tempJsonFile = "temp-vercel-env-json.txt"
$jsonContent | Out-File -FilePath $tempJsonFile -Encoding UTF8
Write-Host "💾 JSON content saved to: $tempJsonFile" -ForegroundColor Green
Write-Host "   (You can open this file and copy the content)" -ForegroundColor Gray
Write-Host ""

