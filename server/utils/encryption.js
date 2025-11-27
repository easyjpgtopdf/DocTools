/**
 * Encryption Utility
 * AES-256 encryption for PDF files at rest
 */

const crypto = require('crypto');

const ALGORITHM = 'aes-256-gcm';
const KEY_LENGTH = 32; // 256 bits
const IV_LENGTH = 16; // 128 bits
const SALT_LENGTH = 64;
const TAG_LENGTH = 16;

// Get encryption key from environment or generate one
function getEncryptionKey() {
  const envKey = process.env.ENCRYPTION_KEY;
  if (envKey && envKey.length >= KEY_LENGTH) {
    return Buffer.from(envKey.slice(0, KEY_LENGTH), 'hex');
  }
  
  // Fallback: Use a default key (NOT SECURE for production)
  // In production, always set ENCRYPTION_KEY environment variable
  console.warn('⚠️ Using default encryption key. Set ENCRYPTION_KEY environment variable for production!');
  return crypto.scryptSync('default-key-change-in-production', 'salt', KEY_LENGTH);
}

/**
 * Encrypt data using AES-256-GCM
 * @param {Buffer} data - Data to encrypt
 * @returns {Buffer} Encrypted data with IV and auth tag
 */
function encrypt(data) {
  try {
    const key = getEncryptionKey();
    const iv = crypto.randomBytes(IV_LENGTH);
    const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
    
    const encrypted = Buffer.concat([
      cipher.update(data),
      cipher.final()
    ]);
    
    const authTag = cipher.getAuthTag();
    
    // Combine: IV (16 bytes) + AuthTag (16 bytes) + Encrypted data
    return Buffer.concat([iv, authTag, encrypted]);
  } catch (error) {
    console.error('Encryption error:', error);
    throw new Error('Failed to encrypt data');
  }
}

/**
 * Decrypt data using AES-256-GCM
 * @param {Buffer} encryptedData - Encrypted data with IV and auth tag
 * @returns {Buffer} Decrypted data
 */
function decrypt(encryptedData) {
  try {
    const key = getEncryptionKey();
    
    // Extract IV, auth tag, and encrypted data
    const iv = encryptedData.slice(0, IV_LENGTH);
    const authTag = encryptedData.slice(IV_LENGTH, IV_LENGTH + TAG_LENGTH);
    const encrypted = encryptedData.slice(IV_LENGTH + TAG_LENGTH);
    
    const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
    decipher.setAuthTag(authTag);
    
    const decrypted = Buffer.concat([
      decipher.update(encrypted),
      decipher.final()
    ]);
    
    return decrypted;
  } catch (error) {
    console.error('Decryption error:', error);
    throw new Error('Failed to decrypt data');
  }
}

/**
 * Hash data using SHA-256
 * @param {Buffer|String} data - Data to hash
 * @returns {String} Hex hash
 */
function hash(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

/**
 * Generate HMAC signature
 * @param {String} data - Data to sign
 * @param {String} secret - Secret key
 * @returns {String} HMAC signature
 */
function generateHMAC(data, secret) {
  return crypto.createHmac('sha256', secret).update(data).digest('hex');
}

/**
 * Verify HMAC signature
 * @param {String} data - Original data
 * @param {String} signature - HMAC signature
 * @param {String} secret - Secret key
 * @returns {Boolean} True if signature is valid
 */
function verifyHMAC(data, signature, secret) {
  const expectedSignature = generateHMAC(data, secret);
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

module.exports = {
  encrypt,
  decrypt,
  hash,
  generateHMAC,
  verifyHMAC
};

