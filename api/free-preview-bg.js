// Vercel Serverless Function - Free Preview Background Removal (512px GPU-accelerated)
// Proxies requests to Google Cloud Run backend for 512px preview

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 'https://bg-removal-birefnet-564572183797.us-central1.run.app';

export default async function handler(req, res) {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.setHeader('Access-Control-Max-Age', '3600');
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(405).json({
      success: false,
      error: 'Method not allowed',
      message: 'Only POST method is supported'
    });
  }

  try {
    const { imageData } = req.body;

    if (!imageData) {
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(400).json({
        success: false,
        error: 'Missing imageData',
        message: 'imageData is required in request body'
      });
    }

    // Proxy to Cloud Run backend for free preview (512px)
    const response = await fetch(`${CLOUDRUN_API_URL}/api/free-preview-bg`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        imageData: imageData,
        quality: 'preview', // 512px output
        maxSize: 512
      }),
      signal: AbortSignal.timeout(300000) // 5 minutes timeout
    });

    // Handle non-OK responses
    if (!response.ok) {
      let errorData = {};
      try {
        const errorText = await response.text();
        try {
          errorData = JSON.parse(errorText);
        } catch (parseError) {
          errorData = {
            success: false,
            error: 'Backend error',
            message: errorText || `Backend returned ${response.status}: ${response.statusText}`
          };
        }
      } catch (e) {
        errorData = {
          success: false,
          error: 'Backend error',
          message: `Backend returned ${response.status}: ${response.statusText}`
        };
      }
      
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(response.status).json(errorData);
    }

    const data = await response.json();
    
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(200).json({
      success: true,
      resultImage: data.resultImage || data.image || data.output,
      outputSize: data.outputSize || data.size,
      outputSizeMB: data.outputSizeMB || (data.outputSize ? (data.outputSize / (1024 * 1024)).toFixed(2) : null),
      processedWith: data.processedWith || 'Free Preview (512px GPU-accelerated)'
    });

  } catch (error) {
    console.error('Free preview proxy error:', error);
    res.setHeader('Access-Control-Allow-Origin', '*');
    
    // Handle timeout errors
    if (error.name === 'AbortError' || error.message.includes('timeout')) {
      return res.status(504).json({
        success: false,
        error: 'Request timeout',
        message: 'Processing took too long. Please try with a smaller image or try again later.'
      });
    }
    
    // Handle network errors
    if (error.message.includes('fetch') || error.message.includes('ECONNREFUSED')) {
      return res.status(503).json({
        success: false,
        error: 'Service unavailable',
        message: 'Background removal service is temporarily unavailable. Please try again later.'
      });
    }
    
    return res.status(500).json({
      success: false,
      error: 'Proxy error',
      message: error.message || 'Failed to process image'
    });
  }
}

