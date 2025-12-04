// Vercel Serverless Function - OCR Status Check
// Returns Google Cloud Vision API status

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
    const vision = require('@google-cloud/vision');

    let statusDetails = {
      active: false,
      method: null,
      error: null
    };

    try {
      let visionClient = null;
      let serviceAccount = null;
      
      if (process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT) {
        serviceAccount = JSON.parse(process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT);
        // Use ImageAnnotatorClient for v4+ or Vision for older versions
        try {
          visionClient = new vision.ImageAnnotatorClient({ credentials: serviceAccount });
        } catch (e) {
          // Fallback for older API versions
          visionClient = new vision.v1.ImageAnnotatorClient({ credentials: serviceAccount });
        }
        statusDetails.active = true;
        statusDetails.method = 'GOOGLE_CLOUD_SERVICE_ACCOUNT';
      } else if (process.env.FIREBASE_SERVICE_ACCOUNT) {
        serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
        try {
          visionClient = new vision.ImageAnnotatorClient({ credentials: serviceAccount });
        } catch (e) {
          visionClient = new vision.v1.ImageAnnotatorClient({ credentials: serviceAccount });
        }
        statusDetails.active = true;
        statusDetails.method = 'FIREBASE_SERVICE_ACCOUNT';
      } else if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
        try {
          visionClient = new vision.ImageAnnotatorClient({ keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS });
        } catch (e) {
          visionClient = new vision.v1.ImageAnnotatorClient({ keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS });
        }
        statusDetails.active = true;
        statusDetails.method = 'GOOGLE_APPLICATION_CREDENTIALS';
      } else {
        try {
          visionClient = new vision.ImageAnnotatorClient();
          statusDetails.active = true;
          statusDetails.method = 'DEFAULT_CREDENTIALS';
        } catch (e) {
          statusDetails.error = 'No credentials found. Set GOOGLE_CLOUD_SERVICE_ACCOUNT environment variable.';
        }
      }
    } catch (error) {
      statusDetails.error = error.message;
    }

    return res.status(200).json({
      success: true,
      ...statusDetails,
      projectId: process.env.GOOGLE_CLOUD_PROJECT || 'easyjpgtopdf-de346',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('OCR status check error:', error);
    return res.status(500).json({
      success: false,
      error: 'Status check failed: ' + error.message
    });
  }
}

