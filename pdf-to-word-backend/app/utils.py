"""
Utility functions for file handling, validation, and common operations.
"""
import os
import uuid
import tempfile
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def generate_temp_filename(extension: str = ".pdf") -> str:
    """Generate a unique temporary filename."""
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{extension}"


def get_temp_path(filename: str) -> str:
    """Get full path for a temporary file."""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, filename)


def ensure_temp_dir() -> str:
    """Ensure temp directory exists and return its path."""
    temp_dir = tempfile.gettempdir()
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def validate_pdf_file(file_path: str, max_size_mb: int = 50) -> Tuple[bool, Optional[str]]:
    """
    Validate PDF file exists and meets size requirements.
    
    Args:
        file_path: Path to PDF file
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        return False, f"File size exceeds maximum of {max_size_mb}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Check file extension
    if not file_path.lower().endswith('.pdf'):
        return False, "File is not a PDF"
    
    return True, None


def cleanup_file(file_path: str) -> None:
    """Safely delete a file if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def generate_safe_filename(original_filename: str) -> str:
    """
    Generate a safe filename using UUID while preserving extension.
    
    Example:
        safe_name = generate_safe_filename("document.pdf")
        # Returns: "550e8400-e29b-41d4-a716-446655440000.pdf"
    
    Args:
        original_filename: Original filename
        
    Returns:
        Safe filename with UUID prefix
    """
    import uuid
    extension = ""
    if "." in original_filename:
        extension = "." + original_filename.rsplit(".", 1)[1].lower()
    
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{extension}"


def parse_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Parse Bearer token from Authorization header.
    
    Example:
        token = parse_bearer_token("Bearer eyJhbGciOiJSUzI1NiIs...")
        # Returns: "eyJhbGciOiJSUzI1NiIs..."
    
    Args:
        auth_header: Authorization header value (e.g., "Bearer <token>")
        
    Returns:
        Token string or None if not found/invalid format
    """
    if not auth_header:
        return None
    
    parts = auth_header.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    
    return None

