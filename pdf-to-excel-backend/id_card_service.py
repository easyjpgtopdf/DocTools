"""
ID Card Processing Service
Handles ID card extraction for FREE and PREMIUM users
"""

import logging
import csv
import json
from io import BytesIO, StringIO
from typing import Dict, Tuple, Optional
import uuid
from datetime import datetime

from storage_gcs import upload_file_to_gcs

logger = logging.getLogger(__name__)

# GCS bucket for ID card outputs
GCS_BUCKET = None

def get_gcs_bucket():
    """Get GCS bucket name from environment."""
    global GCS_BUCKET
    if GCS_BUCKET is None:
        import os
        GCS_BUCKET = os.environ.get('GCS_BUCKET', 'easyjpgtopdf-excel-exports')
    return GCS_BUCKET


def extract_text_from_pdf_free(file_bytes: bytes) -> Dict:
    """
    Extract text from PDF using PyPDF2 (FREE - no OCR cost).
    
    Args:
        file_bytes: PDF file bytes
    
    Returns:
        Dict with extracted text and metadata
    """
    try:
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        
        text_content = ""
        pages_text = []
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text()
            text_content += page_text + "\n\n"
            pages_text.append({
                "page": page_num,
                "text": page_text
            })
        
        return {
            "success": True,
            "text": text_content.strip(),
            "pages": pages_text,
            "page_count": len(pdf_reader.pages)
        }
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "pages": [],
            "page_count": 0
        }


def generate_csv_template() -> bytes:
    """
    Generate CSV template for ID card fields (FREE).
    
    Returns:
        CSV file bytes
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Field Name",
        "Value"
    ])
    
    # Template fields
    fields = [
        ["Name", ""],
        ["Date of Birth", ""],
        ["ID Number", ""],
        ["Gender", ""],
        ["Address", ""],
        ["Father's Name", ""],
        ["Mother's Name", ""],
        ["Nationality", ""],
        ["Issue Date", ""],
        ["Expiry Date", ""]
    ]
    
    for field in fields:
        writer.writerow(field)
    
    csv_content = output.getvalue()
    return csv_content.encode('utf-8')


def process_id_card_free(file_bytes: bytes, filename: str) -> Tuple[Optional[str], Dict]:
    """
    Process ID card for FREE users (text extraction + CSV template).
    NO Document AI / OCR cost.
    
    Args:
        file_bytes: PDF file bytes
        filename: Original filename
    
    Returns:
        Tuple of (csv_template_url, text_extraction_result)
    """
    try:
        # Extract text using free method (PyPDF2)
        text_result = extract_text_from_pdf_free(file_bytes)
        
        # Generate CSV template
        csv_template = generate_csv_template()
        
        # Upload CSV template to GCS
        base_filename = filename.replace('.pdf', '').replace('.PDF', '')
        unique_id = str(uuid.uuid4())[:8]
        csv_filename = f"{base_filename}_id_template_{unique_id}.csv"
        timestamp = datetime.now().strftime('%Y%m%d')
        blob_name = f"id-card-templates/{timestamp}/{csv_filename}"
        
        csv_url = upload_file_to_gcs(
            csv_template,
            blob_name,
            content_type='text/csv'
        )
        
        return csv_url, text_result
        
    except Exception as e:
        logger.error(f"Error processing ID card (FREE): {e}")
        raise


async def process_id_card_premium(file_bytes: bytes, filename: str) -> Tuple[Optional[str], Dict]:
    """
    Process ID card for PREMIUM users using identity-docai processor.
    
    Args:
        file_bytes: PDF file bytes
        filename: Original filename
    
    Returns:
        Tuple of (download_url, extracted_data)
    """
    try:
        # Import identity processor handler
        from docai_multi_processor import process_pdf_with_processor
        
        # Process with identity-docai processor
        download_url, pages_processed, tables_found, extracted_data = await process_pdf_with_processor(
            file_bytes,
            filename,
            "identity-docai"
        )
        
        # For ID cards, we return JSON/CSV, not Excel
        # But the processor returns Excel URL, so we'll work with that
        # In future, we can add a separate JSON/CSV export for ID cards
        
        return download_url, {
            "pages_processed": pages_processed,
            "extracted_data": extracted_data,
            "tables_found": tables_found
        }
        
    except Exception as e:
        logger.error(f"Error processing ID card (PREMIUM): {e}")
        raise

