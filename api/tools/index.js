// Consolidated Tools API Router
// Handles tool-related endpoints via Vercel rewrites
// Routes: /api/tools/unlock-excel, /api/tools/health
// Note: bg-remove-free and bg-remove-premium are handled by direct route files

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '3600');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Extract route from query parameter (set by Vercel rewrite)
  // Vercel rewrite: /api/tools/unlock-excel -> /api/tools/index.js?route=unlock-excel
  
  const route = req.query?.route || null;

  try {
    // Route: /api/tools/unlock-excel
    if (route === 'unlock-excel' && req.method === 'POST') {
      return await handleUnlockExcel(req, res);
    }

    // Route: /api/tools/health
    if (route === 'health') {
      return res.status(200).json({ status: 'healthy', service: 'tools-api' });
    }

    // Unknown route
    return res.status(404).json({ 
      success: false, 
      error: `Route not found: ${route || 'unknown'}`,
      availableRoutes: ['unlock-excel', 'health']
    });

  } catch (error) {
    console.error('Tools API error:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'Internal server error'
    });
  }
};

// Unlock Excel Handler
async function handleUnlockExcel(req, res) {
  try {
    const BACKEND_URL = 'https://excel-unlocker-backend.onrender.com/unlock';
    const { file, password } = req.body;

    if (!file) {
      return res.status(400).json({
        success: false,
        error: 'No file provided'
      });
    }

    const formData = new FormData();
    formData.append('file', file);
    if (password) {
      formData.append('password', password);
    }

    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    return res.status(response.status).json(result);

  } catch (error) {
    console.error('Unlock Excel error:', error);
    return res.status(500).json({
      success: false,
      error: `Server error: ${error.message}`
    });
  }
}
