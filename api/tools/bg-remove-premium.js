// Direct route handler for /api/tools/bg-remove-premium
// Premium HD Background Removal (2000-4000px GPU-accelerated)

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 'https://bg-removal-ai-564572183797.us-central1.run.app';

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

