"""
AWS S3 storage service for uploading PDF files.
(Kept for fallback support with AWS Textract endpoint)
"""

import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional
import uuid
from datetime import datetime

# Initialize S3 client
s3_client = None


def get_s3_client():
    """Initialize and return S3 client."""
    global s3_client
    if s3_client is None:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
    return s3_client


def upload_pdf_to_s3(file_content: bytes, filename: str) -> str:
    """
    Upload PDF file to S3.
    
    Args:
        file_content: PDF file content as bytes
        filename: Original filename
    
    Returns:
        S3 object key (path)
    
    Raises:
        Exception: If upload fails
    """
    bucket_name = os.environ.get('S3_BUCKET')
    if not bucket_name:
        raise ValueError("S3_BUCKET environment variable not set")
    
    # Generate unique S3 key
    file_extension = os.path.splitext(filename)[1] or '.pdf'
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d')
    s3_key = f"pdf-uploads/{timestamp}/{unique_id}{file_extension}"
    
    try:
        s3_client = get_s3_client()
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_content,
            ContentType='application/pdf',
            ServerSideEncryption='AES256'
        )
        return s3_key
    except ClientError as e:
        raise Exception(f"Failed to upload PDF to S3: {str(e)}")


def delete_from_s3(s3_key: str) -> bool:
    """
    Delete file from S3.
    
    Args:
        s3_key: S3 object key to delete
    
    Returns:
        True if successful, False otherwise
    """
    bucket_name = os.environ.get('S3_BUCKET')
    if not bucket_name:
        return False
    
    try:
        s3_client = get_s3_client()
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        return True
    except ClientError:
        return False

