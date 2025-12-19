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

  // Use cleaned and padded base64Part directly (don't re-encode from buffer)
  // Re-encoding from buffer could cause issues with special characters
  return {
    ok: true,
    mime,
    bytes: buffer.length,
    dataUrl: `data:${mime};base64,${base64Part}` // Use cleaned and padded base64 directly
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

// Check credit balance (without deducting)
async function checkCreditBalance(userId, token) {
  try {
    // Use direct Firestore query instead of API call (faster and more reliable)
    const adminModule = await initializeFirebase();
    if (!adminModule || !adminModule.apps.length) {
      console.error('Firebase not initialized for credit check');
      return { hasCredits: false, creditsAvailable: 0, unlimited: false, error: 'Database not available' };
    }
    
    const db = adminModule.firestore();
    const userRef = db.collection('users').doc(userId);
    const userDoc = await userRef.get();
    
    if (!userDoc.exists) {
      return { hasCredits: false, creditsAvailable: 0, unlimited: false, error: 'User not found' };
    }
    
    const userData = userDoc.data();
    // CRITICAL: Ensure credits is a number, not a string
    // Firestore may store credits as strings, so we need to parse them
    const currentCredits = typeof userData.credits === 'number' 
      ? userData.credits 
      : (typeof userData.credits === 'string' ? parseFloat(userData.credits) || 0 : 0);
    
    // Check subscription for unlimited credits
    const subscriptionRef = db.collection('subscriptions').doc(userId);
    const subscriptionDoc = await subscriptionRef.get();
    let unlimited = false;
    if (subscriptionDoc.exists) {
      const subData = subscriptionDoc.data();
      if (subData.plan === 'premium' || subData.plan === 'business') {
        unlimited = subData.features?.unlimitedBackgroundRemoval || false;
      }
    }
    
    return { 
      hasCredits: true, 
      creditsAvailable: currentCredits,
      unlimited: unlimited
    };
  } catch (error) {
    console.error('Credit balance check error:', error);
    return { hasCredits: false, creditsAvailable: 0, unlimited: false, error: error.message };
  }
}

// Deduct credits using Firestore directly (more reliable)
async function deductCredits(userId, token, creditsRequired = 1) {
  try {
    const adminModule = await initializeFirebase();
    if (!adminModule || !adminModule.apps.length) {
      console.error('Firebase not initialized for credit deduction');
      return { success: false, error: 'Database not available' };
    }
    
    const db = adminModule.firestore();
    const userRef = db.collection('users').doc(userId);
    
    // Use transaction to ensure atomic credit deduction
    return await db.runTransaction(async (transaction) => {
      const userDoc = await transaction.get(userRef);
      
      if (!userDoc.exists) {
        throw new Error('User not found');
      }
      
      const userData = userDoc.data();
      // CRITICAL: Ensure credits is a number, not a string
      // Firestore may store credits as strings, so we need to parse them
      const currentCredits = typeof userData.credits === 'number' 
        ? userData.credits 
        : (typeof userData.credits === 'string' ? parseFloat(userData.credits) || 0 : 0);
      
      // Check if user has sufficient credits
      if (currentCredits < creditsRequired) {
        return {
          success: false,
          error: 'Insufficient credits',
          creditsAvailable: currentCredits,
          required: creditsRequired
        };
      }
      
      const newCredits = currentCredits - creditsRequired;
      
      // Update credits
      transaction.update(userRef, {
        credits: adminModule.firestore.FieldValue.increment(-creditsRequired),
        totalCreditsUsed: adminModule.firestore.FieldValue.increment(creditsRequired),
        lastCreditUpdate: adminModule.firestore.FieldValue.serverTimestamp()
      });
      
      // Record transaction
      const transactionRef = db.collection('users').doc(userId)
        .collection('creditTransactions').doc();
      transaction.set(transactionRef, {
        type: 'deduction',
        amount: creditsRequired,
        reason: 'Background removal - Premium HD (up to 25 MP)',
        creditsBefore: currentCredits,
        creditsAfter: newCredits,
        timestamp: adminModule.firestore.FieldValue.serverTimestamp(),
        metadata: {
          tool_used: 'background-remover-premium',
          page: '/background-workspace.html',
          processor: 'premium-hd'
        }
      });
      
      console.log(`✅ Deducted ${creditsRequired} credits from user ${userId}. Before: ${currentCredits}, After: ${newCredits}`);
      
      return {
        success: true,
        creditsAvailable: newCredits,
        creditsDeducted: creditsRequired
      };
    });
  } catch (error) {
    console.error('Credit deduction error:', error);
    return { success: false, error: error.message };
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
    const { imageData, userId, targetSize, targetWidth, targetHeight } = req.body;

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
    
    // Parse targetSize to get width and height if not provided
    let parsedWidth = targetWidth;
    let parsedHeight = targetHeight;
    const selectedSize = targetSize || 'original';
    
    if (selectedSize && selectedSize !== 'original' && !targetWidth && !targetHeight) {
      // Parse sizes like "1920x1080", "2048x2048", etc.
      const sizeMatch = selectedSize.match(/^(\d+)x(\d+)$/);
      if (sizeMatch) {
        parsedWidth = parseInt(sizeMatch[1], 10);
        parsedHeight = parseInt(sizeMatch[2], 10);
        console.log(`[Premium HD] Parsed size ${selectedSize} to width: ${parsedWidth}, height: ${parsedHeight}`);
      }
    }
    
    // STEP 1: Check credit balance based on SELECTED SIZE (not just minimum 4)
    // Credit costs based on size
    const creditCosts = {
      'original': 2, // Will be adjusted based on actual MP, but minimum 2
      '1920x1080': 2,
      '2048x2048': 4,
      '3000x2000': 4,
      '3000x3000': 6,
      '4000x3000': 9,
      '4000x4000': 10,
      '5000x3000': 12,
      '5000x5000': 15,
    };
    
    const creditsRequired = creditCosts[selectedSize] || creditCosts['original'];
    
    const creditCheck = await checkCreditBalance(finalUserId, token);
    
    // CRITICAL: Ensure creditsAvailable is a number for proper comparison
    const availableCredits = typeof creditCheck.creditsAvailable === 'number' 
      ? creditCheck.creditsAvailable 
      : (typeof creditCheck.creditsAvailable === 'string' ? parseFloat(creditCheck.creditsAvailable) || 0 : 0);
    
    console.log(`[Premium HD] Credit check - Available: ${availableCredits}, Required for ${selectedSize}: ${creditsRequired}`);
    
    if (!creditCheck.hasCredits || (!creditCheck.unlimited && availableCredits < creditsRequired)) {
      return res.status(402).json({
        success: false,
        error: 'Insufficient credits',
        message: `You need ${creditsRequired} credit(s) for ${selectedSize} size. You have ${availableCredits} credit(s). Please purchase credits or choose a smaller size.`,
        requiresAuth: false,
        requiresCredits: true,
        creditsAvailable: availableCredits,
        creditsRequired: creditsRequired,
        selectedSize: selectedSize
      });
    }

    console.log('Premium HD request received, proxying to Cloud Run...');
    console.log('Cloud Run URL:', CLOUDRUN_API_URL);
    console.log('Decoded bytes:', normalized.bytes);
    console.log('User ID:', finalUserId);
    console.log('Target Size:', targetSize);

    // STEP 2: Process image first (before deducting credits) at SELECTED SIZE
    const requestBody = {
      imageData: normalized.dataUrl,
      userId: finalUserId, // Use verified userId from token
      quality: 100, // Enterprise requirement: quality 100
      maxMegapixels: 25, // Max 25 Megapixels (width × height)
      preserveOriginal: selectedSize === 'original' || !selectedSize, // Preserve original resolution if ≤ 25 MP
      targetSize: selectedSize || 'original',
      targetWidth: parsedWidth || null, // Use parsed width from targetSize
      targetHeight: parsedHeight || null, // Use parsed height from targetSize
      imageType: req.body.imageType || null, // Forward imageType: "human" | "document" | "id_card" | "a4"
      whiteBackground: true, // Enterprise requirement: white background JPG
      outputFormat: 'jpg' // Enterprise requirement: JPG output
    };
    
    console.log(`[Premium HD] Processing at size: ${selectedSize}, width: ${parsedWidth}, height: ${parsedHeight}`);
    
    console.log('Request body keys:', Object.keys(requestBody));
    console.log('Request body (without imageData):', { ...requestBody, imageData: '[REDACTED]' });
    
    const response = await fetch(`${CLOUDRUN_API_URL}/api/premium-bg`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(requestBody),
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
      
      // Processing failed - don't deduct credits
      return res.status(response.status).json({
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
        message: errorData.message || 'Premium HD processing failed'
      });
    }

    let result;
    try {
      result = await response.json();
    } catch (parseError) {
      console.error('Failed to parse response JSON:', parseError);
      const errorText = await response.text();
      console.error('Response text:', errorText.substring(0, 500));
      return res.status(500).json({
        success: false,
        error: 'Invalid response from server',
        message: 'Server returned invalid JSON response. Please try again.'
      });
    }

    console.log('Cloud Run response:', {
      success: result.success,
      hasResultImage: !!result.resultImage,
      error: result.error,
      message: result.message
    });

    if (!result.success || !result.resultImage) {
      // Processing failed - don't deduct credits
      console.error('Processing failed:', {
        success: result.success,
        error: result.error,
        message: result.message,
        hasResultImage: !!result.resultImage
      });
      return res.status(500).json({
        success: false,
        error: result.error || 'Processing failed',
        message: result.message || 'Background removal processing failed. Please try again.'
      });
    }

    // STEP 3: Processing successful - NOW deduct credits based on SELECTED SIZE (not output size)
    // Use the credits required for the SELECTED size that user chose
    // This ensures user pays for what they selected, not what they got
    console.log(`[Premium HD] Deducting ${creditsRequired} credits for selected size: ${selectedSize}`);
    
    const deductResult = await deductCredits(finalUserId, token, creditsRequired);
    
    if (!deductResult.success) {
      // Processing succeeded but deduction failed - log error but still return result
      // This is a rare case - user got processed image but credits not deducted
      console.error('⚠️ WARNING: Image processed successfully but credit deduction failed:', deductResult.error);
      // Return success with a warning (don't fail the request since processing succeeded)
      return res.status(200).json({
        success: true,
        resultImage: result.resultImage,
        processedWith: 'Premium HD – up to 25 Megapixels (GPU-accelerated High-Resolution)',
        outputSize: result.outputSize,
        outputSizeMB: result.outputSizeMB,
        creditsUsed: result.creditsUsedDisplay || 2, // Show generic 2 in UI
        creditsUsedActual: creditsRequired, // Internal actual credits
        warning: 'Image processed but credit deduction may have failed - please check your account'
      });
    }

    // Success - processing done and credits deducted
    return res.status(200).json({
      success: true,
      resultImage: result.resultImage,
      processedWith: 'Premium HD – up to 25 Megapixels (GPU-accelerated High-Resolution)',
      outputSize: result.outputSize,
      outputSizeMB: result.outputSizeMB,
      creditsUsed: result.creditsUsedDisplay || 2, // Always show 2 in UI (generic)
      creditsUsedActual: creditsRequired, // Internal actual credits (2-7)
      creditsRemaining: deductResult.creditsAvailable,
      megapixels: result.megapixels
    });

  } catch (error) {
    console.error('Premium HD processing error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Premium HD processing failed'
    });
  }
};

