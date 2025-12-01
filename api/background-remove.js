// Vercel Serverless Function - Background Removal Proxy
// Proxies requests to Google Cloud Run API to avoid CORS issues

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL || 'https://bg-remover-api-iwumaktavq-uc.a.run.app';

// Log configuration on startup (for debugging)
console.log('🔧 Background Removal Proxy Configuration:');
console.log('   Cloud Run URL:', CLOUDRUN_API_URL);
console.log('   Environment:', process.env.NODE_ENV || 'production');

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
    console.log('📊 Image data preview:', imageData.substring(0, 50) + '...');
    
    // Add retry logic for cold starts
    let lastError = null;
    const maxRetries = 2;
    const retryDelay = 15000; // 15 seconds
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 180000); // 3 minutes
    
    let response;
    let fetchErrorDetails = null;
    
    // Retry logic for handling cold starts
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          console.log(`🔄 Retry attempt ${attempt}/${maxRetries} after ${retryDelay/1000}s delay...`);
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          // Create new controller for retry
          clearTimeout(timeout);
          const newController = new AbortController();
          const newTimeout = setTimeout(() => newController.abort(), 180000);
          controller = newController;
          timeout = newTimeout;
        }
        
        const startTime = Date.now();
        console.log(`⏱️ Starting fetch request (attempt ${attempt + 1}/${maxRetries + 1}) at:`, new Date().toISOString());
        
        response = await fetch(backendUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ imageData }),
          signal: controller.signal
        });
        
        const fetchTime = Date.now() - startTime;
        console.log(`⏱️ Fetch completed in ${fetchTime}ms`);
        console.log('📥 Response status:', response.status, response.statusText);
        
        // If we got a response (even if not OK), break retry loop
        break;
        
      } catch (fetchError) {
        lastError = fetchError;
        fetchErrorDetails = {
          name: fetchError.name,
          message: fetchError.message,
          stack: fetchError.stack,
          code: fetchError.code,
          errno: fetchError.errno,
          syscall: fetchError.syscall
        };
        
        console.error(`❌ Fetch error (attempt ${attempt + 1}):`, fetchError.message);
        
        // If this is the last attempt, handle the error
        if (attempt === maxRetries) {
          clearTimeout(timeout);
          
          // Detailed error handling based on error type
          if (fetchError.name === 'TypeError') {
            if (fetchError.message.includes('fetch')) {
              return res.status(503).json({
                success: false,
                error: 'Cannot connect to Google Cloud Run backend after multiple attempts. The service may be cold starting or temporarily unavailable.',
                details: {
                  error: 'Network connection failed',
                  url: backendUrl,
                  attempts: maxRetries + 1,
                  suggestion: 'Service is likely cold starting. Please wait 20-30 seconds and try again.',
                  troubleshooting: [
                    '1. Wait 20-30 seconds for service to warm up',
                    '2. Check if Cloud Run service is deployed: gcloud run services list',
                    '3. Verify service URL is correct',
                    '4. Check Cloud Run service logs: gcloud run services logs read bg-remover-api'
                  ]
                }
              });
            } else if (fetchError.message.includes('Invalid URL')) {
              return res.status(500).json({
                success: false,
                error: 'Invalid Cloud Run URL configuration',
                details: {
                  url: backendUrl,
                  suggestion: 'Check CLOUDRUN_API_URL environment variable'
                }
              });
            }
          }
          
          // DNS/Network errors
          if (fetchError.code === 'ENOTFOUND' || fetchError.code === 'ECONNREFUSED') {
            return res.status(503).json({
              success: false,
              error: 'Cannot resolve Cloud Run service URL. The service may not be deployed or the URL is incorrect.',
              details: {
                error: fetchError.message,
                url: backendUrl,
                code: fetchError.code,
                suggestion: 'Deploy Cloud Run service or verify the URL is correct'
              }
            });
          }
          
          throw fetchError;
        }
        // Otherwise, continue to next retry
      }
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
      
      console.error('❌ Backend error response:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        error: errorMessage,
        errorText: errorText.substring(0, 500) // First 500 chars
      });
      
      // Provide helpful error messages based on status code
      if (response.status === 503) {
        // If we got 503, suggest retry with delay
        errorMessage = 'Google Cloud Run service is temporarily unavailable (cold starting). The service is warming up. Please wait 15-20 seconds and try again. The service is configured to stay warm, but first request after deployment may take longer.';
        errorDetails = {
          ...errorDetails,
          suggestion: 'Wait 15-20 seconds and retry. Service should respond on next attempt.',
          troubleshooting: [
            'Service is warming up (normal for first request)',
            'Wait 15-20 seconds and try again',
            'Service is configured with min-instances=1 to prevent cold starts',
            'Check service status: gcloud run services describe bg-remover-api --region us-central1'
          ]
        };
      } else if (response.status === 504) {
        errorMessage = 'Request timeout. The image might be too large or processing is taking longer than expected.';
      } else if (response.status === 500) {
        errorMessage = 'Internal server error. The backend encountered an error processing your image. Check Cloud Run logs for details.';
        errorDetails = {
          ...errorDetails,
          suggestion: 'Check Cloud Run service logs for detailed error information'
        };
      } else if (response.status === 404) {
        errorMessage = 'Cloud Run endpoint not found. The service URL or endpoint path may be incorrect.';
        errorDetails = {
          ...errorDetails,
          url: backendUrl,
          suggestion: 'Verify the Cloud Run service URL and endpoint path'
        };
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage,
        details: errorDetails,
        backendUrl: backendUrl
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

