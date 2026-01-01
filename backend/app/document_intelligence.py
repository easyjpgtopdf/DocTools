"""
Hybrid Document Intelligence Pipeline
Implements comprehensive PDF analysis, classification, and routing
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage
    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False
    logger.warning("pdfminer not available. Some features may be limited.")

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    logger.warning("PyMuPDF not available. Advanced layout parsing will be limited.")


class DocumentNature(str, Enum):
    """Document nature types."""
    DIGITAL = "digital"  # Text-based PDF
    SCANNED = "scanned"  # Image-based PDF
    HYBRID = "hybrid"    # Mixed text and images


class DocumentCategory(str, Enum):
    """Document category types."""
    INVOICE = "invoice"
    BANK_STATEMENT = "bank_statement"
    GOVT_FORM = "govt_form"
    ACADEMIC = "academic"
    GRAPHIC = "graphic"
    RESUME = "resume"
    LETTER = "letter"
    CERTIFICATE = "certificate"
    ID_CARD = "id_card"
    UNKNOWN = "unknown"


class LanguageSignal(str, Enum):
    """Language detection signals."""
    ENGLISH = "english"
    HINDI = "hindi"
    MIXED = "mixed"
    OTHER = "other"


@dataclass
class StructuralMetadata:
    """Metadata for a single page."""
    page_number: int
    has_text_layer: bool
    has_vector_objects: bool
    has_images: bool
    has_logos: bool = False
    has_tables: bool = False
    has_signatures: bool = False
    text_block_count: int = 0
    image_count: int = 0
    table_count: int = 0
    language_signals: List[LanguageSignal] = field(default_factory=list)
    numeric_density: float = 0.0  # Ratio of numeric characters
    table_density: float = 0.0  # Ratio of table content


@dataclass
class LayoutBlock:
    """Represents a layout block on a page."""
    block_type: str  # 'text', 'image', 'table', 'logo', 'shape', 'background'
    bounding_box: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    z_order: int
    reading_sequence: int
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableGrid:
    """Structured table representation."""
    rows: List[List[str]]
    bounding_box: Tuple[float, float, float, float]
    headers: Optional[List[str]] = None
    page_number: int = 1


@dataclass
class DocumentIntelligence:
    """Complete document intelligence result."""
    document_nature: DocumentNature
    document_category: DocumentCategory
    category_confidence: float
    language_signals: List[LanguageSignal]
    structural_metadata: List[StructuralMetadata]
    layout_blocks: List[List[LayoutBlock]]  # Per-page layout blocks
    tables: List[TableGrid]
    logos: List[Dict[str, Any]]  # Logo positions and metadata
    requires_ocr: bool
    requires_layout_preservation: bool
    requires_table_extraction: bool
    processing_notes: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)


class DocumentIntelligencePipeline:
    """Hybrid document intelligence pipeline."""
    
    def __init__(self):
        self.invoice_keywords = [
            'invoice', 'bill', 'tax', 'gst', 'amount', 'total', 'subtotal',
            'due date', 'invoice number', 'invoice no', 'bill to', 'ship to'
        ]
        self.statement_keywords = [
            'bank', 'statement', 'account', 'balance', 'transaction',
            'credit', 'debit', 'deposit', 'withdrawal', 'cheque'
        ]
        self.govt_form_keywords_hindi = [
            'आवेदन', 'फॉर्म', 'प्रमाणपत्र', 'अनुमति', 'लाइसेंस',
            'रजिस्ट्रेशन', 'प्रमाण', 'दस्तावेज'
        ]
        self.academic_keywords = [
            'university', 'college', 'degree', 'course', 'grade',
            'semester', 'credits', 'transcript', 'marksheet'
        ]
        self.resume_keywords = [
            'resume', 'cv', 'curriculum vitae', 'experience',
            'education', 'skills', 'objective', 'summary'
        ]
    
    def analyze_document(
        self,
        pdf_path: str,
        use_docai: bool = False,
        docai_client = None
    ) -> DocumentIntelligence:
        """
        Main entry point for document intelligence pipeline.
        
        Args:
            pdf_path: Path to PDF file
            use_docai: Whether to use DocAI for enhanced analysis
            docai_client: Optional DocAI client for classification
            
        Returns:
            DocumentIntelligence object with complete analysis
        """
        logger.info(f"Starting document intelligence analysis: {pdf_path}")
        
        # Step 1: Document Nature Detection
        nature = self._detect_document_nature(pdf_path)
        logger.info(f"Document nature: {nature}")
        
        # Step 2: Extract structural metadata per page
        structural_metadata = self._extract_structural_metadata(pdf_path)
        
        # Step 3: Language signal detection
        language_signals = self._detect_language_signals(pdf_path, structural_metadata)
        logger.info(f"Language signals: {language_signals}")
        
        # Step 4: Heuristic Classification
        heuristic_category, heuristic_confidence = self._heuristic_classification(
            pdf_path, structural_metadata, language_signals
        )
        logger.info(f"Heuristic classification: {heuristic_category} (confidence: {heuristic_confidence:.2f})")
        
        # Step 5: AI Classifier Confirmation (if available)
        final_category = heuristic_category
        final_confidence = heuristic_confidence
        
        if use_docai and docai_client:
            ai_category, ai_confidence = self._ai_classifier_confirmation(
                pdf_path, docai_client, heuristic_category
            )
            if ai_confidence >= 0.85:
                final_category = ai_category
                final_confidence = ai_confidence
                logger.info(f"AI classifier confirmed: {final_category} (confidence: {final_confidence:.2f})")
            else:
                logger.info(f"AI classifier confidence low ({ai_confidence:.2f}), using heuristic: {heuristic_category}")
        
        # Step 6: Layout Parsing & Object Modeling
        layout_blocks, tables, logos = self._parse_layout_and_objects(
            pdf_path, structural_metadata
        )
        
        # Step 7: Determine processing requirements
        requires_ocr = nature in [DocumentNature.SCANNED, DocumentNature.HYBRID]
        requires_layout_preservation = any(
            meta.has_logos or meta.has_images or meta.has_vector_objects
            for meta in structural_metadata
        )
        requires_table_extraction = any(meta.has_tables for meta in structural_metadata)
        
        # Step 8: Generate processing notes
        processing_notes = self._generate_processing_notes(
            nature, final_category, structural_metadata, requires_ocr
        )
        
        # Build result
        result = DocumentIntelligence(
            document_nature=nature,
            document_category=final_category,
            category_confidence=final_confidence,
            language_signals=language_signals,
            structural_metadata=structural_metadata,
            layout_blocks=layout_blocks,
            tables=tables,
            logos=logos,
            requires_ocr=requires_ocr,
            requires_layout_preservation=requires_layout_preservation,
            requires_table_extraction=requires_table_extraction,
            processing_notes=processing_notes,
            confidence_scores={
                'heuristic': heuristic_confidence,
                'ai_classifier': final_confidence if use_docai else 0.0
            }
        )
        
        logger.info(f"Document intelligence analysis complete: {final_category} ({final_confidence:.2f} confidence)")
        return result
    
    def _detect_document_nature(self, pdf_path: str) -> DocumentNature:
        """Detect if PDF is scanned, digital, or hybrid."""
        if not HAS_PDFMINER:
            # Fallback: assume hybrid if pdfminer not available
            return DocumentNature.HYBRID
        
        try:
            # Extract text from first few pages
            text = pdf_extract_text(pdf_path, maxpages=3)
            cleaned_text = text.strip().replace('\n', '').replace(' ', '')
            
            # Count extractable text characters
            text_char_count = len(cleaned_text)
            
            # Check for images (if PyMuPDF available)
            image_count = 0
            if HAS_PYMUPDF:
                try:
                    doc = fitz.open(pdf_path)
                    for page_num in range(min(3, len(doc))):
                        page = doc.load_page(page_num)
                        image_list = page.get_images()
                        image_count += len(image_list)
                    doc.close()
                except Exception:
                    pass
            
            # Determine nature based on text/image ratio
            if text_char_count > 200 and image_count == 0:
                return DocumentNature.DIGITAL
            elif text_char_count < 50 and image_count > 0:
                return DocumentNature.SCANNED
            else:
                return DocumentNature.HYBRID
                
        except Exception as e:
            logger.warning(f"Error detecting document nature: {e}")
            return DocumentNature.HYBRID
    
    def _extract_structural_metadata(self, pdf_path: str) -> List[StructuralMetadata]:
        """Extract structural metadata for each page."""
        metadata_list = []
        
        try:
            if HAS_PYMUPDF:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    
                    # Check for text layer
                    text = page.get_text()
                    has_text = len(text.strip()) > 0
                    
                    # Check for images
                    image_list = page.get_images()
                    has_images = len(image_list) > 0
                    
                    # Check for vector objects (paths/drawings)
                    drawings = page.get_drawings()
                    has_vector_objects = len(drawings) > 0
                    
                    # Count text blocks (approximate)
                    text_blocks = page.get_text("blocks")
                    text_block_count = len(text_blocks) if text_blocks else 0
                    
                    # Calculate numeric density
                    numeric_chars = sum(1 for c in text if c.isdigit())
                    total_chars = len(text.replace(' ', '').replace('\n', ''))
                    numeric_density = numeric_chars / total_chars if total_chars > 0 else 0.0
                    
                    metadata = StructuralMetadata(
                        page_number=page_num + 1,
                        has_text_layer=has_text,
                        has_vector_objects=has_vector_objects,
                        has_images=has_images,
                        text_block_count=text_block_count,
                        image_count=len(image_list),
                        numeric_density=numeric_density
                    )
                    metadata_list.append(metadata)
                
                doc.close()
            else:
                # Fallback: basic metadata
                if HAS_PDFMINER:
                    text = pdf_extract_text(pdf_path)
                    has_text = len(text.strip()) > 0
                    metadata = StructuralMetadata(
                        page_number=1,
                        has_text_layer=has_text,
                        has_vector_objects=False,
                        has_images=False,
                        text_block_count=1 if has_text else 0
                    )
                    metadata_list.append(metadata)
                    
        except Exception as e:
            logger.error(f"Error extracting structural metadata: {e}")
            # Return minimal metadata
            metadata_list.append(StructuralMetadata(
                page_number=1,
                has_text_layer=False,
                has_vector_objects=False,
                has_images=False
            ))
        
        return metadata_list
    
    def _detect_language_signals(
        self,
        pdf_path: str,
        metadata: List[StructuralMetadata]
    ) -> List[LanguageSignal]:
        """Detect language signals (Hindi, English, Mixed)."""
        signals = []
        
        try:
            if HAS_PDFMINER:
                text = pdf_extract_text(pdf_path, maxpages=5)
                
                # Check for Devanagari script (Hindi)
                devanagari_chars = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
                total_chars = len(text.replace(' ', '').replace('\n', ''))
                
                if total_chars > 0:
                    devanagari_ratio = devanagari_chars / total_chars
                    
                    # Check for English (Latin script)
                    latin_chars = sum(1 for c in text if ord(c) < 0x0900 and c.isalpha())
                    latin_ratio = latin_chars / total_chars
                    
                    if devanagari_ratio > 0.3 and latin_ratio > 0.2:
                        signals.append(LanguageSignal.MIXED)
                    elif devanagari_ratio > 0.3:
                        signals.append(LanguageSignal.HINDI)
                    elif latin_ratio > 0.5:
                        signals.append(LanguageSignal.ENGLISH)
                    else:
                        signals.append(LanguageSignal.OTHER)
                else:
                    signals.append(LanguageSignal.OTHER)
            else:
                signals.append(LanguageSignal.OTHER)
                
        except Exception as e:
            logger.warning(f"Error detecting language signals: {e}")
            signals.append(LanguageSignal.OTHER)
        
        return signals if signals else [LanguageSignal.OTHER]
    
    def _heuristic_classification(
        self,
        pdf_path: str,
        metadata: List[StructuralMetadata],
        language_signals: List[LanguageSignal]
    ) -> Tuple[DocumentCategory, float]:
        """Apply rule-based classification."""
        try:
            if HAS_PDFMINER:
                text = pdf_extract_text(pdf_path, maxpages=3).lower()
            else:
                text = ""
            
            scores = {}
            
            # Invoice detection
            invoice_score = sum(1 for keyword in self.invoice_keywords if keyword in text)
            invoice_score += sum(1 for meta in metadata if meta.numeric_density > 0.2)
            invoice_score /= (len(self.invoice_keywords) + len(metadata))
            scores[DocumentCategory.INVOICE] = min(invoice_score * 2, 1.0)
            
            # Bank statement detection
            statement_score = sum(1 for keyword in self.statement_keywords if keyword in text)
            statement_score += sum(1 for meta in metadata if meta.numeric_density > 0.3)
            statement_score /= (len(self.statement_keywords) + len(metadata))
            scores[DocumentCategory.BANK_STATEMENT] = min(statement_score * 2, 1.0)
            
            # Govt form detection (Hindi)
            if LanguageSignal.HINDI in language_signals or LanguageSignal.MIXED in language_signals:
                govt_score = sum(1 for keyword in self.govt_form_keywords_hindi if keyword in text)
                govt_score /= len(self.govt_form_keywords_hindi) if self.govt_form_keywords_hindi else 1
                scores[DocumentCategory.GOVT_FORM] = min(govt_score * 2, 1.0)
            else:
                scores[DocumentCategory.GOVT_FORM] = 0.0
            
            # Academic detection
            academic_score = sum(1 for keyword in self.academic_keywords if keyword in text)
            academic_score /= len(self.academic_keywords)
            scores[DocumentCategory.ACADEMIC] = min(academic_score * 2, 1.0)
            
            # Resume detection
            resume_score = sum(1 for keyword in self.resume_keywords if keyword in text)
            resume_score /= len(self.resume_keywords)
            scores[DocumentCategory.RESUME] = min(resume_score * 2, 1.0)
            
            # Graphic detection (high image/vector ratio)
            total_images = sum(meta.image_count for meta in metadata)
            total_pages = len(metadata)
            if total_pages > 0 and total_images / total_pages > 3:
                scores[DocumentCategory.GRAPHIC] = 0.7
            else:
                scores[DocumentCategory.GRAPHIC] = 0.0
            
            # Find best match
            best_category = max(scores.items(), key=lambda x: x[1])
            
            if best_category[1] < 0.3:
                return DocumentCategory.UNKNOWN, best_category[1]
            
            return best_category[0], best_category[1]
            
        except Exception as e:
            logger.error(f"Error in heuristic classification: {e}")
            return DocumentCategory.UNKNOWN, 0.0
    
    def _ai_classifier_confirmation(
        self,
        pdf_path: str,
        docai_client,
        fallback_category: DocumentCategory
    ) -> Tuple[DocumentCategory, float]:
        """
        Use AI classifier for confirmation (first 1-2 pages only).
        Returns category and confidence (0-1).
        """
        # Placeholder for AI classifier integration
        # This would use DocAI's document classifier if available
        # For now, return fallback
        logger.info("AI classifier confirmation not yet implemented, using heuristic result")
        return fallback_category, 0.5
    
    def _parse_layout_and_objects(
        self,
        pdf_path: str,
        metadata: List[StructuralMetadata]
    ) -> Tuple[List[List[LayoutBlock]], List[TableGrid], List[Dict[str, Any]]]:
        """
        Parse layout and extract objects (tables, logos, etc.).
        Returns (layout_blocks_per_page, tables, logos)
        """
        layout_blocks_per_page = []
        tables = []
        logos = []
        
        try:
            if HAS_PYMUPDF:
                doc = fitz.open(pdf_path)
                for page_num, page_meta in enumerate(metadata):
                    page = doc.load_page(page_num)
                    blocks = []
                    
                    # Extract text blocks
                    text_blocks = page.get_text("blocks")
                    for idx, block in enumerate(text_blocks):
                        if len(block) >= 5:  # Valid block format
                            bbox = block[:4]
                            text = block[4] if len(block) > 4 else ""
                            layout_block = LayoutBlock(
                                block_type="text",
                                bounding_box=bbox,
                                z_order=0,
                                reading_sequence=idx,
                                content=text
                            )
                            blocks.append(layout_block)
                    
                    # Extract images
                    image_list = page.get_images()
                    for idx, img in enumerate(image_list):
                        try:
                            img_rects = page.get_image_bbox(img[7])
                            layout_block = LayoutBlock(
                                block_type="image",
                                bounding_box=(img_rects.x0, img_rects.y0, img_rects.x1, img_rects.y1),
                                z_order=1,
                                reading_sequence=len(blocks) + idx,
                                metadata={"image_index": img[0]}
                            )
                            blocks.append(layout_block)
                        except Exception:
                            pass
                    
                    layout_blocks_per_page.append(blocks)
                
                doc.close()
            else:
                # Fallback: minimal layout
                for _ in metadata:
                    layout_blocks_per_page.append([])
                    
        except Exception as e:
            logger.error(f"Error parsing layout: {e}")
            # Return empty layout
            layout_blocks_per_page = [[] for _ in metadata]
        
        return layout_blocks_per_page, tables, logos
    
    def _generate_processing_notes(
        self,
        nature: DocumentNature,
        category: DocumentCategory,
        metadata: List[StructuralMetadata],
        requires_ocr: bool
    ) -> List[str]:
        """Generate processing notes for audit trail."""
        notes = []
        
        notes.append(f"Document nature: {nature.value}")
        notes.append(f"Document category: {category.value}")
        notes.append(f"Pages analyzed: {len(metadata)}")
        
        if requires_ocr:
            notes.append("OCR processing required")
        
        total_tables = sum(1 for meta in metadata if meta.has_tables)
        if total_tables > 0:
            notes.append(f"Tables detected: {total_tables} pages")
        
        total_images = sum(meta.image_count for meta in metadata)
        if total_images > 0:
            notes.append(f"Images detected: {total_images}")
        
        return notes


# Global instance
_document_intelligence_pipeline = None

def get_document_intelligence_pipeline() -> DocumentIntelligencePipeline:
    """Get or create global document intelligence pipeline instance."""
    global _document_intelligence_pipeline
    if _document_intelligence_pipeline is None:
        _document_intelligence_pipeline = DocumentIntelligencePipeline()
    return _document_intelligence_pipeline

