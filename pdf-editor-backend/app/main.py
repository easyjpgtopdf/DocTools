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

