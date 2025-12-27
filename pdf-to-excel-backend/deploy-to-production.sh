#!/bin/bash
# Production Deployment Script for PDF to Excel Backend with Adobe Integration
# Run this after critical Adobe API fix

set -e  # Exit on error

echo "======================================================================"
echo "🚀 DEPLOYING PDF TO EXCEL BACKEND TO PRODUCTION"
echo "======================================================================"

# Configuration
PROJECT_ID="easyjpgtopdf-de346"
SERVICE_NAME="pdf-backend"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}📋 Pre-Deployment Checklist${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. ✅ Adobe API fix committed and pushed"
echo "2. ✅ Adobe credentials configured in Cloud Run"
echo "3. ⏳ Ready to deploy..."
echo ""

# Prompt for confirmation
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🔨 Step 1: Building Docker image...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
gcloud builds submit --tag ${IMAGE_NAME} --project=${PROJECT_ID}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🚢 Step 2: Deploying to Cloud Run...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300s \
  --max-instances 10 \
  --set-env-vars="ADOBE_ENABLED=true,QA_VALIDATION_ENABLED=true,DETAILED_COST_LOGGING=true,AUDIT_TRAIL_ENABLED=true"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment successful${NC}"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🔍 Step 3: Verifying deployment...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(status.url)')

echo "Service URL: ${SERVICE_URL}"

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "${SERVICE_URL}/health" || echo "FAILED")

if [[ $HEALTH_RESPONSE == *"healthy"* ]] || [[ $HEALTH_RESPONSE == *"ok"* ]]; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Health check response: ${HEALTH_RESPONSE}${NC}"
fi

echo ""
echo -e "${GREEN}📊 Step 4: Checking environment variables...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Adobe credentials are set (without showing values)
ENV_VARS=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format 'value(spec.template.spec.containers[0].env)')

if [[ $ENV_VARS == *"ADOBE_CLIENT_ID"* ]]; then
    echo -e "${GREEN}✅ ADOBE_CLIENT_ID is set${NC}"
else
    echo -e "${RED}❌ ADOBE_CLIENT_ID is NOT set${NC}"
fi

if [[ $ENV_VARS == *"ADOBE_CLIENT_SECRET"* ]]; then
    echo -e "${GREEN}✅ ADOBE_CLIENT_SECRET is set${NC}"
else
    echo -e "${RED}❌ ADOBE_CLIENT_SECRET is NOT set${NC}"
fi

if [[ $ENV_VARS == *"ADOBE_ENABLED=true"* ]]; then
    echo -e "${GREEN}✅ ADOBE_ENABLED=true${NC}"
else
    echo -e "${YELLOW}⚠️  ADOBE_ENABLED may not be true${NC}"
fi

echo ""
echo -e "${GREEN}📝 Step 5: Checking recent logs...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Fetching last 10 log entries..."
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" \
  --limit 10 \
  --project ${PROJECT_ID} \
  --format "table(timestamp,severity,textPayload)" || echo "Could not fetch logs"

echo ""
echo "======================================================================"
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo "======================================================================"
echo ""
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Next Steps:"
echo "1. Test with invoice PDF: ${SERVICE_URL}/api/pdf-to-excel-docai"
echo "2. Enable premium toggle in frontend"
echo "3. Check Cloud Logging for Adobe API calls"
echo "4. Monitor costs in Adobe Developer Console"
echo ""
echo "Emergency Disable Adobe:"
echo "  gcloud run services update ${SERVICE_NAME} --set-env-vars='ADOBE_ENABLED=false' --region ${REGION}"
echo ""
echo "View Logs:"
echo "  gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}\" --limit 50"
echo ""
echo "======================================================================"

