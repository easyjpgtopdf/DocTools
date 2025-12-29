"""
FastAPI backend for PDF to Excel conversion.
Supports both AWS Textract (fallback) and Google Document AI.
"""

import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Tuple
import traceback

from credit import get_user_id, get_credits, deduct_credits, check_sufficient_credits, get_credit_info
from pricing import MIN_PREMIUM_CREDITS, get_credit_cost_for_document_type, can_access_premium, get_pricing_info
from storage_gcs import upload_excel_to_gcs, upload_file_to_gcs
from id_card_detector import detect_id_card
# Lazy import for docai_service to avoid startup errors
# from docai_service import process_pdf_to_excel_docai
# NEW FREE Engine (completely isolated)
from free_pdf_to_excel.free_engine_controller import process_pdf_to_excel_free
from free_pdf_to_excel.free_limits import generate_free_key
from free_pdf_to_excel.free_response_builder import build_success_response, build_error_response

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
    allow_origins=[
        "https://easyjpgtopdf.com",
        "https://www.easyjpgtopdf.com",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "*"  # Fallback for development
    ],
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
    pricing_info = get_pricing_info()
    return {
        "status": "ok",
        "service": "PDF to Excel Converter API",
        "version": "3.0.0",
        "providers": ["AWS Textract (optional)", "Google Document AI"],
        "endpoints": {
            "textract": "/api/pdf-to-excel (AWS Textract - requires S3_BUCKET)",
            "docai": "/api/pdf-to-excel-docai (Google Document AI - default)"
        },
        "pricing": pricing_info
    }

@app.get("/api/pricing")
async def pricing_endpoint():
    """Get pricing information for PDF to Excel conversion."""
    return JSONResponse(content=get_pricing_info())


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/credits")
async def get_credits_endpoint(request: Request):
    """
    Get current credit balance for the user.
    Includes debug info to help diagnose credit issues.
    """
    try:
        user_id = get_user_id(request)
        logger.info(f"Credit check request for user_id: {user_id}")
        
        credit_info = get_credit_info(user_id)
        current_credits = credit_info.get("credits", 0)
        
        # Log detailed info for debugging
        logger.info(f"User {user_id} credits: {current_credits}")
        logger.info(f"Credit info: {credit_info}")
        
        return {
            "success": True,
            "credits": current_credits,
            "created_at": credit_info.get("created_at"),
            "totalCreditsEarned": credit_info.get("totalCreditsEarned", 0),
            "totalCreditsUsed": credit_info.get("totalCreditsUsed", 0),
            "user_id": user_id,  # Include user_id in response for debugging
            "debug": {
                "firebase_available": hasattr(credit_info, "error") == False,
                "has_error": "error" in credit_info
            }
        }
    except Exception as e:
        logger.error(f"Error getting credits: {str(e)}")
        logger.error(traceback.format_exc())
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
        
        # Step 2: Detect if this is an ID card (before Excel processing)
        # If ID card detected, route to ID card endpoint instead
        try:
            detection_result = detect_id_card(file_content, pdf_metadata=None, text_blocks=None)
            if detection_result.get("document_type") == "ID_CARD" and detection_result.get("confidence", 0) >= 50:
                logger.info(f"ID Card detected (confidence: {detection_result.get('confidence')}). Routing to ID card endpoint.")
                # Return response indicating ID card should use different endpoint
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "ID card detected",
                        "message": "ID cards do not contain tables and cannot be converted to Excel format. Please use the ID card processing endpoint.",
                        "document_type": "ID_CARD",
                        "suggested_endpoint": "/api/id-card-process",
                        "confidence": detection_result.get("confidence")
                    }
                )
        except Exception as e:
            logger.warning(f"ID card detection failed (continuing with Excel conversion): {e}")
            # Continue with normal Excel conversion if detection fails
        
        # Step 3: Get user ID
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
        # Only block if header explicitly says 'free'
        # If header is missing or empty, check credits instead (allow premium users)
        user_type = request.headers.get("X-User-Type", "").strip().lower()
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
        # If user_type is empty or not 'free', continue to credit check (premium users allowed)
        
        # Step 2.5: Extract premium mode preference from form data
        user_wants_premium = False
        try:
            form_data = await request.form()
            if 'user_wants_premium' in form_data:
                user_wants_premium_str = form_data.get('user_wants_premium', 'false')
                user_wants_premium = str(user_wants_premium_str).lower() == 'true'
                logger.info(f"User explicitly {'enabled' if user_wants_premium else 'disabled'} premium mode (Adobe fallback)")
        except Exception as form_err:
            logger.warning(f"Could not extract premium preference from form: {form_err}")
            user_wants_premium = False
        
        # Step 3: Check minimum credits (30 required for premium - UPDATED)
        # TEMPORARY TESTING BYPASS
        TESTING_UID = "NLhUrh6ZurQInLRV875Ktxw9rDn2"
        if user_id == TESTING_UID:
            logger.warning(f"🧪 TESTING MODE: Bypassing credit check for {user_id} in main.py")
            current_credits = 1000  # Bypass credit check
        else:
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
        download_url = None
        pages_processed = 0
        conversion_successful = False
        
        try:
            from docai_service import process_pdf_to_excel_docai
            download_url, pages_processed, unified_layouts, pages_metadata = await process_pdf_to_excel_docai(
                file_content, 
                file.filename,
                user_wants_premium=user_wants_premium
            )
            conversion_successful = True
            logger.info(f"PDF processed successfully. Pages: {pages_processed}, Download URL: {download_url[:50]}...")
            logger.critical(f"BILLING: Received {len(pages_metadata)} pages metadata from docai_service")
        except ImportError as e:
            logger.error(f"Failed to import docai_service: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Document AI service import failed: {str(e)}. Please check google-cloud-documentai installation."
            )
        except ValueError as e:
            # Layout reconstruction failed - don't deduct credits
            logger.error(f"Premium conversion failed (layout reconstruction): {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Premium conversion failed",
                    "message": str(e),
                    "credits_not_deducted": True
                }
            )
        except Exception as e:
            # Other processing errors - don't deduct credits
            logger.error(f"Document AI processing error: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Document AI processing failed",
                    "message": str(e),
                    "credits_not_deducted": True
                }
            )
        
        # Step 6: Only deduct credits if conversion was successful
        if not conversion_successful or not download_url:
            logger.error("Conversion failed - credits will not be deducted")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Conversion failed",
                    "message": "Excel generation failed. Credits not deducted.",
                    "credits_not_deducted": True
                }
            )
        
        # Step 7: Calculate credit cost based on ACTUAL ENGINE USED
        # Extract layout_source early for credit calculation
        # CRITICAL: Force flush logs to ensure visibility
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        
        logger.critical("=" * 80)
        logger.critical("STEP 7: CREDIT CALCULATION - STARTING")
        logger.critical(f"pages_processed from docai_service: {pages_processed}")
        logger.critical(f"unified_layouts available: {unified_layouts is not None}")
        logger.critical(f"unified_layouts count: {len(unified_layouts) if unified_layouts else 0}")
        logger.critical("=" * 80)
        sys.stdout.flush()
        
        layout_source = "docai"  # Default
        if unified_layouts and len(unified_layouts) > 0:
            first_layout = unified_layouts[0]
            if hasattr(first_layout, 'metadata') and first_layout.metadata:
                layout_source = first_layout.metadata.get('layout_source', 'docai')
                logger.info(f"✅ Extracted layout_source from metadata: '{layout_source}'")
            else:
                logger.warning(f"⚠️ First layout has no metadata, using default: 'docai'")
        else:
            logger.warning(f"⚠️ No unified_layouts available, using default: 'docai'")
        
        logger.info(f"✅ Final layout_source for credit calculation: '{layout_source}'")
        logger.info("=" * 80)
        
        # STEP-12: Use centralized credit calculator with per-page slab pricing (ENGINE-BASED)
        import sys
        from billing.credit_calculator import CreditCalculator
        
        # CRITICAL: Ensure pages_metadata exists and is valid
        if 'pages_metadata' not in locals() or not pages_metadata:
            logger.warning("⚠️ STEP-12: pages_metadata not provided - building from unified_layouts")
            pages_metadata = []
            for idx, layout in enumerate(unified_layouts):
                page_num = layout.metadata.get('page_number', idx + 1)
                engine = layout.metadata.get('engine_used', layout.metadata.get('layout_source', 'docai'))
                pages_metadata.append({'page': page_num, 'engine': engine})
                logger.critical(f"   Built metadata: Page {page_num} → engine={engine}")
        
        # CRITICAL: Log pages_metadata before calculation
        logger.critical("=" * 80)
        logger.critical("STEP-12: CREDIT CALCULATION - INPUT")
        logger.critical(f"pages_metadata count: {len(pages_metadata)}")
        for pm in pages_metadata:
            logger.critical(f"   Page {pm.get('page')}: engine={pm.get('engine')}")
        logger.critical("=" * 80)
        
        # Calculate credits using centralized calculator (ENGINE-BASED, not execution_mode)
        billing_breakdown = CreditCalculator.calculate_credits(pages_metadata)
        total_credits_required = billing_breakdown.total_credits
        credit_per_page = total_credits_required / pages_processed if pages_processed > 0 else 0.0
        
        # CRITICAL: Log calculation result
        logger.critical("=" * 80)
        logger.critical("STEP-12: CREDIT CALCULATION - RESULT")
        logger.critical(f"Total credits required: {total_credits_required}")
        logger.critical(f"Credit per page: {credit_per_page:.2f}")
        logger.critical(f"Engine summary: {billing_breakdown.engine_summary}")
        logger.critical("=" * 80)
        
        # CRITICAL: Force flush logs
        sys.stdout.flush()
        sys.stderr.flush()
        
        # CRITICAL: Force flush logs
        sys.stdout.flush()
        sys.stderr.flush()
        
        logger.critical("=" * 80)
        logger.critical("CREDIT CALCULATION - RESULT")
        logger.critical(f"Pages processed: {pages_processed}")
        logger.critical(f"Engine used: {layout_source}")
        logger.critical(f"Average cost: {credit_per_page:.2f} credits/page")
        logger.critical(f"Total cost: {total_credits_required} credits")
        logger.info(f"Formula applied: {'Adobe' if layout_source == 'adobe' else 'DocAI'} pricing")
        if layout_source == 'adobe':
            if pages_processed <= 10:
                logger.info(f"  → {pages_processed} pages × 15 credits/page = {total_credits_required} credits")
            else:
                logger.info(f"  → (10 pages × 15) + ({pages_processed - 10} pages × 5) = {total_credits_required} credits")
        else:
            if pages_processed <= 10:
                logger.info(f"  → {pages_processed} pages × 5 credits/page = {total_credits_required} credits")
            else:
                logger.info(f"  → (10 pages × 5) + ({pages_processed - 10} pages × 2) = {total_credits_required} credits")
        logger.info("=" * 80)
        
        # Step 8: Check credits (after processing to know exact page count and cost)
        # Note: Minimum 30 credits already checked, but verify again for actual cost
        current_credits = get_credits(user_id)
        if current_credits < total_credits_required:
            logger.warning(f"Insufficient credits after processing: need {total_credits_required}, have {current_credits}")
            return JSONResponse(
                status_code=402,
                content={
                    "insufficient_credits": True,
                    "message": f"Insufficient credits. Need {total_credits_required} credits (avg {credit_per_page:.2f}/page × {pages_processed} pages using {layout_source}), have {current_credits}",
                    "required": total_credits_required,
                    "available": current_credits,
                    "credit_per_page": credit_per_page,
                    "pages": pages_processed,
                    "engine_used": layout_source,
                    "credits_not_deducted": True
                }
            )
        
        # Step 9: Deduct credits (only if conversion was successful)
        # CRITICAL DEBUG: Log exact amount being deducted
        credits_to_deduct = int(total_credits_required)
        logger.info("=" * 80)
        logger.info("CREDIT DEDUCTION - CALLING deduct_credits()")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Amount to deduct: {credits_to_deduct} credits")
        logger.info(f"Type: {type(credits_to_deduct)}")
        logger.info(f"Calculation: {pages_processed} pages × {credit_per_page:.2f} credits/page = {total_credits_required} credits")
        logger.info("=" * 80)
        
        if not deduct_credits(user_id, credits_to_deduct):
            logger.error(f"❌ FAILED to deduct {credits_to_deduct} credits from user {user_id}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Failed to deduct credits",
                    "message": "Conversion succeeded but credit deduction failed. Please contact support.",
                    "downloadUrl": download_url  # Still provide download URL
                }
            )
        
        logger.info(f"✅ SUCCESS: Deducted {credits_to_deduct} credits from user {user_id}")
        
        # Get remaining credits after deduction
        remaining_credits = get_credits(user_id)
        
        # ENTERPRISE RESPONSE: Extract mode, confidence, message, guardrails from unified_layouts metadata
        # unified_layouts are created in docai_service and have metadata set by layout_decision_engine
        execution_mode = None
        routing_confidence = 0.5
        routing_reason = ""
        # layout_source already extracted earlier for credit calculation (do not re-extract)
        adobe_guardrails = {}
        estimated_adobe_pages = 0
        
        try:
            # Extract from first layout metadata (all pages have same mode)
            # unified_layouts is available in this scope from docai_service processing
            if 'unified_layouts' in locals() and unified_layouts and len(unified_layouts) > 0:
                first_layout = unified_layouts[0]
                if hasattr(first_layout, 'metadata') and first_layout.metadata:
                    execution_mode = first_layout.metadata.get('execution_mode')
                    routing_confidence = first_layout.metadata.get('routing_confidence', 0.5)
                    routing_reason = first_layout.metadata.get('routing_reason', '')
                    # Get additional Adobe-related metadata
                    adobe_guardrails = first_layout.metadata.get('adobe_guardrails', {})
                    estimated_adobe_pages = first_layout.metadata.get('estimated_adobe_pages', 0)
                    logger.info(f"Extracted metadata: mode={execution_mode}, confidence={routing_confidence:.2f}, reason={routing_reason}, source={layout_source}")
                    if layout_source == 'adobe':
                        logger.info(f"Adobe guardrails: {adobe_guardrails}")
        except Exception as e:
            logger.warning(f"Could not extract mode/confidence from layouts: {e}")
        
        # =====================================================================
        # STEP 10: ENTERPRISE QA VALIDATION (NEW)
        # =====================================================================
        qa_result = None
        try:
            from premium_layout.qa_validator import get_qa_validator
            from feature_flags import get_feature_flags
            
            flags = get_feature_flags()
            
            if flags.QA_VALIDATION_ENABLED:
                qa_validator = get_qa_validator()
                qa_result = qa_validator.validate_conversion(
                    document_name=file.filename,
                    layout_source=layout_source,
                    pages_processed=pages_processed,
                    routing_confidence=routing_confidence,
                    unified_layouts=unified_layouts,
                    adobe_guardrails=adobe_guardrails,
                    user_wants_premium=user_wants_premium
                )
                
                # Check if QA strict mode is enabled and validation failed
                if flags.QA_STRICT_MODE and qa_result.qa_status == "FAIL":
                    logger.error(f"QA STRICT MODE: Blocking conversion due to QA FAIL status")
                    logger.error(f"QA Errors: {'; '.join(qa_result.errors)}")
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error": "QA Validation Failed",
                            "message": f"Conversion blocked by QA validation: {'; '.join(qa_result.errors)}",
                            "qa_status": "FAIL",
                            "qa_errors": qa_result.errors
                        }
                    )
                
                logger.info(f"QA Validation: {qa_result.qa_status} ({len(qa_result.warnings)} warnings, {len(qa_result.errors)} errors)")
        except ImportError as import_err:
            logger.warning(f"QA validation module not available: {import_err}")
        except Exception as qa_err:
            logger.error(f"QA validation failed (non-critical): {qa_err}")
        
        # Build response with QA metadata and billing breakdown (STEP-9)
        response_content = {
            "status": "success",
            "engine": "docai",
            "downloadUrl": download_url,
            "download_url": download_url,  # Also include snake_case for consistency
            "pagesProcessed": pages_processed,
            "creditsLeft": remaining_credits,
            "creditsDeducted": int(total_credits_required),
            "creditPerPage": credit_per_page,
            # ENTERPRISE RESPONSE: Mode, confidence, message, layout source
            "mode": execution_mode or "unknown",
            "execution_mode": execution_mode or "unknown",
            "confidence": routing_confidence,
            "routing_confidence": routing_confidence,
            "message": routing_reason,
            "routing_reason": routing_reason,
            "layout_source": layout_source,  # "docai" or "adobe"
            # STEP-9: Per-page pricing breakdown
            "pricing": {
                "type": "per_page_slab",
                "cost_per_page": credit_per_page,
                "total_cost": int(total_credits_required),
                "pages": pages_processed,
                "engine": layout_source
            },
            "pricing_breakdown": {
                "total_credits": billing_breakdown.total_credits,
                "engine_summary": billing_breakdown.engine_summary,
                "pricing_applied": billing_breakdown.pricing_applied,
                "pages_metadata": [
                    {
                        "page": pm.page_number,
                        "engine": pm.engine,
                        "credits": pm.credits,
                        "slab": pm.slab
                    }
                    for pm in billing_breakdown.pages_metadata
                ]
            },
            "engine_usage_summary": {
                engine: {
                    "page_count": summary["page_count"],
                    "total_credits": summary["total_credits"],
                    "slab_1_5_pages": summary["slab_1_5_count"],
                    "slab_6_plus_pages": summary["slab_6_plus_count"]
                }
                for engine, summary in billing_breakdown.engine_summary.items()
            },
            # ADOBE GUARDRAILS METADATA (if Adobe was used)
            "adobe_guardrails": adobe_guardrails if layout_source == 'adobe' else None,
            "estimated_adobe_pages": estimated_adobe_pages if layout_source == 'adobe' else 0,
            "user_requested_premium": user_wants_premium
        }
        
        # Add QA metadata if validation was performed
        if qa_result:
            response_content["qa_status"] = qa_result.qa_status
            response_content["qa_warnings"] = qa_result.warnings
            response_content["qa_errors"] = qa_result.errors
            response_content["qa_metadata"] = qa_result.metadata
            response_content["engine_chain"] = qa_result.engine_chain
            response_content["billed_pages"] = qa_result.billed_pages
        
        return JSONResponse(
            status_code=200,
            content=response_content
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


# ID Card Processing Endpoint
@app.post("/api/id-card-process")
async def id_card_process_endpoint(request: Request, file: UploadFile = File(...)):
    """
    Process ID card PDFs (both FREE and PREMIUM users).
    
    FREE users: Text extraction + CSV template (zero cost)
    PREMIUM users: Structured extraction using identity-docai (credit-based)
    
    ID cards are detected and routed here from Excel conversion endpoints.
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
        
        # Step 2: Get user ID and type
        user_id = get_user_id(request)
        user_type = request.headers.get("X-User-Type", "").lower()
        current_credits = get_credits(user_id)
        
        # Step 3: Detect ID card (confirm)
        detection_result = detect_id_card(file_content, pdf_metadata=None, text_blocks=None)
        if detection_result.get("document_type") != "ID_CARD":
            logger.warning(f"Document may not be an ID card (confidence: {detection_result.get('confidence')})")
        
        # Step 4: Route based on user type
        if user_type == "free" or not can_access_premium(current_credits):
            # FREE USER FLOW: Text extraction + CSV template (zero cost)
            logger.info(f"Processing ID card for FREE user: {user_id}")
            from id_card_service import process_id_card_free
            
            csv_template_url, text_result = process_id_card_free(file_content, file.filename)
            
            return {
                "status": "success",
                "user_type": "free",
                "document_type": "ID_CARD",
                "csv_template_url": csv_template_url,
                "text_extraction": {
                    "text": text_result.get("text", ""),
                    "page_count": text_result.get("page_count", 0),
                    "pages": text_result.get("pages", [])
                },
                "message": "ID cards do not contain tables. For structured data extraction, upgrade to Premium."
            }
        else:
            # PREMIUM USER FLOW: identity-docai processor
            logger.info(f"Processing ID card for PREMIUM user: {user_id}")
            
            # Check minimum credits (30 required)
            if not can_access_premium(current_credits):
                return JSONResponse(
                    status_code=402,
                    content={
                        "insufficient_credits": True,
                        "message": f"Premium ID card processing requires at least {MIN_PREMIUM_CREDITS} credits. You have {current_credits}.",
                        "required": MIN_PREMIUM_CREDITS,
                        "available": current_credits
                    }
                )
            
            # Use identity-docai processor
            _lazy_import_multi_processor()
            if _process_pdf_with_processor_func is None:
                raise HTTPException(
                    status_code=500,
                    detail="Multi-processor module not available"
                )
            
            # Calculate required credits (6 credits/page for ID cards)
            credit_per_page = get_credit_cost_for_document_type(document_type="id_card")
            # Estimate page count (will be confirmed after processing)
            estimated_pages = detection_result.get("page_count", 1)
            estimated_credits = estimated_pages * credit_per_page
            
            if current_credits < estimated_credits:
                return JSONResponse(
                    status_code=402,
                    content={
                        "insufficient_credits": True,
                        "message": f"Insufficient credits. Estimated {estimated_credits:.1f} credits needed ({estimated_pages} pages × {credit_per_page:.1f}/page), have {current_credits}",
                        "required": estimated_credits,
                        "available": current_credits
                    }
                )
            
            # Process with identity-docai
            download_url, pages_processed, tables_found, extracted_data = await process_pdf_with_processor(
                file_content,
                file.filename,
                "identity-docai"
            )
            
            # Calculate actual credits required
            total_credits_required = pages_processed * credit_per_page
            
            # Check credits again after processing
            current_credits = get_credits(user_id)
            if current_credits < total_credits_required:
                return JSONResponse(
                    status_code=402,
                    content={
                        "insufficient_credits": True,
                        "message": f"Insufficient credits. Need {total_credits_required:.1f} credits ({pages_processed} pages × {credit_per_page:.1f}/page), have {current_credits}",
                        "required": total_credits_required,
                        "available": current_credits
                    }
                )
            
            # Deduct credits
            credits_to_deduct = int(total_credits_required)
            if not deduct_credits(user_id, credits_to_deduct):
                return JSONResponse(
                    status_code=402,
                    content={
                        "insufficient_credits": True,
                        "message": f"Failed to deduct credits. Need {total_credits_required:.1f} credits, have {current_credits}",
                        "required": total_credits_required,
                        "available": current_credits
                    }
                )
            
            credits_left = get_credits(user_id)
            logger.info(f"Credits deducted: {credits_to_deduct} (ID card, {credit_per_page:.1f}/page), remaining: {credits_left}")
            
            return {
                "status": "success",
                "user_type": "premium",
                "document_type": "ID_CARD",
                "downloadUrl": download_url,
                "pagesProcessed": pages_processed,
                "creditsDeducted": credits_to_deduct,
                "creditsLeft": credits_left,
                "costPerPage": credit_per_page,
                "extractedData": extracted_data
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ID card processing error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"ID card processing failed: {str(e)}"
        )


@app.post("/api/pdf-to-excel-free-server")
async def pdf_to_excel_free_server_endpoint(
    request: Request,
    file: UploadFile = File(...),
    fingerprint: Optional[str] = Form(None)
):
    """
    FREE Server-Side PDF to Excel Conversion (NEW ENGINE v1).
    Completely isolated from Premium/Document AI.
    CPU-only processing, NO OCR, NO GPU.
    
    Features:
    - Multi-page support (all pages converted to separate sheets)
    - Merged cells detection and preservation
    - Font preservation
    - Image/logo extraction
    - Form document handling (resumes, letters, ID cards)
    - LibreOffice integration with Python fallback
    
    Limits (hidden):
    - Max 5 PDFs per device/IP per 24 hours
    - Max file size: 2 MB
    - All pages processed (separate sheets)
    """
    try:
        # Get client info for abuse control
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        # Get fingerprint from FormData or header
        if not fingerprint:
            fingerprint = request.headers.get("x-fingerprint", "")
        
        # Generate free key
        free_key = generate_free_key(ip_address, user_agent, fingerprint)
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        logger.info(f"FREE v1 engine request: {file.filename}, size: {file_size} bytes, key: {free_key[:8]}")
        
        # Process PDF to Excel using NEW FREE engine (completely isolated)
        excel_path, pages_processed, confidence, error_message = process_pdf_to_excel_free(
            file_content,
            file.filename,
            free_key,
            ip_address
        )
        
        if error_message:
            # Check if upgrade is required (ONLY for specific cases)
            # Only mark as upgrade_required for:
            # 1. Daily limit reached messages
            # 2. Scanned PDF messages (explicitly asking for upgrade)
            # DO NOT mark for: "File too large", "No text found", "PDF has no pages", etc.
            upgrade_required = (
                "Daily limit" in error_message or
                ("scanned" in error_message.lower() and "Upgrade to Pro" in error_message) or
                ("scanned" in error_message.lower() and "OCR" in error_message)
            )
            
            if upgrade_required:
                return JSONResponse(
                    status_code=403,
                    content=build_error_response(
                        error_message,
                        upgrade_required=True,
                        fallback_available=False
                    )
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content=build_error_response(
                        error_message,
                        upgrade_required=False,
                        fallback_available=False  # Set to False as no fallback available for free tier
                    )
                )
        
        if not excel_path or pages_processed == 0:
            return JSONResponse(
                status_code=400,
                content=build_error_response(
                    "Conversion failed. Try Premium for better accuracy.",
                    upgrade_required=False,
                    fallback_available=True
                )
            )
        
        # Read Excel file
        with open(excel_path, 'rb') as f:
            excel_content = f.read()
        
        # Clean up temp file
        try:
            os.unlink(excel_path)
        except:
            pass
        
        # Upload to GCS and get signed URL
        try:
            download_url = upload_file_to_gcs(
                excel_content,
                file.filename.replace('.pdf', '.xlsx'),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            method = "gcs"
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            # Return file directly if GCS fails
            import base64
            excel_b64 = base64.b64encode(excel_content).decode('utf-8')
            download_url = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_b64}"
            method = "direct_download"
        
        return JSONResponse(
            status_code=200,
            content=build_success_response(
                download_url,
                pages_processed,
                confidence,
                method
            )
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in FREE v1 server conversion endpoint: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content=build_error_response(
                f"Internal server error: {str(e)}",
                upgrade_required=False,
                fallback_available=True
            )
        )


# Debug endpoint for FREE limits (for troubleshooting)
from free_pdf_to_excel.free_limits_debug import get_usage_by_ip, reset_usage_for_ip, get_all_usage_stats

@app.get("/api/free-limits/debug")
async def debug_free_limits(
    request: Request,
    ip: Optional[str] = None
):
    """
    Debug endpoint to check FREE limits for an IP address.
    """
    try:
        ip_address = ip or (request.client.host if request.client else "unknown")
        user_agent = request.headers.get("user-agent", "")
        fingerprint = request.headers.get("x-fingerprint", "")
        
        usage_info = get_usage_by_ip(ip_address, user_agent, fingerprint)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "usage_info": usage_info
            }
        )
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
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
