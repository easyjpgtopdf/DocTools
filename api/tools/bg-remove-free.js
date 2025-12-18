// Direct route handler for /api/tools/bg-remove-free
// Free Preview Background Removal (512px GPU-accelerated)
// CRITICAL: ONLY accepts multipart/form-data - base64 JSON completely removed for 100% consistency

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 'https://bg-removal-ai-564572183797.us-central1.run.app';

// For multipart/form-data parsing (Vercel serverless functions)
let formidable, FormData;
try {
  // Formidable v3+ uses default export, handle both CommonJS and ES module syntax
  const formidableModule = require('formidable');
  formidable = formidableModule.default || formidableModule.formidable || formidableModule;
  FormData = require('form-data');
} catch (e) {
  console.warn('Formidable or form-data not available, multipart upload will use fallback:', e);
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
    
    // CRITICAL: Free preview ONLY accepts multipart/form-data
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
    if (!formidable || typeof formidable !== 'function' && typeof formidable !== 'object') {
      console.error('❌ Formidable library not available or not a function', {
        formidable: typeof formidable,
        FormData: typeof FormData
      });
      return res.status(500).json({
        success: false,
        error: 'Server configuration error',
        message: 'Multipart file upload is not available. Please contact support.'
      });
    }
    
    // MULTIPART/FORM-DATA UPLOAD (ONLY method for free preview)
    console.log('✅ Processing multipart/form-data upload (raw file)');
    
    // Parse multipart request using formidable
    // Handle both v2 and v3 API
    let fields, files;
    try {
      // Free version upload limit: 500 KB (512000 bytes)
      const MAX_FILE_SIZE_FREE = 500 * 1024; // 500 KB
      
      // Try v3 first (formidable is an object with IncomingForm)
      if (formidable && formidable.IncomingForm) {
        const form = formidable.IncomingForm({
          multiples: false,
          maxFileSize: MAX_FILE_SIZE_FREE,
          keepExtensions: true
        });
        [fields, files] = await form.parse(req);
      } else if (typeof formidable === 'function') {
        // Formidable v2 style - direct function call
        const form = formidable({
          multiples: false,
          maxFileSize: MAX_FILE_SIZE_FREE,
          keepExtensions: true
        });
        [fields, files] = await form.parse(req);
      } else {
        // Last resort - try as constructor
        const Form = formidable.default || formidable;
        const form = typeof Form === 'function' ? Form({
          multiples: false,
          maxFileSize: MAX_FILE_SIZE_FREE,
          keepExtensions: true
        }) : new Form({
          multiples: false,
          maxFileSize: MAX_FILE_SIZE_FREE,
          keepExtensions: true
        });
        [fields, files] = await form.parse(req);
      }
    } catch (parseError) {
      console.error('❌ Formidable parse error:', parseError);
      // Try alternative: re-require and use directly
      try {
        const formidableAlt = require('formidable');
        // Try IncomingForm if available
        const IncomingForm = formidableAlt.IncomingForm || formidableAlt.default?.IncomingForm;
        if (IncomingForm) {
          const form = IncomingForm({
            multiples: false,
            maxFileSize: 500 * 1024, // 500 KB for free version
            keepExtensions: true
          });
          [fields, files] = await form.parse(req);
        } else {
          throw new Error('IncomingForm not found in formidable module');
        }
      } catch (altError) {
        console.error('❌ Alternative formidable parse also failed:', altError);
        return res.status(500).json({
          success: false,
          error: 'Failed to parse multipart request',
          message: 'Server configuration error. Please contact support.'
        });
      }
    }
    
    const imageFile = files.image ? (Array.isArray(files.image) ? files.image[0] : files.image) : null;
    const imageType = fields.imageType ? (Array.isArray(fields.imageType) ? fields.imageType[0] : fields.imageType) : null;
    const maxSize = fields.maxSize ? (Array.isArray(fields.maxSize) ? fields.maxSize[0] : fields.maxSize) : '640'; // FIX 1: Default updated to 640px
    
    if (!imageFile) {
      return res.status(400).json({
        success: false,
        error: 'Missing image file',
        message: 'No image file provided in multipart request. Please ensure the file field is named "image".'
      });
    }
    
    // Read file buffer
    const fileBuffer = fs.readFileSync(imageFile.filepath);
    
    // Validate file size: Free version limit is 500 KB
    const MAX_FILE_SIZE_FREE = 500 * 1024; // 500 KB in bytes
    if (fileBuffer.length > MAX_FILE_SIZE_FREE) {
      const fileSizeMB = (fileBuffer.length / (1024 * 1024)).toFixed(2);
      return res.status(400).json({
        success: false,
        error: 'File size exceeds limit',
        message: `File size (${fileSizeMB} MB) exceeds the free version limit of 500 KB. Please compress your image or use Premium HD for larger files.`
      });
    }
    
    // Forward as multipart/form-data to backend
    // CRITICAL: Use form-data package correctly with Node.js fetch
    const backendFormData = new FormData();
    backendFormData.append('image', fileBuffer, {
      filename: imageFile.originalFilename || 'image.jpg',
      contentType: imageFile.mimetype || 'image/jpeg'
    });
    backendFormData.append('maxSize', maxSize);
    if (imageType) {
      backendFormData.append('imageType', imageType);
    }
    
    // Get headers from form-data (includes Content-Type with boundary)
    const formHeaders = backendFormData.getHeaders();
    
    console.log('📤 Forwarding multipart to backend:', {
      url: `${CLOUDRUN_API_URL}/api/free-preview-bg`,
      fileSize: fileBuffer.length,
      filename: imageFile.originalFilename,
      maxSize: maxSize,
      imageType: imageType,
      contentType: formHeaders['content-type'] || 'not-set',
      headers: Object.keys(formHeaders),
      allHeaders: formHeaders
    });
    
    // Clean up temp file
    try {
      fs.unlinkSync(imageFile.filepath);
    } catch (e) {
      console.warn('Failed to delete temp file:', e);
    }
    
    // Verify headers before sending
    if (!formHeaders['content-type'] || !formHeaders['content-type'].includes('multipart/form-data')) {
      console.error('❌ FormData headers missing Content-Type:', formHeaders);
      return res.status(500).json({
        success: false,
        error: 'Server configuration error',
        message: 'Failed to prepare multipart request headers'
      });
    }
    
    // CRITICAL FIX: Node.js fetch with form-data package
    // form-data package's FormData is a readable stream - convert to buffer properly
    const contentTypeWithBoundary = formHeaders['content-type'];
    console.log('📋 Content-Type with boundary:', contentTypeWithBoundary);
    
    // Convert form-data stream to buffer using proper stream reading
    // form-data FormData is a readable stream, but not directly async iterable
    // We need to collect chunks using stream events
    // CRITICAL: Ensure all chunks are Buffers (form-data may emit strings for boundaries)
    const chunks = [];
    await new Promise((resolve, reject) => {
      backendFormData.on('data', (chunk) => {
        // Convert string chunks to Buffer (form-data may emit strings for multipart boundaries)
        if (typeof chunk === 'string') {
          chunks.push(Buffer.from(chunk, 'utf8'));
        } else if (Buffer.isBuffer(chunk)) {
          chunks.push(chunk);
        } else if (chunk instanceof Uint8Array) {
          chunks.push(Buffer.from(chunk));
        } else {
          // Fallback: convert to string then to buffer
          chunks.push(Buffer.from(String(chunk), 'utf8'));
        }
      });
      backendFormData.on('end', () => {
        resolve();
      });
      backendFormData.on('error', (err) => {
        reject(err);
      });
      // Ensure stream starts reading
      backendFormData.resume();
    });
    
    // Verify all chunks are Buffers before concatenating
    if (chunks.length === 0) {
      throw new Error('No data chunks collected from form-data stream');
    }
    
    const formDataBuffer = Buffer.concat(chunks);
    
    console.log('📤 FormData converted to buffer:', {
      bufferSize: formDataBuffer.length,
      contentType: contentTypeWithBoundary
    });
    
    // Send buffer with proper Content-Type header (includes boundary)
    const response = await fetch(`${CLOUDRUN_API_URL}/api/free-preview-bg`, {
      method: 'POST',
      headers: {
        'Content-Type': contentTypeWithBoundary
      },
      body: formDataBuffer,
      signal: AbortSignal.timeout(90000)
    });
    
    console.log('📥 Backend response received:', {
      status: response.status,
      statusText: response.statusText,
      contentType: response.headers.get('content-type')
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

