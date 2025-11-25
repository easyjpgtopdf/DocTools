// Vercel Serverless Function - Cloud Status Check
// Returns comprehensive status of Google Cloud services

// Use CommonJS for Vercel compatibility
module.exports = async function handler(req, res) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ 
      success: false, 
      error: 'Method not allowed. Use GET.' 
    });
  }

  try {
    const { Vision } = require('@google-cloud/vision');
    const admin = require('firebase-admin');

    // Check Vision API
    let visionStatus = {
      active: false,
      method: null,
      error: null
    };

    try {
      let visionClient = null;
      let serviceAccount = null;
      
      if (process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT) {
        serviceAccount = JSON.parse(process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT);
        visionClient = new Vision({ credentials: serviceAccount });
        visionStatus.active = true;
        visionStatus.method = 'GOOGLE_CLOUD_SERVICE_ACCOUNT';
      } else if (process.env.FIREBASE_SERVICE_ACCOUNT) {
        serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
        visionClient = new Vision({ credentials: serviceAccount });
        visionStatus.active = true;
        visionStatus.method = 'FIREBASE_SERVICE_ACCOUNT';
      } else {
        visionStatus.error = 'No service account found';
      }
    } catch (error) {
      visionStatus.error = error.message;
    }

    // Check Storage
    let storageStatus = {
      active: false,
      bucket: null,
      error: null
    };

    try {
      if (admin.apps.length > 0) {
        const bucket = admin.storage().bucket();
        storageStatus.active = true;
        storageStatus.bucket = bucket.name || 'pdf-editor-storage';
      } else {
        // Try to initialize Firebase
        if (process.env.FIREBASE_SERVICE_ACCOUNT) {
          const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
          admin.initializeApp({
            credential: admin.credential.cert(serviceAccount)
          });
          const bucket = admin.storage().bucket();
          storageStatus.active = true;
          storageStatus.bucket = bucket.name || 'pdf-editor-storage';
        } else {
          storageStatus.error = 'Firebase not initialized';
        }
      }
    } catch (error) {
      storageStatus.error = error.message;
    }

    // Check Datastore
    let datastoreStatus = {
      active: false,
      error: null
    };

    try {
      if (admin.apps.length > 0 || process.env.FIREBASE_SERVICE_ACCOUNT) {
        datastoreStatus.active = true;
      } else {
        datastoreStatus.error = 'Firebase not initialized';
      }
    } catch (error) {
      datastoreStatus.error = error.message;
    }

    // Cloud Run status
    const cloudRunStatus = {
      deployed: false,
      url: process.env.CLOUDRUN_SERVICE_URL || null
    };

    return res.status(200).json({
      success: true,
      cloudRun: cloudRunStatus,
      visionApi: visionStatus,
      storage: storageStatus,
      datastore: datastoreStatus,
      projectId: process.env.GOOGLE_CLOUD_PROJECT || 'easyjpgtopdf-de346',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Cloud status check error:', error);
    return res.status(500).json({
      success: false,
      error: 'Status check failed: ' + error.message
    });
  }
}

