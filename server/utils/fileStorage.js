/**
 * File Storage Utility
 * Manages temporary file storage with IDs
 */

const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const crypto = require('crypto');

const storageDir = path.join(__dirname, '../storage');
const metadataFile = path.join(storageDir, 'metadata.json');

// Ensure storage directory exists
if (!fs.existsSync(storageDir)) {
  fs.mkdirSync(storageDir, { recursive: true });
}

// Load metadata
let fileMetadata = {};
try {
  if (fs.existsSync(metadataFile)) {
    fileMetadata = JSON.parse(fs.readFileSync(metadataFile, 'utf8'));
  }
} catch (error) {
  console.warn('Could not load file metadata:', error.message);
  fileMetadata = {};
}

/**
 * Save metadata to disk
 */
function saveMetadata() {
  try {
    fs.writeFileSync(metadataFile, JSON.stringify(fileMetadata, null, 2));
  } catch (error) {
    console.error('Failed to save metadata:', error.message);
  }
}

/**
 * Store file and return ID
 * @param {Buffer} fileBuffer - File buffer
 * @param {String} originalName - Original filename
 * @param {String} mimeType - File MIME type
 * @returns {String} File ID
 */
function storeFile(fileBuffer, originalName, mimeType) {
  const fileId = uuidv4();
  const filePath = path.join(storageDir, `${fileId}.pdf`);
  
  // Save file
  fs.writeFileSync(filePath, fileBuffer);
  
  // Store metadata
  fileMetadata[fileId] = {
    id: fileId,
    originalName: originalName,
    mimeType: mimeType,
    size: fileBuffer.length,
    createdAt: new Date().toISOString(),
    lastAccessed: new Date().toISOString(),
    filePath: filePath,
    edits: []
  };
  
  saveMetadata();
  
  return fileId;
}

/**
 * Get file by ID
 * @param {String} fileId - File ID
 * @returns {Object} File data and metadata
 */
function getFile(fileId) {
  if (!fileMetadata[fileId]) {
    throw new Error('File not found');
  }
  
  const metadata = fileMetadata[fileId];
  const filePath = metadata.filePath;
  
  if (!fs.existsSync(filePath)) {
    throw new Error('File no longer exists');
  }
  
  // Update last accessed
  metadata.lastAccessed = new Date().toISOString();
  saveMetadata();
  
  const fileBuffer = fs.readFileSync(filePath);
  
  return {
    buffer: fileBuffer,
    metadata: metadata
  };
}

/**
 * Update file
 * @param {String} fileId - File ID
 * @param {Buffer} fileBuffer - New file buffer
 */
function updateFile(fileId, fileBuffer) {
  if (!fileMetadata[fileId]) {
    throw new Error('File not found');
  }
  
  const metadata = fileMetadata[fileId];
  const filePath = metadata.filePath;
  
  // Update file
  fs.writeFileSync(filePath, fileBuffer);
  
  // Update metadata
  metadata.size = fileBuffer.length;
  metadata.lastAccessed = new Date().toISOString();
  metadata.updatedAt = new Date().toISOString();
  
  saveMetadata();
}

/**
 * Add edit to file history
 * @param {String} fileId - File ID
 * @param {Object} edit - Edit data
 */
function addEdit(fileId, edit) {
  if (!fileMetadata[fileId]) {
    throw new Error('File not found');
  }
  
  const metadata = fileMetadata[fileId];
  if (!metadata.edits) {
    metadata.edits = [];
  }
  
  metadata.edits.push({
    ...edit,
    timestamp: new Date().toISOString()
  });
  
  saveMetadata();
}

/**
 * Get file metadata
 * @param {String} fileId - File ID
 * @returns {Object} File metadata
 */
function getFileMetadata(fileId) {
  if (!fileMetadata[fileId]) {
    throw new Error('File not found');
  }
  
  return fileMetadata[fileId];
}

/**
 * Delete file
 * @param {String} fileId - File ID
 */
function deleteFile(fileId) {
  if (!fileMetadata[fileId]) {
    throw new Error('File not found');
  }
  
  const metadata = fileMetadata[fileId];
  const filePath = metadata.filePath;
  
  // Delete file
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
  }
  
  // Remove from metadata
  delete fileMetadata[fileId];
  saveMetadata();
}

/**
 * Cleanup old files (older than specified hours)
 * @param {Number} hours - Hours to keep files
 */
function cleanupOldFiles(hours = 24) {
  const now = new Date();
  const cutoffTime = now.getTime() - (hours * 60 * 60 * 1000);
  
  const filesToDelete = [];
  
  for (const [fileId, metadata] of Object.entries(fileMetadata)) {
    const lastAccessed = new Date(metadata.lastAccessed).getTime();
    if (lastAccessed < cutoffTime) {
      filesToDelete.push(fileId);
    }
  }
  
  filesToDelete.forEach(fileId => {
    try {
      deleteFile(fileId);
      console.log(`Cleaned up old file: ${fileId}`);
    } catch (error) {
      console.warn(`Failed to cleanup file ${fileId}:`, error.message);
    }
  });
  
  return filesToDelete.length;
}

// Cleanup old files every hour
setInterval(() => {
  cleanupOldFiles(24); // Keep files for 24 hours
}, 60 * 60 * 1000);

module.exports = {
  storeFile,
  getFile,
  updateFile,
  addEdit,
  getFileMetadata,
  deleteFile,
  cleanupOldFiles
};

