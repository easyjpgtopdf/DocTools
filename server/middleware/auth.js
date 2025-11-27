/**
 * Authentication Middleware
 * JWT token validation and user authentication
 */

const jwt = require('jsonwebtoken');
const User = require('../models/User');
const AuditLog = require('../models/AuditLog');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '7d';

/**
 * Generate JWT token
 */
function generateToken(user) {
  const payload = {
    userId: user._id,
    email: user.email,
    role: user.role,
    teamId: user.teamId,
    subscriptionPlan: user.subscriptionPlan
  };
  
  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: JWT_EXPIRES_IN
  });
}

/**
 * Verify JWT token
 */
function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (error) {
    return null;
  }
}

/**
 * Authentication middleware
 * Validates JWT token and attaches user to request
 */
async function authenticate(req, res, next) {
  try {
    // Get token from header or cookie
    const token = req.headers.authorization?.replace('Bearer ', '') || 
                  req.cookies?.token;
    
    if (!token) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
        code: 'NO_TOKEN'
      });
    }
    
    // Verify token
    const decoded = verifyToken(token);
    if (!decoded) {
      return res.status(401).json({
        success: false,
        error: 'Invalid or expired token',
        code: 'INVALID_TOKEN'
      });
    }
    
    // Get user from database
    const user = await User.findById(decoded.userId).select('+password');
    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    // Check if user is locked
    if (user.isLocked()) {
      return res.status(403).json({
        success: false,
        error: 'Account is temporarily locked due to multiple failed login attempts',
        code: 'ACCOUNT_LOCKED'
      });
    }
    
    // Attach user to request
    req.user = user;
    req.userId = user._id;
    req.userRole = user.role;
    
    // Log API access
    await AuditLog.create({
      userId: user._id,
      organizationId: user.teamId,
      action: 'api_access',
      resourceType: 'api',
      ipAddress: req.ip || req.connection.remoteAddress,
      userAgent: req.headers['user-agent'],
      status: 'success'
    });
    
    next();
  } catch (error) {
    console.error('Authentication error:', error);
    return res.status(500).json({
      success: false,
      error: 'Authentication failed',
      code: 'AUTH_ERROR'
    });
  }
}

/**
 * Role-based access control middleware
 */
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
        code: 'NO_USER'
      });
    }
    
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        error: 'Insufficient permissions',
        code: 'INSUFFICIENT_PERMISSIONS'
      });
    }
    
    next();
  };
}

/**
 * Optional authentication - doesn't fail if no token
 */
async function optionalAuthenticate(req, res, next) {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '') || 
                  req.cookies?.token;
    
    if (token) {
      const decoded = verifyToken(token);
      if (decoded) {
        const user = await User.findById(decoded.userId);
        if (user && !user.isLocked()) {
          req.user = user;
          req.userId = user._id;
          req.userRole = user.role;
        }
      }
    }
    
    next();
  } catch (error) {
    // Continue without authentication
    next();
  }
}

/**
 * API Key authentication
 */
async function authenticateApiKey(req, res, next) {
  try {
    const apiKey = req.headers['x-api-key'] || req.query.apiKey;
    
    if (!apiKey) {
      return res.status(401).json({
        success: false,
        error: 'API key required',
        code: 'NO_API_KEY'
      });
    }
    
    // Find user by API key
    const user = await User.findOne({
      'apiKeys.key': apiKey,
      'apiKeys': { $elemMatch: { key: apiKey } }
    });
    
    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Invalid API key',
        code: 'INVALID_API_KEY'
      });
    }
    
    // Update API key last used
    const apiKeyObj = user.apiKeys.find(k => k.key === apiKey);
    if (apiKeyObj) {
      apiKeyObj.lastUsed = new Date();
      await user.save();
    }
    
    // Check usage limits
    if (!user.checkUsageLimit('api')) {
      return res.status(429).json({
        success: false,
        error: 'API usage limit exceeded',
        code: 'USAGE_LIMIT_EXCEEDED'
      });
    }
    
    // Increment API usage
    await user.incrementUsage('api', 1);
    
    req.user = user;
    req.userId = user._id;
    req.userRole = user.role;
    req.apiKey = apiKey;
    
    next();
  } catch (error) {
    console.error('API key authentication error:', error);
    return res.status(500).json({
      success: false,
      error: 'Authentication failed',
      code: 'AUTH_ERROR'
    });
  }
}

module.exports = {
  generateToken,
  verifyToken,
  authenticate,
  optionalAuthenticate,
  authenticateApiKey,
  requireRole
};

