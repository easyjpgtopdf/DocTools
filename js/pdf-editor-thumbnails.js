/**
 * PDF Editor Page Thumbnails Module
 * Professional page navigation with thumbnails sidebar
 */

export class PDFThumbnailsController {
    constructor(config) {
        this.container = config.container;
        this.onPageSelect = config.onPageSelect || (() => {});
        this.currentPage = 1;
        this.totalPages = 1;
        this.thumbnails = [];
        this.sessionId = null;
        this.apiBaseUrl = config.apiBaseUrl || '';
        
        this.init();
    }
    
    init() {
        if (!this.container) return;
        this.render();
    }
    
    setSessionId(sessionId) {
        this.sessionId = sessionId;
    }
    
    setTotalPages(totalPages) {
        this.totalPages = totalPages;
        this.render();
    }
    
    setCurrentPage(pageNumber) {
        this.currentPage = pageNumber;
        this.updateActiveThumbnail();
    }
    
    async loadThumbnail(pageNumber) {
        if (!this.sessionId) return null;
        
        try {
            const { renderPage } = await import('./pdf-editor-api.js?v=3000');
            const result = await renderPage(this.sessionId, pageNumber, 0.2); // Small scale for thumbnail
            return result.image_base64 || result.image || result.image_base64;
        } catch (error) {
            console.error('Error loading thumbnail:', error);
            return null;
        }
    }
    
    async render() {
        if (!this.container) return;
        
        this.container.innerHTML = '';
        this.thumbnails = [];
        
        // Create header
        const header = document.createElement('div');
        header.style.cssText = 'padding: 12px; border-bottom: 1px solid #3a3a3a; font-weight: 600; color: #e5e5e5; font-size: 13px;';
        header.textContent = 'Pages';
        this.container.appendChild(header);
        
        // Create thumbnails container
        const thumbsContainer = document.createElement('div');
        thumbsContainer.style.cssText = 'overflow-y: auto; max-height: calc(100vh - 200px);';
        thumbsContainer.id = 'thumbnails-container';
        this.container.appendChild(thumbsContainer);
        
        // Create thumbnails
        for (let i = 1; i <= this.totalPages; i++) {
            const thumb = await this.createThumbnail(i);
            thumbsContainer.appendChild(thumb);
            this.thumbnails.push(thumb);
        }
        
        this.updateActiveThumbnail();
    }
    
    async createThumbnail(pageNumber) {
        const thumb = document.createElement('div');
        thumb.className = 'pdf-thumbnail';
        thumb.dataset.page = pageNumber;
        thumb.style.cssText = `
            padding: 8px;
            margin: 4px;
            border: 2px solid #3a3a3a;
            border-radius: 4px;
            cursor: pointer;
            background: #2a2a2a;
            transition: all 0.2s;
            position: relative;
        `;
        
        // Page number
        const pageNum = document.createElement('div');
        pageNum.style.cssText = 'text-align: center; color: #9ca3af; font-size: 11px; margin-bottom: 4px;';
        pageNum.textContent = `Page ${pageNumber}`;
        thumb.appendChild(pageNum);
        
        // Thumbnail image
        const img = document.createElement('img');
        img.style.cssText = 'width: 100%; height: auto; border-radius: 2px; background: white; min-height: 80px; display: block;';
        img.alt = `Page ${pageNumber}`;
        thumb.appendChild(img);
        
        // Load thumbnail asynchronously
        this.loadThumbnail(pageNumber).then(base64 => {
            if (base64) {
                img.src = `data:image/png;base64,${base64}`;
            }
        });
        
        // Click handler
        thumb.addEventListener('click', () => {
            this.onPageSelect(pageNumber);
        });
        
        // Hover effect
        thumb.addEventListener('mouseenter', () => {
            thumb.style.borderColor = '#0078d4';
            thumb.style.background = '#333';
        });
        
        thumb.addEventListener('mouseleave', () => {
            if (pageNumber !== this.currentPage) {
                thumb.style.borderColor = '#3a3a3a';
                thumb.style.background = '#2a2a2a';
            }
        });
        
        return thumb;
    }
    
    updateActiveThumbnail() {
        this.thumbnails.forEach((thumb, index) => {
            const pageNum = index + 1;
            if (pageNum === this.currentPage) {
                thumb.style.borderColor = '#0078d4';
                thumb.style.background = '#1a3a5a';
            } else {
                thumb.style.borderColor = '#3a3a3a';
                thumb.style.background = '#2a2a2a';
            }
        });
        
        // Scroll to active thumbnail
        const activeThumb = this.thumbnails[this.currentPage - 1];
        if (activeThumb) {
            activeThumb.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

