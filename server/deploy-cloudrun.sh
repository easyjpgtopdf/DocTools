#!/bin/bash
# Google Cloud Run Deployment Script for PDF Editor Server
# Deploys main server with all PDF editing features

# Configuration
PROJECT_ID="easyjpgtopdf-de346"
SERVICE_NAME="pdf-editor-server"
REGION="us-central1"

echo "🚀 Starting deployment to Google Cloud Run..."
echo "📦 Project: $PROJECT_ID"
echo "🎯 Service: $SERVICE_NAME"
echo "🌍 Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found!"
    echo "📥 Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
echo "🔐 Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "⚠️ Not authenticated. Running gcloud auth login..."
    gcloud auth login
fi

# Set project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com vision.googleapis.com storage-component.googleapis.com

# Build Docker image
echo ""
echo "🏗️ Building Docker image..."
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
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --quiet

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Deployment successful!"
  echo ""
  echo "🔗 Service URL:"
  gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
  echo ""
  echo "📊 Next steps:"
  echo "1. Set environment variables in Cloud Run console:"
  echo "   - GOOGLE_CLOUD_SERVICE_ACCOUNT (for Vision API)"
  echo "   - FIREBASE_SERVICE_ACCOUNT (for Storage)"
  echo "2. Test the service URL"
  echo "3. Check status at: /api/cloud/status"
  echo ""
  echo "🎉 PDF Editor deployed to Cloud Run!"
else
  echo "❌ Deployment failed. Check logs above."
  exit 1
fi

