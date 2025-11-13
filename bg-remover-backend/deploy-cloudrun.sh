#!/bin/bash
# Google Cloud Run Deployment Script
# For 100% Professional Quality Background Removal

# Configuration
PROJECT_ID="doctools-bg-remover"
SERVICE_NAME="bg-remover-api"
REGION="us-central1"

echo "🚀 Starting deployment to Google Cloud Run..."
echo "📦 Project: $PROJECT_ID"
echo "🎯 Service: $SERVICE_NAME"
echo "🌍 Region: $REGION"
echo ""

# Build Docker image
echo "🏗️ Building Docker image (8-12 minutes)..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .

if [ $? -eq 0 ]; then
  echo "✅ Build successful!"
else
  echo "❌ Build failed. Check logs above."
  exit 1
fi

echo ""
echo "🚀 Deploying to Cloud Run..."

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --allow-unauthenticated \
  --quiet

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Deployment successful!"
  echo ""
  echo "🔗 Service URL:"
  gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
  echo ""
  echo "📊 Next steps:"
  echo "1. Copy the URL above"
  echo "2. Update CLOUDRUN_API_URL in background-workspace.html"
  echo "3. Test with your 230 KB image"
  echo ""
  echo "🎉 100% Professional quality - No over-cleaning!"
else
  echo "❌ Deployment failed. Check logs above."
  exit 1
fi
