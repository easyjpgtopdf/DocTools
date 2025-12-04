// Unified API Router for Vercel
// This single function handles all API endpoints to stay under the 12 function limit
// Usage: /api/router?endpoint=create-order&...
// Or: /api/router/create-order, /api/router/credits/balance, etc.

module.exports = async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Get endpoint from query or path
  let endpoint = req.query.endpoint;
  if (!endpoint) {
    // Try to extract from URL path: /api/router/credits/balance -> credits/balance
    const pathMatch = req.url.match(/\/api\/router\/(.+?)(?:\?|$)/);
    if (pathMatch) {
      endpoint = pathMatch[1];
    }
  }
  
  if (!endpoint) {
    return res.status(400).json({ error: 'Endpoint parameter required. Use ?endpoint=create-order or /api/router/create-order' });
  }

  try {
    // Route to appropriate handler based on endpoint
    let handler;
    
    switch (endpoint) {
      case 'create-order':
        handler = require('../api-handlers/create-order.js');
        break;
      
      case 'credits/balance':
      case 'credits-balance':
        handler = require('../api-handlers/credits/balance.js');
        break;
      
      case 'credits/purchase':
      case 'credits-purchase':
        handler = require('../api-handlers/credits/purchase.js');
        break;
      
      case 'credits/verify':
      case 'credits-verify':
        handler = require('../api-handlers/credits/verify.js');
        break;
      
      case 'payments/razorpay/webhook':
      case 'razorpay-webhook':
        handler = require('../api-handlers/payments/razorpay/webhook.js');
        break;
      
      case 'send-receipt-email':
        handler = require('../api-handlers/send-receipt-email.js');
        break;
      
      case 'unlock-excel':
        handler = require('../api-handlers/unlock-excel.js');
        break;
      
      case 'pdf-ocr/status':
      case 'pdf-ocr-status':
        handler = require('../api-handlers/pdf-ocr/status.js');
        break;
      
      case 'cloud/status':
      case 'cloud-status':
        handler = require('../api-handlers/cloud/status.js');
        break;
      
      case 'background-remove-v2':
        // Try v2 first, fallback to remove-background
        try {
          handler = require('../api-handlers/background-remove-v2.js');
        } catch {
          handler = require('../api-handlers/remove-background.js');
        }
        break;
      
      case 'remove-background':
        handler = require('../api-handlers/remove-background.js');
        break;
      
      default:
        return res.status(404).json({ error: `Endpoint '${endpoint}' not found` });
    }
    
    // Call the handler
    if (typeof handler === 'function') {
      return await handler(req, res);
    } else if (handler.default) {
      return await handler.default(req, res);
    } else if (handler.handler) {
      return await handler.handler(req, res);
    } else {
      return res.status(500).json({ error: 'Handler format not recognized' });
    }
  } catch (error) {
    console.error(`Error handling endpoint ${endpoint}:`, error);
    return res.status(500).json({ 
      error: 'Internal server error',
      message: error.message 
    });
  }
}

