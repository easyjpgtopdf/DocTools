// Direct route handler for /api/tools/bg-remove-free
// Free Preview Background Removal (512px GPU-accelerated)
// CRITICAL: ONLY accepts multipart/form-data (remove.bg style) - base64 JSON completely removed for 100% consistency

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 'https://bg-removal-birefnet-564572183797.us-central1.run.app';

// For multipart/form-data parsing (Vercel serverless functions)
let formidable, FormData;
try {
  formidable = require('formidable');
  FormData = require('form-data');
} catch (e) {
  console.warn('Formidable or form-data not available, multipart upload will use fallback');
}
const fs = require('fs');

// REMOVED: normalizeImageData function - no longer needed as base64 JSON support is removed

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '3600');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      message: 'Only POST method is supported'
    });
  }

  try {
    const contentType = req.headers['content-type'] || '';
    const isMultipart = contentType.includes('multipart/form-data');
    
    // CRITICAL: Free preview ONLY accepts multipart/form-data (remove.bg style)
    // Base64 JSON is completely removed for 100% consistency
    if (!isMultipart) {
      console.error('❌ Free preview requires multipart/form-data upload');
      return res.status(400).json({
        success: false,
        error: 'Invalid request format',
        message: 'Free preview only accepts multipart/form-data upload. Please use FormData to upload your image file.'
      });
    }
    
    // Check if formidable and FormData are available
    if (!formidable || !FormData) {
      console.error('❌ Formidable library not available');
      return res.status(500).json({
        success: false,
        error: 'Server configuration error',
        message: 'Multipart file upload is not available. Please contact support.'
      });
    }
    
    // MULTIPART/FORM-DATA UPLOAD (remove.bg style - ONLY method for free preview)
    console.log('✅ Processing multipart/form-data upload (raw file)');
    
    // Parse multipart request using formidable
    const form = formidable({
      multiples: false,
      maxFileSize: 50 * 1024 * 1024, // 50 MB max
      keepExtensions: true
    });
    
    const [fields, files] = await form.parse(req);
    
    const imageFile = files.image ? (Array.isArray(files.image) ? files.image[0] : files.image) : null;
    const imageType = fields.imageType ? (Array.isArray(fields.imageType) ? fields.imageType[0] : fields.imageType) : null;
    const maxSize = fields.maxSize ? (Array.isArray(fields.maxSize) ? fields.maxSize[0] : fields.maxSize) : '512';
    
    if (!imageFile) {
      return res.status(400).json({
        success: false,
        error: 'Missing image file',
        message: 'No image file provided in multipart request. Please ensure the file field is named "image".'
      });
    }
    
    // Read file buffer
    const fileBuffer = fs.readFileSync(imageFile.filepath);
    
    // Forward as multipart/form-data to backend
    const backendFormData = new FormData();
    backendFormData.append('image', fileBuffer, {
      filename: imageFile.originalFilename || 'image.jpg',
      contentType: imageFile.mimetype || 'image/jpeg'
    });
    backendFormData.append('maxSize', maxSize);
    if (imageType) {
      backendFormData.append('imageType', imageType);
    }
    
    console.log('Forwarding multipart to backend:', {
      fileSize: fileBuffer.length,
      filename: imageFile.originalFilename,
      maxSize: maxSize,
      imageType: imageType
    });
    
    // Clean up temp file
    try {
      fs.unlinkSync(imageFile.filepath);
    } catch (e) {
      console.warn('Failed to delete temp file:', e);
    }
    
    const response = await fetch(`${CLOUDRUN_API_URL}/api/free-preview-bg`, {
      method: 'POST',
      headers: backendFormData.getHeaders(),
      body: backendFormData,
      signal: AbortSignal.timeout(90000)
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorData = {};
      try {
        errorData = JSON.parse(errorText);
      } catch (e) {
        errorData = { error: errorText || `Server error: ${response.status}` };
      }
      
      console.error('❌ Cloud Run Backend Error:', {
        status: response.status,
        statusText: response.statusText,
        error: errorData.error,
        message: errorData.message,
        fullError: errorData,
        errorText: errorText.substring(0, 500) // Limit log size
      });
      
      // Log request details for debugging (multipart path)
      console.error('Request details (multipart path):', {
        url: `${CLOUDRUN_API_URL}/api/free-preview-bg`,
        method: 'multipart/form-data'
      });
      
      // Provide more specific error messages
      let errorMessage = errorData.error || errorData.message || 'Background removal failed';
      let userMessage = errorData.message || errorMessage;
      
      // Handle specific backend errors
      if (errorMessage.includes('bytes-like object') || errorMessage.includes('Image object')) {
        errorMessage = 'Invalid image data format';
        userMessage = 'The image format is not supported. Please try uploading a different image (JPG, PNG, etc.).';
      } else if (errorMessage.includes('Invalid image data')) {
        userMessage = 'Invalid image file. Please ensure you are uploading a valid image file (JPG, PNG, etc.). The image may be corrupted or in an unsupported format.';
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage,
        message: userMessage || 'Background removal failed'
      });
    }

    const result = await response.json();

    if (result.success && result.resultImage) {
      return res.status(200).json({
        success: true,
        resultImage: result.resultImage,
        processedWith: 'Free Preview (512px GPU-accelerated)',
        outputSize: result.outputSize,
        outputSizeMB: result.outputSizeMB
      });
    } else {
      return res.status(500).json({
        success: false,
        error: result.error || 'Processing failed'
      });
    }

  } catch (error) {
    console.error('Free preview processing error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Free preview processing failed'
    });
  }
};

