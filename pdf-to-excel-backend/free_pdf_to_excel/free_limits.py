"""
Abuse control and limits for FREE PDF to Excel conversion.
Tracks usage per device/IP with 24-hour reset.
"""

import hashlib
import time
from typing import Dict, Tuple, Optional

# Constants
MAX_FREE_PAGES_PER_DAY = 20  # Updated: 20 pages per day
MAX_FREE_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
FREE_RESET_HOURS = 24

# In-memory storage (can be moved to Redis/DB for production)
_usage_tracker: Dict[str, Dict] = {}


def generate_free_key(ip_address: str, user_agent: str = "", fingerprint: str = "") -> str:
    """
    Generate a unique key for abuse control.
    
    Args:
        ip_address: Client IP address
        user_agent: Browser user agent
        fingerprint: Browser fingerprint from client
        
    Returns:
        Unique key (16-char hex string)
    """
    combined = f"{ip_address}|{user_agent}|{fingerprint}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def check_limits(free_key: str, requested_pages: int = 1) -> Tuple[bool, str, int]:
    """
    Check if user has exceeded free limits.
    
    Args:
        free_key: Unique identifier for the user/device
        requested_pages: Number of pages requested
        
    Returns:
        (allowed, message, pages_remaining)
    """
    now = time.time()
    
    # Initialize if first time
    if free_key not in _usage_tracker:
        _usage_tracker[free_key] = {
            'pages_used_today': 0,
            'last_reset_timestamp': now,
            'last_file_size': 0
        }
        pages_remaining = MAX_FREE_PAGES_PER_DAY
    else:
        user_data = _usage_tracker[free_key]
        
        # Reset if 24 hours passed
        if now - user_data['last_reset_timestamp'] >= FREE_RESET_HOURS * 3600:
            user_data['pages_used_today'] = 0
            user_data['last_reset_timestamp'] = now
        
        pages_remaining = MAX_FREE_PAGES_PER_DAY - user_data['pages_used_today']
    
    # Check if enough pages remaining
    if pages_remaining < requested_pages:
        return False, f"Daily limit reached. You can convert up to {MAX_FREE_PAGES_PER_DAY} pages per day. Upgrade to Pro for unlimited conversions.", 0
    
    return True, "", pages_remaining


def record_usage(free_key: str, pages_used: int, file_size: int):
    """
    Record usage for abuse control.
    
    Args:
        free_key: Unique identifier
        pages_used: Number of pages processed
        file_size: File size in bytes
    """
    if free_key not in _usage_tracker:
        _usage_tracker[free_key] = {
            'pages_used_today': 0,
            'last_reset_timestamp': time.time(),
            'last_file_size': 0
        }
    
    _usage_tracker[free_key]['pages_used_today'] += pages_used
    _usage_tracker[free_key]['last_file_size'] = file_size


def get_usage_info(free_key: str) -> Dict:
    """
    Get current usage information.
    
    Args:
        free_key: Unique identifier
        
    Returns:
        Dictionary with usage stats
    """
    if free_key not in _usage_tracker:
        return {
            'pages_used_today': 0,
            'pages_remaining': MAX_FREE_PAGES_PER_DAY,
            'last_reset_timestamp': time.time()
        }
    
    user_data = _usage_tracker[free_key]
    now = time.time()
    
    # Reset if 24 hours passed
    if now - user_data['last_reset_timestamp'] >= FREE_RESET_HOURS * 3600:
        user_data['pages_used_today'] = 0
        user_data['last_reset_timestamp'] = now
    
    return {
        'pages_used_today': user_data['pages_used_today'],
        'pages_remaining': MAX_FREE_PAGES_PER_DAY - user_data['pages_used_today'],
        'last_reset_timestamp': user_data['last_reset_timestamp']
    }

