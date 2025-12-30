# Quick deployment script for block extraction fix

Write-Host "Step 1: Committing changes..." -ForegroundColor Yellow
cd C:\Users\apnao\Downloads\DocTools
git add pdf-to-excel-backend/premium_layout/layout_decision_engine.py
git commit -m "FIX: Ensure blocks always extracted - prevent empty layouts"
git push

Write-Host "Step 2: Building Docker image..." -ForegroundColor Yellow
cd C:\Users\apnao\Downloads\DocTools\pdf-to-excel-backend
gcloud builds submit --tag gcr.io/easyjpgtopdf-de346/pdf-to-excel-backend --project easyjpgtopdf-de346

Write-Host "Step 3: Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy pdf-to-excel-backend --image gcr.io/easyjpgtopdf-de346/pdf-to-excel-backend:latest --platform managed --region us-central1 --allow-unauthenticated --project easyjpgtopdf-de346 --memory 1Gi --cpu 1 --timeout 300

Write-Host "Step 4: Testing single PDF..." -ForegroundColor Yellow
cd C:\Users\apnao\Downloads\DocTools
python manual_test_single_pdf.py

Write-Host "✅ Deployment complete! Check results above." -ForegroundColor Green


