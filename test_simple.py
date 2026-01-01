"""Simple test without emojis"""
import requests
import json
import os

API_BASE_URL = "https://pdf-to-word-converter-564572183797.us-central1.run.app"
test_pdf = r"C:\Users\apnao\Downloads\DocTools\Pdf Word\learning.pdf"
output_dir = r"C:\Users\apnao\Downloads\DocTools\Pdf Word"

print("Testing PDF to Word conversion...")
print(f"PDF: {os.path.basename(test_pdf)}")

with open(test_pdf, 'rb') as f:
    files = {'file': (os.path.basename(test_pdf), f, 'application/pdf')}
    response = requests.post(
        f"{API_BASE_URL}/api/convert/pdf-to-word",
        files=files,
        timeout=300
    )

print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    download_url = result.get('primary_download_url') or result.get('download_url')
    print(f"Success! Download URL: {download_url[:80]}...")
    
    # Download
    dl_response = requests.get(download_url, timeout=60)
    if dl_response.status_code == 200:
        output_path = os.path.join(output_dir, os.path.basename(test_pdf).replace('.pdf', '.docx'))
        with open(output_path, 'wb') as out:
            out.write(dl_response.content)
        print(f"File saved to: {output_path}")
        print("SUCCESS!")
    else:
        print(f"Download failed: {dl_response.status_code}")
        print(dl_response.text[:500])
else:
    print("Conversion failed!")
    try:
        error = response.json()
        print(json.dumps(error, indent=2))
    except:
        print(response.text[:500])

