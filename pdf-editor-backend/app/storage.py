import uuid
from typing import Dict

# Simple in-memory store: session_id -> pdf bytes
PDF_SESSIONS: Dict[str, bytes] = {}


def create_session(pdf_bytes: bytes) -> str:
    session_id = str(uuid.uuid4())
    PDF_SESSIONS[session_id] = pdf_bytes
    return session_id


def get_pdf_bytes(session_id: str) -> bytes:
    if session_id not in PDF_SESSIONS:
        raise KeyError("Session not found")
    return PDF_SESSIONS[session_id]


def update_pdf_bytes(session_id: str, pdf_bytes: bytes) -> None:
    if session_id not in PDF_SESSIONS:
        raise KeyError("Session not found")
    PDF_SESSIONS[session_id] = pdf_bytes


def session_exists(session_id: str) -> bool:
    return session_id in PDF_SESSIONS

