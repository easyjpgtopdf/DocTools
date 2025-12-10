"""
Google Document AI client module.
Handles OCR and layout extraction from PDFs using Document AI.

Example usage:
    from app.docai_client import get_docai_client, DocumentAIClient
    
    # Using convenience function
    from app.config import get_settings
    settings = get_settings()
    parsed_doc = process_pdf_to_layout(
        settings.project_id,
        settings.docai_location,
        settings.docai_processor_id,
        pdf_bytes
    )
    
    # Using client directly
    client = DocumentAIClient(
        project_id="my-project",
        location="us",
        processor_id="ffaa7bcd30a9c788"
    )
    parsed_doc = client.process_pdf_to_layout(pdf_bytes)
"""
from google.cloud import documentai_v1 as documentai
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a text block with layout information."""
    text: str
    bounding_box: Optional[Dict] = None
    font_size: Optional[float] = None
    is_heading: bool = False
    page_number: int = 1


@dataclass
class TableData:
    """Represents a table structure."""
    rows: List[List[str]]
    page_number: int = 1


@dataclass
class ParsedDocument:
    """Structured document parsed from Document AI."""
    pages: List[List[TextBlock]]
    tables: List[TableData]
    full_text: str


class DocumentAIClient:
    """Google Document AI client wrapper."""
    
    def __init__(self, project_id: str, location: str, processor_id: str):
        """
        Initialize Document AI client.
        
        Args:
            project_id: Google Cloud Project ID
            location: Document AI location (e.g., 'us')
            processor_id: Document AI processor ID
        """
        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        self.client = documentai.DocumentProcessorServiceClient()
        self.processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
        logger.info(f"Document AI client initialized: {self.processor_name}")
    
    def process_pdf_to_document(self, pdf_bytes: bytes) -> documentai.Document:
        """
        Process PDF bytes and return raw Document AI Document object.
        
        This method returns the raw Document AI response, which can be useful
        for advanced processing or custom parsing.
        
        Example:
            document = client.process_pdf_to_document(pdf_bytes)
            # Access raw Document AI structure
            for page in document.pages:
                print(f"Page {page.page_number} has {len(page.paragraphs)} paragraphs")
        
        Args:
            pdf_bytes: PDF file as bytes
            
        Returns:
            documentai.Document object
        """
        try:
            logger.info("Processing PDF with Document AI (raw mode)...")
            
            # Create RawDocument
            raw_document = documentai.RawDocument(
                content=pdf_bytes,
                mime_type="application/pdf"
            )
            
            # Create process request
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            # Process document
            result = self.client.process_document(request=request)
            document = result.document
            
            logger.info(f"Document processed: {len(document.pages)} pages")
            return document
            
        except Exception as e:
            logger.error(f"Document AI processing error: {e}")
            raise
    
    def process_pdf_to_layout(self, pdf_bytes: bytes) -> ParsedDocument:
        """
        Process PDF bytes and extract text, layout, and structure.
        
        Args:
            pdf_bytes: PDF file as bytes
            
        Returns:
            ParsedDocument with structured content
        """
        try:
            logger.info("Processing PDF with Document AI...")
            
            # Create request
            raw_document = documentai.RawDocument(
                content=pdf_bytes,
                mime_type="application/pdf"
            )
            
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            # Process document
            result = self.client.process_document(request=request)
            document = result.document
            
            logger.info(f"Document processed: {len(document.pages)} pages")
            
            # Extract structured content
            pages = []
            tables = []
            
            for page_num, page in enumerate(document.pages, start=1):
                page_blocks = []
                
                # Extract paragraphs and text blocks
                for block in page.paragraphs:
                    text = self._extract_text_from_layout(block.layout, document.text)
                    font_size = self._get_font_size(block.layout)
                    is_heading = self._is_heading(block.layout, font_size)
                    
                    page_blocks.append(TextBlock(
                        text=text,
                        font_size=font_size,
                        is_heading=is_heading,
                        page_number=page_num
                    ))
                
                # Extract tables
                for table in page.tables:
                    table_data = self._extract_table_data(table, document.text)
                    tables.append(TableData(
                        rows=table_data,
                        page_number=page_num
                    ))
                
                pages.append(page_blocks)
            
            full_text = document.text if document.text else ""
            
            return ParsedDocument(
                pages=pages,
                tables=tables,
                full_text=full_text
            )
            
        except Exception as e:
            logger.error(f"Document AI processing error: {e}")
            raise
    
    def _extract_text_from_layout(self, layout: Any, document_text: str) -> str:
        """Extract text from layout element."""
        try:
            text_anchor = layout.text_anchor
            if text_anchor and text_anchor.text_segments:
                start_index = text_anchor.text_segments[0].start_index
                end_index = text_anchor.text_segments[0].end_index
                return document_text[start_index:end_index].strip()
        except Exception as e:
            logger.warning(f"Error extracting text from layout: {e}")
        return ""
    
    def _get_font_size(self, layout: Any) -> Optional[float]:
        """Extract font size from layout element."""
        try:
            if hasattr(layout, 'detected_languages') and layout.detected_languages:
                # Try to get font size from detected language info
                # This is approximate - Document AI doesn't always provide font size directly
                pass
            
            # Fallback: estimate from bounding box height
            if hasattr(layout, 'bounding_poly') and layout.bounding_poly:
                vertices = layout.bounding_poly.vertices
                if len(vertices) >= 2:
                    height = abs(vertices[2].y - vertices[0].y)
                    # Rough estimation: 1 point ≈ 0.75 pixels
                    estimated_size = height * 0.75
                    return estimated_size
        except Exception as e:
            logger.debug(f"Could not extract font size: {e}")
        return None
    
    def _is_heading(self, layout: Any, font_size: Optional[float]) -> bool:
        """Determine if text block is likely a heading."""
        if not font_size:
            return False
        
        # Heuristics: larger font sizes are likely headings
        # Typical body text is 10-12pt, headings are 14pt+
        return font_size >= 14.0
    
    def _extract_table_data(self, table: Any, document_text: str) -> List[List[str]]:
        """Extract table data into rows and columns."""
        rows_data = []
        try:
            for row in table.body_rows:
                row_data = []
                for cell in row.cells:
                    cell_text = self._extract_text_from_layout(cell.layout, document_text)
                    row_data.append(cell_text)
                if row_data:
                    rows_data.append(row_data)
        except Exception as e:
            logger.warning(f"Error extracting table data: {e}")
        return rows_data


def get_docai_client(settings: Settings) -> DocumentAIClient:
    """
    Get Document AI client from settings.
    
    Example:
        from app.config import get_settings
        settings = get_settings()
        client = get_docai_client(settings)
        parsed_doc = client.process_pdf_to_layout(pdf_bytes)
    
    Args:
        settings: Application settings
        
    Returns:
        DocumentAIClient instance
    """
    return DocumentAIClient(
        settings.project_id,
        settings.docai_location,
        settings.docai_processor_id
    )


def process_pdf_to_layout(
    project_id: str,
    location: str,
    processor_id: str,
    pdf_bytes: bytes
) -> ParsedDocument:
    """
    Convenience function to process PDF with Document AI.
    
    Args:
        project_id: Google Cloud Project ID
        location: Document AI location
        processor_id: Document AI processor ID (e.g., 'ffaa7bcd30a9c788' for pdf-to-word-docai)
        pdf_bytes: PDF file as bytes
        
    Returns:
        ParsedDocument
    """
    client = DocumentAIClient(project_id, location, processor_id)
    return client.process_pdf_to_layout(pdf_bytes)

