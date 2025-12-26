"""
LibreOffice Converter for FREE PDF to Excel Pipeline.
Uses LibreOffice for high-quality conversion with Python fallback.
"""

import os
import io
import logging
import tempfile
import subprocess
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Feature flag for LibreOffice integration
LIBREOFFICE_ENABLED = True  # Set to False to disable LibreOffice and use Python only


def convert_with_libreoffice(pdf_bytes: bytes, output_path: str) -> Tuple[bool, Optional[str]]:
    """
    Convert PDF to Excel using LibreOffice.
    
    Args:
        pdf_bytes: PDF file content
        output_path: Path to save Excel file
        
    Returns:
        (success, error_message)
        - success: True if conversion successful, False otherwise
        - error_message: Error message if failed, None if success
    """
    if not LIBREOFFICE_ENABLED:
        return False, "LibreOffice integration disabled"
    
    # Check if LibreOffice is available
    soffice_path = _find_libreoffice()
    if not soffice_path:
        return False, "LibreOffice not found in system PATH"
    
    temp_pdf_path = None
    temp_output_dir = None
    
    try:
        # Create temporary PDF file
        temp_pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf_path = temp_pdf_file.name
        temp_pdf_file.write(pdf_bytes)
        temp_pdf_file.close()
        
        # Create temporary output directory
        temp_output_dir = tempfile.mkdtemp()
        
        # Run LibreOffice conversion
        # soffice --headless --convert-to xlsx --outdir <output_dir> <input_file>
        cmd = [
            soffice_path,
            '--headless',
            '--nodefault',
            '--nolockcheck',
            '--convert-to', 'xlsx',
            '--outdir', temp_output_dir,
            temp_pdf_path
        ]
        
        logger.info(f"Running LibreOffice conversion: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
            cwd=temp_output_dir
        )
        
        if result.returncode != 0:
            logger.warning(f"LibreOffice conversion failed: {result.stderr}")
            return False, f"LibreOffice conversion failed: {result.stderr[:200]}"
        
        # Find generated Excel file
        pdf_name = Path(temp_pdf_path).stem
        expected_xlsx = os.path.join(temp_output_dir, f"{pdf_name}.xlsx")
        
        if not os.path.exists(expected_xlsx):
            # Try to find any .xlsx file in output directory
            xlsx_files = list(Path(temp_output_dir).glob("*.xlsx"))
            if xlsx_files:
                expected_xlsx = str(xlsx_files[0])
            else:
                return False, "LibreOffice did not generate Excel file"
        
        # Copy to final output path
        import shutil
        shutil.copy2(expected_xlsx, output_path)
        
        logger.info(f"✅ LibreOffice conversion successful: {output_path}")
        return True, None
        
    except subprocess.TimeoutExpired:
        return False, "LibreOffice conversion timed out"
    except Exception as e:
        logger.error(f"Error in LibreOffice conversion: {e}")
        return False, f"LibreOffice error: {str(e)[:200]}"
    finally:
        # Cleanup temporary files
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.unlink(temp_pdf_path)
            except:
                pass
        if temp_output_dir and os.path.exists(temp_output_dir):
            try:
                import shutil
                shutil.rmtree(temp_output_dir)
            except:
                pass


def _find_libreoffice() -> Optional[str]:
    """
    Find LibreOffice soffice executable in system PATH.
    
    Returns:
        Path to soffice executable, or None if not found
    """
    # Common paths for LibreOffice
    common_paths = [
        'soffice',  # In PATH
        '/usr/bin/soffice',  # Linux
        '/usr/local/bin/soffice',  # Linux (local)
        'C:\\Program Files\\LibreOffice\\program\\soffice.exe',  # Windows
        'C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe',  # Windows 32-bit
    ]
    
    for path in common_paths:
        try:
            # Check if executable exists
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
            
            # Try to find in PATH
            result = subprocess.run(
                ['which', path] if os.name != 'nt' else ['where', path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                found_path = result.stdout.strip().split('\n')[0]
                if os.path.isfile(found_path):
                    return found_path
        except:
            continue
    
    # Try to find using 'which' or 'where' command
    try:
        cmd = 'which soffice' if os.name != 'nt' else 'where soffice'
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            found_path = result.stdout.strip().split('\n')[0]
            if os.path.isfile(found_path):
                return found_path
    except:
        pass
    
    return None


def is_libreoffice_available() -> bool:
    """
    Check if LibreOffice is available in the system.
    
    Returns:
        True if LibreOffice is available, False otherwise
    """
    return _find_libreoffice() is not None

