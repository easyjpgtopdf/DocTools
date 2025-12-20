#!/bin/bash

# Quick Deployment Script for Background Removal Service
# Usage: ./DEPLOY_NOW.sh [PROJECT_ID] [REGION]

set -e

PROJECT_ID=${1:-"YOUR_PROJECT_ID"}
REGION=${2:-"us-central1"}
SERVICE_NAME="bg-removal-birefnet"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting Cloud Run Deployment..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check if PROJECT_ID is set
if [ "$PROJECT_ID" == "YOUR_PROJECT_ID" ]; then
    echo "❌ ERROR: Please provide your Google Cloud Project ID"
    echo "Usage: ./DEPLOY_NOW.sh YOUR_PROJECT_ID us-central1"
    exit 1
fi

# Set project
echo "📋 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Build Docker image
echo ""
echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Push to Google Container Registry
echo ""
echo "📤 Pushing image to GCR..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run with GPU (512px processing + 16Gi/4 CPU as per user requirement)
echo ""
echo "🚀 Deploying to Cloud Run with Configuration (512px processing, 16Gi/4 CPU)..."
echo "📊 Configuration: Memory=16Gi, CPU=4, GPU=1xL4, Process=512px"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 16Gi \
  --cpu 4 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 3 \
  --gpu=1 \
  --gpu-type=nvidia-l4 \
  --no-gpu-zonal-redundancy \
  --concurrency 1 \
  --port 8080

# Get service URL
echo ""
echo "📡 Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Service URL: ${SERVICE_URL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Next Steps:"
echo "1. Copy the Service URL above"
echo "2. Go to Vercel Dashboard → Settings → Environment Variables"
echo "3. Update CLOUDRUN_API_URL_BG_REMOVAL with: ${SERVICE_URL}"
echo "4. Redeploy Vercel frontend (if needed)"
echo ""
echo "🧪 Test endpoint:"
echo "curl -X POST ${SERVICE_URL}/health"
echo ""

