"""
Credit management system for PDF to Excel conversion.
Uses Firebase Firestore for real credits (logged-in users only).
"""

from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Try to import Firebase credits module
try:
    from firebase_credits import (
        get_credits_from_firebase,
        deduct_credits_from_firebase,
        get_credit_info_from_firebase
    )
    FIREBASE_AVAILABLE = True
except ImportError:
    logger.warning("Firebase credits module not available, using fallback")
    FIREBASE_AVAILABLE = False
    # Fallback in-memory storage (for development/testing only)
    _credits: Dict[str, Dict] = {}
    DEFAULT_FREE_CREDITS = 5


def get_user_id(request) -> str:
    """
    Extract user ID from request.
    For now, uses a simple session-based approach.
    In production, use proper authentication (JWT, session, etc.)
    """
    # Try to get user_id from headers or query params
    user_id = request.headers.get("X-User-ID") or request.query_params.get("user_id")
    
    # If no user_id provided, generate a temporary one (for demo)
    # In production, this should come from authentication
    if not user_id:
        # Use a default anonymous user for now
        user_id = "anonymous"
    
    return user_id


def get_credits(user_id: str) -> int:
    """
    Get current credit balance for a user.
    Fetches from Firebase Firestore for real logged-in users.
    
    CRITICAL: Returns 0 only if user explicitly has 0 credits in Firebase.
    Returns 0 if user not found to prevent errors, but logs warning.
    """
    # TEMPORARY TESTING BYPASS
    TESTING_UID = "NLhUrh6ZurQInLRV875Ktxw9rDn2"
    if user_id == TESTING_UID:
        logger.warning(f"🧪 TESTING MODE: Bypassing credit fetch in credit.py for {user_id}, returning 1000")
        return 1000
    
    # Try Firebase first (real credits for logged-in users)
    if FIREBASE_AVAILABLE:
        credits = get_credits_from_firebase(user_id)
        if credits is not None:
            return credits
        # If Firebase returns None (error or user not found)
        # Check if user_id looks invalid (localStorage ID instead of Firebase UID)
        if user_id and (user_id.startswith("user_") or user_id.startswith("anonymous_") or user_id == "anonymous"):
            logger.error(f"CRITICAL: Invalid user_id format detected: {user_id}")
            logger.error("This is a localStorage ID, not a Firebase UID!")
            logger.error("User must be logged in with Firebase to access real credits.")
            logger.error("Returning 0, but this is likely because user is not logged in.")
        else:
            logger.error(f"Firebase credit fetch failed for {user_id}. This might indicate:")
            logger.error("  1. Firebase not initialized properly")
            logger.error("  2. User ID mismatch (check Firebase UID)")
            logger.error("  3. Firestore connection issue")
            logger.error("  4. User document doesn't exist in Firestore")
        logger.error("Returning 0 as fallback, but this may be incorrect if user has credits!")
        return 0
    
    # Fallback: in-memory (development/testing only)
    if user_id not in _credits:
        _credits[user_id] = {
            "credits": DEFAULT_FREE_CREDITS,
            "created_at": datetime.now()
        }
    return _credits[user_id]["credits"]


def deduct_credits(user_id: str, amount: int) -> bool:
    """
    Deduct credits from user account.
    Uses Firebase Firestore for real logged-in users.
    Returns True if successful, False if insufficient credits.
    """
    # Try Firebase first (real credits for logged-in users)
    if FIREBASE_AVAILABLE:
        return deduct_credits_from_firebase(user_id, amount)
    
    # Fallback: in-memory (development/testing only)
    current_credits = get_credits(user_id)
    
    if current_credits < amount:
        return False
    
    _credits[user_id]["credits"] = current_credits - amount
    return True


def add_credits(user_id: str, amount: int):
    """Add credits to user account."""
    if user_id not in _credits:
        _credits[user_id] = {
            "credits": DEFAULT_FREE_CREDITS,
            "created_at": datetime.now()
        }
    _credits[user_id]["credits"] += amount


def check_sufficient_credits(user_id: str, pages: int) -> bool:
    """Check if user has sufficient credits for the number of pages."""
    current_credits = get_credits(user_id)
    return current_credits >= pages


def get_credit_info(user_id: str) -> Dict:
    """
    Get detailed credit information for a user.
    Fetches from Firebase Firestore for real logged-in users.
    """
    # Try Firebase first (real credits for logged-in users)
    if FIREBASE_AVAILABLE:
        credit_info = get_credit_info_from_firebase(user_id)
        if credit_info:
            return credit_info
    
    # Fallback: in-memory (development/testing only)
    credits = get_credits(user_id)
    user_data = _credits.get(user_id, {})
    
    return {
        "credits": credits,
        "created_at": user_data.get("created_at").isoformat() if user_data.get("created_at") else None
    }

