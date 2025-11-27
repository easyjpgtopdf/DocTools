/**
 * Authentication Controller
 * User registration, login, password management
 */

const User = require('../models/User');
const Organization = require('../models/Organization');
const AuditLog = require('../models/AuditLog');
const { generateToken } = require('../middleware/auth');
const crypto = require('crypto');
const { asyncHandler } = require('../middleware/errorHandler');

/**
 * Register new user
 */
async function register(req, res) {
  try {
    const { email, password, firstName, lastName, acceptTerms } = req.body;
    
    // Validation
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        error: 'Email and password are required',
        code: 'MISSING_FIELDS'
      });
    }
    
    if (password.length < 8) {
      return res.status(400).json({
        success: false,
        error: 'Password must be at least 8 characters',
        code: 'WEAK_PASSWORD'
      });
    }
    
    if (!acceptTerms) {
      return res.status(400).json({
        success: false,
        error: 'You must accept the terms of service',
        code: 'TERMS_NOT_ACCEPTED'
      });
    }
    
    // Check if user exists
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(409).json({
        success: false,
        error: 'User with this email already exists',
        code: 'USER_EXISTS'
      });
    }
    
    // Create user
    const user = new User({
      email,
      password,
      firstName,
      lastName,
      acceptedTerms: true,
      acceptedTermsAt: new Date(),
      privacyPolicyAccepted: true,
      privacyPolicyAcceptedAt: new Date()
    });
    
    await user.save();
    
    // Generate token
    const token = generateToken(user);
    
    // Log registration
    await AuditLog.create({
      userId: user._id,
      action: 'user_registered',
      resourceType: 'user',
      resourceId: user._id.toString(),
      ipAddress: req.ip || req.connection.remoteAddress,
      userAgent: req.headers['user-agent'],
      status: 'success'
    });
    
    res.status(201).json({
      success: true,
      token,
      user: {
        id: user._id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        subscriptionPlan: user.subscriptionPlan,
        role: user.role
      }
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({
      success: false,
      error: 'Registration failed',
      code: 'REGISTRATION_ERROR'
    });
  }
}

/**
 * Login user
 */
async function login(req, res) {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({
        success: false,
        error: 'Email and password are required',
        code: 'MISSING_FIELDS'
      });
    }
    
    // Find user with password field
    const user = await User.findOne({ email }).select('+password');
    if (!user) {
      // Log failed attempt
      await AuditLog.create({
        action: 'login_failed',
        resourceType: 'security',
        details: { email, reason: 'user_not_found' },
        ipAddress: req.ip || req.connection.remoteAddress,
        userAgent: req.headers['user-agent'],
        status: 'failure'
      });
      
      return res.status(401).json({
        success: false,
        error: 'Invalid email or password',
        code: 'INVALID_CREDENTIALS'
      });
    }
    
    // Check if account is locked
    if (user.isLocked()) {
      return res.status(403).json({
        success: false,
        error: 'Account is temporarily locked. Please try again later.',
        code: 'ACCOUNT_LOCKED'
      });
    }
    
    // Verify password
    const isPasswordValid = await user.comparePassword(password);
    if (!isPasswordValid) {
      // Increment failed attempts
      await user.incrementFailedAttempts();
      
      // Log failed attempt
      await AuditLog.create({
        userId: user._id,
        action: 'login_failed',
        resourceType: 'security',
        details: { email, reason: 'invalid_password' },
        ipAddress: req.ip || req.connection.remoteAddress,
        userAgent: req.headers['user-agent'],
        status: 'failure'
      });
      
      return res.status(401).json({
        success: false,
        error: 'Invalid email or password',
        code: 'INVALID_CREDENTIALS'
      });
    }
    
    // Reset failed attempts on successful login
    await user.resetFailedAttempts();
    
    // Update last login
    user.lastLogin = new Date();
    await user.save();
    
    // Generate token
    const token = generateToken(user);
    
    // Log successful login
    await AuditLog.create({
      userId: user._id,
      organizationId: user.teamId,
      action: 'login_success',
      resourceType: 'security',
      ipAddress: req.ip || req.connection.remoteAddress,
      userAgent: req.headers['user-agent'],
      status: 'success'
    });
    
    res.json({
      success: true,
      token,
      user: {
        id: user._id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        subscriptionPlan: user.subscriptionPlan,
        role: user.role,
        teamId: user.teamId
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      success: false,
      error: 'Login failed',
      code: 'LOGIN_ERROR'
    });
  }
}

/**
 * Get current user profile
 */
async function getProfile(req, res) {
  try {
    const user = await User.findById(req.userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    res.json({
      success: true,
      user: {
        id: user._id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        subscriptionPlan: user.subscriptionPlan,
        subscriptionStatus: user.subscriptionStatus,
        role: user.role,
        teamId: user.teamId,
        usageLimits: user.usageLimits,
        currentUsage: user.currentUsage,
        createdAt: user.createdAt
      }
    });
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get profile',
      code: 'PROFILE_ERROR'
    });
  }
}

/**
 * Update user profile
 */
async function updateProfile(req, res) {
  try {
    const { firstName, lastName } = req.body;
    const user = await User.findById(req.userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    if (firstName) user.firstName = firstName;
    if (lastName) user.lastName = lastName;
    
    await user.save();
    
    // Log profile update
    await AuditLog.create({
      userId: user._id,
      action: 'profile_updated',
      resourceType: 'user',
      resourceId: user._id.toString(),
      ipAddress: req.ip || req.connection.remoteAddress,
      status: 'success'
    });
    
    res.json({
      success: true,
      user: {
        id: user._id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName
      }
    });
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update profile',
      code: 'UPDATE_ERROR'
    });
  }
}

/**
 * Change password
 */
async function changePassword(req, res) {
  try {
    const { currentPassword, newPassword } = req.body;
    const user = await User.findById(req.userId).select('+password');
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    if (!currentPassword || !newPassword) {
      return res.status(400).json({
        success: false,
        error: 'Current password and new password are required',
        code: 'MISSING_FIELDS'
      });
    }
    
    if (newPassword.length < 8) {
      return res.status(400).json({
        success: false,
        error: 'New password must be at least 8 characters',
        code: 'WEAK_PASSWORD'
      });
    }
    
    // Verify current password
    const isPasswordValid = await user.comparePassword(currentPassword);
    if (!isPasswordValid) {
      return res.status(401).json({
        success: false,
        error: 'Current password is incorrect',
        code: 'INVALID_PASSWORD'
      });
    }
    
    // Update password
    user.password = newPassword;
    await user.save();
    
    // Log password change
    await AuditLog.create({
      userId: user._id,
      action: 'password_changed',
      resourceType: 'security',
      ipAddress: req.ip || req.connection.remoteAddress,
      status: 'success'
    });
    
    res.json({
      success: true,
      message: 'Password changed successfully'
    });
  } catch (error) {
    console.error('Change password error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to change password',
      code: 'PASSWORD_CHANGE_ERROR'
    });
  }
}

/**
 * Request password reset
 */
async function requestPasswordReset(req, res) {
  try {
    const { email } = req.body;
    
    if (!email) {
      return res.status(400).json({
        success: false,
        error: 'Email is required',
        code: 'MISSING_EMAIL'
      });
    }
    
    const user = await User.findOne({ email });
    
    // Always return success to prevent email enumeration
    if (!user) {
      return res.json({
        success: true,
        message: 'If an account exists with this email, a password reset link has been sent'
      });
    }
    
    // Generate reset token
    const resetToken = crypto.randomBytes(32).toString('hex');
    user.passwordResetToken = crypto.createHash('sha256').update(resetToken).digest('hex');
    user.passwordResetExpires = new Date(Date.now() + 60 * 60 * 1000); // 1 hour
    await user.save();
    
    // TODO: Send email with reset link
    // await sendPasswordResetEmail(user.email, resetToken);
    
    // Log password reset request
    await AuditLog.create({
      userId: user._id,
      action: 'password_reset_requested',
      resourceType: 'security',
      ipAddress: req.ip || req.connection.remoteAddress,
      status: 'success'
    });
    
    res.json({
      success: true,
      message: 'If an account exists with this email, a password reset link has been sent'
    });
  } catch (error) {
    console.error('Password reset request error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to process password reset request',
      code: 'RESET_ERROR'
    });
  }
}

/**
 * Reset password with token
 */
async function resetPassword(req, res) {
  try {
    const { token, newPassword } = req.body;
    
    if (!token || !newPassword) {
      return res.status(400).json({
        success: false,
        error: 'Token and new password are required',
        code: 'MISSING_FIELDS'
      });
    }
    
    if (newPassword.length < 8) {
      return res.status(400).json({
        success: false,
        error: 'Password must be at least 8 characters',
        code: 'WEAK_PASSWORD'
      });
    }
    
    // Hash token to compare
    const hashedToken = crypto.createHash('sha256').update(token).digest('hex');
    
    // Find user with valid reset token
    const user = await User.findOne({
      passwordResetToken: hashedToken,
      passwordResetExpires: { $gt: new Date() }
    });
    
    if (!user) {
      return res.status(400).json({
        success: false,
        error: 'Invalid or expired reset token',
        code: 'INVALID_TOKEN'
      });
    }
    
    // Update password
    user.password = newPassword;
    user.passwordResetToken = undefined;
    user.passwordResetExpires = undefined;
    await user.save();
    
    // Log password reset
    await AuditLog.create({
      userId: user._id,
      action: 'password_reset_completed',
      resourceType: 'security',
      ipAddress: req.ip || req.connection.remoteAddress,
      status: 'success'
    });
    
    res.json({
      success: true,
      message: 'Password reset successfully'
    });
  } catch (error) {
    console.error('Password reset error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to reset password',
      code: 'RESET_ERROR'
    });
  }
}

/**
 * Generate API key
 */
async function generateApiKey(req, res) {
  try {
    const { name } = req.body;
    const user = await User.findById(req.userId);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }
    
    const apiKey = user.generateApiKey(name || 'Default');
    await user.save();
    
    // Log API key generation
    await AuditLog.create({
      userId: user._id,
      action: 'api_key_generated',
      resourceType: 'api',
      details: { keyName: name || 'Default' },
      ipAddress: req.ip || req.connection.remoteAddress,
      status: 'success'
    });
    
    res.json({
      success: true,
      apiKey,
      message: 'API key generated successfully. Store it securely - it will not be shown again.'
    });
  } catch (error) {
    console.error('Generate API key error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to generate API key',
      code: 'API_KEY_ERROR'
    });
  }
}

module.exports = {
  register: asyncHandler(register),
  login: asyncHandler(login),
  getProfile: asyncHandler(getProfile),
  updateProfile: asyncHandler(updateProfile),
  changePassword: asyncHandler(changePassword),
  requestPasswordReset: asyncHandler(requestPasswordReset),
  resetPassword: asyncHandler(resetPassword),
  generateApiKey: asyncHandler(generateApiKey)
};

