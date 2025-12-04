// Consolidated Cloud Services API Router
// Handles all cloud-related endpoints in a single function

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '3600');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Extract route from query or path
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathParts = url.pathname.split('/').filter(p => p);
  const route = pathParts[pathParts.length - 1] || 'status';

  try {
    // Route: /api/cloud/status
    if (route === 'status' || req.method === 'GET') {
      return await handleCloudStatus(req, res);
    }

    // Route: /api/cloud/health
    if (route === 'health') {
      return res.status(200).json({ status: 'healthy', service: 'cloud-api' });
    }

    // Unknown route
    return res.status(404).json({ 
      success: false, 
      error: `Route not found: ${route}`,
      availableRoutes: ['status', 'health']
    });

  } catch (error) {
    console.error('Cloud API error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Internal server error'
    });
  }
};

// Cloud Status Handler
async function handleCloudStatus(req, res) {
  try {
    const vision = require('@google-cloud/vision');
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
        try {
          visionClient = new vision.ImageAnnotatorClient({ credentials: serviceAccount });
        } catch (e) {
          visionClient = new vision.v1.ImageAnnotatorClient({ credentials: serviceAccount });
        }
        visionStatus.active = true;
        visionStatus.method = 'GOOGLE_CLOUD_SERVICE_ACCOUNT';
      } else if (process.env.FIREBASE_SERVICE_ACCOUNT) {
        serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
        try {
          visionClient = new vision.ImageAnnotatorClient({ credentials: serviceAccount });
        } catch (e) {
          visionClient = new vision.v1.ImageAnnotatorClient({ credentials: serviceAccount });
        }
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
        const serviceAccount = process.env.FIREBASE_SERVICE_ACCOUNT 
          ? JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT) 
          : null;
        const bucketName = serviceAccount?.project_id 
          ? `${serviceAccount.project_id}.appspot.com` 
          : 'pdf-editor-storage';
        const bucket = admin.storage().bucket(bucketName);
        storageStatus.active = true;
        storageStatus.bucket = bucket.name || bucketName;
      } else {
        if (process.env.FIREBASE_SERVICE_ACCOUNT) {
          const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
          const bucketName = serviceAccount.project_id 
            ? `${serviceAccount.project_id}.appspot.com` 
            : 'pdf-editor-storage';
          admin.initializeApp({
            credential: admin.credential.cert(serviceAccount),
            storageBucket: bucketName
          });
          const bucket = admin.storage().bucket(bucketName);
          storageStatus.active = true;
          storageStatus.bucket = bucket.name || bucketName;
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
      url: process.env.CLOUDRUN_SERVICE_URL || process.env.CLOUDRUN_API_URL_BG_REMOVAL || null
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

