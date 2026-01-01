"""
FastAPI main application.
Handles PDF to Word conversion endpoints.
"""
import os
import time
import logging
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Header, Request, Form
from fastapi.responses import JSONResponse, FileResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from app.config import get_settings, Settings
from app.models import (
    ConvertResponse,
    ExcelConvertResponse,
    PdfToJpgResponse,
    ImageInfo,
    ConversionJob,
    AnnotationApplyResponse,
    ErrorResponse,
    HealthResponse,
    CreditBalanceResponse,
    CreditHistoryResponse,
    CreditTransaction,
    CreditAddRequest,
    CreditAddResponse,
    PdfMetadataResponse
)
from app.converter import (
    pdf_has_text,
    convert_pdf_to_docx_with_libreoffice,
    convert_pdf_to_docx_with_docai,
    convert_pdf_to_jpg,
    generate_pdf_thumbnail,
    get_page_count,
    smart_convert_pdf_to_word,
    convert_pdf_to_excel_with_docai,
    ConversionMethod
)
from app.docai_client import process_pdf_to_layout, get_docai_confidence
from app.pdf_editor import apply_annotations_to_pdf
from app.jobs import create_job, update_job_status, get_job, update_job_success, update_job_failure
from app.storage import GCSStorage
from app.auth import initialize_firebase, get_user_from_token
from app.credit_manager import (
    get_user_credits,
    get_credit_history,
    add_credits,
    deduct_credits,
    calculate_required_credits,
    has_sufficient_credits,
    get_firestore_client
)
from app.utils import (
    generate_temp_filename,
    get_temp_path,
    ensure_temp_dir,
    validate_pdf_file,
    cleanup_file
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PDF to Word Converter API",
    description="Production-ready PDF to Word conversion service",
    version="1.0.0"
)

# CORS middleware - Allow all origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://easyjpgtopdf.com",
        "https://www.easyjpgtopdf.com",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize Firebase on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    try:
        ensure_temp_dir()
        logger.info("Temp directory ensured")
        
        # Get settings (non-blocking - allow app to start with partial config)
        try:
            settings = get_settings()
            logger.info(f"Settings loaded: project_id={settings.project_id}")
        except Exception as settings_error:
            logger.warning(f"Settings loading failed (non-critical): {settings_error}")
            logger.info("Continuing with minimal configuration")
        
        # Initialize Firebase (non-blocking - fail gracefully)
        try:
            if settings.google_application_credentials:
                initialize_firebase(settings.google_application_credentials)
            else:
                initialize_firebase()
            logger.info("Firebase Admin initialized successfully")
        except Exception as fb_error:
            logger.warning(f"Firebase initialization failed (non-critical): {fb_error}")
            logger.info("Continuing without Firebase (auth features may be limited)")
        
        # Validate Document AI credentials (non-blocking)
        try:
            from app.docai_client import DocumentAIClient
            if settings.project_id and settings.docai_processor_id and settings.docai_location:
                docai_client = DocumentAIClient(
                    project_id=settings.project_id,
                    location=settings.docai_location,
                    processor_id=settings.docai_processor_id
                )
                if docai_client.validate_credentials():
                    logger.info("Document AI credentials validated successfully")
                else:
                    logger.warning("Document AI credentials validation failed - will use LibreOffice-only fallback")
            else:
                logger.info("Document AI not configured - will use LibreOffice-only mode")
        except Exception as docai_error:
            logger.warning(f"Document AI credential validation failed (non-critical): {docai_error}")
            logger.info("Will use LibreOffice-only fallback mode")
        
        logger.info("Application startup complete")
        logger.info("CORS enabled for all origins")
    except Exception as e:
        logger.error(f"Critical startup error: {e}", exc_info=True)
        # Don't raise - let the app start and log the error
        # This allows Cloud Run health checks to pass


# Dependency for settings
def get_app_settings() -> Settings:
    """Get application settings."""
    return get_settings()


# Dependency for Firebase auth
async def get_current_user_dep(
    request: Request,
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_app_settings)
):
    """Extract and verify Firebase token from request."""
    from app.utils import parse_bearer_token
    
    id_token = None
    if authorization:
        id_token = parse_bearer_token(authorization)
    
    user_info = get_user_from_token(id_token)
    request.state.user = user_info
    return user_info


@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle CORS preflight requests for all endpoints."""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": "PDF to Word Converter API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "convert": "/api/convert/pdf-to-word",
            "convert_jpg": "/api/convert/pdf-to-jpg",
            "apply_annotations": "/api/pdf/apply-annotations"
        }
    }


@app.get("/api/health", response_model=HealthResponse)
@app.post("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint. Supports both GET and POST methods."""
    return HealthResponse()


@app.post("/api/convert/pdf-to-word", response_model=ConvertResponse)
async def convert_pdf_to_word(
    file: UploadFile = File(...),
    request: Request = None,
    user: dict = Depends(get_current_user_dep),
    settings: Settings = Depends(get_app_settings)
) -> ConvertResponse:
    """
    Smart PDF to Word conversion with automatic method selection and alternative generation.
    
    - **file**: PDF file to convert (multipart/form-data)
    - **Authorization**: Optional Bearer token (Firebase ID token)
    
    Returns primary (recommended) and optional alternative conversion URLs.
    """
    start_time = time.time()
    job = None
    temp_pdf_path = None
    temp_dir = None
    primary_docx_path = None
    alt_docx_path = None
    is_authenticated = False
    free_tier_allowed = False
    
    try:
        # Create job for tracking
        job = create_job("pdf-to-word")
        update_job_status(job.id, "processing")
        logger.info(f"[Job {job.id}] PDF to Word conversion started - User: {user.get('user_id')}, File: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        logger.info(f"Conversion request from user: {user.get('user_id')}, file: {file.filename}")
        
        # Check file size before reading
        file_size_bytes = file.size or 0
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            error_msg = f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=413, detail=error_msg)
        
        # Save uploaded file to job-specific directory
        temp_dir = os.path.join(ensure_temp_dir(), job.id)
        os.makedirs(temp_dir, exist_ok=True)
        temp_pdf_path = os.path.join(temp_dir, "input.pdf")
        
        # Read and save file
        contents = await file.read()
        with open(temp_pdf_path, "wb") as f:
            f.write(contents)
        
        file_size = os.path.getsize(temp_pdf_path)
        file_size_mb = file_size / (1024 * 1024)
        logger.info(f"[Job {job.id}] File saved: {temp_pdf_path}, size: {file_size} bytes ({file_size_mb:.2f}MB)")
        print(f"DEBUG: PDF saved: {temp_pdf_path}, size: {file_size_mb:.2f}MB")
        
        # Check user authentication status
        user_id = user.get('user_id', 'anonymous')
        is_authenticated = user_id and user_id != 'anonymous'
        
        # Apply file size limits based on authentication
        from app.daily_usage import FREE_TIER_MAX_FILE_SIZE_MB
        from app.credit_manager import PREMIUM_MAX_FILE_SIZE_MB
        
        if is_authenticated:
            # Logged-in users: 50MB max
            max_size_mb = PREMIUM_MAX_FILE_SIZE_MB
            if file_size_mb > max_size_mb:
                error_msg = f"File too large. Maximum size for logged-in users: {max_size_mb}MB. Your file is {file_size_mb:.2f}MB."
                logger.warning(f"[Job {job.id}] {error_msg}")
                if job:
                    update_job_status(job.id, "error", error_message=error_msg)
                raise HTTPException(status_code=413, detail=error_msg)
        else:
            # Anonymous users: 10MB max
            max_size_mb = FREE_TIER_MAX_FILE_SIZE_MB
            if file_size_mb > max_size_mb:
                error_msg = f"Free tier limit: Maximum file size is {max_size_mb}MB. Your file is {file_size_mb:.2f}MB. Please sign in for higher limits (50MB max)."
                logger.warning(f"[Job {job.id}] {error_msg}")
                if job:
                    update_job_status(job.id, "error", error_message=error_msg)
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "FREE_TIER_SIZE_LIMIT_EXCEEDED",
                        "limit": max_size_mb,
                        "actual": file_size_mb,
                        "message": error_msg
                    }
                )
        
        # Validate PDF (basic validation)
        is_valid, error_msg = validate_pdf_file(temp_pdf_path, settings.max_file_size_mb)
        if not is_valid:
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Use central document detection engine
        from app.document_detector import detect_document, check_free_tier_eligibility, check_premium_requirements
        
        analysis = detect_document(temp_pdf_path, file_size, settings, use_docai_for_analysis=True)
        pages_count = analysis.page_count
        has_text = analysis.has_text
        will_use_docai = analysis.is_scanned  # OCR if scanned
        
        # CRITICAL RULE: Tables and ID cards must use Excel, not Word
        if analysis.has_tables or analysis.is_id_card_like:
            error_msg = f"This document contains tables or structured data (ID card/invoice/form). " \
                       f"For accurate results, please use PDF to Excel (Pro). {analysis.reason}"
            logger.warning(f"[Job {job.id}] Blocked Word conversion: {error_msg}")
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "REQUIRES_EXCEL_TOOL",
                    "message": error_msg,
                    "suggested_tool": "excel",
                    "reason": analysis.reason,
                    "has_tables": analysis.has_tables,
                    "is_id_card_like": analysis.is_id_card_like
                }
            )
        
        # Check limits based on authentication
        db = get_firestore_client()
        
        if is_authenticated:
            # LOGGED-IN USERS: Must use credits (NO free quota)
            # Check premium requirements
            user_credits_info = get_user_credits(user_id, db)
            user_credits = user_credits_info.get('credits', 0)
            
            premium_check = check_premium_requirements(analysis, user_credits)
            
            if not premium_check['eligible']:
                error_msg = premium_check['reason']
                logger.warning(f"[Job {job.id}] {error_msg}")
                if job:
                    update_job_status(job.id, "error", error_message=error_msg)
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "PREMIUM_REQUIREMENTS_NOT_MET",
                        "message": error_msg,
                        "required": premium_check.get('required', 0),
                        "available": premium_check.get('current_credits', user_credits),
                        "required_minimum": premium_check.get('required_minimum', 30)
                    }
                )
            
            required_credits = premium_check['required']
            logger.info(f"[Job {job.id}] Logged-in user: {user_id}, {pages_count} pages, OCR: {will_use_docai}, Credits required: {required_credits}")
            free_tier_allowed = False  # Logged-in users don't get free tier
        else:
            # ANONYMOUS USERS: Can use free tier (10 pages text, 3 pages OCR per day, 20MB max, text PDFs only)
            # Check free tier eligibility using document detector
            free_tier_eligibility = check_free_tier_eligibility(analysis, is_authenticated)
            free_tier_allowed = free_tier_eligibility.get('allowed', False)
            
            if not free_tier_allowed:
                # Check if it's a daily limit issue or a document type issue
                error_msg = free_tier_eligibility.get('reason', 'Free tier not available')
                logger.warning(f"[Job {job.id}] {error_msg}")
                if job:
                    update_job_status(job.id, "error", error_message=error_msg)
                
                # Free tier now only allows 1 page per PDF (no daily limits check needed)
                # Note: We don't check requires_ocr anymore - all PDFs can attempt LibreOffice conversion
                if free_tier_eligibility.get('exceeds_pages'):
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "FREE_TIER_PAGE_LIMIT_EXCEEDED",
                            "message": error_msg,
                            "max_pages": 1,
                            "suggestion": "Upgrade to Premium for multi-page conversion (up to 100 pages)"
                        }
                    )
                elif free_tier_eligibility.get('exceeds_size'):
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "FREE_TIER_SIZE_LIMIT_EXCEEDED",
                            "message": error_msg,
                            "max_size_mb": 2,
                            "suggestion": "Upgrade to Premium for larger files (up to 100MB)"
                        }
                    )
                else:
                    # Generic free tier error
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "FREE_TIER_NOT_ELIGIBLE",
                            "message": error_msg
                        }
                    )
            
            # Free tier allowed - log it
            logger.info(f"[Job {job.id}] Free tier usage: {user_id}, {pages_count} pages, OCR: {will_use_docai}")
        
        # Perform smart conversion (generates both primary and alternative)
        logger.info(f"[Job {job.id}] Starting smart conversion with alternative generation")
        
        # Track job status and engine
        job_status = "processing"
        engine = None
        docai_confidence = None
        
        # Both free and premium tiers try LibreOffice first, fallback to DocAI if needed
        # Free tier: LibreOffice only, no DocAI fallback (will show premium upgrade popup if DocAI needed)
        # Premium tier: LibreOffice first, DocAI fallback if LibreOffice fails (with alternative conversion)
        use_free_pipeline = (not is_authenticated and free_tier_allowed)
        
        try:
            conversion_result = smart_convert_pdf_to_word(
                temp_pdf_path,
                temp_dir,
                settings,
                generate_alternative=is_authenticated,  # Generate alternative only for premium users
                use_free_pipeline=False,  # Deprecated, kept for compatibility
                allow_docai_fallback=is_authenticated  # Only allow DocAI fallback for premium (logged-in) users
            )
        except Exception as conversion_error:
            error_msg = str(conversion_error)
            logger.error(f"[Job {job.id}] Conversion failed: {error_msg}", exc_info=True)
            
            # For free tier, if conversion fails, show a helpful error
            # Don't assume it needs OCR - LibreOffice might fail for technical reasons
            if not is_authenticated:
                # Log the error for debugging
                logger.error(f"[Job {job.id}] Free tier conversion failed: {error_msg}")
                if job:
                    update_job_status(job.id, "error", error_message=error_msg)
                
                # Show a helpful error message that doesn't assume OCR is needed
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "CONVERSION_FAILED",
                        "message": f"Conversion failed: {error_msg}. Please try again or upgrade to Premium for advanced processing.",
                        "suggestion": "Try again or upgrade to Premium for advanced processing",
                        "show_premium_upgrade": True
                    }
                )
            
            # Generic conversion error
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "CONVERSION_FAILED",
                    "message": error_msg
                }
            )
        
        primary_docx_path = conversion_result.main_docx_path
        alt_docx_path = conversion_result.alt_docx_path
        engine = conversion_result.main_method.value  # "libreoffice" or "docai"
        print(f"DEBUG: Using engine: {engine}")
        
        # Try to extract DocAI confidence if Document AI was used
        if conversion_result.used_docai:
            try:
                # Try to get confidence from Document AI result if available
                # This would require storing it in SmartConversionResult or parsing from Document AI response
                # For now, we'll try to get it from the parsed document if we can access it
                docai_confidence = None  # Placeholder - can be enhanced later
            except Exception:
                docai_confidence = None
        
        logger.info(f"[Job {job.id}] Conversion completed. Primary: {conversion_result.main_method.value}, Alternative: {conversion_result.alt_method.value if conversion_result.alt_method else 'None'}")
        
        # FREE TIER: Use direct download endpoint (no GCS signed URL needed)
        # PREMIUM: Upload to GCS and use signed URLs
        if not is_authenticated and free_tier_allowed:
            # Free tier: Rename files to standard names for download endpoint, then return direct download URLs
            logger.info(f"[Job {job.id}] Free tier: Using direct download endpoint (no GCS)")
            
            # Rename primary file to "primary.docx" if needed
            standard_primary_path = os.path.join(temp_dir, "primary.docx")
            if primary_docx_path != standard_primary_path and os.path.exists(primary_docx_path):
                import shutil
                shutil.move(primary_docx_path, standard_primary_path)
                primary_docx_path = standard_primary_path
                logger.info(f"[Job {job.id}] Renamed primary file to: {standard_primary_path}")
            
            # Rename alternative file to "alternative.docx" if needed
            if alt_docx_path and os.path.exists(alt_docx_path):
                standard_alt_path = os.path.join(temp_dir, "alternative.docx")
                if alt_docx_path != standard_alt_path:
                    import shutil
                    shutil.move(alt_docx_path, standard_alt_path)
                    alt_docx_path = standard_alt_path
                    logger.info(f"[Job {job.id}] Renamed alternative file to: {standard_alt_path}")
            
            # Build full URL for download endpoint
            if request:
                base_url = f"{request.url.scheme}://{request.url.netloc}"
            else:
                base_url = f"https://pdf-to-word-converter-564572183797.us-central1.run.app"
            primary_signed_url = f"{base_url}/api/download/{job.id}/primary.docx"
            alt_signed_url = None
            if alt_docx_path and os.path.exists(alt_docx_path):
                alt_signed_url = f"{base_url}/api/download/{job.id}/alternative.docx"
        else:
            # Premium tier: Upload to GCS and generate signed URLs
            storage_client = GCSStorage(settings.project_id)
            primary_blob_name = f"converted/{job.id}/primary.docx"
            
            logger.info(f"[Job {job.id}] Uploading primary DOCX to GCS: {primary_blob_name}")
            try:
                storage_client.upload_file_to_gcs(
                    primary_docx_path,
                    settings.gcs_output_bucket,
                    primary_blob_name,
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as gcs_error:
                error_msg = f"GCS upload failed: {str(gcs_error)}. Bucket: {settings.gcs_output_bucket}, File: {primary_docx_path}"
                logger.error(f"[Job {job.id}] {error_msg}", exc_info=True)
                raise Exception(error_msg)
            
            # Generate signed URL with fallback to direct download if signing fails
            try:
                primary_signed_url = storage_client.generate_signed_url(
                    settings.gcs_output_bucket,
                    primary_blob_name,
                    expiration_seconds=settings.signed_url_expiration
                )
            except Exception as sign_error:
                # If signing fails (no private key), use direct download endpoint as fallback
                logger.warning(f"[Job {job.id}] Signed URL generation failed: {sign_error}. Using direct download endpoint.")
                if request:
                    base_url = f"{request.url.scheme}://{request.url.netloc}"
                else:
                    base_url = f"https://pdf-to-word-converter-iwumaktavq-uc.a.run.app"
                primary_signed_url = f"{base_url}/api/download/{job.id}/primary.docx"
            print(f"DEBUG: Upload path: {primary_signed_url}")
            
            # Upload alternative file if available
            alt_signed_url = None
            if alt_docx_path and os.path.exists(alt_docx_path):
                alt_blob_name = f"converted/{job.id}/alternative.docx"
                logger.info(f"[Job {job.id}] Uploading alternative DOCX to GCS: {alt_blob_name}")
                
                try:
                    storage_client.upload_file_to_gcs(
                        alt_docx_path,
                        settings.gcs_output_bucket,
                        alt_blob_name,
                        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    
                    alt_signed_url = storage_client.generate_signed_url(
                        settings.gcs_output_bucket,
                        alt_blob_name,
                        expiration_seconds=settings.signed_url_expiration
                    )
                except Exception as alt_sign_error:
                    logger.warning(f"[Job {job.id}] Alternative signed URL generation failed: {alt_sign_error}. Using direct download endpoint.")
                    if request:
                        base_url = f"{request.url.scheme}://{request.url.netloc}"
                    else:
                        base_url = f"https://pdf-to-word-converter-iwumaktavq-uc.a.run.app"
                    alt_signed_url = f"{base_url}/api/download/{job.id}/alternative.docx"
        
        # Record daily usage or deduct credits based on tier
        if not is_authenticated and free_tier_allowed:
            # Free tier usage - record daily usage
            try:
                from app.daily_usage import record_daily_usage
                record_daily_usage(user_id, conversion_result.pages, conversion_result.used_docai, db)
                logger.info(f"[Job {job.id}] Recorded free tier usage: {user_id}, {conversion_result.pages} pages, OCR: {conversion_result.used_docai}")
            except Exception as usage_error:
                logger.error(f"[Job {job.id}] Error recording daily usage: {usage_error}", exc_info=True)
        elif is_authenticated:
            # Premium user - deduct credits after successful conversion
            try:
                from app.credit_manager import calculate_required_credits
                required_credits = calculate_required_credits(
                    conversion_result.pages,
                    conversion_result.used_docai,
                    conversion_result.used_adobe_extract
                )
                
                deduct_result = deduct_credits(
                    user_id=user_id,
                    amount=required_credits,
                    reason='Converted PDF to Word',
                    metadata={
                        'file_name': file.filename,
                        'page_count': conversion_result.pages,
                        'processor': conversion_result.main_method.value,
                        'tool': 'pdf-to-word',
                        'job_id': job.id,
                        'engine': engine
                    },
                    db=db
                )
                
                if deduct_result.get('success'):
                    logger.info(f"[Job {job.id}] Credits deducted: {required_credits}. Remaining: {deduct_result['creditsRemaining']}")
                else:
                    logger.error(f"[Job {job.id}] Failed to deduct credits: {deduct_result.get('error')}")
                    # Don't fail the conversion if credit deduction fails - log it
            except Exception as credit_error:
                logger.error(f"[Job {job.id}] Error deducting credits: {credit_error}", exc_info=True)
                # Don't fail the conversion - log the error
        
        # Update job status to completed
        job_status = "completed"
        
        # Log successful conversion details
        conversion_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[Job {job.id}] Conversion successful - Engine: {engine}, Pages: {conversion_result.pages}, Time: {conversion_time_ms}ms, DocAI Confidence: {docai_confidence}")
        
        # Update job with success details
        update_job_success(
            job_id=job.id,
            download_url=primary_signed_url,
            engine=engine,
            pages=conversion_result.pages,
            confidence=docai_confidence
        )
        
        # Also update via legacy function for compatibility
        update_job_status(
            job.id,
            "done",
            result_url=primary_signed_url,
            pages=conversion_result.pages,
            used_docai=conversion_result.used_docai,
            conversion_time_ms=conversion_result.conversion_time_ms
        )
        
        logger.info(f"[Job {job.id}] Upload complete. Primary URL ready, Alternative: {'Available' if alt_signed_url else 'None'}")
        
        return ConvertResponse(
            status="success",
            job_id=job.id,
            primary_download_url=primary_signed_url,
            primary_method=conversion_result.main_method.value,
            alt_download_url=alt_signed_url,
            alt_method=conversion_result.alt_method.value if conversion_result.alt_method else None,
            pages=conversion_result.pages,
            used_docai=conversion_result.used_docai,
            conversion_time_ms=conversion_result.conversion_time_ms,
            file_size_bytes=os.path.getsize(primary_docx_path),
            download_url=primary_signed_url,  # Backward compatibility
            job_status=job_status,
            engine=engine,
            docai_confidence=docai_confidence
        )
        
    except HTTPException as e:
        job_status = "failed"
        if job:
            error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
            update_job_failure(job.id, error_msg)
            update_job_status(job.id, "error", error_message=error_msg)
        logger.exception(f"[Job {job.id if job else 'N/A'}] HTTP Exception: {error_msg if job else str(e.detail)}")
        raise
    except Exception as e:
        job_status = "failed"
        error_msg = str(e)
        logger.exception(f"[Job {job.id if job else 'N/A'}] Conversion error: {error_msg}")
        if job:
            update_job_failure(job.id, error_msg)
            update_job_status(job.id, "error", error_message=error_msg)
        # Return JSON with error details for better frontend handling
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": f"Conversion failed: {error_msg}",
                "error_type": type(e).__name__
            }
        )
    
    finally:
        # Cleanup temporary files ONLY for premium users (free tier files need to stay for download endpoint)
        if is_authenticated or not free_tier_allowed:
            # Premium users: Cleanup immediately after GCS upload
            if temp_pdf_path:
                cleanup_file(temp_pdf_path)
            if primary_docx_path:
                cleanup_file(primary_docx_path)
            if alt_docx_path and alt_docx_path != primary_docx_path:
                cleanup_file(alt_docx_path)
            # Cleanup job directory if empty
            if temp_dir and os.path.exists(temp_dir):
                try:
                    if not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
                except:
                    pass
        else:
            # Free tier: Keep files in temp directory for download endpoint
            # Files will be cleaned up by a background task or after expiration
            logger.info(f"[Job {job.id if job else 'N/A'}] Free tier: Keeping files for direct download")


# Temporary file - copy these endpoints to main.py before exception_handler

@app.post("/api/convert/pdf-to-jpg", response_model=PdfToJpgResponse)
async def convert_pdf_to_jpg_endpoint(
    file: UploadFile = File(...),
    dpi: int = 150,
    user: dict = Depends(get_current_user_dep),
    settings: Settings = Depends(get_app_settings)
):
    """Convert PDF pages to JPG images."""
    start_time = time.time()
    temp_pdf_path = None
    job = None
    image_paths = []
    
    try:
        job = create_job("pdf-to-jpg")
        update_job_status(job.id, "processing")
        logger.info(f"[Job {job.id}] PDF to JPG started - User: {user.get('user_id')}, File: {file.filename}, DPI: {dpi}")
        
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            error_msg = "File must be a PDF"
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        file_size_bytes = file.size or 0
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            error_msg = f"File too large. Maximum: {settings.max_file_size_mb}MB"
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=413, detail=error_msg)
        
        ensure_temp_dir()
        temp_pdf_filename = generate_temp_filename(".pdf")
        temp_pdf_path = get_temp_path(temp_pdf_filename)
        
        contents = await file.read()
        with open(temp_pdf_path, "wb") as f:
            f.write(contents)
        
        is_valid, error_msg = validate_pdf_file(temp_pdf_path, settings.max_file_size_mb)
        if not is_valid:
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        pages = get_page_count(temp_pdf_path)
        logger.info(f"[Job {job.id}] PDF has {pages} pages")
        
        temp_dir = ensure_temp_dir()
        image_paths = convert_pdf_to_jpg(temp_pdf_path, temp_dir, dpi=dpi)
        
        storage_client = GCSStorage(settings.project_id)
        job_folder = f"pdf-to-jpg/{job.id}"
        images_info = []
        
        for idx, image_path in enumerate(image_paths):
            page_num = idx + 1
            blob_name = f"{job_folder}/page-{page_num:03d}.jpg"
            
            storage_client.upload_file_to_gcs(
                image_path, settings.gcs_output_bucket, blob_name, content_type="image/jpeg"
            )
            
            signed_url = storage_client.generate_signed_url(
                settings.gcs_output_bucket, blob_name, expiration_seconds=settings.signed_url_expiration
            )
            
            images_info.append(ImageInfo(page=page_num, url=signed_url))
            cleanup_file(image_path)
        
        conversion_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[Job {job.id}] Conversion successful in {conversion_time_ms}ms, {pages} pages")
        
        update_job_status(job.id, "done", pages=pages, conversion_time_ms=conversion_time_ms)
        
        return PdfToJpgResponse(status="success", pages=pages, images=images_info, job_id=job.id)
        
    except HTTPException:
        if job:
            update_job_status(job.id, "error", error_message=str(e))
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Job {job.id if job else 'N/A'}] PDF to JPG error: {error_msg}", exc_info=True)
        if job:
            update_job_status(job.id, "error", error_message=error_msg)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {error_msg}")
    finally:
        if temp_pdf_path:
            cleanup_file(temp_pdf_path)
        for img_path in image_paths:
            cleanup_file(img_path)


@app.post("/api/convert/pdf-to-excel", response_model=ExcelConvertResponse)
async def convert_pdf_to_excel(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user_dep),
    settings: Settings = Depends(get_app_settings)
):
    """
    Convert PDF to Excel (Premium Pro) - requires login and credits >= 30.
    Excel conversion is optimized for tables, invoices, forms, and ID cards.
    """
    start_time = time.time()
    job = None
    temp_pdf_path = None
    temp_dir = None
    excel_path = None
    
    try:
        # Create job for tracking
        job = create_job("pdf-to-excel")
        update_job_status(job.id, "processing")
        logger.info(f"[Job {job.id}] PDF to Excel conversion started - User: {user.get('user_id')}, File: {file.filename}")
        
        # Validate file
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            error_msg = "File must be a PDF"
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Check user authentication - Excel requires login
        user_id = user.get('user_id', 'anonymous')
        is_authenticated = user_id and user_id != 'anonymous'
        
        if not is_authenticated:
            error_msg = "Excel conversion (Premium Pro) requires login. Please sign in to continue."
            logger.warning(f"[Job {job.id}] {error_msg}")
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "AUTHENTICATION_REQUIRED",
                    "message": error_msg
                }
            )
        
        # Check file size
        file_size_bytes = file.size or 0
        from app.credit_manager import PREMIUM_MAX_FILE_SIZE_MB
        file_size_mb = file_size_bytes / (1024 * 1024)
        max_size_mb = PREMIUM_MAX_FILE_SIZE_MB  # 50MB for premium users
        
        if file_size_mb > max_size_mb:
            error_msg = f"File too large. Maximum size for premium users: {max_size_mb}MB. Your file is {file_size_mb:.2f}MB."
            logger.warning(f"[Job {job.id}] {error_msg}")
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=413, detail=error_msg)
        
        # Save uploaded file
        temp_dir = os.path.join(ensure_temp_dir(), job.id)
        os.makedirs(temp_dir, exist_ok=True)
        temp_pdf_path = os.path.join(temp_dir, "input.pdf")
        
        contents = await file.read()
        with open(temp_pdf_path, "wb") as f:
            f.write(contents)
        
        file_size = os.path.getsize(temp_pdf_path)
        logger.info(f"[Job {job.id}] File saved: {temp_pdf_path}, size: {file_size} bytes")
        
        # Validate PDF
        is_valid, error_msg = validate_pdf_file(temp_pdf_path, settings.max_file_size_mb)
        if not is_valid:
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Use document detection to analyze
        from app.document_detector import detect_document, check_premium_requirements
        analysis = detect_document(temp_pdf_path, file_size, settings, use_docai_for_analysis=True)
        pages_count = analysis.page_count
        
        # Check premium requirements (login + credits >= 30)
        db = get_firestore_client()
        user_credits_info = get_user_credits(user_id, db)
        user_credits = user_credits_info.get('credits', 0)
        
        premium_check = check_premium_requirements(analysis, user_credits)
        
        if not premium_check['eligible']:
            error_msg = premium_check['reason']
            logger.warning(f"[Job {job.id}] {error_msg}")
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "PREMIUM_REQUIREMENTS_NOT_MET",
                    "message": error_msg,
                    "required": premium_check.get('required', 0),
                    "available": premium_check.get('current_credits', user_credits),
                    "required_minimum": premium_check.get('required_minimum', 30)
                }
            )
        
        required_credits = premium_check['required']
        logger.info(f"[Job {job.id}] Premium user: {user_id}, {pages_count} pages, Credits required: {required_credits}")
        
        # Parse document with Document AI once
        with open(temp_pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        from app.docai_client import process_pdf_to_layout
        parsed_doc = process_pdf_to_layout(
            settings.project_id,
            settings.docai_location,
            settings.docai_processor_id,
            pdf_bytes
        )
        table_count = len(parsed_doc.tables) if parsed_doc.tables else 0
        
        # Perform Excel conversion using parsed document
        excel_path = os.path.join(temp_dir, "output.xlsx")
        logger.info(f"[Job {job.id}] Starting Excel conversion with Document AI (found {table_count} tables)")
        
        convert_pdf_to_excel_with_docai(
            temp_pdf_path,
            excel_path,
            parsed_doc=parsed_doc,  # Use pre-parsed document
            settings=settings
        )
        
        # Upload to GCS
        storage_client = GCSStorage(settings.project_id)
        excel_blob_name = f"converted/{job.id}/output.xlsx"
        
        logger.info(f"[Job {job.id}] Uploading Excel to GCS: {excel_blob_name}")
        storage_client.upload_file_to_gcs(
            excel_path,
            settings.gcs_output_bucket,
            excel_blob_name,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        signed_url = storage_client.generate_signed_url(
            settings.gcs_output_bucket,
            excel_blob_name,
            expiration_seconds=settings.signed_url_expiration
        )
        
        # Deduct credits after successful conversion
        try:
            deduct_result = deduct_credits(
                user_id=user_id,
                amount=required_credits,
                reason='Converted PDF to Excel (Premium Pro)',
                metadata={
                    'file_name': file.filename,
                    'page_count': pages_count,
                    'table_count': table_count,
                    'processor': 'docai',
                    'tool': 'pdf-to-excel',
                    'job_id': job.id,
                    'engine': 'docai'
                },
                db=db
            )
            
            if deduct_result.get('success'):
                logger.info(f"[Job {job.id}] Credits deducted: {required_credits}. Remaining: {deduct_result['creditsRemaining']}")
            else:
                logger.error(f"[Job {job.id}] Failed to deduct credits: {deduct_result.get('error')}")
        except Exception as credit_error:
            logger.error(f"[Job {job.id}] Error deducting credits: {credit_error}", exc_info=True)
        
        # Update job status
        conversion_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[Job {job.id}] Excel conversion successful - Pages: {pages_count}, Tables: {table_count}, Time: {conversion_time_ms}ms")
        
        update_job_status(job.id, "done", pages=pages_count, conversion_time_ms=conversion_time_ms)
        update_job_success(
            job_id=job.id,
            download_url=signed_url,
            engine="docai",
            pages=pages_count,
            confidence=None
        )
        
        return ExcelConvertResponse(
            status="success",
            job_id=job.id,
            download_url=signed_url,
            pages=pages_count,
            table_count=table_count,
            conversion_time_ms=conversion_time_ms,
            file_size_bytes=os.path.getsize(excel_path),
            job_status="completed"
        )
        
    except HTTPException as e:
        if job:
            error_msg = str(e.detail) if hasattr(e, 'detail') else str(e)
            update_job_failure(job.id, error_msg)
            update_job_status(job.id, "error", error_message=error_msg)
        logger.exception(f"[Job {job.id if job else 'N/A'}] HTTP Exception: {str(e.detail) if hasattr(e, 'detail') else str(e)}")
        raise
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"[Job {job.id if job else 'N/A'}] Excel conversion error: {error_msg}")
        if job:
            update_job_failure(job.id, error_msg)
            update_job_status(job.id, "error", error_message=error_msg)
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": f"Excel conversion failed: {error_msg}",
                "error_type": type(e).__name__
            }
        )
    finally:
        # Cleanup
        if temp_pdf_path:
            cleanup_file(temp_pdf_path)
        if excel_path:
            cleanup_file(excel_path)
        if temp_dir and os.path.exists(temp_dir):
            try:
                if not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass


@app.get("/api/pdf/thumbnail")
async def get_pdf_thumbnail(
    file_url: Optional[str] = None,
    job_id: Optional[str] = None,
    page: int = 1,
    width: int = 300,
    settings: Settings = Depends(get_app_settings)
):
    """Generate thumbnail of PDF first page."""
    temp_pdf_path = None
    temp_thumbnail_path = None
    
    try:
        if not file_url and not job_id:
            raise HTTPException(status_code=400, detail="Either file_url or job_id required")
        
        if file_url:
            import requests
            ensure_temp_dir()
            temp_pdf_filename = generate_temp_filename(".pdf")
            temp_pdf_path = get_temp_path(temp_pdf_filename)
            
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            with open(temp_pdf_path, "wb") as f:
                f.write(response.content)
        else:
            raise HTTPException(status_code=400, detail="job_id retrieval not yet implemented")
        
        ensure_temp_dir()
        temp_thumbnail_filename = generate_temp_filename(".jpg")
        temp_thumbnail_path = get_temp_path(temp_thumbnail_filename)
        
        generate_pdf_thumbnail(temp_pdf_path, temp_thumbnail_path, width_px=width)
        
        storage_client = GCSStorage(settings.project_id)
        blob_name = f"thumbnails/{generate_temp_filename('.jpg')}"
        
        storage_client.upload_file_to_gcs(
            temp_thumbnail_path, settings.gcs_output_bucket, blob_name, content_type="image/jpeg"
        )
        
        signed_url = storage_client.generate_signed_url(
            settings.gcs_output_bucket, blob_name, expiration_seconds=settings.signed_url_expiration
        )
        
        return {"status": "success", "thumbnail_url": signed_url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Thumbnail error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Thumbnail generation failed: {str(e)}")
    finally:
        if temp_pdf_path:
            cleanup_file(temp_pdf_path)
        if temp_thumbnail_path:
            cleanup_file(temp_thumbnail_path)


@app.post("/api/pdf/apply-annotations", response_model=AnnotationApplyResponse)
async def apply_annotations_endpoint(
    file: UploadFile = File(...),
    annotations: str = Form(...),
    canvas_width: float = Form(800.0),
    canvas_height: float = Form(600.0),
    user: dict = Depends(get_current_user_dep),
    settings: Settings = Depends(get_app_settings)
):
    """Apply annotations to PDF and return edited PDF."""
    start_time = time.time()
    temp_pdf_path = None
    temp_output_path = None
    job = None
    
    try:
        import json
        job = create_job("pdf-apply-annotations")
        update_job_status(job.id, "processing")
        logger.info(f"[Job {job.id}] Applying annotations - User: {user.get('user_id')}")
        
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            error_msg = "File must be a PDF"
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        try:
            annotations_data = json.loads(annotations)
            if not isinstance(annotations_data, list):
                raise ValueError("Annotations must be a list")
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {str(e)}"
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        ensure_temp_dir()
        temp_pdf_filename = generate_temp_filename(".pdf")
        temp_pdf_path = get_temp_path(temp_pdf_filename)
        
        contents = await file.read()
        with open(temp_pdf_path, "wb") as f:
            f.write(contents)
        
        is_valid, error_msg = validate_pdf_file(temp_pdf_path, settings.max_file_size_mb)
        if not is_valid:
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        pages = get_page_count(temp_pdf_path)
        temp_output_filename = generate_temp_filename("-annotated.pdf")
        temp_output_path = get_temp_path(temp_output_filename)
        
        apply_annotations_to_pdf(temp_pdf_path, annotations_data, temp_output_path,
                                  canvas_width=canvas_width, canvas_height=canvas_height)
        
        storage_client = GCSStorage(settings.project_id)
        blob_name = f"annotated/{job.id}.pdf"
        
        storage_client.upload_file_to_gcs(
            temp_output_path, settings.gcs_output_bucket, blob_name, content_type="application/pdf"
        )
        
        signed_url = storage_client.generate_signed_url(
            settings.gcs_output_bucket, blob_name, expiration_seconds=settings.signed_url_expiration
        )
        
        conversion_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[Job {job.id}] Annotations applied in {conversion_time_ms}ms")
        
        update_job_status(job.id, "done", result_url=signed_url, pages=pages, conversion_time_ms=conversion_time_ms)
        
        return AnnotationApplyResponse(status="success", download_url=signed_url, job_id=job.id, pages=pages)
        
    except HTTPException:
        if job:
            update_job_status(job.id, "error", error_message=str(e))
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Job {job.id if job else 'N/A'}] Annotation error: {error_msg}", exc_info=True)
        if job:
            update_job_status(job.id, "error", error_message=error_msg)
        raise HTTPException(status_code=500, detail=f"Annotation failed: {error_msg}")
    finally:
        if temp_pdf_path:
            cleanup_file(temp_pdf_path)
        if temp_output_path:
            cleanup_file(temp_output_path)


@app.get("/api/jobs/{job_id}", response_model=ConversionJob)
async def get_job_status(job_id: str):
    """Get job status by ID."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/download/{job_id}/{filename}")
async def download_file(
    job_id: str,
    filename: str,
    settings: Settings = Depends(get_app_settings)
):
    """
    Direct file download endpoint for free tier (bypasses GCS signed URLs).
    Files are served directly from temp directory.
    """
    try:
        # Security: Only allow .docx files from job directories
        if not filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Construct file path
        temp_dir = os.path.join(ensure_temp_dir(), job_id)
        file_path = os.path.join(temp_dir, filename)
        
        # Security: Verify file exists and is within allowed directory
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Verify file is within temp directory (prevent path traversal)
        real_path = os.path.realpath(file_path)
        real_temp_dir = os.path.realpath(temp_dir)
        if not real_path.startswith(real_temp_dir):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Return file with appropriate headers
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error for job {job_id}, file {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


# ==================== CREDIT SYSTEM ENDPOINTS ====================

@app.get("/api/user/credits", response_model=CreditBalanceResponse)
async def get_user_credit_balance(
    user: dict = Depends(get_current_user_dep),
    settings: Settings = Depends(get_app_settings)
):
    """Get current credit balance for authenticated user."""
    user_id = user.get('user_id')
    if not user_id or user_id == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        db = get_firestore_client()
        credit_info = get_user_credits(user_id, db)
        
        if 'error' in credit_info:
            raise HTTPException(status_code=500, detail=credit_info['error'])
        
        return CreditBalanceResponse(
            credits=credit_info.get('credits', 0),
            totalCreditsEarned=credit_info.get('totalCreditsEarned', 0),
            totalCreditsUsed=credit_info.get('totalCreditsUsed', 0)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user credits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve credit balance")


@app.get("/api/user/history", response_model=CreditHistoryResponse)
async def get_user_credit_history(
    limit: int = 50,
    user: dict = Depends(get_current_user_dep),
    settings: Settings = Depends(get_app_settings)
):
    """Get credit transaction history for authenticated user."""
    user_id = user.get('user_id')
    if not user_id or user_id == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        db = get_firestore_client()
        history = get_credit_history(user_id, limit, db)
        
        transactions = []
        for txn in history:
            # Convert Firestore timestamp to ISO string
            date_value = txn.get('date')
            if hasattr(date_value, 'isoformat'):
                date_str = date_value.isoformat()
            elif isinstance(date_value, datetime):
                date_str = date_value.isoformat()
            else:
                date_str = str(date_value) if date_value else datetime.utcnow().isoformat()
            
            transactions.append(CreditTransaction(
                id=txn.get('id', ''),
                date=date_str,
                type=txn.get('type', 'deduct'),
                credits=float(txn.get('credits', 0)),
                description=txn.get('description', ''),
                creditsBefore=float(txn.get('creditsBefore', 0)),
                creditsAfter=float(txn.get('creditsAfter', 0)),
                file_name=txn.get('file_name'),
                page_count=txn.get('page_count'),
                processor=txn.get('processor')
            ))
        
        return CreditHistoryResponse(transactions=transactions)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting credit history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve credit history")


@app.post("/api/user/add-credits", response_model=CreditAddResponse)
async def add_user_credits(
    request: CreditAddRequest,
    user: dict = Depends(get_current_user_dep),
    settings: Settings = Depends(get_app_settings)
):
    """Add credits to user account (typically after payment)."""
    user_id = user.get('user_id')
    if not user_id or user_id == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        db = get_firestore_client()
        result = add_credits(
            user_id=user_id,
            amount=request.amount,
            reason=request.reason,
            metadata=request.metadata,
            db=db
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to add credits'))
        
        return CreditAddResponse(
            success=True,
            creditsAdded=result['creditsAdded'],
            creditsRemaining=result['creditsRemaining'],
            creditsBefore=result['creditsBefore']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding credits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add credits")


@app.post("/api/convert/pdf-metadata", response_model=PdfMetadataResponse)
async def get_pdf_metadata_for_credits(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_app_settings)
):
    """
    Get PDF metadata using central document detection engine.
    Analyzes document and suggests appropriate tool (Word vs Excel).
    Accepts POST with multipart/form-data file upload.
    """
    temp_pdf_path = None
    try:
        logger.info(f"PDF metadata request - File: {file.filename if file else 'N/A'}, Size: {file.size if file else 0} bytes")
        
        # Save file temporarily
        temp_dir = ensure_temp_dir()
        temp_pdf_path = os.path.join(temp_dir, generate_temp_filename(".pdf"))
        
        contents = await file.read()
        with open(temp_pdf_path, "wb") as f:
            f.write(contents)
        
        file_size_bytes = os.path.getsize(temp_pdf_path)
        
        # Use central document detection engine
        from app.document_detector import detect_document, check_free_tier_eligibility
        analysis = detect_document(temp_pdf_path, file_size_bytes, settings, use_docai_for_analysis=True)
        
        # Get user ID for daily usage check
        user = get_user_from_token(authorization) if authorization else {'user_id': 'anonymous'}
        user_id = user.get('user_id', 'anonymous')
        is_authenticated = user_id and user_id != 'anonymous'
        
        # Check free tier eligibility
        free_tier_eligibility = check_free_tier_eligibility(analysis, is_authenticated)
        
        # Check daily free tier usage (for free tier calculations)
        from app.daily_usage import get_today_usage, FREE_TIER_DAILY_PAGES_TEXT, FREE_TIER_DAILY_PAGES_OCR
        db = get_firestore_client()
        daily_usage = get_today_usage(user_id, db)
        
        # Calculate estimated credits based on analysis
        if analysis.suggested_tool == "excel":
            # Excel uses premium pricing
            estimated_credits_text = analysis.page_count * analysis.credit_cost_per_page
            estimated_credits_ocr = estimated_credits_text  # Excel always uses DocAI
        else:
            # Word conversion
            estimated_credits_text = calculate_required_credits(analysis.page_count, False)
            estimated_credits_ocr = calculate_required_credits(analysis.page_count, True)
        
        logger.info(f"PDF metadata: pages={analysis.page_count}, has_text={analysis.has_text}, has_tables={analysis.has_tables}, "
                   f"suggested_tool={analysis.suggested_tool}, requires_premium={analysis.requires_premium}, "
                   f"free_tier_allowed={free_tier_eligibility.get('allowed', False)}")
        
        return PdfMetadataResponse(
            pages=analysis.page_count,
            has_text=analysis.has_text,
            file_size_bytes=file_size_bytes,
            estimated_credits_text=estimated_credits_text,
            estimated_credits_ocr=estimated_credits_ocr,
            daily_usage_text=daily_usage['text_pages'],
            daily_usage_ocr=daily_usage['ocr_pages'],
            daily_limit_text=FREE_TIER_DAILY_PAGES_TEXT,
            daily_limit_ocr=FREE_TIER_DAILY_PAGES_OCR,
            can_use_free_tier=free_tier_eligibility.get('allowed', False),
            has_tables=analysis.has_tables,
            is_id_card_like=analysis.is_id_card_like,
            is_scanned=analysis.is_scanned,
            suggested_tool=analysis.suggested_tool,
            requires_premium=analysis.requires_premium,
            suggestion_reason=analysis.reason
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting PDF metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get PDF metadata: {str(e)}")
    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            cleanup_file(temp_pdf_path)



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )


