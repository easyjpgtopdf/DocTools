"""
Job tracking and status management.
Simple in-memory implementation (ready for migration to Firestore/Redis).
"""
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional
from app.models import ConversionJob

logger = logging.getLogger(__name__)

# In-memory job store (dict)
# In production, replace with Firestore, Redis, or database
_job_store: Dict[str, ConversionJob] = {}


def create_job(job_type: str) -> ConversionJob:
    """
    Create a new conversion job.
    
    Args:
        job_type: Type of job ("pdf-to-word", "pdf-to-jpg", "pdf-apply-annotations")
        
    Returns:
        ConversionJob instance
    """
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    job = ConversionJob(
        id=job_id,
        type=job_type,  # type: ignore
        status="pending",
        created_at=now,
        updated_at=now
    )
    
    _job_store[job_id] = job
    logger.info(f"Created job: {job_id} (type: {job_type})")
    return job


def update_job_success(
    job_id: str,
    download_url: str,
    engine: str,
    pages: int,
    confidence: Optional[float] = None
) -> Optional[ConversionJob]:
    """
    Update job on successful completion.
    
    Args:
        job_id: Job ID
        download_url: Download URL for converted file
        engine: Conversion engine used ("libreoffice" or "docai")
        pages: Number of pages processed
        confidence: Optional DocAI confidence (0-1)
        
    Returns:
        Updated ConversionJob or None if not found
    """
    if job_id not in _job_store:
        logger.warning(f"Job not found: {job_id}")
        return None
    
    job = _job_store[job_id]
    job.status = "completed"  # type: ignore
    job.updated_at = datetime.utcnow()
    job.result_url = download_url
    job.pages = pages
    job.used_docai = (engine == "docai")
    # Store engine and confidence in job (if we extend ConversionJob model)
    logger.info(f"Updated job {job_id}: status=completed, engine={engine}, pages={pages}")
    return job


def update_job_failure(
    job_id: str,
    error_message: str
) -> Optional[ConversionJob]:
    """
    Update job on failure.
    
    Args:
        job_id: Job ID
        error_message: Error message
        
    Returns:
        Updated ConversionJob or None if not found
    """
    if job_id not in _job_store:
        logger.warning(f"Job not found: {job_id}")
        return None
    
    job = _job_store[job_id]
    job.status = "error"  # type: ignore
    job.updated_at = datetime.utcnow()
    job.error_message = error_message
    logger.info(f"Updated job {job_id}: status=error, error={error_message[:50]}")
    return job


def update_job_status(
    job_id: str,
    status: str,
    result_url: Optional[str] = None,
    pages: Optional[int] = None,
    used_docai: Optional[bool] = None,
    error_message: Optional[str] = None,
    conversion_time_ms: Optional[int] = None
) -> Optional[ConversionJob]:
    """
    Update job status and related fields.
    
    Args:
        job_id: Job ID
        status: New status ("pending", "processing", "done", "error")
        result_url: Optional result URL
        pages: Optional number of pages
        used_docai: Optional flag if Document AI was used
        error_message: Optional error message
        conversion_time_ms: Optional conversion time in milliseconds
        
    Returns:
        Updated ConversionJob or None if job not found
    """
    if job_id not in _job_store:
        logger.warning(f"Job not found: {job_id}")
        return None
    
    job = _job_store[job_id]
    
    # Update fields
    job.status = status  # type: ignore
    job.updated_at = datetime.utcnow()
    
    if result_url is not None:
        job.result_url = result_url
    if pages is not None:
        job.pages = pages
    if used_docai is not None:
        job.used_docai = used_docai
    if error_message is not None:
        job.error_message = error_message
    if conversion_time_ms is not None:
        job.conversion_time_ms = conversion_time_ms
    
    logger.info(f"Updated job {job_id}: status={status}")
    return job


def get_job(job_id: str) -> Optional[ConversionJob]:
    """
    Get job by ID.
    
    Args:
        job_id: Job ID
        
    Returns:
        ConversionJob or None if not found
    """
    return _job_store.get(job_id)


def cleanup_old_jobs(max_age_hours: int = 24) -> int:
    """
    Clean up jobs older than max_age_hours.
    For in-memory store, this helps prevent memory leaks.
    
    Args:
        max_age_hours: Maximum age in hours
        
    Returns:
        Number of jobs cleaned up
    """
    from datetime import timedelta
    
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    to_remove = [
        job_id for job_id, job in _job_store.items()
        if job.created_at < cutoff
    ]
    
    for job_id in to_remove:
        del _job_store[job_id]
    
    if to_remove:
        logger.info(f"Cleaned up {len(to_remove)} old jobs")
    
    return len(to_remove)

