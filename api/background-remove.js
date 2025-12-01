// Vercel Serverless Function - Background Removal Proxy
// Proxies requests to Google Cloud Run API to avoid CORS issues

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL || 'https://bg-remover-api-iwumaktavq-uc.a.run.app';

module.exports = async function handler(req, res) {
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
      // Try root endpoint first (Cloud Run default)
      const backendUrl = `${CLOUDRUN_API_URL}/`;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000); // 10 seconds
      
      const response = await fetch(backendUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        },
        signal: controller.signal
      });
      
      clearTimeout(timeout);
      
      if (response.ok) {
        const data = await response.json().catch(() => ({ status: 'ok' }));
        return res.status(200).json({ 
          ...data, 
          proxy: 'working',
          backend: 'connected'
        });
      } else {
        // Backend exists but returned error
        return res.status(200).json({
          status: 'warning',
          backend: 'reachable',
          message: `Backend returned status ${response.status} but is reachable`
        });
      }
    } catch (error) {
      // Backend is not reachable - return warning but don't fail completely
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
    const backendUrl = `${CLOUDRUN_API_URL}/remove-background`;
    console.log('📤 Proxying request to:', backendUrl);
    console.log('📊 Image data length:', imageData.length);
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 180000); // 3 minutes
    
    let response;
    try {
      response = await fetch(backendUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ imageData }),
        signal: controller.signal
      });
    } catch (fetchError) {
      clearTimeout(timeout);
      console.error('❌ Fetch error:', fetchError.message);
      
      // Check if it's a network error
      if (fetchError.name === 'TypeError' && fetchError.message.includes('fetch')) {
        return res.status(503).json({
          success: false,
          error: 'Cannot connect to Google Cloud Run backend. The service may be starting up or temporarily unavailable. Please try again in a few moments.',
          details: 'Network connection failed',
          suggestion: 'Wait 10-30 seconds and try again (Cloud Run may be cold starting)'
        });
      }
      
      throw fetchError;
    }

    clearTimeout(timeout);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Backend error: ${response.status}`;
      let errorDetails = {};
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
        errorDetails = errorData;
      } catch (e) {
        errorMessage = errorText || errorMessage;
      }
      
      console.error('❌ Backend error:', {
        status: response.status,
        statusText: response.statusText,
        error: errorMessage
      });
      
      // Provide helpful error messages based on status code
      if (response.status === 503) {
        errorMessage = 'Google Cloud Run service is temporarily unavailable. This usually means the service is cold starting (first request after inactivity). Please wait 10-30 seconds and try again.';
      } else if (response.status === 504) {
        errorMessage = 'Request timeout. The image might be too large or processing is taking longer than expected.';
      } else if (response.status === 500) {
        errorMessage = 'Internal server error. The backend encountered an error processing your image.';
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage,
        details: errorDetails
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
        error: 'Request timeout. The image might be too large or the server is busy. Please try with a smaller image or try again later.'
      });
    }
    
    // Network errors
    if (error.message && (error.message.includes('fetch') || error.message.includes('ECONNREFUSED'))) {
      return res.status(503).json({
        success: false,
        error: 'Cannot connect to Google Cloud Run backend. The service may be starting up. Please wait 10-30 seconds and try again.',
        details: error.message
      });
    }
    
    return res.status(500).json({
      success: false,
      error: error.message || 'Failed to process background removal request',
      details: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
};

