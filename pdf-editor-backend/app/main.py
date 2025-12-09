import io
import logging
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


@app.get("/user/credits")
async def get_user_credits(userId: Optional[str] = None):
    """
    Get user credit balance and premium status.
    For now, returns default values. In production, this should query a database.
    """
    if not userId:
        return {
            "credits": 0,
            "unlimited": False,
            "isPremium": False
        }
    
    # TODO: Query database for actual user credits
    # For now, return default values
    # In production, implement:
    # - Query user table for credits balance
    # - Check premium subscription status
    # - Return actual values
    
    return {
        "credits": 0,  # Placeholder - replace with actual query
        "unlimited": False,  # Placeholder - replace with actual query
        "isPremium": False  # Placeholder - replace with actual query
    }


@app.get("/device/ip")
@app.get("/api/device/ip")
async def device_ip(request: Request):
    # Try multiple headers for real client IP
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    return {"ip": ip or "unknown"}


@app.post("/session/start", response_model=StartSessionResponse)
async def start_session(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    pdf_bytes = await file.read()
    session_id = create_session(pdf_bytes)
    pages = get_page_count(pdf_bytes)

    return StartSessionResponse(session_id=session_id, page_count=pages)


@app.post("/page/render")
async def render_page(req: RenderPageRequest):
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

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
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

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
    Edit text in PDF using native replacement.
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
    
    # Validate required fields
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    if not old_text:
        raise HTTPException(status_code=400, detail="old_text is required")
    if not new_text:
        raise HTTPException(status_code=400, detail="new_text is required")
    
    # Get PDF bytes
    try:
        pdf_bytes = get_pdf_bytes(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Replace text using native replacement
    updated = replace_text_native(
        pdf_bytes,
        page_number=page_number,
        old_text=old_text,
        new_text=new_text,
        max_replacements=max_replacements,
    )
    
    # Update PDF in storage
    update_pdf_bytes(session_id, updated)
    
    return {"status": "ok"}


@app.post("/text/delete")
async def delete_text(req: DeleteTextRequest):
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    if not req.bbox:
        raise HTTPException(status_code=400, detail="bbox is required for delete")

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
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

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
    Apply OCR to PDF page by embedding invisible text (render_mode=3).
    Only applies if page has no existing text.
    """
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

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

