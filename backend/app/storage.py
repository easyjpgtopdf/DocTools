"""
Google Cloud Storage module.
Handles file uploads and signed URL generation.
"""
import os
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
import logging
from typing import Optional
from datetime import timedelta

logger = logging.getLogger(__name__)


class GCSStorage:
    """Google Cloud Storage client wrapper."""
    
    def __init__(self, project_id: str):
        """
        Initialize GCS client.
        
        Args:
            project_id: Google Cloud Project ID
        """
        self.project_id = project_id
        self.client = storage.Client(project=project_id)
        logger.info(f"GCS client initialized for project: {project_id}")
    
    def upload_file_to_gcs(
        self,
        local_path: str,
        bucket_name: str,
        blob_name: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to GCS bucket and return blob name.
        
        Args:
            local_path: Local file path to upload
            bucket_name: GCS bucket name
            blob_name: Destination blob name in bucket
            content_type: Optional MIME type for the file
            
        Returns:
            Blob name in GCS
        """
        try:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local file not found: {local_path}")
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            if content_type:
                blob.content_type = content_type
            
            blob.upload_from_filename(local_path)
            logger.info(f"File uploaded successfully to gs://{bucket_name}/{blob_name}")
            return blob_name
        except GoogleCloudError as e:
            error_msg = f"GCS upload error for {local_path} to gs://{bucket_name}/{blob_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error uploading {local_path} to GCS: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
    
    def generate_signed_url(
        self,
        bucket_name: str,
        blob_name: str,
        expiration_seconds: int = 3600,
        method: str = "GET",
        fallback_download_url: Optional[str] = None
    ) -> str:
        """
        Generate a signed URL for accessing a blob.
        If signing fails (e.g., no private key in credentials), returns fallback URL or raises error.
        
        Args:
            bucket_name: GCS bucket name
            blob_name: Blob name in bucket
            expiration_seconds: URL expiration time in seconds
            method: HTTP method (GET, PUT, etc.)
            fallback_download_url: Optional fallback URL to return if signing fails (for free tier)
            
        Returns:
            Signed URL string or fallback URL if signing fails
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # Verify blob exists
            if not blob.exists():
                raise FileNotFoundError(f"Blob does not exist: gs://{bucket_name}/{blob_name}")
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expiration_seconds),
                method=method
            )
            logger.info(f"Generated signed URL for gs://{bucket_name}/{blob_name} (expires in {expiration_seconds}s)")
            return url
        except (GoogleCloudError, ValueError, AttributeError) as e:
            error_msg = str(e)
            # Check if it's a credentials/private key issue
            if "private key" in error_msg.lower() or "credentials" in error_msg.lower() or "sign" in error_msg.lower():
                if fallback_download_url:
                    logger.warning(f"Cannot generate signed URL (missing private key in credentials). Using fallback: {fallback_download_url}")
                    return fallback_download_url
                else:
                    logger.error(f"Error generating signed URL for gs://{bucket_name}/{blob_name}: {error_msg}")
                    raise RuntimeError(f"Cannot generate signed URL: {error_msg}. Please use service account with private key or provide fallback_download_url.") from e
            else:
                error_msg = f"Error generating signed URL for gs://{bucket_name}/{blob_name}: {error_msg}"
                logger.error(error_msg, exc_info=True)
                raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error generating signed URL: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # If fallback is available, use it
            if fallback_download_url and ("private key" in error_msg.lower() or "credentials" in error_msg.lower()):
                logger.warning(f"Using fallback URL due to signing error: {fallback_download_url}")
                return fallback_download_url
            raise RuntimeError(error_msg) from e
    
    def delete_file(self, bucket_name: str, blob_name: str) -> None:
        """
        Delete a file from GCS bucket.
        
        Args:
            bucket_name: GCS bucket name
            blob_name: Blob name to delete
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Deleted gs://{bucket_name}/{blob_name}")
        except GoogleCloudError as e:
            logger.warning(f"Failed to delete file: {e}")


def upload_file_to_gcs(
    project_id: str,
    local_path: str,
    bucket_name: str,
    blob_name: str,
    content_type: Optional[str] = None
) -> str:
    """
    Convenience function to upload file to GCS.
    
    Args:
        project_id: Google Cloud Project ID
        local_path: Local file path
        bucket_name: GCS bucket name
        blob_name: Destination blob name
        content_type: Optional MIME type
        
    Returns:
        Blob name
    """
    storage_client = GCSStorage(project_id)
    return storage_client.upload_file_to_gcs(local_path, bucket_name, blob_name, content_type)


def generate_signed_url(
    project_id: str,
    bucket_name: str,
    blob_name: str,
    expiration_seconds: int = 3600
) -> str:
    """
    Convenience function to generate signed URL.
    
    Args:
        project_id: Google Cloud Project ID
        bucket_name: GCS bucket name
        blob_name: Blob name
        expiration_seconds: URL expiration time
        
    Returns:
        Signed URL
    """
    storage_client = GCSStorage(project_id)
    return storage_client.generate_signed_url(bucket_name, blob_name, expiration_seconds)

