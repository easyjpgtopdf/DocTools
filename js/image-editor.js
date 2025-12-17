/**
 * Image Editor Module
 * Handles image editing (sharp, clear, crop, color adjustment) for background-remover page
 */

class ImageEditor {
  constructor() {
    this.resultImage = null;
    this.originalResultURL = null;
    this.currentEditCanvas = null;
    this.editHistory = [];
    this.editHistoryIndex = -1;
    this.maxHistorySteps = 4;
    this.isOpen = false;
    this.eventsBound = false;
    
    // Store applied filters/effects
    this.currentEffects = {
      sharpness: 0,
      brightness: 0,
      contrast: 0,
      saturation: 0,
      crop: null
    };
  }

  init(resultImageElement, originalURL = null) {
    this.resultImage = resultImageElement;
    
    if (originalURL) {
      this.originalResultURL = originalURL;
      console.log('✅ ImageEditor: Original URL set:', this.originalResultURL.substring(0, 50) + '...');
    } else if (this.resultImage && this.resultImage.src) {
      this.originalResultURL = this.resultImage.src;
    }
    
    // Bind events only once
    if (!this.eventsBound) {
      this.bindEvents();
      this.eventsBound = true;
    }
    this.resetHistory();
    
    console.log('✅ ImageEditor initialized');
  }

  toggle() {
    const panel = document.getElementById('imageEditorPanel');
    if (!panel) {
      console.error('❌ Image editor panel not found!');
      return;
    }

    this.isOpen = !this.isOpen;
    console.log('🔄 Toggling image editor panel:', this.isOpen ? 'OPEN' : 'CLOSE');
    
    if (this.isOpen) {
      panel.style.display = 'block';
      setTimeout(() => {
        panel.style.opacity = '1';
        panel.style.transform = 'translateX(0)';
      }, 10);
    } else {
      panel.style.opacity = '0';
      panel.style.transform = 'translateX(100%)';
      setTimeout(() => {
        panel.style.display = 'none';
      }, 300);
    }
  }

  bindEvents() {
    // Bind sliders
    const sharpnessSlider = document.getElementById('editSharpness');
    const brightnessSlider = document.getElementById('editBrightness');
    const contrastSlider = document.getElementById('editContrast');
    const saturationSlider = document.getElementById('editSaturation');
    
    if (sharpnessSlider) {
      sharpnessSlider.addEventListener('input', (e) => {
        this.currentEffects.sharpness = parseFloat(e.target.value);
        this.updateSliderValues();
        this.applyEffects();
      });
    }
    
    if (brightnessSlider) {
      brightnessSlider.addEventListener('input', (e) => {
        this.currentEffects.brightness = parseFloat(e.target.value);
        this.updateSliderValues();
        this.applyEffects();
      });
    }
    
    if (contrastSlider) {
      contrastSlider.addEventListener('input', (e) => {
        this.currentEffects.contrast = parseFloat(e.target.value);
        this.updateSliderValues();
        this.applyEffects();
      });
    }
    
    if (saturationSlider) {
      saturationSlider.addEventListener('input', (e) => {
        this.currentEffects.saturation = parseFloat(e.target.value);
        this.updateSliderValues();
        this.applyEffects();
      });
    }

    // Auto-enhance button (AI-powered, free)
    const autoEnhanceBtn = document.getElementById('editAutoEnhance');
    if (autoEnhanceBtn) {
      autoEnhanceBtn.addEventListener('click', () => {
        this.applyAutoEnhance();
      });
    }

    // Reset button
    const resetBtn = document.getElementById('editReset');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.resetEffects();
      });
    }

    // Close button
    const closeBtn = document.getElementById('closeImageEditor');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        this.toggle();
      });
    }
  }

  async applyEffects() {
    if (!this.resultImage || !this.originalResultURL) {
      console.error('❌ No image available for editing');
      return;
    }

    try {
      // Load original image
      const img = new Image();
      img.crossOrigin = 'anonymous';
      await this.loadImage(img, this.originalResultURL);

      // Create canvas
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');

      // Draw original image
      ctx.drawImage(img, 0, 0);

      // Apply filters using CSS filters (for real-time preview)
      let filterString = '';
      
      if (this.currentEffects.brightness !== 0) {
        filterString += `brightness(${1 + this.currentEffects.brightness / 100}) `;
      }
      
      if (this.currentEffects.contrast !== 0) {
        filterString += `contrast(${1 + this.currentEffects.contrast / 100}) `;
      }
      
      if (this.currentEffects.saturation !== 0) {
        filterString += `saturate(${1 + this.currentEffects.saturation / 100}) `;
      }

      // Apply CSS filter for immediate preview
      if (filterString) {
        this.resultImage.style.filter = filterString.trim();
      } else {
        this.resultImage.style.filter = 'none';
      }

      // Apply sharpness using canvas (more complex)
      if (this.currentEffects.sharpness !== 0) {
        this.applySharpness(ctx, canvas, this.currentEffects.sharpness);
        const dataURL = canvas.toDataURL('image/png');
        this.resultImage.src = dataURL;
        // Reapply CSS filters after setting src
        if (filterString) {
          setTimeout(() => {
            this.resultImage.style.filter = filterString.trim();
          }, 10);
        }
      } else if (!filterString) {
        // No effects, restore original
        this.resultImage.src = this.originalResultURL;
        this.resultImage.style.filter = 'none';
      }

      // Update download state
      if (window.freePreviewApp && window.freePreviewApp.state) {
        const currentSrc = this.resultImage.src;
        window.freePreviewApp.state.resultURL = currentSrc;
      }

      console.log('✅ Effects applied:', this.currentEffects);
    } catch (err) {
      console.error('❌ Failed to apply effects:', err);
    }
  }

  applySharpness(ctx, canvas, amount) {
    // Simple sharpening using convolution
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    const width = canvas.width;
    const height = canvas.height;

    // Sharpening kernel
    const kernel = [
      0, -amount/100, 0,
      -amount/100, 1 + 4 * amount/100, -amount/100,
      0, -amount/100, 0
    ];

    const newData = new Uint8ClampedArray(data);
    
    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        for (let c = 0; c < 3; c++) {
          let sum = 0;
          for (let ky = -1; ky <= 1; ky++) {
            for (let kx = -1; kx <= 1; kx++) {
              const idx = ((y + ky) * width + (x + kx)) * 4 + c;
              const kIdx = (ky + 1) * 3 + (kx + 1);
              sum += data[idx] * kernel[kIdx];
            }
          }
          newData[(y * width + x) * 4 + c] = Math.max(0, Math.min(255, sum));
        }
      }
    }

    imageData.data.set(newData);
    ctx.putImageData(imageData, 0, 0);
  }

  async applyAutoEnhance() {
    if (!this.resultImage || !this.originalResultURL) {
      console.error('❌ No image available for auto-enhance');
      return;
    }

    console.log('🤖 Applying AI auto-enhance (free)...');
    
    // Auto-enhance using free AI-like enhancements
    // Apply optimal settings automatically
    this.currentEffects.brightness = 5;
    this.currentEffects.contrast = 10;
    this.currentEffects.saturation = 5;
    this.currentEffects.sharpness = 15;

    // Update sliders
    const sharpnessSlider = document.getElementById('editSharpness');
    const brightnessSlider = document.getElementById('editBrightness');
    const contrastSlider = document.getElementById('editContrast');
    const saturationSlider = document.getElementById('editSaturation');
    
    if (sharpnessSlider) sharpnessSlider.value = this.currentEffects.sharpness;
    if (brightnessSlider) brightnessSlider.value = this.currentEffects.brightness;
    if (contrastSlider) contrastSlider.value = this.currentEffects.contrast;
    if (saturationSlider) saturationSlider.value = this.currentEffects.saturation;

    await this.applyEffects();
    this.saveToHistory();
    
    console.log('✅ Auto-enhance applied');
  }

  resetEffects() {
    this.currentEffects = {
      sharpness: 0,
      brightness: 0,
      contrast: 0,
      saturation: 0,
      crop: null
    };

    // Reset sliders
    const sharpnessSlider = document.getElementById('editSharpness');
    const brightnessSlider = document.getElementById('editBrightness');
    const contrastSlider = document.getElementById('editContrast');
    const saturationSlider = document.getElementById('editSaturation');
    
    if (sharpnessSlider) sharpnessSlider.value = 0;
    if (brightnessSlider) brightnessSlider.value = 0;
    if (contrastSlider) contrastSlider.value = 0;
    if (saturationSlider) saturationSlider.value = 0;

    if (this.resultImage && this.originalResultURL) {
      this.resultImage.src = this.originalResultURL;
      this.resultImage.style.filter = 'none';
    }

    // Update download state
    if (window.freePreviewApp && window.freePreviewApp.state) {
      window.freePreviewApp.state.resultURL = this.originalResultURL;
    }

    console.log('✅ Effects reset');
  }

  saveToHistory() {
    if (!this.resultImage || !this.resultImage.src) return;
    if (!window.freePreviewApp || !window.freePreviewApp.state) return;

    const app = window.freePreviewApp;
    const currentSrc = this.resultImage.src;

    // Update current history entry with edits
    if (app.state.history.length > 0 && app.state.historyIndex >= 0) {
      app.state.history[app.state.historyIndex].edits = {
        imageSrc: currentSrc,
        effects: { ...this.currentEffects },
        filter: this.resultImage.style.filter || 'none'
      };
      app.state.history[app.state.historyIndex].result = currentSrc;
      
      // Update result image
      const resultImg = document.getElementById('resultImage');
      if (resultImg) {
        resultImg.src = currentSrc;
        resultImg.style.filter = this.resultImage.style.filter || 'none';
      }
      
      app.state.resultURL = currentSrc;
      app.updateUndoRedoButtons();
    } else {
      // Create new history entry
      if (app.state.originalURL && currentSrc) {
        // Remove future history if not at the end
        if (app.state.historyIndex < app.state.history.length - 1) {
          app.state.history = app.state.history.slice(0, app.state.historyIndex + 1);
        }
        
        app.state.history.push({
          original: app.state.originalURL,
          result: currentSrc,
          edits: {
            imageSrc: currentSrc,
            effects: { ...this.currentEffects },
            filter: this.resultImage.style.filter || 'none'
          },
          background: null
        });
        
        // Limit history to 4 stages
        const maxHistorySteps = 4;
        if (app.state.history.length > maxHistorySteps) {
          app.state.history.shift();
        } else {
          app.state.historyIndex = app.state.history.length - 1;
        }
        
        app.updateUndoRedoButtons();
      }
    }
  }

  updateUndoRedoButtons() {
    // This will be handled by free-preview.js's updateUndoRedoButtons
    // We just need to ensure history is synced
    if (window.freePreviewApp) {
      window.freePreviewApp.updateUndoRedoButtons();
    }
  }

  resetHistory() {
    // History is managed by free-preview.js
    // Just reset local effects
    this.currentEffects = {
      sharpness: 0,
      brightness: 0,
      contrast: 0,
      saturation: 0,
      crop: null
    };
  }

  // Restore from history entry
  restoreFromHistory(historyEntry) {
    if (!historyEntry || !historyEntry.edits) return;
    
    const edits = historyEntry.edits;
    this.currentEffects = { ...edits.effects };
    
    // Update sliders
    const sharpnessSlider = document.getElementById('editSharpness');
    const brightnessSlider = document.getElementById('editBrightness');
    const contrastSlider = document.getElementById('editContrast');
    const saturationSlider = document.getElementById('editSaturation');
    
    if (sharpnessSlider) sharpnessSlider.value = this.currentEffects.sharpness;
    if (brightnessSlider) brightnessSlider.value = this.currentEffects.brightness;
    if (contrastSlider) contrastSlider.value = this.currentEffects.contrast;
    if (saturationSlider) saturationSlider.value = this.currentEffects.saturation;
    
    // Update value displays
    this.updateSliderValues();
    
    // Restore image and filter
    if (this.resultImage && edits.imageSrc) {
      this.resultImage.src = edits.imageSrc;
      this.resultImage.style.filter = edits.filter || 'none';
    }
  }

  updateSliderValues() {
    const sharpnessValue = document.getElementById('sharpnessValue');
    const brightnessValue = document.getElementById('brightnessValue');
    const contrastValue = document.getElementById('contrastValue');
    const saturationValue = document.getElementById('saturationValue');
    
    if (sharpnessValue) sharpnessValue.textContent = this.currentEffects.sharpness;
    if (brightnessValue) brightnessValue.textContent = this.currentEffects.brightness;
    if (contrastValue) contrastValue.textContent = this.currentEffects.contrast;
    if (saturationValue) saturationValue.textContent = this.currentEffects.saturation;
  }

  loadImage(img, src) {
    return new Promise((resolve, reject) => {
      img.onload = () => resolve();
      img.onerror = (err) => {
        console.error('❌ Image load failed:', src.substring(0, 100), err);
        reject(new Error('Failed to load image: ' + src.substring(0, 50)));
      };
      if (!src.startsWith('data:')) {
        img.crossOrigin = 'anonymous';
      }
      img.src = src;
    });
  }

  // Get current edited image URL (for background application)
  getCurrentImageURL() {
    if (this.resultImage && this.resultImage.src) {
      return this.resultImage.src;
    }
    return this.originalResultURL;
  }
}

// Export globally
(function() {
  if (typeof window !== 'undefined') {
    window.ImageEditor = ImageEditor;
    console.log('✅ ImageEditor class registered globally');
  }
})();

