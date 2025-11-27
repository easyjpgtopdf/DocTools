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
 * Process image with Google Cloud Vision API
 * @param {Buffer} imageBuffer - Image buffer
 * @param {Object} options - OCR options
 * @returns {Promise<Object>} OCR results with text and coordinates
 */
async function processImageWithVision(imageBuffer, options = {}) {
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

                    const wordData = {
                      text: wordText,
                      boundingBox: {
                        x: boundingBox[0]?.x || 0,
                        y: boundingBox[0]?.y || 0,
                        width: (boundingBox[2]?.x || 0) - (boundingBox[0]?.x || 0),
                        height: (boundingBox[2]?.y || 0) - (boundingBox[0]?.y || 0),
                        vertices: boundingBox.map(v => ({ x: v.x || 0, y: v.y || 0 }))
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

    // Handle specific Vision API errors
    if (error.code === 8) {
      throw new Error('Resource exhausted. Please try again later or reduce image size.');
    } else if (error.code === 3) {
      throw new Error('Invalid image format. Please ensure the PDF page was converted correctly.');
    } else if (error.code === 16) {
      throw new Error('Permission denied. Please check your Google Cloud credentials.');
    } else if (error.message && error.message.includes('rate limit')) {
      throw new Error('Rate limit exceeded. Please wait a moment and try again.');
    }

    throw new Error(`Vision API processing failed: ${error.message}`);
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
    // Convert PDF page to image
    const imageBuffer = await convertPdfPageToImage(
      pdfBuffer,
      pageIndex,
      options.scale || 2.0
    );

    // Process with Vision API
    const ocrResult = await processImageWithVision(imageBuffer, {
      languageHints: options.languageHints || ['en'],
      clientId: options.clientId
    });

    return {
      ...ocrResult,
      pageIndex: pageIndex,
      method: 'Google Cloud Vision API',
      imageSize: {
        width: imageBuffer.length > 0 ? 'converted' : 0,
        format: 'PNG'
      }
    };
  } catch (error) {
    console.error('OCR processing error:', error);
    throw error;
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

