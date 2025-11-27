/**
 * Error Handler Middleware
 * Provides comprehensive error handling for PDF editing APIs
 */

/**
 * Custom error classes
 */
class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
    this.statusCode = 400;
  }
}

class FileSizeError extends Error {
  constructor(message) {
    super(message);
    this.name = 'FileSizeError';
    this.statusCode = 413;
  }
}

class QuotaExceededError extends Error {
  constructor(message) {
    super(message);
    this.name = 'QuotaExceededError';
    this.statusCode = 429;
  }
}

class PDFCorruptionError extends Error {
  constructor(message) {
    super(message);
    this.name = 'PDFCorruptionError';
    this.statusCode = 422;
  }
}

class NetworkTimeoutError extends Error {
  constructor(message) {
    super(message);
    this.name = 'NetworkTimeoutError';
    this.statusCode = 504;
  }
}

/**
 * Error handler middleware
 */
function errorHandler(error, req, res, next) {
  console.error('API Error:', {
    name: error.name,
    message: error.message,
    stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
    path: req.path,
    method: req.method
  });

  // Handle known error types
  if (error instanceof ValidationError) {
    return res.status(400).json({
      success: false,
      error: 'Validation Error',
      message: error.message,
      code: 'VALIDATION_ERROR'
    });
  }

  if (error instanceof FileSizeError) {
    return res.status(413).json({
      success: false,
      error: 'File Too Large',
      message: error.message,
      code: 'FILE_SIZE_EXCEEDED'
    });
  }

  if (error instanceof QuotaExceededError) {
    return res.status(429).json({
      success: false,
      error: 'Quota Exceeded',
      message: error.message,
      code: 'QUOTA_EXCEEDED'
    });
  }

  if (error instanceof PDFCorruptionError) {
    return res.status(422).json({
      success: false,
      error: 'Invalid PDF File',
      message: error.message,
      code: 'PDF_CORRUPTED'
    });
  }

  if (error instanceof NetworkTimeoutError) {
    return res.status(504).json({
      success: false,
      error: 'Request Timeout',
      message: error.message,
      code: 'NETWORK_TIMEOUT'
    });
  }

  // Handle Google Cloud API errors
  if (error.code === 8 || error.message.includes('RESOURCE_EXHAUSTED')) {
    return res.status(429).json({
      success: false,
      error: 'API Quota Exceeded',
      message: 'Google Cloud Vision API quota has been exceeded. Please try again later.',
      code: 'API_QUOTA_EXCEEDED',
      retryAfter: 3600 // 1 hour
    });
  }

  if (error.code === 3 || error.message.includes('INVALID_ARGUMENT')) {
    return res.status(400).json({
      success: false,
      error: 'Invalid Request',
      message: 'The provided PDF or image is invalid or corrupted.',
      code: 'INVALID_ARGUMENT'
    });
  }

  if (error.code === 16 || error.message.includes('PERMISSION_DENIED')) {
    return res.status(403).json({
      success: false,
      error: 'Permission Denied',
      message: 'Google Cloud Vision API authentication failed. Please check your service account credentials.',
      code: 'PERMISSION_DENIED'
    });
  }

  // Handle PDF-lib errors
  if (error.message.includes('PDF') && error.message.includes('corrupt')) {
    return res.status(422).json({
      success: false,
      error: 'Corrupted PDF',
      message: 'The PDF file appears to be corrupted or invalid. Please try a different file.',
      code: 'PDF_CORRUPTED'
    });
  }

  // Handle network/timeout errors
  if (error.code === 'ETIMEDOUT' || error.code === 'ECONNRESET' || error.message.includes('timeout')) {
    return res.status(504).json({
      success: false,
      error: 'Request Timeout',
      message: 'The request took too long to process. Please try again with a smaller file.',
      code: 'NETWORK_TIMEOUT'
    });
  }

  // Handle multer errors
  if (error.name === 'MulterError') {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(413).json({
        success: false,
        error: 'File Too Large',
        message: 'The uploaded file exceeds the 100MB size limit.',
        code: 'FILE_SIZE_EXCEEDED',
        maxSize: '100MB'
      });
    }
    if (error.code === 'LIMIT_FILE_COUNT') {
      return res.status(400).json({
        success: false,
        error: 'Too Many Files',
        message: 'Only one file can be uploaded at a time.',
        code: 'TOO_MANY_FILES'
      });
    }
  }

  // Default error response
  const statusCode = error.statusCode || error.status || 500;
  const message = process.env.NODE_ENV === 'production' 
    ? 'An error occurred while processing your request. Please try again later.'
    : error.message;

  res.status(statusCode).json({
    success: false,
    error: 'Internal Server Error',
    message: message,
    code: 'INTERNAL_ERROR',
    ...(process.env.NODE_ENV === 'development' && { details: error.message })
  });
}

/**
 * Validate PDF file
 */
async function validatePDF(buffer) {
  // Check if buffer is empty
  if (!buffer || buffer.length === 0) {
    throw new ValidationError('PDF file is empty');
  }

  // Check minimum PDF size (PDF header is at least 4 bytes: %PDF)
  if (buffer.length < 4) {
    throw new PDFCorruptionError('File is too small to be a valid PDF');
  }

  // Check PDF header
  const header = buffer.slice(0, 4).toString('ascii');
  if (header !== '%PDF') {
    throw new PDFCorruptionError('Invalid PDF file format. File does not start with PDF header.');
  }

  // Try to load PDF to verify it's not corrupted
  try {
    const { PDFDocument } = require('pdf-lib');
    await PDFDocument.load(buffer);
  } catch (error) {
    if (error.message.includes('corrupt') || error.message.includes('invalid')) {
      throw new PDFCorruptionError('PDF file appears to be corrupted or invalid');
    }
    throw error;
  }

  return true;
}

/**
 * Validate file size
 */
function validateFileSize(size, maxSize = 100 * 1024 * 1024) {
  if (size > maxSize) {
    const maxSizeMB = (maxSize / 1024 / 1024).toFixed(0);
    const fileSizeMB = (size / 1024 / 1024).toFixed(2);
    throw new FileSizeError(
      `File size (${fileSizeMB}MB) exceeds the maximum allowed size of ${maxSizeMB}MB`
    );
  }
  return true;
}

/**
 * Validate file type
 */
function validateFileType(mimetype, filename) {
  const allowedMimes = ['application/pdf'];
  const allowedExtensions = ['.pdf'];
  
  const isValidMime = allowedMimes.includes(mimetype);
  const isValidExtension = allowedExtensions.some(ext => 
    filename.toLowerCase().endsWith(ext)
  );
  
  if (!isValidMime && !isValidExtension) {
    throw new ValidationError('Invalid file type. Only PDF files are allowed.');
  }
  
  return true;
}

/**
 * Wrap async route handlers with error handling
 */
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

/**
 * Timeout wrapper for long-running operations
 */
function withTimeout(promise, timeoutMs = 30000, errorMessage = 'Operation timed out') {
  return Promise.race([
    promise,
    new Promise((_, reject) => 
      setTimeout(() => reject(new NetworkTimeoutError(errorMessage)), timeoutMs)
    )
  ]);
}

module.exports = {
  errorHandler,
  ValidationError,
  FileSizeError,
  QuotaExceededError,
  PDFCorruptionError,
  NetworkTimeoutError,
  validatePDF,
  validateFileSize,
  validateFileType,
  asyncHandler,
  withTimeout
};

