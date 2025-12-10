#!/bin/bash
# Deployment script for Google Cloud Run
# Project: easyjpgtopdf-de346

set -e

PROJECT_ID="easyjpgtopdf-de346"
SERVICE_NAME="pdf-to-word-converter"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "=== Deploying PDF to Word Converter to Cloud Run ==="
echo "Project ID: ${PROJECT_ID}"
echo "Service Name: ${SERVICE_NAME}"
echo "Region: ${REGION}"

# Set project
echo ""
echo "Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Build Docker image
echo ""
echo "Building Docker image..."
docker build -t ${IMAGE_NAME} ./backend

# Push to Container Registry
echo ""
echo "Pushing to Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo ""
echo "Deploying to Cloud Run..."

# Set environment variables (update these with your values)
ENV_VARS="PROJECT_ID=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},DOCAI_LOCATION=us"

# Check for required env vars or prompt
if [ -z "$GCS_OUTPUT_BUCKET" ]; then
    read -p "Enter GCS Output Bucket name: " GCS_OUTPUT_BUCKET
fi
ENV_VARS="${ENV_VARS},GCS_OUTPUT_BUCKET=${GCS_OUTPUT_BUCKET}"

if [ -z "$DOCAI_PROCESSOR_ID" ]; then
    read -p "Enter Document AI Processor ID (default: ffaa7bcd30a9c788): " DOCAI_PROCESSOR_ID
    DOCAI_PROCESSOR_ID=${DOCAI_PROCESSOR_ID:-ffaa7bcd30a9c788}
fi
ENV_VARS="${ENV_VARS},DOCAI_PROCESSOR_ID=${DOCAI_PROCESSOR_ID}"

if [ -n "$FIREBASE_PROJECT_ID" ]; then
    ENV_VARS="${ENV_VARS},FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}"
fi

gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 540 \
  --set-env-vars "${ENV_VARS}"

echo ""
echo "=== Deployment Complete! ==="
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)")
echo ""
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test the API:"
echo "curl -X POST \"${SERVICE_URL}/api/health\""

