// Vercel Serverless Function - Excel Unlocker Proxy
// This calls the Render backend from Vercel

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ 
      success: false, 
      error: 'Method not allowed. Use POST.' 
    });
  }

  try {
    // Backend URL - Render deployment
    const BACKEND_URL = 'https://excel-unlocker-backend.onrender.com/unlock';

    // Forward the request to Render backend
    const formData = new FormData();
    
    // Get file from request
    const { file, password } = req.body;
    
    if (!file) {
      return res.status(400).json({
        success: false,
        error: 'No file provided'
      });
    }

    formData.append('file', file);
    if (password) {
      formData.append('password', password);
    }

    // Call Render backend
    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    // Return response
    return res.status(response.status).json(result);

  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({
      success: false,
      error: `Server error: ${error.message}`
    });
  }
}
