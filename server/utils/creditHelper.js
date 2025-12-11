/**
 * Credit Helper Utilities
 * Safe helper functions for credit operations that won't break if models fail
 */

/**
 * Safely get user credits without throwing errors
 */
async function safeGetUserCredits(userId) {
  try {
    const UserCredits = require('../models/UserCredits');
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
  safeGetUserCredits,
  safeCheckCredits
};

