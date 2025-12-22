# MongoDB URI Update Script
# Is script ko run karein jab aapko MongoDB Atlas se correct connection string mil jaye

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MongoDB Connection String Update Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get connection string from user
Write-Host "Step 1: MongoDB Atlas se connection string copy karein" -ForegroundColor Yellow
Write-Host "1. https://cloud.mongodb.com/ par login karein" -ForegroundColor White
Write-Host "2. Database > Connect > Connect your application" -ForegroundColor White
Write-Host "3. Node.js driver select karein" -ForegroundColor White
Write-Host "4. Connection string copy karein" -ForegroundColor White
Write-Host ""

$connectionString = Read-Host "MongoDB Connection String yahan paste karein"

if ([string]::IsNullOrWhiteSpace($connectionString)) {
    Write-Host "❌ Connection string required!" -ForegroundColor Red
    exit 1
}

# Validate connection string format
if (-not ($connectionString -match "^mongodb\+srv://")) {
    Write-Host "⚠️ Warning: Connection string mongodb+srv:// se start hona chahiye" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Step 2: Update Cloud Run
Write-Host ""
Write-Host "Step 2: Cloud Run mein update kar raha hoon..." -ForegroundColor Yellow
Write-Host ""

try {
    $result = gcloud run services update pdf-to-word-converter `
        --region us-central1 `
        --update-env-vars "MONGODB_URI=$connectionString" `
        2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Success! MongoDB URI update ho gaya!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Step 3: Connection test kar raha hoon..." -ForegroundColor Yellow
        Write-Host ""
        
        # Wait for deployment
        Start-Sleep -Seconds 15
        
        # Check logs
        Write-Host "Recent logs check kar raha hoon..." -ForegroundColor Cyan
        $logs = gcloud run services logs read pdf-to-word-converter --region us-central1 --limit 10 2>&1
        
        if ($logs -match "MongoDB connected successfully") {
            Write-Host "✅ MongoDB connection successful!" -ForegroundColor Green
        } elseif ($logs -match "ENOTFOUND") {
            Write-Host "❌ DNS Error: Cluster name galat hai" -ForegroundColor Red
            Write-Host "💡 MongoDB Atlas dashboard se cluster name verify karein" -ForegroundColor Yellow
        } elseif ($logs -match "authentication") {
            Write-Host "❌ Authentication Error: Username/password galat hai" -ForegroundColor Red
            Write-Host "💡 MongoDB Atlas dashboard se username/password verify karein" -ForegroundColor Yellow
        } else {
            Write-Host "⚠️ Connection status unclear. Logs check karein:" -ForegroundColor Yellow
            Write-Host $logs
        }
        
    } else {
        Write-Host "❌ Error updating Cloud Run:" -ForegroundColor Red
        Write-Host $result
        exit 1
    }
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Done! Server logs check karne ke liye:" -ForegroundColor Cyan
Write-Host "gcloud run services logs read pdf-to-word-converter --region us-central1 --limit 20" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan

