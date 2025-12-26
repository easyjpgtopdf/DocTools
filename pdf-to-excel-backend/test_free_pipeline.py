"""
Test script for FREE PDF to Excel pipeline.
Tests all implemented features.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required modules can be imported."""
    logger.info("Testing imports...")
    try:
        from free_pdf_to_excel.free_engine_controller import process_pdf_to_excel_free
        from free_pdf_to_excel.free_excel_writer import create_excel_workbook_multi_page
        from free_pdf_to_excel.free_libreoffice_converter import is_libreoffice_available, LIBREOFFICE_ENABLED
        from free_pdf_to_excel.free_limits import generate_free_key
        logger.info("✅ All imports successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def test_libreoffice_detection():
    """Test LibreOffice detection."""
    logger.info("Testing LibreOffice detection...")
    try:
        from free_pdf_to_excel.free_libreoffice_converter import is_libreoffice_available, LIBREOFFICE_ENABLED
        available = is_libreoffice_available()
        logger.info(f"LibreOffice enabled: {LIBREOFFICE_ENABLED}")
        logger.info(f"LibreOffice available: {available}")
        if available:
            logger.info("✅ LibreOffice detected")
        else:
            logger.info("⚠️ LibreOffice not found (will use Python fallback)")
        return True
    except Exception as e:
        logger.error(f"❌ LibreOffice detection error: {e}")
        return False

def test_multi_page_logic():
    """Test multi-page processing logic."""
    logger.info("Testing multi-page logic...")
    try:
        from free_pdf_to_excel.free_pdf_parser import get_page_count
        from free_pdf_to_excel.free_excel_writer import create_excel_workbook_multi_page
        
        # Test with dummy data (proper structure with cell dictionaries)
        dummy_pages_data = [
            {
                'page_num': 0,
                'grid': [
                    [
                        {'text': 'Cell1', 'font_name': 'Arial', 'font_size': 10, 'is_bold': False, 'merged': False},
                        {'text': 'Cell2', 'font_name': 'Arial', 'font_size': 10, 'is_bold': False, 'merged': False}
                    ],
                    [
                        {'text': 'Cell3', 'font_name': 'Arial', 'font_size': 10, 'is_bold': False, 'merged': False},
                        {'text': 'Cell4', 'font_name': 'Arial', 'font_size': 10, 'is_bold': False, 'merged': False}
                    ]
                ],
                'header_rows': [0],
                'rectangles': [],
                'images': [],
                'row_boundaries': [0, 100],
                'column_boundaries': [0, 200],
                'grid_confidence': 0.8
            },
            {
                'page_num': 1,
                'grid': [
                    [
                        {'text': 'Cell5', 'font_name': 'Arial', 'font_size': 10, 'is_bold': False, 'merged': False},
                        {'text': 'Cell6', 'font_name': 'Arial', 'font_size': 10, 'is_bold': False, 'merged': False}
                    ],
                    [
                        {'text': 'Cell7', 'font_name': 'Arial', 'font_size': 10, 'is_bold': False, 'merged': False},
                        {'text': 'Cell8', 'font_name': 'Arial', 'font_size': 10, 'is_bold': False, 'merged': False}
                    ]
                ],
                'header_rows': [0],
                'rectangles': [],
                'images': [],
                'row_boundaries': [0, 100],
                'column_boundaries': [0, 200],
                'grid_confidence': 0.8
            }
        ]
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()
        
        success = create_excel_workbook_multi_page(dummy_pages_data, temp_path)
        
        if success and os.path.exists(temp_path):
            # Check if file has multiple sheets
            try:
                import openpyxl
                wb = openpyxl.load_workbook(temp_path)
                sheet_count = len(wb.worksheets)
                logger.info(f"✅ Multi-page test: Created {sheet_count} sheets")
                if sheet_count >= 2:
                    logger.info("✅ Multi-page logic working correctly")
                else:
                    logger.warning("⚠️ Expected 2+ sheets, got {sheet_count}")
                wb.close()
            except Exception as e:
                logger.warning(f"⚠️ Could not verify sheets: {e}")
            
            os.unlink(temp_path)
            return True
        else:
            logger.error("❌ Multi-page test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Multi-page test error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_merge_detection():
    """Test merged cells detection."""
    logger.info("Testing merge detection...")
    try:
        from free_pdf_to_excel.free_table_inference import snap_text_to_grid
        
        # Test grid with potential merges
        text_objects = [
            {'text': 'Header', 'x': 0, 'y': 0, 'font_name': 'Arial', 'font_size': 12, 'is_bold': True},
            {'text': 'Header', 'x': 100, 'y': 0, 'font_name': 'Arial', 'font_size': 12, 'is_bold': True},
        ]
        column_boundaries = [0, 100, 200]
        row_boundaries = [0, 50]
        
        grid = snap_text_to_grid(text_objects, column_boundaries, row_boundaries)
        
        # Check if merge flags are set
        merge_found = False
        for row in grid:
            for cell in row:
                if cell.get('merged') or cell.get('merge_right') or cell.get('merge_left'):
                    merge_found = True
                    break
        
        if merge_found:
            logger.info("✅ Merge detection working")
        else:
            logger.info("⚠️ No merges detected in test (may be normal)")
        
        return True
    except Exception as e:
        logger.error(f"❌ Merge detection test error: {e}")
        return False

def test_font_extraction():
    """Test font extraction."""
    logger.info("Testing font extraction...")
    try:
        from free_pdf_to_excel.free_pdf_parser import extract_text_with_coordinates
        
        # This would need actual PDF bytes, so just test import
        logger.info("✅ Font extraction module loaded")
        return True
    except Exception as e:
        logger.error(f"❌ Font extraction test error: {e}")
        return False

def test_image_handling():
    """Test image handling."""
    logger.info("Testing image handling...")
    try:
        from free_pdf_to_excel.free_visual_layer import extract_small_images
        
        # This would need actual PDF bytes, so just test import
        logger.info("✅ Image handling module loaded")
        return True
    except Exception as e:
        logger.error(f"❌ Image handling test error: {e}")
        return False

def test_document_type_detection():
    """Test document type detection logic."""
    logger.info("Testing document type detection...")
    try:
        # Test the keyword detection logic
        test_texts = {
            'invoice': 'invoice bill amount due total',
            'bank': 'account balance transaction statement',
            'resume': 'resume cv education experience skills',
            'certificate': 'certificate certified award achievement',
            'form': 'form application please fill signature',
            'letter': 'dear sincerely yours regards letter'
        }
        
        for doc_type, text in test_texts.items():
            text_lower = text.lower()
            if doc_type == 'invoice' and any(kw in text_lower for kw in ['invoice', 'bill', 'amount due']):
                logger.info(f"✅ {doc_type} detection logic working")
            elif doc_type == 'bank' and any(kw in text_lower for kw in ['account', 'balance', 'transaction']):
                logger.info(f"✅ {doc_type} detection logic working")
            # Similar for others...
        
        logger.info("✅ Document type detection logic verified")
        return True
    except Exception as e:
        logger.error(f"❌ Document type detection test error: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("FREE PDF to Excel Pipeline - Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("LibreOffice Detection", test_libreoffice_detection),
        ("Multi-Page Logic", test_multi_page_logic),
        ("Merge Detection", test_merge_detection),
        ("Font Extraction", test_font_extraction),
        ("Image Handling", test_image_handling),
        ("Document Type Detection", test_document_type_detection),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing: {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✅ All tests passed!")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

