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
        
        # Generate signed URL (valid for 1 hour)
        download_url = blob.generate_signed_url(
            expiration=timedelta(hours=1),
            method='GET'
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

