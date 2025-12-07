import io
from typing import Tuple, List

import fitz  # PyMuPDF
from PIL import Image


def load_document(pdf_bytes: bytes) -> fitz.Document:
    return fitz.open(stream=pdf_bytes, filetype="pdf")


def save_document(doc: fitz.Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def get_page_count(pdf_bytes: bytes) -> int:
    doc = load_document(pdf_bytes)
    try:
        return doc.page_count
    finally:
        doc.close()


def render_page_to_png(pdf_bytes: bytes, page_number: int, zoom: float = 1.0) -> bytes:
    doc = load_document(pdf_bytes)
    try:
        page = doc.load_page(page_number - 1)  # 1-based to 0-based
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    finally:
        doc.close()


def _hex_to_rgb01(color_hex: str) -> Tuple[float, float, float]:
    color_hex = color_hex.lstrip("#")
    if len(color_hex) != 6:
        return 0, 0, 0
    r = int(color_hex[0:2], 16) / 255
    g = int(color_hex[2:4], 16) / 255
    b = int(color_hex[4:6], 16) / 255
    return r, g, b


def add_text_to_page(
    pdf_bytes: bytes,
    page_number: int,
    x: float,
    y: float,
    text: str,
    font_name: str = "helv",
    font_size: float = 12,
    color_hex: str = "#000000",
    canvas_width: float = None,
    canvas_height: float = None,
) -> bytes:
    """
    Add text to PDF page using insert_textbox (native PDF editing).
    Converts canvas coordinates (top-left origin, pixel space) to PDF coordinates (bottom-left origin, point space).
    """
    doc = load_document(pdf_bytes)
    try:
        page = doc.load_page(page_number - 1)
        color = _hex_to_rgb01(color_hex)
        
        # Get PDF page dimensions in points
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height
        
        # Convert canvas coordinates to PDF coordinates
        if canvas_width and canvas_height:
            # Scale from canvas pixel space to PDF point space
            px = x * (page_width / canvas_width)
            py_canvas = y * (page_height / canvas_height)
            # Convert from canvas Y (top-left origin) to PDF Y (bottom-left origin)
            py = page_height - py_canvas
        else:
            # Assume coordinates are already in PDF space (backward compatibility)
            px = x
            py = page_height - y  # Simple flip if y was provided as canvas coordinate
        
        # Calculate textbox dimensions
        avg_char_width = font_size * 0.6
        text_width = len(text) * avg_char_width
        text_height = font_size * 1.2
        
        # Create textbox rect in PDF coordinates (bottom-left origin)
        textbox_rect = fitz.Rect(
            px,
            py - text_height,  # Bottom of textbox
            px + text_width,   # Right edge
            py                 # Top of textbox (baseline)
        )
        
        # Use insert_textbox for native PDF text insertion with font embedding
        page.insert_textbox(
            textbox_rect,
            text,
            fontname=font_name,
            fontsize=font_size,
            color=color,
            align=0,  # 0=left, 1=center, 2=right
        )

        return save_document(doc)
    finally:
        doc.close()


def replace_text_native(
    pdf_bytes: bytes,
    page_number: int,
    old_text: str,
    new_text: str,
    max_replacements: int = 1,
) -> bytes:
    """
    Native text replacement using PyMuPDF redaction API (Adobe Acrobat Pro style).
    Uses add_redact_annot() + apply_redactions() to remove old text,
    then insert_textbox() to add new text at the exact same position.
    NO overlays, NO white boxes - real native PDF editing.
    """
    doc = load_document(pdf_bytes)
    try:
        page = doc.load_page(page_number - 1)
        found = page.search_for(old_text)

        if not found:
            # No matches found, return original PDF
            return save_document(doc)

        replaced = 0
        redact_rects = []
        
        # Step 1: Add redaction annotations for all matches
        for rect in found:
            if replaced >= max_replacements:
                break
            
            # Add redaction annotation (this marks text for deletion)
            redact_annot = page.add_redact_annot(rect)
            redact_rects.append(rect)
            replaced += 1

        # Step 2: Apply redactions (this actually removes the text from PDF)
        if redact_rects:
            page.apply_redactions()

        # Step 3: Insert new text at the exact position of the first redacted rect
        if redact_rects and new_text:
            first_rect = redact_rects[0]
            
            # Estimate font size from the original text's bounding box height
            # Typical text height is about 1.2x font size, so font_size ≈ rect_height / 1.2
            rect_height = first_rect.height
            estimated_font_size = max(8, min(200, rect_height / 1.2))  # Clamp between 8 and 200
            
            # Calculate textbox dimensions
            avg_char_width = estimated_font_size * 0.6
            text_width = len(new_text) * avg_char_width
            text_height = estimated_font_size * 1.2
            
            # Use the redacted rect's position for new text
            # The rect is already in PDF coordinates (bottom-left origin)
            textbox_rect = fitz.Rect(
                first_rect.x0,
                first_rect.y0,
                first_rect.x0 + text_width,
                first_rect.y0 + text_height
            )
            
            # Insert new text using textbox (native PDF text with font embedding)
            page.insert_textbox(
                textbox_rect,
                new_text,
                fontname="helv",
                fontsize=estimated_font_size,
                color=(0, 0, 0),  # Black
                align=0,  # Left align
            )

        return save_document(doc)
    finally:
        doc.close()


def delete_text_by_bbox(pdf_bytes: bytes, page_number: int, bbox: List[float]) -> bytes:
    """
    Delete text from PDF using native redaction (Adobe Acrobat Pro style).
    Uses add_redact_annot() + apply_redactions() - NO draw_rect, NO white boxes.
    Real native PDF deletion that removes text from the PDF structure.
    """
    doc = load_document(pdf_bytes)
    try:
        page = doc.load_page(page_number - 1)
        rect = fitz.Rect(bbox)
        
        # Add redaction annotation to mark text for deletion
        page.add_redact_annot(rect)
        
        # Apply redactions to actually remove the text from PDF
        page.apply_redactions()
        
        return save_document(doc)
    finally:
        doc.close()


def search_text(pdf_bytes: bytes, query: str) -> list:
    doc = load_document(pdf_bytes)
    try:
        results = []
        for idx in range(doc.page_count):
            page = doc.load_page(idx)
            for rect in page.search_for(query):
                results.append(
                    {
                        "page_number": idx + 1,
                        "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                        "text": query,
                        "match_id": f"{idx}_{len(results)}",
                    }
                )
        return results
    finally:
        doc.close()

