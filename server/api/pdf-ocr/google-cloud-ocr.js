/**
 * Google Cloud Vision API OCR Processing
 * High-accuracy OCR using Google Cloud Vision API
 * Supports multiple languages and provides structured text extraction
 */

const { Vision } = require('@google-cloud/vision');

// Initialize Google Cloud Vision client
let visionClient = null;

try {
  // Try to initialize with service account from environment variable
  // First try GOOGLE_CLOUD_SERVICE_ACCOUNT, then FIREBASE_SERVICE_ACCOUNT (same credentials work for both)
  let serviceAccount = null;
  
  if (process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT) {
    serviceAccount = JSON.parse(process.env.GOOGLE_CLOUD_SERVICE_ACCOUNT);
    console.log('Google Cloud Vision API: Using GOOGLE_CLOUD_SERVICE_ACCOUNT');
  } else if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    // Firebase service account can also be used for Google Cloud Vision API
    serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    console.log('Google Cloud Vision API: Using FIREBASE_SERVICE_ACCOUNT (shared credentials)');
  }
  
  if (serviceAccount) {
    visionClient = new Vision({
      credentials: serviceAccount
    });
    console.log('✓ Google Cloud Vision API initialized with service account');
  } else if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    // Use credentials file path
    visionClient = new Vision({
      keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS
    });
    console.log('✓ Google Cloud Vision API initialized with credentials file');
  } else {
    // Try default credentials (for local development or GCP environment)
    visionClient = new Vision();
    console.log('✓ Google Cloud Vision API initialized with default credentials');
  }
} catch (error) {
  console.warn('⚠ Google Cloud Vision API initialization failed:', error.message);
  console.warn('OCR will fall back to Python Tesseract if available');
}

/**
 * Process image with Google Cloud Vision API OCR
 * @param {string} imageBase64 - Base64 encoded image data
 * @param {string} language - Language code (e.g., 'en', 'hi', 'es')
 * @returns {Promise<Object>} OCR result with text and bounding boxes
 */
async function processOCRWithGoogleCloud(imageBase64, language = 'en') {
  if (!visionClient) {
    throw new Error('Google Cloud Vision API client not initialized. Please set GOOGLE_CLOUD_SERVICE_ACCOUNT or GOOGLE_APPLICATION_CREDENTIALS environment variable.');
  }

  try {
    // Convert base64 to buffer
    const imageBuffer = Buffer.from(imageBase64, 'base64');

    // Prepare image for Vision API
    const image = {
      content: imageBuffer
    };

    // Configure OCR request
    const request = {
      image: image,
      imageContext: {
        languageHints: [language] // Language hint for better accuracy
      }
    };

    // Perform text detection
    const [result] = await visionClient.textDetection(request);
    const detections = result.textAnnotations;

    if (!detections || detections.length === 0) {
      return {
        success: true,
        text: '',
        words: [],
        message: 'No text detected in the image'
      };
    }

    // First element contains the full text
    const fullText = detections[0].description || '';

    // Extract individual words with bounding boxes
    const words = [];
    if (detections.length > 1) {
      for (let i = 1; i < detections.length; i++) {
        const detection = detections[i];
        const vertices = detection.boundingPoly?.vertices || [];
        
        if (vertices.length >= 2) {
          words.push({
            text: detection.description || '',
            boundingBox: {
              x: vertices[0].x || 0,
              y: vertices[0].y || 0,
              width: (vertices[2]?.x || vertices[1]?.x || 0) - (vertices[0].x || 0),
              height: (vertices[2]?.y || vertices[1]?.y || 0) - (vertices[0].y || 0)
            }
          });
        }
      }
    }

    return {
      success: true,
      text: fullText,
      words: words,
      confidence: detections[0].confidence || 1.0,
      language: language
    };

  } catch (error) {
    console.error('Google Cloud Vision API OCR error:', error);
    throw new Error(`OCR processing failed: ${error.message}`);
  }
}

/**
 * Process document text detection (for dense text documents)
 * @param {string} imageBase64 - Base64 encoded image data
 * @param {string} language - Language code
 * @returns {Promise<Object>} OCR result with structured text
 */
async function processDocumentTextDetection(imageBase64, language = 'en') {
  if (!visionClient) {
    throw new Error('Google Cloud Vision API client not initialized.');
  }

  try {
    const imageBuffer = Buffer.from(imageBase64, 'base64');
    const image = { content: imageBuffer };

    const request = {
      image: image,
      imageContext: {
        languageHints: [language]
      }
    };

    // Use document text detection for better structure
    const [result] = await visionClient.documentTextDetection(request);
    const fullTextAnnotation = result.fullTextAnnotation;

    if (!fullTextAnnotation) {
      return {
        success: true,
        text: '',
        words: [],
        blocks: [],
        message: 'No text detected in the document'
      };
    }

    const text = fullTextAnnotation.text || '';
    const words = [];
    const blocks = [];

    // Extract blocks and paragraphs
    if (fullTextAnnotation.pages && fullTextAnnotation.pages.length > 0) {
      fullTextAnnotation.pages.forEach((page, pageIndex) => {
        if (page.blocks) {
          page.blocks.forEach((block, blockIndex) => {
            const blockText = [];
            if (block.paragraphs) {
              block.paragraphs.forEach(paragraph => {
                if (paragraph.words) {
                  paragraph.words.forEach(word => {
                    const wordText = word.symbols
                      .map(s => s.text)
                      .join('');
                    const vertices = word.boundingBox?.vertices || [];
                    
                    words.push({
                      text: wordText,
                      confidence: word.confidence || 0,
                      boundingBox: {
                        x: vertices[0]?.x || 0,
                        y: vertices[0]?.y || 0,
                        width: (vertices[2]?.x || vertices[1]?.x || 0) - (vertices[0]?.x || 0),
                        height: (vertices[2]?.y || vertices[1]?.y || 0) - (vertices[0]?.y || 0)
                      }
                    });
                    blockText.push(wordText);
                  });
                }
              });
            }
            blocks.push({
              index: blockIndex,
              text: blockText.join(' '),
              confidence: block.confidence || 0
            });
          });
        }
      });
    }

    return {
      success: true,
      text: text,
      words: words,
      blocks: blocks,
      confidence: fullTextAnnotation.pages?.[0]?.confidence || 1.0,
      language: language
    };

  } catch (error) {
    console.error('Google Cloud Document Text Detection error:', error);
    throw new Error(`Document text detection failed: ${error.message}`);
  }
}

module.exports = {
  processOCRWithGoogleCloud,
  processDocumentTextDetection,
  isAvailable: () => visionClient !== null
};

