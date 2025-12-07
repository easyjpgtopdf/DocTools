import io
import logging
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
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
    add_text_to_page,
    replace_text_simple,
    delete_text_by_bbox,
    search_text,
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

    png = render_page_to_png(pdf_bytes, req.page_number, req.zoom)
    return StreamingResponse(io.BytesIO(png), media_type="image/png")


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
    )
    update_pdf_bytes(req.session_id, updated)

    return {"status": "ok"}


@app.post("/text/edit")
async def edit_text(req: EditTextRequest):
    try:
        pdf_bytes = get_pdf_bytes(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    updated = replace_text_simple(
        pdf_bytes,
        page_number=req.page_number,
        old_text=req.old_text,
        new_text=req.new_text,
        max_replacements=req.max_replacements,
    )
    update_pdf_bytes(req.session_id, updated)
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

    png = render_page_to_png(pdf_bytes, req.page_number, zoom=1.5)
    ocr_result = run_ocr_on_image_bytes(png, lang=req.lang)
    return {"page": req.page_number, "results": ocr_result}


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

