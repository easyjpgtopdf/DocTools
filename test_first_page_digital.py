"""
Extract first page from multi-page PDFs and test if they're digital
"""
import os
import sys
import requests
import time
from PyPDF2 import PdfReader, PdfWriter

TEST_FOLDER = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"
OUTPUT_FOLDER = TEST_FOLDER
API_ENDPOINT = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app/api/convert/pdf-to-word"
TEMP_FOLDER = os.path.join(TEST_FOLDER, "temp_single_pages")

def extract_first_page(input_pdf_path, output_pdf_path):
    """Extract first page from PDF"""
    try:
        reader = PdfReader(input_pdf_path)
        if len(reader.pages) == 0:
            return False
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)
        return True
    except Exception as e:
        print(f"      PyPDF2 error: {e}")
        return False

def convert_pdf(pdf_path):
    """Try to convert PDF to DOCX"""
    pdf_name = os.path.basename(pdf_path)
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_name, f, 'application/pdf')}
            response = requests.post(API_ENDPOINT, files=files, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
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
                    else:
                        error_msg = str(error_detail)
                    if 'ocr' in error_msg.lower() or 'scanned' in error_msg.lower():
                        return {'status': 'scanned', 'error': error_msg}
                    else:
                        return {'status': 'failed', 'error': error_msg}
                except:
                    return {'status': 'failed', 'error': response.text[:200]}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

# Create temp folder
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Get all multi-page PDFs (from previous test, we know these are multi-page)
multi_page_pdfs = [
    "CIBIL Report.pdf",
    "DavaNeha.pdf",
    "Fwd_ Payment Process - SECL Jamuna Kotma_inv. no. 046.pdf",
    "Fwd_ Payment Process - SECL Jamuna Kotma_inv. no. 061.pdf",
    "Letter requesting rlease of long overdue pmt..pdf",
    "Print _ Udyam Registration Certificate.pdf",
    "Re_ Overdue Payment of Rs.₹40,769.00_- against invoice no. SSEPL_23-24_061-- SECL (HQRS)_.pdf",
    "शाला प्रबंधन समिति के आय व्यय के सम्बन्ध में.pdf"
]

print("="*80)
print("TESTING FIRST PAGE OF MULTI-PAGE PDFs (Free Tier: 1 page allowed)")
print("="*80)

results = []
success_count = 0

for pdf_name in multi_page_pdfs:
    pdf_path = os.path.join(TEST_FOLDER, pdf_name)
    if not os.path.exists(pdf_path):
        continue
    
    print(f"\n📄 {pdf_name}")
    
    # Extract first page
    temp_pdf_name = "first_page_" + pdf_name.replace(" ", "_").replace("..", "_")
    temp_pdf_path = os.path.join(TEMP_FOLDER, temp_pdf_name)
    
    print(f"   Extracting first page...")
    if not extract_first_page(pdf_path, temp_pdf_path):
        print(f"   ❌ Failed to extract first page")
        continue
    
    print(f"   Testing conversion...")
    result = convert_pdf(temp_pdf_path)
    results.append((pdf_name, result))
    
    if result['status'] == 'success':
        success_count += 1
        # Save with original name prefix
        original_docx = os.path.splitext(pdf_name)[0] + "_first_page.docx"
        original_docx_path = os.path.join(OUTPUT_FOLDER, original_docx)
        if os.path.exists(result['path']):
            import shutil
            shutil.copy2(result['path'], original_docx_path)
            result['docx'] = original_docx
            result['path'] = original_docx_path
        print(f"   ✅ SUCCESS! → {original_docx} ({result['pages']} pages, {result['method']})")
    elif result['status'] == 'scanned':
        print(f"   ⚠️  First page is scanned (requires OCR)")
    else:
        error = result.get('error', 'Unknown')[:100]
        print(f"   ❌ Failed: {error}")
    
    time.sleep(2)

# Summary
print("\n" + "="*80)
print("RESULTS")
print("="*80)
print(f"✅ Successfully converted: {success_count}/{len(results)}")

if success_count > 0:
    print(f"\n✅ DIGITAL PDFs (First Page) CONVERTED:")
    for pdf_name, result in results:
        if result['status'] == 'success':
            print(f"   📄 {pdf_name} (first page only)")
            print(f"      → 📝 {result['docx']}")
            print(f"      → Method: {result['method']}")

# Cleanup
try:
    import shutil
    shutil.rmtree(TEMP_FOLDER)
    print(f"\n🧹 Cleaned up temp folder")
except:
    pass

