#!/bin/bash
# Complete Status Check Script
# Checks all Google Cloud services, Vercel, and application status

PROJECT_ID="easyjpgtopdf-de346"
SERVICE_ACCOUNT="pdf-editor-service@${PROJECT_ID}.iam.gserviceaccount.com"
BUCKET_NAME="pdf-editor-storage"

echo "🔍 Complete Status Check for EasyJpgtoPdf Project"
echo "=================================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found!"
    echo "📥 Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID > /dev/null 2>&1

echo "1️⃣ Google Cloud APIs Status:"
echo "----------------------------"
APIS=(
    "vision.googleapis.com"
    "language.googleapis.com"
    "storage-component.googleapis.com"
    "datastore.googleapis.com"
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "firebase.googleapis.com"
)

ALL_APIS_ENABLED=true
for API in "${APIS[@]}"; do
    STATUS=$(gcloud services list --enabled --project=$PROJECT_ID --filter="name:$API" --format="value(name)" 2>/dev/null)
    if [ "$STATUS" = "$API" ]; then
        echo "   ✅ $API"
    else
        echo "   ❌ $API - NOT ENABLED"
        ALL_APIS_ENABLED=false
    fi
done
echo ""

echo "2️⃣ Service Account Status:"
echo "--------------------------"
if gcloud iam service-accounts describe $SERVICE_ACCOUNT --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "   ✅ Service Account: $SERVICE_ACCOUNT EXISTS"
    
    echo ""
    echo "   📋 Checking Permissions:"
    ROLES=("roles/vision.admin" "roles/storage.admin" "roles/datastore.user" "roles/run.admin" "roles/firebase.admin")
    ALL_ROLES_GRANTED=true
    for ROLE in "${ROLES[@]}"; do
        if gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT} AND bindings.role:$ROLE" --format="value(bindings.role)" 2>/dev/null | grep -q "$ROLE"; then
            echo "      ✅ $ROLE"
        else
            echo "      ❌ $ROLE - NOT GRANTED"
            ALL_ROLES_GRANTED=false
        fi
    done
else
    echo "   ❌ Service Account: NOT FOUND"
    echo "   💡 Run: cd server && bash setup-google-cloud.sh"
fi
echo ""

echo "3️⃣ Storage Bucket Status:"
echo "------------------------"
if gsutil ls -b gs://${BUCKET_NAME} > /dev/null 2>&1; then
    echo "   ✅ Storage Bucket: gs://${BUCKET_NAME} EXISTS"
else
    echo "   ❌ Storage Bucket: NOT FOUND"
    echo "   💡 Run: gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://${BUCKET_NAME}"
fi
echo ""

echo "4️⃣ Service Account Key Status:"
echo "-------------------------------"
KEY_FILE="service-account-key.json"
if [ -f "$KEY_FILE" ]; then
    echo "   ✅ Key File: $KEY_FILE EXISTS"
    
    # Validate JSON
    if python3 -m json.tool "$KEY_FILE" > /dev/null 2>&1 || python -m json.tool "$KEY_FILE" > /dev/null 2>&1; then
        echo "      ✅ JSON format: VALID"
        
        # Check required fields
        if grep -q "project_id" "$KEY_FILE" && grep -q "private_key" "$KEY_FILE" && grep -q "client_email" "$KEY_FILE"; then
            echo "      ✅ Required fields: PRESENT"
        else
            echo "      ⚠️  Required fields: MISSING"
        fi
    else
        echo "      ❌ JSON format: INVALID"
    fi
else
    echo "   ❌ Key File: NOT FOUND"
    echo "   💡 Generate from: https://console.cloud.google.com/iam-admin/serviceaccounts?project=$PROJECT_ID"
fi
echo ""

echo "5️⃣ Local Server Status:"
echo "----------------------"
if [ -f "server/server.js" ]; then
    echo "   ✅ Server file: EXISTS"
    
    # Check if server is running
    if curl -s http://localhost:3000/api/cloud/status > /dev/null 2>&1; then
        echo "   ✅ Server: RUNNING on http://localhost:3000"
        
        # Check status endpoint
        STATUS_RESPONSE=$(curl -s http://localhost:3000/api/cloud/status)
        if [ ! -z "$STATUS_RESPONSE" ]; then
            echo "   ✅ Status endpoint: WORKING"
        else
            echo "   ⚠️  Status endpoint: NOT RESPONDING"
        fi
    else
        echo "   ⚠️  Server: NOT RUNNING"
        echo "   💡 Start with: cd server && npm start"
    fi
else
    echo "   ❌ Server file: NOT FOUND"
fi
echo ""

echo "6️⃣ Vercel Status:"
echo "----------------"
echo "   ℹ️  Manual Check Required:"
echo "   1. Go to: https://vercel.com/your-project"
echo "   2. Check 'Deployments' tab"
echo "   3. Check 'Settings' → 'Environment Variables'"
echo "   4. Verify these variables exist:"
echo "      - GOOGLE_CLOUD_PROJECT"
echo "      - GOOGLE_CLOUD_SERVICE_ACCOUNT"
echo "      - FIREBASE_SERVICE_ACCOUNT"
echo ""

echo "=================================================="
echo "📊 Summary"
echo "=================================================="
echo ""

if [ "$ALL_APIS_ENABLED" = true ] && [ "$ALL_ROLES_GRANTED" = true ]; then
    echo "✅ Google Cloud Setup: COMPLETE"
else
    echo "❌ Google Cloud Setup: INCOMPLETE"
    echo "   Run: cd server && bash setup-google-cloud.sh"
fi

echo ""
echo "📝 Next Steps:"
echo "1. Generate service account key (if not done)"
echo "2. Add environment variables to Vercel"
echo "3. Deploy to Vercel (if not done)"
echo "4. Test API endpoints"
echo ""

