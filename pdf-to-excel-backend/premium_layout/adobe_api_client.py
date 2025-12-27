"""
Real Adobe PDF Extract API Client
Implements actual Adobe PDF Services API integration (not mock)
"""

import logging
import requests
import time
import json
import base64
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


class AdobeAPIClient:
    """
    Production Adobe PDF Extract API client.
    
    Uses Adobe PDF Services API v2 (REST):
    https://developer.adobe.com/document-services/docs/apis/#tag/PDF-Extract
    """
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = 0
        
        # Adobe PDF Services endpoints
        self.auth_url = "https://ims-na1.adobelogin.com/ims/token/v3"
        self.asset_upload_url = "https://pdf-services.adobe.io/assets"
        self.extract_url = "https://pdf-services.adobe.io/operation/extractpdf"
        
    def get_access_token(self) -> Optional[str]:
        """Get OAuth access token for Adobe API"""
        current_time = time.time()
        
        # Reuse token if still valid (5 min buffer)
        if self.access_token and self.token_expiry > current_time + 300:
            logger.debug("Reusing existing Adobe access token")
            return self.access_token
        
        try:
            logger.info("Requesting new Adobe API access token...")
            
            response = requests.post(
                self.auth_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scope': 'openid,AdobeID,read_organizations'
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=15
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expiry = current_time + expires_in
                logger.info(f"✅ Adobe access token obtained (expires in {expires_in}s)")
                return self.access_token
            else:
                logger.error(f"❌ Adobe auth failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Adobe authentication error: {e}")
            return None
    
    def upload_asset(self, pdf_bytes: bytes, filename: str, access_token: str) -> Optional[Dict]:
        """
        Upload PDF asset to Adobe cloud storage.
        
        Returns:
            Dict with 'assetID' and 'uploadUri'
        """
        try:
            logger.info(f"Uploading PDF asset: {filename} ({len(pdf_bytes)} bytes)")
            
            # Step 1: Create asset
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-API-Key': self.client_id,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'mediaType': 'application/pdf'
            }
            
            response = requests.post(
                self.asset_upload_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Asset creation failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            asset_data = response.json()
            asset_id = asset_data.get('assetID')
            upload_uri = asset_data.get('uploadUri')
            
            if not asset_id or not upload_uri:
                logger.error("❌ Missing assetID or uploadUri in response")
                return None
            
            logger.info(f"Asset created: {asset_id}")
            
            # Step 2: Upload PDF to the uploadUri
            upload_headers = {
                'Content-Type': 'application/pdf',
                'Content-Length': str(len(pdf_bytes))
            }
            
            upload_response = requests.put(
                upload_uri,
                headers=upload_headers,
                data=pdf_bytes,
                timeout=120
            )
            
            if upload_response.status_code not in [200, 201]:
                logger.error(f"❌ PDF upload failed: {upload_response.status_code}")
                return None
            
            logger.info("✅ PDF uploaded successfully")
            
            return {
                'assetID': asset_id,
                'uploadUri': upload_uri
            }
            
        except Exception as e:
            logger.error(f"❌ Asset upload error: {e}")
            return None
    
    def extract_pdf(self, asset_id: str, access_token: str) -> Optional[Dict]:
        """
        Extract structured content from PDF using Adobe Extract API.
        
        Returns:
            Extracted data as JSON dict
        """
        try:
            logger.info(f"Starting PDF extraction for asset: {asset_id}")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-API-Key': self.client_id,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'assetID': asset_id,
                'elementsToExtract': ['text', 'tables'],
                'renditionsToExtract': ['tables', 'figures']
            }
            
            # Submit extraction job
            response = requests.post(
                self.extract_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"❌ Extraction job submission failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
            
            job_data = response.json()
            status_uri = job_data.get('location')
            
            if not status_uri:
                logger.error("❌ No status URI in extraction response")
                return None
            
            logger.info(f"Extraction job submitted, polling status...")
            
            # Poll for job completion
            max_polls = 60  # Max 5 minutes (5s interval)
            poll_interval = 5
            
            for poll_count in range(max_polls):
                time.sleep(poll_interval)
                
                status_response = requests.get(
                    status_uri,
                    headers={'Authorization': f'Bearer {access_token}', 'X-API-Key': self.client_id},
                    timeout=15
                )
                
                if status_response.status_code != 200:
                    logger.warning(f"⚠️ Status poll failed: {status_response.status_code}")
                    continue
                
                status_data = status_response.json()
                status = status_data.get('status')
                
                logger.info(f"Job status: {status} (poll {poll_count + 1}/{max_polls})")
                
                if status == 'done':
                    # Download result
                    download_uri = status_data.get('asset', {}).get('downloadUri')
                    
                    if not download_uri:
                        logger.error("❌ No download URI in completed job")
                        return None
                    
                    logger.info("Downloading extraction result...")
                    
                    result_response = requests.get(download_uri, timeout=60)
                    
                    if result_response.status_code != 200:
                        logger.error(f"❌ Result download failed: {result_response.status_code}")
                        return None
                    
                    # Adobe returns a ZIP file containing structuredData.json
                    # For now, we'll parse it assuming JSON directly
                    # In production, you'd unzip and extract structuredData.json
                    
                    try:
                        result_json = result_response.json()
                        logger.info("✅ Extraction complete!")
                        return result_json
                    except json.JSONDecodeError:
                        # It's a ZIP file, need to extract
                        logger.info("Result is ZIP archive, extracting structuredData.json...")
                        import zipfile
                        import io
                        
                        zip_buffer = io.BytesIO(result_response.content)
                        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
                            # Look for structuredData.json
                            if 'structuredData.json' in zip_ref.namelist():
                                with zip_ref.open('structuredData.json') as json_file:
                                    result_json = json.load(json_file)
                                    logger.info("✅ Extraction complete (from ZIP)!")
                                    return result_json
                            else:
                                logger.error("❌ structuredData.json not found in ZIP")
                                return None
                
                elif status == 'failed':
                    error_msg = status_data.get('error', 'Unknown error')
                    logger.error(f"❌ Extraction job failed: {error_msg}")
                    return None
                
                # Status is 'in progress', continue polling
            
            logger.error("❌ Extraction job timed out after 5 minutes")
            return None
            
        except Exception as e:
            logger.error(f"❌ PDF extraction error: {e}")
            return None
    
    def extract_pdf_full_flow(self, pdf_bytes: bytes, filename: str) -> Optional[Dict]:
        """
        Complete flow: Auth → Upload → Extract → Download
        
        Returns:
            Extracted JSON data or None
        """
        try:
            # Step 1: Get access token
            access_token = self.get_access_token()
            if not access_token:
                logger.error("❌ Cannot proceed without access token")
                return None
            
            # Step 2: Upload PDF
            asset_data = self.upload_asset(pdf_bytes, filename, access_token)
            if not asset_data:
                logger.error("❌ PDF upload failed")
                return None
            
            asset_id = asset_data['assetID']
            
            # Step 3: Extract and download
            result = self.extract_pdf(asset_id, access_token)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Full extraction flow failed: {e}")
            return None

