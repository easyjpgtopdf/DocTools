// ============================================
// Background Removal Proxy Endpoints
// Extracted from server/server.js
// Date: 2025-12-12
// ============================================

// Background removal proxy endpoints (to avoid CORS issues)
const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL || 'https://bg-remover-api-iwumaktavq-uc.a.run.app';

// BiRefNet Background Removal Service URL (GPU-accelerated)
const CLOUDRUN_API_URL_BG_REMOVAL = process.env.CLOUDRUN_API_URL_BG_REMOVAL || 
                                     'https://bg-removal-birefnet-564572183797.us-central1.run.app';

app.post('/api/background-remove', async (req, res) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180000); // 3 minutes
  
  try {
    const { imageData } = req.body;
    
    if (!imageData) {
      clearTimeout(timeout);
      return res.status(400).json({ 
        success: false, 
        error: 'No imageData provided' 
      });
    }

    // Forward request to Cloud Run API
    const backendUrl = `${CLOUDRUN_API_URL}/remove-background`;
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ imageData }),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Backend error: ${response.status}`;
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch (e) {
        errorMessage = errorText || errorMessage;
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage
      });
    }

    const result = await response.json();
    res.json(result);
    
  } catch (error) {
    clearTimeout(timeout);
    console.error('Background removal proxy error:', error);
    
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      return res.status(504).json({
        success: false,
        error: 'Request timeout. The image might be too large or the server is busy.'
      });
    }
    
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to process background removal request'
    });
  }
});

// Health check for background removal service
app.get('/api/background-remove/health', async (req, res) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000); // 5 seconds for health check
  
  try {
    const backendUrl = `${CLOUDRUN_API_URL}/health`;
    const response = await fetch(backendUrl, {
      method: 'GET',
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    
    if (response.ok) {
      const data = await response.json();
      res.json({ ...data, proxy: 'working' });
    } else {
      res.status(response.status).json({
        status: 'unhealthy',
        error: `Backend returned status ${response.status}`
      });
    }
  } catch (error) {
    clearTimeout(timeout);
    res.status(503).json({
      status: 'unhealthy',
      error: error.message || 'Backend service unavailable'
    });
  }
});

// ============================================
// BiRefNet Background Removal Proxy
// ============================================

// POST /api/background-remove-birefnet - Process image (using BiRefNet backend)
app.post('/api/background-remove-birefnet', async (req, res) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180000); // 3 minutes
  
  try {
    const { imageData } = req.body;
    
    if (!imageData) {
      clearTimeout(timeout);
      return res.status(400).json({ 
        success: false, 
        error: 'No imageData provided' 
      });
    }

    // Get headers from request to forward to backend
    const userHeaders = {};
    if (req.headers['x-user-id']) userHeaders['X-User-ID'] = req.headers['x-user-id'];
    if (req.headers['x-user-type']) userHeaders['X-User-Type'] = req.headers['x-user-type'];
    if (req.headers['x-device-id']) userHeaders['X-Device-ID'] = req.headers['x-device-id'];
    if (req.headers['x-auth-token']) userHeaders['X-Auth-Token'] = req.headers['x-auth-token'];

    // Forward request to BiRefNet Cloud Run API (free preview endpoint)
    const backendUrl = `${CLOUDRUN_API_URL_BG_REMOVAL}/api/free-preview-bg`;
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...userHeaders
      },
      body: JSON.stringify({ 
        imageData,
        maxSize: 512,
        quality: 'preview'
      }),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Backend error: ${response.status}`;
      
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch (e) {
        errorMessage = errorText || errorMessage;
      }
      
      return res.status(response.status).json({
        success: false,
        error: errorMessage
      });
    }

    const result = await response.json();
    // Adapt response format if needed
    if (result.success !== undefined) {
      res.json(result);
    } else {
      // Convert BiRefNet response to expected format
      res.json({
        success: true,
        resultImage: result.resultImage || result.imageData || result.data,
        processedWith: 'birefnet',
        ...result
      });
    }
    
  } catch (error) {
    clearTimeout(timeout);
    console.error('Background removal proxy error:', error);
    
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      return res.status(504).json({
        success: false,
        error: 'Request timeout. The image might be too large or the server is busy.'
      });
    }
    
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to process background removal request'
    });
  }
});

// GET /api/background-remove-birefnet/health - Health check
app.get('/api/background-remove-birefnet/health', async (req, res) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000); // 5 seconds for health check
  
  try {
    const backendUrl = `${CLOUDRUN_API_URL_BG_REMOVAL}/health`;
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      },
      signal: controller.signal
    });
    
    clearTimeout(timeout);
    
    if (response.ok) {
      const data = await response.json();
      res.json({ ...data, proxy: 'working', model: 'birefnet' });
    } else {
      res.status(response.status).json({
        status: 'unhealthy',
        error: `Backend returned status ${response.status}`
      });
    }
  } catch (error) {
    clearTimeout(timeout);
    res.status(503).json({
      status: 'unhealthy',
      error: error.message || 'Backend service unavailable'
    });
  }
});

// GET /api/background-remove-birefnet/usage - Usage statistics (stub endpoint)
app.get('/api/background-remove-birefnet/usage', async (req, res) => {
  // BiRefNet doesn't have a usage endpoint, return default values
  res.json({
    userId: req.headers['x-user-id'] || 'anonymous',
    userType: req.headers['x-user-type'] || 'free',
    deviceId: req.headers['x-device-id'] || 'unknown',
    imageCount: 0,
    imageLimit: -1,
    uploadBytes: 0,
    uploadLimit: 'infinity',
    downloadBytes: 0,
    downloadLimit: 'infinity',
    remainingImages: -1
  });
});

