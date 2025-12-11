/**
 * Credit Helper Utilities
 * Helper functions for credit operations
 */

const UserCredits = require('../models/UserCredits');
const CreditTransaction = require('../models/CreditTransaction');
const PageVisit = require('../models/PageVisit');

const CREDIT_EXPIRY_DAYS = 90;

/**
 * Deduct credits from user account
 */
async function deductCreditsFromUser(userId, creditsToDeduct, toolUsed) {
  try {
    const userCredit = await UserCredits.getOrCreate(userId);
    
    if (userCredit.credits < creditsToDeduct) {
      return { 
        success: false, 
        message: 'Insufficient credits',
        credits: userCredit.credits
      };
    }

    await userCredit.deductCredits(creditsToDeduct);
    
    return { 
      success: true, 
      newBalance: userCredit.credits 
    };
  } catch (error) {
    console.error(`Error deducting credits for user ${userId}:`, error);
    return { success: false, message: 'Failed to deduct credits' };
  }
}

/**
 * Record a credit transaction
 */
async function recordCreditTransaction(userId, type, creditsChange, balanceAfter, metadata = {}) {
  try {
    await CreditTransaction.create({
      user_id: userId,
      type,
      credits_change: creditsChange,
      balance_after: balanceAfter,
      metadata
    });
  } catch (error) {
    console.error(`Error recording credit transaction for user ${userId}:`, error);
  }
}

/**
 * Record a page visit and tool usage
 */
async function recordPageVisit(userId, page, toolUsed = null, creditsSpent = 0) {
  try {
    await PageVisit.recordVisit(userId, page, toolUsed, creditsSpent);
  } catch (error) {
    console.error(`Error recording page visit for user ${userId}:`, error);
  }
}

/**
 * Safely get user credits without throwing errors
 */
async function safeGetUserCredits(userId) {
  try {
    return await UserCredits.getOrCreate(userId);
  } catch (error) {
    console.error('Error getting user credits:', error);
    return null;
  }
}

/**
 * Safely check if user has enough credits
 */
async function safeCheckCredits(userId, requiredAmount) {
  try {
    const credits = await safeGetUserCredits(userId);
    if (!credits) return { hasEnough: false, balance: 0 };
    
    credits.checkExpiry();
    return {
      hasEnough: credits.credits >= requiredAmount,
      balance: credits.credits
    };
  } catch (error) {
    console.error('Error checking credits:', error);
    return { hasEnough: false, balance: 0 };
  }
}

module.exports = {
  deductCreditsFromUser,
  recordCreditTransaction,
  recordPageVisit,
  safeGetUserCredits,
  safeCheckCredits
};

