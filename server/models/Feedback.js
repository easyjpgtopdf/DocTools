/**
 * Feedback Model
 * Stores user comments, reviews, and feedback from all pages
 */

const mongoose = require('mongoose');

const feedbackSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true,
    default: 'Anonymous'
  },
  email: {
    type: String,
    trim: true,
    lowercase: true,
    default: null
  },
  rating: {
    type: Number,
    min: 1,
    max: 5,
    default: null
  },
  comment: {
    type: String,
    required: true,
    trim: true
  },
  page: {
    type: String,
    required: true,
    trim: true,
    index: true
  },
  pageName: {
    type: String,
    trim: true
  },
  replies: [{
    name: {
      type: String,
      default: 'Admin'
    },
    comment: {
      type: String,
      required: true
    },
    createdAt: {
      type: Date,
      default: Date.now
    }
  }],
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  },
  updatedAt: {
    type: Date,
    default: Date.now
  },
  // Firebase document ID for migration/sync purposes
  firebaseId: {
    type: String,
    sparse: true,
    index: true
  }
}, {
  timestamps: false
});

// Indexes for fast queries
feedbackSchema.index({ page: 1, createdAt: -1 });
feedbackSchema.index({ createdAt: -1 });
feedbackSchema.index({ rating: 1 });

const Feedback = mongoose.model('Feedback', feedbackSchema);

module.exports = Feedback;

