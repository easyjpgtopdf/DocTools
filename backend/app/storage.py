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
        method: str = "GET"
    ) -> str:
        """
        Generate a signed URL for accessing a blob.
        
        Args:
            bucket_name: GCS bucket name
            blob_name: Blob name in bucket
            expiration_seconds: URL expiration time in seconds
            method: HTTP method (GET, PUT, etc.)
            
        Returns:
            Signed URL string
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
        except GoogleCloudError as e:
            error_msg = f"Error generating signed URL for gs://{bucket_name}/{blob_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error generating signed URL: {str(e)}"
            logger.error(error_msg, exc_info=True)
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

