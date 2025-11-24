/**
 * Subscription API Routes
 * Add these routes to your Express server
 */

const createOrder = require('./create-order');
const verifyPayment = require('./verify-payment');
const autoExpire = require('./auto-expire');

module.exports = function(app) {
  // Create subscription order
  app.post('/api/subscriptions/create-order', createOrder);
  
  // Verify payment and activate subscription
  app.post('/api/subscriptions/verify-payment', verifyPayment);
  
  // Auto-expire subscriptions (cron job endpoint)
  app.post('/api/subscriptions/auto-expire', autoExpire);
  app.get('/api/subscriptions/auto-expire', autoExpire); // Also allow GET for easier cron setup
};

