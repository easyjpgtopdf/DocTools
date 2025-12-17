/**
 * Background Picker Module
 * Handles background selection and application for background-remover page
 */

class BackgroundPicker {
  constructor() {
    this.currentBackground = null;
    this.resultImage = null;
    this.originalResultURL = null;
    this.backgroundImage = new Image();
    this.isOpen = false;
    
    // Background data from background-style.html
    this.backgrounds = {
      magic: [
        { label: 'Aurora Night', url: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Mountain Sunrise', url: 'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Golden Forest', url: 'https://images.unsplash.com/photo-1470770903676-69b98201ea1c?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Desert Dream', url: 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Lavender Field', url: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80&sat=-20' },
        { label: 'Sea Mist', url: 'https://images.unsplash.com/photo-1474871256005-c5f7eb1d77f1?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Canyon Glow', url: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Foggy Pines', url: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Snow Valley', url: 'https://images.unsplash.com/photo-1508261305430-1e1c5237c11f?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Moody Lake', url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Cherry Blossoms', url: 'https://images.unsplash.com/photo-1494475673543-6a6a27143b22?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Palm Horizon', url: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Beach Sunset', url: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Autumn Path', url: 'https://images.unsplash.com/photo-1476041800959-2f6bb412c8ce?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Starry Ridge', url: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1600&q=80&sat=-30' },
        { label: 'Emerald Hills', url: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=80' },
        { label: 'River Glow', url: 'https://images.unsplash.com/photo-1477414348463-c0eb7f1359b6?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Purple Mountains', url: 'https://images.unsplash.com/photo-1500534625967-5b1fd4700f39?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Rolling Clouds', url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1600&q=80&sat=-50' },
        { label: 'Glacier Lagoon', url: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1600&q=80&hue=190' },
        { label: 'Tropical Blush', url: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1600&q=80&sat=-10' },
        { label: 'Winter Sunrise', url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1600&q=80&hue=0' }
      ],
      photos: [
        { label: 'New York Skyline', url: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1600&q=80' },
        { label: 'London Bridge', url: 'https://images.unsplash.com/photo-1498887960847-2a25ef84c54b?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Paris Eiffel', url: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Tokyo Lights', url: 'https://images.unsplash.com/photo-1549693578-d683be217e58?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Dubai Skyline', url: 'https://images.unsplash.com/photo-1533104816931-20fa691ff6ca?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Singapore Marina', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Sydney Opera', url: 'https://images.unsplash.com/photo-1506976785307-8732e854ad89?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Hong Kong', url: 'https://images.unsplash.com/photo-1505767641034-1b3f0a7ab1d2?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Barcelona Streets', url: 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?auto=format&fit=crop&w=1600&q=80' },
        { label: 'San Francisco', url: 'https://images.unsplash.com/photo-1465446751832-9c63a0470b97?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Seoul Skyline', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&sat=-20' },
        { label: 'Shanghai Tower', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&hue=210' },
        { label: 'Amsterdam Canals', url: 'https://images.unsplash.com/photo-1444676632488-26a136c45b9b?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Rome Sunrise', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&sat=-60' },
        { label: 'Los Angeles', url: 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?auto=format&fit=crop&w=1600&q=80&hue=15' },
        { label: 'Rio de Janeiro', url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1600&q=80&hue=5' },
        { label: 'Berlin Lights', url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1600&q=80&sat=-10' },
        { label: 'Istanbul', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&hue=30' },
        { label: 'Cape Town', url: 'https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Moscow', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&hue=340' },
        { label: 'Vancouver', url: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1600&q=80&sat=-80' },
        { label: 'Mumbai', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&sat=-30' }
      ],
      tech: [
        { label: 'Data Center', url: 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Neon Grid', url: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Modern Office', url: 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Blue Circuit', url: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80&sat=-60' },
        { label: 'Server Aisle', url: 'https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Drone City', url: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Futuristic Lobby', url: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80&hue=200' },
        { label: 'Cyber Lines', url: 'https://images.unsplash.com/photo-1535223289827-42f1e9919769?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Innovation Hub', url: 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1600&q=80&sat=-30' },
        { label: 'Neon Tunnel', url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1600&q=80&hue=280' },
        { label: 'VR Experience', url: 'https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=1600&q=80&sat=-40' },
        { label: 'Innovation Lab', url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1600&q=80&sat=-20' },
        { label: 'Neon Bridge', url: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1600&q=80&sat=-20' },
        { label: 'Tech Expo', url: 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1600&q=80&hue=300' },
        { label: 'Smart City', url: 'https://images.unsplash.com/photo-1535223289827-42f1e9919769?auto=format&fit=crop&w=1600&q=80&sat=-45' },
        { label: 'AI Circuit', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&sat=-70' },
        { label: 'Digital Wave', url: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80&hue=220' },
        { label: 'Tech Vibes', url: 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=1600&q=80&hue=340' },
        { label: 'Quantum Lab', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&sat=-15' },
        { label: 'Hologram Hall', url: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80&hue=180' },
        { label: 'Innovation Bridge', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&sat=-5' },
        { label: 'Satellite View', url: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=80&sat=-70' },
        { label: 'IoT Hub', url: 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1600&q=80' },
        { label: 'Digital Aurora', url: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1600&q=80&sat=-5' },
        { label: 'Smart Grid', url: 'https://images.unsplash.com/photo-1526481280695-3c469928b67b?auto=format&fit=crop&w=1600&q=80&hue=250' }
      ]
    };

    this.colorPalette = [
      { label: 'Transparent', value: 'transparent' },
      { label: 'Pure White', value: '#ffffff' },
      { label: 'Charcoal', value: '#111827' },
      { label: 'Sky Blue', value: '#bfdbfe' },
      { label: 'Sunset', value: '#fb7185' },
      { label: 'Mint', value: '#bbf7d0' },
      { label: 'Lavender', value: '#c4b5fd' },
      { label: 'Peach', value: '#fed7aa' },
      { label: 'Slate', value: '#475569' },
      { label: 'Golden', value: '#facc15' },
      { label: 'Emerald', value: '#34d399' }
    ];
  }

  init(resultImageElement, originalURL = null) {
    this.resultImage = resultImageElement;
    
    // Use provided originalURL if available, otherwise get from image
    if (originalURL) {
      this.originalResultURL = originalURL;
      console.log('✅ Original result URL set from parameter:', this.originalResultURL.substring(0, 50) + '...');
    } else if (this.resultImage) {
      // Wait for image to load before saving original URL
      if (this.resultImage.complete && this.resultImage.naturalWidth > 0) {
        // Image already loaded
        this.originalResultURL = this.resultImage.src;
        console.log('✅ Original result URL saved from image src:', this.originalResultURL.substring(0, 50) + '...');
      } else {
        // Wait for image to load
        this.resultImage.onload = () => {
          // Only set if not already set
          if (!this.originalResultURL) {
            this.originalResultURL = this.resultImage.src;
            console.log('✅ Original result URL saved (after load):', this.originalResultURL.substring(0, 50) + '...');
          }
        };
        // Also set if already has src
        if (this.resultImage.src && !this.originalResultURL) {
          this.originalResultURL = this.resultImage.src;
        }
      }
    }
    
    this.renderGrids();
    this.renderColors();
    this.bindTabEvents();
    this.bindCloseButton();
    
    console.log('BackgroundPicker initialized with originalResultURL:', this.originalResultURL ? 'SET' : 'NOT SET');
  }

  toggle() {
    const panel = document.getElementById('backgroundPickerPanel');
    if (!panel) return;

    this.isOpen = !this.isOpen;
    
    if (this.isOpen) {
      panel.style.display = 'block';
      // Animate slide-in
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

  renderGrids() {
    // Render Magic Photos
    this.renderGrid('magicGrid', this.backgrounds.magic);
    
    // Render Cityscapes
    this.renderGrid('photoGrid', this.backgrounds.photos);
    
    // Render Tech & Infra
    this.renderGrid('techGrid', this.backgrounds.tech);
  }

  renderGrid(containerId, items) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';
    items.forEach((item) => {
      const div = document.createElement('div');
      div.className = 'bg-thumb';
      const img = document.createElement('img');
      img.src = item.url;
      img.alt = item.label;
      img.loading = 'lazy';
      const label = document.createElement('span');
      label.textContent = item.label;
      div.appendChild(img);
      div.appendChild(label);
      div.addEventListener('click', async () => {
        await this.applyBackgroundImage(item.url, item.label);
        // Update selected state
        document.querySelectorAll('.bg-thumb').forEach((el) => el.classList.remove('selected'));
        div.classList.add('selected');
      });
      container.appendChild(div);
    });
  }

  renderColors() {
    const container = document.getElementById('colorGrid');
    if (!container) return;

    container.innerHTML = '';
    this.colorPalette.forEach((entry) => {
      if (entry.value === 'transparent') return; // handled in transparent tab
      
      const chip = document.createElement('div');
      chip.className = 'bg-color-chip';
      const fill = document.createElement('div');
      fill.className = 'fill';
      fill.style.background = entry.value;
      chip.appendChild(fill);
      chip.addEventListener('click', () => {
        document.querySelectorAll('.bg-color-chip').forEach((el) => el.classList.remove('selected'));
        chip.classList.add('selected');
        this.applyBackgroundColor(entry.value, entry.label);
      });
      container.appendChild(chip);
    });
  }

  bindTabEvents() {
    document.querySelectorAll('.bg-tab-button').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.bg-tab-button').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('.bg-tab-content').forEach((panel) => {
          panel.hidden = panel.dataset.tab !== btn.dataset.tab;
        });
        
        if (btn.dataset.tab === 'transparent') {
          this.applyBackgroundColor('transparent', 'Transparent');
        }
      });
    });
  }

  bindCloseButton() {
    const closeBtn = document.getElementById('closeBackgroundPicker');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        this.toggle();
      });
    }
  }

  async applyBackgroundImage(imageUrl, label) {
    if (!this.resultImage || !this.originalResultURL) {
      console.error('No result image available');
      return;
    }

    try {
      // Load background image
      await this.loadImage(this.backgroundImage, imageUrl + '&auto=compress&fit=crop&w=1200&q=80');
      
      // Load foreground (result image with transparent background)
      const foregroundImg = new Image();
      foregroundImg.crossOrigin = 'anonymous';
      await this.loadImage(foregroundImg, this.originalResultURL);

      // Create canvas for composition
      const canvas = document.createElement('canvas');
      canvas.width = foregroundImg.width;
      canvas.height = foregroundImg.height;
      const ctx = canvas.getContext('2d');

      console.log('🖼️ Compositing images:', {
        canvasWidth: canvas.width,
        canvasHeight: canvas.height,
        bgWidth: this.backgroundImage.width,
        bgHeight: this.backgroundImage.height,
        fgWidth: foregroundImg.width,
        fgHeight: foregroundImg.height
      });

      // Draw background (scale to fit canvas)
      ctx.drawImage(this.backgroundImage, 0, 0, canvas.width, canvas.height);
      
      // Draw foreground on top
      ctx.drawImage(foregroundImg, 0, 0);

      // Update result image
      const dataURL = canvas.toDataURL('image/png');
      this.resultImage.src = dataURL;
      this.currentBackground = imageUrl;
      
      // Update download state in free-preview.js if available
      if (window.freePreviewApp && window.freePreviewApp.state) {
        window.freePreviewApp.state.resultURL = dataURL;
      }

      console.log(`✅ Background applied successfully: ${label}`);
    } catch (err) {
      console.error('❌ Failed to apply background image:', err);
      alert('Failed to apply background. Please try another background or check console for details.');
    }
  }

  async applyBackgroundColor(color, label) {
    if (!this.resultImage || !this.originalResultURL) {
      console.error('❌ No result image available:', {
        hasResultImage: !!this.resultImage,
        hasOriginalURL: !!this.originalResultURL
      });
      return;
    }

    console.log('🎨 Applying background color:', label);

    try {
      // Load foreground (result image with transparent background)
      console.log('📥 Loading foreground image (original result)...');
      const foregroundImg = new Image();
      if (!this.originalResultURL.startsWith('data:')) {
        foregroundImg.crossOrigin = 'anonymous';
      }
      await this.loadImage(foregroundImg, this.originalResultURL);

      // Create canvas for composition
      const canvas = document.createElement('canvas');
      canvas.width = foregroundImg.width;
      canvas.height = foregroundImg.height;
      const ctx = canvas.getContext('2d');

      if (color === 'transparent') {
        // Draw checkerboard pattern for transparent
        const size = 40;
        for (let y = 0; y < canvas.height; y += size) {
          for (let x = 0; x < canvas.width; x += size) {
            ctx.fillStyle = ((x / size + y / size) % 2 === 0) ? '#f1f5f9' : '#e2e8f0';
            ctx.fillRect(x, y, size, size);
          }
        }
      } else {
        // Draw solid color
        ctx.fillStyle = color;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }

      // Draw foreground on top
      ctx.drawImage(foregroundImg, 0, 0);

      // Update result image
      const dataURL = canvas.toDataURL('image/png');
      this.resultImage.src = dataURL;
      this.currentBackground = color;
      
      // Update download state in free-preview.js if available
      if (window.freePreviewApp && window.freePreviewApp.state) {
        window.freePreviewApp.state.resultURL = dataURL;
      }

      console.log(`✅ Background color applied successfully: ${label}`);
    } catch (err) {
      console.error('❌ Failed to apply background color:', err);
      alert('Failed to apply background color. Please try again or check console for details.');
    }
  }

  loadImage(img, src) {
    return new Promise((resolve, reject) => {
      img.onload = () => resolve();
      img.onerror = (err) => {
        console.error('❌ Image load failed:', src.substring(0, 100), err);
        reject(new Error('Failed to load image: ' + src.substring(0, 50)));
      };
      // Set crossOrigin before src to avoid CORS issues
      if (!src.startsWith('data:')) {
        img.crossOrigin = 'anonymous';
      }
      img.src = src;
    });
  }

  reset() {
    if (this.resultImage && this.originalResultURL) {
      this.resultImage.src = this.originalResultURL;
      this.currentBackground = null;
      document.querySelectorAll('.bg-thumb').forEach((el) => el.classList.remove('selected'));
      document.querySelectorAll('.bg-color-chip').forEach((el) => el.classList.remove('selected'));
    }
  }
}

// Export for use in other scripts - make it globally available immediately
(function() {
  if (typeof window !== 'undefined') {
    window.BackgroundPicker = BackgroundPicker;
    console.log('✅ BackgroundPicker class registered globally');
  }
})();

