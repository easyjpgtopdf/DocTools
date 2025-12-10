#!/bin/bash
# Deployment script for Google Cloud Run

set -e

PROJECT_ID=${PROJECT_ID:-"easyjpgtopdf-de346"}
SERVICE_NAME=${SERVICE_NAME:-"pdf-to-word-converter"}
REGION=${REGION:-"us-central1"}

echo "Building Docker image..."
docker build -t gcr.io/${PROJECT_ID}/${SERVICE_NAME} ./backend

echo "Pushing to Container Registry..."
docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}

echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 540 \
  --set-env-vars PROJECT_ID=${PROJECT_ID}

echo "Deployment complete!"

