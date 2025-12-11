/**
 * Admin Only Middleware
 * Restricts access to admin/owner only
 */

const User = require('../models/User');

/**
 * Middleware to allow only admin/owner access
 */
async function adminOnly(req, res, next) {
  try {
    if (!req.userId) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
        code: 'NO_TOKEN'
      });
    }

    const user = await User.findById(req.userId);
    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }

    // Check if user is admin or owner
    // You can customize this based on your user model
    const isAdmin = user.role === 'admin' || 
                    user.email === process.env.OWNER_EMAIL ||
                    user.subscriptionPlan === 'enterprise';

    if (!isAdmin) {
      console.warn(`Unauthorized admin access attempt by user ${req.userId}`);
      return res.status(403).json({
        success: false,
        error: 'Access denied',
        message: 'This action requires administrator privileges',
        code: 'INSUFFICIENT_PERMISSIONS'
      });
    }

    next();
  } catch (error) {
    console.error('Admin check error:', error);
    return res.status(500).json({
      success: false,
      error: 'Authorization check failed',
      code: 'AUTH_CHECK_ERROR'
    });
  }
}

module.exports = { adminOnly };

