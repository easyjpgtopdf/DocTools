#!/bin/bash

# PDF Editor Deployment Script
# Deploys both backend and frontend

set -e

echo "🚀 Starting PDF Editor Deployment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Deploy Backend to Cloud Run
echo -e "${BLUE}📦 Deploying Backend to Cloud Run...${NC}"
cd pdf-editor-backend

if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

echo "Deploying to Cloud Run..."
gcloud run deploy pdf-editor-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars="PYTHONUNBUFFERED=1" || {
    echo -e "${YELLOW}⚠️  Cloud Run deployment failed. Make sure you're authenticated with gcloud.${NC}"
    echo "You can deploy manually or skip this step."
}

cd ..

# 2. Deploy Frontend to Vercel
echo -e "${BLUE}🌐 Deploying Frontend to Vercel...${NC}"

if command -v vercel &> /dev/null; then
    vercel --prod || {
        echo -e "${YELLOW}⚠️  Vercel deployment failed. Make sure you're logged in.${NC}"
        echo "Run: vercel login"
    }
else
    echo -e "${YELLOW}⚠️  Vercel CLI not found. Install with: npm i -g vercel${NC}"
fi

# 3. Push to GitHub
echo -e "${BLUE}📤 Pushing to GitHub...${NC}"

if [ -d ".git" ]; then
    git add .
    git commit -m "feat: Deploy dual-layer PDF editor system" || echo "No changes to commit"
    git push origin main || {
        echo -e "${YELLOW}⚠️  Git push failed. Make sure you have a remote configured.${NC}"
    }
else
    echo -e "${YELLOW}⚠️  Not a git repository. Initialize with: git init${NC}"
fi

echo -e "${GREEN}✅ Deployment process completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Update PDF_EDITOR_BACKEND_URL in Vercel environment variables"
echo "2. Test the deployed application"
echo "3. Monitor Cloud Run logs for any issues"

