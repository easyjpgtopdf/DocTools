"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConvertResponse(BaseModel):
    """PDF to Word conversion response model with smart conversion support."""
    status: str
    job_id: str
    primary_download_url: str
    primary_method: str  # "libreoffice" or "docai"
    alt_download_url: Optional[str] = None
    alt_method: Optional[str] = None  # "libreoffice" or "docai"
    pages: Optional[int] = None
    used_docai: bool
    conversion_time_ms: int
    file_size_bytes: Optional[int] = None
    # Backward compatibility fields
    download_url: Optional[str] = None  # Same as primary_download_url
    # New fields for job tracking and confidence
    job_status: Optional[str] = None  # "completed" / "failed" / "processing"
    engine: Optional[str] = None  # "libreoffice" or "docai" (same as primary_method but for compatibility)
    docai_confidence: Optional[float] = None  # 0-1 range if available from Document AI


class ImageInfo(BaseModel):
    """Image information for PDF to JPG response."""
    page: int
    url: str


class PdfToJpgResponse(BaseModel):
    """PDF to JPG conversion response model."""
    status: str
    pages: int
    images: List[ImageInfo]
    job_id: Optional[str] = None


class ConversionJob(BaseModel):
    """Job tracking model."""
    id: str
    type: Literal["pdf-to-word", "pdf-to-jpg", "pdf-apply-annotations"]
    status: Literal["pending", "processing", "done", "error"]
    created_at: datetime
    updated_at: datetime
    result_url: Optional[str] = None
    pages: Optional[int] = None
    used_docai: Optional[bool] = None
    error_message: Optional[str] = None
    conversion_time_ms: Optional[int] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str = "error"
    error: str
    code: Optional[str] = None


class AnnotationApplyResponse(BaseModel):
    """PDF annotation apply response model."""
    status: str
    download_url: str
    job_id: Optional[str] = None
    pages: Optional[int] = None


class CreditBalanceResponse(BaseModel):
    """User credit balance response."""
    credits: float
    totalCreditsEarned: float
    totalCreditsUsed: float


class CreditTransaction(BaseModel):
    """Credit transaction model."""
    id: str
    date: str
    type: Literal["add", "deduct"]
    credits: float
    description: str
    creditsBefore: float
    creditsAfter: float
    file_name: Optional[str] = None
    page_count: Optional[int] = None
    processor: Optional[Literal["docai", "libreoffice"]] = None


class CreditHistoryResponse(BaseModel):
    """Credit history response."""
    transactions: List[CreditTransaction]


class CreditAddRequest(BaseModel):
    """Request to add credits."""
    amount: float
    reason: str = "Credit purchase"
    metadata: Optional[Dict] = None


class CreditAddResponse(BaseModel):
    """Response after adding credits."""
    success: bool
    creditsAdded: float
    creditsRemaining: float
    creditsBefore: float


class PdfMetadataResponse(BaseModel):
    """PDF metadata response for credit calculation."""
    pages: int
    has_text: Optional[bool] = False  # Whether PDF has extractable text
    file_size_bytes: int
    estimated_credits_text: float
    estimated_credits_ocr: float
    daily_usage_text: Optional[int] = 0  # Pages used today (text)
    daily_usage_ocr: Optional[int] = 0  # Pages used today (OCR)
    daily_limit_text: Optional[int] = 10  # Daily limit for text pages
    daily_limit_ocr: Optional[int] = 5  # Daily limit for OCR pages
    can_use_free_tier: Optional[bool] = True  # Whether user can use free tier for this file

