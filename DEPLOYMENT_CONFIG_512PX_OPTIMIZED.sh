#!/bin/bash

# Deployment script for Background Removal Service to Google Cloud Run
# OPTIMIZED VERSION: 512px processing + Reduced Resources (8Gi, 2 CPU)
# Usage: ./DEPLOYMENT_CONFIG_512PX_OPTIMIZED.sh [PROJECT_ID] [REGION]

set -e

PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}
SERVICE_NAME="bg-removal-birefnet"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Background Removal Service to Google Cloud Run"
echo "📊 OPTIMIZED CONFIGURATION: 512px Processing + Reduced Resources"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"

# Set project
gcloud config set project ${PROJECT_ID}

# Build Docker image
echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Push to Google Container Registry
echo "📤 Pushing image to GCR..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run with OPTIMIZED configuration
echo "🚀 Deploying to Cloud Run with OPTIMIZED Configuration (512px + Reduced Resources)..."
echo "📊 Configuration:"
echo "   - Memory: 8Gi (reduced from 16Gi)"
echo "   - CPU: 2 vCPU (reduced from 4 vCPU)"
echo "   - GPU: 1x NVIDIA L4 (same)"
echo "   - Process Size: 512px (optimized)"
echo "   - Output Size: 512px (same)"

gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 8Gi \
  --cpu 2 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 3 \
  --gpu=1 \
  --gpu-type=nvidia-l4 \
  --no-gpu-zonal-redundancy \
  --concurrency 1 \
  --port 8080

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "📊 Expected Cost Savings:"
echo "   - 10,000 images: ~$6.78 (vs $13.58 with 768px + 16Gi/4CPU)"
echo "   - Savings: ~50% reduction"
echo ""
echo "Update your Vercel environment variable:"
echo "CLOUDRUN_API_URL_BG_REMOVAL=${SERVICE_URL}"

