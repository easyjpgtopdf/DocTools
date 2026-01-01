"""
Local PDF to Word Conversion Test Script
Tests all PDFs locally using LibreOffice directly (without API)
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import time

# Configuration
TEST_FOLDER = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"
OUTPUT_FOLDER = os.path.join(TEST_FOLDER, "converted_outputs")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Test results file
RESULTS_FILE = os.path.join(OUTPUT_FOLDER, f"test_results_local_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

def log_result(message, to_file=True, to_console=True):
    """Log message to both file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    
    if to_file:
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg)
    if to_console:
        print(message)

def find_soffice_binary():
    """Find LibreOffice soffice binary"""
    # Common paths on Windows
    common_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        r"C:\Program Files\LibreOffice 7\program\soffice.exe",
    ]
    
    # Check PATH
    soffice = shutil.which("soffice")
    if soffice:
        return soffice
    
    # Check common paths
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

def convert_pdf_to_word_local(pdf_path, output_dir):
    """Convert PDF to Word using LibreOffice locally"""
    pdf_name = os.path.basename(pdf_path)
    log_result(f"\n{'='*80}")
    log_result(f"Testing: {pdf_name}")
    log_result(f"{'='*80}")
    
    try:
        # Check file size
        file_size = os.path.getsize(pdf_path)
        file_size_mb = file_size / (1024 * 1024)
        log_result(f"File size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        
        # Find LibreOffice
        soffice_path = find_soffice_binary()
        if not soffice_path:
            error_msg = "LibreOffice not found. Please install LibreOffice."
            log_result(f"❌ {error_msg}")
            return {
                'status': 'error',
                'pdf': pdf_name,
                'error': error_msg
            }
        
        log_result(f"Using LibreOffice: {soffice_path}")
        
        # Prepare output path
        output_filename = os.path.splitext(pdf_name)[0] + ".docx"
        output_path = os.path.join(output_dir, output_filename)
        
        # Convert using LibreOffice
        # soffice --headless --convert-to docx --outdir <output_dir> <input_pdf>
        log_result(f"Converting to: {output_path}")
        start_time = time.time()
        
        cmd = [
            soffice_path,
            "--headless",
            "--convert-to", "docx",
            "--outdir", output_dir,
            pdf_path
        ]
        
        log_result(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            encoding='utf-8',
            errors='ignore'
        )
        
        elapsed_time = time.time() - start_time
        
        # Check if output file was created
        expected_output = os.path.join(output_dir, output_filename)
        if os.path.exists(expected_output):
            output_size = os.path.getsize(expected_output)
            log_result(f"✅ Conversion successful!")
            log_result(f"   Output: {expected_output}")
            log_result(f"   Output size: {output_size:,} bytes ({output_size/(1024*1024):.2f} MB)")
            log_result(f"   Conversion time: {elapsed_time:.2f} seconds")
            
            return {
                'status': 'success',
                'pdf': pdf_name,
                'output': output_filename,
                'file_size_mb': file_size_mb,
                'output_size_mb': output_size/(1024*1024),
                'conversion_time': elapsed_time,
                'error': None
            }
        else:
            error_msg = f"Output file not created. Return code: {result.returncode}"
            if result.stderr:
                error_msg += f"\n   Error: {result.stderr[:500]}"
            if result.stdout:
                error_msg += f"\n   Output: {result.stdout[:500]}"
            
            log_result(f"❌ Conversion failed!")
            log_result(f"   {error_msg}")
            
            return {
                'status': 'failed',
                'pdf': pdf_name,
                'return_code': result.returncode,
                'error': error_msg[:500]
            }
    
    except subprocess.TimeoutExpired:
        error_msg = "Conversion timeout (file may be too large)"
        log_result(f"❌ {error_msg}")
        return {
            'status': 'timeout',
            'pdf': pdf_name,
            'error': error_msg
        }
    except Exception as e:
        error_msg = str(e)
        log_result(f"❌ Exception during conversion: {error_msg}")
        import traceback
        log_result(f"   Traceback: {traceback.format_exc()}")
        return {
            'status': 'exception',
            'pdf': pdf_name,
            'error': error_msg
        }

def main():
    """Main test function"""
    log_result("="*80)
    log_result("LOCAL PDF TO WORD CONVERSION TEST SUITE")
    log_result("="*80)
    log_result(f"Test folder: {TEST_FOLDER}")
    log_result(f"Output folder: {OUTPUT_FOLDER}")
    log_result(f"Results file: {RESULTS_FILE}")
    log_result("="*80)
    
    # Check LibreOffice
    log_result("\n[STEP 1] Checking LibreOffice installation...")
    soffice_path = find_soffice_binary()
    if not soffice_path:
        log_result("❌ LibreOffice not found!")
        log_result("   Please install LibreOffice from https://www.libreoffice.org/")
        return 1
    
    log_result(f"✅ LibreOffice found: {soffice_path}")
    
    # Find all PDF files
    log_result("\n[STEP 2] Scanning for PDF files...")
    pdf_files = []
    if os.path.exists(TEST_FOLDER):
        for file in os.listdir(TEST_FOLDER):
            if file.lower().endswith('.pdf') and os.path.isfile(os.path.join(TEST_FOLDER, file)):
                pdf_files.append(os.path.join(TEST_FOLDER, file))
    
    if not pdf_files:
        log_result("❌ No PDF files found in test folder!")
        return 1
    
    log_result(f"✅ Found {len(pdf_files)} PDF file(s)")
    for i, pdf in enumerate(pdf_files, 1):
        log_result(f"   {i}. {os.path.basename(pdf)}")
    
    # Test each PDF
    log_result("\n[STEP 3] Starting conversion tests...")
    results = []
    total = len(pdf_files)
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        log_result(f"\n[{idx}/{total}] Processing...")
        result = convert_pdf_to_word_local(pdf_path, OUTPUT_FOLDER)
        results.append(result)
        
        # Small delay between conversions
        if idx < total:
            time.sleep(1)
    
    # Summary
    log_result("\n" + "="*80)
    log_result("TEST SUMMARY")
    log_result("="*80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] != 'success')
    
    log_result(f"\nTotal PDFs tested: {total}")
    log_result(f"✅ Successful: {success_count}")
    log_result(f"❌ Failed: {failed_count}")
    log_result(f"Success rate: {(success_count/total*100):.1f}%")
    
    # Detailed breakdown
    log_result("\nDetailed Results:")
    status_counts = {}
    for result in results:
        status = result['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        log_result(f"   {status}: {count}")
    
    # List failed files
    failed_files = [r for r in results if r['status'] != 'success']
    if failed_files:
        log_result("\n❌ Failed Files:")
        for result in failed_files:
            log_result(f"   - {result['pdf']}: {result.get('error', 'Unknown error')[:100]}")
    
    # List successful files
    successful_files = [r for r in results if r['status'] == 'success']
    if successful_files:
        log_result("\n✅ Successful Conversions:")
        for result in successful_files:
            log_result(f"   - {result['pdf']} → {result['output']} ({result.get('conversion_time', 0):.2f}s)")
    
    log_result("\n" + "="*80)
    log_result(f"Results saved to: {RESULTS_FILE}")
    log_result("="*80)
    
    # Save JSON summary
    import json
    json_summary = {
        'timestamp': datetime.now().isoformat(),
        'total_tested': total,
        'successful': success_count,
        'failed': failed_count,
        'success_rate': success_count/total*100 if total > 0 else 0,
        'results': results
    }
    
    json_file = RESULTS_FILE.replace('.txt', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_summary, f, indent=2, ensure_ascii=False)
    
    log_result(f"JSON summary saved to: {json_file}")
    
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    try:
        # Set console encoding for Windows
        if os.name == 'nt':
            os.system('chcp 65001 >nul 2>&1')
        
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log_result("\n\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        log_result(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        log_result(traceback.format_exc())
        sys.exit(1)

