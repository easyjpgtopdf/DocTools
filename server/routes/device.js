/**
 * Device Quota Routes
 * Handles IP/device fingerprint-based quota tracking
 */

const express = require('express');
const router = express.Router();
const deviceController = require('../controllers/deviceController');

// Get client IP address
router.get('/ip', deviceController.getDeviceIP);

// Check device quota
router.post('/check-quota', deviceController.checkDeviceQuota);

// Increment device quota
router.post('/increment-quota', deviceController.incrementDeviceQuota);

// Get device quota status
router.post('/quota-status', deviceController.getDeviceQuotaStatus);

module.exports = router;

