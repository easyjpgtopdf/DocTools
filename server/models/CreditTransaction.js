/**
 * Credit Transaction Model
 * Tracks all credit transactions (purchases, deductions, expirations)
 */

const mongoose = require('mongoose');

const creditTransactionSchema = new mongoose.Schema({
  user_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  type: {
    type: String,
    enum: ['purchase', 'deduct', 'expire'],
    required: true,
    index: true
  },
  credits_change: {
    type: Number,
    required: true
  },
  balance_after: {
    type: Number,
    required: true
  },
  metadata: {
    // For purchase transactions
    orderId: String,
    paymentId: String,
    plan: String,
    amount: Number,
    currency: String,
    
    // For deduct transactions
    tool_used: String,
    page: String,
    file_name: String,
    page_count: Number,
    processor: String,
    
    // For expire transactions
    expired_credits: Number
  },
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  }
}, {
  timestamps: true
});

// Indexes for efficient queries
creditTransactionSchema.index({ user_id: 1, createdAt: -1 });
creditTransactionSchema.index({ type: 1, createdAt: -1 });

module.exports = mongoose.model('CreditTransaction', creditTransactionSchema);

