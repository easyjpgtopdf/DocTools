#!/bin/bash
# Deploy PDF Editor Service to Google Cloud Run
# CPU only, minimum instances 0 (no monthly bill when idle)

PROJECT_ID="easyjpgtopdf-de346"
SERVICE_NAME="pdf-editor-service"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Building Docker image..."
docker build -t ${IMAGE_NAME} .

echo "Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}

echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 2Gi \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --concurrency 80 \
  --set-env-vars API_BASE_URL=https://easyjpgtopdf.com

echo "Deployment complete!"
echo "Service URL: https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app"

