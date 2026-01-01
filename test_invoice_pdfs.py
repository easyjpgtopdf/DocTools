"""
Test invoice and digital PDFs specifically - Convert to DOCX
"""
import os
import sys
import requests
import time

# Configuration
TEST_FOLDER = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"
OUTPUT_FOLDER = TEST_FOLDER
API_ENDPOINT = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app/api/convert/pdf-to-word"

def convert_pdf_to_docx(pdf_path):
    """Convert PDF to DOCX and save output"""
    pdf_name = os.path.basename(pdf_path)
    print(f"\n{'='*80}")
    print(f"Converting: {pdf_name}")
    print(f"{'='*80}")
    
    try:
        file_size = os.path.getsize(pdf_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB")
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_name, f, 'application/pdf')}
            print(f"Uploading to API (Free Version)...")
            start_time = time.time()
            
            response = requests.post(
                API_ENDPOINT,
                files=files,
                timeout=300
            )
            
            elapsed_time = time.time() - start_time
            print(f"Response time: {elapsed_time:.2f} seconds")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Conversion successful!")
                print(f"   Pages: {result.get('pages', 'N/A')}")
                print(f"   Method: {result.get('primary_method', 'N/A')}")
                
                # Download and save DOCX
                if 'primary_download_url' in result:
                    download_url = result['primary_download_url']
                    print(f"   Downloading DOCX...")
                    
                    docx_response = requests.get(download_url, timeout=60)
                    if docx_response.status_code == 200:
                        output_filename = os.path.splitext(pdf_name)[0] + ".docx"
                        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                        
                        with open(output_path, 'wb') as out_file:
                            out_file.write(docx_response.content)
                        
                        output_size = os.path.getsize(output_path)
                        print(f"✅ DOCX saved: {output_filename}")
                        print(f"   Size: {output_size:,} bytes ({output_size/(1024*1024):.2f} MB)")
                        print(f"   Path: {output_path}")
                        return {'status': 'success', 'pdf': pdf_name, 'docx': output_filename}
                    else:
                        print(f"❌ Download failed: {docx_response.status_code}")
                        return {'status': 'download_failed', 'pdf': pdf_name}
                else:
                    print(f"⚠️ No download URL")
                    return {'status': 'no_url', 'pdf': pdf_name}
            else:
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(error_data))
                    if isinstance(error_detail, dict):
                        error_detail = error_detail.get('message', str(error_detail))
                except:
                    error_detail = response.text[:300]
                
                print(f"❌ Failed: {error_detail}")
                return {'status': 'failed', 'pdf': pdf_name, 'error': str(error_detail)[:200]}
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {'status': 'exception', 'pdf': pdf_name, 'error': str(e)}

def main():
    """Main function"""
    print("="*80)
    print("TESTING INVOICE & DIGITAL PDFs - FREE VERSION")
    print("="*80)
    print(f"Folder: {TEST_FOLDER}")
    print("="*80)
    
    # Find invoice PDFs
    pdf_files = []
    if os.path.exists(TEST_FOLDER):
        for file in sorted(os.listdir(TEST_FOLDER)):
            if file.lower().endswith('.pdf') and os.path.isfile(os.path.join(TEST_FOLDER, file)):
                pdf_path = os.path.join(TEST_FOLDER, file)
                # Prioritize invoices and digital documents
                if 'invoice' in file.lower() or 'ack' in file.lower():
                    pdf_files.insert(0, pdf_path)  # Add to front
                else:
                    pdf_files.append(pdf_path)
    
    if not pdf_files:
        print("❌ No PDF files found!")
        return 1
    
    print(f"\nFound {len(pdf_files)} PDF files")
    print("Testing invoices and digital PDFs first...")
    
    results = []
    success_count = 0
    max_tests = min(10, len(pdf_files))
    
    for i, pdf_path in enumerate(pdf_files[:max_tests], 1):
        pdf_name = os.path.basename(pdf_path)
        print(f"\n[{i}/{max_tests}] Testing: {pdf_name}")
        result = convert_pdf_to_docx(pdf_path)
        results.append(result)
        
        if result['status'] == 'success':
            success_count += 1
            print(f"✅ SUCCESS! DOCX created: {result['docx']}")
        
        # Stop after getting 4 successful conversions
        if success_count >= 4:
            print(f"\n✅ Got {success_count} successful conversions!")
            break
        
        time.sleep(2)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total tested: {len(results)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    
    if success_count > 0:
        print("\n✅ Successfully converted to DOCX:")
        for r in results:
            if r['status'] == 'success':
                print(f"   📄 {r['pdf']} → 📝 {r['docx']}")
    else:
        print("\n❌ No successful conversions")
        print("\nAll PDFs appear to require Premium/OCR")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    try:
        if os.name == 'nt':
            os.system('chcp 65001 >nul 2>&1')
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

