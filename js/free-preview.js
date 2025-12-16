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
    fileInput: '#imageInput', // background-remover.html uses imageInput
    uploadButton: '#browseBtn', // background-remover.html uses browseBtn
    previewImage: '#previewImage',
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
        isProcessing: false,
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
        previewImage: get(this.selectors.previewImage),
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
        this.el.uploadButton.addEventListener('click', () => {
          this.el.fileInput.click();
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
      if (this.el.previewImage) this.el.previewImage.style.display = 'none';
      if (this.el.resultImage) this.el.resultImage.style.display = 'none';
      if (this.el.downloadButton) this.el.downloadButton.disabled = true;
      this.setStatus('Upload an image to start free preview.');
      this.showError('');
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
      if (this.el.previewImage) {
        this.el.previewImage.src = url;
        this.el.previewImage.style.display = 'block';
        this.el.previewImage.style.opacity = '1';
      }
      // Also set result image initially to show original
      if (this.el.resultImage) {
        this.el.resultImage.src = url;
        this.el.resultImage.style.display = 'block';
        this.el.resultImage.style.opacity = '1';
      }
      // Show preview container
      const previewContainer = document.getElementById('previewContainer');
      if (previewContainer) {
        previewContainer.style.display = 'block';
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
          if (this.el.resultImage) {
            this.el.resultImage.src = result.resultImage;
            this.el.resultImage.style.display = 'block';
            this.el.resultImage.style.opacity = '1';
          }
          
          // Show preview container if hidden
          const previewContainer = document.getElementById('previewContainer');
          if (previewContainer) {
            previewContainer.style.display = 'block';
          }
          
          // Enable download button
          if (this.el.downloadButton) {
            this.el.downloadButton.disabled = false;
            this.el.downloadButton.style.opacity = '1';
          }
          
          this.setStatus('✅ Free preview complete! Background removed successfully.');
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

