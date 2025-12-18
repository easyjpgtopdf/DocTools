/**
 * Background Workspace - Instant Upload with MaxMatting Processing
 * Features:
 * - Instant image upload and preview
 * - Automatic high-quality background removal with MaxMatting
 * - Multiple download sizes with credit deduction
 * - Automatic credit deduction after processing
 */

// Helper function to get current user ID
async function getCurrentUserId() {
  // Try Firebase auth first
  try {
    if (window.auth && window.auth.currentUser) {
      return window.auth.currentUser.uid;
    }
    
    // Try to import Firebase auth
    const { getAuth, onAuthStateChanged } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js');
    const auth = getAuth();
    if (auth.currentUser) {
      return auth.currentUser.uid;
    }
    
    // Wait for auth state
    return new Promise((resolve) => {
      const unsubscribe = onAuthStateChanged(auth, (user) => {
        unsubscribe();
        resolve(user ? user.uid : null);
      });
      setTimeout(() => resolve(null), 2000);
    });
  } catch (error) {
    // Fallback to sessionStorage/localStorage
    return sessionStorage.getItem('userId') || 
           localStorage.getItem('userId') || 
           sessionStorage.getItem('user') || 
           null;
  }
}

// Credit manager functions (will be loaded dynamically)
let creditManagerLoaded = false;
let getUserCredits, deductCredits;

// Load credit manager functions
async function loadCreditManager() {
  if (creditManagerLoaded) return;
  
  try {
    const creditModule = await import('./credit-manager.js');
    getUserCredits = creditModule.getUserCredits;
    deductCredits = creditModule.deductCredits;
    creditManagerLoaded = true;
  } catch (error) {
    console.warn('Credit manager not available:', error);
    // Fallback functions
    getUserCredits = async () => ({ credits: 0, error: 'Credit manager not available' });
    deductCredits = async () => ({ success: false, error: 'Credit manager not available' });
    creditManagerLoaded = true;
  }
}

// Get API base URL
function getApiBaseUrl() {
  const hostname = window.location.hostname;
  const isDevelopment = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.');
  if (isDevelopment) {
    return 'http://localhost:3000';
  }
  return window.location.origin;
}

const API_BASE_URL = getApiBaseUrl();
const BACKEND_API_URL = 'https://bg-removal-birefnet-564572183797.us-central1.run.app';

class BackgroundWorkspaceApp {
  constructor() {
    this.state = {
      file: null,
      previewURL: null,
      resultURL: null,
      isProcessing: false,
      processedImageData: null,
      creditsUsed: 0,
      userId: null,
      authToken: null
    };
    
    // Credit costs based on megapixels (matching backend logic)
    this.creditCosts = {
      '1920x1080': 2,   // 2.07 MP - ≤2 MP = 2 credits
      '2048x2048': 4,   // 4.19 MP - ≤6 MP = 4 credits
      '3000x2000': 4,   // 6 MP - ≤6 MP = 4 credits
      '3000x3000': 6,   // 9 MP - ≤9 MP = 6 credits
      '4000x3000': 9,   // 12 MP - ≤12 MP = 9 credits
      '4000x4000': 10,  // 16 MP - ≤16 MP = 10 credits
      '5000x3000': 12,  // 15 MP - ≤20 MP = 12 credits
      '5000x5000': 15,  // 25 MP - ≤25 MP = 15 credits
      'original': 15    // Default for original (will be calculated by backend)
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
      // Try to get user ID from Firebase
      this.state.userId = await getCurrentUserId();
      
      // Try to get auth token
      if (window.auth && window.auth.currentUser) {
        this.state.authToken = await window.auth.currentUser.getIdToken();
      } else {
        // Try from localStorage/sessionStorage
        this.state.authToken = localStorage.getItem('authToken') || 
                              sessionStorage.getItem('authToken') || 
                              localStorage.getItem('firebaseAuthToken');
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
    // File upload
    if (this.el.fileInput) {
      this.el.fileInput.addEventListener('change', (e) => {
        const file = e.target.files?.[0];
        if (file) {
          this.handleFile(file);
        }
      });
    }

    // Upload button
    if (this.el.uploadButton && this.el.fileInput) {
      this.el.uploadButton.addEventListener('click', () => {
        this.el.fileInput.click();
      });
    }

    // Download button
    if (this.el.downloadButton) {
      this.el.downloadButton.addEventListener('click', () => {
        this.showDownloadModal();
      });
    }

    // Download modal events
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

    // Close modal on background click
    if (this.el.downloadModal) {
      this.el.downloadModal.addEventListener('click', (e) => {
        if (e.target === this.el.downloadModal) {
          this.closeDownloadModal();
        }
      });
    }
  }

  resetUI() {
    // Ensure overlay is hidden on page load
    if (this.el.previewOverlay) {
      this.el.previewOverlay.style.display = 'none';
      this.el.previewOverlay.classList.remove('processing');
    }
    
    if (this.el.previewStage) {
      this.el.previewStage.classList.add('empty');
    }
    
    if (this.el.previewPlaceholder) {
      this.el.previewPlaceholder.classList.remove('hidden');
    }
    
    if (this.el.previewOriginal) {
      this.el.previewOriginal.hidden = true;
    }
    
    if (this.el.previewResult) {
      this.el.previewResult.hidden = true;
    }
    
    if (this.el.downloadButton) {
      this.el.downloadButton.disabled = true;
    }
  }

  async handleFile(file) {
    if (!file) return;
    
    this.state.file = file;
    
    // Show preview instantly
    this.showPreview(file);
    
    // Start processing immediately with MaxMatting
    await this.processImage(file);
  }

  showPreview(file) {
    const url = URL.createObjectURL(file);
    this.state.previewURL = url;
    
    // Hide placeholder
    if (this.el.previewPlaceholder) {
      this.el.previewPlaceholder.classList.add('hidden');
    }
    
    // Show preview stage
    if (this.el.previewStage) {
      this.el.previewStage.classList.remove('empty');
    }
    
    // Show original image
    if (this.el.previewOriginal) {
      this.el.previewOriginal.src = url;
      this.el.previewOriginal.hidden = false;
    }
    
    // Hide result initially
    if (this.el.previewResult) {
      this.el.previewResult.hidden = true;
    }
  }

  async processImage(file) {
    if (this.state.isProcessing) return;
    
    this.state.isProcessing = true;
    this.showProcessing(true);
    
    try {
      // Convert file to base64
      const dataURL = await this.fileToDataURL(file);
      
      // Determine image type for optimal processing
      const imageType = await this.detectImageType(file);
      
      // Process with MaxMatting (premium endpoint) - with white background (no transparent)
      const response = await fetch(`${BACKEND_API_URL}/api/premium-bg`, {
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
          whiteBackground: true  // No transparent PNG - white background output
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
        }
        
        if (this.el.previewStage) {
          this.el.previewStage.classList.add('revealed');
        }
        
        if (this.el.downloadButton) {
          this.el.downloadButton.disabled = false;
        }
        
        // Deduct credits automatically
        if (this.state.userId && this.state.creditsUsed > 0) {
          await this.deductCredits(this.state.creditsUsed);
        }
        
        this.showProcessing(false);
        console.log('✅ Image processed successfully with MaxMatting');
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

  async detectImageType(file) {
    // Simple detection based on file name and size
    // You can enhance this with actual image analysis
    const fileName = file.name.toLowerCase();
    
    if (fileName.includes('document') || fileName.includes('doc') || 
        fileName.includes('id') || fileName.includes('card') ||
        fileName.includes('a4') || fileName.includes('letter')) {
      return 'document';
    }
    
    if (fileName.includes('human') || fileName.includes('person') || 
        fileName.includes('portrait') || fileName.includes('people')) {
      return 'human';
    }
    
    if (fileName.includes('animal') || fileName.includes('pet') || 
        fileName.includes('dog') || fileName.includes('cat')) {
      return 'animal';
    }
    
    if (fileName.includes('product') || fileName.includes('ecommerce') || 
        fileName.includes('shop') || fileName.includes('item')) {
      return 'ecommerce';
    }
    
    // Default to human for photos
    return 'human';
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
        this.el.previewOverlay.classList.add('processing');
      } else {
        this.el.previewOverlay.style.display = 'none';
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
        'Background removal with MaxMatting',
        {
          imageType: this.state.processedImageData?.imageType,
          megapixels: this.state.processedImageData?.megapixels,
          pipelineType: this.state.processedImageData?.pipelineType
        }
      );
      
      if (result.success) {
        console.log(`✅ ${amount} credits deducted. Remaining: ${result.creditsRemaining}`);
        // Update dashboard if available
        this.updateDashboardCredits(result.creditsRemaining);
      } else {
        console.error('Credit deduction failed:', result.error);
      }
    } catch (error) {
      console.error('Error deducting credits:', error);
    }
  }

  showDownloadModal() {
    if (!this.el.downloadModal) return;
    
    this.el.downloadModal.classList.add('active');
    this.selectedQuality = null;
    this.selectedSize = 'original';
    
    // Reset selections
    if (this.el.freeDownloadOption) {
      this.el.freeDownloadOption.classList.remove('selected');
    }
    if (this.el.premiumDownloadOption) {
      this.el.premiumDownloadOption.classList.remove('selected');
    }
    if (this.el.confirmDownload) {
      this.el.confirmDownload.disabled = true;
    }
    
    // Update credit info for premium
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
    
    // Update UI
    if (this.el.freeDownloadOption) {
      this.el.freeDownloadOption.classList.toggle('selected', quality === 'free');
    }
    if (this.el.premiumDownloadOption) {
      this.el.premiumDownloadOption.classList.toggle('selected', quality === 'premium');
    }
    
    // Show/hide size selection for premium
    if (this.el.premiumSizeSelect && this.el.premiumSizeSelect.parentElement) {
      if (quality === 'premium') {
        this.el.premiumSizeSelect.parentElement.classList.add('active');
        this.updateCreditInfo(this.el.premiumSizeSelect.value);
      } else {
        this.el.premiumSizeSelect.parentElement.classList.remove('active');
      }
    }
    
    // Enable download button
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
      // Check credits for premium
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
    a.download = 'background-removed-free.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  updateDashboardCredits(creditsRemaining) {
    // Update dashboard credit display if on dashboard page
    if (typeof creditsRemaining === 'number') {
      // Update credit balance display elements
      const creditDisplays = document.querySelectorAll('.user-credits, #credit-balance-display, #credit-balance-display-main, .credit-balance');
      creditDisplays.forEach(el => {
        if (el) {
          el.textContent = creditsRemaining;
          // Add animation effect
          el.style.transition = 'all 0.3s ease';
          el.style.transform = 'scale(1.1)';
          setTimeout(() => {
            el.style.transform = 'scale(1)';
          }, 300);
        }
      });
      
      // Trigger custom event for dashboard updates
      window.dispatchEvent(new CustomEvent('creditsUpdated', {
        detail: { credits: creditsRemaining }
      }));
      
      // Call global update function if available
      if (window.updateCreditBalance) {
        window.updateCreditBalance(creditsRemaining);
      }
      
      // Update via localStorage for cross-tab sync
      localStorage.setItem('lastCreditBalance', creditsRemaining.toString());
      localStorage.setItem('lastCreditUpdate', Date.now().toString());
    }
  }

  async downloadPremiumSize(size) {
    if (!this.state.file) return;
    
    try {
      // Show processing
      this.showProcessing(true);
      
      // Convert file to base64
      const dataURL = await this.fileToDataURL(this.state.file);
      
      // Determine image type
      const imageType = await this.detectImageType(this.state.file);
      
      // Process with selected size - with white background (no transparent)
      const response = await fetch(`${BACKEND_API_URL}/api/premium-bg`, {
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
          whiteBackground: true  // No transparent PNG - white background output
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
        a.download = `background-removed-${size}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Deduct credits
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
  window.backgroundWorkspaceApp = new BackgroundWorkspaceApp();
});

export default BackgroundWorkspaceApp;

