/**
 * Free Preview (remove.bg style) – isolated flow
 * Requirements:
 * - File/Blob ONLY
 * - multipart/form-data upload
 * - Endpoint: /api/tools/bg-remove-free
 * - No sessionStorage / canvas / credits / premium helpers
 */
(function () {
  const DEFAULT_SELECTORS = {
    fileInput: '#imageInput',
    uploadButton: '#browseBtn',
    resultImage: '#resultImage',
    status: '#statusMessage',
    downloadButton: '#downloadBtn',
    errorBox: '#errorBox',
  };

  class FreePreviewApp {
    constructor(options = {}) {
      this.endpoint = options.endpoint || '/api/tools/bg-remove-free';
      this.apiBaseUrl = options.apiBaseUrl || window.location.origin;
      this.selectors = { ...DEFAULT_SELECTORS, ...(options.selectors || {}) };
      this.state = {
        file: null,
        previewURL: null,
        resultURL: null,
        originalURL: null,
        isProcessing: false,
        history: [],
        historyIndex: -1,
        previewHistory: [], // Array to store processed images (max 6)
      };
      this.bindElements();
      this.bindEvents();
      this.resetUI();
    }

    bindElements() {
      const get = (sel) => document.querySelector(sel);
      this.el = {
        fileInput: get(this.selectors.fileInput),
        uploadButton: get(this.selectors.uploadButton),
        resultImage: get(this.selectors.resultImage),
        status: get(this.selectors.status),
        downloadButton: get(this.selectors.downloadButton),
        errorBox: get(this.selectors.errorBox),
      };
    }

    bindEvents() {
      if (this.el.fileInput) {
        this.el.fileInput.addEventListener('change', (e) => {
          const file = e.target.files?.[0];
          if (file) this.handleFile(file);
        });
      }

      if (this.el.uploadButton && this.el.fileInput) {
        this.el.uploadButton.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          console.log('🔘 Upload button clicked, triggering file input');
          if (this.el.fileInput) {
            this.el.fileInput.click();
          }
        });
      }

      // Undo/Redo buttons
      const undoBtn = document.getElementById('undoBtn');
      if (undoBtn) {
        undoBtn.addEventListener('click', () => {
          this.undo();
        });
      }
      
      const redoBtn = document.getElementById('redoBtn');
      if (redoBtn) {
        redoBtn.addEventListener('click', () => {
          this.redo();
        });
      }

      // Wire drag-drop on dropzone
      const dropzone = document.getElementById('dropzone');
      if (dropzone) {
        dropzone.addEventListener('dragover', (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.add('dragover');
        });
        
        dropzone.addEventListener('dragleave', (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.remove('dragover');
        });
        
        dropzone.addEventListener('drop', (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.remove('dragover');
          const file = e.dataTransfer.files?.[0];
          if (file) {
            this.handleFile(file);
          }
        });
        
        // Click on dropzone to trigger file input (but not if clicking button)
        dropzone.addEventListener('click', (e) => {
          if (e.target.closest('button') || e.target.closest('#browseBtn')) {
            return; // Button handles its own click
          }
          if (this.el.fileInput) {
            this.el.fileInput.click();
          }
        });
      }

      if (this.el.downloadButton) {
        this.el.downloadButton.addEventListener('click', () => {
          if (this.state.resultURL) {
            const a = document.createElement('a');
            a.href = this.state.resultURL;
            a.download = 'background-removed.png';
            document.body.appendChild(a);
            a.click();
            a.remove();
          }
        });
      }
    }

    resetUI() {
      if (this.el.resultImage) this.el.resultImage.style.display = 'none';
      if (this.el.downloadButton) this.el.downloadButton.disabled = true;
      this.setStatus('Upload an image to start free preview.');
      this.showError('');
    }

    resetToUpload() {
      // Hide result section and show upload section
      const uploadSection = document.getElementById('uploadSection');
      const resultSection = document.getElementById('resultSection');
      const imagePreview = document.getElementById('imagePreview');
      const uploadContent = document.getElementById('uploadContent');
      const toggle = document.getElementById('beforeAfterToggle');
      
      if (uploadSection) {
        uploadSection.style.display = 'block';
      }
      if (resultSection) {
        resultSection.style.display = 'none';
      }
      if (toggle) {
        toggle.style.display = 'none';
      }
      
      // Hide preview image and restore upload content
      if (imagePreview) {
        imagePreview.style.display = 'none';
      }
      if (uploadContent) {
        uploadContent.style.opacity = '1';
      }
      
      // Reset file input
      if (this.el.fileInput) {
        this.el.fileInput.value = '';
      }
      
      // Reset state (keep preview history until page refresh)
      this.state.file = null;
      this.state.previewURL = null;
      this.state.resultURL = null;
      this.state.originalURL = null;
      this.state.isProcessing = false;
      this.state.history = [];
      this.state.historyIndex = -1;
      // Note: previewHistory is kept for recovery
      
      // Reset UI
      this.resetUI();
      this.updateUndoRedoButtons();
    }

    initBeforeAfterToggle() {
      const toggleContainer = document.getElementById('beforeAfterToggle');
      const toggleSlider = document.getElementById('toggleSlider');
      const toggleText = document.getElementById('toggleText');
      const resultImg = document.getElementById('resultImage');
      const beforeImg = document.getElementById('beforeImage');
      
      if (!toggleContainer || !toggleSlider || !toggleText || !resultImg || !beforeImg) return;
      
      // Remove existing listeners by cloning
      const newToggle = toggleContainer.cloneNode(true);
      toggleContainer.parentNode.replaceChild(newToggle, toggleContainer);
      const newSlider = document.getElementById('toggleSlider');
      const newText = document.getElementById('toggleText');
      const newResultImg = document.getElementById('resultImage');
      const newBeforeImg = document.getElementById('beforeImage');
      
      let showingAfter = true;
      
      // Set initial state - show After
      newResultImg.style.opacity = '1';
      newResultImg.style.display = 'block';
      newBeforeImg.style.opacity = '0';
      newBeforeImg.style.display = 'none';
      newSlider.style.transform = 'translateX(0)';
      newText.textContent = 'After';
      
      // Click handler
      const toggleBtn = newToggle.querySelector('div[style*="cursor: pointer"]');
      if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
          showingAfter = !showingAfter;
          
          if (showingAfter) {
            // Show After (result)
            newSlider.style.transform = 'translateX(0)';
            newText.textContent = 'After';
            newBeforeImg.style.opacity = '0';
            setTimeout(() => {
              newBeforeImg.style.display = 'none';
              newResultImg.style.display = 'block';
            }, 150);
            setTimeout(() => {
              newResultImg.style.opacity = '1';
            }, 160);
          } else {
            // Show Before (original)
            newSlider.style.transform = 'translateX(-48px)';
            newText.textContent = 'Before';
            newResultImg.style.opacity = '0';
            setTimeout(() => {
              newResultImg.style.display = 'none';
              newBeforeImg.style.display = 'block';
            }, 150);
            setTimeout(() => {
              newBeforeImg.style.opacity = '1';
            }, 160);
          }
        });
      }
    }

    updateUndoRedoButtons() {
      const undoBtn = document.getElementById('undoBtn');
      const redoBtn = document.getElementById('redoBtn');
      
      if (undoBtn) {
        undoBtn.disabled = this.state.historyIndex <= 0;
      }
      if (redoBtn) {
        redoBtn.disabled = this.state.historyIndex >= this.state.history.length - 1;
      }
    }

    undo() {
      if (this.state.historyIndex > 0) {
        this.state.historyIndex--;
        this.applyHistoryState();
      }
    }

    redo() {
      if (this.state.historyIndex < this.state.history.length - 1) {
        this.state.historyIndex++;
        this.applyHistoryState();
      }
    }

    applyHistoryState() {
      if (this.state.historyIndex >= 0 && this.state.historyIndex < this.state.history.length) {
        const state = this.state.history[this.state.historyIndex];
        const resultImg = document.getElementById('resultImage');
        const beforeImg = document.getElementById('beforeImage');
        
        if (resultImg && state.result) {
          resultImg.src = state.result;
        }
        if (beforeImg && state.original) {
          beforeImg.src = state.original;
        }
        
        this.updateUndoRedoButtons();
      }
    }

    showError(message) {
      if (!this.el.errorBox) return;
      // Parse JSON error messages if needed
      let displayMessage = message || '';
      if (message) {
        try {
          const parsed = typeof message === 'string' ? JSON.parse(message) : message;
          if (parsed.error) {
            displayMessage = parsed.error;
            if (parsed.message) {
              displayMessage += ': ' + parsed.message;
            }
          }
        } catch (e) {
          // Not JSON, use as-is
        }
      }
      this.el.errorBox.textContent = displayMessage;
      this.el.errorBox.style.display = displayMessage ? 'block' : 'none';
      // Also log for debugging
      if (displayMessage) {
        console.error('❌ Free Preview Error:', displayMessage);
      }
    }

    setStatus(message) {
      if (this.el.status) {
        this.el.status.textContent = message;
        this.el.status.style.display = message ? 'block' : 'none';
      }
      console.log('📊 Free Preview Status:', message);
    }

    showPreview(file) {
      const url = URL.createObjectURL(file);
      this.state.previewURL = url;
      this.state.originalURL = url;
      
      // Show instant preview in upload bar
      const imagePreview = document.getElementById('imagePreview');
      const previewImg = document.getElementById('previewImg');
      const uploadContent = document.getElementById('uploadContent');
      
      if (imagePreview && previewImg) {
        previewImg.src = url;
        imagePreview.style.display = 'block';
        if (uploadContent) {
          uploadContent.style.opacity = '0.3';
        }
      }
      
      // Auto-start processing after a small delay to ensure UI is updated
      setTimeout(() => {
        this.process(file).finally(() => {
          // Revoke preview URL after processing/display to avoid leaks
          setTimeout(() => URL.revokeObjectURL(url), 5000);
        });
      }, 100);
    }

    async handleFile(file) {
      // Validate File/Blob
      if (!(file instanceof File) && !(file instanceof Blob)) {
        this.showError('Please select a valid image file.');
        return;
      }
      this.state.file = file;
      this.showError('');
      this.setStatus('Preview ready. Starting processing...');
      this.showPreview(file);
    }

    async process(file) {
      if (this.state.isProcessing) {
        this.setStatus('Processing already in progress...');
        return;
      }
      this.state.isProcessing = true;
      this.setStatus('Processing with Free Preview (512px)...');
      this.showError(''); // Clear previous errors

      try {
        // Validate file before creating FormData
        if (!file || (!(file instanceof File) && !(file instanceof Blob))) {
          throw new Error('Invalid file: File object is required');
        }

        console.log('📤 Creating FormData:', {
          fileName: file.name || 'blob',
          fileSize: file.size,
          fileType: file.type
        });

        const formData = new FormData();
        formData.append('image', file, file.name || 'image.jpg');
        formData.append('maxSize', '512');
        formData.append('imageType', 'human'); // default; backend may override

        // Verify FormData contents (for debugging)
        console.log('✅ FormData created with image file');
        console.log('🌐 Sending request to:', `${this.apiBaseUrl}${this.endpoint}`);
        console.log('📋 Request method: POST');
        console.log('📦 Content-Type: multipart/form-data (browser will set boundary)');

        const response = await fetch(`${this.apiBaseUrl}${this.endpoint}`, {
          method: 'POST',
          body: formData,
          // DO NOT set Content-Type header - browser will set it with boundary automatically
        });

        console.log('📥 Response received:', {
          status: response.status,
          statusText: response.statusText,
          contentType: response.headers.get('content-type')
        });

        if (!response.ok) {
          let errorText = await response.text();
          console.error('❌ API Error Response:', errorText);
          
          // Try to parse as JSON
          try {
            const errorJson = JSON.parse(errorText);
            throw new Error(JSON.stringify(errorJson));
          } catch (e) {
            throw new Error(errorText || `Server error ${response.status}`);
          }
        }

        const result = await response.json();
        console.log('✅ API Response:', result);

        if (result.success && result.resultImage) {
          this.state.resultURL = result.resultImage;
          
          // Add to history
          if (this.state.originalURL && result.resultImage) {
            this.state.history.push({
              original: this.state.originalURL,
              result: result.resultImage
            });
            this.state.historyIndex = this.state.history.length - 1;
            this.updateUndoRedoButtons();
          }
          
          // Hide upload section and show result section
          const uploadSection = document.getElementById('uploadSection');
          const resultSection = document.getElementById('resultSection');
          const resultImg = document.getElementById('resultImage');
          const beforeImg = document.getElementById('beforeImage');
          
          console.log('📸 Setting result image:', {
            resultURL: result.resultImage,
            resultImgExists: !!resultImg,
            resultSectionExists: !!resultSection
          });
          
          if (resultImg && resultSection) {
            // First, ensure result section is visible
            resultSection.style.display = 'block';
            
            // Set before image (original)
            if (beforeImg && this.state.originalURL) {
              beforeImg.src = this.state.originalURL;
            }
            
            // Set result image source and force visibility
            resultImg.src = result.resultImage;
            resultImg.style.display = 'block';
            resultImg.style.visibility = 'visible';
            resultImg.style.opacity = '1';
            resultImg.style.width = '100%';
            resultImg.style.height = '100%';
            resultImg.style.objectFit = 'contain';
            
            // Show toggle button
            const toggle = document.getElementById('beforeAfterToggle');
            if (toggle) {
              toggle.style.display = 'block';
            }
            
            // Initialize toggle after images load
            resultImg.onload = () => {
              console.log('✅ Result image loaded successfully');
              this.initBeforeAfterToggle();
            };
            resultImg.onerror = (e) => {
              console.error('❌ Result image failed to load:', e);
              console.error('Image src was:', result.resultImage);
              this.showError('Failed to load result image. Please try again.');
            };
          } else {
            console.error('❌ Missing elements:', {
              resultImg: !!resultImg,
              resultSection: !!resultSection
            });
          }
          
          if (uploadSection) {
            uploadSection.style.display = 'none';
          }
          
          // Enable download button
          if (this.el.downloadButton) {
            this.el.downloadButton.disabled = false;
            this.el.downloadButton.style.opacity = '1';
          }
          
          this.setStatus('✅ Background removed successfully!');
          this.showError(''); // Clear any errors
          console.log('✅ Processing complete, result URL:', result.resultImage);
        } else {
          throw new Error(result.error || result.message || 'Processing failed');
        }
      } catch (err) {
        console.error('❌ Processing error:', err);
        const errorMsg = err.message || 'Processing failed. Please try again.';
        this.showError(errorMsg);
        this.setStatus('❌ Processing failed.');
        
        // Reset state on error
        if (this.el.downloadButton) this.el.downloadButton.disabled = true;
      } finally {
        this.state.isProcessing = false;
      }
    }
  }

  // Auto-init if elements exist
  document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.querySelector(DEFAULT_SELECTORS.fileInput);
    if (fileInput) {
      window.freePreviewApp = new FreePreviewApp();
    }
  });
})();

