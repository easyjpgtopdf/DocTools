"""
FastAPI main application.
Handles PDF to Word conversion endpoints.
"""
import os
import time
import logging
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Header, Request, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from app.config import get_settings, Settings
from app.models import (
    ConvertResponse,
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
        
        # Get settings (this will fail if required env vars are missing)
        settings = get_settings()
        logger.info(f"Settings loaded: project_id={settings.project_id}")
        
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
    user: dict = Depends(get_current_user_dep),
    settings: Settings = Depends(get_app_settings)
):
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
        
        # Validate PDF
        is_valid, error_msg = validate_pdf_file(temp_pdf_path, settings.max_file_size_mb)
        if not is_valid:
            if job:
                update_job_status(job.id, "error", error_message=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        file_size = os.path.getsize(temp_pdf_path)
        logger.info(f"[Job {job.id}] File saved: {temp_pdf_path}, size: {file_size} bytes")
        print(f"DEBUG: PDF saved: {temp_pdf_path}")
        
        # Get page count for credit calculation
        pages_count = get_page_count(temp_pdf_path)
        
        # Check credits if user is authenticated
        user_id = user.get('user_id')
        if user_id and user_id != 'anonymous':
            # Detect if PDF is text-based or scanned (will use OCR)
            has_text = pdf_has_text(temp_pdf_path)
            will_use_docai = not has_text  # OCR if no text
            
            # Calculate required credits
            required_credits = calculate_required_credits(pages_count, will_use_docai)
            
            # Check if user has sufficient credits
            db = get_firestore_client()
            credit_check = has_sufficient_credits(user_id, required_credits, db)
            
            if not credit_check['hasCredits']:
                error_msg = f"Insufficient credits. Required: {required_credits}, Available: {credit_check['creditsAvailable']}"
                logger.warning(f"[Job {job.id}] {error_msg}")
                if job:
                    update_job_status(job.id, "error", error_message=error_msg)
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "NOT_ENOUGH_CREDITS",
                        "required": required_credits,
                        "available": credit_check['creditsAvailable'],
                        "message": error_msg
                    }
                )
            
            logger.info(f"[Job {job.id}] Credits check passed. Required: {required_credits}, Available: {credit_check['creditsAvailable']}")
        
        # Perform smart conversion (generates both primary and alternative)
        logger.info(f"[Job {job.id}] Starting smart conversion with alternative generation")
        
        # Track job status and engine
        job_status = "processing"
        engine = None
        docai_confidence = None
        
        conversion_result = smart_convert_pdf_to_word(
            temp_pdf_path,
            temp_dir,
            settings,
            generate_alternative=True
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
        
        # Upload primary file to GCS
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
        
        primary_signed_url = storage_client.generate_signed_url(
            settings.gcs_output_bucket,
            primary_blob_name,
            expiration_seconds=settings.signed_url_expiration
        )
        print(f"DEBUG: Upload path: {primary_signed_url}")
        
        # Upload alternative file if available
        alt_signed_url = None
        if alt_docx_path and os.path.exists(alt_docx_path):
            alt_blob_name = f"converted/{job.id}/alternative.docx"
            logger.info(f"[Job {job.id}] Uploading alternative DOCX to GCS: {alt_blob_name}")
            
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
        
        # Deduct credits after successful conversion
        if user_id and user_id != 'anonymous':
            try:
                db = get_firestore_client()
                required_credits = calculate_required_credits(conversion_result.pages, conversion_result.used_docai)
                
                deduct_result = deduct_credits(
                    user_id=user_id,
                    amount=required_credits,
                    reason='Converted PDF to Word',
                    metadata={
                        'file_name': file.filename,
                        'page_count': conversion_result.pages,
                        'processor': conversion_result.main_method.value,
                        'job_id': job.id
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
        raise
    except Exception as e:
        job_status = "failed"
        error_msg = str(e)
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"[Job {job.id if job else 'N/A'}] Conversion error: {error_msg}")
        logger.error(f"[Job {job.id if job else 'N/A'}] Full traceback:\n{error_traceback}")
        print(f"DEBUG: Conversion error: {error_msg}")
        print(f"DEBUG: Full traceback:\n{error_traceback}")
        if job:
            update_job_failure(job.id, error_msg)
            update_job_status(job.id, "error", error_message=error_msg)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {error_msg}")
    
    finally:
        # Cleanup temporary files
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


@app.post("/api/convert/pdf-metadata")
async def get_pdf_metadata_for_credits(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_app_settings)
):
    """Get PDF metadata (pages, size) to calculate required credits."""
    temp_pdf_path = None
    try:
        # Save file temporarily
        temp_dir = ensure_temp_dir()
        temp_pdf_path = os.path.join(temp_dir, generate_temp_filename(".pdf"))
        
        contents = await file.read()
        with open(temp_pdf_path, "wb") as f:
            f.write(contents)
        
        # Get page count
        pages = get_page_count(temp_pdf_path)
        file_size_bytes = os.path.getsize(temp_pdf_path)
        
        # Calculate estimated credits
        estimated_credits_text = calculate_required_credits(pages, False)
        estimated_credits_ocr = calculate_required_credits(pages, True)
        
        return PdfMetadataResponse(
            pages=pages,
            file_size_bytes=file_size_bytes,
            estimated_credits_text=estimated_credits_text,
            estimated_credits_ocr=estimated_credits_ocr
        )
    except Exception as e:
        logger.error(f"Error getting PDF metadata: {e}", exc_info=True)
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


