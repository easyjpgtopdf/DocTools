"""
Complete Credit Management System for PDF Tools.
Handles credit operations, transaction history, and billing integration.
"""
from typing import Dict, List, Optional
from datetime import datetime
from firebase_admin import firestore
import logging

logger = logging.getLogger(__name__)

# Global Firestore client
_db_client = None

def get_firestore_client():
    """Get or initialize Firestore client."""
    global _db_client
    if _db_client is None:
        try:
            _db_client = firestore.client()
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            return None
    return _db_client

# Credit pricing constants (for logged-in/premium users)
# Word conversion pricing
CREDITS_PER_PAGE_TEXT = 2.0   # 2 credits per text page (Premium)
CREDITS_PER_PAGE_OCR = 2.0    # 2 credits per OCR page (Premium)
# Excel conversion pricing (Premium Pro)
CREDITS_PER_PAGE_EXCEL = 2.0  # 2 credits per page for Excel conversion
# Premium user file size limit
PREMIUM_MAX_FILE_SIZE_MB = 50  # Maximum 50MB file size for logged-in users


def calculate_required_credits(pages: int, used_docai: bool) -> float:
    """
    Calculate required credits based on page count and conversion method.
    
    Args:
        pages: Number of pages in the PDF
        used_docai: Whether OCR (Document AI) was used
        
    Returns:
        Required credits as float
    """
    if used_docai:
        return pages * CREDITS_PER_PAGE_OCR
    else:
        return pages * CREDITS_PER_PAGE_TEXT


def initialize_user_credits(user_id: str, db: Optional[firestore.Client] = None) -> None:
    """Initialize user credits in Firestore (if not exists)."""
    try:
        if db is None:
            db = get_firestore_client()
        if db is None:
            logger.error("Firestore client not available")
            return
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            user_ref.set({
                'credits': 0,
                'totalCreditsEarned': 0,
                'totalCreditsUsed': 0,
                'creditHistory': [],
                'createdAt': firestore.SERVER_TIMESTAMP,
                'lastCreditUpdate': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Initialized credits for user: {user_id}")
        else:
            # Ensure credit fields exist
            data = user_doc.to_dict()
            updates = {}
            if 'credits' not in data:
                updates['credits'] = 0
            if 'totalCreditsEarned' not in data:
                updates['totalCreditsEarned'] = 0
            if 'totalCreditsUsed' not in data:
                updates['totalCreditsUsed'] = 0
            if 'creditHistory' not in data:
                updates['creditHistory'] = []
            
            if updates:
                updates['lastCreditUpdate'] = firestore.SERVER_TIMESTAMP
                user_ref.update(updates)
                logger.info(f"Updated credit fields for user: {user_id}")
    except Exception as e:
        logger.error(f"Error initializing user credits: {e}", exc_info=True)


def get_user_credits(user_id: str, db: Optional[firestore.Client] = None) -> Dict:
    """Get current credit balance and info for a user."""
    try:
        if db is None:
            db = get_firestore_client()
        if db is None:
            return {'credits': 0, 'error': 'Database not available'}
        
        initialize_user_credits(user_id, db)
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return {'credits': 0}
        
        data = user_doc.to_dict()
        return {
            'credits': float(data.get('credits', 0)),
            'totalCreditsEarned': float(data.get('totalCreditsEarned', 0)),
            'totalCreditsUsed': float(data.get('totalCreditsUsed', 0))
        }
    except Exception as e:
        logger.error(f"Error getting user credits: {e}", exc_info=True)
        return {'credits': 0, 'error': str(e)}


def has_sufficient_credits(user_id: str, required_credits: float, db: Optional[firestore.Client] = None) -> Dict:
    """Check if user has sufficient credits."""
    credit_info = get_user_credits(user_id, db)
    available = credit_info.get('credits', 0)
    
    return {
        'hasCredits': available >= required_credits,
        'creditsAvailable': available,
        'requiredCredits': required_credits
    }


def deduct_credits(
    user_id: str,
    amount: float,
    reason: str = 'PDF conversion',
    metadata: Optional[Dict] = None,
    db: Optional[firestore.Client] = None
) -> Dict:
    """Deduct credits from user account and record transaction."""
    try:
        if db is None:
            db = get_firestore_client()
        if db is None:
            return {'success': False, 'error': 'Database not available'}
        
        # Check if user has sufficient credits
        credit_check = has_sufficient_credits(user_id, amount, db)
        if not credit_check['hasCredits']:
            return {
                'success': False,
                'error': 'NOT_ENOUGH_CREDITS',
                'creditsAvailable': credit_check['creditsAvailable'],
                'requiredCredits': amount
            }
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            initialize_user_credits(user_id, db)
            user_doc = user_ref.get()
        
        current_credits = float(user_doc.to_dict().get('credits', 0))
        new_credits = current_credits - amount
        
        # Update credits
        user_ref.update({
            'credits': firestore.Increment(-amount),
            'totalCreditsUsed': firestore.Increment(amount),
            'lastCreditUpdate': firestore.SERVER_TIMESTAMP
        })
        
        # Record transaction in history
        transaction = {
            'id': f"txn_{datetime.utcnow().isoformat().replace(':', '-')}_{user_id[:8]}",
            'date': firestore.SERVER_TIMESTAMP,
            'type': 'deduct',
            'credits': amount,
            'description': reason,
            'creditsBefore': current_credits,
            'creditsAfter': new_credits,
            **(metadata or {})
        }
        
        user_ref.update({
            'creditHistory': firestore.ArrayUnion([transaction])
        })
        
        logger.info(f"Deducted {amount} credits from user {user_id}. Remaining: {new_credits}")
        
        return {
            'success': True,
            'creditsDeducted': amount,
            'creditsRemaining': new_credits,
            'creditsBefore': current_credits
        }
    except Exception as e:
        logger.error(f"Error deducting credits: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def add_credits(
    user_id: str,
    amount: float,
    reason: str = 'Credit purchase',
    metadata: Optional[Dict] = None,
    db: Optional[firestore.Client] = None
) -> Dict:
    """Add credits to user account and record transaction."""
    try:
        if db is None:
            db = get_firestore_client()
        if db is None:
            return {'success': False, 'error': 'Database not available'}
        
        initialize_user_credits(user_id, db)
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        current_credits = float(user_doc.to_dict().get('credits', 0))
        new_credits = current_credits + amount
        
        # Update credits
        user_ref.update({
            'credits': firestore.Increment(amount),
            'totalCreditsEarned': firestore.Increment(amount),
            'lastCreditUpdate': firestore.SERVER_TIMESTAMP
        })
        
        # Record transaction
        transaction = {
            'id': f"txn_{datetime.utcnow().isoformat().replace(':', '-')}_{user_id[:8]}",
            'date': firestore.SERVER_TIMESTAMP,
            'type': 'add',
            'credits': amount,
            'description': reason,
            'creditsBefore': current_credits,
            'creditsAfter': new_credits,
            **(metadata or {})
        }
        
        user_ref.update({
            'creditHistory': firestore.ArrayUnion([transaction])
        })
        
        logger.info(f"Added {amount} credits to user {user_id}. New balance: {new_credits}")
        
        return {
            'success': True,
            'creditsAdded': amount,
            'creditsRemaining': new_credits,
            'creditsBefore': current_credits
        }
    except Exception as e:
        logger.error(f"Error adding credits: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def get_credit_history(user_id: str, limit: int = 50, db: Optional[firestore.Client] = None) -> List[Dict]:
    """Get credit transaction history for a user."""
    try:
        if db is None:
            db = get_firestore_client()
        if db is None:
            return []
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return []
        
        history = user_doc.to_dict().get('creditHistory', [])
        
        # Sort by date (newest first) and limit
        sorted_history = sorted(
            history,
            key=lambda x: x.get('date', datetime.min),
            reverse=True
        )[:limit]
        
        return sorted_history
    except Exception as e:
        logger.error(f"Error getting credit history: {e}", exc_info=True)
        return []

