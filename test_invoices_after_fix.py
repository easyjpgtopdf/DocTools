"""
Test invoice PDFs after fixing text detection threshold
"""
import os
import sys
import requests
import time

TEST_FOLDER = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"
OUTPUT_FOLDER = TEST_FOLDER
API_ENDPOINT = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app/api/convert/pdf-to-word"

def convert_pdf(pdf_path):
    """Convert PDF to DOCX"""
    pdf_name = os.path.basename(pdf_path)
    print(f"\n{'='*60}")
    print(f"Testing: {pdf_name}")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_name, f, 'application/pdf')}
            print("Uploading...")
            response = requests.post(API_ENDPOINT, files=files, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                if 'primary_download_url' in result:
                    print(f"✅ SUCCESS! Downloading DOCX...")
                    docx_response = requests.get(result['primary_download_url'], timeout=60)
                    if docx_response.status_code == 200:
                        output_filename = os.path.splitext(pdf_name)[0] + ".docx"
                        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                        with open(output_path, 'wb') as out_file:
                            out_file.write(docx_response.content)
                        print(f"✅ DOCX saved: {output_filename}")
                        return {'status': 'success', 'docx': output_filename}
            else:
                error = response.json().get('detail', {}).get('message', 'Unknown error')
                print(f"❌ Failed: {error}")
                return {'status': 'failed', 'error': error}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# Test invoice PDFs specifically
invoice_files = []
for file in sorted(os.listdir(TEST_FOLDER)):
    if file.lower().endswith('.pdf') and 'invoice' in file.lower():
        invoice_files.append(os.path.join(TEST_FOLDER, file))

print(f"Found {len(invoice_files)} invoice PDFs")
results = []
for pdf_path in invoice_files[:4]:  # Test first 4 invoices
    result = convert_pdf(pdf_path)
    results.append(result)
    if result['status'] == 'success':
        print(f"\n✅ SUCCESS! DOCX file created: {result['docx']}")
    time.sleep(2)

success_count = sum(1 for r in results if r['status'] == 'success')
print(f"\n{'='*60}")
print(f"Results: {success_count}/{len(results)} successful")
if success_count > 0:
    print("\n✅ DOCX files created:")
    for r in results:
        if r['status'] == 'success':
            print(f"   - {r['docx']}")

