// Consolidated Tools API Router
// Handles all tool-related endpoints in a single function
// Routes: /api/tools/bg-remove-free, /api/tools/bg-remove-premium, /api/tools/unlock-excel, etc.

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 'https://bg-removal-ai-564572183797.us-central1.run.app';

// Firebase Admin SDK for credit verification
let admin = null;
let firebaseInitialized = false;

async function initializeFirebase() {
  if (firebaseInitialized) return admin;
  
  try {
    const adminModule = await import('firebase-admin');
    admin = adminModule.default;
    
    if (!admin.apps.length) {
      const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT 
        ? JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT)
        : null;
      
      if (serviceAccount) {
        admin.initializeApp({
          credential: admin.credential.cert(serviceAccount)
        });
      } else if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
        admin.initializeApp({
          credential: admin.credential.applicationDefault()
        });
      } else {
        return null;
      }
    }
    
    firebaseInitialized = true;
    return admin;
  } catch (error) {
    console.warn('Firebase Admin initialization failed:', error);
    return null;
  }
}

// Verify and deduct credits
async function verifyAndDeductCredits(userId, creditsRequired = 1) {
  try {
    const adminInstance = await initializeFirebase();
    if (!adminInstance) {
      return { hasCredits: false, error: 'Firebase not initialized' };
    }

    const db = adminInstance.firestore();
    
    // Check subscription for unlimited credits
    const subscriptionRef = db.collection('subscriptions').doc(userId);
    const subscriptionDoc = await subscriptionRef.get();
    
    if (subscriptionDoc.exists) {
      const subData = subscriptionDoc.data();
      if (subData.plan === 'premium' || subData.plan === 'business') {
        if (subData.features?.unlimitedBackgroundRemoval) {
          return { hasCredits: true, unlimited: true };
        }
      }
    }

    // Use transaction to check and deduct credits atomically
    let result = { hasCredits: false, creditsAvailable: 0 };
    
    await db.runTransaction(async (transaction) => {
      const userRef = db.collection('users').doc(userId);
      const userDoc = await transaction.get(userRef);

      if (!userDoc.exists) {
        result = { hasCredits: false, creditsAvailable: 0, error: 'User not found' };
        return;
      }

      const userData = userDoc.data();
      const currentCredits = userData.credits || 0;

      if (currentCredits >= creditsRequired) {
        // Deduct credits
        transaction.update(userRef, {
          credits: currentCredits - creditsRequired,
          totalCreditsUsed: (userData.totalCreditsUsed || 0) + creditsRequired,
          lastCreditUpdate: adminInstance.firestore.FieldValue.serverTimestamp()
        });
        result = { hasCredits: true, creditsAvailable: currentCredits - creditsRequired };
      } else {
        result = { hasCredits: false, creditsAvailable: currentCredits };
      }
    });

    return result;
  } catch (error) {
    console.error('Credit verification error:', error);
    return { hasCredits: false, error: error.message };
  }
}

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '3600');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Extract route from query parameter (set by Vercel rewrite) or URL path
  // Vercel rewrite: /api/tools/bg-remove-free -> /api/tools/index.js?route=bg-remove-free
  
  // Extract route - Multiple methods for maximum compatibility
  let route = null;
  
  // METHOD 1: req.query.route (from Vercel rewrite: /api/tools/bg-remove-free -> /api/tools/index.js?route=bg-remove-free)
  if (req.query && req.query.route) {
    route = req.query.route;
    console.log('[METHOD 1] Route from req.query.route:', route);
  }
  
  // METHOD 2: Parse query string from req.url directly
  if (!route && req.url && req.url.includes('route=')) {
    try {
      const queryMatch = req.url.match(/[?&]route=([^&]+)/);
      if (queryMatch && queryMatch[1]) {
        route = decodeURIComponent(queryMatch[1]);
        console.log('[METHOD 2] Route from req.url query string:', route);
      }
    } catch (e) {
      console.warn('Failed to parse route from req.url:', e);
    }
  }
  
  // METHOD 3: Extract from original URL path (from Vercel headers)
  if (!route) {
    let originalUrl = req.headers['x-vercel-original-url'] || 
                     req.headers['x-invoke-path'] || 
                     req.headers['x-forwarded-path'] ||
                     '';
    
    // If no header, check req.url but skip if it's the rewritten path
    if (!originalUrl && req.url) {
      // Only use req.url if it's NOT the rewritten path
      if (!req.url.includes('/api/tools/index.js')) {
        originalUrl = req.url;
      }
    }
    
    if (originalUrl) {
      // Remove query string first
      if (originalUrl.includes('?')) {
        const [pathPart, queryPart] = originalUrl.split('?');
        originalUrl = pathPart;
        // Also try to extract route from query string if present
        if (queryPart) {
          try {
            const params = new URLSearchParams(queryPart);
            const queryRoute = params.get('route');
            if (queryRoute && queryRoute !== 'index.js' && queryRoute !== 'index') {
              const validRoutes = ['bg-remove-free', 'bg-remove-premium', 'unlock-excel', 'health'];
              if (validRoutes.includes(queryRoute)) {
                route = queryRoute;
                console.log('[METHOD 3a] Route from query string:', route);
              }
            }
          } catch (e) {
            // Continue with path parsing
          }
        }
      }
      
      // If route still not found, parse path
      if (!route && originalUrl) {
        // Remove protocol
        if (originalUrl.includes('://')) {
          try {
            const urlObj = new URL(originalUrl);
            originalUrl = urlObj.pathname;
          } catch (e) {
            // Continue
          }
        }
        
        // Parse: /api/tools/bg-remove-free -> bg-remove-free
        const pathParts = originalUrl.split('/').filter(p => p && p !== 'api' && p !== 'tools' && p !== 'index.js' && p !== 'index');
        const toolsIndex = originalUrl.split('/').indexOf('tools');
        
        if (toolsIndex >= 0) {
          const pathAfterTools = originalUrl.split('/').slice(toolsIndex + 1).filter(p => p);
          const extractedRoute = pathAfterTools[0];
          
          // CRITICAL: Filter out index.js and index
          if (extractedRoute && extractedRoute !== 'index.js' && extractedRoute !== 'index') {
            // Validate - must be a real route name
            const validRoutes = ['bg-remove-free', 'bg-remove-premium', 'unlock-excel', 'health'];
            if (validRoutes.includes(extractedRoute)) {
              route = extractedRoute;
              console.log('[METHOD 3b] Route from path parsing:', route);
            }
          }
        }
      }
    }
  }
  
  // CRITICAL VALIDATION: Reject invalid routes
  const validRoutes = ['bg-remove-free', 'bg-remove-premium', 'unlock-excel', 'health'];
  if (route && !validRoutes.includes(route)) {
    console.error('[VALIDATION] Invalid route detected:', route, '| Rejecting and using fallback');
    route = null;
  }
  
  // Reject index.js or index explicitly
  if (route === 'index.js' || route === 'index' || route === 'tools') {
    console.error('[VALIDATION] Route is invalid (index.js/index/tools):', route, '| Using fallback');
    route = null;
  }
  
  // METHOD 4: Final fallback - use default based on method
  if (!route) {
    console.error('[METHOD 4] CRITICAL: Route extraction failed!', {
      'req.url': req.url,
      'req.query': JSON.stringify(req.query),
      'req.method': req.method,
      'headers': {
        'x-vercel-original-url': req.headers['x-vercel-original-url'],
        'x-invoke-path': req.headers['x-invoke-path'],
        'x-forwarded-path': req.headers['x-forwarded-path']
      }
    });
    // Default: bg-remove-free for POST, health for GET
    route = req.method === 'POST' ? 'bg-remove-free' : 'health';
  }
  
  console.log('[FINAL] Route determined:', route, '| Method:', req.method);

  try {
    // Route: /api/tools/bg-remove-free (Free Preview 512px)
    if (route === 'bg-remove-free' && req.method === 'POST') {
      return await handleBgRemoveFree(req, res);
    }

    // Route: /api/tools/bg-remove-premium (Premium HD 2000-4000px)
    if (route === 'bg-remove-premium' && req.method === 'POST') {
      return await handleBgRemovePremium(req, res);
    }

    // Route: /api/tools/unlock-excel
    if (route === 'unlock-excel' && req.method === 'POST') {
      return await handleUnlockExcel(req, res);
    }

    // Route: /api/tools/health
    if (route === 'health') {
      return res.status(200).json({ status: 'healthy', service: 'tools-api' });
    }

    // Unknown route
    return res.status(404).json({ 
      success: false, 
      error: `Route not found: ${route}`,
      availableRoutes: ['bg-remove-free', 'bg-remove-premium', 'unlock-excel', 'health']
    });

  } catch (error) {
    console.error('Tools API error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Internal server error'
    });
  }
};

// Free Background Removal Handler (512px)
async function handleBgRemoveFree(req, res) {
  try {
    const { imageData } = req.body;

    if (!imageData) {
      return res.status(400).json({
        success: false,
        error: 'Missing imageData',
        message: 'imageData is required in request body'
      });
    }

    // Proxy to Cloud Run backend for free preview (512px)
    const response = await fetch(`${CLOUDRUN_API_URL}/api/free-preview-bg`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        imageData: imageData,
        quality: 'preview',
        maxSize: 512
      }),
      signal: AbortSignal.timeout(300000)
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorData = {};
      try {
        errorData = JSON.parse(errorText);
      } catch (e) {
        errorData = { error: errorText || `Server error: ${response.status}` };
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
        message: errorData.message || 'Background removal failed'
      });
    }

    const result = await response.json();

    if (result.success && result.resultImage) {
      return res.status(200).json({
        success: true,
        resultImage: result.resultImage,
        processedWith: 'Free Preview (512px GPU-accelerated)',
        outputSize: result.outputSize,
        outputSizeMB: result.outputSizeMB
      });
    } else {
      return res.status(500).json({
        success: false,
        error: result.error || 'Processing failed'
      });
    }

  } catch (error) {
    console.error('Free preview processing error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Free preview processing failed'
    });
  }
}

// Premium Background Removal Handler (2000-4000px)
async function handleBgRemovePremium(req, res) {
  try {
    const { imageData, userId } = req.body;

    if (!imageData) {
      return res.status(400).json({
        success: false,
        error: 'Missing imageData',
        message: 'imageData is required in request body'
      });
    }

    // Verify credits if userId provided
    if (userId) {
      const creditCheck = await verifyAndDeductCredits(userId, 1);
      
      if (!creditCheck.hasCredits && !creditCheck.unlimited) {
        return res.status(402).json({
          success: false,
          error: 'Insufficient credits',
          message: `You need 1 credit for Premium HD. You have ${creditCheck.creditsAvailable || 0} credit(s).`,
          requiresAuth: !userId,
          requiresCredits: true
        });
      }
    } else {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
        message: 'Please sign in to use Premium HD processing',
        requiresAuth: true
      });
    }

    // Proxy to Cloud Run backend for premium HD
    const response = await fetch(`${CLOUDRUN_API_URL}/api/premium-bg`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        imageData: imageData,
        quality: 'hd',
        maxSize: 4000
      }),
      signal: AbortSignal.timeout(300000)
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorData = {};
      try {
        errorData = JSON.parse(errorText);
      } catch (e) {
        errorData = { error: errorText || `Server error: ${response.status}` };
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
        message: errorData.message || 'Premium HD processing failed'
      });
    }

    const result = await response.json();

    if (result.success && result.resultImage) {
      return res.status(200).json({
        success: true,
        resultImage: result.resultImage,
        processedWith: 'Premium HD (2000-4000px GPU-accelerated High-Resolution)',
        outputSize: result.outputSize,
        outputSizeMB: result.outputSizeMB,
        creditsUsed: 1
      });
    } else {
      return res.status(500).json({
        success: false,
        error: result.error || 'Processing failed'
      });
    }

  } catch (error) {
    console.error('Premium HD processing error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Premium HD processing failed'
    });
  }
}

// Unlock Excel Handler
async function handleUnlockExcel(req, res) {
  try {
    const BACKEND_URL = 'https://excel-unlocker-backend.onrender.com/unlock';
    const { file, password } = req.body;

    if (!file) {
      return res.status(400).json({
        success: false,
        error: 'No file provided'
      });
    }

    const formData = new FormData();
    formData.append('file', file);
    if (password) {
      formData.append('password', password);
    }

    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    return res.status(response.status).json(result);

  } catch (error) {
    console.error('Unlock Excel error:', error);
    return res.status(500).json({
      success: false,
      error: `Server error: ${error.message}`
    });
  }
}

