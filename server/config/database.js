/**
 * Database Configuration
 * MongoDB connection with connection pooling and optimization
 * SECURITY: Passwords are never logged or exposed
 */

const mongoose = require('mongoose');

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/pdf-editor-enterprise';

// Connection options for performance with better DNS resolution
const options = {
  maxPoolSize: 10, // Maintain up to 10 socket connections
  minPoolSize: 5, // Maintain at least 5 socket connections
  serverSelectionTimeoutMS: 30000, // Increased to 30 seconds for DNS resolution
  socketTimeoutMS: 45000, // Close sockets after 45 seconds of inactivity
  connectTimeoutMS: 30000, // Connection timeout increased
  retryWrites: true,
  w: 'majority',
  // Additional options for better DNS resolution
  directConnection: false, // Use SRV records for mongodb+srv
  tls: true, // Enable TLS for mongodb+srv
  tlsAllowInvalidCertificates: false
};

// Helper function to sanitize URIs (hide passwords)
function sanitizeUri(uri) {
  if (!uri) return '***';
  return uri.replace(/mongodb\+srv:\/\/[^:]+:[^@]+@/g, 'mongodb+srv://***:***@')
            .replace(/mongodb:\/\/[^:]+:[^@]+@/g, 'mongodb://***:***@');
}

// Helper function to sanitize error messages
function sanitizeError(error) {
  if (!error) return error;
  const sanitized = { ...error };
  if (sanitized.message) {
    sanitized.message = sanitizeUri(sanitized.message);
  }
  return sanitized;
}

// Connection event handlers
mongoose.connection.on('connected', () => {
  console.log('✅ MongoDB connected successfully');
});

mongoose.connection.on('error', (err) => {
  // Sanitize error message to hide passwords
  const sanitizedError = sanitizeError(err);
  console.error('❌ MongoDB connection error:', sanitizedError.message || sanitizedError);
});

mongoose.connection.on('disconnected', () => {
  console.warn('⚠️ MongoDB disconnected');
});

// Graceful shutdown
process.on('SIGINT', async () => {
  await mongoose.connection.close();
  console.log('MongoDB connection closed through app termination');
  process.exit(0);
});

/**
 * Connect to MongoDB with retry logic
 * SECURITY: Never logs passwords or sensitive connection details
 */
async function connectDatabase() {
  const maxRetries = 3;
  const retryDelay = 5000; // 5 seconds
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      // Extract cluster info for logging (without password)
      const clusterInfo = MONGODB_URI.includes('@') ? MONGODB_URI.split('@')[1].split('/')[0] : '***';
      
      if (attempt > 1) {
        console.log(`🔄 Retry attempt ${attempt}/${maxRetries} for MongoDB connection...`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      } else {
        console.log('🔌 Attempting MongoDB connection to cluster:', clusterInfo);
      }
      
      // Validate connection string format
      if (!MONGODB_URI.startsWith('mongodb://') && !MONGODB_URI.startsWith('mongodb+srv://')) {
        throw new Error('Invalid MongoDB URI format. Must start with mongodb:// or mongodb+srv://');
      }
      
      // For mongodb+srv, validate format
      if (MONGODB_URI.startsWith('mongodb+srv://')) {
        const uriParts = MONGODB_URI.split('@');
        if (uriParts.length !== 2) {
          throw new Error('Invalid mongodb+srv URI format');
        }
        
        // Verify cluster name format
        const clusterPart = uriParts[1].split('/')[0];
        if (!clusterPart.includes('.mongodb.net')) {
          throw new Error('Invalid cluster name format. Expected: cluster.xxxxx.mongodb.net');
        }
        
        console.log('📡 Using mongodb+srv protocol (SRV record lookup)');
      }
      
      // Attempt connection
      await mongoose.connect(MONGODB_URI, options);
      console.log('✅ Database connection established');
      return mongoose.connection;
      
    } catch (error) {
      // Sanitize error message to hide passwords
      const sanitizedError = sanitizeError(error);
      const errorMessage = sanitizedError.message || sanitizedError.code || 'Unknown error';
      
      console.error(`❌ Database connection attempt ${attempt} failed:`, errorMessage);
      
      // Provide helpful error messages without exposing sensitive data
      if (error.code === 'ENOTFOUND' || (error.message && error.message.includes('ENOTFOUND'))) {
        console.error('💡 DNS Error - Possible causes:');
        console.error('   1. Cluster name incorrect - verify in MongoDB Atlas dashboard');
        console.error('   2. Cluster deleted/renamed - check cluster status');
        console.error('   3. Network DNS issue - SRV record not found');
        
        if (attempt < maxRetries) {
          console.log(`⏳ Waiting ${retryDelay/1000} seconds before retry...`);
          continue;
        } else {
          console.error('❌ All connection attempts failed. Server will continue without database.');
          console.error('💡 To fix: Update MONGODB_URI in Cloud Run with correct cluster name from MongoDB Atlas');
        }
      } else if (error.message && error.message.includes('authentication')) {
        console.error('💡 Authentication Error: Check username and password');
        throw error; // Don't retry auth errors
      } else if (error.message && error.message.includes('timeout')) {
        console.error('💡 Timeout Error: Check network access (0.0.0.0/0) in MongoDB Atlas');
        if (attempt < maxRetries) {
          continue;
        }
      } else {
        // Other errors - retry
        if (attempt < maxRetries) {
          continue;
        }
      }
      
      // If last attempt, throw error (but server will continue)
      if (attempt === maxRetries) {
        throw error;
      }
    }
  }
}

/**
 * Disconnect from MongoDB
 */
async function disconnectDatabase() {
  try {
    await mongoose.connection.close();
    console.log('✅ Database disconnected');
  } catch (error) {
    const sanitizedError = sanitizeError(error);
    console.error('❌ Database disconnection error:', sanitizedError.message || sanitizedError);
    throw error;
  }
}

/**
 * Get database connection status
 */
function getConnectionStatus() {
  return {
    readyState: mongoose.connection.readyState,
    host: mongoose.connection.host ? mongoose.connection.host.replace(/:[^@]+@/g, ':***@') : null,
    name: mongoose.connection.name,
    models: Object.keys(mongoose.models)
  };
}

module.exports = {
  connectDatabase,
  disconnectDatabase,
  getConnectionStatus,
  mongoose
};
