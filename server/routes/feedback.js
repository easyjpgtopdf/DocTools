/**
 * Feedback Routes
 */

const express = require('express');
const router = express.Router();
const feedbackController = require('../controllers/feedbackController');

// Get all feedback (with optional page filter)
router.get('/', feedbackController.getAllFeedback);

// Get unique pages
router.get('/pages', feedbackController.getFeedbackPages);

// Submit new feedback
router.post('/', feedbackController.submitFeedback);

// Add reply to feedback
router.post('/:feedbackId/reply', feedbackController.addReply);

module.exports = router;

