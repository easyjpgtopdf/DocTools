"""
Configuration management using Pydantic settings.
Reads environment variables for GCP, Firebase, and Document AI configuration.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # GCP Project Configuration
    project_id: Optional[str] = Field(default=None, env="PROJECT_ID", description="Google Cloud Project ID")

    # Google Cloud Storage Configuration
    gcs_input_bucket: Optional[str] = Field(default=None, env="GCS_INPUT_BUCKET", description="GCS bucket for input files")
    gcs_output_bucket: Optional[str] = Field(default=None, env="GCS_OUTPUT_BUCKET", description="GCS bucket for output files")

    # Document AI Configuration
    docai_location: str = Field(default="us", env="DOCAI_LOCATION", description="Document AI location (e.g. 'us')")
    docai_processor_id: Optional[str] = Field(default=None, env="DOCAI_PROCESSOR_ID", description="Document AI processor ID")

    # Firebase Configuration
    firebase_project_id: Optional[str] = Field(default=None, env="FIREBASE_PROJECT_ID", description="Firebase project ID")

    # Google Application Credentials
    google_application_credentials: Optional[str] = Field(
        default=None,
        env="GOOGLE_APPLICATION_CREDENTIALS",
        description="Path to Google Cloud service account JSON key file"
    )

    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST", description="Server host")
    port: int = Field(default=8080, env="PORT", description="Server port")

    # Conversion Settings
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB", description="Maximum file size in MB")
    signed_url_expiration: int = Field(default=3600, env="SIGNED_URL_EXPIRATION", description="Signed URL expiration in seconds")
    
    # Adobe Extract API Configuration (Optional - Premium fallback only)
    adobe_client_id: Optional[str] = Field(
        default=None,
        env="ADOBE_CLIENT_ID",
        description="Adobe Extract API Client ID (premium fallback only)"
    )
    adobe_client_secret: Optional[str] = Field(
        default=None,
        env="ADOBE_CLIENT_SECRET",
        description="Adobe Extract API Client Secret (premium fallback only)"
    )
    adobe_tech_account_id: Optional[str] = Field(
        default=None,
        env="ADOBE_TECH_ACCOUNT_ID",
        description="Adobe Technical Account ID (premium fallback only)"
    )
    adobe_tech_account_email: Optional[str] = Field(
        default=None,
        env="ADOBE_TECH_ACCOUNT_EMAIL",
        description="Adobe Technical Account Email (premium fallback only)"
    )
    adobe_org_id: Optional[str] = Field(
        default=None,
        env="ADOBE_ORG_ID",
        description="Adobe Organization ID (premium fallback only)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
