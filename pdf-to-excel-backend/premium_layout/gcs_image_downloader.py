"""
GCS Image Downloader
Downloads images from Google Cloud Storage for Document AI image references.
"""

import logging
from typing import Optional, List, Dict
from io import BytesIO

try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("google-cloud-storage not available")

logger = logging.getLogger(__name__)


class GCSImageDownloader:
    """Downloads images from GCS for Document AI"""
    
    def __init__(self):
        """Initialize GCS downloader"""
        self.storage_client = None
        if GCS_AVAILABLE:
            try:
                self.storage_client = storage.Client()
            except Exception as e:
                logger.warning(f"Failed to initialize GCS client: {e}")
    
    def download_image_from_gcs(self, gcs_uri: str) -> Optional[bytes]:
        """
        Download image from GCS URI.
        
        Args:
            gcs_uri: GCS URI (e.g., gs://bucket/path/to/image.png)
            
        Returns:
            Image bytes or None if download fails
        """
        if not GCS_AVAILABLE or not self.storage_client:
            logger.warning("GCS not available, cannot download image")
            return None
        
        try:
            # Parse GCS URI
            if not gcs_uri.startswith('gs://'):
                logger.warning(f"Invalid GCS URI: {gcs_uri}")
                return None
            
            # Remove gs:// prefix
            path = gcs_uri[5:]  # Remove 'gs://'
            parts = path.split('/', 1)
            
            if len(parts) != 2:
                logger.warning(f"Invalid GCS URI format: {gcs_uri}")
                return None
            
            bucket_name = parts[0]
            blob_name = parts[1]
            
            # Download blob
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            image_bytes = blob.download_as_bytes()
            logger.info(f"Downloaded image from GCS: {len(image_bytes)} bytes")
            return image_bytes
        
        except Exception as e:
            logger.warning(f"Failed to download image from GCS {gcs_uri}: {e}")
            return None
    
    def download_images_from_structure(self, full_structure: Dict) -> List[Dict]:
        """
        Download all images from full OCR structure.
        
        Args:
            full_structure: Full OCR structure from FullOCRExtractor
            
        Returns:
            List of image dictionaries with downloaded bytes
        """
        downloaded_images = []
        
        if not GCS_AVAILABLE or not self.storage_client:
            logger.warning("GCS not available, skipping image download")
            return downloaded_images
        
        # Process images from all pages
        for page_structure in full_structure.get('pages', []):
            page_images = page_structure.get('images', [])
            for image_info in page_images:
                gcs_uri = image_info.get('gcs_uri')
                if gcs_uri:
                    image_bytes = self.download_image_from_gcs(gcs_uri)
                    if image_bytes:
                        image_info['image_bytes'] = image_bytes
                        downloaded_images.append(image_info)
        
        logger.info(f"Downloaded {len(downloaded_images)} images from GCS")
        return downloaded_images

