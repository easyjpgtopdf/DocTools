// Direct route handler for /api/tools/bg-remove-premium
// Premium HD Background Removal (2000-4000px GPU-accelerated)

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 'https://bg-removal-birefnet-564572183797.us-central1.run.app';

function normalizeImageData(imageData) {
  if (!imageData || typeof imageData !== 'string') {
    return { ok: false, message: 'imageData is required and must be a string' };
  }

  const trimmed = imageData.trim();
  const isDataUrl = trimmed.startsWith('data:');

  let mime = 'image/png';
  let base64Part = trimmed;

  if (isDataUrl) {
    const match = trimmed.match(/^data:(image\/[a-zA-Z0-9.+-]+);base64,(.+)$/);
    if (!match) {
      return { ok: false, message: 'imageData must be a base64 data URL (data:image/...;base64,...)' };
    }
    mime = match[1];
    base64Part = match[2];
  }

  // Clean and pad base64
  base64Part = base64Part.replace(/\s+/g, '').replace(/-/g, '+').replace(/_/g, '/');
  if (base64Part.length < 100) {
    return { ok: false, message: 'Image data is too small or corrupted' };
  }
  const remainder = base64Part.length % 4;
  if (remainder) {
    base64Part = base64Part.padEnd(base64Part.length + (4 - remainder), '=');
  }

  let buffer;
  try {
    buffer = Buffer.from(base64Part, 'base64');
  } catch (err) {
    return { ok: false, message: `Invalid base64 encoding: ${err.message}` };
  }

  if (!buffer?.length) {
    return { ok: false, message: 'Decoded image is empty' };
  }

  return {
    ok: true,
    mime,
    bytes: buffer.length,
    dataUrl: `data:${mime};base64,${buffer.toString('base64')}`
  };
}

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

// Verify and deduct credits using new MongoDB credit system
async function verifyAndDeductCredits(userId, token, creditsRequired = 1) {
  try {
    // Use new credit API endpoint (MongoDB-based)
    const API_BASE_URL = process.env.BACKEND_URL || 'https://pdf-to-word-converter-iwumaktavq-uc.a.run.app';
    
    // First check balance
    const balanceResponse = await fetch(`${API_BASE_URL}/api/credits/balance`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!balanceResponse.ok) {
      console.error('Failed to check credit balance:', balanceResponse.status);
      return { hasCredits: false, creditsAvailable: 0, error: 'Failed to check credits' };
    }

    const balanceData = await balanceResponse.json();
    if (!balanceData.success) {
      return { hasCredits: false, creditsAvailable: 0, error: balanceData.error || 'Failed to check credits' };
    }

    const currentCredits = balanceData.credits || 0;

    if (currentCredits < creditsRequired) {
      return { hasCredits: false, creditsAvailable: currentCredits };
    }

    // Deduct credits via API
    const deductResponse = await fetch(`${API_BASE_URL}/api/credits/deduct`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        amount: creditsRequired,
        tool_used: 'background-remover-premium',
        page: '/background-workspace.html',
        processor: 'premium-hd'
      })
    });

    if (!deductResponse.ok) {
      const errorData = await deductResponse.json().catch(() => ({}));
      console.error('Failed to deduct credits:', errorData);
      return { hasCredits: false, creditsAvailable: currentCredits, error: errorData.error || 'Failed to deduct credits' };
    }

    const deductData = await deductResponse.json();
    if (!deductData.success) {
      return { hasCredits: false, creditsAvailable: currentCredits, error: deductData.error || 'Failed to deduct credits' };
    }

    return { 
      hasCredits: true, 
      creditsAvailable: deductData.credits || (currentCredits - creditsRequired),
      unlimited: false
    };
  } catch (error) {
    console.error('Credit verification error:', error);
    return { hasCredits: false, creditsAvailable: 0, error: error.message };
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

  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      message: 'Only POST method is supported'
    });
  }

  try {
    const { imageData, userId } = req.body;

    const normalized = normalizeImageData(imageData);
    if (!normalized.ok) {
      return res.status(400).json({
        success: false,
        error: 'Invalid image data',
        message: normalized.message
      });
    }

    // SECURITY: Get token from Authorization header (not from request body)
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
        message: 'Please sign in to use Premium HD processing',
        requiresAuth: true
      });
    }

    const token = authHeader.replace('Bearer ', '');

    // SECURITY: Verify token and get userId from token (not from request body)
    let verifiedUserId = null;
    try {
      const adminModule = await initializeFirebase();
      if (adminModule && adminModule.apps.length) {
        const decodedToken = await adminModule.auth().verifyIdToken(token);
        verifiedUserId = decodedToken.uid;
      } else {
        // Fallback: use userId from body if Firebase not initialized
        console.warn('Firebase not initialized, using userId from request body');
        verifiedUserId = userId;
      }
    } catch (tokenError) {
      console.error('Token verification failed:', tokenError);
      return res.status(401).json({
        success: false,
        error: 'Invalid authentication token',
        message: 'Please sign in again to use Premium HD processing',
        requiresAuth: true
      });
    }

    // Verify userId is provided and matches token
    if (!verifiedUserId) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
        message: 'Please sign in to use Premium HD processing',
        requiresAuth: true
      });
    }

    // SECURITY: Verify userId from token matches userId from request body
    if (userId && userId !== verifiedUserId) {
      console.warn(`User ID mismatch: token userId (${verifiedUserId}) != request userId (${userId})`);
      return res.status(403).json({
        success: false,
        error: 'User ID mismatch',
        message: 'Authentication failed: User ID does not match token',
        requiresAuth: true
      });
    }

    // Use verified userId from token for credit operations
    const finalUserId = verifiedUserId;

    // Verify and deduct credits using verified userId from token
    const creditCheck = await verifyAndDeductCredits(finalUserId, token, 1);
    
    if (!creditCheck.hasCredits && !creditCheck.unlimited) {
      return res.status(402).json({
        success: false,
        error: 'Insufficient credits',
        message: `You need 1 credit for Premium HD. You have ${creditCheck.creditsAvailable || 0} credit(s). Please purchase credits.`,
        requiresAuth: false,
        requiresCredits: true,
        creditsAvailable: creditCheck.creditsAvailable || 0
      });
    }

    console.log('Premium HD request received, proxying to Cloud Run...');
    console.log('Cloud Run URL:', CLOUDRUN_API_URL);
    console.log('Decoded bytes:', normalized.bytes);

    // Proxy to Cloud Run backend for premium HD
    const response = await fetch(`${CLOUDRUN_API_URL}/api/premium-bg`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        imageData: normalized.dataUrl,
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
      
      console.error('Cloud Run error:', {
        status: response.status,
        error: errorData
      });
      
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
};

