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
      this.el.errorBox.textContent = message || '';
      this.el.errorBox.style.display = message ? 'block' : 'none';
    }

    setStatus(message) {
      if (this.el.status) this.el.status.textContent = message;
    }

    showPreview(file) {
      const url = URL.createObjectURL(file);
      this.state.previewURL = url;
      if (this.el.previewImage) {
        this.el.previewImage.src = url;
        this.el.previewImage.style.display = 'block';
      }
      // Show preview container
      const previewContainer = document.getElementById('previewContainer');
      if (previewContainer) previewContainer.style.display = 'block';
      // Auto-start processing
      this.process(file).finally(() => {
        // Revoke preview URL after processing/display to avoid leaks
        setTimeout(() => URL.revokeObjectURL(url), 5000);
      });
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

      try {
        const formData = new FormData();
        formData.append('image', file);
        formData.append('maxSize', '512');
        formData.append('imageType', 'human'); // default; backend may override

        const response = await fetch(`${this.apiBaseUrl}${this.endpoint}`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || `Server error ${response.status}`);
        }

        const result = await response.json();
        if (result.success && result.resultImage) {
          this.state.resultURL = result.resultImage;
          if (this.el.resultImage) {
            this.el.resultImage.src = result.resultImage;
            this.el.resultImage.style.display = 'block';
          }
          if (this.el.downloadButton) this.el.downloadButton.disabled = false;
          this.setStatus('Free preview complete!');
        } else {
          throw new Error(result.error || 'Processing failed');
        }
      } catch (err) {
        this.showError(err.message || 'Processing failed. Please try again.');
        this.setStatus('Processing failed.');
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

