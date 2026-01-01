import io
import logging
import os
import requests
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi import Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .models import (
    StartSessionResponse,
    RenderPageRequest,
    AddTextRequest,
    EditTextRequest,
    DeleteTextRequest,
    SearchRequest,
    OcrPageRequest,
    ExportRequest,
    ValidateRequest,
)
from .storage import create_session, get_pdf_bytes, update_pdf_bytes, session_exists
from .pdf_engine import (
    get_page_count,
    render_page_to_png,
    render_page_with_text_layer,
    add_text_to_page,
    replace_text_native,
    delete_text_by_bbox,
    search_text,
    load_document,
    apply_ocr_to_page,
)
from .ocr_engine import run_ocr_on_image_bytes

logger = logging.getLogger(__name__)

# Premium access constants
MIN_CREDITS_TO_ENTER = 30
CREDITS_PER_PAGE_ACTION = 6

app = FastAPI(title="PDF Native Editor Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "pdf-native-editor"}


# ============================================================================
# PREMIUM ACCESS & CREDIT MANAGEMENT
# ============================================================================

async def get_user_credit_info(user_id: str) -> dict:
    """
    Fetch user credit balance and premium status from API.
    Returns: {credits: int, unlimited: bool, isPremium: bool}
    """
    if not user_id:
        return {"credits": 0, "unlimited": False, "isPremium": False}
    
    try:
        api_base = os.environ.get('API_BASE_URL', 'https://easyjpgtopdf.com')
        response = requests.get(
            f"{api_base}/api/credits/balance",
            params={"userId": user_id},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "credits": data.get("credits", 0),
                "unlimited": data.get("unlimited", False),
                "isPremium": data.get("isPremium", False)
            }
    except Exception as e:
        logger.error(f"Error fetching user credits: {e}")
    
    # Default: no credits
    return {"credits": 0, "unlimited": False, "isPremium": False}


async def deduct_credits(user_id: str, amount: int, reason: str) -> bool:
    """
    Deduct credits from user account atomically.
    Returns True if deduction successful, False otherwise.
    """
    if not user_id:
        return False
    
    try:
        api_base = os.environ.get('API_BASE_URL', 'https://easyjpgtopdf.com')
        response = requests.post(
            f"{api_base}/api/credits/deduct",
            json={
                "userId": user_id,
                "amount": amount,
                "reason": reason,
                "metadata": {}
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error deducting credits: {e}")
        return False


async def requirePremiumAccess(user_id: Optional[str], required_credits: int = MIN_CREDITS_TO_ENTER):
    """
    Enforce premium access requirement.
    Raises HTTPException 403 if user doesn't have sufficient credits.
    """
    if not user_id:
        raise HTTPException(
            status_code=403,
            detail="User ID required. Please sign in to access PDF Editor."
        )
    
    credit_info = await get_user_credit_info(user_id)
    
    # Unlimited users bypass credit check
    if credit_info.get("unlimited", False):
        return
    
    # Check if user has sufficient credits
    available_credits = credit_info.get("credits", 0)
    if available_credits < required_credits:
        raise HTTPException(
            status_code=403,
            detail=f"Upgrade to Premium. Minimum {required_credits} credits required."
        )


@app.get("/user/credits")
async def get_user_credits(userId: Optional[str] = None):
    """
    Get user credit balance and premium status.
    Queries the main API for actual credit information.
    """
    return await get_user_credit_info(userId or "")


@app.get("/device/ip")
@app.get("/api/device/ip")
async def device_ip(request: Request):
    # Try multiple headers for real client IP
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    return {"ip": ip or "unknown"}


@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(
    file: UploadFile = File(...),
    userId: Optional[str] = None
):
    """
    Start a new PDF editing session.
    REQUIRES: userId and minimum 30 credits (premium access).
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # PREMIUM ACCESS ENFORCEMENT: Require userId and 30 credits
    if not userId:
        raise HTTPException(
            status_code=403,
            detail="User ID required. Please sign in to access PDF Editor."
        )
    
    # Check premium access (30 credits minimum)
    await requirePremiumAccess(userId, MIN_CREDITS_TO_ENTER)
    
    pdf_bytes = await file.read()
    session_id = create_session(pdf_bytes)
    pages = get_page_count(pdf_bytes)

    return StartSessionResponse(session_id=session_id, page_count=pages)


@app.post("/page/render")
async def render_page(req: RenderPageRequest):
    """
    Render PDF page as PNG with text layer.
    DEDUCTS: 6 credits per page (premium only).
    """
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # PREMIUM ACCESS: Deduct 6 credits per page
    if req.userId:
        credit_info = await get_user_credit_info(req.userId)
        if not credit_info.get("unlimited", False):
            # Check if user has sufficient credits
            if credit_info.get("credits", 0) < CREDITS_PER_PAGE_ACTION:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"Insufficient credits. {CREDITS_PER_PAGE_ACTION} credits required per page."
                )
            # Deduct credits atomically
            success = await deduct_credits(
                req.userId,
                CREDITS_PER_PAGE_ACTION,
                f"PDF page render (page {req.page_number})"
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to deduct credits. Please try again."
                )

    # Render PNG and extract text layer
    png_bytes, text_layer, page_width, page_height = render_page_with_text_layer(
        pdf_bytes, req.page_number, req.zoom
    )
    
    # Convert PNG to base64
    import base64
    png_base64 = base64.b64encode(png_bytes).decode('utf-8')
    
    # Return JSON with PNG and text layer
    return {
        "image": png_base64,
        "pageWidth": page_width,
        "pageHeight": page_height,
        "textLayer": text_layer
    }


@app.post("/text/add")
async def add_text(req: AddTextRequest):
    """
    Add new text to PDF page.
    DEDUCTS: 6 credits per page (premium only).
    """
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # PREMIUM ACCESS: Deduct 6 credits per page
    if req.userId:
        credit_info = await get_user_credit_info(req.userId)
        if not credit_info.get("unlimited", False):
            if credit_info.get("credits", 0) < CREDITS_PER_PAGE_ACTION:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"Insufficient credits. {CREDITS_PER_PAGE_ACTION} credits required per page."
                )
            success = await deduct_credits(
                req.userId,
                CREDITS_PER_PAGE_ACTION,
                f"PDF text add (page {req.page_number})"
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to deduct credits. Please try again."
                )

    # Normalize color
    color_hex = "#000000"
    if isinstance(req.color, str):
        color_hex = req.color
    elif isinstance(req.color, list) and len(req.color) >= 3:
        r, g, b = req.color[:3]
        color_hex = "#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b))

    updated = add_text_to_page(
        pdf_bytes,
        page_number=req.page_number,
        x=req.x,
        y=req.y,
        text=req.text,
        font_name=req.font_name,
        font_size=req.font_size,
        color_hex=color_hex,
        canvas_width=req.canvas_width,
        canvas_height=req.canvas_height,
    )
    update_pdf_bytes(req.session_id, updated)

    return {"status": "ok"}


@app.post("/text/edit")
async def edit_text(request: FastAPIRequest):
    """
    Edit text in PDF using bbox-based replacement (iLovePDF style).
    DEDUCTS: 6 credits per page (premium only).
    Uses Request instead of Pydantic model to avoid 422 validation errors.
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    
    # Parse request body manually
    session_id = body.get("session_id")
    page_number = int(body.get("page_number") or 1)
    old_text = (body.get("old_text") or "").strip()
    new_text = (body.get("new_text") or "").strip()
    max_replacements = int(body.get("max_replacements") or 1)
    userId = body.get("userId") or body.get("user_id")  # Support both formats
    bbox = body.get("bbox")  # Optional: bbox for precise editing
    
    # Validate required fields
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    if not old_text:
        raise HTTPException(status_code=400, detail="old_text is required")
    if not new_text:
        raise HTTPException(status_code=400, detail="new_text is required")
    
    # PREMIUM ACCESS: Deduct 6 credits per page
    if userId:
        credit_info = await get_user_credit_info(userId)
        if not credit_info.get("unlimited", False):
            if credit_info.get("credits", 0) < CREDITS_PER_PAGE_ACTION:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"Insufficient credits. {CREDITS_PER_PAGE_ACTION} credits required per page."
                )
            success = await deduct_credits(
                userId,
                CREDITS_PER_PAGE_ACTION,
                f"PDF text edit (page {page_number})"
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to deduct credits. Please try again."
                )
    
    # Get PDF bytes
    try:
        pdf_bytes = get_pdf_bytes(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # MANDATORY: ONLY bbox-based editing (iLovePDF/Acrobat style)
    # DO NOT use string replacement - PDF text is fragmented
    if not bbox or len(bbox) < 4:
        raise HTTPException(
            status_code=400,
            detail="bbox is required for text editing. PDF editing uses bbox-based replacement, not string matching."
        )
    
    # Bbox-based edit: delete old text by bbox, then add new text at same position
    # This EXACTLY matches iLovePDF/Acrobat behavior
    updated = delete_text_by_bbox(pdf_bytes, page_number, bbox)
    
    # Extract position and dimensions from bbox
    x0, y0, x1, y1 = bbox[:4]
    x = x0
    y = y1  # Use top of bbox for text baseline
    
    # Extract font info from request if provided, otherwise use defaults
    font_name = body.get("font_name") or body.get("fontName") or "Helvetica"
    font_size = body.get("font_size") or body.get("fontSize") or 12
    color_hex = body.get("color") or body.get("color_hex") or "#000000"
    
    # Add new text at the same bbox position
    updated = add_text_to_page(
        updated,
        page_number=page_number,
        x=x,
        y=y,
        text=new_text,
        font_name=font_name,
        font_size=font_size,
        color_hex=color_hex,
    )
    
    # Update PDF in storage
    update_pdf_bytes(session_id, updated)
    
    return {"status": "ok"}


@app.post("/text/delete")
async def delete_text(req: DeleteTextRequest):
    """
    Delete text from PDF by bbox (iLovePDF style).
    DEDUCTS: 6 credits per page (premium only).
    """
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    if not req.bbox:
        raise HTTPException(status_code=400, detail="bbox is required for delete")
    
    # PREMIUM ACCESS: Deduct 6 credits per page
    if req.userId:
        credit_info = await get_user_credit_info(req.userId)
        if not credit_info.get("unlimited", False):
            if credit_info.get("credits", 0) < CREDITS_PER_PAGE_ACTION:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"Insufficient credits. {CREDITS_PER_PAGE_ACTION} credits required per page."
                )
            success = await deduct_credits(
                req.userId,
                CREDITS_PER_PAGE_ACTION,
                f"PDF text delete (page {req.page_number})"
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to deduct credits. Please try again."
                )

    updated = delete_text_by_bbox(pdf_bytes, req.page_number, req.bbox)
    update_pdf_bytes(req.session_id, updated)
    return {"status": "ok"}


@app.post("/text/search")
async def search_text_route(req: SearchRequest):
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    results = search_text(pdf_bytes, req.query)
    return {"success": True, "matches": results, "count": len(results)}


@app.post("/ocr/page")
async def ocr_page(req: OcrPageRequest):
    """
    Run OCR on PDF page (returns OCR results, does not embed).
    DEDUCTS: 6 credits per page (premium only).
    """
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # PREMIUM ACCESS: Deduct 6 credits per page
    if req.userId:
        credit_info = await get_user_credit_info(req.userId)
        if not credit_info.get("unlimited", False):
            if credit_info.get("credits", 0) < CREDITS_PER_PAGE_ACTION:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"Insufficient credits. {CREDITS_PER_PAGE_ACTION} credits required per page."
                )
            success = await deduct_credits(
                req.userId,
                CREDITS_PER_PAGE_ACTION,
                f"PDF OCR (page {req.page_number})"
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to deduct credits. Please try again."
                )

    # Render page at higher zoom for better OCR accuracy
    png = render_page_to_png(pdf_bytes, req.page_number, zoom=2.0)
    ocr_result = run_ocr_on_image_bytes(png, lang=req.lang)
    
    # Convert OCR bbox from image pixel coordinates to PDF point coordinates
    # OCR image was rendered at 2.0x zoom, so we need to scale down
    doc = load_document(pdf_bytes)
    try:
        page = doc.load_page(req.page_number - 1)
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        # Get OCR image dimensions (rendered at 2.0x zoom)
        from PIL import Image
        import io
        ocr_img = Image.open(io.BytesIO(png))
        ocr_img_width = ocr_img.width
        ocr_img_height = ocr_img.height
        
        # Convert each OCR result bbox from image pixels to PDF points
        converted_results = []
        for item in ocr_result:
            bbox = item.get("bbox", [])
            if bbox and len(bbox) >= 4:
                # Handle both formats: [[x,y], [x,y], ...] or [x0, y0, x1, y1]
                if isinstance(bbox[0], (list, tuple)):
                    # Format: [[x0,y0], [x1,y1], [x2,y2], [x3,y3]]
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    x0_img = min(xs)
                    y0_img = min(ys)
                    x1_img = max(xs)
                    y1_img = max(ys)
                else:
                    # Format: [x0, y0, x1, y1]
                    x0_img, y0_img, x1_img, y1_img = bbox[:4]
                
                # Convert from OCR image pixel coordinates to PDF point coordinates
                # OCR image is at 2.0x zoom, so divide by 2.0
                x0_pdf = (x0_img / 2.0) * (page_width / (ocr_img_width / 2.0))
                y0_pdf = (y0_img / 2.0) * (page_height / (ocr_img_height / 2.0))
                x1_pdf = (x1_img / 2.0) * (page_width / (ocr_img_width / 2.0))
                y1_pdf = (y1_img / 2.0) * (page_height / (ocr_img_height / 2.0))
                
                # PDF coordinates: bottom-left origin, so y needs to be flipped
                y0_pdf_flipped = page_height - y1_pdf
                y1_pdf_flipped = page_height - y0_pdf
                
                converted_results.append({
                    "text": item.get("text", ""),
                    "bbox": [x0_pdf, y0_pdf_flipped, x1_pdf, y1_pdf_flipped],  # PDF coordinates
                    "confidence": item.get("confidence", 0.9)
                })
            else:
                converted_results.append(item)
        
        return {"page": req.page_number, "results": converted_results}
    finally:
        doc.close()


@app.post("/ocr/apply")
async def ocr_apply(req: OcrPageRequest):
    """
    Apply OCR to PDF page by embedding native text (not overlays).
    OCR is text-layer creation, not edit mode.
    Only applies if page has no existing text.
    DEDUCTS: 6 credits per page (premium only).
    """
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # PREMIUM ACCESS: Deduct 6 credits per page
    if req.userId:
        credit_info = await get_user_credit_info(req.userId)
        if not credit_info.get("unlimited", False):
            if credit_info.get("credits", 0) < CREDITS_PER_PAGE_ACTION:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"Insufficient credits. {CREDITS_PER_PAGE_ACTION} credits required per page."
                )
            success = await deduct_credits(
                req.userId,
                CREDITS_PER_PAGE_ACTION,
                f"PDF OCR apply (page {req.page_number})"
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to deduct credits. Please try again."
                )

    # First, run OCR to get text results
    png = render_page_to_png(pdf_bytes, req.page_number, zoom=2.0)
    ocr_result = run_ocr_on_image_bytes(png, lang=req.lang)
    
    # Convert OCR bbox from image pixel coordinates to PDF point coordinates
    doc = load_document(pdf_bytes)
    try:
        page = doc.load_page(req.page_number - 1)
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        # Get OCR image dimensions (rendered at 2.0x zoom)
        from PIL import Image
        import io
        ocr_img = Image.open(io.BytesIO(png))
        ocr_img_width = ocr_img.width
        ocr_img_height = ocr_img.height
        
        # Convert each OCR result bbox from image pixels to PDF points
        converted_results = []
        for item in ocr_result:
            bbox = item.get("bbox", [])
            if bbox and len(bbox) >= 4:
                # Handle both formats: [[x,y], [x,y], ...] or [x0, y0, x1, y1]
                if isinstance(bbox[0], (list, tuple)):
                    # Format: [[x0,y0], [x1,y1], [x2,y2], [x3,y3]]
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    x0_img = min(xs)
                    y0_img = min(ys)
                    x1_img = max(xs)
                    y1_img = max(ys)
                else:
                    # Format: [x0, y0, x1, y1]
                    x0_img, y0_img, x1_img, y1_img = bbox[:4]
                
                # Convert from OCR image pixel coordinates to PDF point coordinates
                # OCR image is at 2.0x zoom, so divide by 2.0
                x0_pdf = (x0_img / 2.0) * (page_width / (ocr_img_width / 2.0))
                y0_pdf = (y0_img / 2.0) * (page_height / (ocr_img_height / 2.0))
                x1_pdf = (x1_img / 2.0) * (page_width / (ocr_img_width / 2.0))
                y1_pdf = (y1_img / 2.0) * (page_height / (ocr_img_height / 2.0))
                
                # PDF coordinates: bottom-left origin, so y needs to be flipped
                y0_pdf_flipped = page_height - y1_pdf
                y1_pdf_flipped = page_height - y0_pdf
                
                converted_results.append({
                    "text": item.get("text", ""),
                    "bbox": [x0_pdf, y0_pdf_flipped, x1_pdf, y1_pdf_flipped],  # PDF coordinates
                    "confidence": item.get("confidence", 0.9)
                })
        
        # Apply OCR results to PDF
        updated = apply_ocr_to_page(pdf_bytes, req.page_number, converted_results)
        update_pdf_bytes(req.session_id, updated)
        
        return {"status": "ok", "page": req.page_number, "results_count": len(converted_results)}
    finally:
        doc.close()


@app.post("/export")
async def export_pdf(req: ExportRequest):
    if req.format != "pdf":
        raise HTTPException(status_code=400, detail="Only PDF export implemented in v1")

    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    filename = f"edited-document-{req.session_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/validate")
async def validate_pdf(req: ValidateRequest):
    """
    Validate that exported PDF contains expected text objects (not just images).
    Returns pass/fail result for debugging.
    """
    import base64
    
    try:
        # Decode base64 PDF
        if req.pdf_bytes.startswith("data:application/pdf;base64,"):
            pdf_bytes = base64.b64decode(req.pdf_bytes.split(",", 1)[1])
        else:
            pdf_bytes = base64.b64decode(req.pdf_bytes)
        
        # Search for each expected text
        validation_results = []
        all_found = True
        
        for expected_text in req.expected_texts:
            if not expected_text or not expected_text.strip():
                continue
                
            # Search for text in PDF
            matches = search_text(pdf_bytes, expected_text.strip())
            
            # Filter by page if specified
            if req.page_number:
                matches = [m for m in matches if m["page_number"] == req.page_number]
            
            found = len(matches) > 0
            all_found = all_found and found
            
            validation_results.append({
                "text": expected_text,
                "found": found,
                "match_count": len(matches),
                "matches": matches[:5] if matches else []  # Limit to first 5 matches
            })
        
        return {
            "success": True,
            "valid": all_found,
            "results": validation_results,
            "summary": {
                "total_expected": len(req.expected_texts),
                "total_found": sum(1 for r in validation_results if r["found"]),
                "all_found": all_found
            }
        }
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

