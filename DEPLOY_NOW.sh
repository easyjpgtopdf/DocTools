#!/bin/bash
# Quick Deployment Script for PDF Editor
# Run this script to deploy backend and frontend

set -e

echo "🚀 PDF Editor Deployment Script"
echo ""

# Step 1: Get Project ID
read -p "Enter your Google Cloud Project ID: " PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Project ID is required!"
    exit 1
fi

read -p "Enter region (default: us-central1): " REGION
REGION=${REGION:-us-central1}

SERVICE_NAME="pdf-editor-service"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo ""
echo "📋 Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo ""

# Step 2: Check prerequisites
echo "🔍 Checking prerequisites..."

command -v gcloud >/dev/null 2>&1 && echo "  ✅ gcloud installed" || echo "  ❌ gcloud not found"
command -v docker >/dev/null 2>&1 && echo "  ✅ docker installed" || echo "  ❌ docker not found"
command -v vercel >/dev/null 2>&1 && echo "  ✅ vercel installed" || echo "  ❌ vercel not found"

echo ""

# Step 3: Deploy Backend
read -p "Deploy backend to Cloud Run? (Y/n): " deploy_backend
if [ "$deploy_backend" != "n" ] && [ "$deploy_backend" != "N" ]; then
    echo ""
    echo "📦 Building Docker image..."
    cd pdf-editor-backend
    
    docker build -t ${IMAGE_NAME} .
    
    echo "📤 Pushing to Google Container Registry..."
    docker push ${IMAGE_NAME}
    
    echo "🚀 Deploying to Cloud Run..."
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
    
    cd ..
    echo "✅ Backend deployed successfully!"
    BACKEND_URL="https://${SERVICE_NAME}-${PROJECT_ID}.a.run.app"
    echo "   Backend URL: $BACKEND_URL"
else
    read -p "Enter existing backend URL: " BACKEND_URL
fi

echo ""

# Step 4: Update Frontend
echo "📝 Updating frontend configuration..."

# Update backend URL in API client
if [ -f "js/pdf-editor-api.js" ]; then
    sed -i.bak "s|https://pdf-editor-service-YOUR_PROJECT_ID.a.run.app|${BACKEND_URL}|g" js/pdf-editor-api.js
    sed -i.bak "s|https://pdf-editor-service-.*\.a\.run\.app|${BACKEND_URL}|g" js/pdf-editor-api.js
    echo "✅ Updated backend URL in js/pdf-editor-api.js"
else
    echo "⚠️  js/pdf-editor-api.js not found, please update manually"
fi

echo ""

# Step 5: Deploy Frontend
read -p "Deploy frontend to Vercel? (Y/n): " deploy_frontend
if [ "$deploy_frontend" != "n" ] && [ "$deploy_frontend" != "N" ]; then
    echo ""
    echo "🌐 Setting Vercel environment variable..."
    echo "$BACKEND_URL" | vercel env add PDF_EDITOR_BACKEND_URL production
    
    echo "🚀 Deploying to Vercel..."
    vercel --prod --yes
    
    echo "✅ Frontend deployed successfully!"
fi

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📋 Summary:"
echo "  Backend URL: $BACKEND_URL"
echo "  Frontend: https://easyjpgtopdf.com/pdf-editor-preview.html"
echo ""
echo "🧪 Test your deployment:"
echo "  1. Open: https://easyjpgtopdf.com/pdf-editor-preview.html"
echo "  2. Upload a PDF"
echo "  3. Test add/edit/delete text"
echo "  4. Verify daily limit (5 pages)"
echo "  5. Test OCR and export"
echo ""
echo "📊 Monitor logs:"
echo "  gcloud run services logs read ${SERVICE_NAME} --region ${REGION}"
echo ""

