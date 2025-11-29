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
