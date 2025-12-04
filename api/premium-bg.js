// Vercel Serverless Function - Premium HD Background Removal (2000-4000px GPU-accelerated)
// Proxies requests to Google Cloud Run backend with credit verification

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 'https://bg-removal-birefnet-564572183797.us-central1.run.app';

// Firebase Admin SDK for credit verification
let admin = null;
let firebaseInitialized = false;

async function initializeFirebase() {
  if (firebaseInitialized) return admin;
  
  try {
    // Try to use Firebase Admin SDK
    const adminModule = await import('firebase-admin');
    admin = adminModule.default;
    
    if (!admin.apps.length) {
      // Initialize with service account from environment
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
        console.warn('Firebase Admin not initialized - credit verification may be limited');
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
      console.warn('Firebase not available - skipping credit verification');
      return { success: false, error: 'Credit system unavailable' };
    }
    
    const db = adminInstance.firestore();
    const userRef = db.collection('users').doc(userId);
    const userDoc = await userRef.get();
    
    if (!userDoc.exists) {
      // Initialize user credits
      await userRef.set({
        credits: 0,
        totalCreditsEarned: 0,
        totalCreditsUsed: 0,
        createdAt: adminInstance.firestore.FieldValue.serverTimestamp(),
        lastCreditUpdate: adminInstance.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
      return {
        success: false,
        error: 'Insufficient credits',
        creditsRequired: creditsRequired,
        creditsAvailable: 0
      };
    }
    
    const userData = userDoc.data();
    const currentCredits = userData.credits || 0;
    
    // Check subscription plan for unlimited credits
    const subscriptionRef = db.collection('subscriptions').doc(userId);
    const subscriptionDoc = await subscriptionRef.get();
    
    let hasUnlimited = false;
    if (subscriptionDoc.exists) {
      const subData = subscriptionDoc.data();
      if (subData.plan === 'premium' || subData.plan === 'business') {
        // Premium/Business users may have unlimited credits
        hasUnlimited = subData.features?.unlimitedBackgroundRemoval || false;
      }
    }
    
    if (!hasUnlimited && currentCredits < creditsRequired) {
      return {
        success: false,
        error: 'Insufficient credits',
        creditsRequired: creditsRequired,
        creditsAvailable: currentCredits
      };
    }
    
    // Deduct credits (if not unlimited)
    if (!hasUnlimited) {
      await userRef.update({
        credits: adminInstance.firestore.FieldValue.increment(-creditsRequired),
        totalCreditsUsed: adminInstance.firestore.FieldValue.increment(creditsRequired),
        lastCreditUpdate: adminInstance.firestore.FieldValue.serverTimestamp()
      });
      
      // Record transaction
      await db.collection('users').doc(userId).collection('creditTransactions').add({
        type: 'deduction',
        amount: creditsRequired,
        reason: 'Premium HD Background Removal',
        creditsBefore: currentCredits,
        creditsAfter: currentCredits - creditsRequired,
        timestamp: adminInstance.firestore.FieldValue.serverTimestamp(),
        metadata: {
          service: 'background-removal',
          quality: 'premium-hd'
        }
      });
    }
    
    const updatedCredits = hasUnlimited ? 'unlimited' : currentCredits - creditsRequired;
    
    return {
      success: true,
      creditsRemaining: updatedCredits,
      creditsUsed: hasUnlimited ? 0 : creditsRequired,
      unlimited: hasUnlimited
    };
  } catch (error) {
    console.error('Credit verification error:', error);
    return {
      success: false,
      error: 'Credit verification failed',
      message: error.message
    };
  }
}

export default async function handler(req, res) {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.setHeader('Access-Control-Max-Age', '3600');
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      message: 'Only POST method is supported'
    });
  }

  try {
    const { imageData, userId } = req.body;
    const authHeader = req.headers.authorization;

    if (!imageData) {
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(400).json({
        success: false,
        error: 'Missing imageData',
        message: 'imageData is required in request body'
      });
    }

    // Get userId from body or extract from auth token
    let finalUserId = userId;
    if (!finalUserId && authHeader) {
      try {
        // Extract user ID from Firebase token (simplified - in production, verify token)
        const token = authHeader.replace('Bearer ', '');
        // For now, we'll use userId from body or require it
      } catch (e) {
        console.warn('Token extraction failed:', e);
      }
    }

    if (!finalUserId) {
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
        message: 'userId is required for premium processing. Please sign in.'
      });
    }

    // Verify and deduct credits BEFORE processing
    const creditsRequired = 1; // 1 credit per premium HD processing
    const creditCheck = await verifyAndDeductCredits(finalUserId, creditsRequired);

    if (!creditCheck.success) {
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(402).json({
        success: false,
        error: creditCheck.error || 'Insufficient credits',
        message: creditCheck.error === 'Insufficient credits' 
          ? `You need ${creditsRequired} credit(s) for Premium HD processing. You have ${creditCheck.creditsAvailable || 0} credit(s) available.`
          : 'Credit verification failed',
        creditsRequired: creditsRequired,
        creditsAvailable: creditCheck.creditsAvailable
      });
    }

    // Proxy to Cloud Run backend for premium HD (2000-4000px)
    const response = await fetch(`${CLOUDRUN_API_URL}/api/premium-bg`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-User-ID': finalUserId
      },
      body: JSON.stringify({
        imageData: imageData,
        quality: 'hd', // 2000-4000px output
        minSize: 2000,
        maxSize: 4000,
        userId: finalUserId
      }),
      signal: AbortSignal.timeout(300000) // 5 minutes timeout
    });

    // Handle non-OK responses
    if (!response.ok) {
      // If processing failed, refund credits
      if (creditCheck.creditsUsed) {
        try {
          const adminInstance = await initializeFirebase();
          if (adminInstance) {
            const db = adminInstance.firestore();
            await db.collection('users').doc(finalUserId).update({
              credits: adminInstance.firestore.FieldValue.increment(creditCheck.creditsUsed)
            });
          }
        } catch (refundError) {
          console.error('Credit refund failed:', refundError);
        }
      }

      let errorData = {};
      try {
        const errorText = await response.text();
        try {
          errorData = JSON.parse(errorText);
        } catch (parseError) {
          errorData = {
            success: false,
            error: 'Backend error',
            message: errorText || `Backend returned ${response.status}: ${response.statusText}`
          };
        }
      } catch (e) {
        errorData = {
          success: false,
          error: 'Backend error',
          message: `Backend returned ${response.status}: ${response.statusText}`
        };
      }
      
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(response.status).json(errorData);
    }

    const data = await response.json();
    
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(200).json({
      success: true,
      resultImage: data.resultImage || data.image || data.output,
      outputSize: data.outputSize || data.size,
      outputSizeMB: data.outputSizeMB || (data.outputSize ? (data.outputSize / (1024 * 1024)).toFixed(2) : null),
      processedWith: data.processedWith || 'Premium HD (2000-4000px GPU-accelerated High-Resolution)',
      creditsUsed: creditCheck.creditsUsed || creditsRequired,
      creditsRemaining: creditCheck.creditsRemaining
    });

  } catch (error) {
    console.error('Premium HD proxy error:', error);
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    // Handle timeout errors
    if (error.name === 'AbortError' || error.message.includes('timeout')) {
      return res.status(504).json({
        success: false,
        error: 'Request timeout',
        message: 'Processing took too long. Please try with a smaller image or try again later.'
      });
    }
    
    // Handle network errors
    if (error.message.includes('fetch') || error.message.includes('ECONNREFUSED')) {
      return res.status(503).json({
        success: false,
        error: 'Service unavailable',
        message: 'Background removal service is temporarily unavailable. Please try again later.'
      });
    }
    
    return res.status(500).json({
      success: false,
      error: 'Proxy error',
      message: error.message || 'Failed to process image'
    });
  }
}

