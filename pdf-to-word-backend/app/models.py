"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConvertResponse(BaseModel):
    """PDF to Word conversion response model."""
    status: str
    download_url: str
    used_docai: bool
    pages: Optional[int] = None
    conversion_time_ms: int
    file_size_bytes: Optional[int] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str = "error"
    error: str
    code: Optional[str] = None

