"""
FastAPI main application.
Handles PDF to Word conversion endpoints.
"""
import os
import time
import logging
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from app.config import get_settings, Settings
from app.models import HealthResponse, ConvertResponse, ErrorResponse
from app.auth import initialize_firebase, get_user_from_token
from app.storage import GCSStorage
from app.converter import pdf_has_text, convert_pdf_to_docx_with_libreoffice, convert_pdf_to_docx_with_docai
from app.docai_client import process_pdf_to_layout
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    try:
        settings = get_settings()
        if settings.google_application_credentials:
            initialize_firebase(settings.google_application_credentials)
        else:
            initialize_firebase()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup error: {e}")


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


@app.post("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


@app.post("/api/convert/pdf-to-word", response_model=ConvertResponse)
async def convert_pdf_to_word(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user_dep),
    settings: Settings = Depends(get_app_settings)
):
    """
    Convert PDF file to Word document.
    
    - **file**: PDF file to convert (multipart/form-data)
    - **Authorization**: Optional Bearer token (Firebase ID token)
    """
    start_time = time.time()
    temp_pdf_path = None
    temp_docx_path = None
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        logger.info(f"Conversion request from user: {user.get('user_id')}, file: {file.filename}")
        
        # Save uploaded file to temp directory
        ensure_temp_dir()
        temp_pdf_filename = generate_temp_filename(".pdf")
        temp_pdf_path = get_temp_path(temp_pdf_filename)
        
        # Read and save file
        contents = await file.read()
        with open(temp_pdf_path, "wb") as f:
            f.write(contents)
        
        # Validate file
        is_valid, error_msg = validate_pdf_file(temp_pdf_path, settings.max_file_size_mb)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        file_size = os.path.getsize(temp_pdf_path)
        logger.info(f"File saved: {temp_pdf_path}, size: {file_size} bytes")
        
        # Determine conversion method
        has_text = pdf_has_text(temp_pdf_path)
        logger.info(f"PDF has text: {has_text}")
        
        # Get page count for response
        from app.converter import get_page_count
        pages = get_page_count(temp_pdf_path)
        logger.info(f"PDF has {pages} pages")
        
        temp_dir = ensure_temp_dir()
        output_filename = generate_temp_filename(".docx")
        temp_docx_path = get_temp_path(output_filename)
        
        used_docai = False
        
        if has_text:
            # Use LibreOffice for PDFs with text
            logger.info("Using LibreOffice conversion")
            temp_docx_path = convert_pdf_to_docx_with_libreoffice(temp_pdf_path, temp_dir)
            # Extract base name (LibreOffice adds .docx extension)
            if not temp_docx_path.endswith('.docx'):
                temp_docx_path = temp_docx_path + '.docx'
        else:
            # Use Document AI for scanned PDFs
            logger.info("Using Document AI conversion")
            used_docai = True
            
            # Read PDF bytes
            with open(temp_pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            # Process with Document AI
            parsed_doc = process_pdf_to_layout(
                settings.project_id,
                settings.docai_location,
                settings.docai_processor_id,
                pdf_bytes
            )
            
            # Count pages
            pages = len(parsed_doc.pages)
            
            # Convert to DOCX
            convert_pdf_to_docx_with_docai(temp_pdf_path, temp_docx_path, parsed_doc)
        
        # Upload to GCS
        logger.info(f"Uploading DOCX to GCS: {settings.gcs_output_bucket}")
        storage_client = GCSStorage(settings.project_id)
        
        # Generate unique blob name
        import uuid
        blob_name = f"{uuid.uuid4()}.docx"
        
        storage_client.upload_file_to_gcs(
            temp_docx_path,
            settings.gcs_output_bucket,
            blob_name,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # Generate signed URL
        signed_url = storage_client.generate_signed_url(
            settings.gcs_output_bucket,
            blob_name,
            expiration_seconds=settings.signed_url_expiration
        )
        
        # Calculate conversion time
        conversion_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Conversion successful in {conversion_time_ms}ms, used_docai={used_docai}")
        
        return ConvertResponse(
            status="success",
            download_url=signed_url,
            used_docai=used_docai,
            pages=pages,
            conversion_time_ms=conversion_time_ms,
            file_size_bytes=os.path.getsize(temp_docx_path)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    finally:
        # Cleanup temporary files
        if temp_pdf_path:
            cleanup_file(temp_pdf_path)
        if temp_docx_path:
            cleanup_file(temp_docx_path)


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

