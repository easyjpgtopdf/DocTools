const fetch = require('node-fetch');
const FormData = require('form-data');

// Remove.bg API key - set in environment variables
const REMOVE_BG_API_KEY = process.env.REMOVE_BG_API_KEY;

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    if (!REMOVE_BG_API_KEY) {
      return res.status(503).json({ 
        error: 'Remove.bg API not configured',
        fallback: true,
        message: 'Using local AI processing instead'
      });
    }

    const { imageData, size } = req.body;
    
    if (!imageData) {
      return res.status(400).json({ error: 'No image data provided' });
    }

    // Convert base64 to buffer
    const base64Data = imageData.replace(/^data:image\/\w+;base64,/, '');
    const imageBuffer = Buffer.from(base64Data, 'base64');

    // Create form data for remove.bg API
    const formData = new FormData();
    formData.append('image_file_b64', base64Data);
    formData.append('size', size || 'auto'); // auto, preview, full, medium, hd, 4k
    formData.append('format', 'png');
    formData.append('type', 'auto'); // auto, person, product, car
    formData.append('channels', 'rgba'); // rgba, alpha (transparency)
    formData.append('bg_color', ''); // Empty for transparent
    formData.append('roi', '0% 0% 100% 100%'); // Region of interest (full image)

    // Call remove.bg API
    const response = await fetch('https://api.remove.bg/v1.0/removebg', {
      method: 'POST',
      headers: {
        'X-Api-Key': REMOVE_BG_API_KEY,
      },
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Remove.bg API error:', response.status, errorData);
      
      // Return fallback flag for client to use local AI
      return res.status(response.status).json({ 
        error: errorData.errors || 'Background removal failed',
        fallback: true,
        message: 'Falling back to local AI processing'
      });
    }

    // Get the result as buffer
    const resultBuffer = await response.buffer();
    const resultBase64 = resultBuffer.toString('base64');
    const resultDataUrl = `data:image/png;base64,${resultBase64}`;

    // Get API credits info from headers
    const creditsCharged = response.headers.get('X-Credits-Charged');
    const creditsRemaining = response.headers.get('X-RateLimit-Remaining');

    res.status(200).json({
      success: true,
      resultImage: resultDataUrl,
      credits: {
        charged: creditsCharged,
        remaining: creditsRemaining
      }
    });

  } catch (error) {
    console.error('Remove background error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      fallback: true,
      message: 'Using local AI processing instead'
    });
  }
};
