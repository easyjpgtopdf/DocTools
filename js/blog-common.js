// Blog Common Components - Shared Header/Footer for all blog pages
// This file ensures all blog pages have consistent structure

/**
 * Initialize blog filter buttons with proper navigation
 */
function initBlogFilters(currentPage = 'all') {
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    // Filter button links mapping
    const filterLinks = {
        'all': 'blog-articles.html',
        'tutorials': 'blog-tutorials.html',
        'tips': 'blog-tips.html',
        'news': 'blog-news.html',
        'guides': 'blog-guides.html'
    };
    
    // Filter button labels
    const filterLabels = {
        'all': 'All Articles',
        'tutorials': 'Tutorials',
        'tips': 'Tips & Tricks',
        'news': 'News & Updates',
        'guides': 'Guides'
    };
    
    filterBtns.forEach(btn => {
        const filter = btn.getAttribute('data-filter');
        const label = filterLabels[filter] || filter;
        
        // Convert button to link
        const link = document.createElement('a');
        link.href = filterLinks[filter] || 'blog.html';
        link.className = btn.className;
        link.textContent = label;
        
        // Set active state
        if (filter === currentPage) {
            link.classList.add('active');
        }
        
        // Replace button with link
        btn.parentNode.replaceChild(link, btn);
    });
}

/**
 * Add filter buttons to page if they don't exist
 */
function addBlogFilters(currentPage = 'all') {
    // Check if filter buttons already exist
    if (document.querySelector('.blog-filters')) {
        return;
    }
    
    const main = document.querySelector('main .container') || document.querySelector('main');
    if (!main) return;
    
    const blogHeader = main.querySelector('.page-header') || main.querySelector('h1');
    if (!blogHeader) return;
    
    // Create filter buttons container
    const filtersDiv = document.createElement('div');
    filtersDiv.className = 'blog-filters';
    filtersDiv.innerHTML = `
        <a href="blog-articles.html" class="filter-btn ${currentPage === 'all' ? 'active' : ''}" data-filter="all">All Articles</a>
        <a href="blog-tutorials.html" class="filter-btn ${currentPage === 'tutorials' ? 'active' : ''}" data-filter="tutorials">Tutorials</a>
        <a href="blog-tips.html" class="filter-btn ${currentPage === 'tips' ? 'active' : ''}" data-filter="tips">Tips & Tricks</a>
        <a href="blog-news.html" class="filter-btn ${currentPage === 'news' ? 'active' : ''}" data-filter="news">News & Updates</a>
        <a href="blog-guides.html" class="filter-btn ${currentPage === 'guides' ? 'active' : ''}" data-filter="guides">Guides</a>
    `;
    
    // Insert after header
    blogHeader.parentNode.insertBefore(filtersDiv, blogHeader.nextSibling);
}

/**
 * Initialize blog page
 */
function initBlogPage(currentPage = 'all') {
    // Add filter buttons if not present
    addBlogFilters(currentPage);
    
    // Initialize existing filter buttons
    initBlogFilters(currentPage);
    
    // Add CSS if not already present
    addBlogFilterStyles();
}

/**
 * Add filter button styles if not present
 */
function addBlogFilterStyles() {
    if (document.getElementById('blog-filter-styles')) {
        return;
    }
    
    const style = document.createElement('style');
    style.id = 'blog-filter-styles';
    style.textContent = `
        .blog-filters {
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
            margin-bottom: 40px;
            margin-top: 30px;
        }
        
        .filter-btn {
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
        }
        
        .filter-btn:hover,
        .filter-btn.active {
            background: linear-gradient(135deg, #4361ee, #3a0ca3);
            color: white;
            border-color: #4361ee;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
            text-decoration: none;
        }
    `;
    
    document.head.appendChild(style);
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Detect current page from URL
        const currentPath = window.location.pathname;
        let currentPage = 'all';
        
        if (currentPath.includes('blog-tutorials')) currentPage = 'tutorials';
        else if (currentPath.includes('blog-tips')) currentPage = 'tips';
        else if (currentPath.includes('blog-news')) currentPage = 'news';
        else if (currentPath.includes('blog-guides')) currentPage = 'guides';
        else if (currentPath.includes('blog-articles')) currentPage = 'all';
        
        initBlogPage(currentPage);
    });
} else {
    // DOM already loaded
    const currentPath = window.location.pathname;
    let currentPage = 'all';
    
    if (currentPath.includes('blog-tutorials')) currentPage = 'tutorials';
    else if (currentPath.includes('blog-tips')) currentPage = 'tips';
    else if (currentPath.includes('blog-news')) currentPage = 'news';
    else if (currentPath.includes('blog-guides')) currentPage = 'guides';
    else if (currentPath.includes('blog-articles')) currentPage = 'all';
    
    initBlogPage(currentPage);
}

