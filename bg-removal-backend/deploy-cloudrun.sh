#!/bin/bash

# Deployment script for Background Removal Service to Google Cloud Run
# Usage: ./deploy-cloudrun.sh [PROJECT_ID] [REGION]

set -e

PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}
SERVICE_NAME="bg-removal-birefnet"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Background Removal Service to Google Cloud Run"
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

# Deploy to Cloud Run with GPU (Upgraded Configuration)
echo "🚀 Deploying to Cloud Run with High-Performance GPU..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 8Gi \
  --cpu 4 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10 \
  --add-gpu type=nvidia-l4 \
  --gpu-count 1 \
  --concurrency 5 \
  --port 8080

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Update your Vercel environment variable:"
echo "CLOUDRUN_API_URL_BG_REMOVAL=${SERVICE_URL}"

