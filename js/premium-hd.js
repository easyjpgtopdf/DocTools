/**
 * Premium HD Flow (isolated)
 * Requirements:
 * - Upload via JSON (base64 dataURL)
 * - Models: BiRefNet + MaxMatting + feather/halo/color cleanup (handled backend)
 * - Sizes: 1920–5000px (≤25MP)
 * - Auth + credits required (token/userId supplied by host page)
 * - Canvas allowed ONLY here (for dataURL conversion/resizing if needed)
 */
(function () {
  const DEFAULT_SELECTORS = {
    fileInput: '#multipleImageUpload', // background-workspace.html uses multipleImageUpload
    uploadButton: '#newUploadBtn', // background-workspace.html uses newUploadBtn
    previewImage: '#previewOriginal', // background-workspace.html uses previewOriginal
    resultImage: '#previewResult', // background-workspace.html uses previewResult
    status: '#statusMessage', // Matches
    downloadButton: '#downloadPng', // background-workspace.html uses downloadPng
    sizeSelect: '#premiumSizeSelect', // background-workspace.html uses premiumSizeSelect (in modal)
    processButton: '#processBtn', // background-workspace.html has processBtn
    errorBox: '#statusMessage', // Use statusMessage for errors too
    downloadModal: '#downloadModal', // Download modal
    confirmDownload: '#confirmDownload', // Confirm download button
    cancelDownload: '#cancelDownload', // Cancel download button
    freeDownloadOption: '#freeDownloadOption', // Free download option
    premiumDownloadOption: '#premiumDownloadOption', // Premium download option
    premiumSizeSelection: '#premiumSizeSelection', // Premium size selection container
    premiumCreditInfo: '#premiumCreditInfo', // Credit info display
    premiumCreditText: '#premiumCreditText', // Credit text
  };

  class PremiumHDApp {
    constructor(options = {}) {
      this.endpoint = options.endpoint || '/api/tools/bg-remove-premium';
      this.apiBaseUrl = options.apiBaseUrl || window.location.origin;
      this.selectors = { ...DEFAULT_SELECTORS, ...(options.selectors || {}) };
      this.getAuthToken = options.getAuthToken || (async () => null);
      this.getUserId = options.getUserId || (async () => null);
      this.state = {
        file: null,
        previewURL: null,
        resultURL: null,
        isProcessing: false,
        targetSize: 'original',
        selectedQuality: null,
        selectedSize: 'original',
        userId: null,
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
        sizeSelect: get(this.selectors.sizeSelect),
        errorBox: get(this.selectors.errorBox),
        downloadModal: get(this.selectors.downloadModal),
        confirmDownload: get(this.selectors.confirmDownload),
        cancelDownload: get(this.selectors.cancelDownload),
        freeDownloadOption: get(this.selectors.freeDownloadOption),
        premiumDownloadOption: get(this.selectors.premiumDownloadOption),
        premiumSizeSelection: get(this.selectors.premiumSizeSelection),
        premiumCreditInfo: get(this.selectors.premiumCreditInfo),
        premiumCreditText: get(this.selectors.premiumCreditText),
      };
    }

    bindEvents() {
      if (this.el.fileInput) {
        this.el.fileInput.addEventListener('change', (e) => {
          const file = e.target.files?.[0];
          if (file) {
            console.log('File selected:', file.name, file.type, file.size);
            this.handleFile(file);
          } else {
            console.warn('No file selected');
          }
        });
      } else {
        console.error('File input not found:', this.selectors.fileInput);
      }

      if (this.el.uploadButton && this.el.fileInput) {
        this.el.uploadButton.addEventListener('click', (e) => {
          e.preventDefault();
          console.log('Upload button clicked');
          this.el.fileInput.click();
        });
      } else {
        if (!this.el.uploadButton) {
          console.error('Upload button not found:', this.selectors.uploadButton);
        }
        if (!this.el.fileInput) {
          console.error('File input not found for upload button');
        }
      }

      if (this.el.sizeSelect) {
        this.el.sizeSelect.addEventListener('change', (e) => {
          this.state.targetSize = e.target.value || 'original';
        });
      }

      // Wire up process button if it exists
      const processBtn = document.getElementById('processBtn');
      if (processBtn) {
        processBtn.addEventListener('click', () => {
          this.process();
        });
      }

      // Download button - show modal instead of direct download
      if (this.el.downloadButton) {
        this.el.downloadButton.addEventListener('click', () => {
          if (this.state.resultURL) {
            this.showDownloadModal();
          }
        });
      }
      
      // Download modal handlers
      if (this.el.cancelDownload) {
        this.el.cancelDownload.addEventListener('click', () => {
          this.closeDownloadModal();
        });
      }
      
      // Close modal on outside click
      if (this.el.downloadModal) {
        this.el.downloadModal.addEventListener('click', (e) => {
          if (e.target === this.el.downloadModal) {
            this.closeDownloadModal();
          }
        });
      }
      
      // Free download option
      if (this.el.freeDownloadOption) {
        this.el.freeDownloadOption.addEventListener('click', () => {
          this.selectDownloadOption('free');
        });
      }
      
      // Premium download option
      if (this.el.premiumDownloadOption) {
        this.el.premiumDownloadOption.addEventListener('click', () => {
          this.selectDownloadOption('premium');
        });
      }
      
      // Size selection change
      if (this.el.sizeSelect) {
        this.el.sizeSelect.addEventListener('change', (e) => {
          this.updateCreditInfo(e.target.value);
        });
      }
      
      // Confirm download
      if (this.el.confirmDownload) {
        this.el.confirmDownload.addEventListener('click', () => {
          this.handleDownload();
        });
      }
    }

    resetUI() {
      if (this.el.previewImage) this.el.previewImage.style.display = 'none';
      if (this.el.resultImage) this.el.resultImage.style.display = 'none';
      if (this.el.downloadButton) this.el.downloadButton.disabled = true;
      this.setStatus('Upload an image to start Premium HD processing.');
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
        this.el.previewImage.hidden = false;
        this.el.previewImage.style.display = 'block';
        
        // Remove empty class from preview-stage to show image
        const previewStage = document.getElementById('previewStage');
        if (previewStage) {
          previewStage.classList.remove('empty');
        }
        
        // Hide placeholder
        const placeholder = document.getElementById('previewPlaceholder');
        if (placeholder) {
          placeholder.classList.add('hidden');
        }
      }
    }
    
    showProcessingOverlay() {
      const overlay = document.getElementById('previewOverlay');
      if (overlay) {
        overlay.classList.add('processing');
        overlay.style.display = 'flex';
      }
    }
    
    hideProcessingOverlay() {
      const overlay = document.getElementById('previewOverlay');
      if (overlay) {
        overlay.classList.remove('processing');
        overlay.style.display = 'none';
        overlay.style.opacity = '0';
      }
      const previewStage = document.getElementById('previewStage');
      if (previewStage) {
        previewStage.classList.remove('empty');
        previewStage.classList.add('revealed');
      }
    }

    async handleFile(file) {
      if (!(file instanceof File) && !(file instanceof Blob)) {
        this.showError('Please select a valid image file.');
        return;
      }
      this.state.file = file;
      this.showError('');
      this.setStatus('Image uploaded! Processing with AI...');
      this.showPreview(file);
      
      // Auto-start processing after preview (for better UX)
      // Small delay to ensure preview is visible first
      setTimeout(() => {
        this.process();
      }, 500);
    }

    async fileToDataURL(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    async process(file = null, targetSize = null) {
      if (this.state.isProcessing) {
        this.setStatus('Processing already in progress...');
        return;
      }
      
      // Use provided file or state file
      const processFile = file || this.state.file;
      if (!processFile) {
        this.showError('Please upload a file first.');
        return;
      }
      
      // Update target size if provided
      if (targetSize) {
        this.state.targetSize = targetSize;
      }

      this.state.isProcessing = true;
      this.setStatus('AI is processing your image...');
      this.showError('');
      
      // Show processing overlay
      this.showProcessingOverlay();

      try {
        const dataURL = await this.fileToDataURL(processFile);
        const token = await this.getAuthToken();
        const userId = await this.getUserId();
        
        // Store userId for credit checks
        if (userId) {
          this.state.userId = userId;
        }

        if (!token || !userId) {
          throw new Error('Please sign in to use Premium HD.');
        }

        const body = {
          imageData: dataURL,
          userId,
          targetSize: this.state.targetSize || 'original',
          whiteBackground: true,  // Enterprise requirement: white background JPG
          outputFormat: 'jpg',     // Enterprise requirement: JPG output
          quality: 100,            // Enterprise requirement: quality 100
        };

        const response = await fetch(`${this.apiBaseUrl}${this.endpoint}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(body),
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || `Server error ${response.status}`);
        }

        const result = await response.json();
        console.log('API Response:', { success: result.success, hasResultImage: !!result.resultImage, result });
        
        if (result.success && result.resultImage) {
          this.state.resultURL = result.resultImage;
          
          // Hide original preview image
          if (this.el.previewImage) {
            this.el.previewImage.style.display = 'none';
            this.el.previewImage.hidden = true;
          }
          
          // Show result image
          if (this.el.resultImage) {
            this.el.resultImage.src = result.resultImage;
            this.el.resultImage.hidden = false;
            this.el.resultImage.style.display = 'block';
            this.el.resultImage.style.opacity = '1';
            
            // Ensure preview-stage shows result
            const previewStage = document.getElementById('previewStage');
            if (previewStage) {
              previewStage.classList.remove('empty');
              previewStage.classList.add('revealed');
            }
            
            // Hide placeholder
            const placeholder = document.getElementById('previewPlaceholder');
            if (placeholder) {
              placeholder.classList.add('hidden');
              placeholder.style.display = 'none';
            }
          }
          
          if (this.el.downloadButton) this.el.downloadButton.disabled = false;
          this.setStatus('Background removed successfully!');
          
          // Hide processing overlay and show result
          this.hideProcessingOverlay();
          
          console.log('✅ Result image displayed successfully');
        } else {
          console.error('❌ Processing failed:', result);
          throw new Error(result.error || result.message || 'Processing failed');
        }
      } catch (err) {
        this.showError(err.message || 'Processing failed. Please try again.');
        this.setStatus('Processing failed.');
        this.hideProcessingOverlay();
      } finally {
        this.state.isProcessing = false;
      }
    }
    
    // Download modal functions
    showDownloadModal() {
      if (!this.el.downloadModal || !this.state.resultURL) return;
      
      this.el.downloadModal.classList.add('active');
      this.state.selectedQuality = null;
      this.state.selectedSize = 'original';
      
      // Reset UI
      if (this.el.freeDownloadOption) {
        this.el.freeDownloadOption.classList.remove('selected');
      }
      if (this.el.premiumDownloadOption) {
        this.el.premiumDownloadOption.classList.remove('selected');
      }
      if (this.el.confirmDownload) {
        this.el.confirmDownload.disabled = true;
      }
      if (this.el.premiumSizeSelection) {
        this.el.premiumSizeSelection.classList.remove('active');
      }
      
      // Update credit info for default size
      if (this.el.sizeSelect) {
        this.updateCreditInfo(this.el.sizeSelect.value);
      }
    }
    
    closeDownloadModal() {
      if (this.el.downloadModal) {
        this.el.downloadModal.classList.remove('active');
      }
    }
    
    selectDownloadOption(quality) {
      this.state.selectedQuality = quality;
      
      if (this.el.freeDownloadOption) {
        this.el.freeDownloadOption.classList.toggle('selected', quality === 'free');
      }
      if (this.el.premiumDownloadOption) {
        this.el.premiumDownloadOption.classList.toggle('selected', quality === 'premium');
      }
      
      if (this.el.premiumSizeSelection) {
        if (quality === 'premium') {
          this.el.premiumSizeSelection.classList.add('active');
          if (this.el.sizeSelect) {
            this.updateCreditInfo(this.el.sizeSelect.value);
          }
        } else {
          this.el.premiumSizeSelection.classList.remove('active');
        }
      }
      
      if (this.el.confirmDownload) {
        this.el.confirmDownload.disabled = false;
      }
    }
    
    async updateCreditInfo(size) {
      if (!this.el.premiumCreditInfo || !this.el.premiumCreditText) return;
      
      // Credit costs based on size
      const creditCosts = {
        'original': 2,
        '1920x1080': 2,
        '2048x2048': 4,
        '3000x2000': 4,
        '3000x3000': 6,
        '4000x3000': 9,
        '4000x4000': 10,
        '5000x3000': 12,
        '5000x5000': 15,
      };
      
      const credits = creditCosts[size] || creditCosts['original'];
      this.state.selectedSize = size;
      
      if (this.state.userId) {
        try {
          // Get user credits
          const token = await this.getAuthToken();
          const response = await fetch(`/api/user/credits?userId=${this.state.userId}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          
          if (response.ok) {
            const data = await response.json();
            const available = data.credits || 0;
            const hasEnough = available >= credits;
            
            this.el.premiumCreditInfo.style.display = 'block';
            this.el.premiumCreditText.textContent = hasEnough
              ? `You have ${available} credits. This download will cost ${credits} credits.`
              : `Insufficient credits. You have ${available} credits, but need ${credits} credits.`;
            
            if (this.el.confirmDownload) {
              this.el.confirmDownload.disabled = !hasEnough || !this.state.selectedQuality;
            }
          } else {
            this.el.premiumCreditInfo.style.display = 'block';
            this.el.premiumCreditText.textContent = `This download will cost ${credits} credits.`;
          }
        } catch (err) {
          console.error('Error fetching credits:', err);
          this.el.premiumCreditInfo.style.display = 'block';
          this.el.premiumCreditText.textContent = `This download will cost ${credits} credits.`;
        }
      } else {
        this.el.premiumCreditInfo.style.display = 'block';
        this.el.premiumCreditText.textContent = `This download will cost ${credits} credits.`;
      }
    }
    
    async handleDownload() {
      if (!this.state.resultURL || !this.state.selectedQuality) return;
      
      try {
        if (this.state.selectedQuality === 'free') {
          // Free download - 512px preview
          this.downloadImage(this.state.resultURL, 'background-removed-free.png');
          this.closeDownloadModal();
        } else {
          // Premium download - process at selected size
          const size = this.state.selectedSize || 'original';
          
          // Credit costs
          const creditCosts = {
            'original': 2,
            '1920x1080': 2,
            '2048x2048': 4,
            '3000x2000': 4,
            '3000x3000': 6,
            '4000x3000': 9,
            '4000x4000': 10,
            '5000x3000': 12,
            '5000x5000': 15,
          };
          
          const credits = creditCosts[size] || creditCosts['original'];
          
          // Process image at selected size
          this.setStatus(`Processing ${size} image...`);
          this.closeDownloadModal();
          
          // Re-process with selected size
          if (this.state.file) {
            await this.process(this.state.file, size);
          } else {
            throw new Error('Original file not available');
          }
        }
      } catch (err) {
        this.showError(err.message || 'Download failed');
      }
    }
    
    downloadImage(url, filename) {
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
  }

  // Expose class for manual init
  window.PremiumHDApp = PremiumHDApp;
  
  // Auto-initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
  } else {
    initializeApp();
  }
  
  async function initializeApp() {
    try {
      // Get auth token and user ID
      async function getAuthToken() {
        try {
          if (window.auth && window.auth.currentUser) {
            return await window.auth.currentUser.getIdToken();
          }
          return localStorage.getItem('authToken') || sessionStorage.getItem('authToken') || null;
        } catch (e) {
          return null;
        }
      }
      
      async function getUserId() {
        try {
          if (window.auth && window.auth.currentUser) {
            return window.auth.currentUser.uid;
          }
          return localStorage.getItem('userId') || sessionStorage.getItem('userId') || null;
        } catch (e) {
          return null;
        }
      }
      
      // Initialize PremiumHDApp
      if (window.PremiumHDApp) {
        console.log('Initializing PremiumHDApp...');
        window.premiumHDApp = new window.PremiumHDApp({
          getAuthToken,
          getUserId,
        });
        console.log('PremiumHDApp initialized:', window.premiumHDApp);
        console.log('File input element:', window.premiumHDApp.el?.fileInput);
        console.log('Upload button element:', window.premiumHDApp.el?.uploadButton);
      } else {
        console.error('PremiumHDApp class not found!');
      }
    } catch (error) {
      console.error('Failed to initialize PremiumHDApp:', error);
    }
  }
})();

