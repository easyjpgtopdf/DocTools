"""
Test ALL PDFs to find digital ones that can be converted with free version
"""
import os
import sys
import requests
import time

TEST_FOLDER = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"
OUTPUT_FOLDER = TEST_FOLDER
API_ENDPOINT = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app/api/convert/pdf-to-word"

def convert_pdf(pdf_path):
    """Try to convert PDF to DOCX"""
    pdf_name = os.path.basename(pdf_path)
    
    try:
        file_size = os.path.getsize(pdf_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Skip if too large for free tier
        if file_size_mb > 2:
            return {'status': 'size_limit', 'size_mb': file_size_mb}
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_name, f, 'application/pdf')}
            response = requests.post(API_ENDPOINT, files=files, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                
                # Download DOCX
                if 'primary_download_url' in result:
                    docx_response = requests.get(result['primary_download_url'], timeout=60)
                    if docx_response.status_code == 200:
                        output_filename = os.path.splitext(pdf_name)[0] + ".docx"
                        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                        with open(output_path, 'wb') as out_file:
                            out_file.write(docx_response.content)
                        return {
                            'status': 'success',
                            'docx': output_filename,
                            'path': output_path,
                            'pages': result.get('pages'),
                            'method': result.get('primary_method')
                        }
            else:
                try:
                    error_detail = response.json().get('detail', {})
                    if isinstance(error_detail, dict):
                        error_msg = error_detail.get('message', str(error_detail))
                        error_code = error_detail.get('error', '')
                    else:
                        error_msg = str(error_detail)
                        error_code = ''
                    
                    # Check error type
                    if 'page' in error_msg.lower() or 'exceeds_pages' in error_code.lower():
                        return {'status': 'page_limit', 'error': error_msg}
                    elif 'ocr' in error_msg.lower() or 'scanned' in error_msg.lower():
                        return {'status': 'scanned', 'error': error_msg}
                    elif 'size' in error_msg.lower():
                        return {'status': 'size_limit', 'error': error_msg}
                    else:
                        return {'status': 'failed', 'error': error_msg}
                except:
                    return {'status': 'failed', 'error': response.text[:200]}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

# Get all PDFs
all_pdfs = []
for file in sorted(os.listdir(TEST_FOLDER)):
    if file.lower().endswith('.pdf'):
        all_pdfs.append(os.path.join(TEST_FOLDER, file))

print("="*80)
print(f"TESTING ALL {len(all_pdfs)} PDFs TO FIND DIGITAL ONES")
print("="*80)

results = []
success_count = 0

for i, pdf_path in enumerate(all_pdfs, 1):
    pdf_name = os.path.basename(pdf_path)
    print(f"\n[{i}/{len(all_pdfs)}] {pdf_name}")
    
    result = convert_pdf(pdf_path)
    results.append((pdf_name, result))
    
    if result['status'] == 'success':
        success_count += 1
        print(f"   ✅ SUCCESS! → {result['docx']} ({result['pages']} pages, {result['method']})")
    elif result['status'] == 'page_limit':
        print(f"   ⚠️  Multi-page (free limit: 1 page)")
    elif result['status'] == 'scanned':
        print(f"   ⚠️  Scanned PDF (requires OCR/Premium)")
    elif result['status'] == 'size_limit':
        size = result.get('size_mb', 0)
        print(f"   ⚠️  Too large ({size:.2f} MB, free limit: 2 MB)")
    else:
        error = result.get('error', 'Unknown')[:100]
        print(f"   ❌ Failed: {error}")
    
    time.sleep(2)  # Rate limiting

# Final Summary
print("\n" + "="*80)
print("FINAL SUMMARY")
print("="*80)
print(f"Total PDFs tested: {len(results)}")
print(f"✅ Successfully converted: {success_count}")

if success_count > 0:
    print(f"\n✅ DIGITAL PDFs CONVERTED TO DOCX:")
    for pdf_name, result in results:
        if result['status'] == 'success':
            print(f"   📄 {pdf_name}")
            print(f"      → 📝 {result['docx']}")
            print(f"      → Pages: {result['pages']}, Method: {result['method']}")
            print(f"      → Saved: {result['path']}")
else:
    print("\n❌ No PDFs successfully converted")
    print("\n📊 Breakdown:")
    scanned = sum(1 for _, r in results if r['status'] == 'scanned')
    page_limit = sum(1 for _, r in results if r['status'] == 'page_limit')
    size_limit = sum(1 for _, r in results if r['status'] == 'size_limit')
    failed = sum(1 for _, r in results if r['status'] in ['failed', 'error'])
    
    print(f"   - Scanned (requires OCR): {scanned}")
    print(f"   - Multi-page (>1 page): {page_limit}")
    print(f"   - Too large (>2MB): {size_limit}")
    print(f"   - Other errors: {failed}")

