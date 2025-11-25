/**
 * Google Cloud Run Status Check
 * Verifies all Google Cloud services status
 */

const { Vision } = require('@google-cloud/vision');
const admin = require('firebase-admin');

/**
 * Check Google Cloud Vision API status
 */
function checkCloudVisionStatus() {
  try {
    let visionClient = null;
    let serviceAccount = null;
    let method = null;
    
    if (process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT) {
      serviceAccount = JSON.parse(process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT);
      visionClient = new Vision({ credentials: serviceAccount });
      method = 'GOOGLE_CLOUD_SERVICE_ACCOUNT';
    } else if (process.env.FIREBASE_SERVICE_ACCOUNT) {
      serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
      visionClient = new Vision({ credentials: serviceAccount });
      method = 'FIREBASE_SERVICE_ACCOUNT';
    } else if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
      visionClient = new Vision({ keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS });
      method = 'GOOGLE_APPLICATION_CREDENTIALS';
    } else {
      visionClient = new Vision();
      method = 'DEFAULT_CREDENTIALS';
    }
    
    return {
      available: visionClient !== null,
      method: method,
      client: visionClient
    };
  } catch (error) {
    return {
      available: false,
      error: error.message,
      method: null
    };
  }
}

/**
 * Check Google Cloud Storage status
 */
function checkCloudStorageStatus() {
  try {
    if (!admin.apps.length) {
      return {
        available: false,
        error: 'Firebase Admin not initialized'
      };
    }
    
    const bucket = admin.storage().bucket();
    return {
      available: bucket !== null,
      bucketName: bucket.name || 'Not configured'
    };
  } catch (error) {
    return {
      available: false,
      error: error.message
    };
  }
}

/**
 * Check Cloud Run deployment status
 */
function checkCloudRunStatus() {
  const cloudRunUrl = process.env.CLOUDRUN_SERVICE_URL;
  const projectId = process.env.GOOGLE_CLOUD_PROJECT || 'easyjpgtopdf-de346';
  const region = process.env.GOOGLE_CLOUD_REGION || 'us-central1';
  const serviceName = process.env.CLOUDRUN_SERVICE_NAME || 'pdf-editor-server';
  
  return {
    deployed: !!cloudRunUrl,
    serviceUrl: cloudRunUrl,
    projectId: projectId,
    region: region,
    serviceName: serviceName,
    environment: process.env.NODE_ENV || 'development'
  };
}

/**
 * Check Network Egress status
 */
function checkNetworkEgressStatus() {
  // Check if running on Cloud Run
  const isCloudRun = !!process.env.K_SERVICE; // Cloud Run sets this automatically
  const cloudRunUrl = process.env.CLOUDRUN_SERVICE_URL;
  
  return {
    isCloudRun: isCloudRun,
    serviceUrl: cloudRunUrl,
    hasEgress: isCloudRun || !!cloudRunUrl,
    region: process.env.GOOGLE_CLOUD_REGION || 'us-central1'
  };
}

/**
 * Get comprehensive status
 */
function getComprehensiveStatus() {
  const visionStatus = checkCloudVisionStatus();
  const storageStatus = checkCloudStorageStatus();
  const cloudRunStatus = checkCloudRunStatus();
  const networkStatus = checkNetworkEgressStatus();
  
  return {
    timestamp: new Date().toISOString(),
    cloudRun: {
      deployed: cloudRunStatus.deployed,
      serviceUrl: cloudRunStatus.serviceUrl,
      projectId: cloudRunStatus.projectId,
      region: cloudRunStatus.region,
      serviceName: cloudRunStatus.serviceName,
      environment: cloudRunStatus.environment
    },
    cloudVision: {
      available: visionStatus.available,
      method: visionStatus.method,
      error: visionStatus.error || null
    },
    cloudStorage: {
      available: storageStatus.available,
      bucketName: storageStatus.bucketName,
      error: storageStatus.error || null
    },
    networkEgress: {
      isCloudRun: networkStatus.isCloudRun,
      hasEgress: networkStatus.hasEgress,
      serviceUrl: networkStatus.serviceUrl,
      region: networkStatus.region
    },
    summary: {
      allServicesActive: visionStatus.available && storageStatus.available && cloudRunStatus.deployed,
      deploymentStatus: cloudRunStatus.deployed ? 'Deployed on Cloud Run' : 'Not deployed on Cloud Run',
      visionStatus: visionStatus.available ? 'Active' : 'Inactive',
      storageStatus: storageStatus.available ? 'Active' : 'Inactive',
      egressStatus: networkStatus.hasEgress ? 'Active' : 'Inactive'
    }
  };
}

module.exports = {
  checkCloudVisionStatus,
  checkCloudStorageStatus,
  checkCloudRunStatus,
  checkNetworkEgressStatus,
  getComprehensiveStatus
};

