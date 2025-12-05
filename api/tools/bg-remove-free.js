// Direct route handler for /api/tools/bg-remove-free
// Free Preview Background Removal (512px GPU-accelerated)

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 'https://bg-removal-ai-564572183797.us-central1.run.app';

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
    const { imageData } = req.body;

    // Validate imageData is present and not empty
    if (!imageData || typeof imageData !== 'string') {
      console.error('Invalid imageData received:', { 
        hasImageData: !!imageData, 
        type: typeof imageData,
        length: imageData?.length 
      });
      return res.status(400).json({
        success: false,
        error: 'Missing or invalid imageData',
        message: 'imageData is required in request body and must be a valid base64 data URL'
      });
    }

    // Validate it's a data URL
    if (!imageData.startsWith('data:image/')) {
      console.error('Invalid image data format:', imageData.substring(0, 50));
      return res.status(400).json({
        success: false,
        error: 'Invalid image format',
        message: 'imageData must be a valid data URL starting with data:image/'
      });
    }

    // Check if base64 part exists
    if (!imageData.includes(',') || imageData.split(',')[1].length < 100) {
      console.error('Incomplete or corrupted image data');
      return res.status(400).json({
        success: false,
        error: 'Incomplete or corrupted image data',
        message: 'Image data appears to be incomplete or corrupted. Please try uploading again.'
      });
    }

    console.log('Free preview request received, proxying to Cloud Run...');
    console.log('Cloud Run URL:', CLOUDRUN_API_URL);
    console.log('Image data length:', imageData.length, 'chars');
    console.log('Image data format:', imageData.substring(0, 30) + '...');
    
    // Extract base64 part for validation
    const base64Part = imageData.includes(',') ? imageData.split(',')[1] : imageData;
    console.log('Base64 part length:', base64Part.length, 'chars');
    console.log('Base64 part preview:', base64Part.substring(0, 50) + '...');

    // Proxy to Cloud Run backend for free preview (512px)
    const requestPayload = {
      imageData: imageData,
      quality: 'preview',
      maxSize: 512
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
      
      console.error('Cloud Run error:', {
        status: response.status,
        statusText: response.statusText,
        error: errorData,
        errorText: errorText
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

