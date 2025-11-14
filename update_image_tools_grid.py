import os
from bs4 import BeautifulSoup

# List of image tool pages to update
image_tools = [
    {"url": "image-repair.html", "name": "AI Image Repair", "icon": "fas fa-magic", "desc": "Fix blurry, scratched, or damaged photos with AI"},
    {"url": "image-compressor.html", "name": "Image Compressor", "icon": "fas fa-compress-arrows-alt", "desc": "Reduce image file size without losing quality"},
    {"url": "image-resizer.html", "name": "Image Resizer", "icon": "fas fa-expand-arrows-alt", "desc": "Resize images to any dimension"},
    {"url": "image-editor.html", "name": "Image Editor", "icon": "fas fa-edit", "desc": "Edit and enhance your images online"},
    {"url": "background-remover.html", "name": "Background Remover", "icon": "fas fa-eraser", "desc": "Remove background from images automatically"},
    {"url": "ocr-image.html", "name": "OCR Image", "icon": "fas fa-font", "desc": "Extract text from images with OCR technology"},
    {"url": "image-watermark.html", "name": "Image Watermark", "icon": "fas fa-water", "desc": "Add watermarks to protect your images"}
]

def add_tools_grid(html_content, current_page):
    """Add a grid of image tools to the page"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Create the tools grid section
    tools_section = soup.new_tag('section', **{'class': 'tools-section'})
    
    # Add section title
    title_div = soup.new_tag('div', **{'class': 'section-title'})
    title_h2 = soup.new_tag('h2')
    title_h2.string = 'More Image Tools'
    title_div.append(title_h2)
    tools_section.append(title_div)
    
    # Create tools grid
    tools_grid = soup.new_tag('div', **{'class': 'tools-grid'})
    
    # Add tool cards
    for tool in image_tools:
        tool_card = soup.new_tag('a', href=tool['url'], **{'class': 'tool-card'})
        if tool['url'] == current_page:
            tool_card['class'].append('active')
        
        icon_div = soup.new_tag('div', **{'class': 'tool-icon'})
        icon = soup.new_tag('i', **{'class': tool['icon']})
        icon_div.append(icon)
        
        tool_content = soup.new_tag('div', **{'class': 'tool-content'})
        tool_name = soup.new_tag('h3')
        tool_name.string = tool['name']
        tool_desc = soup.new_tag('p')
        tool_desc.string = tool['desc']
        
        tool_content.append(tool_name)
        tool_content.append(tool_desc)
        
        tool_card.append(icon_div)
        tool_card.append(tool_content)
        tools_grid.append(tool_card)
    
    tools_section.append(tools_grid)
    
    # Find the main content and insert the tools grid before the footer
    main_content = soup.find('main')
    if main_content:
        main_content.append(tools_section)
    
    return str(soup)

def update_headers(html_content):
    """Update the Image Tools dropdown in the header"""
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
            
            # Add all image tools to the dropdown
            for tool in image_tools:
                link = soup.new_tag('a', href=tool['url'])
                link.string = tool['name']
                if tool['url'] in html_content:  # Mark current page as active
                    link['class'] = 'active'
                dropdown_content.append(link)
    
    return str(soup)

def process_file(file_path):
    """Process a single HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update headers and add tools grid
        updated_content = update_headers(content)
        updated_content = add_tools_grid(updated_content, os.path.basename(file_path))
        
        # Save the updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Updated: {file_path}")
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False

def main():
    print("Updating image tool pages...")
    
    # Process each image tool page
    for tool in image_tools:
        if os.path.exists(tool['url']):
            process_file(tool['url'])
    
    print("Update complete!")

if __name__ == "__main__":
    main()
