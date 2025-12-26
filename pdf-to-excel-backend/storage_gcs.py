"""
Google Cloud Storage service for storing converted Excel files.
"""

import os
from google.cloud import storage
from typing import Optional
import uuid
from datetime import datetime, timedelta

# Initialize GCS client
gcs_client = None


def get_gcs_client():
    """Initialize and return GCS client."""
    global gcs_client
    if gcs_client is None:
        # GCS client will use credentials from environment or default credentials
        gcs_client = storage.Client(project=os.environ.get('GCP_PROJECT_ID', 'easyjpgtopdf-de346'))
    return gcs_client


def upload_excel_to_gcs(file_content: bytes, filename: str) -> str:
    """
    Upload Excel file to GCS and return a signed URL for download.
    
    Args:
        file_content: Excel file content as bytes
        filename: Original filename (without extension)
    
    Returns:
        Signed download URL (valid for 1 hour)
    
    Raises:
        Exception: If upload fails
    """
    bucket_name = os.environ.get('GCS_BUCKET')
    if not bucket_name:
        raise ValueError("GCS_BUCKET environment variable not set")
    
    # Generate unique GCS blob name
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d')
    blob_name = f"excel-exports/{timestamp}/{unique_id}.xlsx"
    
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Upload file
        blob.upload_from_string(
            file_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Try to generate signed URL (requires private key)
        # If that fails (e.g., on Cloud Run with default credentials), use public URL
        try:
            download_url = blob.generate_signed_url(
                expiration=timedelta(hours=1),
                method='GET'
            )
        except Exception as sign_error:
            # Fallback: Make blob publicly accessible temporarily and use public URL
            # This works when bucket has public access or IAM allows it
            try:
                blob.make_public()
                download_url = blob.public_url
            except Exception as public_error:
                # Last resort: Use the blob's URI (user will need GCS access)
                download_url = f"gs://{bucket_name}/{blob_name}"
                # Log the issue but don't fail - the file is uploaded
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Could not generate signed or public URL for {blob_name}. "
                    f"Signed URL error: {sign_error}, Public URL error: {public_error}. "
                    f"Using GCS URI: {download_url}"
                )
        
        return download_url
    except Exception as e:
        raise Exception(f"Failed to upload Excel to GCS: {str(e)}")


def upload_pdf_to_gcs_temp(file_content: bytes, filename: str) -> str:
    """
    Upload PDF to GCS temporarily for Document AI processing.
    Returns GCS URI (gs://bucket/path).
    
    Args:
        file_content: PDF file content as bytes
        filename: Original filename
    
    Returns:
        GCS URI string (gs://bucket/path)
    
    Raises:
        Exception: If upload fails
    """
    bucket_name = os.environ.get('GCS_BUCKET')
    if not bucket_name:
        raise ValueError("GCS_BUCKET environment variable not set")
    
    # Generate unique GCS blob name
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d')
    blob_name = f"temp-pdf-uploads/{timestamp}/{unique_id}.pdf"
    
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        blob.upload_from_string(
            file_content,
            content_type='application/pdf'
        )
        
        # Return GCS URI
        return f"gs://{bucket_name}/{blob_name}"
    except Exception as e:
        raise Exception(f"Failed to upload PDF to GCS: {str(e)}")


def upload_file_to_gcs(file_content: bytes, blob_name: str, content_type: str = 'application/octet-stream') -> str:
    """
    Upload file to GCS and return a signed URL for download.
    
    Args:
        file_content: File content as bytes
        blob_name: GCS blob name (path)
        content_type: MIME type of the file
    
    Returns:
        Signed download URL (valid for 1 hour)
    
    Raises:
        Exception: If upload fails
    """
    bucket_name = os.environ.get('GCS_BUCKET')
    if not bucket_name:
        raise ValueError("GCS_BUCKET environment variable not set")
    
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Upload file
        blob.upload_from_string(
            file_content,
            content_type=content_type
        )
        
        # Try to generate signed URL (requires private key)
        # If that fails (e.g., on Cloud Run with default credentials), use public URL
        try:
            download_url = blob.generate_signed_url(
                expiration=timedelta(hours=1),
                method='GET'
            )
        except Exception as sign_error:
            # Fallback: Make blob publicly accessible temporarily and use public URL
            # This works when bucket has public access or IAM allows it
            try:
                blob.make_public()
                download_url = blob.public_url
            except Exception as public_error:
                # Last resort: Use the blob's URI (user will need GCS access)
                download_url = f"gs://{bucket_name}/{blob_name}"
                # Log the issue but don't fail - the file is uploaded
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Could not generate signed or public URL for {blob_name}. "
                    f"Signed URL error: {sign_error}, Public URL error: {public_error}. "
                    f"Using GCS URI: {download_url}"
                )
        
        return download_url
    except Exception as e:
        raise Exception(f"Failed to upload file to GCS: {str(e)}")


def delete_from_gcs(blob_name: str) -> bool:
    """
    Delete file from GCS.
    
    Args:
        blob_name: GCS blob name to delete
    
    Returns:
        True if successful, False otherwise
    """
    bucket_name = os.environ.get('GCS_BUCKET')
    if not bucket_name:
        return False
    
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        return True
    except Exception:
        return False


def delete_from_gcs_temp(gcs_uri: str) -> bool:
    """
    Delete temporary file from GCS using GCS URI.
    
    Args:
        gcs_uri: GCS URI (gs://bucket/path) to delete
    
    Returns:
        True if successful, False otherwise
    """
    if not gcs_uri or not gcs_uri.startswith('gs://'):
        return False
    
    try:
        # Extract bucket and blob name from GCS URI
        # Format: gs://bucket_name/blob_name
        uri_parts = gcs_uri.replace('gs://', '').split('/', 1)
        if len(uri_parts) != 2:
            return False
        
        bucket_name = uri_parts[0]
        blob_name = uri_parts[1]
        
        # Delete using GCS client
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        return True
    except Exception as e:
        # Log error but don't raise (cleanup failures shouldn't break the flow)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to delete temporary file from GCS: {gcs_uri}, error: {e}")
        return False
