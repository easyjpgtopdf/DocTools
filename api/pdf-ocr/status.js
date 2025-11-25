// Vercel Serverless Function - OCR Status Check
// Returns Google Cloud Vision API status

export default async function handler(req, res) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ 
      success: false, 
      error: 'Method not allowed. Use GET.' 
    });
  }

  try {
    const { Vision } = require('@google-cloud/vision');

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
        visionClient = new Vision({ credentials: serviceAccount });
        statusDetails.active = true;
        statusDetails.method = 'GOOGLE_CLOUD_SERVICE_ACCOUNT';
      } else if (process.env.FIREBASE_SERVICE_ACCOUNT) {
        serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
        visionClient = new Vision({ credentials: serviceAccount });
        statusDetails.active = true;
        statusDetails.method = 'FIREBASE_SERVICE_ACCOUNT';
      } else if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
        visionClient = new Vision({ keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS });
        statusDetails.active = true;
        statusDetails.method = 'GOOGLE_APPLICATION_CREDENTIALS';
      } else {
        try {
          visionClient = new Vision();
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

