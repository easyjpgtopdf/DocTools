/**
 * Database Configuration
 * MongoDB connection with connection pooling and optimization
 */

const mongoose = require('mongoose');

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/pdf-editor-enterprise';

// Connection options for performance
const options = {
  maxPoolSize: 10, // Maintain up to 10 socket connections
  minPoolSize: 5, // Maintain at least 5 socket connections
  serverSelectionTimeoutMS: 5000, // Keep trying to send operations for 5 seconds
  socketTimeoutMS: 45000, // Close sockets after 45 seconds of inactivity
  bufferMaxEntries: 0, // Disable mongoose buffering
  bufferCommands: false, // Disable mongoose buffering
  useNewUrlParser: true,
  useUnifiedTopology: true
};

// Connection event handlers
mongoose.connection.on('connected', () => {
  console.log('✅ MongoDB connected successfully');
});

mongoose.connection.on('error', (err) => {
  console.error('❌ MongoDB connection error:', err);
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
 * Connect to MongoDB
 */
async function connectDatabase() {
  try {
    await mongoose.connect(MONGODB_URI, options);
    console.log('✅ Database connection established');
    return mongoose.connection;
  } catch (error) {
    console.error('❌ Database connection failed:', error);
    throw error;
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
    console.error('❌ Database disconnection error:', error);
    throw error;
  }
}

/**
 * Get database connection status
 */
function getConnectionStatus() {
  return {
    readyState: mongoose.connection.readyState,
    host: mongoose.connection.host,
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

