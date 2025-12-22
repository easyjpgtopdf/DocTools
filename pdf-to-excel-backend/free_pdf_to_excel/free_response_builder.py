"""
Response Builder for FREE version API responses.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def build_success_response(
    download_url: str,
    pages_processed: int,
    confidence: float,
    method: str = "gcs"
) -> Dict:
    """
    Build success response.
    
    Args:
        download_url: URL to download Excel file
        pages_processed: Number of pages processed
        confidence: Confidence score (0.0 to 1.0)
        method: Download method ("gcs" or "direct_download")
        
    Returns:
        Response dictionary
    """
    return {
        "status": "success",
        "success": True,
        "engine": "free-pdf-to-excel-v1",
        "downloadUrl": download_url,
        "method": method,
        "pagesProcessed": pages_processed,
        "confidence": round(confidence, 2)
    }


def build_error_response(
    error_message: str,
    upgrade_required: bool = False,
    fallback_available: bool = False
) -> Dict:
    """
    Build error response.
    
    Args:
        error_message: Error message
        upgrade_required: Whether upgrade is required
        fallback_available: Whether browser fallback is available
        
    Returns:
        Response dictionary
    """
    response = {
        "status": "error",
        "success": False,
        "error": error_message
    }
    
    if upgrade_required:
        response["upgrade_required"] = True
    
    if fallback_available:
        response["fallback_available"] = True
    
    return response

