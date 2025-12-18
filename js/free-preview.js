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
      };
      this.backgroundPicker = null;
      this.imageEditor = null;
      this.bindElements();
      this.bindEvents();
      this.resetUI();
      this.initBackgroundPicker();
      this.initImageEditor();
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

      // New upload button
      const newUploadBtn = document.getElementById('newUploadBtn');
      if (newUploadBtn) {
        newUploadBtn.addEventListener('click', () => {
          this.resetToUpload();
        });
      }

      // Edit Image button - toggle image editor panel
      const editImageBtn = document.getElementById('editImageBtn');
      if (editImageBtn) {
        editImageBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          
          console.log('✏️ Edit Image button clicked');
          
          // Check if result section is visible (user must have processed an image first)
          const resultSection = document.getElementById('resultSection');
          if (!resultSection || resultSection.style.display === 'none') {
            alert('Please upload and process an image first before editing.');
            return false;
          }
          
          // Close background picker if open
          if (this.backgroundPicker && this.backgroundPicker.isOpen) {
            this.backgroundPicker.toggle();
          }
          
          if (this.imageEditor) {
            console.log('✅ Image editor found, toggling panel...');
            this.imageEditor.toggle();
          } else {
            console.warn('⚠️ Image editor not initialized yet, initializing now...');
            this.initImageEditor();
            if (this.imageEditor) {
              const resultImg = document.getElementById('resultImage');
              if (resultImg && resultImg.src) {
                this.imageEditor.init(resultImg, this.state.resultURL || resultImg.src);
              }
              setTimeout(() => {
                this.imageEditor.toggle();
              }, 100);
            }
          }
          
          return false;
        });
      } else {
        console.warn('⚠️ Edit Image button not found!');
      }

      // Background button - toggle background picker panel
      const backgroundBtn = document.getElementById('backgroundBtn');
      if (backgroundBtn) {
        backgroundBtn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          
          console.log('🎨 Background button clicked');
          
          // Check if result section is visible (user must have processed an image first)
          const resultSection = document.getElementById('resultSection');
          if (!resultSection || resultSection.style.display === 'none') {
            alert('Please upload and process an image first before applying backgrounds.');
            return false;
          }
          
          // Close image editor if open
          if (this.imageEditor && this.imageEditor.isOpen) {
            this.imageEditor.toggle();
          }
          
          // Update background picker's originalResultURL to use current edited image
          if (this.backgroundPicker && this.imageEditor) {
            const currentImageURL = this.imageEditor.getCurrentImageURL();
            if (currentImageURL) {
              this.backgroundPicker.originalResultURL = currentImageURL;
              console.log('✅ Background picker updated with edited image URL');
            }
          }
          
          if (this.backgroundPicker) {
            console.log('✅ Background picker found, toggling panel...');
            this.backgroundPicker.toggle();
          } else {
            console.warn('⚠️ Background picker not initialized yet, initializing now...');
            this.initBackgroundPicker();
            if (this.backgroundPicker) {
              const resultImg = document.getElementById('resultImage');
              if (resultImg && resultImg.src) {
                // Use edited image if available
                const currentURL = this.imageEditor ? this.imageEditor.getCurrentImageURL() : resultImg.src;
                this.backgroundPicker.init(resultImg, currentURL);
              }
              setTimeout(() => {
                this.backgroundPicker.toggle();
              }, 100);
            }
          }
          
          return false;
        });
      } else {
        console.warn('⚠️ Background button not found!');
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

      // Download button with dropdown
      const downloadBtn = document.getElementById('downloadBtn');
      const downloadDropdown = document.getElementById('downloadDropdown');
      const downloadFree512 = document.getElementById('downloadFree512');
      const downloadPremiumHD = document.getElementById('downloadPremiumHD');
      
      if (downloadBtn) {
        // Toggle dropdown on click
        downloadBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (downloadDropdown) {
            const isVisible = downloadDropdown.style.display === 'block';
            downloadDropdown.style.display = isVisible ? 'none' : 'block';
            
            // Close dropdown if clicking outside
            if (!isVisible) {
              setTimeout(() => {
                document.addEventListener('click', function closeDropdown(e) {
                  if (!downloadBtn.contains(e.target) && !downloadDropdown.contains(e.target)) {
                    downloadDropdown.style.display = 'none';
                    document.removeEventListener('click', closeDropdown);
                  }
                });
              }, 10);
            }
          }
        });
      }
      
      // Free 640px download (updated for industry-level quality)
      if (downloadFree512) {
        downloadFree512.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (downloadDropdown) {
            downloadDropdown.style.display = 'none';
          }
          
          // Get current image src (includes any applied background/edits)
          const resultImg = document.getElementById('resultImage');
          const downloadURL = resultImg && resultImg.src ? resultImg.src : this.state.resultURL;
          
          if (downloadURL) {
            try {
              // Convert to blob if needed
              const response = await fetch(downloadURL);
              const blob = await response.blob();
              const blobURL = URL.createObjectURL(blob);
              
              const a = document.createElement('a');
              a.href = blobURL;
              a.download = 'background-removed-640px.png';
              document.body.appendChild(a);
              a.click();
              a.remove();
              
              // Clean up blob URL
              setTimeout(() => URL.revokeObjectURL(blobURL), 100);
              
              console.log('✅ Free 640px download triggered');
            } catch (err) {
              console.error('❌ Download failed:', err);
              // Fallback to direct download
              const a = document.createElement('a');
              a.href = downloadURL;
              a.download = 'background-removed-640px.png';
              document.body.appendChild(a);
              a.click();
              a.remove();
            }
          } else {
            console.warn('⚠️ No image to download');
            alert('No image available to download. Please process an image first.');
          }
        });
      }
      
      // Premium HD download - check auth and redirect
      if (downloadPremiumHD) {
        downloadPremiumHD.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (downloadDropdown) {
            downloadDropdown.style.display = 'none';
          }
          
          console.log('👑 Premium HD download clicked, checking authentication...');
          
          // Check if user is logged in
          const isLoggedIn = await this.checkUserLoginStatus();
          
          if (isLoggedIn) {
            console.log('✅ User is logged in, redirecting to workspace...');
            // Save current image state to sessionStorage for workspace
            if (this.state.resultURL) {
              sessionStorage.setItem('bgRemovePreviewImage', this.state.resultURL);
              sessionStorage.setItem('bgRemoveOriginalImage', this.state.originalURL || '');
            }
            window.location.href = 'background-workspace.html';
          } else {
            console.log('⚠️ User not logged in, redirecting to pricing...');
            // Save current image state (user can access from dashboard later)
            if (this.state.resultURL) {
              sessionStorage.setItem('bgRemovePreviewImage', this.state.resultURL);
              sessionStorage.setItem('bgRemoveOriginalImage', this.state.originalURL || '');
              // NO auto-redirect after login - user stays in dashboard
            }
            window.location.href = 'pricing.html';
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
      
      // Reset UI
      this.resetUI();
      this.updateUndoRedoButtons();
      
      // Close background picker if open
      if (this.backgroundPicker && this.backgroundPicker.isOpen) {
        this.backgroundPicker.toggle();
      }
    }

    initImageEditor() {
      // Initialize image editor after DOM is ready
      // Wait a bit for scripts to load if needed
      if (typeof window.ImageEditor !== 'undefined') {
        this.imageEditor = new window.ImageEditor();
        const resultImg = document.getElementById('resultImage');
        if (resultImg && resultImg.src) {
          this.imageEditor.init(resultImg, this.state.resultURL || resultImg.src);
        }
        console.log('✅ Image editor initialized');
      } else if (typeof ImageEditor !== 'undefined') {
        // Fallback: try without window prefix
        this.imageEditor = new ImageEditor();
        const resultImg = document.getElementById('resultImage');
        if (resultImg && resultImg.src) {
          this.imageEditor.init(resultImg, this.state.resultURL || resultImg.src);
        }
        console.log('✅ Image editor initialized (fallback)');
      } else {
        console.warn('⚠️ ImageEditor class not found. Make sure image-editor.js is loaded.');
        // Try again after a short delay
        setTimeout(() => {
          if (typeof window.ImageEditor !== 'undefined') {
            this.initImageEditor();
          }
        }, 500);
      }
    }

    initBackgroundPicker() {
      // Initialize background picker after DOM is ready
      // Wait a bit for scripts to load if needed
      if (typeof window.BackgroundPicker !== 'undefined') {
        this.backgroundPicker = new window.BackgroundPicker();
        const resultImg = document.getElementById('resultImage');
        if (resultImg && resultImg.src) {
          this.backgroundPicker.init(resultImg);
        }
        console.log('✅ Background picker initialized');
      } else if (typeof BackgroundPicker !== 'undefined') {
        // Fallback: try without window prefix
        this.backgroundPicker = new BackgroundPicker();
        const resultImg = document.getElementById('resultImage');
        if (resultImg && resultImg.src) {
          this.backgroundPicker.init(resultImg);
        }
        console.log('✅ Background picker initialized (fallback)');
      } else {
        console.warn('⚠️ BackgroundPicker class not found. Make sure background-picker.js is loaded.');
        // Try again after a short delay
        setTimeout(() => {
          if (typeof window.BackgroundPicker !== 'undefined') {
            this.initBackgroundPicker();
          }
        }, 500);
      }
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
      
      console.log('🔄 Updating undo/redo buttons:', {
        historyLength: this.state.history.length,
        historyIndex: this.state.historyIndex,
        canUndo: this.state.historyIndex > 0,
        canRedo: this.state.historyIndex < this.state.history.length - 1
      });
      
      if (undoBtn) {
        const canUndo = this.state.historyIndex > 0 && this.state.history.length > 0;
        undoBtn.disabled = !canUndo;
        console.log('Undo button:', canUndo ? 'ENABLED' : 'DISABLED');
      }
      if (redoBtn) {
        const canRedo = this.state.historyIndex < this.state.history.length - 1;
        redoBtn.disabled = !canRedo;
        console.log('Redo button:', canRedo ? 'ENABLED' : 'DISABLED');
      }
    }

    undo() {
      console.log('⏪ Undo clicked, current index:', this.state.historyIndex, 'history length:', this.state.history.length);
      if (this.state.historyIndex > 0 && this.state.history.length > 0) {
        this.state.historyIndex--;
        this.applyHistoryState();
        console.log('✅ Undo applied, new index:', this.state.historyIndex);
      } else {
        console.warn('⚠️ Cannot undo - at beginning of history or no history');
      }
    }

    redo() {
      console.log('⏩ Redo clicked, current index:', this.state.historyIndex, 'history length:', this.state.history.length);
      if (this.state.historyIndex < this.state.history.length - 1) {
        this.state.historyIndex++;
        this.applyHistoryState();
        console.log('✅ Redo applied, new index:', this.state.historyIndex);
      } else {
        console.warn('⚠️ Cannot redo - at end of history');
      }
    }

    applyHistoryState() {
      if (this.state.historyIndex >= 0 && this.state.historyIndex < this.state.history.length) {
        const state = this.state.history[this.state.historyIndex];
        
        if (this.el.resultImage) {
          // Restore result image
          if (state.result) {
            this.el.resultImage.src = state.result;
            this.state.resultURL = state.result;
          }
          
          // Restore edits if any
          if (state.edits && this.imageEditor) {
            this.imageEditor.restoreFromHistory(state);
          } else if (this.imageEditor) {
            // Reset edits if no edits in this state
            this.imageEditor.currentEffects = {
              sharpness: 0,
              brightness: 0,
              contrast: 0,
              saturation: 0,
              crop: null
            };
            this.imageEditor.updateSliderValues();
          }
          
          // Restore background if any (background is already in state.result if applied)
        }
        
        if (this.el.beforeImage && state.original) {
          this.el.beforeImage.src = state.original;
        }
        
        // Update background picker's original URL to current edited image
        if (this.backgroundPicker && this.imageEditor) {
          const currentURL = this.imageEditor.getCurrentImageURL();
          if (currentURL) {
            this.backgroundPicker.originalResultURL = currentURL;
          }
        }
        
        this.updateUndoRedoButtons();
      }
    }

    async checkUserLoginStatus() {
      // Check Firebase auth if available
      try {
        // Method 1: Check Firebase Auth (Firebase v9+ modular SDK)
        if (typeof window !== 'undefined') {
          // Try to access auth from firebase-init.js or auth.js
          const firebaseInit = await import('./firebase-init.js').catch(() => null);
          if (firebaseInit && firebaseInit.auth) {
            return new Promise((resolve) => {
              firebaseInit.auth.onAuthStateChanged((user) => {
                resolve(!!user);
              });
              // Timeout after 2 seconds
              setTimeout(() => resolve(false), 2000);
            });
          }
          
          // Check if auth module is available globally
          if (window.auth) {
            return new Promise((resolve) => {
              window.auth.onAuthStateChanged((user) => {
                resolve(!!user);
              });
              setTimeout(() => resolve(false), 2000);
            });
          }
        }
        
        // Method 2: Check sessionStorage for user data
        const userId = sessionStorage.getItem('userId') || sessionStorage.getItem('user') || sessionStorage.getItem('userUid');
        if (userId) {
          return true;
        }
        
        // Method 3: Check localStorage for auth token
        const authToken = localStorage.getItem('authToken') || localStorage.getItem('token') || localStorage.getItem('firebaseAuthToken');
        if (authToken) {
          return true;
        }
        
        // Method 4: Check for Firebase user in sessionStorage
        const firebaseUser = sessionStorage.getItem('firebaseUser') || sessionStorage.getItem('firebase:authUser');
        if (firebaseUser) {
          try {
            const userObj = JSON.parse(firebaseUser);
            if (userObj && userObj.uid) {
              return true;
            }
          } catch (e) {
            // Not JSON, but exists
            return true;
          }
        }
        
        return false;
      } catch (err) {
        console.warn('⚠️ Error checking login status:', err);
        return false;
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
      // INSTANT PREVIEW: Show container IMMEDIATELY (synchronous, no async operations)
      const imagePreview = document.getElementById('imagePreview');
      const previewImg = document.getElementById('previewImg');
      const uploadContent = document.getElementById('uploadContent');
      
      // STEP 1: Show preview container IMMEDIATELY (before any async operations)
      if (imagePreview && previewImg) {
        // Show container FIRST - this is instant (no delay)
        imagePreview.style.display = 'block';
        imagePreview.style.visibility = 'visible';
        imagePreview.style.opacity = '1';
        imagePreview.style.zIndex = '10';
        
        // Set image properties BEFORE setting src
        previewImg.style.display = 'block';
        previewImg.style.visibility = 'visible';
        previewImg.style.width = '100%';
        previewImg.style.height = '100%';
        previewImg.style.objectFit = 'contain';
        
        // Hide upload button/content IMMEDIATELY for instant visual feedback
        if (uploadContent) {
          uploadContent.style.opacity = '0.1';
          uploadContent.style.pointerEvents = 'none';
          uploadContent.style.transition = 'opacity 0.1s';
        }
      }
      
      // STEP 2: Create object URL and set src (async, but container already visible)
      const url = URL.createObjectURL(file);
      this.state.previewURL = url;
      this.state.originalURL = url;
      
      // Set src - image will load and appear in already-visible container
      if (previewImg) {
        previewImg.src = url;
      }
      
      // STEP 3: Show result section IMMEDIATELY (before processing)
      const resultImg = document.getElementById('resultImage');
      const resultSection = document.getElementById('resultSection');
      const uploadSection = document.getElementById('uploadSection');
      
      if (resultImg && resultSection && uploadSection) {
        // Show result section immediately (synchronous)
        uploadSection.style.display = 'none';
        resultSection.style.display = 'block';
        resultSection.style.visibility = 'visible';
        
        // Set image properties
        resultImg.style.display = 'block';
        resultImg.style.visibility = 'visible';
        resultImg.style.opacity = '0.7'; // Slightly transparent to show it's preview
        resultImg.style.width = '100%';
        resultImg.style.height = '100%';
        resultImg.style.objectFit = 'contain';
        
        // Set src - image will load in already-visible container
        resultImg.src = url;
      }
    }

    async handleFile(file) {
      // Validate File/Blob
      if (!(file instanceof File) && !(file instanceof Blob)) {
        this.showError('Please select a valid image file.');
        return;
      }
      
      // Validate file size: Free version limit is 500 KB
      const MAX_FILE_SIZE = 500 * 1024; // 500 KB in bytes
      if (file.size > MAX_FILE_SIZE) {
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        this.showError(`File size (${fileSizeMB} MB) exceeds the free version limit of 500 KB. Please compress your image or use Premium HD for larger files.`);
        return;
      }
      
      this.state.file = file;
      this.showError('');
      
      // INSTANT PREVIEW: Show uploaded image immediately
      this.showPreview(file);
      this.setStatus('Image uploaded! Processing with AI...');
      
      // Start processing automatically after showing preview
      await this.process(file);
    }

    async process(file) {
      if (this.state.isProcessing) {
        this.setStatus('Processing already in progress...');
        return;
      }
      this.state.isProcessing = true;
      this.setStatus('AI is processing your image...');
      this.showError(''); // Clear previous errors
      
      // Show processing animation with blinking stars
      this.showProcessingAnimation();

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
        formData.append('maxSize', '640'); // FIX 1: Updated to 640px for industry-level free quality
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
        
        // Hide processing animation
        this.hideProcessingAnimation();

        if (result.success && result.resultImage) {
          this.state.resultURL = result.resultImage;
          
          // Add to history (limit to 4 stages)
          if (this.state.originalURL && result.resultImage) {
            // Remove future history if not at the end
            if (this.state.historyIndex < this.state.history.length - 1) {
              this.state.history = this.state.history.slice(0, this.state.historyIndex + 1);
            }
            
            this.state.history.push({
              original: this.state.originalURL,
              result: result.resultImage,
              edits: null,
              background: null
            });
            
            // Limit history to 4 stages
            const maxHistorySteps = 4;
            if (this.state.history.length > maxHistorySteps) {
              this.state.history.shift();
            } else {
              this.state.historyIndex = this.state.history.length - 1;
            }
            
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
              // Initialize/update background picker with the result image
              if (this.backgroundPicker) {
                // Pass the original transparent background URL directly
                this.backgroundPicker.init(resultImg, result.resultImage);
                console.log('✅ Background picker initialized with original URL:', result.resultImage.substring(0, 50) + '...');
              }
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
        
        // Hide processing animation on error
        this.hideProcessingAnimation();
        
        // Reset state on error
        if (this.el.downloadButton) this.el.downloadButton.disabled = true;
      } finally {
        this.state.isProcessing = false;
      }
    }
    
    showProcessingAnimation() {
      // Create or get processing overlay with blinking stars
      let overlay = document.getElementById('processingOverlay');
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'processingOverlay';
        overlay.style.cssText = `
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: transparent;
          border-radius: 24px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          z-index: 100;
          animation: fadeIn 0.3s ease;
          pointer-events: none;
        `;
        
        // Add blinking stars container
        const starsContainer = document.createElement('div');
        starsContainer.style.cssText = `
          position: relative;
          width: 200px;
          height: 200px;
        `;
        
        // Create multiple blinking stars in a circle
        for (let i = 0; i < 12; i++) {
          const star = document.createElement('div');
          const angle = (i * 30) * Math.PI / 180;
          const radius = 80;
          const x = Math.cos(angle) * radius;
          const y = Math.sin(angle) * radius;
          
          star.style.cssText = `
            position: absolute;
            left: 50%;
            top: 50%;
            width: 8px;
            height: 8px;
            background: #fff;
            border-radius: 50%;
            transform: translate(${x}px, ${y}px);
            box-shadow: 0 0 15px rgba(255, 255, 255, 1), 0 0 30px rgba(67, 97, 238, 0.8);
            animation: blinkStar${i} ${0.8 + (i * 0.1)}s ease-in-out infinite;
            animation-delay: ${i * 0.1}s;
          `;
          starsContainer.appendChild(star);
        }
        
        // Add center AI icon/text
        const centerText = document.createElement('div');
        centerText.textContent = 'AI';
        centerText.style.cssText = `
          position: absolute;
          left: 50%;
          top: 50%;
          transform: translate(-50%, -50%);
          font-size: 2rem;
          font-weight: 700;
          color: #fff;
          text-shadow: 0 0 20px rgba(255, 255, 255, 1), 0 0 40px rgba(67, 97, 238, 0.9), 2px 2px 4px rgba(0, 0, 0, 0.5);
          animation: pulse 1.5s ease-in-out infinite;
        `;
        starsContainer.appendChild(centerText);
        
        overlay.appendChild(starsContainer);
        
        // Add CSS animations if not already added
        if (!document.getElementById('processingAnimationStyles')) {
          const style = document.createElement('style');
          style.id = 'processingAnimationStyles';
          style.textContent = `
            @keyframes fadeIn {
              from { opacity: 0; }
              to { opacity: 1; }
            }
            @keyframes pulse {
              0%, 100% { opacity: 0.7; transform: translate(-50%, -50%) scale(1); }
              50% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
            }
          `;
          // Add individual star animations
          for (let i = 0; i < 12; i++) {
            const angle = (i * 30) * Math.PI / 180;
            const radius = 80;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            style.textContent += `
              @keyframes blinkStar${i} {
                0%, 100% { opacity: 0.3; transform: translate(${x}px, ${y}px) scale(0.8); }
                50% { opacity: 1; transform: translate(${x}px, ${y}px) scale(1.2); }
              }
            `;
          }
          document.head.appendChild(style);
        }
        
        // Find the result image container to append overlay
        const resultImg = document.getElementById('resultImage');
        const container = resultImg?.parentElement;
        
        if (container) {
          container.style.position = 'relative';
          container.appendChild(overlay);
        }
      } else {
        overlay.style.display = 'flex';
      }
    }
    
    hideProcessingAnimation() {
      const overlay = document.getElementById('processingOverlay');
      if (overlay) {
        overlay.style.display = 'none';
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

