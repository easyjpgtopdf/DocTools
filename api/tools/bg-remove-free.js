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

    if (!imageData) {
      return res.status(400).json({
        success: false,
        error: 'Missing imageData',
        message: 'imageData is required in request body'
      });
    }

    console.log('Free preview request received, proxying to Cloud Run...');
    console.log('Cloud Run URL:', CLOUDRUN_API_URL);

    // Proxy to Cloud Run backend for free preview (512px)
    const response = await fetch(`${CLOUDRUN_API_URL}/api/free-preview-bg`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        imageData: imageData,
        quality: 'preview',
        maxSize: 512
      }),
      signal: AbortSignal.timeout(60000) // 60 seconds - optimized for faster free preview
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
        error: errorData
      });
      
      return res.status(response.status).json({
        success: false,
        error: errorData.error || `Server error: ${response.status}`,
        message: errorData.message || 'Background removal failed'
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

