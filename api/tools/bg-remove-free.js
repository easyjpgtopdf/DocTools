// Direct route handler for /api/tools/bg-remove-free
// Free Preview Background Removal (512px GPU-accelerated)
// IMPLEMENTED: multipart/form-data upload (remove.bg style) + base64 JSON fallback

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

function normalizeImageData(imageData) {
  if (!imageData || typeof imageData !== 'string') {
    return { ok: false, message: 'imageData is required and must be a string' };
  }

  const trimmed = imageData.trim();
  
  // Check if it's already a data URL
  if (trimmed.startsWith('data:')) {
    // It's already a valid data URL, check format
    const match = trimmed.match(/^data:(image\/[a-zA-Z0-9.+-]+);base64,(.+)$/);
    if (!match) {
      return { ok: false, message: 'imageData must be a base64 data URL (data:image/...;base64,...)' };
    }
    
    const mime = match[1];
    let base64Part = match[2];
    
    // Enhanced base64 cleaning and validation
    // Remove all whitespace, fix URL-safe variants, remove invalid characters
    base64Part = base64Part.replace(/\s+/g, '').replace(/-/g, '+').replace(/_/g, '/');
    
    // Remove any non-base64 characters that might have crept in
    base64Part = base64Part.replace(/[^A-Za-z0-9+/=]/g, '');
    
    if (base64Part.length < 100) {
      return { ok: false, message: 'Image data is too small or corrupted. Please upload a valid image file.' };
    }
    
    // Pad if needed (base64 must be multiple of 4)
    const remainder = base64Part.length % 4;
    if (remainder) {
      base64Part = base64Part.padEnd(base64Part.length + (4 - remainder), '=');
    }

    // Validate base64
    let buffer;
    try {
      buffer = Buffer.from(base64Part, 'base64');
      if (!buffer || buffer.length === 0) {
        return { ok: false, message: 'Decoded image is empty' };
      }
    } catch (err) {
      return { ok: false, message: `Invalid base64 encoding: ${err.message}` };
    }

    // Return properly padded data URL to ensure backend can decode it
    return {
      ok: true,
      mime,
      bytes: buffer.length,
      dataUrl: `data:${mime};base64,${base64Part}` // Return properly padded version
    };
  }
  
  // If not a data URL, treat as raw base64
  // Enhanced cleaning and validation
  let base64Part = trimmed.replace(/\s+/g, '').replace(/-/g, '+').replace(/_/g, '/');
  
  // Remove any non-base64 characters
  base64Part = base64Part.replace(/[^A-Za-z0-9+/=]/g, '');
  
  if (base64Part.length < 100) {
    return { ok: false, message: 'Image data is too small or corrupted. Please upload a valid image file.' };
  }
  
  // Pad if needed (base64 must be multiple of 4)
  const remainder = base64Part.length % 4;
  if (remainder) {
    base64Part = base64Part.padEnd(base64Part.length + (4 - remainder), '=');
  }

  let buffer;
  try {
    buffer = Buffer.from(base64Part, 'base64');
    if (!buffer || buffer.length === 0) {
      return { ok: false, message: 'Decoded image is empty' };
    }
  } catch (err) {
    return { ok: false, message: `Invalid base64 encoding: ${err.message}` };
  }

  return {
    ok: true,
    mime: 'image/png',
    bytes: buffer.length,
    dataUrl: `data:image/png;base64,${base64Part}`
  };
}

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
    
    let response;
    
    if (isMultipart && formidable && FormData) {
      // MULTIPART/FORM-DATA UPLOAD (remove.bg style - preferred method)
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
          message: 'No image file provided in multipart request.'
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
      
      response = await fetch(`${CLOUDRUN_API_URL}/api/free-preview-bg`, {
        method: 'POST',
        headers: backendFormData.getHeaders(),
        body: backendFormData,
        signal: AbortSignal.timeout(90000)
      });
      
    } else {
      // FALLBACK: Base64 JSON (backward compatibility)
      console.log('⚠️ Processing base64 JSON upload (fallback mode)');
      
      const { imageData, imageType } = req.body || {};
      
      if (!imageData) {
        return res.status(400).json({
          success: false,
          error: 'Missing imageData',
          message: 'No image data provided in request body'
        });
      }

      // Validate and normalize image data before proxying
      const normalized = normalizeImageData(imageData);
      if (!normalized.ok) {
        console.error('Invalid imageData received:', {
          hasImageData: !!imageData,
          type: typeof imageData,
          length: imageData?.length,
          reason: normalized.message
        });
        return res.status(400).json({
          success: false,
          error: 'Invalid image data',
          message: normalized.message
        });
      }

      console.log('Free preview request received (base64), proxying to Cloud Run...');
      console.log('Cloud Run URL:', CLOUDRUN_API_URL);
      console.log('Image data length:', normalized.dataUrl.length, 'chars');
      
      // Proxy to Cloud Run backend for free preview (512px)
      // Backend accepts both multipart/form-data AND base64 JSON (backward compatible)
      const requestPayload = {
        imageData: normalized.dataUrl,
        quality: 'preview',
        maxSize: 512,
        imageType: imageType || null
      };
      
      response = await fetch(`${CLOUDRUN_API_URL}/api/free-preview-bg`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestPayload),
        signal: AbortSignal.timeout(90000)
      });
    }

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
      
      // Log request details for debugging (only if requestPayload exists - base64 path)
      if (typeof requestPayload !== 'undefined') {
        console.error('Request details (base64 path):', {
          url: `${CLOUDRUN_API_URL}/api/free-preview-bg`,
          payloadSize: JSON.stringify(requestPayload).length,
          imageDataLength: normalized?.dataUrl?.length || 'N/A',
          imageType: imageType
        });
      } else {
        console.error('Request details (multipart path):', {
          url: `${CLOUDRUN_API_URL}/api/free-preview-bg`,
          method: 'multipart/form-data'
        });
      }
      
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

