# Premium Layout System

## Overview

The Premium Layout System provides enhanced PDF-to-Excel/Word conversion by separating Document AI extraction from heuristic layout inference. This system intelligently handles documents that don't have native table structures detected by Document AI.

## Architecture

```
Document AI Processing
    ↓
Extract Native Tables + Parsed Tables
    ↓
Premium Layout System (if available)
    ├─→ Document Type Classification
    ├─→ Layout Decision (Native vs Heuristic)
    ├─→ Heuristic Table Building (if needed)
    └─→ Unified Layout Model
    ↓
Excel/Word Rendering
    ↓
Fallback to Standard Method (if premium fails)
```

## Components

### 1. `unified_layout_model.py`
- Standard layout structure (Cell, CellStyle, UnifiedLayout)
- Supports merged cells, styling, and metadata
- Platform-agnostic representation

### 2. `document_type_classifier.py`
- Classifies documents into types:
  - Invoice, Bank Statement, Bill
  - Resume, Certificate, ID Card
  - Letter, Office Document
  - Digital PDF, OCR Image
  - Unknown
- Uses keyword matching and table detection

### 3. `heuristic_table_builder.py`
- Builds tables from text + bounding boxes
- Document-type-specific handlers
- Multiple fallback methods:
  1. Paragraphs with layouts (preferred)
  2. Tokens (fallback)
  3. Line-based extraction (last resort)

### 4. `layout_decision_engine.py`
- Decides: native tables vs heuristic
- Converts native tables to unified layout
- Falls back to heuristic if no native tables

### 5. `excel_word_renderer.py`
- Renders unified layout to Excel (openpyxl)
- Renders unified layout to Word (python-docx, optional)
- Preserves Unicode, applies borders/spacing

## Integration

The system is integrated via a **safe hook** in `docai_service.py` (lines 213-238):

- Tries premium layout system first
- Falls back gracefully if unavailable or fails
- Preserves existing functionality
- No breaking changes

## Features

### Document Type Support

- **Resume** → Key-value table format
- **Certificate** → Structured fields with headers
- **ID Card** → Compact key-value layout
- **Invoice/Bank/Bill** → Table-like structure with columns
- **Letter** → Paragraph-based format
- **Office Documents** → Generic table structure

### Robustness

- Multiple text extraction methods
- Unicode preservation
- Graceful error handling
- Automatic fallback to standard method

## Usage

The system is automatically used for PREMIUM conversions. No manual configuration needed.

## Logging

The system logs:
- Document classification results
- Layout decision (native vs heuristic)
- Text block extraction counts
- Any fallback scenarios

## Dependencies

- `openpyxl` (required for Excel)
- `python-docx` (optional, for Word export)
- Google Cloud Document AI (required)

## Testing

To test the system:
1. Upload a PDF (resume, invoice, certificate, etc.)
2. Check Cloud Run logs for premium layout system messages
3. Verify Excel output has structured data

## Future Enhancements

- Image extraction and placement
- Advanced layout detection algorithms
- Custom document type templates
- Multi-language support improvements

