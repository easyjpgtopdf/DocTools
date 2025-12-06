#!/bin/bash
# Complete Deployment Script for PDF Editor
# Deploys backend to Cloud Run and frontend to Vercel

set -e  # Exit on error

echo "🚀 Starting Complete Deployment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if required tools are installed
command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}Error: gcloud CLI not installed${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: Docker not installed${NC}"; exit 1; }
command -v vercel >/dev/null 2>&1 || { echo -e "${RED}Error: Vercel CLI not installed. Install with: npm i -g vercel${NC}"; exit 1; }

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
SERVICE_NAME="pdf-editor-service"
REGION="${GCP_REGION:-us-central1}"
BACKEND_URL="https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app"

echo -e "${BLUE}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Service Name: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  Backend URL: $BACKEND_URL"
echo ""

# Step 1: Deploy Backend to Cloud Run
echo -e "${GREEN}Step 1: Deploying Backend to Cloud Run...${NC}"
cd pdf-editor-backend

# Build Docker image
echo "Building Docker image..."
docker build -t gcr.io/${PROJECT_ID}/${SERVICE_NAME} .

# Push to Google Container Registry
echo "Pushing to Google Container Registry..."
docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
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

echo -e "${GREEN}✅ Backend deployed successfully!${NC}"
echo "Backend URL: $BACKEND_URL"
echo ""

# Step 2: Update Frontend Configuration
echo -e "${GREEN}Step 2: Updating Frontend Configuration...${NC}"
cd ..

# Update backend URL in API client
if [ -f "js/pdf-editor-api.js" ]; then
    # Create backup
    cp js/pdf-editor-api.js js/pdf-editor-api.js.bak
    
    # Update backend URL (simple sed replacement)
    sed -i.bak "s|https://pdf-editor-service-YOUR_PROJECT_ID.a.run.app|${BACKEND_URL}|g" js/pdf-editor-api.js
    echo "Updated backend URL in js/pdf-editor-api.js"
fi

# Step 3: Deploy Frontend to Vercel
echo -e "${GREEN}Step 3: Deploying Frontend to Vercel...${NC}"

# Set environment variable
echo "Setting Vercel environment variable..."
vercel env add PDF_EDITOR_BACKEND_URL production <<EOF
${BACKEND_URL}
EOF

# Deploy
echo "Deploying to Vercel..."
vercel --prod --yes

echo -e "${GREEN}✅ Frontend deployed successfully!${NC}"
echo ""

# Step 4: Health Check
echo -e "${GREEN}Step 4: Verifying Deployment...${NC}"
sleep 5  # Wait for deployment to propagate

# Check backend health
echo "Checking backend health..."
HEALTH_RESPONSE=$(curl -s https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app/health || echo "FAILED")

if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo -e "${GREEN}✅ Backend is healthy!${NC}"
else
    echo -e "${RED}⚠️  Backend health check failed${NC}"
fi

# Step 5: Git Commit (if in git repo)
if [ -d ".git" ]; then
    echo -e "${GREEN}Step 5: Committing changes to Git...${NC}"
    git add .
    git commit -m "Deploy PDF editor with 5 pages/day limit and device tracking" || echo "No changes to commit"
    git push origin main || echo "Git push skipped"
fi

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "Next Steps:"
echo "1. Test the PDF editor at: https://easyjpgtopdf.com/pdf-editor-preview.html"
echo "2. Verify daily limit tracking"
echo "3. Test credit deduction"
echo "4. Monitor Cloud Run logs: gcloud run services logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Frontend: https://easyjpgtopdf.com/pdf-editor-preview.html"

