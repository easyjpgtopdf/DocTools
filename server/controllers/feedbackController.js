/**
 * Feedback Controller
 * Handles feedback submission and retrieval
 */

const Feedback = require('../models/Feedback');
const { asyncHandler } = require('../middleware/errorHandler');

/**
 * Get all feedback with optional page filter
 */
exports.getAllFeedback = asyncHandler(async (req, res) => {
  const { page } = req.query;
  
  let query = {};
  if (page && page !== 'all') {
    query.page = page;
  }

  const feedbacks = await Feedback.find(query)
    .sort({ createdAt: -1 })
    .limit(500) // Limit to prevent huge responses
    .lean();

  // Format dates for frontend
  const formattedFeedbacks = feedbacks.map(fb => ({
    ...fb,
    date: fb.createdAt ? new Date(fb.createdAt).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }) : 'Recently',
    createdAt: fb.createdAt ? new Date(fb.createdAt).toISOString() : null
  }));

  res.json({
    success: true,
    count: formattedFeedbacks.length,
    feedbacks: formattedFeedbacks
  });
});

/**
 * Get unique pages that have feedback
 */
exports.getFeedbackPages = asyncHandler(async (req, res) => {
  const pages = await Feedback.distinct('page');
  
  const pageCounts = await Promise.all(
    pages.map(async (page) => {
      const count = await Feedback.countDocuments({ page });
      return { page, count };
    })
  );

  res.json({
    success: true,
    pages: pageCounts
  });
});

/**
 * Submit new feedback
 */
exports.submitFeedback = asyncHandler(async (req, res) => {
  const { name, email, rating, comment, page, pageName } = req.body;

  if (!comment || !comment.trim()) {
    return res.status(400).json({
      success: false,
      message: 'Comment is required'
    });
  }

  if (!page) {
    return res.status(400).json({
      success: false,
      message: 'Page identifier is required'
    });
  }

  const feedback = new Feedback({
    name: name?.trim() || 'Anonymous',
    email: email?.trim() || null,
    rating: rating ? parseInt(rating) : null,
    comment: comment.trim(),
    page: page.trim(),
    pageName: pageName?.trim() || page.replace('.html', '').replace(/-/g, ' ')
  });

  await feedback.save();

  res.status(201).json({
    success: true,
    message: 'Feedback submitted successfully',
    feedback: {
      ...feedback.toObject(),
      date: new Date(feedback.createdAt).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }
  });
});

/**
 * Add reply to feedback
 */
exports.addReply = asyncHandler(async (req, res) => {
  const { feedbackId } = req.params;
  const { name, comment } = req.body;

  if (!comment || !comment.trim()) {
    return res.status(400).json({
      success: false,
      message: 'Reply comment is required'
    });
  }

  const feedback = await Feedback.findById(feedbackId);
  
  if (!feedback) {
    return res.status(404).json({
      success: false,
      message: 'Feedback not found'
    });
  }

  feedback.replies.push({
    name: name?.trim() || 'Admin',
    comment: comment.trim(),
    createdAt: new Date()
  });

  feedback.updatedAt = new Date();
  await feedback.save();

  res.json({
    success: true,
    message: 'Reply added successfully',
    feedback: feedback.toObject()
  });
});

