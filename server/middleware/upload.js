/**
 * File Upload Middleware
 * Handles PDF file uploads with validation and storage
 */

const multer = require('multer');
const path = require('path');
const fs = require('fs');

// Ensure uploads directory exists
const uploadsDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Configure storage
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    // Create subdirectory for PDFs
    const pdfDir = path.join(uploadsDir, 'pdfs');
    if (!fs.existsSync(pdfDir)) {
      fs.mkdirSync(pdfDir, { recursive: true });
    }
    cb(null, pdfDir);
  },
  filename: (req, file, cb) => {
    // Generate unique filename
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    const ext = path.extname(file.originalname);
    cb(null, `pdf-${uniqueSuffix}${ext}`);
  }
});

// File filter for PDFs only
const fileFilter = (req, file, cb) => {
  const allowedMimes = ['application/pdf'];
  const allowedExtensions = ['.pdf'];
  
  const isValidMime = allowedMimes.includes(file.mimetype);
  const isValidExtension = allowedExtensions.some(ext => 
    file.originalname.toLowerCase().endsWith(ext)
  );
  
  if (isValidMime || isValidExtension) {
    cb(null, true);
  } else {
    cb(new Error('Only PDF files are allowed!'), false);
  }
};

// Create multer instance
const upload = multer({
  storage: storage,
  limits: {
    fileSize: 100 * 1024 * 1024, // 100MB limit
    files: 1 // Single file only
  },
  fileFilter: fileFilter
});

/**
 * Middleware for single PDF upload
 */
const uploadPDF = upload.single('pdfFile');

/**
 * Middleware for multiple PDF uploads
 */
const uploadMultiplePDFs = upload.array('pdfFiles', 10); // Max 10 files

/**
 * Error handler for upload errors
 */
function handleUploadError(err, req, res, next) {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        error: 'File size exceeds 100MB limit'
      });
    }
    if (err.code === 'LIMIT_FILE_COUNT') {
      return res.status(400).json({
        success: false,
        error: 'Too many files uploaded'
      });
    }
    return res.status(400).json({
      success: false,
      error: 'Upload error: ' + err.message
    });
  }
  
  if (err) {
    return res.status(400).json({
      success: false,
      error: err.message || 'Upload failed'
    });
  }
  
  next();
}

/**
 * Cleanup uploaded file
 */
function cleanupFile(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  } catch (error) {
    console.warn('Failed to cleanup file:', filePath, error.message);
  }
}

/**
 * Cleanup files after delay (for temporary storage)
 */
function scheduleCleanup(filePath, delayMs = 3600000) { // Default: 1 hour
  setTimeout(() => {
    cleanupFile(filePath);
  }, delayMs);
}

module.exports = {
  uploadPDF,
  uploadMultiplePDFs,
  handleUploadError,
  cleanupFile,
  scheduleCleanup
};

