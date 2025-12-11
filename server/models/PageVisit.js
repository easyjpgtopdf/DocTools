/**
 * Page Visit Model
 * Tracks user page visits and tool usage
 */

const mongoose = require('mongoose');

const pageVisitSchema = new mongoose.Schema({
  user_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  page: {
    type: String,
    required: true,
    index: true
  },
  tool_used: {
    type: String,
    default: null,
    index: true
  },
  credits_spent: {
    type: Number,
    default: 0
  },
  visit_count: {
    type: Number,
    default: 1
  },
  last_visited: {
    type: Date,
    default: Date.now,
    index: true
  },
  first_visited: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Indexes for efficient queries
pageVisitSchema.index({ user_id: 1, page: 1 });
pageVisitSchema.index({ user_id: 1, last_visited: -1 });
pageVisitSchema.index({ tool_used: 1 });

// Method to record a visit
pageVisitSchema.statics.recordVisit = async function(userId, page, toolUsed = null, creditsSpent = 0) {
  const visit = await this.findOne({ user_id: userId, page });
  
  if (visit) {
    visit.visit_count += 1;
    visit.last_visited = new Date();
    if (toolUsed) visit.tool_used = toolUsed;
    visit.credits_spent += creditsSpent;
    await visit.save();
  } else {
    await this.create({
      user_id: userId,
      page,
      tool_used: toolUsed,
      credits_spent: creditsSpent,
      visit_count: 1
    });
  }
};

module.exports = mongoose.model('PageVisit', pageVisitSchema);

