/**
 * PDF Editor Backend Server
 * Main server file with Express setup and route configuration
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

// Import configuration
const { initializeVisionClient, initializeFirebaseAdmin, checkGoogleCloudStatus } = require('./config/google-cloud');

// Import routes
const pdfRoutes = require('./routes/pdf');
const pagesRoutes = require('./routes/pages');

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  credentials: true
}));

app.use(express.json({ limit: '100mb' }));
app.use(express.urlencoded({ extended: true, limit: '100mb' }));

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
app.use('/api/pdf', pdfRoutes);
app.use('/api/pdf/pages', pagesRoutes);

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

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Server error:', error);
  
  res.status(error.status || 500).json({
    success: false,
    error: error.message || 'Internal server error',
    ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found',
    path: req.path
  });
});

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

module.exports = app;
