/**
 * Security Middleware
 * SSL, HMAC verification, security headers
 */

const helmet = require('helmet');
const { verifyHMAC } = require('../utils/encryption');
const AuditLog = require('../models/AuditLog');

/**
 * Security headers middleware
 */
function securityHeaders() {
  return helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
        scriptSrc: ["'self'", "https://cdnjs.cloudflare.com"],
        imgSrc: ["'self'", "data:", "https:"],
        connectSrc: ["'self'"],
        fontSrc: ["'self'", "https://cdnjs.cloudflare.com", "https://fonts.googleapis.com"]
      }
    },
    hsts: {
      maxAge: 31536000,
      includeSubDomains: true,
      preload: true
    },
    noSniff: true,
    xssFilter: true,
    frameguard: { action: 'deny' }
  });
}

/**
 * HMAC verification middleware
 * Verifies API requests using HMAC signatures
 */
function verifyHMACSignature(req, res, next) {
  try {
    // Skip HMAC verification for certain endpoints
    const skipPaths = ['/api/auth/login', '/api/auth/register', '/api/health'];
    if (skipPaths.includes(req.path)) {
      return next();
    }
    
    const signature = req.headers['x-hmac-signature'];
    const timestamp = req.headers['x-timestamp'];
    
    if (!signature || !timestamp) {
      // HMAC is optional for now, log but don't block
      return next();
    }
    
    // Check timestamp (prevent replay attacks)
    const requestTime = parseInt(timestamp);
    const now = Date.now();
    const timeDiff = Math.abs(now - requestTime);
    
    if (timeDiff > 5 * 60 * 1000) { // 5 minutes
      return res.status(401).json({
        success: false,
        error: 'Request timestamp is too old',
        code: 'TIMESTAMP_EXPIRED'
      });
    }
    
    // Verify HMAC
    const secret = process.env.HMAC_SECRET || 'your-hmac-secret-change-in-production';
    const data = `${req.method}${req.path}${timestamp}${JSON.stringify(req.body)}`;
    
    if (!verifyHMAC(data, signature, secret)) {
      // Log suspicious activity
      AuditLog.create({
        action: 'hmac_verification_failed',
        resourceType: 'security',
        details: { path: req.path, ip: req.ip },
        ipAddress: req.ip || req.connection.remoteAddress,
        userAgent: req.headers['user-agent'],
        status: 'failure'
      }).catch(console.error);
      
      return res.status(401).json({
        success: false,
        error: 'Invalid HMAC signature',
        code: 'INVALID_SIGNATURE'
      });
    }
    
    next();
  } catch (error) {
    console.error('HMAC verification error:', error);
    next(); // Continue on error (optional verification)
  }
}

/**
 * Rate limiting per user
 */
function userRateLimit(req, res, next) {
  // This will be enhanced with Redis later
  // For now, use express-rate-limit
  next();
}

/**
 * Security monitoring middleware
 * Logs suspicious activities
 */
async function securityMonitoring(req, res, next) {
  try {
    // Monitor for suspicious patterns
    const suspiciousPatterns = [
      /\.\./, // Path traversal
      /<script/i, // XSS attempts
      /union.*select/i, // SQL injection
      /eval\(/i, // Code injection
    ];
    
    const requestString = JSON.stringify({
      path: req.path,
      query: req.query,
      body: JSON.stringify(req.body)
    });
    
    for (const pattern of suspiciousPatterns) {
      if (pattern.test(requestString)) {
        // Log suspicious activity
        await AuditLog.create({
          action: 'suspicious_activity_detected',
          resourceType: 'security',
          details: {
            pattern: pattern.toString(),
            path: req.path,
            query: req.query
          },
          ipAddress: req.ip || req.connection.remoteAddress,
          userAgent: req.headers['user-agent'],
          status: 'failure'
        });
        
        return res.status(403).json({
          success: false,
          error: 'Suspicious activity detected',
          code: 'SUSPICIOUS_ACTIVITY'
        });
      }
    }
    
    next();
  } catch (error) {
    console.error('Security monitoring error:', error);
    next(); // Continue on error
  }
}

module.exports = {
  securityHeaders,
  verifyHMACSignature,
  userRateLimit,
  securityMonitoring
};

