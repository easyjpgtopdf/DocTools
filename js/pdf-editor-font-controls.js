/**
 * PDF Editor Font Controls Module
 * Professional font toolbar
 */

export class FontControlsController {
    constructor(config) {
        this.container = config.container;
        this.onFontChange = config.onFontChange || (() => {});
        this.currentFont = {
            family: 'Helvetica',
            size: 12,
            bold: false,
            italic: false,
            color: '#000000',
            align: 'left'
        };
        
        this.init();
    }
    
    init() {
        if (!this.container) return;
        this.render();
    }
    
    render() {
        if (!this.container) return;
        
        this.container.innerHTML = '';
        this.container.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: #2a2a2a;
            border-bottom: 1px solid #3a3a3a;
            flex-wrap: wrap;
        `;
        
        // Font Family
        const fontFamily = this.createSelect('font-family', [
            { value: 'Helvetica', label: 'Helvetica' },
            { value: 'Times-Roman', label: 'Times' },
            { value: 'Courier', label: 'Courier' },
            { value: 'Arial', label: 'Arial' }
        ], this.currentFont.family);
        this.container.appendChild(fontFamily);
        
        // Font Size
        const fontSize = this.createInput('number', 'font-size', this.currentFont.size, { min: 6, max: 72, step: 1 });
        fontSize.style.width = '60px';
        this.container.appendChild(fontSize);
        
        // Bold
        const boldBtn = this.createButton('bold', 'fas fa-bold', this.currentFont.bold);
        this.container.appendChild(boldBtn);
        
        // Italic
        const italicBtn = this.createButton('italic', 'fas fa-italic', this.currentFont.italic);
        this.container.appendChild(italicBtn);
        
        // Color Picker
        const colorPicker = this.createInput('color', 'font-color', this.currentFont.color);
        colorPicker.style.width = '40px';
        colorPicker.style.height = '30px';
        this.container.appendChild(colorPicker);
        
        // Text Align
        const alignLeft = this.createButton('align-left', 'fas fa-align-left', this.currentFont.align === 'left');
        const alignCenter = this.createButton('align-center', 'fas fa-align-center', this.currentFont.align === 'center');
        const alignRight = this.createButton('align-right', 'fas fa-align-right', this.currentFont.align === 'right');
        this.container.appendChild(alignLeft);
        this.container.appendChild(alignCenter);
        this.container.appendChild(alignRight);
    }
    
    createSelect(name, options, value) {
        const select = document.createElement('select');
        select.id = `font-${name}`;
        select.style.cssText = 'padding: 6px 8px; background: #1a1a1a; border: 1px solid #3a3a3a; border-radius: 4px; color: #e5e5e5; font-size: 12px; cursor: pointer;';
        
        options.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.label;
            if (opt.value === value) option.selected = true;
            select.appendChild(option);
        });
        
        select.addEventListener('change', () => {
            this.currentFont[name] = select.value;
            this.onFontChange({ ...this.currentFont });
        });
        
        return select;
    }
    
    createInput(type, name, value, attrs = {}) {
        const input = document.createElement('input');
        input.type = type;
        input.id = `font-${name}`;
        input.value = value;
        input.style.cssText = 'padding: 6px 8px; background: #1a1a1a; border: 1px solid #3a3a3a; border-radius: 4px; color: #e5e5e5; font-size: 12px;';
        
        Object.entries(attrs).forEach(([key, val]) => {
            input.setAttribute(key, val);
        });
        
        input.addEventListener('change', () => {
            this.currentFont[name] = type === 'number' ? parseInt(input.value) : input.value;
            this.onFontChange({ ...this.currentFont });
        });
        
        return input;
    }
    
    createButton(name, icon, active = false) {
        const btn = document.createElement('button');
        btn.id = `font-${name}`;
        btn.innerHTML = `<i class="${icon}"></i>`;
        btn.style.cssText = `
            padding: 6px 10px;
            background: ${active ? '#0078d4' : '#1a1a1a'};
            border: 1px solid ${active ? '#0078d4' : '#3a3a3a'};
            border-radius: 4px;
            color: ${active ? 'white' : '#e5e5e5'};
            cursor: pointer;
            font-size: 12px;
        `;
        
        btn.addEventListener('click', () => {
            if (name.startsWith('align-')) {
                // Handle align buttons
                document.querySelectorAll('[id^="font-align-"]').forEach(b => {
                    b.style.background = '#1a1a1a';
                    b.style.borderColor = '#3a3a3a';
                    b.style.color = '#e5e5e5';
                });
                btn.style.background = '#0078d4';
                btn.style.borderColor = '#0078d4';
                btn.style.color = 'white';
                this.currentFont.align = name.replace('align-', '');
            } else {
                // Toggle button
                this.currentFont[name] = !this.currentFont[name];
                btn.style.background = this.currentFont[name] ? '#0078d4' : '#1a1a1a';
                btn.style.borderColor = this.currentFont[name] ? '#0078d4' : '#3a3a3a';
                btn.style.color = this.currentFont[name] ? 'white' : '#e5e5e5';
            }
            this.onFontChange({ ...this.currentFont });
        });
        
        return btn;
    }
    
    getCurrentFont() {
        return { ...this.currentFont };
    }
    
    setFont(font) {
        this.currentFont = { ...this.currentFont, ...font };
        this.render();
    }
}

