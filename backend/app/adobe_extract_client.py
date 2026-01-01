"""
Adobe Extract API Client
Fallback service for rare cases where DocAI fails with tables/structured content
ONLY for Premium pipeline, costs 20 credits per page
"""

import logging
import os
import base64
import requests
import json
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Adobe Extract API endpoints
ADOBE_IMS_TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
ADOBE_EXTRACT_API_BASE = "https://pdf-services.adobe.io/operation/extractpdf"


class AdobeExtractClient:
    """Client for Adobe Extract API (premium fallback only)."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tech_account_id: str,
        tech_account_email: str,
        org_id: str
    ):
        """
        Initialize Adobe Extract client.
        
        Args:
            client_id: Adobe Client ID
            client_secret: Adobe Client Secret
            tech_account_id: Technical Account ID
            tech_account_email: Technical Account Email
            org_id: Organization ID
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tech_account_id = tech_account_id
        self.tech_account_email = tech_account_email
        self.org_id = org_id
        self._access_token: Optional[str] = None
    
    def _get_access_token(self) -> str:
        """
        Get Adobe IMS access token using JWT authentication.
        Returns cached token if still valid, otherwise fetches new token.
        """
        if self._access_token:
            # TODO: Add token expiry check and refresh if needed
            return self._access_token
        
        try:
            # Construct JWT token request
            # Note: This is a simplified version - full implementation requires JWT signing
            # For production, you'd need to use a JWT library and private key
            
            # For now, return placeholder - full implementation requires:
            # 1. JWT token generation with private key
            # 2. Token exchange with Adobe IMS
            # 3. Token caching with expiry handling
            
            logger.warning("Adobe Extract API token generation not fully implemented")
            logger.warning("Full implementation requires JWT signing with private key")
            
            # Placeholder - in production, this would make actual API call
            # token_response = requests.post(ADOBE_IMS_TOKEN_URL, data={...})
            # self._access_token = token_response.json()["access_token"]
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting Adobe access token: {e}")
            raise Exception(f"Adobe Extract API authentication failed: {str(e)}")
    
    def extract_pdf(
        self,
        pdf_path: str,
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Extract content from PDF using Adobe Extract API.
        
        Args:
            pdf_path: Path to input PDF file
            output_path: Optional path to save extracted content
            
        Returns:
            Dictionary with extracted content (text, tables, etc.)
        """
        try:
            # Get access token
            access_token = self._get_access_token()
            if not access_token:
                raise Exception("Could not obtain Adobe access token")
            
            # Read PDF file
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {access_token}",
                "x-api-key": self.client_id,
                "Content-Type": "application/pdf"
            }
            
            # Extract parameters
            extract_params = {
                "elementsToExtract": ["text", "tables"],
                "tableOutputFormat": "csv",
                "charInfo": True
            }
            
            # Make API call
            # Note: Actual API call structure may differ - check Adobe documentation
            response = requests.post(
                ADOBE_EXTRACT_API_BASE,
                headers=headers,
                data=pdf_bytes,
                params=extract_params,
                timeout=300
            )
            
            if response.status_code != 200:
                raise Exception(f"Adobe Extract API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Save to file if output path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info("Adobe Extract API extraction successful")
            return result
            
        except Exception as e:
            logger.error(f"Adobe Extract API extraction failed: {e}")
            raise Exception(f"Adobe Extract API failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Adobe Extract API is properly configured."""
        return all([
            self.client_id,
            self.client_secret,
            self.tech_account_id,
            self.tech_account_email,
            self.org_id
        ])


def get_adobe_extract_client(settings) -> Optional[AdobeExtractClient]:
    """
    Get Adobe Extract client if credentials are configured.
    Returns None if not configured (which is expected - it's optional).
    """
    if not all([
        settings.adobe_client_id,
        settings.adobe_client_secret,
        settings.adobe_tech_account_id,
        settings.adobe_tech_account_email,
        settings.adobe_org_id
    ]):
        logger.debug("Adobe Extract API credentials not configured (expected - optional premium fallback)")
        return None
    
    try:
        client = AdobeExtractClient(
            client_id=settings.adobe_client_id,
            client_secret=settings.adobe_client_secret,
            tech_account_id=settings.adobe_tech_account_id,
            tech_account_email=settings.adobe_tech_account_email,
            org_id=settings.adobe_org_id
        )
        logger.info("Adobe Extract API client initialized (premium fallback)")
        return client
    except Exception as e:
        logger.warning(f"Failed to initialize Adobe Extract client: {e}")
        return None

