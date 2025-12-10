"""
Credit management system for PDF to Excel conversion.
In-memory implementation (can be replaced with database later).
"""

from typing import Dict
from datetime import datetime

# In-memory credit storage
# Format: {user_id: {"credits": int, "created_at": datetime}}
_credits: Dict[str, Dict] = {}

# Default free credits for new users
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
    """Get current credit balance for a user."""
    if user_id not in _credits:
        # New user gets free credits
        _credits[user_id] = {
            "credits": DEFAULT_FREE_CREDITS,
            "created_at": datetime.now()
        }
    return _credits[user_id]["credits"]


def deduct_credits(user_id: str, amount: int) -> bool:
    """
    Deduct credits from user account.
    Returns True if successful, False if insufficient credits.
    """
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
    """Get detailed credit information for a user."""
    credits = get_credits(user_id)
    user_data = _credits.get(user_id, {})
    
    return {
        "credits": credits,
        "created_at": user_data.get("created_at").isoformat() if user_data.get("created_at") else None
    }

