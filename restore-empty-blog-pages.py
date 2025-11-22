#!/usr/bin/env python3
"""
Restore Empty Blog Pages:
- blog.html (Blog Home)
- blog-tutorials.html (Tutorials)
- blog-tips.html (Tips & Tricks)
- blog-news.html (News & Updates)
- blog-guides.html (Guides)
"""

import os
from pathlib import Path

def get_blog_page_template(page_type, title, description):
    """Generate blog page template based on type"""
    
    if page_type == 'home':
        # Blog home page
        page_header = '''            <div class="blog-header">
                <h1><i class="fas fa-newspaper"></i> Blog & Articles</h1>
                <p>Read our latest articles, tutorials, and tips about PDF tools, image editing, and document management.</p>
            </div>'''
        filter_active = 'blog.html'
    elif page_type == 'tutorials':
        page_header = '''            <div class="page-header">
                <h1><i class="fas fa-graduation-cap"></i> Tutorials</h1>
                <p>Step-by-step tutorials to help you master PDF tools and image editing.</p>
            </div>'''
        filter_active = 'blog-tutorials.html'
    elif page_type == 'tips':
        page_header = '''            <div class="page-header">
                <h1><i class="fas fa-lightbulb"></i> Tips & Tricks</h1>
                <p>Pro tips and tricks to boost your productivity with PDF and image tools.</p>
            </div>'''
        filter_active = 'blog-tips.html'
    elif page_type == 'news':
        page_header = '''            <div class="page-header">
                <h1><i class="fas fa-newspaper"></i> News & Updates</h1>
                <p>Latest news, updates, and announcements about our tools and features.</p>
            </div>'''
        filter_active = 'blog-news.html'
    elif page_type == 'guides':
        page_header = '''            <div class="page-header">
                <h1><i class="fas fa-book"></i> Guides</h1>
                <p>Comprehensive guides to help you make the most of our PDF and image tools.</p>
            </div>'''
        filter_active = 'blog-guides.html'
    
    template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - easyjpgtopdf Blog</title>
    <meta name="description" content="{description}">
    <link rel="stylesheet" href="css/footer.css">
    <link rel="stylesheet" href="css/header.css">
    <link rel="stylesheet" href="css/theme-modern.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {{
            background: #f5f7ff;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        main {{
            flex: 1;
            padding: 24px 24px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .page-header {{
            text-align: center;
            margin-bottom: 24px;
        }}
        
        .blog-header {{
            text-align: center;
            margin-bottom: 24px;
        }}
        
        .page-header h1, .blog-header h1 {{
            font-size: 2.5rem;
            color: #0b1630;
            margin-bottom: 16px;
            font-weight: 700;
        }}
        
        .page-header p, .blog-header p {{
            font-size: 1.1rem;
            color: #56607a;
        }}
        
        /* Modern AI Search Bar */
        .blog-search-container {{
            margin: 20px 0 25px;
            width: 100%;
        }}
        
        .blog-search-wrapper {{
            position: relative;
            max-width: 650px;
            margin: 0 auto;
        }}
        
        .blog-search-input-wrapper {{
            position: relative;
            display: flex;
            align-items: center;
            background: white;
            border: 2px solid rgba(67, 97, 238, 0.2);
            border-radius: 999px;
            padding: 12px 20px;
            box-shadow: 0 4px 12px rgba(67, 97, 238, 0.1);
            transition: all 0.3s;
        }}
        
        .blog-search-input-wrapper:focus-within {{
            border-color: #4361ee;
            box-shadow: 0 6px 20px rgba(67, 97, 238, 0.2);
            transform: translateY(-2px);
        }}
        
        .blog-search-icon {{
            color: #4361ee;
            font-size: 1rem;
            margin-right: 10px;
        }}
        
        .blog-search-input {{
            flex: 1;
            border: none;
            outline: none;
            font-size: 1rem;
            color: #0b1630;
            background: transparent;
            font-weight: 500;
        }}
        
        .blog-search-input::placeholder {{
            color: #7a8196;
        }}
        
        .blog-search-clear {{
            background: none;
            border: none;
            color: #7a8196;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 50%;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .blog-search-clear:hover {{
            background: rgba(67, 97, 238, 0.1);
            color: #4361ee;
        }}
        
        .blog-search-results {{
            position: absolute;
            top: calc(100% + 10px);
            left: 0;
            right: 0;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            max-height: 500px;
            overflow-y: auto;
            z-index: 1000;
            margin-top: 8px;
        }}
        
        /* Advertisement Space */
        .ad-banner-top {{
            width: 100%;
            min-height: 100px;
            background: #f5f7ff;
            border: 2px dashed #dbe2ef;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #64748b;
            font-size: 0.9rem;
            margin: 30px 0;
            padding: 20px;
            text-align: center;
        }}
        
        .ad-banner-bottom {{
            width: 100%;
            min-height: 100px;
            background: #f5f7ff;
            border: 2px dashed #dbe2ef;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #64748b;
            font-size: 0.9rem;
            margin: 30px 0;
            padding: 20px;
            text-align: center;
        }}
        
        /* Blog Filter Buttons */
        .blog-filters {{
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
            margin-bottom: 40px;
            margin-top: 30px;
        }}
        
        .filter-btn {{
            padding: 10px 24px;
            border: 2px solid rgba(67, 97, 238, 0.2);
            background: white;
            color: #4361ee;
            border-radius: 999px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }}
        
        .filter-btn:hover,
        .filter-btn.active {{
            background: linear-gradient(135deg, #4361ee, #3a0ca3);
            color: white;
            border-color: #4361ee;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
            text-decoration: none;
        }}
        
        @media (max-width: 768px) {{
            .blog-search-container {{
                margin: 15px 0 20px;
            }}
            
            .page-header h1, .blog-header h1 {{
                font-size: 2rem;
            }}
            
            .ad-banner-top,
            .ad-banner-bottom {{
                min-height: 80px;
                margin: 20px 0;
            }}
        }}
    </style>

    <link rel="stylesheet" href="css/voice-assistant.css">
</head>
<body>
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
                            <a href="edit-pdf.html">Pdf Editor</a>
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
                        <a href="#">Other Tools <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="resume-maker.html">Resume Maker</a>
                            <a href="biodata-maker.html">Marrige Biodata-Data Maker</a>
                            <a href="ai-image-generator.html">AI Image Generator</a>
                            <a href="marriage-card.html">Marriage Card</a>
                            <a href="excel-unlocker/" target="_blank">Excel Unlocker</a>
                            <a href="protect-excel.html">Protect Excel Sheet</a>
                        </div>
                    </div>
                    <div class="dropdown">
                        <a href="#">More <i class="fas fa-chevron-down"></i></a>
                        <div class="dropdown-content">
                            <a href="pricing.html">Pricing</a>
                            <div class="dropdown">
                                <a href="#">Blog/Articles <i class="fas fa-chevron-down"></i></a>
                                <div class="dropdown-content">
                                    <a href="blog.html">Blog Home</a>
                                    <a href="blog-articles.html">All Articles</a>
                                    <a href="blog-tutorials.html">Tutorials</a>
                                    <a href="blog-tips.html">Tips & Tricks</a>
                                    <a href="blog-news.html">News & Updates</a>
                                    <a href="blog-guides.html">Guides</a>
                                </div>
                            </div>
                            <a href="https://apnaonlineservic.com" target="_blank">Shop-ApnaOnline</a>
                            <a href="https://aimathmaster.com" target="_blank">AI-Math Master</a>
                        </div>
                    </div>
                </div>
                <div class="auth-buttons">
                    <a href="login.html" class="auth-link">Sign In</a>
                    <a href="signup.html" class="auth-btn"><i class="fas fa-user-plus"></i><span>Signup</span></a>
                </div>
                <div id="user-menu" class="user-menu" data-open="false">
                    <button id="user-menu-toggle" class="user-menu-toggle" type="button">
                        <span class="user-initial">U</span>
                        <i class="fas fa-chevron-down"></i>
                    </button>
                    <div class="user-dropdown" id="user-dropdown" hidden>
                        <a href="dashboard.html#dashboard-overview"><i class="fas fa-user-circle"></i> Account Dashboard</a>
                        <a href="dashboard.html#dashboard-billing"><i class="fas fa-file-invoice"></i> Billing Details</a>
                        <a href="dashboard.html#dashboard-payments"><i class="fas fa-wallet"></i> Payment History</a>
                        <a href="dashboard.html#dashboard-orders"><i class="fas fa-clipboard-list"></i> Orders & Subscriptions</a>
                        <a href="accounts.html#login"><i class="fas fa-user-cog"></i> Account Center</a>
                        <button type="button" id="logout-button" class="dropdown-logout"><i class="fas fa-sign-out-alt"></i> Sign out</button>
                    </div>
                </div>
            </nav>
        </div>
    </header>

    <main>
        <div class="container">
{page_header}
            <!-- Blog Search Bar -->
            <div class="blog-search-container">
                <div class="blog-search-wrapper">
                    <div class="blog-search-input-wrapper">
                        <i class="fas fa-search blog-search-icon"></i>
                        <input 
                            type="text" 
                            class="blog-search-input" 
                            id="blogSearchInput"
                            placeholder="Search all tools and pages..." 
                            autocomplete="off"
                        />
                        <button class="blog-search-clear" id="blogSearchClear" style="display: none;">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="blog-search-results" id="blogSearchResults" style="display: none;"></div>
                </div>
            </div>
            <!-- Jarvis Voice Assistant Button -->
            <div class="voice-assistant-container" style="text-align: center; margin: 15px 0;">
                <button id="voiceAssistantBtn" class="voice-assistant-btn" aria-label="Start voice command">
                    <i class="fas fa-microphone"></i>
                    <span class="voice-assistant-text">Voice Search</span>
                </button>
                <div id="voiceStatus" class="voice-status" style="display: none;"></div>
            </div>

            <!-- Advertisement Banner Top -->
            <div class="ad-banner-top">
                <p><i class="fas fa-ad"></i> Advertisement Space</p>
            </div>

            <!-- Blog Filter Buttons -->
            <div class="blog-filters">
                <a href="blog-articles.html" class="filter-btn{' active' if filter_active == 'blog-articles.html' else ''}" data-filter="all">All Articles</a>
                <a href="blog-tutorials.html" class="filter-btn{' active' if filter_active == 'blog-tutorials.html' else ''}" data-filter="tutorials">Tutorials</a>
                <a href="blog-tips.html" class="filter-btn{' active' if filter_active == 'blog-tips.html' else ''}" data-filter="tips">Tips & Tricks</a>
                <a href="blog-news.html" class="filter-btn{' active' if filter_active == 'blog-news.html' else ''}" data-filter="news">News & Updates</a>
                <a href="blog-guides.html" class="filter-btn{' active' if filter_active == 'blog-guides.html' else ''}" data-filter="guides">Guides</a>
            </div>

            <!-- Blog Content Area -->
            <div class="blog-content-area" style="margin-top: 40px; text-align: center; padding: 60px 20px; color: #56607a;">
                <i class="fas fa-newspaper" style="font-size: 4rem; color: #dbe2ef; margin-bottom: 20px;"></i>
                <h2 style="font-size: 1.5rem; color: #0b1630; margin-bottom: 10px;">Content Coming Soon</h2>
                <p style="font-size: 1rem; max-width: 600px; margin: 0 auto;">We're working on adding great content here. Check back soon!</p>
            </div>
            
    </main>

    <!-- Blog Common Script -->
    <script src="js/blog-common.js"></script>
    
    <!-- Blog Search Script -->
    <script src="js/blog-search.js"></script>
    
    <!-- Voice Assistant Script -->
    <script src="js/voice-assistant.js"></script>
    
    <script type="module">
        const isLocalFileProtocol = window.location.protocol === 'file:';
        if (!isLocalFileProtocol) {{
            import('./js/auth.js').catch(err => {{
                console.error('❌ Failed to load auth.js:', err);
            }});
        }}
    </script>

    
    <!-- Advertisement Banner Bottom -->
    <div class="ad-banner-bottom">
        <p><i class="fas fa-ad"></i> Advertisement Space</p>
    </div>

    <footer>
        <div class="container footer-inner">
            <div class="footer-company-links">
                <span>Company</span>
                <a href="index.html#about">About Us</a>
                <a href="index.html#contact">Contact</a>
                <a href="pricing.html">Pricing</a>
                <a href="privacy-policy.html">Privacy Policy</a>
                <a href="terms-of-service.html">Terms of Service</a>
                <a href="dmca-en.html">DMCA</a>
                <a href="blog.html">Blog</a>
            </div>
            <p class="footer-brand-line">&copy; easyjpgtopdf &mdash; Free PDF &amp; Image Tools for everyone. All rights reserved.</p>
            <p class="footer-credits">
                Thanks to Font Awesome, Google Fonts, jsPDF, pdf.js, pdf-lib, Mammoth, Tesseract.js, IMG.LY, Firebase, Unsplash photographers, and every open-source contributor powering this site.
                <a href="attributions.html">See full acknowledgements</a>.
            </p>
        </div>
    </footer>

    <script>
        // Voice Assistant + Blog Search Integration
        document.addEventListener('DOMContentLoaded', function() {{
            const voiceBtn = document.getElementById('voiceAssistantBtn');
            const blogSearchInput = document.getElementById('blogSearchInput');
            const blogSearchInstance = window.blogSearchInstance;
            
            if (voiceBtn && blogSearchInput && blogSearchInstance) {{
                // Listen for voice recognition results
                document.addEventListener('voiceCommand', function(event) {{
                    const command = event.detail.command.toLowerCase();
                    
                    // Search in blog using voice command
                    if (blogSearchInput && blogSearchInstance) {{
                        blogSearchInput.value = command;
                        blogSearchInstance.handleSearch(command);
                        
                        // Show search results
                        const resultsContainer = document.getElementById('blogSearchResults');
                        if (resultsContainer) {{
                            resultsContainer.style.display = 'block';
                        }}
                    }}
                }});
                
                // Enhanced voice commands for blog functions
                const blogVoiceCommands = {{
                    'all articles': 'blog-articles.html',
                    'articles': 'blog-articles.html',
                    'all article': 'blog-articles.html',
                    'tutorials': 'blog-tutorials.html',
                    'tutorial': 'blog-tutorials.html',
                    'tips': 'blog-tips.html',
                    'tips and tricks': 'blog-tips.html',
                    'tips & tricks': 'blog-tips.html',
                    'news': 'blog-news.html',
                    'updates': 'blog-news.html',
                    'news and updates': 'blog-news.html',
                    'news & updates': 'blog-news.html',
                    'guides': 'blog-guides.html',
                    'guide': 'blog-guides.html',
                    'search': function(cmd) {{
                        if (blogSearchInput) {{
                            blogSearchInput.focus();
                        }}
                    }},
                    'search for': function(cmd) {{
                        if (blogSearchInput && blogSearchInstance) {{
                            const searchTerm = cmd.replace('search for', '').trim();
                            blogSearchInput.value = searchTerm;
                            blogSearchInstance.handleSearch(searchTerm);
                        }}
                    }},
                    'find': function(cmd) {{
                        if (blogSearchInput && blogSearchInstance) {{
                            const searchTerm = cmd.replace('find', '').trim();
                            blogSearchInput.value = searchTerm;
                            blogSearchInstance.handleSearch(searchTerm);
                        }}
                    }},
                    'pdf tools': function(cmd) {{
                        if (blogSearchInput && blogSearchInstance) {{
                            blogSearchInput.value = 'pdf';
                            blogSearchInstance.handleSearch('pdf');
                        }}
                    }},
                    'image tools': function(cmd) {{
                        if (blogSearchInput && blogSearchInstance) {{
                            blogSearchInput.value = 'image';
                            blogSearchInstance.handleSearch('image');
                        }}
                    }},
                }};
                
                // Override voice command handler if needed
                if (window.voiceAssistant) {{
                    const originalHandler = window.voiceAssistant.handleVoiceCommand;
                    window.voiceAssistant.handleVoiceCommand = function(command) {{
                        // Check blog-specific commands first
                        const cmd = command.toLowerCase().trim();
                        
                        if (blogVoiceCommands[cmd]) {{
                            const target = blogVoiceCommands[cmd];
                            if (typeof target === 'function') {{
                                target(cmd);
                            }} else if (target.startsWith('blog-')) {{
                                window.location.href = target;
                            }} else {{
                                // Search keyword
                                if (blogSearchInput && blogSearchInstance) {{
                                    blogSearchInput.value = target;
                                    blogSearchInstance.handleSearch(target);
                                }}
                            }}
                            return true;
                        }}
                        
                        // Default voice command handling
                        if (originalHandler) {{
                            return originalHandler.call(this, command);
                        }}
                        
                        // Fallback: search in blog
                        if (blogSearchInput && blogSearchInstance) {{
                            blogSearchInput.value = command;
                            blogSearchInstance.handleSearch(command);
                            return true;
                        }}
                        
                        return false;
                    }};
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    return template

def main():
    """Main function"""
    root_dir = Path(__file__).parent
    
    # Define blog pages to restore
    blog_pages = [
        {
            'file': 'blog.html',
            'type': 'home',
            'title': 'Blog & Articles',
            'description': 'Read our latest articles, tutorials, and tips about PDF tools, image editing, and document management.'
        },
        {
            'file': 'blog-tutorials.html',
            'type': 'tutorials',
            'title': 'Tutorials',
            'description': 'Step-by-step tutorials to help you master PDF tools and image editing.'
        },
        {
            'file': 'blog-tips.html',
            'type': 'tips',
            'title': 'Tips & Tricks',
            'description': 'Pro tips and tricks to boost your productivity with PDF and image tools.'
        },
        {
            'file': 'blog-news.html',
            'type': 'news',
            'title': 'News & Updates',
            'description': 'Latest news, updates, and announcements about our tools and features.'
        },
        {
            'file': 'blog-guides.html',
            'type': 'guides',
            'title': 'Guides',
            'description': 'Comprehensive guides to help you make the most of our PDF and image tools.'
        }
    ]
    
    print("🔧 Restoring Empty Blog Pages...\n")
    print("="*80)
    
    restored_count = 0
    
    for page_info in blog_pages:
        file_path = root_dir / page_info['file']
        
        # Check if file is empty or doesn't exist
        file_size = 0
        if file_path.exists():
            file_size = file_path.stat().st_size
        
        if file_size == 0:
            print(f"\n📄 Restoring: {page_info['file']} (was empty)")
            
            # Generate template
            template = get_blog_page_template(
                page_info['type'],
                page_info['title'],
                page_info['description']
            )
            
            # Write file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(template)
                print(f"   ✅ Restored successfully!")
                restored_count += 1
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        else:
            print(f"\n📄 {page_info['file']}: Already has content ({file_size} bytes)")
    
    # Summary
    print("\n" + "="*80)
    print(f"✅ Restored {restored_count} empty blog pages")
    print("="*80)
    print("\nAll blog pages should now work correctly!")
    print("  • blog.html - Blog Home")
    print("  • blog-articles.html - All Articles")
    print("  • blog-tutorials.html - Tutorials")
    print("  • blog-tips.html - Tips & Tricks")
    print("  • blog-news.html - News & Updates")
    print("  • blog-guides.html - Guides")

if __name__ == '__main__':
    main()

