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
    // Connect to MongoDB
    if (process.env.MONGODB_URI) {
      await connectDatabase();
    } else {
      console.warn('⚠️ MongoDB URI not set. Database features will be disabled.');
    }
    
    // Start server
    app.listen(PORT, () => {
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
