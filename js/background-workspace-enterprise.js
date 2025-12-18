/**
 * Enterprise Background Workspace - Premium Quality Background Removal
 * Features:
 * - Instant high-res preview (no downscaling)
 * - Client-side image type detection
 * - BiRefNet + MaxMatting processing
 * - Multiple download sizes with credit deduction
 * - Real-time credit balance updates
 */

// Helper function to get current user ID
async function getCurrentUserId() {
  try {
    if (window.auth && window.auth.currentUser) {
      return window.auth.currentUser.uid;
    }
    
    const { getAuth, onAuthStateChanged } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js');
    const auth = getAuth();
    if (auth.currentUser) {
      return auth.currentUser.uid;
    }
    
    return new Promise((resolve) => {
      const unsubscribe = onAuthStateChanged(auth, (user) => {
        unsubscribe();
        resolve(user ? user.uid : null);
      });
      setTimeout(() => resolve(null), 2000);
    });
  } catch (error) {
    return sessionStorage.getItem('userId') || 
           localStorage.getItem('userId') || 
           sessionStorage.getItem('user') || 
           null;
  }
}

// Credit manager functions
let creditManagerLoaded = false;
let getUserCredits, deductCredits;

async function loadCreditManager() {
  if (creditManagerLoaded) return;
  
  try {
    const creditModule = await import('./credit-manager.js');
    getUserCredits = creditModule.getUserCredits;
    deductCredits = creditModule.deductCredits;
    creditManagerLoaded = true;
  } catch (error) {
    console.warn('Credit manager not available:', error);
    getUserCredits = async () => ({ credits: 0, error: 'Credit manager not available' });
    deductCredits = async () => ({ success: false, error: 'Credit manager not available' });
    creditManagerLoaded = true;
  }
}

// Use relative path to proxy through server (avoids CORS, better security)
const BACKEND_API_URL = ''; // Empty = same origin (relative path)

class EnterpriseBackgroundWorkspace {
  constructor() {
    this.state = {
      file: null,
      previewURL: null,
      resultURL: null,
      isProcessing: false,
      processedImageData: null,
      creditsUsed: 0,
      userId: null,
      authToken: null,
      detectedImageType: null,
      imageDimensions: null
    };
    
    // Credit costs based on megapixels
    this.creditCosts = {
      '1920x1080': 2,   // 2.07 MP
      '2048x2048': 4,   // 4.19 MP
      '3000x2000': 4,   // 6 MP
      '3000x3000': 6,   // 9 MP
      '4000x3000': 9,   // 12 MP
      '4000x4000': 10,  // 16 MP
      '5000x3000': 12,  // 15 MP
      '5000x5000': 15,  // 25 MP
      'original': 15    // Default (calculated by backend)
    };
    
    this.init();
  }

  async init() {
    await loadCreditManager();
    await this.initializeAuth();
    this.bindElements();
    this.bindEvents();
    this.resetUI();
  }

  async initializeAuth() {
    try {
      // Get current user ID
      this.state.userId = await getCurrentUserId();
      
      // Get Firebase auth token
      if (window.auth && window.auth.currentUser) {
        try {
          this.state.authToken = await window.auth.currentUser.getIdToken(false); // Get fresh token
        } catch (tokenError) {
          console.warn('Failed to get fresh token, trying cached:', tokenError);
          // Fallback to cached token
          this.state.authToken = await window.auth.currentUser.getIdToken(true);
        }
      } else {
        // Try to get from storage as fallback
        this.state.authToken = localStorage.getItem('authToken') || 
                              sessionStorage.getItem('authToken') || 
                              localStorage.getItem('firebaseAuthToken');
      }
      
      // Ensure we have both userId and token for authenticated requests
      if (!this.state.userId && this.state.authToken) {
        // Try to extract userId from token (if stored)
        const storedUserId = localStorage.getItem('userId') || sessionStorage.getItem('userId');
        if (storedUserId) {
          this.state.userId = storedUserId;
        }
      }
      
      // Refresh auth state listener
      if (window.auth) {
        window.auth.onAuthStateChanged(async (user) => {
          if (user) {
            this.state.userId = user.uid;
            try {
              this.state.authToken = await user.getIdToken(false);
            } catch (e) {
              console.warn('Token refresh failed:', e);
            }
          } else {
            this.state.userId = null;
            this.state.authToken = null;
          }
        });
      }
    } catch (error) {
      console.warn('Auth initialization failed:', error);
    }
  }

  bindElements() {
    this.el = {
      fileInput: document.getElementById('multipleImageUpload'),
      uploadButton: document.getElementById('newUploadBtn'),
      previewOriginal: document.getElementById('previewOriginal'),
      previewResult: document.getElementById('previewResult'),
      previewStage: document.getElementById('previewStage'),
      previewOverlay: document.getElementById('previewOverlay'),
      previewPlaceholder: document.getElementById('previewPlaceholder'),
      downloadButton: document.getElementById('downloadPng'),
      downloadModal: document.getElementById('downloadModal'),
      premiumSizeSelect: document.getElementById('premiumSizeSelect'),
      confirmDownload: document.getElementById('confirmDownload'),
      cancelDownload: document.getElementById('cancelDownload'),
      freeDownloadOption: document.getElementById('freeDownloadOption'),
      premiumDownloadOption: document.getElementById('premiumDownloadOption'),
      premiumCreditInfo: document.getElementById('premiumCreditInfo'),
      premiumCreditText: document.getElementById('premiumCreditText')
    };
  }

  bindEvents() {
    if (this.el.fileInput) {
      this.el.fileInput.addEventListener('change', (e) => {
        const file = e.target.files?.[0];
        if (file) {
          this.handleFile(file);
        }
      });
    }

    if (this.el.uploadButton && this.el.fileInput) {
      this.el.uploadButton.addEventListener('click', () => {
        this.el.fileInput.click();
      });
    }

    if (this.el.downloadButton) {
      this.el.downloadButton.addEventListener('click', () => {
        this.showDownloadModal();
      });
    }

    if (this.el.freeDownloadOption) {
      this.el.freeDownloadOption.addEventListener('click', () => {
        this.selectDownloadOption('free');
      });
    }

    if (this.el.premiumDownloadOption) {
      this.el.premiumDownloadOption.addEventListener('click', () => {
        this.selectDownloadOption('premium');
      });
    }

    if (this.el.premiumSizeSelect) {
      this.el.premiumSizeSelect.addEventListener('change', (e) => {
        this.updateCreditInfo(e.target.value);
      });
    }

    if (this.el.confirmDownload) {
      this.el.confirmDownload.addEventListener('click', () => {
        this.handleDownload();
      });
    }

    if (this.el.cancelDownload) {
      this.el.cancelDownload.addEventListener('click', () => {
        this.closeDownloadModal();
      });
    }

    if (this.el.downloadModal) {
      this.el.downloadModal.addEventListener('click', (e) => {
        if (e.target === this.el.downloadModal) {
          this.closeDownloadModal();
        }
      });
    }
  }

  resetUI() {
    // CRITICAL: No preview, no loader on page load
    if (this.el.previewOverlay) {
      this.el.previewOverlay.style.display = 'none';
      this.el.previewOverlay.classList.remove('processing');
      this.el.previewOverlay.style.opacity = '0';
    }
    
    if (this.el.previewStage) {
      this.el.previewStage.classList.add('empty');
    }
    
    if (this.el.previewPlaceholder) {
      this.el.previewPlaceholder.style.display = 'flex';
    }
    
    if (this.el.previewOriginal) {
      this.el.previewOriginal.hidden = true;
      this.el.previewOriginal.style.display = 'none';
    }
    
    if (this.el.previewResult) {
      this.el.previewResult.hidden = true;
      this.el.previewResult.style.display = 'none';
    }
    
    if (this.el.downloadButton) {
      this.el.downloadButton.disabled = true;
    }
  }

  /**
   * Client-side image type detection
   * Based on aspect ratio + metadata
   */
  async detectImageType(file) {
    return new Promise((resolve) => {
      const img = new Image();
      const url = URL.createObjectURL(file);
      
      img.onload = () => {
        const width = img.width;
        const height = img.height;
        const aspectRatio = width / height;
        const megapixels = (width * height) / 1_000_000;
        
        // Store dimensions
        this.state.imageDimensions = { width, height, aspectRatio, megapixels };
        
        // Detection logic
        let imageType = 'human'; // Default
        
        // Document/ID Card detection
        // A4: 0.707, Letter: 0.773, ID: 0.6-0.7 or 1.5-1.7
        if ((aspectRatio >= 0.6 && aspectRatio <= 0.85) || 
            (aspectRatio >= 1.2 && aspectRatio <= 1.7)) {
          // Check if it's likely a document
          if (megapixels <= 12 || file.name.toLowerCase().match(/document|doc|id|card|a4|letter/i)) {
            imageType = 'document';
          }
        }
        
        // Animal detection (often square or portrait)
        if (file.name.toLowerCase().match(/animal|pet|dog|cat|bird|wildlife/i)) {
          imageType = 'animal';
        }
        
        // E-commerce detection (often square or product-like)
        if (file.name.toLowerCase().match(/product|ecommerce|shop|item|merchandise/i) ||
            (aspectRatio >= 0.9 && aspectRatio <= 1.1 && megapixels <= 8)) {
          imageType = 'ecommerce';
        }
        
        // Human detection (portrait or landscape with people)
        if (file.name.toLowerCase().match(/human|person|people|portrait|selfie|photo/i) ||
            (aspectRatio >= 0.5 && aspectRatio <= 2.0 && megapixels > 2)) {
          imageType = 'human';
        }
        
        this.state.detectedImageType = imageType;
        URL.revokeObjectURL(url);
        resolve(imageType);
      };
      
      img.onerror = () => {
        URL.revokeObjectURL(url);
        resolve('human'); // Default fallback
      };
      
      img.src = url;
    });
  }

  async handleFile(file) {
    if (!file) return;
    
    this.state.file = file;
    
    // Detect image type
    await this.detectImageType(file);
    
    // Show high-res preview instantly (no downscaling)
    this.showHighResPreview(file);
    
    // Start processing immediately
    await this.processImage(file);
  }

  /**
   * Show high-resolution preview (no downscaling, no blur)
   */
  showHighResPreview(file) {
    const url = URL.createObjectURL(file);
    this.state.previewURL = url;
    
    // Hide placeholder
    if (this.el.previewPlaceholder) {
      this.el.previewPlaceholder.style.display = 'none';
    }
    
    // Show preview stage
    if (this.el.previewStage) {
      this.el.previewStage.classList.remove('empty');
    }
    
    // Show original image at full resolution
    if (this.el.previewOriginal) {
      this.el.previewOriginal.src = url;
      this.el.previewOriginal.hidden = false;
      this.el.previewOriginal.style.display = 'block';
      // Ensure no blur
      this.el.previewOriginal.style.imageRendering = 'high-quality';
      this.el.previewOriginal.style.imageRendering = '-webkit-optimize-contrast';
    }
    
    // Hide result initially
    if (this.el.previewResult) {
      this.el.previewResult.hidden = true;
      this.el.previewResult.style.display = 'none';
    }
  }

  async processImage(file) {
    if (this.state.isProcessing) return;
    
    this.state.isProcessing = true;
    this.showProcessing(true);
    
    try {
      // Convert file to base64
      const dataURL = await this.fileToDataURL(file);
      
      // Use detected image type
      const imageType = this.state.detectedImageType || 'human';
      
      // Process with BiRefNet + MaxMatting (enterprise endpoint)
      const response = await fetch('/api/premium-bg', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.state.authToken ? `Bearer ${this.state.authToken}` : ''
        },
        body: JSON.stringify({
          imageData: dataURL,
          userId: this.state.userId,
          targetSize: 'original',
          imageType: imageType,
          whiteBackground: true,  // JPG with white background
          outputFormat: 'jpg',    // JPG format
          quality: 100            // Maximum quality
        })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Server error ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success && result.resultImage) {
        // Store processed image data
        this.state.resultURL = result.resultImage;
        this.state.processedImageData = result;
        this.state.creditsUsed = result.creditsUsed || 0;
        
        // Show result
        if (this.el.previewResult) {
          this.el.previewResult.src = result.resultImage;
          this.el.previewResult.hidden = false;
          this.el.previewResult.style.display = 'block';
          this.el.previewResult.style.imageRendering = 'high-quality';
        }
        
        if (this.el.previewStage) {
          this.el.previewStage.classList.add('revealed');
        }
        
        if (this.el.downloadButton) {
          this.el.downloadButton.disabled = false;
        }
        
        // Hide processing overlay immediately
        this.showProcessing(false);
        
        // Deduct credits automatically AFTER successful processing
        if (this.state.userId && this.state.creditsUsed > 0) {
          await this.deductCredits(this.state.creditsUsed);
        }
        
        console.log('✅ Image processed successfully with BiRefNet + MaxMatting');
      } else {
        throw new Error(result.error || 'Processing failed');
      }
    } catch (error) {
      console.error('Processing error:', error);
      this.showProcessing(false);
      alert(`Processing failed: ${error.message}. Please try again.`);
    } finally {
      this.state.isProcessing = false;
    }
  }

  fileToDataURL(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  showProcessing(show) {
    if (this.el.previewOverlay) {
      if (show) {
        this.el.previewOverlay.style.display = 'flex';
        this.el.previewOverlay.style.opacity = '1';
        this.el.previewOverlay.classList.add('processing');
      } else {
        // Hide immediately after processing
        this.el.previewOverlay.style.display = 'none';
        this.el.previewOverlay.style.opacity = '0';
        this.el.previewOverlay.classList.remove('processing');
      }
    }
  }

  async deductCredits(amount) {
    if (!this.state.userId) {
      console.warn('No user ID, skipping credit deduction');
      return;
    }
    
    try {
      const result = await deductCredits(
        this.state.userId,
        amount,
        'Enterprise background removal (BiRefNet + MaxMatting)',
        {
          imageType: this.state.detectedImageType,
          megapixels: this.state.imageDimensions?.megapixels,
          pipelineType: 'enterprise'
        }
      );
      
      if (result.success) {
        console.log(`✅ ${amount} credits deducted. Remaining: ${result.creditsRemaining}`);
        this.updateDashboardCredits(result.creditsRemaining);
      } else {
        console.error('Credit deduction failed:', result.error);
      }
    } catch (error) {
      console.error('Error deducting credits:', error);
    }
  }

  updateDashboardCredits(creditsRemaining) {
    if (typeof creditsRemaining === 'number') {
      const creditDisplays = document.querySelectorAll('.user-credits, #credit-balance-display, #credit-balance-display-main, .credit-balance');
      creditDisplays.forEach(el => {
        if (el) {
          el.textContent = creditsRemaining;
          el.style.transition = 'all 0.3s ease';
          el.style.transform = 'scale(1.1)';
          setTimeout(() => {
            el.style.transform = 'scale(1)';
          }, 300);
        }
      });
      
      window.dispatchEvent(new CustomEvent('creditsUpdated', {
        detail: { credits: creditsRemaining }
      }));
      
      if (window.updateCreditBalance) {
        window.updateCreditBalance(creditsRemaining);
      }
      
      localStorage.setItem('lastCreditBalance', creditsRemaining.toString());
      localStorage.setItem('lastCreditUpdate', Date.now().toString());
    }
  }

  showDownloadModal() {
    if (!this.el.downloadModal) return;
    
    this.el.downloadModal.classList.add('active');
    this.selectedQuality = null;
    this.selectedSize = 'original';
    
    if (this.el.freeDownloadOption) {
      this.el.freeDownloadOption.classList.remove('selected');
    }
    if (this.el.premiumDownloadOption) {
      this.el.premiumDownloadOption.classList.remove('selected');
    }
    if (this.el.confirmDownload) {
      this.el.confirmDownload.disabled = true;
    }
    
    if (this.el.premiumSizeSelect) {
      this.updateCreditInfo(this.el.premiumSizeSelect.value);
    }
  }

  closeDownloadModal() {
    if (this.el.downloadModal) {
      this.el.downloadModal.classList.remove('active');
    }
  }

  selectDownloadOption(quality) {
    this.selectedQuality = quality;
    
    if (this.el.freeDownloadOption) {
      this.el.freeDownloadOption.classList.toggle('selected', quality === 'free');
    }
    if (this.el.premiumDownloadOption) {
      this.el.premiumDownloadOption.classList.toggle('selected', quality === 'premium');
    }
    
    if (this.el.premiumSizeSelect && this.el.premiumSizeSelect.parentElement) {
      if (quality === 'premium') {
        this.el.premiumSizeSelect.parentElement.classList.add('active');
        this.updateCreditInfo(this.el.premiumSizeSelect.value);
      } else {
        this.el.premiumSizeSelect.parentElement.classList.remove('active');
      }
    }
    
    if (this.el.confirmDownload) {
      this.el.confirmDownload.disabled = false;
    }
  }

  async updateCreditInfo(size) {
    if (!this.el.premiumCreditInfo || !this.el.premiumCreditText) return;
    
    const credits = this.creditCosts[size] || this.creditCosts['original'];
    this.selectedSize = size;
    
    if (this.state.userId) {
      try {
        const creditInfo = await getUserCredits(this.state.userId);
        const available = creditInfo.credits || 0;
        const hasEnough = available >= credits;
        
        this.el.premiumCreditText.innerHTML = `
          <strong>Credits Required:</strong> ${credits} credits<br>
          <strong>Your Balance:</strong> ${available} credits
          ${!hasEnough ? '<br><span style="color: #ef4444;">⚠️ Insufficient credits</span>' : ''}
        `;
        this.el.premiumCreditInfo.style.display = 'block';
        
        // Disable download if insufficient credits
        if (this.el.confirmDownload) {
          this.el.confirmDownload.disabled = !hasEnough;
        }
      } catch (error) {
        console.error('Error fetching credit info:', error);
        this.el.premiumCreditText.textContent = `Credits Required: ${credits} credits`;
        this.el.premiumCreditInfo.style.display = 'block';
      }
    } else {
      this.el.premiumCreditText.textContent = `Credits Required: ${credits} credits (Sign in required)`;
      this.el.premiumCreditInfo.style.display = 'block';
    }
  }

  async handleDownload() {
    if (!this.selectedQuality) {
      alert('Please select a download option');
      return;
    }
    
    if (this.selectedQuality === 'premium') {
      const credits = this.creditCosts[this.selectedSize] || this.creditCosts['original'];
      
      if (this.state.userId) {
        const creditInfo = await getUserCredits(this.state.userId);
        const available = creditInfo.credits || 0;
        
        if (available < credits) {
          alert(`Insufficient credits. You need ${credits} credits but only have ${available}. Please purchase more credits.`);
          return;
        }
      } else {
        alert('Please sign in to download premium quality images.');
        return;
      }
      
      // Process with selected size
      await this.downloadPremiumSize(this.selectedSize);
    } else {
      // Free download (512px)
      this.downloadFree();
    }
    
    this.closeDownloadModal();
  }

  downloadFree() {
    if (!this.state.resultURL) return;
    
    const a = document.createElement('a');
    a.href = this.state.resultURL;
    a.download = 'background-removed-free.jpg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  async downloadPremiumSize(size) {
    if (!this.state.file) return;
    
    try {
      this.showProcessing(true);
      
      const dataURL = await this.fileToDataURL(this.state.file);
      const imageType = this.state.detectedImageType || 'human';
      
      const response = await fetch('/api/premium-bg', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.state.authToken ? `Bearer ${this.state.authToken}` : ''
        },
        body: JSON.stringify({
          imageData: dataURL,
          userId: this.state.userId,
          targetSize: size,
          imageType: imageType,
          whiteBackground: true,
          outputFormat: 'jpg',
          quality: 100
        })
      });
      
      if (!response.ok) {
        throw new Error(`Server error ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success && result.resultImage) {
        // Download
        const a = document.createElement('a');
        a.href = result.resultImage;
        a.download = `background-removed-${size}.jpg`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Deduct credits BEFORE download completes
        const credits = result.creditsUsed || this.creditCosts[size] || this.creditCosts['original'];
        if (this.state.userId && credits > 0) {
          await this.deductCredits(credits);
        }
        
        this.showProcessing(false);
      } else {
        throw new Error(result.error || 'Processing failed');
      }
    } catch (error) {
      console.error('Download error:', error);
      this.showProcessing(false);
      alert(`Download failed: ${error.message}`);
    }
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  window.enterpriseBackgroundWorkspace = new EnterpriseBackgroundWorkspace();
});

export default EnterpriseBackgroundWorkspace;

