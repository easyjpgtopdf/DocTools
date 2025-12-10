"""
Google Document AI service for extracting tables from PDF documents.
New endpoint: /api/pdf-to-excel-docai
"""

import os
# Lazy import for documentai to avoid startup errors
# from google.cloud import documentai
from google.api_core import exceptions as gcp_exceptions
from typing import Tuple
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from io import BytesIO
import logging
import uuid
from datetime import datetime

from storage_gcs import upload_excel_to_gcs, upload_pdf_to_gcs_temp, delete_from_gcs_temp

logger = logging.getLogger(__name__)

# Environment variables
DOCAI_PROJECT_ID = os.environ.get('DOCAI_PROJECT_ID', 'easyjpgtopdf-de346')
DOCAI_LOCATION = os.environ.get('DOCAI_LOCATION', 'us')  # 'us', 'eu', or 'asia'
DOCAI_PROCESSOR_ID = os.environ.get('DOCAI_PROCESSOR_ID', '')  # e.g., '19a07dc1c08ce733'
GCS_BUCKET = os.environ.get('GCS_BUCKET', '')

# Initialize Document AI client
document_ai_client = None


def get_document_ai_client():
    """Initialize and return Document AI client using Application Default Credentials."""
    global document_ai_client
    if document_ai_client is None:
        # Lazy import to avoid startup errors
        try:
            from google.cloud import documentai
            document_ai_client = documentai.DocumentProcessorServiceClient()
        except ImportError as e:
            raise ImportError(f"Failed to import google.cloud.documentai: {e}. Please install google-cloud-documentai.")
    return document_ai_client


def upload_pdf_to_gcs_temp(file_content: bytes, filename: str) -> str:
    """
    Upload PDF to GCS temporarily for Document AI processing.
    Returns GCS URI.
    """
    from google.cloud import storage
    
    if not GCS_BUCKET:
        raise ValueError("GCS_BUCKET environment variable not set")
    
    # Generate unique GCS blob name
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d')
    blob_name = f"temp-pdf-uploads/{timestamp}/{unique_id}.pdf"
    
    try:
        client = storage.Client(project=DOCAI_PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(blob_name)
        
        blob.upload_from_string(
            file_content,
            content_type='application/pdf'
        )
        
        # Return GCS URI
        return f"gs://{GCS_BUCKET}/{blob_name}"
    except Exception as e:
        raise Exception(f"Failed to upload PDF to GCS: {str(e)}")


async def process_pdf_to_excel_docai(file_bytes: bytes, filename: str) -> Tuple[str, int]:
    """
    Process PDF with Google Document AI and convert to Excel.
    
    Args:
        file_bytes: PDF file content as bytes
        filename: Original PDF filename
    
    Returns:
        Tuple of (download_url, pages_processed)
    
    Raises:
        Exception: If processing fails
    """
    try:
        # Validate environment variables
        if not DOCAI_PROCESSOR_ID:
            raise ValueError("DOCAI_PROCESSOR_ID environment variable not set")
        if not GCS_BUCKET:
            raise ValueError("GCS_BUCKET environment variable not set")
        
        # Step 1: Upload PDF to GCS (Document AI requires GCS input)
        logger.info("Uploading PDF to GCS for Document AI processing...")
        gcs_uri = upload_pdf_to_gcs_temp(file_bytes, filename)
        logger.info(f"PDF uploaded to GCS: {gcs_uri}")
        
        # Step 2: Build Document AI resource name
        processor_name = f"projects/{DOCAI_PROJECT_ID}/locations/{DOCAI_LOCATION}/processors/{DOCAI_PROCESSOR_ID}"
        
        # Step 3: Call Document AI
        logger.info(f"Processing document with Document AI: {processor_name}")
        client = get_document_ai_client()
        
        # Configure the process request
        # Try different import approaches for compatibility
        try:
            from google.cloud.documentai_v1.types import document_processor_service
            GcsDocument = document_processor_service.GcsDocument
            InputConfig = document_processor_service.InputConfig
            ProcessRequest = document_processor_service.ProcessRequest
        except ImportError:
            # Fallback: try alternative import path
            try:
                from google.cloud import documentai_v1
                GcsDocument = documentai_v1.types.GcsDocument
                InputConfig = documentai_v1.types.InputConfig
                ProcessRequest = documentai_v1.types.ProcessRequest
            except (ImportError, AttributeError) as e:
                raise ImportError(f"Could not import Document AI types: {e}. Please check google-cloud-documentai installation.")
        
        gcs_document = GcsDocument(
            gcs_uri=gcs_uri,
            mime_type="application/pdf"
        )
        
        input_config = InputConfig(
            gcs_document=gcs_document,
            mime_type="application/pdf"
        )
        
        request = ProcessRequest(
            name=processor_name,
            input_config=input_config
        )
        
        # Process the document
        result = client.process_document(request=request)
        document = result.document
        
        # Step 4: Get page count
        pages_processed = len(document.pages)
        logger.info(f"Document processed. Pages: {pages_processed}")
        
        # Step 5: Extract tables
        logger.info("Extracting tables from Document AI response...")
        tables = extract_tables_from_document(document)
        logger.info(f"Found {len(tables)} tables")
        
        # Step 6: Create Excel workbook
        logger.info("Creating Excel workbook...")
        excel_bytes = create_excel_from_docai_tables(tables, filename)
        logger.info(f"Excel created: {len(excel_bytes)} bytes")
        
        # Step 7: Upload Excel to GCS and get signed URL
        logger.info("Uploading Excel to GCS...")
        base_filename = filename.replace('.pdf', '').replace('.PDF', '')
        download_url = upload_excel_to_gcs(excel_bytes, base_filename)
        logger.info(f"Excel uploaded. Download URL generated")
        
        return download_url, pages_processed
        
    except gcp_exceptions.GoogleAPIError as e:
        raise Exception(f"Document AI API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in process_pdf_to_excel_docai: {str(e)}")
        raise


def extract_tables_from_document(document) -> list:
    """
    Extract tables from Document AI document.
    Note: document type is documentai.Document but we avoid type hint to prevent import errors.
    """
    """
    Extract tables from Document AI document.
    Returns list of tables, each table is a 2D list (rows x columns).
    """
    tables = []
    
    # Iterate through all pages
    for page in document.pages:
        if page.tables:
            for table in page.tables:
                parsed_table = parse_docai_table(table, document.text)
                if parsed_table:
                    tables.append(parsed_table)
    
    return tables


def parse_docai_table(table, full_text: str) -> list:
    """
    Parse a Document AI table into a 2D list.
    Note: table type is documentai.Document.Page.Table but we avoid type hint to prevent import errors.
    """
    """
    Parse a single table from Document AI.
    Returns 2D list (rows x columns).
    """
    if not table.header_rows and not table.body_rows:
        return []
    
    # Combine header and body rows
    all_rows = []
    if table.header_rows:
        all_rows.extend(table.header_rows)
    if table.body_rows:
        all_rows.extend(table.body_rows)
    
    if not all_rows:
        return []
    
    # Find max columns
    max_cols = 0
    for row in all_rows:
        if row.cells:
            max_cols = max(max_cols, len(row.cells))
    
    if max_cols == 0:
        return []
    
    # Build grid
    grid = []
    for row in all_rows:
        row_data = [''] * max_cols
        if row.cells:
            for col_idx, cell in enumerate(row.cells):
                if col_idx < max_cols:
                    cell_text = extract_text_from_layout(cell.layout, full_text)
                    row_data[col_idx] = cell_text
        grid.append(row_data)
    
    return grid


def extract_text_from_layout(layout, full_text: str) -> str:
    """
    Extract text from a Document AI layout element.
    Note: layout type is documentai.Document.Page.Layout but we avoid type hint to prevent import errors.
    """
    """Extract text from a layout element using text anchor."""
    if not layout or not layout.text_anchor:
        return ''
    
    text_anchor = layout.text_anchor
    if not text_anchor.text_segments:
        return ''
    
    text_parts = []
    for segment in text_anchor.text_segments:
        start_index = int(segment.start_index) if segment.start_index else 0
        end_index = int(segment.end_index) if segment.end_index else 0
        
        if start_index < len(full_text) and end_index <= len(full_text):
            text_parts.append(full_text[start_index:end_index])
    
    return ' '.join(text_parts).strip()


def create_excel_from_docai_tables(tables: list, pdf_filename: str) -> bytes:
    """
    Create Excel workbook from Document AI tables.
    One sheet per table (or per page if multiple tables per page).
    """
    workbook = Workbook()
    workbook.remove(workbook.active)
    
    # Style definitions
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = openpyxl.styles.PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_alignment = Alignment(horizontal='center', vertical='center')
    
    base_name = pdf_filename.replace('.pdf', '').replace('.PDF', '')
    
    # If no tables found
    if not tables:
        sheet = workbook.create_sheet(title="No Tables")
        sheet['A1'] = "No tables detected in this PDF."
        sheet['A1'].font = Font(italic=True, color="666666")
    else:
        # Create one sheet per table
        for idx, table in enumerate(tables):
            sheet_name = f"Table {idx + 1}" if len(tables) > 1 else base_name[:31]
            sheet = workbook.create_sheet(title=sheet_name)
            
            # Write table data
            for row_idx, row in enumerate(table, start=1):
                for col_idx, cell_value in enumerate(row, start=1):
                    cell = sheet.cell(row=row_idx, column=col_idx)
                    cell.value = cell_value
                    cell.border = border
                    cell.alignment = center_alignment
                    
                    # Style header row (first row)
                    if row_idx == 1:
                        cell.font = header_font
                        cell.fill = header_fill
    
    # Auto-adjust column widths
    for sheet in workbook.worksheets:
        for column in sheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            sheet.column_dimensions[column_letter].width = adjusted_width
    
    # Save to bytes
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output.getvalue()

