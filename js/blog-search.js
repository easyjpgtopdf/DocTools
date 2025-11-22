// Modern AI Search Bar for Blog Pages
// Searches all tools and pages on the website

class BlogSearch {
    constructor() {
        this.searchData = this.initializeSearchData();
        this.searchResults = [];
        this.currentQuery = '';
        this.searchInput = null;
        this.resultsContainer = null;
    }

    // Initialize search data - all tools and pages on website
    initializeSearchData() {
        return [
            // PDF Tools
            { title: 'JPG to PDF', url: 'jpg-to-pdf.html', category: 'PDF Tools', description: 'Convert JPG images to PDF format', keywords: ['jpg', 'image', 'pdf', 'convert', 'photo', 'picture'] },
            { title: 'Word to PDF', url: 'word-to-pdf.html', category: 'PDF Tools', description: 'Convert Word documents to PDF', keywords: ['word', 'doc', 'pdf', 'document', 'convert'] },
            { title: 'Excel to PDF', url: 'excel-to-pdf.html', category: 'PDF Tools', description: 'Convert Excel spreadsheets to PDF', keywords: ['excel', 'xls', 'pdf', 'spreadsheet', 'convert'] },
            { title: 'PowerPoint to PDF', url: 'ppt-to-pdf.html', category: 'PDF Tools', description: 'Convert PowerPoint presentations to PDF', keywords: ['powerpoint', 'ppt', 'pdf', 'presentation', 'convert'] },
            { title: 'PDF to JPG', url: 'pdf-to-jpg.html', category: 'PDF Tools', description: 'Convert PDF pages to JPG images', keywords: ['pdf', 'jpg', 'image', 'convert', 'extract'] },
            { title: 'PDF to Word', url: 'pdf-to-word.html', category: 'PDF Tools', description: 'Convert PDF to Word documents', keywords: ['pdf', 'word', 'doc', 'convert', 'document'] },
            { title: 'PDF to Excel', url: 'pdf-to-excel.html', category: 'PDF Tools', description: 'Convert PDF tables to Excel', keywords: ['pdf', 'excel', 'xls', 'convert', 'table'] },
            { title: 'PDF to PowerPoint', url: 'pdf-to-ppt.html', category: 'PDF Tools', description: 'Convert PDF to PowerPoint', keywords: ['pdf', 'powerpoint', 'ppt', 'convert'] },
            
            // PDF Editor Tools
            { title: 'Merge PDF', url: 'merge-pdf.html', category: 'PDF Editor', description: 'Combine multiple PDF files into one', keywords: ['merge', 'combine', 'pdf', 'join', 'multiple'] },
            { title: 'Split PDF', url: 'split-pdf.html', category: 'PDF Editor', description: 'Split PDF into separate files', keywords: ['split', 'divide', 'pdf', 'separate', 'break'] },
            { title: 'Compress PDF', url: 'compress-pdf.html', category: 'PDF Editor', description: 'Reduce PDF file size', keywords: ['compress', 'reduce', 'pdf', 'size', 'optimize'] },
            { title: 'Edit PDF', url: 'edit-pdf.html', category: 'PDF Editor', description: 'Edit PDF documents online', keywords: ['edit', 'modify', 'pdf', 'change', 'update'] },
            { title: 'Protect PDF', url: 'protect-pdf.html', category: 'PDF Editor', description: 'Add password protection to PDF', keywords: ['protect', 'password', 'pdf', 'secure', 'lock'] },
            { title: 'Unlock PDF', url: 'unlock-pdf.html', category: 'PDF Editor', description: 'Remove password from PDF', keywords: ['unlock', 'remove', 'password', 'pdf', 'open'] },
            { title: 'Watermark PDF', url: 'watermark-pdf.html', category: 'PDF Editor', description: 'Add watermark to PDF files', keywords: ['watermark', 'mark', 'pdf', 'brand'] },
            { title: 'Crop PDF', url: 'crop-pdf.html', category: 'PDF Editor', description: 'Crop PDF pages', keywords: ['crop', 'cut', 'pdf', 'trim'] },
            { title: 'Add Page Numbers', url: 'add-page-numbers.html', category: 'PDF Editor', description: 'Add page numbers to PDF', keywords: ['page', 'numbers', 'pdf', 'pagination'] },
            
            // Image Tools
            { title: 'AI Image Repair', url: 'image-repair.html', category: 'Image Tools', description: 'Fix and restore damaged images using AI', keywords: ['repair', 'fix', 'image', 'ai', 'restore', 'damaged'] },
            { title: 'Image Compressor', url: 'image-compressor.html', category: 'Image Tools', description: 'Compress image files', keywords: ['compress', 'image', 'reduce', 'size', 'optimize'] },
            { title: 'Image Resizer', url: 'image-resizer.html', category: 'Image Tools', description: 'Resize images online', keywords: ['resize', 'image', 'change', 'size', 'dimensions'] },
            { title: 'Image Editor', url: 'image-editor.html', category: 'Image Tools', description: 'Edit images online', keywords: ['edit', 'image', 'modify', 'photo', 'picture'] },
            { title: 'Background Remover', url: 'background-remover.html', category: 'Image Tools', description: 'Remove background from images using AI', keywords: ['background', 'remove', 'image', 'ai', 'transparent'] },
            { title: 'OCR Image', url: 'ocr-image.html', category: 'Image Tools', description: 'Extract text from images using OCR', keywords: ['ocr', 'text', 'extract', 'image', 'read'] },
            { title: 'Image Watermark', url: 'image-watermark.html', category: 'Image Tools', description: 'Add watermark to images', keywords: ['watermark', 'image', 'mark', 'brand'] },
            
            // Other Tools
            { title: 'Resume Maker', url: 'resume-maker.html', category: 'Other Tools', description: 'Create professional resumes', keywords: ['resume', 'cv', 'create', 'professional', 'job'] },
            { title: 'Biodata Maker', url: 'biodata-maker.html', category: 'Other Tools', description: 'Create marriage biodata', keywords: ['biodata', 'marriage', 'create', 'profile'] },
            { title: 'AI Image Generator', url: 'ai-image-generator.html', category: 'Other Tools', description: 'Generate images using AI', keywords: ['ai', 'image', 'generate', 'create', 'art'] },
            { title: 'Marriage Card', url: 'marriage-card.html', category: 'Other Tools', description: 'Create marriage invitation cards', keywords: ['marriage', 'card', 'invitation', 'create'] },
            { title: 'Excel Unlocker', url: 'excel-unlocker/', category: 'Other Tools', description: 'Unlock password-protected Excel files', keywords: ['excel', 'unlock', 'password', 'open'] },
            { title: 'Protect Excel', url: 'protect-excel.html', category: 'Other Tools', description: 'Protect Excel sheets with password', keywords: ['excel', 'protect', 'password', 'secure'] },
            
            // Blog Pages
            { title: 'Blog Home', url: 'blog.html', category: 'Blog', description: 'Main blog page with all articles', keywords: ['blog', 'articles', 'home', 'main'] },
            { title: 'All Articles', url: 'blog-articles.html', category: 'Blog', description: 'Browse all blog articles', keywords: ['articles', 'blog', 'all', 'posts'] },
            { title: 'Tutorials', url: 'blog-tutorials.html', category: 'Blog', description: 'Step-by-step tutorials', keywords: ['tutorials', 'guide', 'how', 'learn', 'step'] },
            { title: 'Tips & Tricks', url: 'blog-tips.html', category: 'Blog', description: 'Tips and tricks for productivity', keywords: ['tips', 'tricks', 'productivity', 'help', 'advice'] },
            { title: 'News & Updates', url: 'blog-news.html', category: 'Blog', description: 'Latest news and updates', keywords: ['news', 'updates', 'latest', 'recent'] },
            { title: 'Guides', url: 'blog-guides.html', category: 'Blog', description: 'Comprehensive guides', keywords: ['guides', 'documentation', 'help', 'manual'] },
            
            // Other Pages
            { title: 'Pricing', url: 'pricing.html', category: 'Info', description: 'View pricing plans', keywords: ['pricing', 'price', 'plans', 'cost', 'subscription'] },
            { title: 'Dashboard', url: 'dashboard.html', category: 'Account', description: 'User account dashboard', keywords: ['dashboard', 'account', 'profile', 'user'] },
        ];
    }

    // Smart search with fuzzy matching
    search(query) {
        if (!query || query.trim().length < 2) {
            return [];
        }

        const searchTerm = query.toLowerCase().trim();
        const results = [];
        const exactMatches = [];
        const partialMatches = [];

        this.searchData.forEach(item => {
            const titleLower = item.title.toLowerCase();
            const descLower = item.description.toLowerCase();
            const categoryLower = item.category.toLowerCase();
            const keywords = item.keywords.map(k => k.toLowerCase());

            let score = 0;

            // Exact title match (highest priority)
            if (titleLower === searchTerm) {
                score = 100;
            } else if (titleLower.includes(searchTerm)) {
                score = 80;
            } else if (searchTerm.includes(titleLower)) {
                score = 70;
            }

            // Description match
            if (descLower.includes(searchTerm)) {
                score += 30;
            }

            // Category match
            if (categoryLower.includes(searchTerm)) {
                score += 20;
            }

            // Keywords match
            keywords.forEach(keyword => {
                if (keyword === searchTerm) {
                    score += 40;
                } else if (keyword.includes(searchTerm) || searchTerm.includes(keyword)) {
                    score += 20;
                }
            });

            // Fuzzy matching for words
            const searchWords = searchTerm.split(/\s+/);
            searchWords.forEach(word => {
                if (word.length >= 3) {
                    if (titleLower.includes(word)) score += 15;
                    if (descLower.includes(word)) score += 10;
                    keywords.forEach(keyword => {
                        if (keyword.includes(word) || word.includes(keyword)) {
                            score += 10;
                        }
                    });
                }
            });

            if (score > 0) {
                const result = { ...item, score };
                
                if (score >= 70) {
                    exactMatches.push(result);
                } else {
                    partialMatches.push(result);
                }
            }
        });

        // Sort and combine results
        exactMatches.sort((a, b) => b.score - a.score);
        partialMatches.sort((a, b) => b.score - a.score);

        return [...exactMatches, ...partialMatches].slice(0, 10);
    }

    // Create search bar HTML
    createSearchBar() {
        return `
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
        `;
    }

    // Initialize search bar
    init() {
        const main = document.querySelector('main .container') || document.querySelector('main');
        if (!main) return;

        const pageHeader = main.querySelector('.page-header') || main.querySelector('h1');
        if (!pageHeader) return;

        // Create search bar
        const searchHTML = this.createSearchBar();
        const searchDiv = document.createElement('div');
        searchDiv.innerHTML = searchHTML;
        main.insertBefore(searchDiv, pageHeader);

        // Get elements
        this.searchInput = document.getElementById('blogSearchInput');
        this.resultsContainer = document.getElementById('blogSearchResults');
        const clearBtn = document.getElementById('blogSearchClear');

        if (!this.searchInput || !this.resultsContainer) return;

        // Add event listeners
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });

        this.searchInput.addEventListener('focus', () => {
            if (this.searchResults.length > 0) {
                this.showResults();
            }
        });

        clearBtn.addEventListener('click', () => {
            this.clearSearch();
        });

        // Close results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.blog-search-container')) {
                this.hideResults();
            }
        });

        // Handle keyboard shortcuts
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearSearch();
                this.searchInput.blur();
            } else if (e.key === 'Enter' && this.searchResults.length > 0) {
                window.location.href = this.searchResults[0].url;
            }
        });
    }

    // Handle search input
    handleSearch(query) {
        this.currentQuery = query;
        const clearBtn = document.getElementById('blogSearchClear');

        if (!query || query.trim().length < 2) {
            this.hideResults();
            if (clearBtn) clearBtn.style.display = 'none';
            return;
        }

        if (clearBtn) clearBtn.style.display = 'block';

        // Perform search
        this.searchResults = this.search(query);

        if (this.searchResults.length > 0) {
            this.displayResults();
            this.showResults();
        } else {
            this.displayNoResults();
            this.showResults();
        }
    }

    // Display search results
    displayResults() {
        if (!this.resultsContainer) return;

        let html = '<div class="blog-search-results-header">';
        html += `<strong>${this.searchResults.length}</strong> result${this.searchResults.length > 1 ? 's' : ''} found for "<strong>${this.currentQuery}</strong>"`;
        html += '</div>';

        this.searchResults.forEach(result => {
            html += `
                <a href="${result.url}" class="blog-search-result-item">
                    <div class="blog-search-result-icon">
                        <i class="fas fa-${this.getIconForCategory(result.category)}"></i>
                    </div>
                    <div class="blog-search-result-content">
                        <div class="blog-search-result-title">${this.highlightMatch(result.title, this.currentQuery)}</div>
                        <div class="blog-search-result-description">${result.description}</div>
                        <div class="blog-search-result-category">${result.category}</div>
                    </div>
                    <div class="blog-search-result-arrow">
                        <i class="fas fa-chevron-right"></i>
                    </div>
                </a>
            `;
        });

        this.resultsContainer.innerHTML = html;
    }

    // Display no results message
    displayNoResults() {
        if (!this.resultsContainer) return;

        this.resultsContainer.innerHTML = `
            <div class="blog-search-no-results">
                <i class="fas fa-search"></i>
                <h3>No results found</h3>
                <p>Try searching for different keywords or browse our categories</p>
                <div class="blog-search-suggestions">
                    <span>Suggestions:</span>
                    <a href="blog-articles.html">All Articles</a>
                    <a href="blog-tutorials.html">Tutorials</a>
                    <a href="blog-tips.html">Tips & Tricks</a>
                </div>
            </div>
        `;
    }

    // Highlight matching text
    highlightMatch(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    // Get icon for category
    getIconForCategory(category) {
        const icons = {
            'PDF Tools': 'file-pdf',
            'PDF Editor': 'edit',
            'Image Tools': 'image',
            'Other Tools': 'tools',
            'Blog': 'newspaper',
            'Info': 'info-circle',
            'Account': 'user-circle'
        };
        return icons[category] || 'circle';
    }

    // Show results
    showResults() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'block';
        }
    }

    // Hide results
    hideResults() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'none';
        }
    }

    // Clear search
    clearSearch() {
        if (this.searchInput) {
            this.searchInput.value = '';
            this.currentQuery = '';
            this.searchResults = [];
        }
        this.hideResults();
        const clearBtn = document.getElementById('blogSearchClear');
        if (clearBtn) clearBtn.style.display = 'none';
    }
}

// Initialize search on page load
let blogSearchInstance = null;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        blogSearchInstance = new BlogSearch();
        blogSearchInstance.init();
    });
} else {
    blogSearchInstance = new BlogSearch();
    blogSearchInstance.init();
}

