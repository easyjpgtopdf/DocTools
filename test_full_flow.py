"""Test full conversion and download flow"""
import requests
import json
import os
import time

API_BASE_URL = "https://pdf-to-word-converter-564572183797.us-central1.run.app"
test_pdf = r"C:\Users\apnao\Downloads\DocTools\Pdf Word\learning.pdf"
output_dir = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"

print("=" * 60)
print("Full Conversion and Download Test")
print("=" * 60)
print(f"\nPDF: {os.path.basename(test_pdf)}")
print(f"Size: {os.path.getsize(test_pdf) / 1024:.2f} KB")

# Step 1: Convert
print("\n[Step 1] Uploading and converting...")
try:
    with open(test_pdf, 'rb') as f:
        files = {'file': (os.path.basename(test_pdf), f, 'application/pdf')}
        response = requests.post(
            f"{API_BASE_URL}/api/convert/pdf-to-word",
            files=files,
            timeout=300
        )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print("Conversion failed!")
        try:
            error = response.json()
            print(json.dumps(error, indent=2))
        except:
            print(response.text[:500])
        exit(1)
    
    result = response.json()
    print("Conversion successful!")
    print(f"Job ID: {result.get('job_id')}")
    print(f"Method: {result.get('primary_method')}")
    print(f"Pages: {result.get('pages')}")
    
    download_url = result.get('primary_download_url') or result.get('download_url')
    if not download_url:
        print("ERROR: No download URL in response!")
        print(f"Full response: {json.dumps(result, indent=2)}")
        exit(1)
    
    print(f"\nDownload URL: {download_url[:80]}...")
    
    # Step 2: Download
    print("\n[Step 2] Downloading converted file...")
    time.sleep(2)  # Wait a bit for file to be ready
    
    dl_response = requests.get(download_url, timeout=60, allow_redirects=True)
    print(f"Download Status: {dl_response.status_code}")
    print(f"Content-Type: {dl_response.headers.get('content-type', 'unknown')}")
    print(f"Content-Length: {len(dl_response.content)} bytes")
    
    if dl_response.status_code != 200:
        print("Download failed!")
        print(f"Response: {dl_response.text[:500]}")
        exit(1)
    
    # Check if we got JSON error instead of file
    if 'json' in dl_response.headers.get('content-type', '').lower():
        try:
            error = dl_response.json()
            print("ERROR: Server returned JSON instead of file:")
            print(json.dumps(error, indent=2))
            exit(1)
        except:
            pass
    
    # Save file
    output_filename = os.path.basename(test_pdf).replace('.pdf', '.docx')
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'wb') as f:
        f.write(dl_response.content)
    
    file_size = len(dl_response.content) / 1024
    print(f"\nFile saved successfully!")
    print(f"Output: {output_path}")
    print(f"Size: {file_size:.2f} KB")
    
    if os.path.exists(output_path) and file_size > 0:
        print("\n" + "=" * 60)
        print("SUCCESS! File converted and downloaded.")
        print("=" * 60)
    else:
        print("\nERROR: File was not saved correctly!")
        exit(1)
        
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

