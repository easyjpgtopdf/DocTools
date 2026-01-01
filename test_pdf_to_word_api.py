"""
Test script to upload PDF, convert to Word, and download the result.
"""
import requests
import json
import os
import sys
from pathlib import Path

# API endpoint
API_BASE_URL = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app"

# Test PDF files (try multiple)
test_pdfs = [
    r"C:\Users\apnao\Downloads\DocTools\Pdf Word\learning.pdf",
    r"C:\Users\apnao\Downloads\DocTools\Pdf Word\Resume.pdf",
    r"C:\Users\apnao\Downloads\DocTools\Pdf Word\E Call Letter.pdf",
]
output_dir = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"

def test_conversion(pdf_path):
    """Test PDF to Word conversion via API."""
    print("=" * 60)
    print("PDF to Word Conversion Test")
    print("=" * 60)
    
    # Check if test file exists
    if not os.path.exists(pdf_path):
        print(f"❌ Error: Test PDF not found: {pdf_path}")
        return False
    
    print(f"\n📄 Test PDF: {os.path.basename(pdf_path)}")
    file_size = os.path.getsize(pdf_path) / 1024  # KB
    print(f"   Size: {file_size:.2f} KB")
    
    # Step 1: Upload and convert
    print(f"\n🔄 Step 1: Uploading PDF and starting conversion...")
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            response = requests.post(
                f"{API_BASE_URL}/api/convert/pdf-to-word",
                files=files,
                timeout=300  # 5 minutes timeout
            )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Conversion failed!")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Error: {response.text[:500]}")
            return False
        
        result = response.json()
        print(f"✅ Conversion successful!")
        print(f"   Job ID: {result.get('job_id')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Method: {result.get('primary_method')}")
        print(f"   Pages: {result.get('pages')}")
        
        # Get download URL
        download_url = result.get('primary_download_url') or result.get('download_url')
        if not download_url:
            print("❌ No download URL in response!")
            print(f"   Full response: {json.dumps(result, indent=2)}")
            return False
        
        print(f"\n📥 Step 2: Downloading converted file...")
        print(f"   Download URL: {download_url[:100]}...")
        
        # Step 2: Download the file
        download_response = requests.get(download_url, timeout=60, allow_redirects=True)
        print(f"   Download Status: {download_response.status_code}")
        
        if download_response.status_code != 200:
            print(f"❌ Download failed!")
            print(f"   Response headers: {dict(download_response.headers)}")
            try:
                error_data = download_response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Error text: {download_response.text[:500]}")
            return False
        
        # Check content type
        content_type = download_response.headers.get('content-type', '')
        print(f"   Content-Type: {content_type}")
        
        if 'json' in content_type.lower():
            # Got JSON error instead of file
            try:
                error_data = download_response.json()
                print(f"❌ Server returned JSON error:")
                print(f"   {json.dumps(error_data, indent=2)}")
            except:
                print(f"❌ Server returned non-file response: {download_response.text[:500]}")
            return False
        
        # Save file
        output_filename = os.path.basename(pdf_path).replace('.pdf', '.docx')
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'wb') as f:
            f.write(download_response.content)
        
        file_size_docx = len(download_response.content) / 1024  # KB
        print(f"✅ File downloaded successfully!")
        print(f"   Output: {output_path}")
        print(f"   Size: {file_size_docx:.2f} KB")
        
        # Verify file exists
        if os.path.exists(output_path) and file_size_docx > 0:
            print(f"\n✅✅✅ SUCCESS! ✅✅✅")
            print(f"   Converted file saved to: {output_path}")
            return True
        else:
            print(f"❌ File was not saved correctly!")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out!")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Try multiple PDFs until one works
    for pdf_path in test_pdfs:
        if os.path.exists(pdf_path):
            print(f"\n{'='*60}")
            print(f"Trying: {os.path.basename(pdf_path)}")
            print(f"{'='*60}")
            if test_conversion(pdf_path):
                print("\n✅ Test completed successfully!")
                sys.exit(0)
            else:
                print("\n❌ This PDF failed, trying next...")
                print()
    
    print("\n❌❌❌ All PDFs failed! ❌❌❌")
    sys.exit(1)
