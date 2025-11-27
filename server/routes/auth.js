/**
 * Authentication Routes
 * User registration, login, password management
 */

const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');
const { authenticate } = require('../middleware/auth');
const { apiLimiter } = require('../middleware/rateLimiter');

// Public routes
router.post('/register', apiLimiter, authController.register);
router.post('/login', apiLimiter, authController.login);
router.post('/password-reset/request', apiLimiter, authController.requestPasswordReset);
router.post('/password-reset/reset', apiLimiter, authController.resetPassword);

// Protected routes
router.get('/profile', authenticate, authController.getProfile);
router.put('/profile', authenticate, authController.updateProfile);
router.post('/change-password', authenticate, authController.changePassword);
router.post('/api-key/generate', authenticate, authController.generateApiKey);

module.exports = router;

