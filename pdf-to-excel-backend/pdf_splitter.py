"""
PDF Splitter utility for handling documents that exceed Document AI page limits.
Splits PDFs into chunks of 30 pages for processing.
"""

import logging
from typing import List, Tuple
from io import BytesIO

logger = logging.getLogger(__name__)

try:
    import PyPDF2
    PDF2_AVAILABLE = True
except ImportError:
    PDF2_AVAILABLE = False
    logger.warning("PyPDF2 not available - PDF splitting disabled")

try:
    from pdf_lib import PDFDocument
    PDF_LIB_AVAILABLE = True
except ImportError:
    PDF_LIB_AVAILABLE = False
    logger.warning("pdf-lib not available - trying PyPDF2 for PDF splitting")


def split_pdf_into_chunks(pdf_bytes: bytes, max_pages_per_chunk: int = 30) -> List[Tuple[bytes, int, int]]:
    """
    Split PDF into chunks of max_pages_per_chunk pages.
    
    Args:
        pdf_bytes: PDF file as bytes
        max_pages_per_chunk: Maximum pages per chunk (default: 30 for Document AI limit)
    
    Returns:
        List of tuples: (chunk_bytes, start_page, end_page) where pages are 1-based
    """
    if not PDF2_AVAILABLE:
        raise ImportError("PyPDF2 is required for PDF splitting. Please install: pip install PyPDF2")
    
    chunks = []
    
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        total_pages = len(pdf_reader.pages)
        
        logger.info(f"Splitting PDF: {total_pages} pages into chunks of {max_pages_per_chunk}")
        
        if total_pages <= max_pages_per_chunk:
            # No splitting needed
            logger.info(f"PDF has {total_pages} pages (≤{max_pages_per_chunk}), no splitting required")
            return [(pdf_bytes, 1, total_pages)]
        
        # Split into chunks
        for start_page in range(0, total_pages, max_pages_per_chunk):
            end_page = min(start_page + max_pages_per_chunk, total_pages)
            
            # Create new PDF with pages from start_page to end_page
            pdf_writer = PyPDF2.PdfWriter()
            for page_idx in range(start_page, end_page):
                pdf_writer.add_page(pdf_reader.pages[page_idx])
            
            # Write to bytes
            chunk_buffer = BytesIO()
            pdf_writer.write(chunk_buffer)
            chunk_bytes = chunk_buffer.getvalue()
            
            # Store chunk with 1-based page numbers
            chunks.append((chunk_bytes, start_page + 1, end_page))
            logger.info(f"Created chunk: pages {start_page + 1}-{end_page} ({end_page - start_page} pages)")
        
        logger.info(f"Split PDF into {len(chunks)} chunk(s)")
        return chunks
        
    except Exception as e:
        logger.error(f"Error splitting PDF: {e}")
        raise Exception(f"Failed to split PDF: {str(e)}")

