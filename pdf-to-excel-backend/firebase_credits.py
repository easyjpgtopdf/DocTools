"""
Firebase Firestore Credit Management
Fetches real credits from Firebase for logged-in users only
"""

import os
import logging
from typing import Optional, Dict
from google.cloud import firestore

logger = logging.getLogger(__name__)

# Initialize Firestore client (uses Application Default Credentials)
_firestore_client = None

def get_firestore_client():
    """Initialize and return Firestore client."""
    global _firestore_client
    if _firestore_client is None:
        try:
            _firestore_client = firestore.Client()
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            _firestore_client = None
    return _firestore_client


def get_credits_from_firebase(user_id: str) -> Optional[int]:
    """
    Get real credits from Firebase Firestore for a logged-in user.
    
    Args:
        user_id: Firebase user ID (UID)
    
    Returns:
        Credit balance (int) or None if user not found or error
    """
    try:
        db = get_firestore_client()
        if not db:
            logger.warning("Firestore client not available, cannot fetch credits")
            return None
        
        # Get user document from Firestore
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            logger.info(f"User {user_id} not found in Firestore")
            return 0  # New user starts with 0 credits
        
        user_data = user_doc.to_dict()
        
        # Get credits field (ensure it's a number)
        credits = user_data.get('credits', 0)
        
        # Ensure credits is a number
        if isinstance(credits, str):
            credits = float(credits) if credits else 0
        elif credits is None:
            credits = 0
        
        credits = int(credits) if credits >= 0 else 0
        
        logger.info(f"Fetched credits for user {user_id}: {credits}")
        return credits
        
    except Exception as e:
        logger.error(f"Error fetching credits from Firebase for user {user_id}: {e}")
        return None


def deduct_credits_from_firebase(user_id: str, amount: int) -> bool:
    """
    Deduct credits from Firebase Firestore.
    
    Args:
        user_id: Firebase user ID (UID)
        amount: Credits to deduct
    
    Returns:
        True if successful, False if insufficient credits or error
    """
    try:
        db = get_firestore_client()
        if not db:
            logger.warning("Firestore client not available, cannot deduct credits")
            return False
        
        user_ref = db.collection('users').document(user_id)
        
        # First, get current credits to check
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            logger.warning(f"User {user_id} not found in Firestore")
            return False
        
        user_data = user_doc.to_dict()
        current_credits = user_data.get('credits', 0)
        
        # Ensure credits is a number
        if isinstance(current_credits, str):
            current_credits = float(current_credits) if current_credits else 0
        elif current_credits is None:
            current_credits = 0
        
        current_credits = int(current_credits) if current_credits >= 0 else 0
        
        # Check if sufficient credits
        if current_credits < amount:
            logger.warning(f"Insufficient credits for user {user_id}: {current_credits} < {amount}")
            return False
        
        # Deduct credits using update (atomic operation with Increment)
        user_ref.update({
            'credits': firestore.Increment(-amount),
            'totalCreditsUsed': firestore.Increment(amount),
            'lastCreditUpdate': firestore.SERVER_TIMESTAMP
        })
        
        logger.info(f"Deducted {amount} credits from user {user_id}. New balance: {new_credits}")
        return True
        
    except Exception as e:
        logger.error(f"Error deducting credits from Firebase for user {user_id}: {e}")
        return False


def get_credit_info_from_firebase(user_id: str) -> Dict:
    """
    Get detailed credit information from Firebase.
    
    Args:
        user_id: Firebase user ID (UID)
    
    Returns:
        Dict with credits, totalCreditsEarned, totalCreditsUsed, etc.
    """
    try:
        db = get_firestore_client()
        if not db:
            return {"credits": 0, "error": "Firestore not available"}
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return {
                "credits": 0,
                "totalCreditsEarned": 0,
                "totalCreditsUsed": 0,
                "created_at": None
            }
        
        user_data = user_doc.to_dict()
        
        # Ensure all credit fields are numbers
        credits = user_data.get('credits', 0)
        if isinstance(credits, str):
            credits = float(credits) if credits else 0
        elif credits is None:
            credits = 0
        credits = int(credits) if credits >= 0 else 0
        
        total_earned = user_data.get('totalCreditsEarned', 0)
        if isinstance(total_earned, str):
            total_earned = float(total_earned) if total_earned else 0
        elif total_earned is None:
            total_earned = 0
        total_earned = int(total_earned) if total_earned >= 0 else 0
        
        total_used = user_data.get('totalCreditsUsed', 0)
        if isinstance(total_used, str):
            total_used = float(total_used) if total_used else 0
        elif total_used is None:
            total_used = 0
        total_used = int(total_used) if total_used >= 0 else 0
        
        created_at = user_data.get('createdAt')
        if created_at:
            created_at = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)
        
        return {
            "credits": credits,
            "totalCreditsEarned": total_earned,
            "totalCreditsUsed": total_used,
            "created_at": created_at
        }
        
    except Exception as e:
        logger.error(f"Error getting credit info from Firebase for user {user_id}: {e}")
        return {"credits": 0, "error": str(e)}

