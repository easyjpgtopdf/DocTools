/**
 * Credit Deduction Middleware
 * Automatically deducts credits when premium tools are used
 */

const UserCredits = require('../models/UserCredits');
const CreditTransaction = require('../models/CreditTransaction');
const PageVisit = require('../models/PageVisit');

/**
 * Middleware to deduct credits for premium tool usage
 * @param {number} creditAmount - Amount of credits to deduct
 * @param {string} toolName - Name of the tool being used
 */
function deductCredits(creditAmount, toolName) {
  return async (req, res, next) => {
    try {
      // Skip if user is not authenticated
      if (!req.userId) {
        return next();
      }

      // Get user credits
      const userCredits = await UserCredits.getOrCreate(req.userId);
      
      // Check expiry
      userCredits.checkExpiry();

      // Check if user has enough credits
      if (userCredits.credits < creditAmount) {
        return res.status(402).json({
          success: false,
          error: 'Insufficient credits',
          credits: userCredits.credits,
          required: creditAmount,
          message: `You need ${creditAmount} credits to use this feature. Please purchase credits.`
        });
      }

      // Store original response methods safely
      const originalJson = res.json.bind(res);
      const originalSend = res.send.bind(res);
      let creditsDeducted = false;

      // Helper to deduct credits once
      const deductOnce = () => {
        if (!creditsDeducted && res.statusCode < 400) {
          creditsDeducted = true;
          deductCreditsAsync(req.userId, creditAmount, toolName, req.path, req.body);
        }
      };

      // Override res.json to deduct credits after successful response
      res.json = function(data) {
        // Only deduct if the response is successful
        if (data && data.success !== false && res.statusCode < 400) {
          deductOnce();
        }
        return originalJson.call(this, data);
      };

      // Override res.send for file downloads
      res.send = function(data) {
        // Only deduct if the response is successful
        if (res.statusCode < 400) {
          deductOnce();
        }
        return originalSend.call(this, data);
      };

      // Also handle res.end for completeness
      const originalEnd = res.end.bind(res);
      res.end = function(data, encoding) {
        if (res.statusCode < 400 && !creditsDeducted) {
          deductOnce();
        }
        return originalEnd.call(this, data, encoding);
      };

      next();
    } catch (error) {
      console.error('Error in credit deduction middleware:', error);
      // Don't block the request if credit deduction fails
      next();
    }
  };
}

/**
 * Async function to deduct credits (non-blocking)
 */
async function deductCreditsAsync(userId, amount, toolName, page, metadata = {}) {
  try {
    const userCredits = await UserCredits.getOrCreate(userId);
    
    // Double-check balance
    if (userCredits.credits < amount) {
      console.warn(`Insufficient credits for user ${userId}. Balance: ${userCredits.credits}, Required: ${amount}`);
      return;
    }

    // Deduct credits
    await userCredits.deductCredits(amount);

    // Record transaction
    await CreditTransaction.create({
      user_id: userId,
      type: 'deduct',
      credits_change: -amount,
      balance_after: userCredits.credits,
      metadata: {
        tool_used: toolName,
        page: page,
        file_name: metadata.file_name || metadata.fileName || null,
        page_count: metadata.page_count || metadata.pageCount || null,
        processor: metadata.processor || null
      }
    });

    // Record page visit
    if (page) {
      await PageVisit.recordVisit(userId, page, toolName, amount);
    }

    console.log(`✓ Deducted ${amount} credits from user ${userId} for ${toolName}`);
  } catch (error) {
    console.error('Error deducting credits asynchronously:', error);
  }
}

/**
 * Check if user has enough credits (non-deducting)
 */
async function checkCredits(req, res, next) {
  try {
    if (!req.userId) {
      return next();
    }

    const userCredits = await UserCredits.getOrCreate(req.userId);
    userCredits.checkExpiry();

    // Attach credit info to request
    req.userCredits = {
      balance: userCredits.credits,
      expiresAt: userCredits.expiresAt,
      lastUsedAt: userCredits.lastUsedAt
    };

    next();
  } catch (error) {
    console.error('Error checking credits:', error);
    next();
  }
}

module.exports = {
  deductCredits,
  checkCredits
};

