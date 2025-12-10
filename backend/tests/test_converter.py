"""
Tests for PDF converter functionality.
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.converter import (
    pdf_has_text,
    convert_pdf_to_docx_with_libreoffice,
    convert_pdf_to_docx_with_docai,
    get_page_count
)
from app.docai_client import ParsedDocument, TextBlock, TableData


class TestPDFHasText:
    """Tests for pdf_has_text function."""
    
    @patch('app.converter.pdf_extract_text')
    def test_pdf_has_text_returns_true_when_text_found(self, mock_extract):
        """Test that pdf_has_text returns True when text is found."""
        mock_extract.return_value = "This is some sample text content that should be detected."
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            result = pdf_has_text(tmp.name)
            assert result is True
            os.unlink(tmp.name)
    
    @patch('app.converter.pdf_extract_text')
    def test_pdf_has_text_returns_false_when_no_text(self, mock_extract):
        """Test that pdf_has_text returns False when no text is found."""
        mock_extract.return_value = "   \n\n  "  # Only whitespace
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            result = pdf_has_text(tmp.name)
            assert result is False
            os.unlink(tmp.name)
    
    @patch('app.converter.pdf_extract_text')
    def test_pdf_has_text_handles_exception(self, mock_extract):
        """Test that pdf_has_text handles exceptions gracefully."""
        mock_extract.side_effect = Exception("PDF parsing error")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            result = pdf_has_text(tmp.name)
            assert result is False  # Should return False on error
            os.unlink(tmp.name)


class TestLibreOfficeConversion:
    """Tests for LibreOffice conversion."""
    
    @patch('app.converter.subprocess.run')
    @patch('os.path.exists')
    def test_convert_with_libreoffice_success(self, mock_exists, mock_run):
        """Test successful LibreOffice conversion."""
        mock_run.return_value = Mock(returncode=0, stderr="")
        mock_exists.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            Path(pdf_path).touch()
            
            result = convert_pdf_to_docx_with_libreoffice(pdf_path, tmpdir)
            assert result.endswith('.docx')
            mock_run.assert_called_once()
    
    @patch('app.converter.subprocess.run')
    def test_convert_with_libreoffice_failure(self, mock_run):
        """Test LibreOffice conversion failure handling."""
        mock_run.return_value = Mock(returncode=1, stderr="Conversion failed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            Path(pdf_path).touch()
            
            with pytest.raises(Exception, match="LibreOffice conversion failed"):
                convert_pdf_to_docx_with_libreoffice(pdf_path, tmpdir)


class TestDocAIConversion:
    """Tests for Document AI conversion."""
    
    def test_convert_with_docai_creates_docx(self):
        """Test that DocAI conversion creates a DOCX file."""
        # Create mock parsed document
        parsed_doc = ParsedDocument(
            pages=[
                [
                    TextBlock(text="Page 1 content", is_heading=False, page_number=1),
                    TextBlock(text="Heading", is_heading=True, page_number=1)
                ]
            ],
            tables=[],
            full_text="Page 1 content Heading"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            output_path = os.path.join(tmpdir, "output.docx")
            Path(pdf_path).touch()
            
            result = convert_pdf_to_docx_with_docai(pdf_path, output_path, parsed_doc)
            
            assert result == output_path
            assert os.path.exists(output_path)
    
    def test_convert_with_docai_handles_tables(self):
        """Test that DocAI conversion handles tables."""
        parsed_doc = ParsedDocument(
            pages=[[TextBlock(text="Content", page_number=1)]],
            tables=[
                TableData(
                    rows=[["Header1", "Header2"], ["Value1", "Value2"]],
                    page_number=1
                )
            ],
            full_text="Content"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            output_path = os.path.join(tmpdir, "output.docx")
            Path(pdf_path).touch()
            
            result = convert_pdf_to_docx_with_docai(pdf_path, output_path, parsed_doc)
            assert os.path.exists(result)


class TestPageCount:
    """Tests for get_page_count function."""
    
    @patch('app.converter.PdfReader')
    def test_get_page_count(self, mock_pdf_reader):
        """Test page count extraction."""
        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock(), Mock()]  # 3 pages
        mock_pdf_reader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            count = get_page_count(tmp.name)
            assert count == 3
            os.unlink(tmp.name)

