import os
import re
from bs4 import BeautifulSoup

# Read the index.html to get the header
with open('index.html', 'r', encoding='utf-8') as f:
    index_content = f.read()

# Parse the index.html to extract the header
soup = BeautifulSoup(index_content, 'html.parser')
header = soup.find('header')
if header:
    header_html = str(header)
    print("Header template found in index.html")
else:
    print("Error: Could not find header in index.html")
    exit(1)

# Get all HTML files in the current directory
html_files = [f for f in os.listdir('.') if f.endswith('.html') and f != 'index.html']

for filename in html_files:
    print(f"Processing {filename}...")
    
    try:
        # Read the file
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the existing header
        old_header = soup.find('header')
        if old_header:
            # Replace the old header with the new one
            old_header.replace_with(BeautifulSoup(header_html, 'html.parser'))
            
            # Write the updated content back to the file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print(f"  ✓ Updated header in {filename}")
        else:
            print(f"  ⚠️ No header found in {filename}")
            
    except Exception as e:
        print(f"  ✗ Error processing {filename}: {str(e)}")

print("\nHeader update process completed!")
