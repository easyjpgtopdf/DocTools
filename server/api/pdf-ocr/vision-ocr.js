/**
 * Google Cloud Vision API OCR Integration
 * Converts PDF pages to images and processes with Vision API
 */

const vision = require('@google-cloud/vision');
const { createCanvas } = require('canvas');
const pdfjsLib = require('pdfjs-dist/legacy/build/pdf.js');
const fs = require('fs');
const path = require('path');

// Rate limiting configuration
const RATE_LIMIT = {
  maxRequests: 100, // Max requests per minute
  windowMs: 60000, // 1 minute window
  requests: new Map() // Track requests by IP
};

// Initialize Vision API client
let visionClient = null;

/**
 * Initialize Google Cloud Vision API client
 */
function initializeVisionClient() {
  if (visionClient) {
    return visionClient;
  }

  try {
    const serviceAccountRaw = process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT || 
                              process.env.FIREBASE_SERVICE_ACCOUNT;
    
    if (serviceAccountRaw) {
      const serviceAccount = JSON.parse(serviceAccountRaw);
      visionClient = new vision.ImageAnnotatorClient({
        credentials: serviceAccount
      });
      console.log('✓ Google Cloud Vision API initialized with service account');
    } else {
      // Try default credentials
      visionClient = new vision.ImageAnnotatorClient();
      console.log('✓ Google Cloud Vision API initialized with default credentials');
    }
  } catch (error) {
    console.warn('⚠ Google Cloud Vision API initialization failed:', error.message);
    visionClient = null;
  }

  return visionClient;
}

/**
 * Check rate limit
 */
function checkRateLimit(clientId = 'default') {
  const now = Date.now();
  const clientRequests = RATE_LIMIT.requests.get(clientId) || { count: 0, resetTime: now + RATE_LIMIT.windowMs };

  // Reset if window expired
  if (now > clientRequests.resetTime) {
    clientRequests.count = 0;
    clientRequests.resetTime = now + RATE_LIMIT.windowMs;
  }

  // Check if limit exceeded
  if (clientRequests.count >= RATE_LIMIT.maxRequests) {
    const waitTime = Math.ceil((clientRequests.resetTime - now) / 1000);
    throw new Error(`Rate limit exceeded. Please wait ${waitTime} seconds before trying again.`);
  }

  // Increment counter
  clientRequests.count++;
  RATE_LIMIT.requests.set(clientId, clientRequests);

  return true;
}

/**
 * Convert PDF page to image buffer
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Number} pageIndex - Page index (0-based)
 * @param {Number} scale - Scale factor for image quality (default: 2.0)
 * @returns {Promise<Buffer>} Image buffer (PNG format)
 */
async function convertPdfPageToImage(pdfBuffer, pageIndex, scale = 2.0) {
  try {
    // Load PDF document
    const loadingTask = pdfjsLib.getDocument({
      data: new Uint8Array(pdfBuffer),
      verbosity: 0 // Suppress console warnings
    });
    
    const pdfDocument = await loadingTask.promise;
    const totalPages = pdfDocument.numPages;

    if (pageIndex < 0 || pageIndex >= totalPages) {
      throw new Error(`Invalid page index. PDF has ${totalPages} pages.`);
    }

    // Get page
    const page = await pdfDocument.getPage(pageIndex + 1); // pdfjs uses 1-based indexing

    // Get viewport
    const viewport = page.getViewport({ scale: scale });

    // Create canvas
    const canvas = createCanvas(viewport.width, viewport.height);
    const context = canvas.getContext('2d');

    // Render PDF page to canvas
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    };

    await page.render(renderContext).promise;

    // Convert canvas to PNG buffer
    const imageBuffer = canvas.toBuffer('image/png');

    return imageBuffer;
  } catch (error) {
    console.error('Error converting PDF page to image:', error);
    throw new Error(`Failed to convert PDF page to image: ${error.message}`);
  }
}

/**
 * Map image coordinates to PDF coordinates
 * @param {Number} imageX - X coordinate in image space (top-left origin)
 * @param {Number} imageY - Y coordinate in image space (top-left origin)
 * @param {Number} imageWidth - Image width in pixels
 * @param {Number} imageHeight - Image height in pixels
 * @param {Number} pdfWidth - PDF page width in points
 * @param {Number} pdfHeight - PDF page height in points
 * @returns {Object} PDF coordinates (bottom-left origin)
 */
function mapImageToPDFCoordinates(imageX, imageY, imageWidth, imageHeight, pdfWidth, pdfHeight) {
  // Convert image coordinates (top-left origin) to PDF coordinates (bottom-left origin)
  // Image: (0,0) at top-left, Y increases downward
  // PDF: (0,0) at bottom-left, Y increases upward
  
  // Normalize image coordinates (0-1 range)
  const normalizedX = imageX / imageWidth;
  const normalizedY = 1 - (imageY / imageHeight); // Flip Y axis
  
  // Map to PDF coordinates
  const pdfX = normalizedX * pdfWidth;
  const pdfY = normalizedY * pdfHeight;
  
  return { x: pdfX, y: pdfY };
}

/**
 * Process image with Google Cloud Vision API
 * @param {Buffer} imageBuffer - Image buffer
 * @param {Object} metadata - Image and PDF metadata for coordinate mapping
 * @param {Object} options - OCR options
 * @returns {Promise<Object>} OCR results with text and coordinates
 */
async function processImageWithVision(imageBuffer, metadata, options = {}) {
  if (!visionClient) {
    visionClient = initializeVisionClient();
    if (!visionClient) {
      throw new Error('Google Cloud Vision API not initialized');
    }
  }

  try {
    // Check rate limit
    checkRateLimit(options.clientId);

    // Prepare image for Vision API
    const image = {
      content: imageBuffer
    };

    // Configure request
    const request = {
      image: image,
      imageContext: {
        languageHints: options.languageHints || ['en']
      }
    };

    // Perform text detection
    const [result] = await visionClient.documentTextDetection(request);

    // Extract text and coordinates
    const fullTextAnnotation = result.fullTextAnnotation;
    
    if (!fullTextAnnotation || !fullTextAnnotation.pages || fullTextAnnotation.pages.length === 0) {
      return {
        success: true,
        text: '',
        words: [],
        paragraphs: [],
        blocks: [],
        confidence: 0
      };
    }

    const page = fullTextAnnotation.pages[0];
    const text = fullTextAnnotation.text || '';
    
    // Extract words with coordinates
    const words = [];
    const paragraphs = [];
    const blocks = [];

    if (fullTextAnnotation.pages && fullTextAnnotation.pages.length > 0) {
      const pageData = fullTextAnnotation.pages[0];
      
      // Process blocks
      if (pageData.blocks) {
        pageData.blocks.forEach((block, blockIndex) => {
          const blockText = [];
          const blockWords = [];

          // Process paragraphs in block
          if (block.paragraphs) {
            block.paragraphs.forEach((paragraph, paraIndex) => {
              const paraText = [];
              const paraWords = [];

              // Process words in paragraph
              if (paragraph.words) {
                paragraph.words.forEach((word) => {
                  const wordText = word.symbols
                    ? word.symbols.map(s => s.text).join('')
                    : '';
                  
                  if (wordText.trim()) {
                    const boundingBox = word.boundingBox?.vertices || [];
                    const confidence = word.confidence || 0;

                    // Get bounding box coordinates in image space
                    const imageX = boundingBox[0]?.x || 0;
                    const imageY = boundingBox[0]?.y || 0;
                    const imageWidth = (boundingBox[2]?.x || 0) - (boundingBox[0]?.x || 0);
                    const imageHeight = (boundingBox[2]?.y || 0) - (boundingBox[0]?.y || 0);

                    // Map image coordinates to PDF coordinates
                    const pdfCoords = mapImageToPDFCoordinates(
                      imageX,
                      imageY + imageHeight, // Bottom-left corner of bounding box
                      metadata.imageWidth,
                      metadata.imageHeight,
                      metadata.pdfWidth,
                      metadata.pdfHeight
                    );

                    // Map all vertices
                    const pdfVertices = boundingBox.map(vertex => {
                      const v = mapImageToPDFCoordinates(
                        vertex.x || 0,
                        vertex.y || 0,
                        metadata.imageWidth,
                        metadata.imageHeight,
                        metadata.pdfWidth,
                        metadata.pdfHeight
                      );
                      return v;
                    });

                    const wordData = {
                      text: wordText,
                      // Image coordinates (for reference)
                      imageCoordinates: {
                        x: imageX,
                        y: imageY,
                        width: imageWidth,
                        height: imageHeight,
                        vertices: boundingBox.map(v => ({ x: v.x || 0, y: v.y || 0 }))
                      },
                      // PDF coordinates (primary)
                      pdfCoordinates: {
                        x: pdfCoords.x,
                        y: pdfCoords.y,
                        width: (imageWidth / metadata.imageWidth) * metadata.pdfWidth,
                        height: (imageHeight / metadata.imageHeight) * metadata.pdfHeight,
                        vertices: pdfVertices
                      },
                      confidence: confidence
                    };

                    words.push(wordData);
                    paraWords.push(wordData);
                    paraText.push(wordText);
                  }
                });
              }

              if (paraText.length > 0) {
                paragraphs.push({
                  text: paraText.join(' '),
                  words: paraWords,
                  confidence: paragraph.confidence || 0,
                  boundingBox: paragraph.boundingBox?.vertices || []
                });
                blockText.push(paraText.join(' '));
                blockWords.push(...paraWords);
              }
            });
          }

          if (blockText.length > 0) {
            blocks.push({
              text: blockText.join('\n'),
              words: blockWords,
              confidence: block.confidence || 0,
              boundingBox: block.boundingBox?.vertices || []
            });
          }
        });
      }
    }

    // Calculate average confidence
    const confidences = words.map(w => w.confidence).filter(c => c > 0);
    const avgConfidence = confidences.length > 0
      ? confidences.reduce((a, b) => a + b, 0) / confidences.length
      : 0;

    return {
      success: true,
      text: text,
      words: words,
      paragraphs: paragraphs,
      blocks: blocks,
      confidence: avgConfidence,
      pageWidth: page.width || 0,
      pageHeight: page.height || 0
    };
  } catch (error) {
    console.error('Vision API error:', error);

    // Handle specific Vision API errors with proper error codes
    if (error.code === 8 || error.message.includes('RESOURCE_EXHAUSTED')) {
      const quotaError = new Error('Google Cloud Vision API quota exceeded. Please try again later.');
      quotaError.code = 'QUOTA_EXCEEDED';
      quotaError.statusCode = 429;
      throw quotaError;
    } else if (error.code === 3 || error.message.includes('INVALID_ARGUMENT')) {
      const invalidError = new Error('Invalid image format. Please ensure the PDF page was converted correctly.');
      invalidError.code = 'INVALID_IMAGE';
      invalidError.statusCode = 400;
      throw invalidError;
    } else if (error.code === 16 || error.message.includes('PERMISSION_DENIED')) {
      const permError = new Error('Permission denied. Please check your Google Cloud credentials.');
      permError.code = 'PERMISSION_DENIED';
      permError.statusCode = 403;
      throw permError;
    } else if (error.code === 4 || error.message.includes('DEADLINE_EXCEEDED')) {
      const timeoutError = new Error('OCR processing timed out. Please try again with a smaller page or lower scale.');
      timeoutError.code = 'TIMEOUT';
      timeoutError.statusCode = 504;
      throw timeoutError;
    } else if (error.message && error.message.includes('rate limit')) {
      const rateError = new Error('Rate limit exceeded. Please wait a moment and try again.');
      rateError.code = 'RATE_LIMIT';
      rateError.statusCode = 429;
      throw rateError;
    }

    const apiError = new Error(`Vision API processing failed: ${error.message}`);
    apiError.code = 'VISION_API_ERROR';
    apiError.statusCode = 500;
    throw apiError;
  }
}

/**
 * Perform OCR on PDF page
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Number} pageIndex - Page index (0-based)
 * @param {Object} options - OCR options
 * @returns {Promise<Object>} OCR results
 */
async function performOCR(pdfBuffer, pageIndex, options = {}) {
  try {
    // Validate inputs
    if (!pdfBuffer || pdfBuffer.length === 0) {
      throw new Error('PDF buffer is empty');
    }

    if (pageIndex < 0) {
      throw new Error('Invalid page index. Page index must be 0 or greater.');
    }

    // Convert PDF page to image with error handling
    let conversionResult;
    try {
      conversionResult = await convertPdfPageToImage(
        pdfBuffer,
        pageIndex,
        options.scale || 2.0
      );
    } catch (error) {
      if (error.message.includes('Invalid page index')) {
        throw error;
      }
      throw new Error(`Failed to convert PDF page to image: ${error.message}`);
    }

    // Extract image buffer and metadata
    const { imageBuffer, metadata } = conversionResult;

    // Validate image buffer
    if (!imageBuffer || imageBuffer.length === 0) {
      throw new Error('Failed to generate image from PDF page');
    }

    // Process with Vision API (pass metadata for coordinate mapping)
    const ocrResult = await processImageWithVision(imageBuffer, metadata, {
      languageHints: options.languageHints || ['en'],
      clientId: options.clientId
    });

    return {
      ...ocrResult,
      pageIndex: pageIndex,
      method: 'Google Cloud Vision API',
      imageSize: {
        width: metadata.imageWidth,
        height: metadata.imageHeight,
        format: 'PNG'
      },
      pdfSize: {
        width: metadata.pdfWidth,
        height: metadata.pdfHeight,
        unit: 'points'
      },
      scale: metadata.scale
    };
  } catch (error) {
    console.error('OCR processing error:', error);
    
    // Re-throw with context
    if (error.code && error.statusCode) {
      throw error; // Already a structured error
    }
    
    // Wrap in generic error if needed
    const ocrError = new Error(`OCR processing failed: ${error.message}`);
    ocrError.originalError = error;
    throw ocrError;
  }
}

/**
 * Perform OCR on multiple PDF pages
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array<Number>} pageIndices - Array of page indices (0-based)
 * @param {Object} options - OCR options
 * @returns {Promise<Array<Object>>} Array of OCR results
 */
async function performBatchOCR(pdfBuffer, pageIndices, options = {}) {
  const results = [];
  const errors = [];

  for (const pageIndex of pageIndices) {
    try {
      // Add delay between requests to avoid rate limiting
      if (results.length > 0) {
        await new Promise(resolve => setTimeout(resolve, 100)); // 100ms delay
      }

      const result = await performOCR(pdfBuffer, pageIndex, options);
      results.push(result);
    } catch (error) {
      errors.push({
        pageIndex: pageIndex,
        error: error.message
      });
    }
  }

  return {
    success: errors.length === 0,
    results: results,
    errors: errors,
    totalPages: pageIndices.length,
    processedPages: results.length,
    failedPages: errors.length
  };
}

module.exports = {
  initializeVisionClient,
  convertPdfPageToImage,
  processImageWithVision,
  performOCR,
  performBatchOCR,
  checkRateLimit
};

