// Consolidated OCR API Router
// Handles all OCR-related endpoints in a single function

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
    // Route: /api/ocr/status
    if (route === 'status' && req.method === 'GET') {
      return await handleOCRStatus(req, res);
    }

    // Route: /api/ocr/process (for future OCR processing)
    if (route === 'process' && req.method === 'POST') {
      return await handleOCRProcess(req, res);
    }

    // Route: /api/ocr/health
    if (route === 'health') {
      return res.status(200).json({ status: 'healthy', service: 'ocr-api' });
    }

    // Unknown route
    return res.status(404).json({ 
      success: false, 
      error: `Route not found: ${route}`,
      availableRoutes: ['status', 'process', 'health']
    });

  } catch (error) {
    console.error('OCR API error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Internal server error'
    });
  }
};

// OCR Status Handler
async function handleOCRStatus(req, res) {
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
        try {
          visionClient = new vision.ImageAnnotatorClient({ credentials: serviceAccount });
        } catch (e) {
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

// OCR Process Handler (placeholder for future OCR processing)
async function handleOCRProcess(req, res) {
  return res.status(501).json({
    success: false,
    error: 'OCR processing endpoint coming soon'
  });
}

