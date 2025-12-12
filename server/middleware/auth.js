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
 * Verify Firebase ID token and get/create user in MongoDB
 */
async function verifyFirebaseTokenAndGetUser(token) {
  try {
    const { getFirebaseAdmin } = require('../config/google-cloud');
    const firebaseAdmin = getFirebaseAdmin();
    
    if (!firebaseAdmin) {
      return null;
    }
    
    // Verify Firebase ID token
    const decodedToken = await firebaseAdmin.auth().verifyIdToken(token);
    
    if (!decodedToken || !decodedToken.uid) {
      return null;
    }
    
    // Find or create user in MongoDB
    let user = await User.findOne({ firebaseUid: decodedToken.uid });
    
    if (!user) {
      // Create new user from Firebase token
      user = await User.create({
        email: decodedToken.email || `firebase_${decodedToken.uid}@temp.com`,
        firebaseUid: decodedToken.uid,
        firstName: decodedToken.name?.split(' ')[0] || decodedToken.email?.split('@')[0] || 'User',
        lastName: decodedToken.name?.split(' ').slice(1).join(' ') || '',
        role: 'viewer',
        subscriptionPlan: 'free',
        emailVerified: decodedToken.email_verified || false
      });
    } else {
      // Update user info from Firebase if needed
      if (decodedToken.email && user.email !== decodedToken.email) {
        user.email = decodedToken.email;
      }
      if (decodedToken.name) {
        const nameParts = decodedToken.name.split(' ');
        if (nameParts.length > 0) {
          user.firstName = nameParts[0];
          user.lastName = nameParts.slice(1).join(' ') || '';
        }
      }
      if (decodedToken.email_verified !== undefined) {
        user.emailVerified = decodedToken.email_verified;
      }
      await user.save();
    }
    
    return user;
  } catch (error) {
    console.error('Firebase token verification error:', error.message);
    return null;
  }
}

/**
 * Authentication middleware
 * Validates JWT token or Firebase ID token and attaches user to request
 */
async function authenticate(req, res, next) {
  try {
    // Handle OPTIONS requests for CORS preflight
    if (req.method === 'OPTIONS') {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      return res.status(200).end();
    }
    
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
    
    let user = null;
    
    // Try Firebase token first (for frontend Firebase Auth users)
    const firebaseUser = await verifyFirebaseTokenAndGetUser(token);
    if (firebaseUser) {
      user = firebaseUser;
    } else {
      // Fallback to JWT token verification (for backend-generated tokens)
      const decoded = verifyToken(token);
      if (decoded && decoded.userId) {
        user = await User.findById(decoded.userId).select('+password');
      }
    }
    
    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Invalid or expired token',
        code: 'INVALID_TOKEN'
      });
    }
    
    // Check if user is locked
    if (user.isLocked && user.isLocked()) {
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
    }).catch(console.error);
    
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

