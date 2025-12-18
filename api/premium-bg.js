// Vercel Serverless Function for Premium Background Removal
// Proxies requests to Cloud Run BiRefNet backend with authentication

const CLOUDRUN_API_URL_BG_REMOVAL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 
                                     'https://bg-removal-ai-564572183797.us-central1.run.app';

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '3600');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      message: 'Only POST method is supported'
    });
  }

  try {
    // Verify authentication token and extract userId
    const authHeader = req.headers.authorization;
    let verifiedUserId = null;
    
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.replace('Bearer ', '');
      
      // Try to verify Firebase token if Firebase Admin is available
      // Note: In Vercel serverless, Firebase Admin might not be available
      // The token will be verified by the backend or we can skip verification here
      // and let the backend handle it
      try {
        // Try to load Firebase Admin (may not be available in Vercel serverless)
        let firebaseAdmin = null;
        try {
          const admin = require('firebase-admin');
          if (admin.apps.length > 0) {
            firebaseAdmin = admin.app();
          } else {
            // Try to initialize if service account is available
            const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT;
            if (serviceAccount) {
              const serviceAccountJson = JSON.parse(serviceAccount);
              firebaseAdmin = admin.initializeApp({
                credential: admin.credential.cert(serviceAccountJson)
              });
            }
          }
        } catch (adminError) {
          // Firebase Admin not available - this is OK, backend will verify
          console.log('Firebase Admin not available in serverless function (this is OK)');
        }
        
        if (firebaseAdmin && firebaseAdmin.apps.length > 0) {
          const decodedToken = await firebaseAdmin.auth().verifyIdToken(token);
          verifiedUserId = decodedToken.uid;
          console.log(`✅ Verified Firebase token for user: ${verifiedUserId}`);
        }
      } catch (firebaseError) {
        // If Firebase Admin not available or token invalid, continue with token from body
        // Backend will verify the token
        console.log('Token verification skipped in serverless (backend will verify):', firebaseError.message);
      }
    }
    
    // If userId not verified from token, use from request body (fallback)
    const requestBody = { ...req.body };
    if (verifiedUserId && !requestBody.userId) {
      requestBody.userId = verifiedUserId;
    }
    
    // Forward request to Cloud Run BiRefNet API
    const backendUrl = `${CLOUDRUN_API_URL_BG_REMOVAL}/api/premium-bg`;
    
    // Forward headers (especially Authorization)
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    
    if (req.headers.authorization) {
      headers['Authorization'] = req.headers.authorization;
    }
    
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 300000); // 5 minutes
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestBody),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Backend error: ${response.status}`;
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch (e) {
        errorMessage = errorText || errorMessage;
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage
      });
    }

    const result = await response.json();
    res.json(result);
    
  } catch (error) {
    console.error('Premium BG removal proxy error:', error);
    
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      return res.status(504).json({
        success: false,
        error: 'Request timeout. The image might be too large or the server is busy.'
      });
    }
    
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to process premium background removal request'
    });
  }
};

