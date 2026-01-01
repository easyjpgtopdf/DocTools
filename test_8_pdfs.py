"""
Test 8 PDFs from Pdf Word folder using the deployed API
Save outputs in the same folder
"""
import os
import sys
import requests
import json
from pathlib import Path
from datetime import datetime
import time

# Configuration
TEST_FOLDER = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"
OUTPUT_FOLDER = TEST_FOLDER
API_BASE_URL = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app"
API_ENDPOINT = f"{API_BASE_URL}/api/convert/pdf-to-word"

# Results file
RESULTS_FILE = os.path.join(OUTPUT_FOLDER, f"test_8_pdfs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

def log_result(message, to_file=True, to_console=True):
    """Log message to both file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    
    if to_file:
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg)
    if to_console:
        print(message)

def convert_pdf_to_word(pdf_path):
    """Convert a single PDF to Word using the API"""
    pdf_name = os.path.basename(pdf_path)
    log_result(f"\n{'='*80}")
    log_result(f"Testing: {pdf_name}")
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
                        output_filename = os.path.splitext(pdf_name)[0] + ".docx"
                        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                        
                        with open(output_path, 'wb') as out_file:
                            out_file.write(docx_response.content)
                        
                        output_size = os.path.getsize(output_path)
                        log_result(f"✅ Downloaded and saved: {output_filename}")
                        log_result(f"   Output size: {output_size:,} bytes ({output_size/(1024*1024):.2f} MB)")
                        
                        return {
                            'status': 'success',
                            'pdf': pdf_name,
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
                            'pdf': pdf_name,
                            'error': f"Download failed: {docx_response.status_code}"
                        }
                else:
                    log_result(f"⚠️ Conversion response missing downloadUrl")
                    return {
                        'status': 'no_url',
                        'pdf': pdf_name,
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
                    'pdf': pdf_name,
                    'status_code': response.status_code,
                    'error': str(error_detail)[:200]
                }
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout"
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
    log_result("TESTING 8 PDFs FROM Pdf Word FOLDER")
    log_result("="*80)
    log_result(f"Test folder: {TEST_FOLDER}")
    log_result(f"Output folder: {OUTPUT_FOLDER}")
    log_result(f"API endpoint: {API_ENDPOINT}")
    log_result(f"Results file: {RESULTS_FILE}")
    log_result("="*80)
    
    # Find all PDF files and select 8
    log_result("\n[STEP 1] Scanning for PDF files...")
    pdf_files = []
    if os.path.exists(TEST_FOLDER):
        for file in os.listdir(TEST_FOLDER):
            if file.lower().endswith('.pdf') and os.path.isfile(os.path.join(TEST_FOLDER, file)):
                pdf_path = os.path.join(TEST_FOLDER, file)
                file_size = os.path.getsize(pdf_path)
                pdf_files.append((pdf_path, file_size))
        
        # Sort by file size (smallest first for faster testing)
        pdf_files.sort(key=lambda x: x[1])
        
        # Select first 8
        selected_pdfs = [path for path, size in pdf_files[:8]]
    
    if not selected_pdfs:
        log_result("❌ No PDF files found in test folder!")
        return 1
    
    log_result(f"✅ Found {len(pdf_files)} PDF file(s), testing first 8 (by size):")
    for i, pdf_path in enumerate(selected_pdfs, 1):
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        log_result(f"   {i}. {os.path.basename(pdf_path)} ({file_size_mb:.2f} MB)")
    
    # Test each PDF
    log_result("\n[STEP 2] Starting conversion tests...")
    results = []
    
    for idx, pdf_path in enumerate(selected_pdfs, 1):
        log_result(f"\n[{idx}/8] Processing...")
        result = convert_pdf_to_word(pdf_path)
        results.append(result)
        
        # Delay between requests
        if idx < len(selected_pdfs):
            time.sleep(3)
    
    # Summary
    log_result("\n" + "="*80)
    log_result("TEST SUMMARY")
    log_result("="*80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] != 'success')
    
    log_result(f"\nTotal PDFs tested: {len(selected_pdfs)}")
    log_result(f"✅ Successful: {success_count}")
    log_result(f"❌ Failed: {failed_count}")
    log_result(f"Success rate: {(success_count/len(selected_pdfs)*100):.1f}%")
    
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
            log_result(f"   - {result['pdf']} → {result['output']} ({result.get('pages', 'N/A')} pages, {result.get('method', 'N/A')})")
    
    log_result("\n" + "="*80)
    log_result(f"Results saved to: {RESULTS_FILE}")
    log_result("="*80)
    
    # Save JSON summary
    json_summary = {
        'timestamp': datetime.now().isoformat(),
        'total_tested': len(selected_pdfs),
        'successful': success_count,
        'failed': failed_count,
        'success_rate': success_count/len(selected_pdfs)*100 if selected_pdfs else 0,
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

