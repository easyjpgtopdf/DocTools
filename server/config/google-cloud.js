/**
 * Google Cloud Configuration
 * Handles service account authentication and client initialization
 */

const vision = require('@google-cloud/vision');
const admin = require('firebase-admin');

let visionClient = null;
let firebaseAdmin = null;

/**
 * Initialize Google Cloud Vision API client
 */
function initializeVisionClient() {
  if (visionClient) {
    return visionClient;
  }

  try {
    const serviceAccountRaw = process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT || 
                              process.env.FIREBASE_SERVICE_ACCOUNT;
    
    if (serviceAccountRaw) {
      const serviceAccount = JSON.parse(serviceAccountRaw);
      visionClient = new vision.ImageAnnotatorClient({
        credentials: serviceAccount,
        projectId: serviceAccount.project_id
      });
      console.log('✓ Google Cloud Vision API initialized with service account');
      return visionClient;
    } else {
      // Try default credentials
      visionClient = new vision.ImageAnnotatorClient();
      console.log('✓ Google Cloud Vision API initialized with default credentials');
      return visionClient;
    }
  } catch (error) {
    console.warn('⚠ Google Cloud Vision API initialization failed:', error.message);
    return null;
  }
}

/**
 * Initialize Firebase Admin SDK
 */
function initializeFirebaseAdmin() {
  if (firebaseAdmin) {
    return firebaseAdmin;
  }

  try {
    const serviceAccountRaw = process.env.FIREBASE_SERVICE_ACCOUNT || 
                              process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT;
    
    if (serviceAccountRaw) {
      const serviceAccount = JSON.parse(serviceAccountRaw);
      
      if (!admin.apps.length) {
        firebaseAdmin = admin.initializeApp({
          credential: admin.credential.cert(serviceAccount)
        });
        console.log('✓ Firebase Admin SDK initialized');
      } else {
        firebaseAdmin = admin.app();
      }
      return firebaseAdmin;
    } else {
      if (!admin.apps.length) {
        firebaseAdmin = admin.initializeApp();
        console.log('✓ Firebase Admin SDK initialized with default credentials');
      } else {
        firebaseAdmin = admin.app();
      }
      return firebaseAdmin;
    }
  } catch (error) {
    console.warn('⚠ Firebase Admin SDK initialization failed:', error.message);
    return null;
  }
}

/**
 * Get Vision API client (initialize if needed)
 */
function getVisionClient() {
  if (!visionClient) {
    visionClient = initializeVisionClient();
  }
  return visionClient;
}

/**
 * Get Firebase Admin instance (initialize if needed)
 */
function getFirebaseAdmin() {
  if (!firebaseAdmin) {
    firebaseAdmin = initializeFirebaseAdmin();
  }
  return firebaseAdmin;
}

/**
 * Check if Google Cloud services are available
 */
function checkGoogleCloudStatus() {
  return {
    vision: {
      initialized: !!getVisionClient(),
      available: !!visionClient
    },
    firebase: {
      initialized: !!getFirebaseAdmin(),
      available: !!firebaseAdmin
    }
  };
}

module.exports = {
  initializeVisionClient,
  initializeFirebaseAdmin,
  getVisionClient,
  getFirebaseAdmin,
  checkGoogleCloudStatus
};

