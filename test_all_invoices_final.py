"""
Test all invoice PDFs with fixed logic - Convert to DOCX
"""
import os
import sys
import requests
import time

TEST_FOLDER = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"
OUTPUT_FOLDER = TEST_FOLDER
API_ENDPOINT = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app/api/convert/pdf-to-word"

def convert_pdf(pdf_path):
    """Convert PDF to DOCX and save"""
    pdf_name = os.path.basename(pdf_path)
    print(f"\n{'='*70}")
    print(f"Converting: {pdf_name}")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_name, f, 'application/pdf')}
            print("Uploading...")
            response = requests.post(API_ENDPOINT, files=files, timeout=300)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS! Pages: {result.get('pages')}, Method: {result.get('primary_method')}")
                
                if 'primary_download_url' in result:
                    print("Downloading DOCX...")
                    docx_response = requests.get(result['primary_download_url'], timeout=60)
                    if docx_response.status_code == 200:
                        output_filename = os.path.splitext(pdf_name)[0] + ".docx"
                        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                        with open(output_path, 'wb') as out_file:
                            out_file.write(docx_response.content)
                        output_size = os.path.getsize(output_path)
                        print(f"✅ DOCX saved: {output_filename} ({output_size:,} bytes)")
                        return {'status': 'success', 'docx': output_filename, 'path': output_path}
            else:
                try:
                    error = response.json().get('detail', {})
                    if isinstance(error, dict):
                        error_msg = error.get('message', str(error))
                    else:
                        error_msg = str(error)
                except:
                    error_msg = response.text[:200]
                print(f"❌ Failed: {error_msg}")
                return {'status': 'failed', 'error': error_msg}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# Find invoice PDFs
invoice_files = []
for file in sorted(os.listdir(TEST_FOLDER)):
    if file.lower().endswith('.pdf') and 'invoice' in file.lower():
        invoice_files.append(os.path.join(TEST_FOLDER, file))

print("="*70)
print(f"TESTING {len(invoice_files)} INVOICE PDFs")
print("="*70)

results = []
for i, pdf_path in enumerate(invoice_files, 1):
    print(f"\n[{i}/{len(invoice_files)}]")
    result = convert_pdf(pdf_path)
    results.append((os.path.basename(pdf_path), result))
    if result['status'] == 'success':
        print(f"✅✅✅ SUCCESS! DOCX created!")
    time.sleep(3)

# Summary
print("\n" + "="*70)
print("FINAL RESULTS")
print("="*70)
success_count = sum(1 for _, r in results if r['status'] == 'success')
print(f"Successful: {success_count}/{len(results)}")

if success_count > 0:
    print("\n✅ DOCX FILES CREATED:")
    for pdf_name, result in results:
        if result['status'] == 'success':
            print(f"   📄 {pdf_name} → 📝 {result['docx']}")
            print(f"      Saved: {result['path']}")
else:
    print("\n❌ No DOCX files created")
    print("\nAll invoice PDFs require Premium/OCR or have other restrictions")

