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
    sizeSelect: '#premiumSizeSelectBeforeUpload', // NEW: Size select BEFORE upload
    sizeSelectModal: '#premiumSizeSelect', // Old: Size select in modal (for backward compatibility)
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
      // Check credits on page load ONCE - don't check again on size selection
      this.pageAccessChecked = false;
      this.checkPageAccess();
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
        sizeSelectModal: get(this.selectors.sizeSelectModal),
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
        this.el.fileInput.addEventListener('change', async (e) => {
          const file = e.target.files?.[0];
          if (file) {
            console.log('File selected:', file.name, file.type, file.size);
            // Check credits BEFORE allowing file upload
            const hasCredits = await this.checkCreditsBeforeUpload();
            if (!hasCredits) {
              // Reset file input
              this.el.fileInput.value = '';
              return;
            }
            this.handleFile(file);
          } else {
            console.warn('No file selected');
          }
        });
      } else {
        console.error('File input not found:', this.selectors.fileInput);
      }

      if (this.el.uploadButton && this.el.fileInput) {
        this.el.uploadButton.addEventListener('click', async (e) => {
          e.preventDefault();
          console.log('Upload button clicked');
          // Check credits BEFORE allowing file selection
          const hasCredits = await this.checkCreditsBeforeUpload();
          if (!hasCredits) {
            return;
          }
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

      // Size selection BEFORE upload - NO credit check, NO redirect, just update state
      if (this.el.sizeSelect) {
        this.el.sizeSelect.addEventListener('change', (e) => {
          e.stopPropagation(); // Prevent any event bubbling that might trigger redirects
          const selectedSize = e.target.value || 'original';
          this.state.targetSize = selectedSize;
          console.log(`[Size Selection Before Upload] Selected size: ${selectedSize} - NO redirect, NO credit check`);
          // NO redirect, NO credit check, NO page access check - only update state
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
      
      // Size selection change in download modal (if exists) - NO redirect, just update credit info
      if (this.el.sizeSelectModal) {
        this.el.sizeSelectModal.addEventListener('change', (e) => {
          const selectedSize = e.target.value || 'original';
          this.state.selectedSize = selectedSize;
          this.updateCreditInfo(selectedSize);
          // NO redirect, NO page access check - just update UI
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

    // Check page access on load - redirect if insufficient credits (ONLY ONCE)
    async checkPageAccess() {
      // Prevent multiple calls
      if (this.pageAccessChecked) {
        console.log('[Page Access] Already checked, skipping...');
        return;
      }
      
      // Mark as checked immediately to prevent race conditions
      this.pageAccessChecked = true;
      
      // Wait a bit for auth to initialize
      await new Promise(resolve => setTimeout(resolve, 500));
      
      let retries = 3;
      while (retries > 0) {
        try {
          console.log(`[Page Access] Attempt ${4 - retries}/3 - Checking user access...`);
          
          const userId = await this.getUserId();
          console.log(`[Page Access] User ID: ${userId || 'null'}`);
          
          if (!userId) {
            // Wait a bit more and retry (auth might still be initializing)
            if (retries > 1) {
              console.log('[Page Access] No userId yet, waiting for auth...');
              await new Promise(resolve => setTimeout(resolve, 1000));
              retries--;
              continue;
            }
            // Final attempt failed - user not logged in
            console.log('[Page Access] User not logged in - redirecting to pricing');
            window.location.href = '/pricing.html';
            return;
          }

          const token = await this.getAuthToken();
          if (!token) {
            console.log('[Page Access] No auth token - waiting...');
            if (retries > 1) {
              await new Promise(resolve => setTimeout(resolve, 1000));
              retries--;
              continue;
            }
            console.log('[Page Access] No auth token - redirecting to pricing');
            window.location.href = '/pricing.html';
            return;
          }

          const MIN_CREDITS_REQUIRED = 4;
          console.log(`[Page Access] Checking credits for user ${userId}...`);

          // Check credits via API
          const response = await fetch(`/api/user/credits?userId=${userId}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          console.log(`[Page Access] Credit check response status: ${response.status}`);

          if (!response.ok) {
            // If can't check credits, try again or redirect
            if (retries > 1) {
              console.log('[Page Access] Credit check failed, retrying...');
              await new Promise(resolve => setTimeout(resolve, 1000));
              retries--;
              continue;
            }
            console.log('[Page Access] Credit check failed - redirecting to pricing');
            window.location.href = '/pricing.html';
            return;
          }

          const data = await response.json();
          const availableCredits = data.credits || 0;
          console.log(`[Page Access] Available credits: ${availableCredits}`);

          if (availableCredits < MIN_CREDITS_REQUIRED) {
            // Insufficient credits - redirect to pricing
            console.log(`[Page Access] Insufficient credits (${availableCredits} < ${MIN_CREDITS_REQUIRED}) - redirecting`);
            alert(`You need at least ${MIN_CREDITS_REQUIRED} credits to use Premium HD. You have ${availableCredits} credit(s). Redirecting to pricing page...`);
            window.location.href = '/pricing.html';
            return;
          }

          // Credits sufficient - allow access
          console.log(`✅ [Page Access] Access granted. User has ${availableCredits} credits.`);
          return; // Success - exit function
          
        } catch (error) {
          console.error(`[Page Access] Error (attempt ${4 - retries}/3):`, error);
          if (retries > 1) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            retries--;
            continue;
          }
          // Final attempt failed - redirect to pricing for safety
          console.error('[Page Access] All retries failed - redirecting to pricing');
          window.location.href = '/pricing.html';
          return;
        }
      }
    }

    // Show credit upgrade popup
    showCreditUpgradePopup(selectedSize, creditsRequired, availableCredits) {
      const message = `You need ${creditsRequired} credits for ${selectedSize} size, but you only have ${availableCredits} credit(s).\n\nWould you like to upgrade your credits?`;
      
      if (confirm(message)) {
        // User wants to upgrade - redirect to pricing
        window.location.href = '/pricing.html';
      } else {
        // User cancelled - just show message, don't redirect
        this.showError(`Insufficient credits. You need ${creditsRequired} credits for ${selectedSize} size.`);
        this.setStatus(`You have ${availableCredits} credit(s), but need ${creditsRequired} credits. Please choose a smaller size or upgrade credits.`);
      }
    }

    // Check credits BEFORE file upload (based on selected size) - NO redirect, show popup
    async checkCreditsBeforeUpload() {
      try {
        const userId = await this.getUserId();
        if (!userId) {
          this.showError('Please sign in to use Premium HD.');
          return false;
        }

        const token = await this.getAuthToken();
        
        // Get credits required for selected size
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
        
        const selectedSize = this.state.targetSize || 'original';
        const creditsRequired = creditCosts[selectedSize] || creditCosts['original'];

        console.log(`[Credit Check] Checking credits for size: ${selectedSize}, required: ${creditsRequired}`);

        // Check credits via API
        const response = await fetch(`/api/user/credits?userId=${userId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          this.showError('Unable to check credits. Please try again.');
          return false;
        }

        const data = await response.json();
        const availableCredits = data.credits || 0;

        console.log(`[Credit Check] Available: ${availableCredits}, Required: ${creditsRequired}`);

        if (availableCredits < creditsRequired) {
          // Show popup instead of redirecting
          this.showCreditUpgradePopup(selectedSize, creditsRequired, availableCredits);
          return false;
        }

        // Credits sufficient
        this.showError('');
        this.setStatus(`You have ${availableCredits} credits. Ready to process at ${selectedSize} size.`);
        return true;
      } catch (error) {
        console.error('Credit check error:', error);
        this.showError('Unable to check credits. Please try again.');
        return false;
      }
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
          let errorData = {};
          try {
            errorData = JSON.parse(text);
          } catch (e) {
            errorData = { error: text || `Server error: ${response.status}` };
          }
          
          // Handle 402 (Payment Required) - Insufficient credits
          if (response.status === 402) {
            const message = errorData.message || `Insufficient credits. You need at least ${errorData.minRequired || 4} credits. Please purchase credits.`;
            this.showError(message);
            this.setStatus(`Insufficient credits. You have ${errorData.creditsAvailable || 0} credit(s).`);
            return;
          }
          
          // Handle 401 (Unauthorized) - Authentication required
          if (response.status === 401) {
            this.showError(errorData.message || 'Please sign in to use Premium HD.');
            this.setStatus('Authentication required.');
            return;
          }
          
          throw new Error(errorData.error || errorData.message || `Server error: ${response.status}`);
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
            this.el.resultImage.removeAttribute('hidden');
            this.el.resultImage.style.display = 'block';
            this.el.resultImage.style.opacity = '1';
            this.el.resultImage.style.visibility = 'visible';
            // Force reflow to ensure display
            this.el.resultImage.offsetHeight;
            
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
      if (!this.state.resultURL) return;
      
      try {
        // Since image is already processed at selected size, just download it
        // No need to re-process
        const filename = `background-removed-${this.state.targetSize || 'original'}.jpg`;
        this.downloadImage(this.state.resultURL, filename);
        this.closeDownloadModal();
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
          // First check if auth is available and user is already logged in
          if (window.auth && window.auth.currentUser) {
            return await window.auth.currentUser.getIdToken();
          }
          
          // Check localStorage/sessionStorage
          const storedToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
          if (storedToken) {
            return storedToken;
          }
          
          // Wait for auth state change if auth is available
          if (window.auth) {
            return new Promise(async (resolve) => {
              const unsubscribe = window.auth.onAuthStateChanged(async (user) => {
                unsubscribe();
                if (user) {
                  try {
                    const token = await user.getIdToken();
                    resolve(token);
                  } catch (e) {
                    resolve(null);
                  }
                } else {
                  // Wait a bit more for auth to initialize
                  setTimeout(async () => {
                    if (window.auth?.currentUser) {
                      try {
                        const token = await window.auth.currentUser.getIdToken();
                        resolve(token);
                      } catch (e) {
                        resolve(null);
                      }
                    } else {
                      resolve(null);
                    }
                  }, 500);
                }
              });
              
              // Timeout after 3 seconds
              setTimeout(() => {
                unsubscribe();
                resolve(null);
              }, 3000);
            });
          }
          
          return null;
        } catch (e) {
          console.error('getAuthToken error:', e);
          return null;
        }
      }
      
      async function getUserId() {
        try {
          // First check if auth is available and user is already logged in
          if (window.auth && window.auth.currentUser) {
            return window.auth.currentUser.uid;
          }
          
          // Check localStorage/sessionStorage
          const storedUserId = localStorage.getItem('userId') || sessionStorage.getItem('userId');
          if (storedUserId) {
            return storedUserId;
          }
          
          // Wait for auth state change if auth is available
          if (window.auth) {
            return new Promise((resolve) => {
              const unsubscribe = window.auth.onAuthStateChanged((user) => {
                unsubscribe();
                if (user) {
                  resolve(user.uid);
                } else {
                  // Wait a bit more for auth to initialize
                  setTimeout(() => {
                    resolve(window.auth?.currentUser?.uid || null);
                  }, 500);
                }
              });
              
              // Timeout after 3 seconds
              setTimeout(() => {
                unsubscribe();
                resolve(window.auth?.currentUser?.uid || null);
              }, 3000);
            });
          }
          
          return null;
        } catch (e) {
          console.error('getUserId error:', e);
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

