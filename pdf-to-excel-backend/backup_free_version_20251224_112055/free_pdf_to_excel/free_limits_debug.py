"""
Debug utilities for FREE limits tracking.
Helps diagnose limit issues by IP address.
"""

from .free_limits import _usage_tracker, generate_free_key, get_usage_info, MAX_FREE_PDFS_PER_DAY
import logging

logger = logging.getLogger(__name__)


def get_usage_by_ip(ip_address: str, user_agent: str = "", fingerprint: str = "") -> dict:
    """
    Get usage information for a specific IP address.
    
    Args:
        ip_address: Client IP address
        user_agent: Browser user agent
        fingerprint: Browser fingerprint
        
    Returns:
        Dictionary with usage information
    """
    free_key = generate_free_key(ip_address, user_agent, fingerprint)
    usage_info = get_usage_info(free_key)
    
    return {
        "ip_address": ip_address,
        "free_key": free_key[:8],  # First 8 chars for debugging
        "pdfs_used_today": usage_info['pdfs_used_today'],
        "pdfs_remaining": usage_info['pdfs_remaining'],
        "max_pdfs_per_day": MAX_FREE_PDFS_PER_DAY,
        "last_reset_timestamp": usage_info['last_reset_timestamp'],
        "is_limit_reached": usage_info['is_limit_reached']
    }


def reset_usage_for_ip(ip_address: str, user_agent: str = "", fingerprint: str = ""):
    """
    Reset usage for a specific IP address (for debugging/admin use).
    
    Args:
        ip_address: Client IP address
        user_agent: Browser user agent
        fingerprint: Browser fingerprint
    """
    free_key = generate_free_key(ip_address, user_agent, fingerprint)
    if free_key in _usage_tracker:
        _usage_tracker[free_key]['pdfs_used_today'] = 0
        logger.info(f"Reset usage for IP {ip_address} (key: {free_key[:8]})")
        return True
    return False


def get_all_usage_stats() -> dict:
    """
    Get all usage statistics (for admin/debugging).
    
    Returns:
        Dictionary with all tracked usage
    """
    return {
        "total_tracked_keys": len(_usage_tracker),
        "max_pdfs_per_day": MAX_FREE_PDFS_PER_DAY,
        "usage_by_key": {
            key[:8]: {
                "pdfs_used": data['pdfs_used_today'],
                "last_reset": data['last_reset_timestamp']
            }
            for key, data in _usage_tracker.items()
        }
    }

