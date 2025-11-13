# Deployment script for Google Cloud Run
# Run this after setting up gcloud CLI

# Set your project ID
PROJECT_ID="your-project-id"
SERVICE_NAME="bg-remover-api"
REGION="us-central1"

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --allow-unauthenticated
