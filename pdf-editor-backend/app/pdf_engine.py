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
) -> bytes:
    doc = load_document(pdf_bytes)
    try:
        page = doc.load_page(page_number - 1)
        color = _hex_to_rgb01(color_hex)

        page.insert_text(
            (x, y),
            text,
            fontname=font_name,
            fontsize=font_size,
            color=color,
        )

        return save_document(doc)
    finally:
        doc.close()


def replace_text_simple(
    pdf_bytes: bytes,
    page_number: int,
    old_text: str,
    new_text: str,
    max_replacements: int = 1,
) -> bytes:
    """
    Simple text replace: search text, draw white rect, then insert new text.
    """
    doc = load_document(pdf_bytes)
    try:
        page = doc.load_page(page_number - 1)
        found = page.search_for(old_text)

        replaced = 0
        for rect in found:
            if replaced >= max_replacements:
                break

            # cover old text
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            x, y = rect.x0, rect.y0 + 10
            page.insert_text((x, y), new_text, fontsize=12, fontname="helv", color=(0, 0, 0))
            replaced += 1

        return save_document(doc)
    finally:
        doc.close()


def delete_text_by_bbox(pdf_bytes: bytes, page_number: int, bbox: List[float]) -> bytes:
    doc = load_document(pdf_bytes)
    try:
        page = doc.load_page(page_number - 1)
        rect = fitz.Rect(bbox)
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
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

