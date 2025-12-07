# Vercel Deployment Fix for PDF Editor

## Issue
Frontend was using empty string for API base URL in production, causing it to use relative URLs instead of Cloud Run backend.

## Fix Applied

### 1. Updated `getApiBaseUrl()` in `pdf-editor-preview.html`

**Before:**
```javascript
function getApiBaseUrl() {
    if (window.location.protocol === 'file:') {
        return 'http://localhost:3000';
    }
    return ''; // ❌ Empty string - uses relative URLs
}
```

**After:**
```javascript
function getApiBaseUrl() {
    const hostname = window.location.hostname;
    const isDevelopment = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.');
    
    if (isDevelopment) {
        return 'http://localhost:8080'; // Local backend
    }
    
    // Production: Use Cloud Run backend URL
    const cloudRunUrl = window.PDF_EDITOR_BACKEND_URL || 
                       'https://pdf-editor-service-564572183797.us-central1.run.app';
    
    console.log(`🔧 API Base URL configured: ${cloudRunUrl}`);
    return cloudRunUrl;
}
```

### 2. Backend URL Configuration

The frontend now uses:
- **Development:** `http://localhost:8080`
- **Production:** `https://pdf-editor-service-564572183797.us-central1.run.app`

### 3. Vercel Environment Variable (Optional)

You can set `PDF_EDITOR_BACKEND_URL` in Vercel environment variables if you want to override the default:

1. Go to Vercel Dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add: `PDF_EDITOR_BACKEND_URL` = `https://pdf-editor-service-564572183797.us-central1.run.app`

### 4. Deployment Steps

1. ✅ Fixed `getApiBaseUrl()` function
2. ✅ Backend deployed to Cloud Run
3. ⏳ **Deploy frontend to Vercel** (commit and push changes)

```bash
# Commit changes
git add pdf-editor-preview.html
git commit -m "Fix: Update getApiBaseUrl to use Cloud Run backend"
git push

# Vercel will auto-deploy, or manually deploy:
vercel --prod
```

### 5. Verification

After deployment, check browser console:
- Should see: `🔧 API Base URL configured: https://pdf-editor-service-564572183797.us-central1.run.app`
- All API calls should go to Cloud Run backend
- PDF editing features should work with native editing

### 6. Testing

1. Upload a PDF
2. Try adding text - should work with native editing
3. Try search - should highlight on canvas
4. Try replace - should use native redaction
5. Try OCR - should embed text natively

---

**Status:** ✅ Frontend code fixed, ready for Vercel deployment
