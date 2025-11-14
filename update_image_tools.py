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
    'image-watermark-convert.html'
]

def update_header(html_content):
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
            # Check if AI Image Repair link already exists
            if not dropdown_content.find('a', string='AI Image Repair'):
                # Create and insert the new link at the top of the dropdown
                repair_link = soup.new_tag('a', href='image-repair.html')
                repair_link.string = 'AI Image Repair'
                dropdown_content.insert(0, repair_link)
                dropdown_content.insert(1, soup.new_tag('div', **{'class': 'dropdown-divider'}))
    
    return str(soup)

def update_middle_panel(html_content):
    """Update the middle panel with a grid of image tools"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the main content area (this might need adjustment based on your HTML structure)
    main_content = soup.find('main') or soup.find('div', class_='container')
    
    if main_content:
        # Check if tools grid already exists
        if not main_content.find('div', class_='tools-grid'):
            # Create the tools grid section
            tools_grid = soup.new_tag('div', **{'class': 'tools-grid'})
            
            # Add CSS for the grid
            style = soup.new_tag('style')
            style.string = """
                .tools-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }
                .tool-card {
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    transition: transform 0.3s, box-shadow 0.3s;
                    text-decoration: none;
                    color: #333;
                }
                .tool-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.15);
                }
                .tool-icon {
                    background: #f0f4ff;
                    padding: 20px;
                    text-align: center;
                    color: #4a6cf7;
                    font-size: 2rem;
                }
                .tool-info {
                    padding: 15px;
                }
                .tool-info h3 {
                    margin: 0 0 10px 0;
                    color: #1a1a1a;
                }
                .tool-info p {
                    margin: 0;
                    color: #666;
                    font-size: 0.9rem;
                }
            """
            
            # Add the tools grid HTML
            tools_html = """
            <div class="tools-grid">
                <a href="image-repair.html" class="tool-card">
                    <div class="tool-icon">
                        <i class="fas fa-magic"></i>
                    </div>
                    <div class="tool-info">
                        <h3>AI Image Repair</h3>
                        <p>Fix blurry, scratched or damaged photos with AI</p>
                    </div>
                </a>
                <a href="image-compressor.html" class="tool-card">
                    <div class="tool-icon">
                        <i class="fas fa-compress-alt"></i>
                    </div>
                    <div class="tool-info">
                        <h3>Image Compressor</h3>
                        <p>Reduce image file size without losing quality</p>
                    </div>
                </a>
                <a href="image-resizer.html" class="tool-card">
                    <div class="tool-icon">
                        <i class="fas fa-expand-alt"></i>
                    </div>
                    <div class="tool-info">
                        <h3>Image Resizer</h3>
                        <p>Resize images to any dimension</p>
                    </div>
                </a>
                <a href="image-editor.html" class="tool-card">
                    <div class="tool-icon">
                        <i class="fas fa-edit"></i>
                    </div>
                    <div class="tool-info">
                        <h3>Image Editor</h3>
                        <p>Edit and enhance your images online</p>
                    </div>
                </a>
                <a href="background-remover.html" class="tool-card">
                    <div class="tool-icon">
                        <i class="fas fa-cut"></i>
                    </div>
                    <div class="tool-info">
                        <h3>Background Remover</h3>
                        <p>Remove background from images automatically</p>
                    </div>
                </a>
                <a href="ocr-image.html" class="tool-card">
                    <div class="tool-icon">
                        <i class="fas fa-font"></i>
                    </div>
                    <div class="tool-info">
                        <h3>OCR Image</h3>
                        <p>Extract text from images with OCR technology</p>
                    </div>
                </a>
                <a href="image-watermark.html" class="tool-card">
                    <div class="tool-icon">
                        <i class="fas fa-stamp"></i>
                    </div>
                    <div class="tool-info">
                        <h3>Image Watermark</h3>
                        <p>Add watermarks to your images</p>
                    </div>
                </a>
            </div>
            """
            
            tools_grid_soup = BeautifulSoup(tools_html, 'html.parser')
            
            # Insert the grid after the main heading or at the top of the main content
            heading = main_content.find(['h1', 'h2', 'h3'])
            if heading:
                heading.insert_after(style)
                heading.insert_after(tools_grid_soup)
            else:
                main_content.insert(0, style)
                main_content.insert(1, tools_grid_soup)
    
    return str(soup)

def update_image_tools():
    for page in image_tools_pages:
        try:
            with open(page, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update header
            updated_content = update_header(content)
            
            # Update middle panel
            updated_content = update_middle_panel(updated_content)
            
            # Save the updated content
            with open(page, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            print(f"Updated: {page}")
            
        except Exception as e:
            print(f"Error updating {page}: {str(e)}")

if __name__ == "__main__":
    print("Updating image tool pages...")
    update_image_tools()
    print("Update complete!")
