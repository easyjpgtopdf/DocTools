#!/bin/bash
# Google Cloud Setup Script for EasyJpgtoPdf Project
# Project ID: easyjpgtopdf-de346
# Project Number: 564572183797

PROJECT_ID="easyjpgtopdf-de346"
PROJECT_NUMBER="564572183797"
SERVICE_ACCOUNT_NAME="pdf-editor-service"
REGION="us-central1"
BUCKET_NAME="pdf-editor-storage"

echo "🚀 Starting Google Cloud Setup for EasyJpgtoPdf..."
echo "📦 Project ID: $PROJECT_ID"
echo "🔢 Project Number: $PROJECT_NUMBER"
echo "🌍 Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found!"
    echo "📥 Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
echo "🔐 Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "⚠️ Not authenticated. Running gcloud auth login..."
    gcloud auth login
fi

# Set project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Verify project
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "❌ Failed to set project. Please check your permissions."
    exit 1
fi

echo "✅ Project set to: $CURRENT_PROJECT"
echo ""

# Enable APIs
echo "🔌 Enabling required APIs..."
echo "   Enabling Vision API (vision.googleapis.com)..."
gcloud services enable vision.googleapis.com --project=$PROJECT_ID
echo "   Enabling Language API (language.googleapis.com)..."
gcloud services enable language.googleapis.com --project=$PROJECT_ID
echo "   Enabling Storage API..."
gcloud services enable storage-component.googleapis.com --project=$PROJECT_ID
echo "   Enabling Cloud Run API..."
gcloud services enable run.googleapis.com --project=$PROJECT_ID
echo "   Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
echo "   Enabling Firebase API..."
gcloud services enable firebase.googleapis.com --project=$PROJECT_ID

echo "✅ All APIs enabled"
echo ""

# Create service account
echo "👤 Creating service account..."
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com --project=$PROJECT_ID &>/dev/null; then
    echo "⚠️ Service account already exists, skipping creation..."
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="PDF Editor Service Account" \
        --description="Service account for PDF Editor with Cloud Vision, Storage, and Cloud Run access" \
        --project=$PROJECT_ID
    echo "✅ Service account created"
fi
echo ""

# Grant permissions
echo "🔑 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/vision.admin" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.admin" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.admin" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/firebase.admin" \
    --condition=None

echo "✅ Permissions granted"
echo ""

# Create storage bucket
echo "🪣 Creating Cloud Storage bucket..."
if gsutil ls -b gs://${BUCKET_NAME} &>/dev/null; then
    echo "⚠️ Bucket already exists, skipping creation..."
    echo "   Bucket: gs://${BUCKET_NAME}"
else
    echo "   Creating bucket: gs://${BUCKET_NAME}"
    gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://${BUCKET_NAME}
    if [ $? -eq 0 ]; then
        echo "✅ Bucket created: gs://${BUCKET_NAME}"
        echo "   Storage API: storage-component.googleapis.com"
        echo "   Region: $REGION"
    else
        echo "❌ Failed to create bucket. Check Storage API is enabled."
    fi
fi
echo ""

# Create service account key
echo "🔐 Creating service account key..."
KEY_FILE="service-account-key.json"
if [ -f "$KEY_FILE" ]; then
    echo "⚠️ Key file already exists. Backing up to ${KEY_FILE}.backup..."
    mv "$KEY_FILE" "${KEY_FILE}.backup"
fi

gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com \
    --project=$PROJECT_ID

if [ -f "$KEY_FILE" ]; then
    echo "✅ Service account key created: $KEY_FILE"
    echo ""
    echo "📋 IMPORTANT: Copy the content of $KEY_FILE to your environment variables:"
    echo "   - GOOGLE_CLOUD_SERVICE_ACCOUNT"
    echo "   - FIREBASE_SERVICE_ACCOUNT (can be same)"
    echo ""
    echo "⚠️  NEVER commit this file to Git!"
else
    echo "❌ Failed to create service account key"
    exit 1
fi

# Display summary
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Project Information:"
echo "  Project ID: $PROJECT_ID"
echo "  Project Number: $PROJECT_NUMBER"
echo "  Service Account: ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "  Storage Bucket: gs://${BUCKET_NAME}"
echo "  Region: $REGION"
echo ""
echo "Next Steps:"
echo "1. Copy content of $KEY_FILE to Vercel environment variables"
echo "2. Set GOOGLE_CLOUD_PROJECT=$PROJECT_ID in environment variables"
echo "3. Deploy to Cloud Run: cd server && ./deploy-cloudrun.sh"
echo ""
echo "To verify setup:"
echo "  gcloud services list --enabled --project=$PROJECT_ID"
echo "  gcloud iam service-accounts list --project=$PROJECT_ID"
echo "  gsutil ls gs://${BUCKET_NAME}"
echo ""

