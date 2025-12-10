"""
Tests for GCS storage operations.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.storage import GCSStorage, upload_file_to_gcs, generate_signed_url


class TestGCSStorage:
    """Tests for GCS storage operations."""
    
    @patch('app.storage.storage.Client')
    def test_upload_file_to_gcs(self, mock_client_class):
        """Test file upload to GCS."""
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        
        mock_client_class.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        storage_client = GCSStorage("test-project")
        result = storage_client.upload_file_to_gcs(
            "local_file.pdf",
            "test-bucket",
            "blob_name.docx"
        )
        
        assert result == "blob_name.docx"
        mock_blob.upload_from_filename.assert_called_once_with("local_file.pdf")
    
    @patch('app.storage.storage.Client')
    def test_generate_signed_url(self, mock_client_class):
        """Test signed URL generation."""
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_blob.generate_signed_url.return_value = "https://signed-url.com/file"
        
        mock_client_class.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        storage_client = GCSStorage("test-project")
        result = storage_client.generate_signed_url(
            "test-bucket",
            "blob_name.docx",
            expiration_seconds=3600
        )
        
        assert result == "https://signed-url.com/file"
        mock_blob.generate_signed_url.assert_called_once()

