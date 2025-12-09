/**
 * Frontend Fetch Code Example for PDF to Excel Conversion
 * 
 * This shows how to call the backend API from your frontend.
 * Replace API_BASE_URL with your actual Cloud Run URL.
 */

// Backend API URL - Update this with your Cloud Run URL after deployment
const API_BASE_URL = 'https://pdf-to-excel-backend-xxxxx-uc.a.run.app';

/**
 * Example 1: Convert PDF to Excel (from file input)
 * Use this when user uploads a PDF file
 */
async function convertPdfToExcel(file) {
  try {
    // Validate file
    if (!file || file.type !== 'application/pdf') {
      alert('Please select a valid PDF file');
      return;
    }
    
    if (file.size > 100 * 1024 * 1024) {
      alert('File size exceeds 100MB limit');
      return;
    }
    
    // Show loading state
    console.log('Uploading and converting PDF...');
    
    // Create FormData
    const fd = new FormData();
    fd.append('file', file);
    
    // Call backend API
    const response = await fetch(`${API_BASE_URL}/api/pdf-to-excel`, {
      method: 'POST',
      body: fd
    });
    
    const result = await response.json();
    
    // Check for insufficient credits
    if (result.insufficient_credits) {
      alert(`Not enough credits. You need ${result.required} credits but only have ${result.available}. Please buy more credits.`);
      return;
    }
    
    // Check for errors
    if (!response.ok || !result.success) {
      throw new Error(result.message || result.detail || 'Conversion failed');
    }
    
    // Success - redirect to download URL
    console.log(`Success! Converted ${result.pagesConverted} pages. Credits left: ${result.creditsLeft}`);
    window.location.href = result.downloadUrl;
    
  } catch (error) {
    console.error('Conversion error:', error);
    alert('Failed to convert PDF to Excel: ' + error.message);
  }
}

/**
 * Example 2: Get current credit balance
 */
async function getCredits() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/credits`, {
      method: 'GET',
      headers: {
        'X-User-ID': 'user123' // In production, get from auth system
      }
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log(`Current credits: ${result.credits}`);
      return result.credits;
    } else {
      throw new Error('Failed to get credits');
    }
  } catch (error) {
    console.error('Error getting credits:', error);
    return null;
  }
}

/**
 * Example 3: Buy credits (dummy endpoint)
 */
async function buyCredits(amount = 10) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/buy-credits?amount=${amount}`, {
      method: 'POST',
      headers: {
        'X-User-ID': 'user123' // In production, get from auth system
      }
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log(`Added ${amount} credits. New balance: ${result.credits}`);
      return result.credits;
    } else {
      throw new Error('Failed to buy credits');
    }
  } catch (error) {
    console.error('Error buying credits:', error);
    return null;
  }
}

/**
 * Example 4: Complete workflow with file input
 * Use this in your HTML file input change handler
 */
document.addEventListener('DOMContentLoaded', function() {
  const fileInput = document.getElementById('pdf-file-input'); // Your file input ID
  const convertButton = document.getElementById('convert-button'); // Your convert button ID
  
  if (fileInput) {
    fileInput.addEventListener('change', async function(e) {
      const file = e.target.files[0];
      if (file) {
        await convertPdfToExcel(file);
      }
    });
  }
  
  if (convertButton) {
    convertButton.addEventListener('click', async function() {
      const fileInput = document.getElementById('pdf-file-input');
      const file = fileInput?.files[0];
      if (file) {
        await convertPdfToExcel(file);
      } else {
        alert('Please select a PDF file first');
      }
    });
  }
});

/**
 * Example 5: Using with drag and drop
 */
function setupDragAndDrop() {
  const dropZone = document.getElementById('drop-zone');
  
  if (!dropZone) return;
  
  dropZone.addEventListener('dragover', function(e) {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
  
  dropZone.addEventListener('dragleave', function(e) {
    e.preventDefault();
    dropZone.classList.remove('dragover');
  });
  
  dropZone.addEventListener('drop', async function(e) {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      await convertPdfToExcel(file);
    } else {
      alert('Please drop a valid PDF file');
    }
  });
}

// Initialize drag and drop if drop zone exists
if (document.getElementById('drop-zone')) {
  setupDragAndDrop();
}

