"""
Firebase Authentication module.
Handles Firebase ID token verification.
"""
import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

_firebase_initialized = False


def initialize_firebase(credentials_path: Optional[str] = None) -> None:
    """Initialize Firebase Admin SDK."""
    global _firebase_initialized
    
    if _firebase_initialized:
        logger.info("Firebase already initialized")
        return
    
    try:
        if credentials_path:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
        else:
            # Use Application Default Credentials
            firebase_admin.initialize_app()
        
        _firebase_initialized = True
        logger.info("Firebase Admin initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def verify_firebase_token(id_token: str) -> Optional[Dict]:
    """
    Verify Firebase ID token and return decoded token.
    
    Args:
        id_token: Firebase ID token string
        
    Returns:
        Decoded token dict with user info (uid, email, etc.) or None if invalid
    """
    try:
        if not _firebase_initialized:
            initialize_firebase()
        
        decoded_token = auth.verify_id_token(id_token)
        logger.info(f"Token verified for user: {decoded_token.get('uid')}")
        return decoded_token
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid ID token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


def get_user_from_token(id_token: Optional[str]) -> Dict:
    """
    Extract user information from Firebase token or return anonymous user.
    
    Args:
        id_token: Optional Firebase ID token
        
    Returns:
        Dict with user_id and email (if authenticated) or anonymous user info
    """
    if not id_token:
        return {"user_id": "anonymous", "email": None, "authenticated": False}
    
    decoded = verify_firebase_token(id_token)
    if decoded:
        return {
            "user_id": decoded.get("uid"),
            "email": decoded.get("email"),
            "authenticated": True
        }
    
    return {"user_id": "anonymous", "email": None, "authenticated": False}


# FastAPI dependency for authentication
async def get_current_user(
    authorization: Optional[str] = None,
    optional: bool = True
) -> Optional[Dict]:
    """
    FastAPI dependency to get current user from Firebase token.
    
    Usage in FastAPI route:
        @app.post("/api/convert/pdf-to-word")
        async def convert(
            file: UploadFile,
            user: dict = Depends(lambda: get_current_user(optional=True))
        ):
            user_id = user.get("user_id") if user else "anonymous"
    
    Args:
        authorization: Authorization header value (passed via FastAPI Header)
        optional: If True, returns None instead of raising exception when token is missing
        
    Returns:
        User dict with uid and email, or None if optional=True and no token
    """
    from fastapi import Header, HTTPException
    from app.utils import parse_bearer_token
    
    # Extract token from header
    id_token = None
    if authorization:
        id_token = parse_bearer_token(authorization)
    
    # If no token and optional, return None
    if not id_token and optional:
        return None
    
    # If no token and required, raise exception
    if not id_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide a valid Firebase ID token."
        )
    
    # Verify token
    decoded = verify_firebase_token(id_token)
    if not decoded:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token."
        )
    
    return {
        "uid": decoded.get("uid"),
        "email": decoded.get("email"),
        "authenticated": True
    }

