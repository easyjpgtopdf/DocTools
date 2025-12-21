"""
Daily Free Tier Usage Tracking
Tracks daily usage for both anonymous and authenticated users.
Free limits: 10 pages/day (text), 5 pages/day (OCR)
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from firebase_admin import firestore
import logging

logger = logging.getLogger(__name__)

# Free tier daily limits (ONLY for anonymous/unauthenticated users)
FREE_TIER_DAILY_PAGES_TEXT = 10  # 10 pages per day for text-based conversion
FREE_TIER_DAILY_PAGES_OCR = 3    # 3 pages per day for OCR conversion
FREE_TIER_MAX_FILE_SIZE_MB = 20  # Maximum 20MB file size for anonymous users (free tier)

def get_firestore_client():
    """Get Firestore client."""
    try:
        return firestore.client()
    except Exception as e:
        logger.error(f"Failed to get Firestore client: {e}")
        return None

def get_daily_usage_key(user_id: str, date_str: Optional[str] = None) -> str:
    """Generate key for daily usage tracking."""
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
    return f"daily_usage:{user_id}:{date_str}"

def get_today_usage(user_id: str, db: Optional[firestore.Client] = None) -> Dict:
    """
    Get today's usage for a user.
    
    Returns:
        {
            'text_pages': int,
            'ocr_pages': int,
            'text_remaining': int,
            'ocr_remaining': int
        }
    """
    if db is None:
        db = get_firestore_client()
    
    if db is None:
        # If Firestore unavailable, allow usage (graceful degradation)
        logger.warning("Firestore unavailable, allowing usage")
        return {
            'text_pages': 0,
            'ocr_pages': 0,
            'text_remaining': FREE_TIER_DAILY_PAGES_TEXT,
            'ocr_remaining': FREE_TIER_DAILY_PAGES_OCR
        }
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    usage_key = get_daily_usage_key(user_id, today)
    
    try:
        usage_doc = db.collection('daily_usage').document(usage_key).get()
        if usage_doc.exists:
            data = usage_doc.to_dict()
            text_pages = data.get('text_pages', 0)
            ocr_pages = data.get('ocr_pages', 0)
        else:
            text_pages = 0
            ocr_pages = 0
        
        return {
            'text_pages': text_pages,
            'ocr_pages': ocr_pages,
            'text_remaining': max(0, FREE_TIER_DAILY_PAGES_TEXT - text_pages),
            'ocr_remaining': max(0, FREE_TIER_DAILY_PAGES_OCR - ocr_pages)
        }
    except Exception as e:
        logger.error(f"Error getting daily usage: {e}")
        # Graceful degradation - allow usage if tracking fails
        return {
            'text_pages': 0,
            'ocr_pages': 0,
            'text_remaining': FREE_TIER_DAILY_PAGES_TEXT,
            'ocr_remaining': FREE_TIER_DAILY_PAGES_OCR
        }

def can_use_free_tier(user_id: str, pages: int, is_ocr: bool, db: Optional[firestore.Client] = None) -> Dict:
    """
    Check if user can use free tier for this conversion.
    
    Args:
        user_id: User ID (or 'anonymous' for anonymous users)
        pages: Number of pages in the PDF
        is_ocr: Whether OCR will be used
        
    Returns:
        {
            'allowed': bool,
            'reason': str,
            'remaining_text': int,
            'remaining_ocr': int
        }
    """
    usage = get_today_usage(user_id, db)
    
    if is_ocr:
        # OCR conversion
        if pages <= usage['ocr_remaining']:
            return {
                'allowed': True,
                'reason': 'Free tier OCR available',
                'remaining_text': usage['text_remaining'],
                'remaining_ocr': usage['ocr_remaining'] - pages
            }
        else:
            return {
                'allowed': False,
                'reason': f"Free OCR limit exceeded. You've used {usage['ocr_pages']}/{FREE_TIER_DAILY_PAGES_OCR} OCR pages today. {pages} more pages needed.",
                'remaining_text': usage['text_remaining'],
                'remaining_ocr': usage['ocr_remaining']
            }
    else:
        # Text-based conversion
        if pages <= usage['text_remaining']:
            return {
                'allowed': True,
                'reason': 'Free tier text conversion available',
                'remaining_text': usage['text_remaining'] - pages,
                'remaining_ocr': usage['ocr_remaining']
            }
        else:
            return {
                'allowed': False,
                'reason': f"Free text limit exceeded. You've used {usage['text_pages']}/{FREE_TIER_DAILY_PAGES_TEXT} text pages today. {pages} more pages needed.",
                'remaining_text': usage['text_remaining'],
                'remaining_ocr': usage['ocr_remaining']
            }

def record_daily_usage(user_id: str, pages: int, is_ocr: bool, db: Optional[firestore.Client] = None) -> None:
    """
    Record daily usage for free tier.
    
    Args:
        user_id: User ID (or 'anonymous' for anonymous users)
        pages: Number of pages converted
        is_ocr: Whether OCR was used
    """
    if db is None:
        db = get_firestore_client()
    
    if db is None:
        logger.warning("Cannot record usage - Firestore unavailable")
        return
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    usage_key = get_daily_usage_key(user_id, today)
    
    try:
        usage_ref = db.collection('daily_usage').document(usage_key)
        usage_ref.set({
            'user_id': user_id,
            'date': today,
            'text_pages': firestore.Increment(pages if not is_ocr else 0),
            'ocr_pages': firestore.Increment(pages if is_ocr else 0),
            'last_updated': firestore.SERVER_TIMESTAMP
        }, merge=True)
        logger.info(f"Recorded daily usage: {user_id}, {pages} pages, OCR: {is_ocr}")
    except Exception as e:
        logger.error(f"Error recording daily usage: {e}")

