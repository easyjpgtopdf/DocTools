"""
Abuse control and limits for FREE PDF to Excel conversion.
Tracks usage per device/IP with 24-hour reset.
"""

import hashlib
import time
from typing import Dict, Tuple

# Constants
MAX_FREE_PDFS_PER_DAY = 5  # 5 PDFs per day (not pages)
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


def check_limits(free_key: str, requested_pdfs: int = 1) -> Tuple[bool, str, int]:
    """
    Check if user has exceeded free limits.
    
    Args:
        free_key: Unique identifier for the user/device
        requested_pdfs: Number of PDFs requested (default: 1)
        
    Returns:
        (allowed, message, pdfs_remaining)
    """
    now = time.time()
    
    # Initialize if first time
    if free_key not in _usage_tracker:
        _usage_tracker[free_key] = {
            'pdfs_used_today': 0,
            'last_reset_timestamp': now,
            'last_file_size': 0
        }
        pdfs_remaining = MAX_FREE_PDFS_PER_DAY
    else:
        user_data = _usage_tracker[free_key]
        
        # Reset if 24 hours passed
        if now - user_data['last_reset_timestamp'] >= FREE_RESET_HOURS * 3600:
            user_data['pdfs_used_today'] = 0
            user_data['last_reset_timestamp'] = now
        
        pdfs_remaining = MAX_FREE_PDFS_PER_DAY - user_data['pdfs_used_today']
    
    # Check if enough PDFs remaining
    if pdfs_remaining < requested_pdfs:
        return False, f"Daily limit reached. You can convert up to {MAX_FREE_PDFS_PER_DAY} PDFs per day. Upgrade to Pro for unlimited conversions.", 0
    
    return True, "", pdfs_remaining


def record_usage(free_key: str, pdfs_used: int = 1, file_size: int = 0):
    """
    Record usage for abuse control.
    
    Args:
        free_key: Unique identifier
        pdfs_used: Number of PDFs processed (default: 1)
        file_size: File size in bytes
    """
    if free_key not in _usage_tracker:
        _usage_tracker[free_key] = {
            'pdfs_used_today': 0,
            'last_reset_timestamp': time.time(),
            'last_file_size': 0
        }
    
    _usage_tracker[free_key]['pdfs_used_today'] += pdfs_used
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
            'pdfs_used_today': 0,
            'pdfs_remaining': MAX_FREE_PDFS_PER_DAY,
            'max_pdfs_per_day': MAX_FREE_PDFS_PER_DAY,
            'is_limit_reached': False,
            'last_reset_timestamp': time.time()
        }
    
    user_data = _usage_tracker[free_key]
    now = time.time()
    
    # Reset if 24 hours passed
    if now - user_data['last_reset_timestamp'] >= FREE_RESET_HOURS * 3600:
        user_data['pdfs_used_today'] = 0
        user_data['last_reset_timestamp'] = now
    
    pdfs_remaining = MAX_FREE_PDFS_PER_DAY - user_data['pdfs_used_today']
    is_limit_reached = pdfs_remaining <= 0
    
    return {
        'pdfs_used_today': user_data['pdfs_used_today'],
        'pdfs_remaining': pdfs_remaining,
        'max_pdfs_per_day': MAX_FREE_PDFS_PER_DAY,
        'is_limit_reached': is_limit_reached,
        'last_reset_timestamp': user_data['last_reset_timestamp']
    }

