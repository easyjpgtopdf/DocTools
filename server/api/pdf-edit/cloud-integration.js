/**
 * Cloud Integration for PDF Processing
 * Google Cloud Storage, Firebase Storage, etc.
 */

const admin = require('firebase-admin');

/**
 * Save PDF to Google Cloud Storage
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {string} filename - Original filename
 * @returns {Promise<string>} Cloud storage URL
 */
async function saveToGoogleCloud(pdfBuffer, filename) {
  try {
    // Initialize Firebase Storage if available
    if (!admin.apps.length) {
      console.warn('Firebase Admin not initialized, cloud save unavailable');
      return null;
    }
    
    const bucket = admin.storage().bucket();
    const file = bucket.file(`pdf-edits/${Date.now()}-${filename}`);
    
    await file.save(pdfBuffer, {
      metadata: {
        contentType: 'application/pdf',
        cacheControl: 'public, max-age=3600'
      }
    });
    
    // Make file publicly accessible
    await file.makePublic();
    
    const publicUrl = `https://storage.googleapis.com/${bucket.name}/${file.name}`;
    return publicUrl;
  } catch (error) {
    console.error('Google Cloud Storage save error:', error);
    throw new Error(`Cloud save failed: ${error.message}`);
  }
}

/**
 * Save PDF to Firebase Storage
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {string} filename - Original filename
 * @returns {Promise<string>} Firebase storage URL
 */
async function saveToFirebase(pdfBuffer, filename) {
  try {
    if (!admin.apps.length) {
      console.warn('Firebase Admin not initialized');
      return null;
    }
    
    const bucket = admin.storage().bucket();
    const file = bucket.file(`pdf-edits/${Date.now()}-${filename}`);
    
    const stream = file.createWriteStream({
      metadata: {
        contentType: 'application/pdf',
      }
    });
    
    return new Promise((resolve, reject) => {
      stream.on('error', reject);
      stream.on('finish', async () => {
        try {
          await file.makePublic();
          const publicUrl = `https://storage.googleapis.com/${bucket.name}/${file.name}`;
          resolve(publicUrl);
        } catch (e) {
          reject(e);
        }
      });
      stream.end(pdfBuffer);
    });
  } catch (error) {
    console.error('Firebase Storage save error:', error);
    throw new Error(`Firebase save failed: ${error.message}`);
  }
}

module.exports = {
  saveToGoogleCloud,
  saveToFirebase
};

