/**
 * PDF Editor Backend Server
 * Main server file with Express setup and route configuration
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const path = require('path');
const fs = require('fs');

// Import database configuration
const { connectDatabase } = require('./config/database');

// Import configuration
const { initializeVisionClient, initializeFirebaseAdmin, checkGoogleCloudStatus } = require('./config/google-cloud');

// Import security middleware
const { securityHeaders, securityMonitoring } = require('./middleware/security');

// Import routes
const pdfRoutes = require('./routes/pdf');
const pagesRoutes = require('./routes/pages');
const authRoutes = require('./routes/auth');
const subscriptionRoutes = require('./routes/subscription');
const razorpayRoutes = require('./routes/razorpayRoutes');
const deviceRoutes = require('./routes/device');
const creditRoutes = require('./routes/credits');
const razorpayController = require('./controllers/razorpayController');
// Note: analyticsRoutes will be added when analytics module is ready

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware (must be first)
app.use(securityHeaders());
app.use(securityMonitoring);

// CORS middleware
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  credentials: true
}));

// Body parsing middleware
app.use(express.json({ limit: '100mb' }));
app.use(express.urlencoded({ extended: true, limit: '100mb' }));
app.use(cookieParser());

// Serve static files
app.use(express.static('public'));
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));
app.use('/previews', express.static(path.join(__dirname, 'previews')));
app.use('/converted', express.static(path.join(__dirname, 'converted')));

// Initialize Google Cloud services
console.log('\n' + '='.repeat(50));
console.log('Initializing Google Cloud Services...');
console.log('='.repeat(50));

try {
  initializeVisionClient();
  initializeFirebaseAdmin();
  
  const status = checkGoogleCloudStatus();
  console.log('Vision API:', status.vision.initialized ? '✓ Initialized' : '✗ Not initialized');
  console.log('Firebase Admin:', status.firebase.initialized ? '✓ Initialized' : '✗ Not initialized');
} catch (error) {
  console.warn('⚠ Google Cloud services initialization warning:', error.message);
}

console.log('='.repeat(50) + '\n');

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/subscription', subscriptionRoutes);
app.use('/api/pdf', pdfRoutes);
app.use('/api/pdf/pages', pagesRoutes);
app.use('/api/razorpay', razorpayRoutes);
app.use('/api/device', deviceRoutes);
app.use('/api/credits', creditRoutes);

// Donation endpoint (for index.html donate button)
app.options('/api/create-order', (req, res) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.status(200).end();
});

app.post('/api/create-order', (req, res) => {
  // CORS headers
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  razorpayController.createOrder(req, res);
});

// Background removal proxy endpoints (to avoid CORS issues)
const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL || 'https://bg-remover-api-iwumaktavq-uc.a.run.app';

// BiRefNet Background Removal Service URL (GPU-accelerated)
const CLOUDRUN_API_URL_BG_REMOVAL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 
                                     'https://bg-removal-birefnet-564572183797.us-central1.run.app';

app.post('/api/background-remove', async (req, res) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180000); // 3 minutes
  
  try {
    const { imageData } = req.body;
    
    if (!imageData) {
      clearTimeout(timeout);
      return res.status(400).json({ 
        success: false, 
        error: 'No imageData provided' 
      });
    }

    // Forward request to Cloud Run API
    const backendUrl = `${CLOUDRUN_API_URL}/remove-background`;
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ imageData }),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Backend error: ${response.status}`;
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch (e) {
        errorMessage = errorText || errorMessage;
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage
      });
    }

    const result = await response.json();
    res.json(result);
    
  } catch (error) {
    clearTimeout(timeout);
    console.error('Background removal proxy error:', error);
    
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      return res.status(504).json({
        success: false,
        error: 'Request timeout. The image might be too large or the server is busy.'
      });
    }
    
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to process background removal request'
    });
  }
});

// Health check for background removal service
app.get('/api/background-remove/health', async (req, res) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000); // 5 seconds for health check
  
  try {
    const backendUrl = `${CLOUDRUN_API_URL}/health`;
    const response = await fetch(backendUrl, {
      method: 'GET',
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    
    if (response.ok) {
      const data = await response.json();
      res.json({ ...data, proxy: 'working' });
    } else {
      res.status(response.status).json({
        status: 'unhealthy',
        error: `Backend returned status ${response.status}`
      });
    }
  } catch (error) {
    clearTimeout(timeout);
    res.status(503).json({
      status: 'unhealthy',
      error: error.message || 'Backend service unavailable'
    });
  }
});

// ============================================
// BiRefNet Background Removal Proxy
// ============================================

// POST /api/premium-bg - Premium HD Background Removal (Enterprise Pipeline)
app.post('/api/premium-bg', async (req, res) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 300000); // 5 minutes for premium processing
  
  try {
    // Verify authentication token and extract userId
    const authHeader = req.headers.authorization;
    let verifiedUserId = null;
    
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.replace('Bearer ', '');
      
      // Try to verify Firebase token if Firebase Admin is available
      try {
        const { getFirebaseAdmin } = require('./config/google-cloud');
        const firebaseAdmin = getFirebaseAdmin();
        
        if (firebaseAdmin && firebaseAdmin.apps.length > 0) {
          const decodedToken = await firebaseAdmin.auth().verifyIdToken(token);
          verifiedUserId = decodedToken.uid;
          console.log(`✅ Verified Firebase token for user: ${verifiedUserId}`);
        }
      } catch (firebaseError) {
        // If Firebase Admin not available or token invalid, continue with token from body
        console.warn('Firebase token verification failed (may not be configured):', firebaseError.message);
      }
    }
    
    // If userId not verified from token, use from request body (fallback)
    const requestBody = { ...req.body };
    if (verifiedUserId && !requestBody.userId) {
      requestBody.userId = verifiedUserId;
    }
    
    // Forward request to Cloud Run BiRefNet API
    const backendUrl = `${CLOUDRUN_API_URL_BG_REMOVAL}/api/premium-bg`;
    
    // Forward headers (especially Authorization)
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    
    if (req.headers.authorization) {
      headers['Authorization'] = req.headers.authorization;
    }
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestBody),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Backend error: ${response.status}`;
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch (e) {
        errorMessage = errorText || errorMessage;
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage
      });
    }

    const result = await response.json();
    res.json(result);
    
  } catch (error) {
    clearTimeout(timeout);
    console.error('Premium BG removal proxy error:', error);
    
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      return res.status(504).json({
        success: false,
        error: 'Request timeout. The image might be too large or the server is busy.'
      });
    }
    
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to process premium background removal request'
    });
  }
});

// POST /api/background-remove-birefnet - Process image (using BiRefNet backend)
app.post('/api/background-remove-birefnet', async (req, res) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180000); // 3 minutes
  
  try {
    const { imageData } = req.body;
    
    if (!imageData) {
      clearTimeout(timeout);
      return res.status(400).json({ 
        success: false, 
        error: 'No imageData provided' 
      });
    }

    // Get headers from request to forward to backend
    const userHeaders = {};
    if (req.headers['x-user-id']) userHeaders['X-User-ID'] = req.headers['x-user-id'];
    if (req.headers['x-user-type']) userHeaders['X-User-Type'] = req.headers['x-user-type'];
    if (req.headers['x-device-id']) userHeaders['X-Device-ID'] = req.headers['x-device-id'];
    if (req.headers['x-auth-token']) userHeaders['X-Auth-Token'] = req.headers['x-auth-token'];

    // Forward request to BiRefNet Cloud Run API (free preview endpoint)
    const backendUrl = `${CLOUDRUN_API_URL_BG_REMOVAL}/api/free-preview-bg`;
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...userHeaders
      },
      body: JSON.stringify({ 
        imageData,
        maxSize: 512,
        quality: 'preview'
      }),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Backend error: ${response.status}`;
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch (e) {
        errorMessage = errorText || errorMessage;
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage
      });
    }

    const result = await response.json();
    // Adapt response format if needed
    if (result.success !== undefined) {
      res.json(result);
    } else {
      // Convert BiRefNet response to expected format
      res.json({
        success: true,
        resultImage: result.resultImage || result.imageData || result.data,
        processedWith: 'birefnet',
        ...result
      });
    }
    
  } catch (error) {
    clearTimeout(timeout);
    console.error('Background removal proxy error:', error);
    
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      return res.status(504).json({
        success: false,
        error: 'Request timeout. The image might be too large or the server is busy.'
      });
    }
    
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to process background removal request'
    });
  }
});

// GET /api/background-remove-birefnet/health - Health check
app.get('/api/background-remove-birefnet/health', async (req, res) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000); // 5 seconds for health check
  
  try {
    const backendUrl = `${CLOUDRUN_API_URL_BG_REMOVAL}/health`;
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      },
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    
    if (response.ok) {
      const data = await response.json();
      res.json({ ...data, proxy: 'working', model: 'birefnet' });
    } else {
      res.status(response.status).json({
        status: 'unhealthy',
        error: `Backend returned status ${response.status}`
      });
    }
  } catch (error) {
    clearTimeout(timeout);
    res.status(503).json({
      status: 'unhealthy',
      error: error.message || 'Backend service unavailable'
    });
  }
});

// Admin endpoint to add test credits (SECURE - should add admin auth in production)
// const addTestCreditsHandler = require('../api/admin/add-test-credits.js'); // File not found - commented out
// app.post('/api/admin/add-test-credits', addTestCreditsHandler);

// GET /api/background-remove-birefnet/usage - Usage statistics (stub endpoint)
app.get('/api/background-remove-birefnet/usage', async (req, res) => {
  // BiRefNet doesn't have a usage endpoint, return default values
  res.json({
    userId: req.headers['x-user-id'] || 'anonymous',
    userType: req.headers['x-user-type'] || 'free',
    deviceId: req.headers['x-device-id'] || 'unknown',
    imageCount: 0,
    imageLimit: -1,
    uploadBytes: 0,
    uploadLimit: 'infinity',
    downloadBytes: 0,
    downloadLimit: 'infinity',
    remainingUploadMB: 'infinity',
    remainingDownloadMB: 'infinity'
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'PDF Editor Backend',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: '/health',
      pdf: '/api/pdf',
      pages: '/api/pdf/pages'
    }
  });
});

// Import error handler
const { errorHandler } = require('./middleware/errorHandler');

// Error handling middleware (must be last)
app.use(errorHandler);

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found',
    path: req.path
  });
});

// Initialize database and start server
async function startServer() {
  try {
    // Connect to MongoDB (non-blocking - don't fail server if DB connection fails)
    if (process.env.MONGODB_URI) {
      try {
        await connectDatabase();
      } catch (dbError) {
        // Sanitize error message to hide passwords
        const sanitizedMessage = dbError.message ? dbError.message.replace(/mongodb\+srv:\/\/[^:]+:[^@]+@/g, 'mongodb+srv://***:***@') : dbError.message;
        console.error('⚠️ MongoDB connection failed, but continuing server startup:', sanitizedMessage);
        console.warn('⚠️ Database features will be disabled until connection is restored.');
        console.warn('💡 Check: 1) MongoDB Atlas cluster name, 2) Network access (0.0.0.0/0), 3) Connection string format');
      }
    } else {
      console.warn('⚠️ MongoDB URI not set. Database features will be disabled.');
    }
    
    // Start server - listen on 0.0.0.0 for Cloud Run
    app.listen(PORT, '0.0.0.0', () => {
      console.log('\n' + '='.repeat(50));
      console.log('PDF Editor Backend Server');
      console.log('='.repeat(50));
      console.log(`Server running on port ${PORT}`);
      console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
      console.log(`Health check: http://localhost:${PORT}/health`);
      console.log(`API base: http://localhost:${PORT}/api`);
      console.log('='.repeat(50) + '\n');
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Start the server
startServer();

module.exports = app;
