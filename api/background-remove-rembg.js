// Vercel Serverless Function - Background Remover Rembg U2Net Proxy
// Proxies requests to Google Cloud Run backend with rembg U2Net

const CLOUDRUN_API_URL = process.env.CLOUDRUN_API_URL_REMBG || 'https://bg-remover-rembg-u2net-564572183797.us-central1.run.app';

export default async function handler(req, res) {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-User-ID, X-User-Type');
    res.setHeader('Access-Control-Max-Age', '3600');
    return res.status(200).end();
  }

  // Get the URL path from query or request
  const urlPath = req.url || req.query.path || '';
  const isHealth = urlPath.includes('/health') || req.url?.includes('/health');
  const isUsage = urlPath.includes('/usage') || req.url?.includes('/usage');

  // Health check endpoint
  if (req.method === 'GET' && isHealth) {
    try {
      const response = await fetch(`${CLOUDRUN_API_URL}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      
      const data = await response.ok ? await response.json() : { status: 'error' };
      
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(200).json({
        ...data,
        proxy: 'working',
        backend: response.ok ? 'connected' : 'error'
      });
    } catch (error) {
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(200).json({
        status: 'warning',
        backend: 'unreachable',
        error: error.message
      });
    }
  }

  // Usage endpoint
  if (req.method === 'GET' && isUsage) {
    try {
      const userId = req.headers['x-user-id'] || 'anonymous';
      const userType = req.headers['x-user-type'] || 'free';
      
      const response = await fetch(`${CLOUDRUN_API_URL}/usage`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'X-User-ID': userId,
          'X-User-Type': userType
        }
      });
      
      const data = await response.json();
      
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(response.status).json(data);
    } catch (error) {
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(500).json({
        error: 'Proxy error',
        message: error.message
      });
    }
  }

  // Main background removal endpoint
  if (req.method === 'POST') {
    try {
      const userId = req.headers['x-user-id'] || 'anonymous';
      const userType = req.headers['x-user-type'] || 'free';
      
      const response = await fetch(`${CLOUDRUN_API_URL}/remove-background`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-User-ID': userId,
          'X-User-Type': userType
        },
        body: JSON.stringify(req.body),
        timeout: 300000 // 5 minutes timeout
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
      return res.status(response.status).json(data);
    } catch (error) {
      console.error('Proxy error:', error);
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(500).json({
        success: false,
        error: 'Proxy error',
        message: error.message || 'Failed to connect to backend service'
      });
    }
  }

  // Root endpoint (GET /)
  if (req.method === 'GET') {
    try {
      const response = await fetch(`${CLOUDRUN_API_URL}/`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      
      const data = await response.json();
      
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(response.status).json(data);
    } catch (error) {
      res.setHeader('Access-Control-Allow-Origin', '*');
      return res.status(500).json({
        error: 'Proxy error',
        message: error.message
      });
    }
  }

  // Default response
  res.setHeader('Access-Control-Allow-Origin', '*');
  return res.status(405).json({
    error: 'Method not allowed',
    message: 'Only GET and POST methods are supported'
  });
}

