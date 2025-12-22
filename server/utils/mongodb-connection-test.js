/**
 * MongoDB Connection Test Utility
 * Tests connection without exposing passwords
 */

const mongoose = require('mongoose');

/**
 * Test MongoDB connection
 * Returns connection status without exposing sensitive data
 */
async function testMongoDBConnection(uri) {
  try {
    // Extract cluster info for logging (without password)
    const clusterMatch = uri.match(/@([^/]+)/);
    const clusterInfo = clusterMatch ? clusterMatch[1] : 'unknown';
    
    console.log('🔍 Testing MongoDB connection to:', clusterInfo);
    
    // Test connection with short timeout
    await mongoose.connect(uri, {
      serverSelectionTimeoutMS: 5000,
      connectTimeoutMS: 5000
    });
    
    console.log('✅ MongoDB connection test successful');
    await mongoose.disconnect();
    return { success: true, cluster: clusterInfo };
  } catch (error) {
    const errorInfo = {
      code: error.code,
      message: error.message ? error.message.replace(/mongodb\+srv:\/\/[^:]+:[^@]+@/g, 'mongodb+srv://***:***@') : error.message,
      name: error.name
    };
    
    console.error('❌ MongoDB connection test failed:', errorInfo);
    
    // Provide specific guidance based on error
    if (error.code === 'ENOTFOUND') {
      console.error('💡 DNS Error - Possible causes:');
      console.error('   1. Cluster name is incorrect in connection string');
      console.error('   2. Cluster was deleted or renamed in MongoDB Atlas');
      console.error('   3. Network DNS resolution issue');
      console.error('   → Verify cluster name in MongoDB Atlas dashboard');
    } else if (error.message && error.message.includes('authentication')) {
      console.error('💡 Authentication Error - Check username/password');
    } else if (error.message && error.message.includes('timeout')) {
      console.error('💡 Timeout Error - Check network access (0.0.0.0/0)');
    }
    
    return { success: false, error: errorInfo };
  }
}

module.exports = { testMongoDBConnection };

