// Vercel Serverless Function - Background Removal Proxy
// Simple proxy that forwards requests to Google Cloud Run

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Accept');
  res.setHeader('Access-Control-Max-Age', '3600');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Health check endpoint
  if (req.method === 'GET') {
    try {
      const response = await fetch('https://bg-remover-api-iwumaktavq-uc.a.run.app/', {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json().catch(() => ({ status: 'ok' }));
        return res.status(200).json({ 
          ...data, 
          proxy: 'working',
          backend: 'connected'
        });
      } else {
        return res.status(200).json({
          status: 'warning',
          backend: 'reachable',
          message: `Backend returned status ${response.status} but is reachable`
        });
      }
    } catch (error) {
      console.error('Health check error:', error.message);
      return res.status(200).json({
        status: 'warning',
        backend: 'unreachable',
        error: error.message || 'Backend service may be starting up',
        message: 'Backend will be tested on first request'
      });
    }
  }

  // Background removal endpoint
  if (req.method !== 'POST') {
    return res.status(405).json({ 
      success: false, 
      error: 'Method not allowed. Use POST.' 
    });
  }

  try {
    const { imageData } = req.body;
    
    if (!imageData) {
      return res.status(400).json({ 
        success: false, 
        error: 'No imageData provided' 
      });
    }

    // Forward request to Cloud Run API
    const backendUrl = 'https://bg-remover-api-iwumaktavq-uc.a.run.app/remove-background';
    console.log('📤 Proxying request to:', backendUrl);
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ imageData })
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Backend error: ${response.status}`;
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch (e) {
        errorMessage = errorText || errorMessage;
      }
      
      // Provide helpful error messages
      if (response.status === 503) {
        errorMessage = 'Google Cloud Run service is temporarily unavailable (cold starting). Please wait 15-20 seconds and try again.';
      } else if (response.status === 504) {
        errorMessage = 'Request timeout. The image might be too large or processing is taking longer than expected.';
      } else if (response.status === 500) {
        errorMessage = 'Internal server error. The backend encountered an error processing your image.';
      } else if (response.status === 404) {
        errorMessage = 'Cloud Run endpoint not found. The service URL or endpoint path may be incorrect.';
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage
      });
    }

    const result = await response.json();
    console.log('✅ Processing successful');
    return res.status(200).json(result);
    
  } catch (error) {
    console.error('❌ Background removal proxy error:', error);
    
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      return res.status(504).json({
        success: false,
        error: 'Request timeout. The image might be too large or the server is busy. Please try again later.'
      });
    }
    
    // Network errors
    if (error.message && (error.message.includes('fetch') || error.message.includes('ECONNREFUSED'))) {
      return res.status(503).json({
        success: false,
        error: 'Cannot connect to Google Cloud Run backend. The service may be starting up. Please wait 10-30 seconds and try again.'
      });
    }
    
    return res.status(500).json({
      success: false,
      error: error.message || 'Failed to process background removal request'
    });
  }
}
