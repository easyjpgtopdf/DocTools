from typing import Optional, Literal

from pydantic import BaseModel


class StartSessionResponse(BaseModel):
    session_id: str
    page_count: int


class RenderPageRequest(BaseModel):
    session_id: str
    page_number: int
    zoom: float = 1.0
    userId: Optional[str] = None


class AddTextRequest(BaseModel):
    session_id: str
    page_number: int
    x: float
    y: float
    text: str
    font_name: str = "Helvetica"
    font_size: float = 12
    color: str | list[float] | None = "#000000"  # hex string or [r,g,b]
    canvas_width: Optional[float] = None  # Canvas width in pixels for coordinate conversion
    canvas_height: Optional[float] = None  # Canvas height in pixels for coordinate conversion
    userId: Optional[str] = None


class EditTextRequest(BaseModel):
    session_id: str
    page_number: int
    old_text: str
    new_text: str
    max_replacements: int = 1


class DeleteTextRequest(BaseModel):
    session_id: str
    page_number: int
    bbox: Optional[list[float]] = None  # [x0, y0, x1, y1]
    userId: Optional[str] = None


class SearchRequest(BaseModel):
    session_id: str
    query: str


class OcrPageRequest(BaseModel):
    session_id: str
    page_number: int
    lang: str = "en"
    userId: Optional[str] = None


class ExportRequest(BaseModel):
    session_id: str
    format: Literal["pdf"] = "pdf"


class ValidateRequest(BaseModel):
    pdf_bytes: str  # base64 encoded PDF
    expected_texts: list[str]  # List of text strings that should exist in PDF
    page_number: Optional[int] = None  # Optional: validate on specific page only

