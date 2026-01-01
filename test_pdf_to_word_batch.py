#!/usr/bin/env python3
"""
Batch Test Script for PDF to Word Conversion
Tests all PDFs in the "Pdf Word" folder using LibreOffice directly
Saves outputs in the same folder
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path
from typing import List, Dict

# Test folder
TEST_FOLDER = Path(__file__).parent / "Pdf Word"
OUTPUT_SUBFOLDER = TEST_FOLDER / "converted_outputs"

def check_libreoffice() -> str:
    """Check if LibreOffice is available and return the path."""
    # Check common locations
    soffice_paths = [
        "soffice",  # In PATH
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
        "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
    ]
    
    for path in soffice_paths:
        if path == "soffice":
            # Check if it's in PATH
            soffice_bin = shutil.which("soffice")
            if soffice_bin:
                return soffice_bin
        elif os.path.exists(path):
            return path
    
    return None

def get_pdf_files(folder: Path) -> List[Path]:
    """Get all PDF files from the folder."""
    pdf_files = list(folder.glob("*.pdf"))
    return sorted(pdf_files)

def test_pdf_conversion(pdf_path: Path, output_dir: Path, soffice_path: str) -> Dict[str, any]:
    """
    Test PDF to Word conversion using LibreOffice directly.
    Returns result dictionary with status and details.
    """
    result = {
        "pdf_file": pdf_path.name,
        "status": "pending",
        "output_file": None,
        "error": None,
        "time_taken": None
    }
    
    try:
        start_time = time.time()
        
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build LibreOffice command (use writer6 format for docx)
        cmd = [
            soffice_path,
            "--headless",
            "--nologo",
            "--nodefault",
            "--nolockcheck",
            "--norestore",
            "--convert-to", "docx:writer6",
            "--outdir", str(output_dir),
            str(pdf_path)
        ]
        
        # Run LibreOffice conversion
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=90
        )
        
        # Check for output file (LibreOffice creates files in output_dir)
        # Search for any .docx file that matches the PDF name (stem)
        docx_files = list(output_dir.glob(f"{pdf_path.stem}*.docx"))
        
        # Also check for exact match
        expected_output = output_dir / f"{pdf_path.stem}.docx"
        if expected_output.exists():
            docx_files.append(expected_output)
        
        # Remove duplicates
        docx_files = list(set(docx_files))
        
        if proc.returncode == 0 and docx_files:
            # Use the first matching docx file
            output_file = docx_files[0]
            result["status"] = "success"
            result["output_file"] = output_file.name
            result["time_taken"] = f"{time.time() - start_time:.2f}s"
            
            # Get file sizes
            pdf_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
            docx_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            result["pdf_size_mb"] = f"{pdf_size:.2f}"
            result["docx_size_mb"] = f"{docx_size:.2f}"
        else:
            result["status"] = "error"
            error_msg = f"Return code: {proc.returncode}"
            if proc.stderr:
                error_msg += f", Error: {proc.stderr[:200]}"
            result["error"] = error_msg
            result["time_taken"] = f"{time.time() - start_time:.2f}s"
            
    except subprocess.TimeoutExpired:
        result["status"] = "error"
        result["error"] = "Conversion timed out after 90 seconds"
        result["time_taken"] = f"{time.time() - start_time:.2f}s"
    except FileNotFoundError:
        result["status"] = "error"
        result["error"] = f"LibreOffice not found at: {soffice_path}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["time_taken"] = f"{time.time() - start_time:.2f}s" if 'start_time' in locals() else "N/A"
    
    return result

def main():
    """Main test function."""
    print("=" * 80)
    print("PDF to Word Batch Conversion Test (LibreOffice)")
    print("=" * 80)
    print(f"\nTest Folder: {TEST_FOLDER}")
    print(f"Output Folder: {OUTPUT_SUBFOLDER}\n")
    
    # Check if test folder exists
    if not TEST_FOLDER.exists():
        print(f"ERROR: Test folder not found: {TEST_FOLDER}")
        return 1
    
    # Check for LibreOffice
    soffice_path = check_libreoffice()
    if not soffice_path:
        print("ERROR: LibreOffice (soffice) not found!")
        print("\nPlease install LibreOffice:")
        print("  Windows: https://www.libreoffice.org/download/")
        print("  Linux: sudo apt-get install libreoffice-writer")
        print("  Mac: brew install --cask libreoffice")
        return 1
    
    print(f"[OK] LibreOffice found: {soffice_path}\n")
    
    # Get all PDF files
    pdf_files = get_pdf_files(TEST_FOLDER)
    
    if not pdf_files:
        print(f"No PDF files found in {TEST_FOLDER}")
        return 1
    
    print(f"Found {len(pdf_files)} PDF file(s) to test:\n")
    for i, pdf_file in enumerate(pdf_files, 1):
        size_mb = os.path.getsize(pdf_file) / (1024 * 1024)
        try:
            print(f"  {i}. {pdf_file.name} ({size_mb:.2f} MB)")
        except UnicodeEncodeError:
            # Fallback for non-ASCII characters
            safe_name = pdf_file.name.encode('ascii', 'replace').decode('ascii')
            print(f"  {i}. {safe_name} ({size_mb:.2f} MB)")
    
    print("\n" + "=" * 80)
    print("Starting Conversion Tests...")
    print("=" * 80 + "\n")
    
    # Create output directory
    OUTPUT_SUBFOLDER.mkdir(parents=True, exist_ok=True)
    
    # Test results
    results = []
    success_count = 0
    error_count = 0
    
    # Test each PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            print(f"[{i}/{len(pdf_files)}] Testing: {pdf_file.name}")
        except UnicodeEncodeError:
            safe_name = pdf_file.name.encode('ascii', 'replace').decode('ascii')
            print(f"[{i}/{len(pdf_files)}] Testing: {safe_name}")
        print("-" * 80)
        
        result = test_pdf_conversion(pdf_file, OUTPUT_SUBFOLDER, soffice_path)
        results.append(result)
        
        if result["status"] == "success":
            success_count += 1
            print(f"[SUCCESS]")
            print(f"   Output: {result['output_file']}")
            print(f"   Time: {result['time_taken']}")
            print(f"   PDF Size: {result.get('pdf_size_mb', 'N/A')} MB")
            print(f"   DOCX Size: {result.get('docx_size_mb', 'N/A')} MB")
        else:
            error_count += 1
            print(f"[ERROR]")
            print(f"   Error: {result['error']}")
            print(f"   Time: {result['time_taken']}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total PDFs: {len(pdf_files)}")
    print(f"[OK] Successful: {success_count}")
    print(f"[ERROR] Failed: {error_count}")
    print(f"Success Rate: {(success_count/len(pdf_files)*100):.1f}%")
    print()
    
    # Detailed results
    if error_count > 0:
        print("FAILED CONVERSIONS:")
        print("-" * 80)
        for result in results:
            if result["status"] == "error":
                print(f"  [X] {result['pdf_file']}")
                print(f"     Error: {result['error']}")
        print()
    
    # Save results to file
    results_file = OUTPUT_SUBFOLDER / "test_results.txt"
    with open(results_file, "w", encoding="utf-8") as f:
        f.write("PDF to Word Conversion Test Results (LibreOffice)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"LibreOffice Path: {soffice_path}\n")
        f.write(f"Total PDFs: {len(pdf_files)}\n")
        f.write(f"Successful: {success_count}\n")
        f.write(f"Failed: {error_count}\n")
        f.write(f"Success Rate: {(success_count/len(pdf_files)*100):.1f}%\n\n")
        
        f.write("DETAILED RESULTS:\n")
        f.write("-" * 80 + "\n\n")
        for result in results:
            f.write(f"PDF: {result['pdf_file']}\n")
            f.write(f"Status: {result['status'].upper()}\n")
            if result['status'] == "success":
                f.write(f"Output: {result['output_file']}\n")
                f.write(f"Time: {result['time_taken']}\n")
                if 'pdf_size_mb' in result:
                    f.write(f"PDF Size: {result['pdf_size_mb']} MB\n")
                    f.write(f"DOCX Size: {result['docx_size_mb']} MB\n")
            else:
                f.write(f"Error: {result['error']}\n")
            f.write("\n")
    
    print(f"[INFO] Detailed results saved to: {results_file}")
    print(f"[INFO] Output files saved to: {OUTPUT_SUBFOLDER}")
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
