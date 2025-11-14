import re

def get_header_content():
    header_content = '''    <!-- Header -->
    <header>
        <div class="container">
            <nav class="navbar">
                <a href="index.html" class="logo"><img src="images/logo.png" alt="Logo" style="height:54px;"></a>
                <div class="nav-links">
                    <div class="dropdown">
                        <a href="#">Convert to PDF <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="jpg-to-pdf.html">JPG to PDF</a>
                            <a href="word-to-pdf.html">Word to PDF</a>
                            <a href="excel-to-pdf.html">Excel to PDF</a>
                            <a href="ppt-to-pdf.html">PowerPoint to PDF</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">Convert from PDF <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="pdf-to-jpg.html">PDF to JPG</a>
                            <a href="pdf-to-word.html">PDF to Word</a>
                            <a href="pdf-to-excel.html">PDF to Excel</a>
                            <a href="pdf-to-ppt.html">PDF to PowerPoint</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">Pdf Editor <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="merge-pdf.html">Merge PDF</a>
                            <a href="split-pdf.html">Split PDF</a>
                            <a href="compress-pdf.html">Compress PDF</a>
                            <a href="edit-pdf.html">Edit PDF</a>
                            <a href="protect-pdf.html">Protect PDF</a>
                            <a href="unlock-pdf.html">Unlock PDF</a>
                            <a href="watermark-pdf.html">Watermark PDF</a>
                            <a href="crop-pdf.html">Crop PDF</a>
                            <a href="add-page-numbers.html">Add Page Numbers</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">Image Tools <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="image-compressor.html">Image Compressor</a>
                            <a href="image-resizer.html">Image Resizer</a>
                            <a href="image-editor.html">Image Editor</a>
                            <a href="background-remover.html">Image Background Remover</a>
                            <a href="ocr-image.html">OCR Image</a>
                            <a href="image-watermark.html">Image Watermark Tool</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">Design Tools <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="resume-maker.html">Resume Maker</a>
                            <a href="biodata-maker.html">Marriage Biodata Maker</a>
                            <a href="ai-image-generator.html">AI Image Generator</a>
                            <a href="marriage-card.html">Marriage Card</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">Other Tools <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="excel-unlocker.html">Excel Unlocker</a>
                            <a href="protect-excel.html">Protect Excel Sheet</a>
                        </div>
                    </div>
                </div>
                <div class="auth-buttons">
                    <a href="login.html" class="auth-link">Sign In</a>
                    <a href="signup.html" class="auth-btn"><i class="fas fa-user-plus" aria-hidden="true"></i><span>Signup</span></a>
                </div>
                <div id="user-menu" class="user-menu" data-open="false">
                    <button id="user-menu-toggle" class="user-menu-toggle" type="button" aria-haspopup="true" aria-expanded="false" aria-label="Account menu">
                        <span class="user-initial" aria-hidden="true">U</span>
                        <i class="fas fa-chevron-down" aria-hidden="true"></i>
                    </button>
                    <div id="user-dropdown" class="user-dropdown" hidden>
                        <a href="dashboard.html" class="user-dropdown-item"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
                        <a href="accounts.html" class="user-dropdown-item"><i class="fas fa-user"></i> My Account</a>
                        <a href="#" id="logout-btn" class="user-dropdown-item"><i class="fas fa-sign-out-alt"></i> Sign Out</a>
                    </div>
                </div>
            </nav>
        </div>
    </header>'''
    return header_content

def update_header(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove existing header
    content = re.sub(r'<!-- Header -->.*?</header>', '', content, flags=re.DOTALL)
    
    # Add new header
    new_header = get_header_content()
    content = content.replace('<body>', '<body>\n' + new_header, 1)
    
    # Save the updated content
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

# Update protect-excel.html
update_header('protect-excel.html')
print("Header in protect-excel.html has been updated successfully!")
