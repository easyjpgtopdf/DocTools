"""
Comprehensive PDF to Word Conversion Test Script
Tests all PDFs in the "Pdf Word" folder and saves outputs
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
OUTPUT_FOLDER = os.path.join(TEST_FOLDER, "converted_outputs")
API_BASE_URL = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app"
API_ENDPOINT = f"{API_BASE_URL}/api/convert/pdf-to-word"

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Test results file
RESULTS_FILE = os.path.join(OUTPUT_FOLDER, f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

def log_result(message, to_file=True, to_console=True):
    """Log message to both file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    
    if to_file:
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg)
    if to_console:
        print(message)

def test_api_health():
    """Test if API is accessible"""
    try:
        # Try GET first
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            log_result("✅ API is healthy and accessible")
            return True
        
        # Try POST if GET doesn't work
        response = requests.post(f"{API_BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            log_result("✅ API is healthy and accessible")
            return True
        
        # If both fail, try root endpoint
        response = requests.get(f"{API_BASE_URL}/", timeout=10)
        if response.status_code in [200, 404]:  # 404 is OK, means server is responding
            log_result("⚠️ Health endpoint not found, but server is responding (will continue testing)")
            return True
        
        log_result(f"⚠️ API health check returned status {response.status_code}")
        return False
    except requests.exceptions.ConnectionError:
        log_result(f"❌ Cannot connect to API. Is the service running?")
        return False
    except Exception as e:
        log_result(f"⚠️ API health check issue: {str(e)} (will continue testing)")
        return True  # Continue anyway

def convert_pdf_to_word(pdf_path):
    """Convert a single PDF to Word using the API"""
    pdf_name = os.path.basename(pdf_path)
    log_result(f"\n{'='*80}")
    log_result(f"Testing: {pdf_name}")
    log_result(f"{'='*80}")
    
    try:
        # Check file size
        file_size = os.path.getsize(pdf_path)
        file_size_mb = file_size / (1024 * 1024)
        log_result(f"File size: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        
        # Prepare file for upload
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_name, f, 'application/pdf')}
            
            # Make API request (no auth token for free tier testing)
            log_result(f"Uploading to API: {API_ENDPOINT}")
            start_time = time.time()
            
            response = requests.post(
                API_ENDPOINT,
                files=files,
                timeout=300,  # 5 minutes timeout for large files
                headers={
                    'Accept': 'application/json'
                }
            )
            
            elapsed_time = time.time() - start_time
            log_result(f"API response time: {elapsed_time:.2f} seconds")
            log_result(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Download the converted file
                if 'downloadUrl' in result:
                    download_url = result['downloadUrl']
                    log_result(f"✅ Conversion successful!")
                    log_result(f"   Download URL: {download_url}")
                    
                    # Download the Word file
                    docx_response = requests.get(download_url, timeout=60)
                    if docx_response.status_code == 200:
                        # Save to output folder
                        output_filename = os.path.splitext(pdf_name)[0] + ".docx"
                        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                        
                        with open(output_path, 'wb') as out_file:
                            out_file.write(docx_response.content)
                        
                        output_size = os.path.getsize(output_path)
                        log_result(f"✅ Downloaded and saved: {output_path}")
                        log_result(f"   Output size: {output_size:,} bytes ({output_size/(1024*1024):.2f} MB)")
                        
                        return {
                            'status': 'success',
                            'pdf': pdf_name,
                            'output': output_filename,
                            'file_size_mb': file_size_mb,
                            'output_size_mb': output_size/(1024*1024),
                            'response_time': elapsed_time,
                            'job_id': result.get('jobId', 'N/A'),
                            'pages': result.get('pages', 'N/A'),
                            'method': result.get('method', 'N/A'),
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
                    log_result(f"   Response: {json.dumps(result, indent=2)}")
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
                except:
                    error_detail = response.text[:500]
                
                log_result(f"❌ Conversion failed!")
                log_result(f"   Status: {response.status_code}")
                log_result(f"   Error: {error_detail}")
                
                return {
                    'status': 'failed',
                    'pdf': pdf_name,
                    'status_code': response.status_code,
                    'error': error_detail[:200]  # Truncate long errors
                }
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout (file may be too large or processing too slow)"
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
    log_result("PDF TO WORD CONVERSION TEST SUITE")
    log_result("="*80)
    log_result(f"Test folder: {TEST_FOLDER}")
    log_result(f"Output folder: {OUTPUT_FOLDER}")
    log_result(f"API endpoint: {API_ENDPOINT}")
    log_result(f"Results file: {RESULTS_FILE}")
    log_result("="*80)
    
    # Test API health first
    log_result("\n[STEP 1] Testing API health...")
    if not test_api_health():
        log_result("\n❌ API is not accessible. Stopping tests.")
        return 1
    
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
        result = convert_pdf_to_word(pdf_path)
        results.append(result)
        
        # Small delay between requests
        if idx < total:
            time.sleep(2)
    
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
            log_result(f"   - {result['pdf']}: {result.get('error', 'Unknown error')}")
    
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

