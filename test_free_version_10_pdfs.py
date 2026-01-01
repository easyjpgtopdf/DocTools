"""
Test Free Version Pipeline with 10 PDFs (1 page only per PDF)
Extracts first page from each PDF and tests conversion
"""
import os
import sys
import requests
import json
from pathlib import Path
from datetime import datetime
import time
import subprocess
import shutil

# Configuration
TEST_FOLDER = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"
OUTPUT_FOLDER = TEST_FOLDER
TEMP_FOLDER = os.path.join(TEST_FOLDER, "temp_single_pages")
API_BASE_URL = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app"
API_ENDPOINT = f"{API_BASE_URL}/api/convert/pdf-to-word"

# Create temp folder for single-page PDFs
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Results file
RESULTS_FILE = os.path.join(OUTPUT_FOLDER, f"test_free_version_10_pdfs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

def log_result(message, to_file=True, to_console=True):
    """Log message to both file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    
    if to_file:
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg)
    if to_console:
        print(message)

def find_pdftk():
    """Find pdftk or use PyPDF2 to extract first page"""
    # Try pdftk first (better for PDF manipulation)
    pdftk = shutil.which("pdftk")
    if pdftk:
        return "pdftk", pdftk
    
    # Fall back to PyPDF2 (Python library)
    try:
        import PyPDF2
        return "pypdf2", None
    except ImportError:
        return None, None

def extract_first_page_pypdf2(pdf_path, output_path):
    """Extract first page using PyPDF2"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as input_file:
            pdf_reader = PyPDF2.PdfReader(input_file)
            if len(pdf_reader.pages) == 0:
                raise Exception("PDF has no pages")
            
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[0])
            
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
        
        return True
    except Exception as e:
        log_result(f"   PyPDF2 extraction error: {str(e)}")
        return False

def extract_first_page(pdf_path, output_path):
    """Extract first page from PDF"""
    tool_type, tool_path = find_pdftk()
    
    if tool_type == "pdftk":
        # Use pdftk
        try:
            result = subprocess.run(
                [tool_path, pdf_path, "cat", "1", "output", output_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and os.path.exists(output_path):
                return True
            else:
                log_result(f"   pdftk error: {result.stderr}")
                return False
        except Exception as e:
            log_result(f"   pdftk exception: {str(e)}")
            return False
    elif tool_type == "pypdf2":
        # Use PyPDF2
        return extract_first_page_pypdf2(pdf_path, output_path)
    else:
        log_result("   No PDF extraction tool available (need pdftk or PyPDF2)")
        return False

def convert_pdf_to_word(pdf_path, original_name):
    """Convert a single PDF to Word using the API"""
    pdf_name = os.path.basename(pdf_path)
    log_result(f"\n{'='*80}")
    log_result(f"Testing: {original_name} (first page only)")
    log_result(f"{'='*80}")
    
    try:
        file_size = os.path.getsize(pdf_path)
        file_size_mb = file_size / (1024 * 1024)
        log_result(f"File size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_name, f, 'application/pdf')}
            log_result(f"Uploading to API...")
            start_time = time.time()
            
            response = requests.post(
                API_ENDPOINT,
                files=files,
                timeout=300
            )
            
            elapsed_time = time.time() - start_time
            log_result(f"API response time: {elapsed_time:.2f} seconds")
            log_result(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                log_result(f"✅ Conversion successful!")
                log_result(f"   Job ID: {result.get('job_id', 'N/A')}")
                log_result(f"   Pages: {result.get('pages', 'N/A')}")
                log_result(f"   Method: {result.get('primary_method', 'N/A')}")
                
                # Download the converted file
                if 'primary_download_url' in result:
                    download_url = result['primary_download_url']
                    log_result(f"   Download URL: {download_url}")
                    
                    docx_response = requests.get(download_url, timeout=60)
                    if docx_response.status_code == 200:
                        # Save with original name prefix
                        output_filename = os.path.splitext(original_name)[0] + "_page1.docx"
                        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                        
                        with open(output_path, 'wb') as out_file:
                            out_file.write(docx_response.content)
                        
                        output_size = os.path.getsize(output_path)
                        log_result(f"✅ Downloaded and saved: {output_filename}")
                        log_result(f"   Output size: {output_size:,} bytes ({output_size/(1024*1024):.2f} MB)")
                        
                        return {
                            'status': 'success',
                            'pdf': original_name,
                            'output': output_filename,
                            'file_size_mb': file_size_mb,
                            'output_size_mb': output_size/(1024*1024),
                            'response_time': elapsed_time,
                            'job_id': result.get('job_id', 'N/A'),
                            'pages': result.get('pages', 'N/A'),
                            'method': result.get('primary_method', 'N/A'),
                            'error': None
                        }
                    else:
                        log_result(f"❌ Failed to download converted file: Status {docx_response.status_code}")
                        return {
                            'status': 'download_failed',
                            'pdf': original_name,
                            'error': f"Download failed: {docx_response.status_code}"
                        }
                else:
                    log_result(f"⚠️ Conversion response missing downloadUrl")
                    return {
                        'status': 'no_url',
                        'pdf': original_name,
                        'error': 'Response missing downloadUrl'
                    }
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(error_data))
                    if isinstance(error_detail, dict):
                        error_detail = error_detail.get('message', str(error_detail))
                except:
                    error_detail = response.text[:500]
                
                log_result(f"❌ Conversion failed!")
                log_result(f"   Status: {response.status_code}")
                log_result(f"   Error: {error_detail}")
                
                return {
                    'status': 'failed',
                    'pdf': original_name,
                    'status_code': response.status_code,
                    'error': str(error_detail)[:200]
                }
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout"
        log_result(f"❌ {error_msg}")
        return {
            'status': 'timeout',
            'pdf': original_name,
            'error': error_msg
        }
    except Exception as e:
        error_msg = str(e)
        log_result(f"❌ Exception during conversion: {error_msg}")
        import traceback
        log_result(f"   Traceback: {traceback.format_exc()}")
        return {
            'status': 'exception',
            'pdf': original_name,
            'error': error_msg
        }

def main():
    """Main test function"""
    log_result("="*80)
    log_result("FREE VERSION PIPELINE TEST - 10 PDFs (First Page Only)")
    log_result("="*80)
    log_result(f"Test folder: {TEST_FOLDER}")
    log_result(f"Output folder: {OUTPUT_FOLDER}")
    log_result(f"Temp folder: {TEMP_FOLDER}")
    log_result(f"API endpoint: {API_ENDPOINT}")
    log_result(f"Results file: {RESULTS_FILE}")
    log_result("="*80)
    
    # Check for PDF extraction tool
    tool_type, tool_path = find_pdftk()
    if tool_type:
        log_result(f"\n✅ PDF extraction tool found: {tool_type}")
    else:
        log_result(f"\n⚠️ No PDF extraction tool found. Trying to install PyPDF2...")
        try:
            import PyPDF2
            log_result("✅ PyPDF2 is available")
        except ImportError:
            log_result("❌ PyPDF2 not available. Please install: pip install PyPDF2")
            return 1
    
    # Find all PDF files and select 10
    log_result("\n[STEP 1] Scanning for PDF files...")
    pdf_files = []
    if os.path.exists(TEST_FOLDER):
        for file in os.listdir(TEST_FOLDER):
            if file.lower().endswith('.pdf') and os.path.isfile(os.path.join(TEST_FOLDER, file)):
                pdf_path = os.path.join(TEST_FOLDER, file)
                pdf_files.append(pdf_path)
    
    if len(pdf_files) < 10:
        log_result(f"⚠️ Only found {len(pdf_files)} PDFs, will test all of them")
        selected_pdfs = pdf_files[:10]
    else:
        selected_pdfs = pdf_files[:10]
    
    if not selected_pdfs:
        log_result("❌ No PDF files found in test folder!")
        return 1
    
    log_result(f"✅ Selected {len(selected_pdfs)} PDF file(s) for testing:")
    for i, pdf_path in enumerate(selected_pdfs, 1):
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        log_result(f"   {i}. {os.path.basename(pdf_path)} ({file_size_mb:.2f} MB)")
    
    # Extract first page from each PDF
    log_result("\n[STEP 2] Extracting first page from each PDF...")
    single_page_pdfs = []
    
    for pdf_path in selected_pdfs:
        original_name = os.path.basename(pdf_path)
        single_page_name = f"page1_{original_name}"
        single_page_path = os.path.join(TEMP_FOLDER, single_page_name)
        
        log_result(f"   Extracting first page: {original_name} → {single_page_name}")
        if extract_first_page(pdf_path, single_page_path):
            if os.path.exists(single_page_path):
                single_page_pdfs.append((single_page_path, original_name))
                log_result(f"   ✅ Extracted successfully")
            else:
                log_result(f"   ❌ Extraction failed: Output file not created")
        else:
            log_result(f"   ❌ Extraction failed")
    
    if not single_page_pdfs:
        log_result("❌ No single-page PDFs created. Cannot proceed with testing.")
        return 1
    
    log_result(f"\n✅ Successfully created {len(single_page_pdfs)} single-page PDFs")
    
    # Test each single-page PDF
    log_result("\n[STEP 3] Starting conversion tests (Free Version Pipeline)...")
    results = []
    
    for idx, (single_page_path, original_name) in enumerate(single_page_pdfs, 1):
        log_result(f"\n[{idx}/{len(single_page_pdfs)}] Processing...")
        result = convert_pdf_to_word(single_page_path, original_name)
        results.append(result)
        
        # Delay between requests
        if idx < len(single_page_pdfs):
            time.sleep(3)
    
    # Cleanup temp files
    log_result("\n[STEP 4] Cleaning up temporary files...")
    try:
        for file in os.listdir(TEMP_FOLDER):
            file_path = os.path.join(TEMP_FOLDER, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(TEMP_FOLDER)
        log_result("✅ Temp folder cleaned up")
    except Exception as e:
        log_result(f"⚠️ Cleanup warning: {str(e)}")
    
    # Summary
    log_result("\n" + "="*80)
    log_result("TEST SUMMARY - FREE VERSION PIPELINE")
    log_result("="*80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] != 'success')
    
    log_result(f"\nTotal PDFs tested: {len(single_page_pdfs)}")
    log_result(f"✅ Successful: {success_count}")
    log_result(f"❌ Failed: {failed_count}")
    log_result(f"Success rate: {(success_count/len(single_page_pdfs)*100):.1f}%")
    
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
            log_result(f"   - {result['pdf']} (page 1) → {result['output']} ({result.get('pages', 'N/A')} pages, {result.get('method', 'N/A')})")
    
    log_result("\n" + "="*80)
    log_result(f"Results saved to: {RESULTS_FILE}")
    log_result(f"Output files saved to: {OUTPUT_FOLDER}")
    log_result("="*80)
    
    # Save JSON summary
    json_summary = {
        'timestamp': datetime.now().isoformat(),
        'pipeline': 'free_version',
        'test_type': 'single_page_only',
        'total_tested': len(single_page_pdfs),
        'successful': success_count,
        'failed': failed_count,
        'success_rate': success_count/len(single_page_pdfs)*100 if single_page_pdfs else 0,
        'results': results
    }
    
    json_file = RESULTS_FILE.replace('.txt', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_summary, f, indent=2, ensure_ascii=False)
    
    log_result(f"JSON summary saved to: {json_file}")
    
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    try:
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

