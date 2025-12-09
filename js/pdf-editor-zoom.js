/**
 * PDF Editor Zoom & Pan Module
 * Professional zoom controls with mouse wheel and pan support
 */

export class PDFZoomController {
    constructor(config) {
        this.scale = config.initialScale || 1.0;
        this.minScale = config.minScale || 0.25;
        this.maxScale = config.maxScale || 5.0;
        this.step = config.step || 0.1;
        this.wrapper = config.wrapper;
        this.container = config.container;
        this.onZoomChange = config.onZoomChange || (() => {});
        this.panEnabled = false;
        this.panStart = { x: 0, y: 0 };
        this.panOffset = { x: 0, y: 0 };
        this.isPanning = false;
        
        this.init();
    }
    
    init() {
        if (this.wrapper) {
            this.wrapper.style.transformOrigin = 'top left';
        }
        this.setupMouseWheel();
        this.setupPan();
    }
    
    zoomIn(centerPoint = null) {
        const oldScale = this.scale;
        this.scale = Math.min(this.scale + this.step, this.maxScale);
        this.applyZoom(centerPoint, oldScale);
    }
    
    zoomOut(centerPoint = null) {
        const oldScale = this.scale;
        this.scale = Math.max(this.scale - this.step, this.minScale);
        this.applyZoom(centerPoint, oldScale);
    }
    
    zoomTo(scale, centerPoint = null) {
        const oldScale = this.scale;
        this.scale = Math.max(this.minScale, Math.min(scale, this.maxScale));
        this.applyZoom(centerPoint, oldScale);
    }
    
    reset() {
        this.scale = 1.0;
        this.panOffset = { x: 0, y: 0 };
        this.applyZoom();
    }
    
    fitToWidth() {
        if (!this.wrapper || !this.container) return;
        const containerWidth = this.container.clientWidth - 40; // padding
        const wrapperWidth = this.wrapper.offsetWidth / this.scale;
        this.scale = containerWidth / wrapperWidth;
        this.panOffset = { x: 0, y: 0 };
        this.applyZoom();
    }
    
    fitToPage() {
        if (!this.wrapper || !this.container) return;
        const containerWidth = this.container.clientWidth - 40;
        const containerHeight = this.container.clientHeight - 40;
        const wrapperWidth = this.wrapper.offsetWidth / this.scale;
        const wrapperHeight = this.wrapper.offsetHeight / this.scale;
        const scaleX = containerWidth / wrapperWidth;
        const scaleY = containerHeight / wrapperHeight;
        this.scale = Math.min(scaleX, scaleY);
        this.panOffset = { x: 0, y: 0 };
        this.applyZoom();
    }
    
    applyZoom(centerPoint = null, oldScale = null) {
        if (!this.wrapper) return;
        
        if (centerPoint && oldScale) {
            // Zoom towards mouse position
            const rect = this.wrapper.getBoundingClientRect();
            const containerRect = this.container.getBoundingClientRect();
            const x = centerPoint.x - containerRect.left;
            const y = centerPoint.y - containerRect.top;
            
            const scaleChange = this.scale / oldScale;
            this.panOffset.x = x - (x - this.panOffset.x) * scaleChange;
            this.panOffset.y = y - (y - this.panOffset.y) * scaleChange;
        }
        
        this.wrapper.style.transform = `translate(${this.panOffset.x}px, ${this.panOffset.y}px) scale(${this.scale})`;
        this.onZoomChange(this.scale);
    }
    
    setupMouseWheel() {
        if (!this.container) return;
        
        this.container.addEventListener('wheel', (e) => {
            if (!e.ctrlKey && !e.metaKey) return; // Only zoom with Ctrl/Cmd + wheel
            
            e.preventDefault();
            const centerPoint = { x: e.clientX, y: e.clientY };
            
            if (e.deltaY < 0) {
                this.zoomIn(centerPoint);
            } else {
                this.zoomOut(centerPoint);
            }
        }, { passive: false });
    }
    
    setupPan() {
        if (!this.container) return;
        
        this.container.addEventListener('mousedown', (e) => {
            if (e.button !== 0 || !this.panEnabled) return; // Only left mouse button
            if (this.scale <= 1.0) return; // Only pan when zoomed
            
            this.isPanning = true;
            this.panStart = { x: e.clientX - this.panOffset.x, y: e.clientY - this.panOffset.y };
            this.container.style.cursor = 'grabbing';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!this.isPanning) return;
            
            this.panOffset.x = e.clientX - this.panStart.x;
            this.panOffset.y = e.clientY - this.panStart.y;
            this.applyZoom();
        });
        
        document.addEventListener('mouseup', () => {
            if (this.isPanning) {
                this.isPanning = false;
                if (this.container) {
                    this.container.style.cursor = this.scale > 1.0 ? 'grab' : 'default';
                }
            }
        });
        
        // Enable pan cursor when zoomed
        this.container.addEventListener('mouseenter', () => {
            if (this.scale > 1.0 && !this.isPanning) {
                this.container.style.cursor = 'grab';
            }
        });
    }
    
    enablePan() {
        this.panEnabled = true;
    }
    
    disablePan() {
        this.panEnabled = false;
        this.isPanning = false;
    }
    
    getScale() {
        return this.scale;
    }
    
    getPanOffset() {
        return { ...this.panOffset };
    }
}

