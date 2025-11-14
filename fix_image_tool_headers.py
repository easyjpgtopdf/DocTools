import os
from bs4 import BeautifulSoup

# List of image tool pages to update
image_tools_pages = [
    'image-compressor.html',
    'image-resizer.html',
    'image-editor.html',
    'background-remover.html',
    'ocr-image.html',
    'image-watermark.html',
    'image-watermark-convert.html',
    'image-repair.html'
]

def update_header(html_content, current_page):
    """Update the header to include AI Image Repair in the Image Tools dropdown"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the Image Tools dropdown
    dropdowns = soup.find_all('div', class_='dropdown')
    image_tools_dropdown = None
    
    for dropdown in dropdowns:
        if 'Image Tools' in dropdown.get_text():
            image_tools_dropdown = dropdown
            break
    
    if image_tools_dropdown:
        dropdown_content = image_tools_dropdown.find('div', class_='dropdown-content')
        if dropdown_content:
            # Clear existing content
            dropdown_content.clear()
            
            # Add the tools in the correct order
            tools = [
                ('image-repair.html', 'AI Image Repair'),
                ('image-compressor.html', 'Image Compressor'),
                ('image-resizer.html', 'Image Resizer'),
                ('image-editor.html', 'Image Editor'),
                ('background-remover.html', 'Background Remover'),
                ('ocr-image.html', 'OCR Image'),
                ('image-watermark.html', 'Image Watermark')
            ]
            
            for tool_url, tool_name in tools:
                link = soup.new_tag('a', href=tool_url)
                link.string = tool_name
                if tool_url == current_page:
                    link['class'] = 'active'
                dropdown_content.append(link)
    
    return str(soup)

def update_all_headers():
    for page in image_tools_pages:
        try:
            with open(page, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update header
            updated_content = update_header(content, page)
            
            # Save the updated content
            with open(page, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            print(f"Updated header in: {page}")
            
        except Exception as e:
            print(f"Error updating {page}: {str(e)}")

if __name__ == "__main__":
    print("Updating headers in image tool pages...")
    update_all_headers()
    print("Update complete!")
