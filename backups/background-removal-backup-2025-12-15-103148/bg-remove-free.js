// Direct route handler for /api/tools/bg-remove-free
// Free Preview Background Removal (512px GPU-accelerated)

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 'https://bg-removal-birefnet-564572183797.us-central1.run.app';

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
    
    // Clean and pad base64
    base64Part = base64Part.replace(/\s+/g, '').replace(/-/g, '+').replace(/_/g, '/');
    if (base64Part.length < 100) {
      return { ok: false, message: 'Image data is too small or corrupted' };
    }
    
    // Pad if needed
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
  let base64Part = trimmed.replace(/\s+/g, '').replace(/-/g, '+').replace(/_/g, '/');
  if (base64Part.length < 100) {
    return { ok: false, message: 'Image data is too small or corrupted' };
  }
  
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
    const { imageData, imageType } = req.body;

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

    console.log('Free preview request received, proxying to Cloud Run...');
    console.log('Cloud Run URL:', CLOUDRUN_API_URL);
    console.log('Image data length:', normalized.dataUrl.length, 'chars');
    console.log('Image data format:', normalized.dataUrl.substring(0, 30) + '...');
    
    // Extract base64 part for validation
    const base64Part = normalized.dataUrl.includes(',') ? normalized.dataUrl.split(',')[1] : normalized.dataUrl;
    console.log('Base64 part length:', base64Part.length, 'chars');
    console.log('Base64 part preview:', base64Part.substring(0, 50) + '...');
    console.log('Decoded bytes:', normalized.bytes);

    // Proxy to Cloud Run backend for free preview (512px)
    const requestPayload = {
      imageData: normalized.dataUrl,
      quality: 'preview',
      maxSize: 512,
      imageType: imageType || null // Forward imageType for proper routing
    };
    
    console.log('Request payload size:', JSON.stringify(requestPayload).length, 'chars');
    
    const response = await fetch(`${CLOUDRUN_API_URL}/api/free-preview-bg`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(requestPayload),
      signal: AbortSignal.timeout(90000) // 90 seconds - balanced timeout for free preview
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
      
      // Log request details for debugging
      console.error('Request details:', {
        url: `${CLOUDRUN_API_URL}/api/free-preview-bg`,
        payloadSize: JSON.stringify(requestPayload).length,
        imageDataLength: normalized.dataUrl.length,
        imageType: imageType
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

