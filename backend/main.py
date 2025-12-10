"""
FastAPI backend for PDF to Excel conversion.
Supports both AWS Textract (fallback) and Google Document AI.
"""

import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import traceback

from credit import get_user_id, get_credits, deduct_credits, check_sufficient_credits, get_credit_info
from storage_gcs import upload_excel_to_gcs
# Lazy import for docai_service to avoid startup errors
# from docai_service import process_pdf_to_excel_docai

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Multi-processor functions (lazy import to avoid startup errors)
# These will be imported only when needed
_get_available_processors = None
_get_processor_id_func = None
_process_pdf_with_processor_func = None

def _lazy_import_multi_processor():
    """Lazy import multi-processor module."""
    global _get_available_processors, _get_processor_id_func, _process_pdf_with_processor_func
    if _get_available_processors is None:
        try:
            # Import with explicit error handling
            import sys
            import traceback
            from docai_multi_processor import (
                get_available_processors,
                get_processor_id,
                process_pdf_with_processor
            )
            _get_available_processors = get_available_processors
            _get_processor_id_func = get_processor_id
            _process_pdf_with_processor_func = process_pdf_with_processor
        except Exception as e:
            logger.error(f"Could not load multi-processor module: {e}")
            logger.error(traceback.format_exc())
            # Return empty functions that won't break the app
            _get_available_processors = lambda: []
            _get_processor_id_func = lambda x: None
            _process_pdf_with_processor_func = lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("Multi-processor module not available"))

def get_available_processors():
    """Get available processors."""
    _lazy_import_multi_processor()
    if _get_available_processors:
        try:
            return _get_available_processors()
        except Exception as e:
            logger.warning(f"Error getting processors: {e}")
            return []
    return []

def get_processor_id(processor_type: str):
    """Get processor ID."""
    _lazy_import_multi_processor()
    if _get_processor_id_func:
        try:
            return _get_processor_id_func(processor_type)
        except Exception as e:
            logger.warning(f"Error getting processor ID: {e}")
            return None
    return None

def process_pdf_with_processor(file_bytes: bytes, filename: str, processor_type: str):
    """Process PDF with processor."""
    _lazy_import_multi_processor()
    if _process_pdf_with_processor_func:
        return _process_pdf_with_processor_func(file_bytes, filename, processor_type)
    raise ValueError("Multi-processor module not available")

# Initialize FastAPI app
app = FastAPI(
    title="PDF to Excel Converter API",
    description="Convert PDF files to Excel using AWS Textract (fallback) or Google Document AI",
    version="2.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
GCS_BUCKET = os.environ.get('GCS_BUCKET')
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "PDF to Excel Converter API",
        "version": "3.0.0",
        "providers": ["AWS Textract (optional)", "Google Document AI"],
        "endpoints": {
            "textract": "/api/pdf-to-excel (AWS Textract - requires S3_BUCKET)",
            "docai": "/api/pdf-to-excel-docai (Google Document AI - default)"
        }
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/credits")
async def get_credits_endpoint(request: Request):
    """
    Get current credit balance for the user.
    """
    try:
        user_id = get_user_id(request)
        credit_info = get_credit_info(user_id)
        return {
            "success": True,
            "credits": credit_info["credits"],
            "created_at": credit_info["created_at"]
        }
    except Exception as e:
        logger.error(f"Error getting credits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get credits: {str(e)}")


@app.post("/api/buy-credits")
async def buy_credits_endpoint(request: Request, amount: Optional[int] = None):
    """
    Dummy endpoint for buying credits.
    In production, this would integrate with payment gateway.
    """
    try:
        user_id = get_user_id(request)
        credits_to_add = amount or 10  # Default to 10 credits
        
        from credit import add_credits
        add_credits(user_id, credits_to_add)
        
        return {
            "success": True,
            "message": f"Added {credits_to_add} credits",
            "credits": get_credits(user_id)
        }
    except Exception as e:
        logger.error(f"Error buying credits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to buy credits: {str(e)}")


@app.post("/api/pdf-to-excel")
async def pdf_to_excel_endpoint(request: Request, file: UploadFile = File(...)):
    """
    Fallback endpoint: Convert PDF to Excel using AWS Textract.
    (Kept for backward compatibility)
    
    Workflow:
    1. Validate file
    2. Upload PDF to S3
    3. Check user credits
    4. Call Textract to analyze document
    5. Get page count
    6. Check credits again (after knowing page count)
    7. Parse tables from Textract response
    8. Create Excel workbook
    9. Upload Excel to GCS
    10. Deduct credits
    11. Return download URL
    """
    try:
        # Step 1: Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f}MB limit"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        logger.info(f"Received PDF file: {file.filename}, size: {file_size} bytes")
        
        # Step 2: Get user ID
        user_id = get_user_id(request)
        logger.info(f"Processing request for user: {user_id}")
        
        # Step 3: Upload PDF to S3 (for Textract)
        logger.info("Uploading PDF to S3...")
        from storage_s3 import upload_pdf_to_s3, delete_from_s3
        s3_key = upload_pdf_to_s3(file_content, file.filename)
        logger.info(f"PDF uploaded to S3: {s3_key}")
        
        # Step 4: Call Textract to get page count first
        logger.info("Calling Textract to analyze document...")
        from textract_service import analyze_document_with_tables, get_page_count
        
        S3_BUCKET = os.environ.get('S3_BUCKET')
        if not S3_BUCKET:
            delete_from_s3(s3_key)
            raise HTTPException(
                status_code=500,
                detail="S3_BUCKET environment variable not configured. AWS Textract requires S3 bucket. Please use Document AI endpoint instead: /api/pdf-to-excel-docai"
            )
        
        textract_response = analyze_document_with_tables(S3_BUCKET, s3_key)
        page_count = get_page_count(textract_response)
        logger.info(f"PDF has {page_count} pages")
        
        # Step 5: Check credits
        if not check_sufficient_credits(user_id, page_count):
            delete_from_s3(s3_key)
            return JSONResponse(
                status_code=402,
                content={
                    "insufficient_credits": True,
                    "message": f"Insufficient credits. Need {page_count} credits, have {get_credits(user_id)}",
                    "required": page_count,
                    "available": get_credits(user_id)
                }
            )
        
        # Step 6: Parse tables and create Excel
        logger.info("Converting PDF to Excel...")
        from textract_service import convert_pdf_to_excel as textract_convert
        
        excel_bytes, actual_page_count, tables = textract_convert(
            S3_BUCKET, s3_key, file.filename
        )
        
        logger.info(f"Excel created: {len(excel_bytes)} bytes, {len(tables)} tables")
        
        # Step 6: Upload Excel to GCS
        logger.info("Uploading Excel to GCS...")
        base_filename = file.filename.replace('.pdf', '').replace('.PDF', '')
        download_url = upload_excel_to_gcs(excel_bytes, base_filename)
        logger.info(f"Excel uploaded, download URL generated")
        
        # Step 7: Deduct credits (only after successful conversion)
        deduct_credits(user_id, actual_page_count)
        credits_left = get_credits(user_id)
        logger.info(f"Credits deducted: {actual_page_count}, remaining: {credits_left}")
        
        # Step 8: Return success response
        return {
            "status": "success",
            "engine": "textract",
            "downloadUrl": download_url,
            "pagesProcessed": actual_page_count,
            "creditsLeft": credits_left,
            "tablesFound": len(tables),
            "filename": f"{base_filename}.xlsx"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        if 's3_key' in locals():
            try:
                delete_from_s3(s3_key)
            except:
                pass
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Clean up S3 file on error
        if 's3_key' in locals():
            try:
                delete_from_s3(s3_key)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )


@app.post("/api/pdf-to-excel-docai")
async def pdf_to_excel_docai_endpoint(request: Request, file: UploadFile = File(...)):
    """
    New endpoint: Convert PDF to Excel using Google Document AI.
    
    Workflow:
    1. Validate file
    2. Check Document AI environment variables
    3. Process PDF with Document AI (estimate pages or process first)
    4. Get page count from Document AI response
    5. Check credits
    6. Extract tables and create Excel
    7. Upload Excel to GCS
    8. Deduct credits
    9. Return download URL
    """
    try:
        # Step 1: Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f}MB limit"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        logger.info(f"Received PDF file: {file.filename}, size: {file_size} bytes")
        
        # Step 2: Check Document AI environment variables
        if not os.environ.get('DOCAI_PROCESSOR_ID'):
            raise HTTPException(
                status_code=500,
                detail={"error": "Document AI environment variables not configured", "message": "DOCAI_PROCESSOR_ID is required"}
            )
        
        if not os.environ.get('DOCAI_PROJECT_ID'):
            raise HTTPException(
                status_code=500,
                detail={"error": "Document AI environment variables not configured", "message": "DOCAI_PROJECT_ID is required"}
            )
        
        if not os.environ.get('DOCAI_LOCATION'):
            raise HTTPException(
                status_code=500,
                detail={"error": "Document AI environment variables not configured", "message": "DOCAI_LOCATION is required"}
            )
        
        # Step 3: Get user ID
        user_id = get_user_id(request)
        logger.info(f"Processing request for user: {user_id}")
        
        # Step 4: Process PDF with Document AI (lazy import)
        # This will return page count and create Excel
        logger.info("Processing PDF with Google Document AI...")
        try:
            from docai_service import process_pdf_to_excel_docai
            download_url, pages_processed = await process_pdf_to_excel_docai(file_content, file.filename)
        except ImportError as e:
            logger.error(f"Failed to import docai_service: {e}")
            raise HTTPException(
                status_code=500,
                detail="Document AI service not available. Please check dependencies."
            )
        
        logger.info(f"PDF processed. Pages: {pages_processed}")
        
        # Step 5: Check credits (after processing to know exact page count)
        if not check_sufficient_credits(user_id, pages_processed):
            return JSONResponse(
                status_code=402,
                content={
                    "insufficient_credits": True,
                    "message": f"Insufficient credits. Need {pages_processed} credits, have {get_credits(user_id)}",
                    "required": pages_processed,
                    "available": get_credits(user_id)
                }
            )
        
        # Step 6: Deduct credits (only after successful conversion)
        deduct_credits(user_id, pages_processed)
        credits_left = get_credits(user_id)
        logger.info(f"Credits deducted: {pages_processed}, remaining: {credits_left}")
        
        # Step 7: Return success response
        return {
            "status": "success",
            "engine": "docai",
            "downloadUrl": download_url,
            "pagesProcessed": pages_processed,
            "creditsLeft": credits_left
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )


# Multi-processor routes (temporarily disabled until import issue is resolved)
# TODO: Re-enable after fixing docai_multi_processor import issues
"""
try:
    _lazy_import_multi_processor()
    # Test if import worked
    if _get_available_processors and callable(_get_available_processors):
        @app.get("/api/docai/processors")
        async def get_processors():
            """
            Get list of available Document AI processors.
            """
            return {
                "success": True,
                "processors": get_available_processors(),
                "processor_map": {
                    ptype: get_processor_id(ptype) 
                    for ptype in get_available_processors()
                }
            }

        @app.post("/api/docai/process/{processor_type}")
        async def process_with_docai(
    processor_type: str,
    request: Request,
    file: UploadFile = File(...)
):
    """
    Process PDF with specified Document AI processor type.
    
    Supported types:
    - form-parser-docai
    - layout-parser-docai
    - bank-docai
    - expense-docai
    - identity-docai
    - pay-slip-docai
    - utility-docai
    - w2-docai
    - w9-docai
    - pdf-to-excel-docai (default)
    """
    try:
        # Step 1: Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f}MB limit"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        logger.info(f"Received PDF file for {processor_type}: {file.filename}, size: {file_size} bytes")
        
        # Step 2: Validate processor type
        processor_id = get_processor_id(processor_type)
        if not processor_id:
            available = get_available_processors()
            raise HTTPException(
                status_code=400,
                detail=f"Invalid processor type: {processor_type}. Available: {', '.join(available)}"
            )
        
        # Step 3: Get user ID
        user_id = get_user_id(request)
        logger.info(f"Processing {processor_type} request for user: {user_id}")
        
        # Step 4: Process PDF with Document AI
        logger.info(f"Processing PDF with {processor_type}...")
        download_url, pages_processed, tables_found, extracted_data = await process_pdf_with_processor(
            file_content, file.filename, processor_type
        )
        
        logger.info(f"PDF processed. Pages: {pages_processed}, Tables: {tables_found}")
        
        # Step 5: Check credits
        if not check_sufficient_credits(user_id, pages_processed):
            return JSONResponse(
                status_code=402,
                content={
                    "insufficient_credits": True,
                    "message": f"Insufficient credits. Need {pages_processed} credits, have {get_credits(user_id)}",
                    "required": pages_processed,
                    "available": get_credits(user_id)
                }
            )
        
        # Step 6: Deduct credits (only after successful conversion)
        deduct_credits(user_id, pages_processed)
        credits_left = get_credits(user_id)
        logger.info(f"Credits deducted: {pages_processed}, remaining: {credits_left}")
        
        # Step 7: Return success response
        return {
            "success": True,
            "engine": "docai",
            "processor_type": processor_type,
            "downloadUrl": download_url,
            "pagesConverted": pages_processed,
            "creditsLeft": credits_left,
            "tablesFound": tables_found,
            "entitiesFound": len(extracted_data.get('entities', [])),
            "filename": f"{file.filename.replace('.pdf', '').replace('.PDF', '')}_{processor_type}.xlsx"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Value error in {processor_type}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in {processor_type}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Document AI processing failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
