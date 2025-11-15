# 🚀 Optimized Google Cloud Run Deployment Guide
## ₹0-50/Month Budget (Stay Within FREE Tier)

---

## 📋 **Services to Deploy (Optimized for FREE Tier)**

### **Priority 1: Essential Services (Deploy First)**

#### **1. Background Removal (U2Net RemBG)**
```bash
# Create Dockerfile
cat > Dockerfile.rembg << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    flask==2.3.0 \
    flask-cors==4.0.0 \
    rembg==2.0.50 \
    pillow==10.0.0 \
    gunicorn==21.2.0

# Copy app
COPY app.py .

# Expose port
EXPOSE 8080

# Run with Gunicorn
CMD exec gunicorn --bind :8080 --workers 1 --threads 2 --timeout 60 app:app
EOF

# Create app.py
cat > app.py << 'EOF'
from flask import Flask, request, send_file
from flask_cors import CORS
from rembg import remove
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

@app.route('/remove-background', methods=['POST'])
def remove_background():
    if 'image' not in request.files:
        return {'error': 'No image provided'}, 400
    
    file = request.files['image']
    input_image = Image.open(file.stream)
    
    # Remove background
    output_image = remove(input_image)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    output_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return send_file(img_byte_arr, mimetype='image/png')

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

# Deploy with OPTIMIZED settings for FREE tier
gcloud run deploy rembg-service \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60 \
    --min-instances 0 \
    --max-instances 5 \
    --concurrency 10 \
    --set-env-vars "U2NET_HOME=/tmp"
```

**FREE Tier Capacity:** 60,000 images/month ✅

---

#### **2. Face Detection (Cloud Vision API - No Deployment Needed)**
```javascript
// Use Google Cloud Vision API directly (Built-in service)
// 1,000 detections/month FREE

const CLOUD_VISION_API_KEY = 'YOUR_API_KEY'; // Optional, use OAuth instead

async function detectFacesWithVisionAPI(imageBlob) {
    const base64Image = await blobToBase64(imageBlob);
    
    const response = await fetch(
        `https://vision.googleapis.com/v1/images:annotate?key=${CLOUD_VISION_API_KEY}`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                requests: [{
                    image: { content: base64Image.split(',')[1] },
                    features: [{ type: 'FACE_DETECTION', maxResults: 10 }]
                }]
            })
        }
    );
    
    const result = await response.json();
    return result.responses[0].faceAnnotations || [];
}

function blobToBase64(blob) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.readAsDataURL(blob);
    });
}
```

**FREE Tier: 1,000 detections/month** ✅  
**Cost after free tier: $1.50/1,000 images**

---

#### **3. Face Blur (Lightweight Custom Service)**
```bash
# Dockerfile.faceblur
cat > Dockerfile.faceblur << 'EOF'
FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    flask==2.3.0 \
    flask-cors==4.0.0 \
    opencv-python-headless==4.8.0 \
    pillow==10.0.0 \
    numpy==1.24.0 \
    gunicorn==21.2.0

COPY app_blur.py app.py

EXPOSE 8080

CMD exec gunicorn --bind :8080 --workers 1 --threads 2 --timeout 30 app:app
EOF

# app_blur.py
cat > app_blur.py << 'EOF'
from flask import Flask, request, send_file
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

# Load face cascade (lightweight)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@app.route('/blur-faces', methods=['POST'])
def blur_faces():
    if 'image' not in request.files:
        return {'error': 'No image'}, 400
    
    # Read image
    file = request.files['image']
    img = Image.open(file.stream)
    img_array = np.array(img)
    
    # Convert to grayscale for detection
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    # Blur each face
    blur_strength = int(request.form.get('blur_strength', 25))
    for (x, y, w, h) in faces:
        # Extract face region
        face_region = img_array[y:y+h, x:x+w]
        
        # Apply Gaussian blur
        blurred_face = cv2.GaussianBlur(face_region, (blur_strength, blur_strength), 30)
        
        # Replace face with blurred version
        img_array[y:y+h, x:x+w] = blurred_face
    
    # Convert back to image
    result_img = Image.fromarray(img_array)
    
    # Return
    img_byte_arr = io.BytesIO()
    result_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return send_file(img_byte_arr, mimetype='image/png')

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

# Deploy with optimized settings
gcloud run deploy faceblur-service \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 30 \
    --min-instances 0 \
    --max-instances 5 \
    --concurrency 10
```

**FREE Tier Capacity:** 90,000 images/month ✅

---

#### **4. Perspective Correction (OpenCV Service)**
```bash
# Dockerfile.perspective
cat > Dockerfile.perspective << 'EOF'
FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    flask==2.3.0 \
    flask-cors==4.0.0 \
    opencv-python-headless==4.8.0 \
    pillow==10.0.0 \
    numpy==1.24.0 \
    gunicorn==21.2.0

COPY app_perspective.py app.py

EXPOSE 8080

CMD exec gunicorn --bind :8080 --workers 1 --threads 2 --timeout 30 app:app
EOF

# app_perspective.py
cat > app_perspective.py << 'EOF'
from flask import Flask, request, send_file
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    
    return warped

@app.route('/correct-perspective', methods=['POST'])
def correct_perspective():
    if 'image' not in request.files:
        return {'error': 'No image'}, 400
    
    # Read image
    file = request.files['image']
    img = Image.open(file.stream)
    img_array = np.array(img)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Edge detection
    edged = cv2.Canny(gray, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Get largest contour
        contour = max(contours, key=cv2.contourArea)
        
        # Approximate to rectangle
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        if len(approx) == 4:
            # Apply perspective transform
            warped = four_point_transform(img_array, approx.reshape(4, 2))
            result_img = Image.fromarray(warped)
        else:
            # Auto-rotate based on edges
            angle = calculate_skew_angle(gray)
            if abs(angle) > 0.5:
                result_img = rotate_image(img, angle)
            else:
                result_img = img
    else:
        result_img = img
    
    # Return result
    img_byte_arr = io.BytesIO()
    result_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return send_file(img_byte_arr, mimetype='image/png')

def calculate_skew_angle(image):
    coords = np.column_stack(np.where(image > 0))
    if len(coords) < 5:
        return 0
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    return angle

def rotate_image(image, angle):
    (h, w) = image.size[::-1]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(np.array(image), M, (w, h), 
                             flags=cv2.INTER_CUBIC, 
                             borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(rotated)

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

# Deploy
gcloud run deploy perspective-service \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 30 \
    --min-instances 0 \
    --max-instances 5
```

**FREE Tier Capacity:** 180,000 images/month ✅

---

### **Priority 2: Optional Services (Deploy if Needed)**

#### **5. Photo Repair (Lightweight Model - Optional)**
```bash
# Use lighter model to stay within free tier
# Only deploy if you need AI repair (local fallback works well)

cat > Dockerfile.repair << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Use smaller model
RUN pip install --no-cache-dir \
    flask==2.3.0 \
    flask-cors==4.0.0 \
    opencv-python-headless==4.8.0 \
    pillow==10.0.0 \
    scikit-image==0.21.0 \
    gunicorn==21.2.0

COPY app_repair.py app.py

EXPOSE 8080

CMD exec gunicorn --bind :8080 --workers 1 --threads 1 --timeout 60 app:app
EOF

# app_repair.py - Simple denoise + enhance
cat > app_repair.py << 'EOF'
from flask import Flask, request, send_file
from flask_cors import CORS
from skimage import restoration, exposure
from PIL import Image
import numpy as np
import io

app = Flask(__name__)
CORS(app)

@app.route('/repair', methods=['POST'])
def repair_photo():
    if 'image' not in request.files:
        return {'error': 'No image'}, 400
    
    file = request.files['image']
    img = Image.open(file.stream)
    img_array = np.array(img) / 255.0
    
    # Denoise
    denoised = restoration.denoise_nl_means(
        img_array,
        h=0.05,
        fast_mode=True,
        patch_size=5,
        patch_distance=6
    )
    
    # Enhance contrast
    enhanced = exposure.equalize_adapthist(denoised, clip_limit=0.03)
    
    # Convert back
    result = (enhanced * 255).astype(np.uint8)
    result_img = Image.fromarray(result)
    
    img_byte_arr = io.BytesIO()
    result_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return send_file(img_byte_arr, mimetype='image/png')

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

# Deploy (OPTIONAL - only if local repair not sufficient)
gcloud run deploy repair-service \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60 \
    --min-instances 0 \
    --max-instances 3
```

**Note:** Local photo repair works very well. Only deploy this if you need AI-powered repair.

---

## 💰 **Cost Breakdown - Optimized Configuration**

### **Monthly FREE Tier Allowance**
```
Cloud Run:
✅ 2,000,000 requests/month
✅ 360,000 GB-seconds/month
✅ 180,000 vCPU-seconds/month
✅ 1 GB network egress/month

Cloud Vision API (Face Detection):
✅ 1,000 face detections/month
```

### **Your Services - FREE Capacity**

| Service | Memory | Time/Image | Free Capacity | Your Usage | Cost |
|---------|--------|------------|---------------|------------|------|
| **RemBG** | 1GB | 3s | 60,000/mo | 500/mo | ₹0 |
| **Face Detect** | API | 0.5s | 1,000/mo | 200/mo | ₹0 |
| **Face Blur** | 512MB | 2s | 90,000/mo | 200/mo | ₹0 |
| **Perspective** | 512MB | 1s | 180,000/mo | 500/mo | ₹0 |
| **Repair** | 1GB | 5s | 36,000/mo | 100/mo | ₹0 |

**TOTAL: ₹0/month** (All within FREE tier) ✅

---

## 📊 **Usage Scenarios**

### **Scenario 1: Personal Use (Recommended)**
```
Monthly:
- 500 background removals
- 200 face detections
- 100 face blurs
- 200 perspective fixes
- 50 photo repairs

Total: 1,050 operations
All FREE ✅
Cost: ₹0
```

### **Scenario 2: Regular Use**
```
Monthly:
- 2,000 background removals
- 500 face detections
- 300 face blurs
- 500 perspective fixes
- 200 photo repairs

Total: 3,500 operations
All within FREE tier ✅
Cost: ₹0
```

### **Scenario 3: Heavy Use**
```
Monthly:
- 10,000 background removals
- 1,500 face detections
- 1,000 face blurs
- 2,000 perspective fixes
- 1,000 photo repairs

Overage:
- RemBG: within vCPU limit ✅
- Face detect: 500 extra ($0.75)
- Others: within free tier ✅

Cost: ₹60-100/month
```

---

## 🎯 **Deployment Steps**

### **Step 1: Setup Google Cloud**
```bash
# Install Google Cloud SDK
# Windows: Download from https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### **Step 2: Deploy Services**
```bash
# Deploy in order (Priority 1 first)

# 1. Background Removal
cd rembg-service
gcloud run deploy rembg-service --source . --region us-central1 --allow-unauthenticated --memory 1Gi --cpu 1 --min-instances 0 --max-instances 5

# 2. Face Blur
cd ../faceblur-service
gcloud run deploy faceblur-service --source . --region us-central1 --allow-unauthenticated --memory 512Mi --cpu 1 --min-instances 0 --max-instances 5

# 3. Perspective Correction
cd ../perspective-service
gcloud run deploy perspective-service --source . --region us-central1 --allow-unauthenticated --memory 512Mi --cpu 1 --min-instances 0 --max-instances 5

# 4. (Optional) Photo Repair
cd ../repair-service
gcloud run deploy repair-service --source . --region us-central1 --allow-unauthenticated --memory 1Gi --cpu 1 --min-instances 0 --max-instances 3
```

### **Step 3: Get Service URLs**
```bash
# Get all service URLs
gcloud run services list --platform managed

# Copy the URLs and update your HTML file
# Example URLs:
# https://rembg-service-XXXXX-uc.a.run.app
# https://faceblur-service-XXXXX-uc.a.run.app
# https://perspective-service-XXXXX-uc.a.run.app
```

### **Step 4: Update HTML Code**
```javascript
// Update CLOUD_RUN_ENDPOINTS in image-repair-editor.html
const CLOUD_RUN_ENDPOINTS = {
    rembg: 'https://rembg-service-XXXXX-uc.a.run.app/remove-background',
    face_detect: 'https://vision.googleapis.com/v1/images:annotate',
    face_blur: 'https://faceblur-service-XXXXX-uc.a.run.app/blur-faces',
    perspective: 'https://perspective-service-XXXXX-uc.a.run.app/correct-perspective',
    photo_repair: 'https://repair-service-XXXXX-uc.a.run.app/repair' // Optional
};
```

### **Step 5: Set Billing Alerts**
```bash
# Set budget alerts to prevent unexpected charges
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT \
    --display-name="Monthly Budget Alert" \
    --budget-amount=100 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100
```

---

## 🔒 **Cost Control Strategies**

### **1. Monitor Usage**
```bash
# Check Cloud Run usage
gcloud run services describe SERVICE_NAME --region us-central1 --format="value(status.url)"

# View metrics
https://console.cloud.google.com/run
```

### **2. Set Resource Limits**
```bash
# Limit max instances to prevent runaway costs
gcloud run services update SERVICE_NAME \
    --max-instances 5 \
    --min-instances 0 \
    --region us-central1
```

### **3. Use Local Fallbacks**
```javascript
// Always provide local fallback algorithms
// If Cloud Run fails or is unavailable, use local processing
// This prevents dependency on paid services

async function processImage() {
    try {
        // Try Cloud Run service
        const result = await cloudRunAPI();
        return result;
    } catch (error) {
        // Fallback to local processing
        return localProcessing();
    }
}
```

### **4. Client-side Optimization**
```javascript
// Compress images before sending to Cloud Run
// Smaller images = Faster processing = Less GB-seconds used

async function compressBeforeSend(imageBlob) {
    const img = await createImageBitmap(imageBlob);
    const canvas = document.createElement('canvas');
    
    // Limit max dimensions
    const maxDim = 1920;
    let width = img.width;
    let height = img.height;
    
    if (width > maxDim || height > maxDim) {
        if (width > height) {
            height = (height / width) * maxDim;
            width = maxDim;
        } else {
            width = (width / height) * maxDim;
            height = maxDim;
        }
    }
    
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, width, height);
    
    return new Promise(resolve => {
        canvas.toBlob(resolve, 'image/jpeg', 0.9);
    });
}
```

---

## ✅ **Final Recommendation**

### **Deploy These 3 Services (Most Important)**
1. ✅ **Background Removal** - Essential feature
2. ✅ **Face Blur** - Privacy feature
3. ✅ **Perspective Correction** - Utility feature

### **Use Built-in API (No Deployment)**
4. ✅ **Face Detection** - Cloud Vision API (1,000 free/month)

### **Use Local Algorithms (No Cost)**
5. ✅ **Photo Repair** - Local fallback works excellently
6. ✅ **Noise Removal** - Local algorithm very effective
7. ✅ **Auto Straighten** - Pure JavaScript, no server needed

---

## 💡 **Cost Summary**

**Deploying 3 services:**
- Personal use (500 images/month): **₹0**
- Regular use (2,000 images/month): **₹0**
- Heavy use (10,000 images/month): **₹50-100**

**Compared to alternatives:**
- RemBG API: ₹750/month
- Photoshop: ₹1,675/month
- Canva Pro: ₹1,000/month

**Your savings: 94-100%** 🎉

---

## 🚀 **Ready to Deploy?**

Run these commands in order:

```bash
# 1. Setup
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable services
gcloud services enable run.googleapis.com vision.googleapis.com

# 3. Deploy (one by one)
# See detailed deployment commands above for each service

# 4. Get URLs
gcloud run services list

# 5. Update HTML file with URLs

# 6. Test!
```

**Your total investment: ₹0-50/month** ✅
**Features: Professional image editor** ✅
**Performance: Smooth on all devices** ✅
