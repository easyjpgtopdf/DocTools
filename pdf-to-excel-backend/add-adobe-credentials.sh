#!/bin/bash
# Adobe PDF Extract API Credentials Setup Script (Linux/Mac)
# Run this script to add Adobe credentials to Google Cloud Run
# 
# Usage:
#   chmod +x add-adobe-credentials.sh
#   ./add-adobe-credentials.sh

echo "============================================================"
echo "Adobe PDF Extract API - Credentials Setup"
echo "============================================================"
echo ""

# Check if user has credentials
echo "Do you have Adobe PDF Extract API credentials?"
echo "Get them from: https://developer.adobe.com/console"
echo ""

# Prompt for credentials
read -p "Enter your Adobe Client ID: " ADOBE_CLIENT_ID
read -sp "Enter your Adobe Client Secret (will be hidden): " ADOBE_CLIENT_SECRET
echo ""

# Validate inputs
if [ -z "$ADOBE_CLIENT_ID" ]; then
    echo "ERROR: Adobe Client ID cannot be empty!"
    exit 1
fi

if [ -z "$ADOBE_CLIENT_SECRET" ]; then
    echo "ERROR: Adobe Client Secret cannot be empty!"
    exit 1
fi

echo ""
echo "============================================================"
echo "Adding credentials to Google Cloud Run..."
echo "============================================================"
echo ""

# Cloud Run service details
PROJECT_ID="easyjpgtopdf-de346"
SERVICE_NAME="pdf-to-excel-backend"
REGION="us-central1"

# Add environment variables to Cloud Run
echo "Running: gcloud run services update $SERVICE_NAME..."

gcloud run services update $SERVICE_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --update-env-vars="ADOBE_CLIENT_ID=$ADOBE_CLIENT_ID,ADOBE_CLIENT_SECRET=$ADOBE_CLIENT_SECRET" \
    --quiet

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ SUCCESS: Adobe credentials added to Cloud Run!"
    echo "============================================================"
    echo ""
    echo "Adobe fallback is now ACTIVE and will trigger for:"
    echo "  - Documents with Document AI confidence < 0.65"
    echo "  - Complex PDFs (merged cells, mixed content)"
    echo "  - Premium plan users"
    echo ""
    echo "Monitor logs for: 'ADOBE FALLBACK: Triggered'"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "❌ ERROR: Failed to add credentials"
    echo "============================================================"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check if you're logged in: gcloud auth list"
    echo "2. Check project: gcloud config get-value project"
    echo "3. Log in if needed: gcloud auth login"
    echo "4. Set project: gcloud config set project $PROJECT_ID"
    exit 1
fi

echo "Verifying deployment..."
echo ""

# Get current service configuration
gcloud run services describe $SERVICE_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --format="value(spec.template.spec.containers[0].env)" \
    | grep ADOBE

echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Next Steps:"
echo "1. Test with a complex PDF at:"
echo "   https://www.easyjpgtopdf.com/pdf-to-excel-premium.html"
echo ""
echo "2. Check logs for Adobe fallback:"
echo "   gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND textPayload=~\"ADOBE\"' --limit=50 --project=$PROJECT_ID"
echo ""

