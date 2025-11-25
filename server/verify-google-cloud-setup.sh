#!/bin/bash
# Verify Google Cloud Setup for EasyJpgtoPdf Project
# Checks if all services are properly configured

PROJECT_ID="easyjpgtopdf-de346"
PROJECT_NUMBER="564572183797"
SERVICE_ACCOUNT_NAME="pdf-editor-service"
VISION_API="vision.googleapis.com"

echo "🔍 Verifying Google Cloud Setup..."
echo "📦 Project ID: $PROJECT_ID"
echo "🔢 Project Number: $PROJECT_NUMBER"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found!"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID > /dev/null 2>&1

echo "1️⃣ Checking Vision API Status..."
VISION_STATUS=$(gcloud services list --enabled --project=$PROJECT_ID --filter="name:$VISION_API" --format="value(name)" 2>/dev/null)
if [ "$VISION_STATUS" = "$VISION_API" ]; then
    echo "   ✅ Vision API ($VISION_API): ENABLED"
else
    echo "   ❌ Vision API ($VISION_API): NOT ENABLED"
    echo "   💡 Run: gcloud services enable $VISION_API --project=$PROJECT_ID"
fi
echo ""

echo "2️⃣ Checking Other Required APIs..."
APIS=(
    "language.googleapis.com"
    "storage-component.googleapis.com"
    "datastore.googleapis.com"
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "firebase.googleapis.com"
)

for API in "${APIS[@]}"; do
    API_STATUS=$(gcloud services list --enabled --project=$PROJECT_ID --filter="name:$API" --format="value(name)" 2>/dev/null)
    if [ "$API_STATUS" = "$API" ]; then
        echo "   ✅ $API: ENABLED"
    else
        echo "   ❌ $API: NOT ENABLED"
    fi
done
echo ""

echo "3️⃣ Checking Service Account..."
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
if gcloud iam service-accounts describe $SERVICE_ACCOUNT --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "   ✅ Service Account ($SERVICE_ACCOUNT): EXISTS"
    
    # Check permissions
    echo "   📋 Checking permissions..."
    ROLES=("roles/vision.admin" "roles/storage.admin" "roles/run.admin")
    for ROLE in "${ROLES[@]}"; do
        if gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT} AND bindings.role:$ROLE" --format="value(bindings.role)" 2>/dev/null | grep -q "$ROLE"; then
            echo "      ✅ $ROLE: GRANTED"
        else
            echo "      ❌ $ROLE: NOT GRANTED"
        fi
    done
else
    echo "   ❌ Service Account ($SERVICE_ACCOUNT): NOT FOUND"
    echo "   💡 Run: ./setup-google-cloud.sh"
fi
echo ""

echo "4️⃣ Checking Storage Bucket..."
BUCKET_NAME="pdf-editor-storage"
if gsutil ls -b gs://${BUCKET_NAME} > /dev/null 2>&1; then
    echo "   ✅ Storage Bucket (gs://${BUCKET_NAME}): EXISTS"
else
    echo "   ❌ Storage Bucket (gs://${BUCKET_NAME}): NOT FOUND"
    echo "   💡 Run: gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://${BUCKET_NAME}"
fi
echo ""

echo "5️⃣ Checking Service Account Key..."
KEY_FILE="service-account-key.json"
if [ -f "$KEY_FILE" ]; then
    echo "   ✅ Service Account Key ($KEY_FILE): EXISTS"
    
    # Validate JSON
    if python3 -m json.tool "$KEY_FILE" > /dev/null 2>&1 || python -m json.tool "$KEY_FILE" > /dev/null 2>&1; then
        echo "      ✅ JSON format: VALID"
        
        # Check if it contains required fields
        if grep -q "project_id" "$KEY_FILE" && grep -q "private_key" "$KEY_FILE"; then
            echo "      ✅ Required fields: PRESENT"
        else
            echo "      ⚠️  Required fields: MISSING"
        fi
    else
        echo "      ❌ JSON format: INVALID"
    fi
else
    echo "   ❌ Service Account Key ($KEY_FILE): NOT FOUND"
    echo "   💡 Run: gcloud iam service-accounts keys create $KEY_FILE --iam-account=$SERVICE_ACCOUNT --project=$PROJECT_ID"
fi
echo ""

echo "6️⃣ Checking Environment Variables..."
if [ -f ".env" ]; then
    echo "   ✅ .env file: EXISTS"
    if grep -q "GOOGLE_CLOUD_PROJECT" .env && grep -q "GOOGLE_CLOUD_SERVICE_ACCOUNT" .env; then
        echo "      ✅ Required variables: PRESENT"
    else
        echo "      ⚠️  Required variables: MISSING"
    fi
else
    echo "   ⚠️  .env file: NOT FOUND (optional for local development)"
fi
echo ""

echo "=========================================="
echo "📊 Summary"
echo "=========================================="
echo ""
echo "✅ Setup Complete: All checks passed"
echo "❌ Setup Incomplete: Some checks failed"
echo ""
echo "💡 To fix issues, run: ./setup-google-cloud.sh"
echo ""

