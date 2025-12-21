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
from pricing import MIN_PREMIUM_CREDITS, get_credit_cost_for_document_type, can_access_premium, get_pricing_info
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
    PREMIUM endpoint: Convert PDF to Excel using Google Document AI.
    
    SECURITY: This endpoint is PREMIUM ONLY. Free users are blocked.
    
    Workflow:
    1. Validate file
    2. Check user type (PREMIUM ONLY - FREE users blocked)
    3. Check credits (minimum 15 required)
    4. Check Document AI environment variables
    5. Process PDF with Document AI
    6. Get page count from Document AI response
    7. Check credits again
    8. Extract tables and create Excel
    9. Upload Excel to GCS
    10. Deduct credits
    11. Return download URL
    """
    try:
        # Step 1: Get user ID and check user type
        user_id = get_user_id(request)
        
        # Step 2: Check user type from header (FREE users blocked)
        user_type = request.headers.get("X-User-Type", "").lower()
        if user_type == "free":
            logger.warning(f"FREE user {user_id} attempted to access PREMIUM endpoint")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Premium feature only",
                    "message": "This feature requires a Premium subscription. Free users cannot use Document AI (OCR). Please use the basic conversion or upgrade to Premium.",
                    "user_type": "free",
                    "required": "premium"
                }
            )
        
        # Step 3: Check minimum credits (30 required for premium - UPDATED)
        current_credits = get_credits(user_id)
        if not can_access_premium(current_credits):
            logger.warning(f"User {user_id} has insufficient credits for premium: {current_credits} < {MIN_PREMIUM_CREDITS}")
            return JSONResponse(
                status_code=402,
                content={
                    "insufficient_credits": True,
                    "message": f"Premium conversion requires at least {MIN_PREMIUM_CREDITS} credits. You have {current_credits}. Please purchase credits to continue.",
                    "required": MIN_PREMIUM_CREDITS,
                    "available": current_credits,
                    "minimum_premium_credits": MIN_PREMIUM_CREDITS
                }
            )
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
        logger.info(f"Processing PREMIUM conversion for user: {user_id} (type: {user_type or 'premium'})")
        
        # Step 4: Check Document AI environment variables
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
        
        # Step 5: Process PDF with Document AI (lazy import)
        # This will return page count and create Excel
        logger.info("Processing PDF with Google Document AI...")
        try:
            from docai_service import process_pdf_to_excel_docai
            download_url, pages_processed = await process_pdf_to_excel_docai(file_content, file.filename)
        except ImportError as e:
            logger.error(f"Failed to import docai_service: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Document AI service import failed: {str(e)}. Please check google-cloud-documentai installation."
            )
        except Exception as e:
            logger.error(f"Document AI processing error: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Document AI processing failed: {str(e)}"
            )
        
        logger.info(f"PDF processed. Pages: {pages_processed}")
        
        # Step 6: Calculate credit cost based on document type
        # For now, use default pricing (2 credits/page for clean tables)
        # TODO: Detect document type and use appropriate pricing
        credit_per_page = get_credit_cost_for_document_type(
            document_type=None,  # Could be enhanced to detect from filename/content
            is_scanned=False     # Could be detected from analysis
        )
        total_credits_required = pages_processed * credit_per_page
        
        # Step 7: Check credits (after processing to know exact page count and cost)
        # Note: Minimum 30 credits already checked, but verify again for actual cost
        current_credits = get_credits(user_id)
        if current_credits < total_credits_required:
            return JSONResponse(
                status_code=402,
                content={
                    "insufficient_credits": True,
                    "message": f"Insufficient credits. Need {total_credits_required} credits ({credit_per_page} per page × {pages_processed} pages), have {current_credits}",
                    "required": total_credits_required,
                    "available": current_credits,
                    "credit_per_page": credit_per_page,
                    "pages": pages_processed
                }
            )
        
        # Step 8: Deduct credits (variable cost based on document type)
        if not deduct_credits(user_id, int(total_credits_required)):
            logger.error(f"Failed to deduct credits for user {user_id}")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to deduct credits"}
            )
        
        # Get remaining credits after deduction
        remaining_credits = get_credits(user_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "engine": "docai",
                "downloadUrl": download_url,
                "pagesProcessed": pages_processed,
                "creditsLeft": remaining_credits,
                "creditsDeducted": int(total_credits_required),
                "creditPerPage": credit_per_page,
                "pricing": {
                    "type": "per_page",
                    "cost_per_page": credit_per_page,
                    "total_cost": int(total_credits_required),
                    "pages": pages_processed
                }
            }
        )
        
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
# Routes are disabled to prevent startup errors
# To enable: Uncomment the code in docai_multi_processor.py and re-enable routes here


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
